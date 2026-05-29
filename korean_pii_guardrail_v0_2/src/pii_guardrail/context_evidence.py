"""Raw-text-free context rule inventory and evidence reporting.

This module supports the M4 context scoring evidence upgrade without changing
runtime scoring behavior. It inventories configured context reason codes and
aggregates rule firing counts from existing labeled evaluation datasets.
"""

from __future__ import annotations

import datetime
import json
import math
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .context_scorer import (
    _BOOST_RULES_BY_ENTITY,
    _EXAMPLE_PENALTY_RULE,
    _FIELD_LABEL_GROUP_BY_RULE,
    _NEGATIVE_GROUP_BY_RULE,
    _PENALTY_RULES_BY_ENTITY,
)
from .dictionary_loader import (
    load_composite_upgrades,
    load_context_boosts,
    load_context_penalties,
)
from .enums import Action, EntityType
from .evaluation_harness import (
    EvaluationCase,
    EvaluationRunner,
    count_report_raw_text_leaks,
    load_jsonl_cases,
)
from .pipeline import GuardrailPipeline


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ACTIONABLE_ACTIONS = frozenset({Action.MASK, Action.HASH, Action.BLOCK})
CONTEXT_REASON_PREFIXES = (
    "context.boost.",
    "context.penalty.",
    "context.composite.",
)
DEFAULT_MINIMUM_SUPPORT = 50
SMOOTHING_ALPHA = 0.5


@dataclass(frozen=True)
class DatasetSpec:
    dataset_id: str
    path: Path


@dataclass(frozen=True)
class EvidenceBuildResult:
    payload: dict[str, Any]
    cases: tuple[EvaluationCase, ...]


def build_context_rule_inventory(
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    """Return every configured context reason code and its behavior owner."""

    config_dir = project_root / "configs"
    scoring_path = config_dir / "scoring.yaml"
    boosts = load_context_boosts(scoring_path)
    penalties = load_context_penalties(scoring_path)
    composite_upgrades = load_composite_upgrades(scoring_path)

    boost_targets = _reverse_rule_targets(_BOOST_RULES_BY_ENTITY)
    penalty_targets = _reverse_rule_targets(_PENALTY_RULES_BY_ENTITY)
    rows: list[dict[str, Any]] = []

    for rule_name in sorted(boosts):
        rows.append(
            {
                "rule_id": f"context.boost.{rule_name}",
                "rule_name": rule_name,
                "rule_family": "boost",
                "configured_delta": boosts[rule_name],
                "configured_risk_upgrade": None,
                "target_entities": boost_targets.get(rule_name, ()),
                "effect_scope": "candidate_score",
                "policy_interaction": _policy_interaction_for_rule(rule_name, "boost"),
                "term_group": _FIELD_LABEL_GROUP_BY_RULE.get(rule_name),
                "owner": "configs/scoring.yaml:context_boosts + ContextScorer._evaluate_boost",
                "metric_scopes": ["candidate_level", "actionable_level"],
                "raw_value_logged": False,
            }
        )

    for rule_name in sorted(penalties):
        targets = penalty_targets.get(rule_name, ())
        if rule_name == _EXAMPLE_PENALTY_RULE:
            targets = ("ALL_CANDIDATES",)
        rows.append(
            {
                "rule_id": f"context.penalty.{rule_name}",
                "rule_name": rule_name,
                "rule_family": "penalty",
                "configured_delta": penalties[rule_name],
                "configured_risk_upgrade": None,
                "target_entities": targets,
                "effect_scope": "candidate_score",
                "policy_interaction": _policy_interaction_for_rule(rule_name, "penalty"),
                "term_group": _NEGATIVE_GROUP_BY_RULE.get(rule_name),
                "owner": "configs/scoring.yaml:context_penalties + ContextScorer._evaluate_penalty",
                "metric_scopes": ["candidate_level", "actionable_level"],
                "raw_value_logged": False,
            }
        )

    for peer_entity in _composite_reason_entities(composite_upgrades):
        related_keys = [
            _composite_key_to_string(key)
            for key in composite_upgrades
            if peer_entity in key
        ]
        target_entities = sorted(
            entity
            for key in composite_upgrades
            if peer_entity in key
            for entity in key
            if entity != peer_entity
        )
        rows.append(
            {
                "rule_id": f"context.composite.{peer_entity}",
                "rule_name": peer_entity,
                "rule_family": "composite",
                "configured_delta": None,
                "configured_risk_upgrade": sorted(
                    {composite_upgrades[key] for key in composite_upgrades if peer_entity in key}
                ),
                "target_entities": target_entities,
                "effect_scope": "composite_status_and_policy_action",
                "policy_interaction": "policy.composite.mask via is_composite",
                "term_group": None,
                "owner": "configs/scoring.yaml:single_turn_composite.upgrades + ContextScorer composite marking",
                "related_composite_rules": sorted(related_keys),
                "metric_scopes": ["candidate_level", "actionable_level"],
                "raw_value_logged": False,
            }
        )

    return {
        "report_type": "ContextRuleInventory",
        "version": "v0.2-single-turn",
        "phase": "Execution Phase 1. Baseline Evidence MVP",
        "scope": "M4 deterministic context scorer",
        "runtime_scoring_behavior_changed": False,
        "raw_value_logged": False,
        "rule_count": len(rows),
        "rules": sorted(rows, key=lambda row: row["rule_id"]),
        "generated_at": _now(),
    }


def default_existing_dataset_specs(
    project_root: Path = PROJECT_ROOT,
) -> tuple[DatasetSpec, ...]:
    """Return the existing labeled datasets available for Phase 1 evidence."""

    data_root = project_root / "data" / "eval"
    return (
        DatasetSpec("hard_cases_v0", data_root / "hard_cases_v0.jsonl"),
        _stage_dataset_spec(data_root, "stage1_person_name_expanded"),
        _stage_dataset_spec(data_root, "stage2_contact_expanded"),
        _stage_dataset_spec(data_root, "stage3_address_expanded"),
        _stage_dataset_spec(data_root, "stage4_corporate_rrn_expanded"),
        _stage_dataset_spec(data_root, "stage5_numeric_identifier_expanded"),
        DatasetSpec(
            "release_gate_v0_2_5000",
            data_root / "generated" / "release_gate_v0_2_5000.jsonl",
        ),
    )


def build_existing_context_rule_evidence(
    project_root: Path = PROJECT_ROOT,
    *,
    dataset_specs: tuple[DatasetSpec, ...] | None = None,
    minimum_support: int = DEFAULT_MINIMUM_SUPPORT,
) -> EvidenceBuildResult:
    """Run current pipeline on existing data and aggregate context evidence.

    The returned payload contains no case text, span text, raw offsets, hashes,
    or token maps. It only stores aggregate counts and rule identifiers.
    """

    inventory = build_context_rule_inventory(project_root)
    known_rule_ids = {row["rule_id"] for row in inventory["rules"]}
    rule_counts = {
        rule_id: _empty_rule_counter()
        for rule_id in known_rule_ids
    }
    entity_totals: dict[str, Counter[str]] = defaultdict(Counter)
    dataset_summaries: list[dict[str, Any]] = []
    missing_datasets: list[dict[str, str]] = []
    unknown_context_reason_codes: Counter[str] = Counter()
    loaded_cases: list[EvaluationCase] = []
    raw_pii_counts = Counter()

    specs = dataset_specs or default_existing_dataset_specs(project_root)
    pipeline = GuardrailPipeline.from_config_dir(project_root / "configs")
    runner = EvaluationRunner(pipeline)

    for spec in specs:
        dataset_path = spec.path
        if not dataset_path.exists():
            missing_datasets.append(
                {
                    "dataset_id": spec.dataset_id,
                    "path": _safe_relpath(dataset_path, project_root),
                    "status": "missing",
                }
            )
            continue

        cases = load_jsonl_cases(dataset_path)
        loaded_cases.extend(cases)
        report = runner.evaluate(cases, dataset_id=spec.dataset_id)
        dataset_context_firing_count = 0

        raw_pii_counts["raw_pii_logging_count"] += report.raw_pii_logging_count
        raw_pii_counts["response_raw_value_logged_count"] += (
            report.response_raw_value_logged_count
        )
        raw_pii_counts["public_span_raw_value_logged_count"] += (
            report.public_span_raw_value_logged_count
        )
        raw_pii_counts["audit_event_raw_value_logged_count"] += (
            report.audit_event_raw_value_logged_count
        )

        for case_result in report.case_results:
            for match in case_result.matches:
                if match.actual is None:
                    continue
                actual = match.actual
                entity = actual.entity_type.value
                action = actual.action.value
                is_candidate_tp = match.match_type in {"exact", "partial"}
                is_candidate_fp = match.match_type == "spurious"
                is_actionable = actual.action in ACTIONABLE_ACTIONS

                if is_candidate_tp:
                    entity_totals[entity]["candidate_tp_total"] += 1
                    if is_actionable:
                        entity_totals[entity]["actionable_tp_total"] += 1
                elif is_candidate_fp:
                    entity_totals[entity]["candidate_fp_total"] += 1
                    if is_actionable:
                        entity_totals[entity]["actionable_fp_total"] += 1

                context_codes = _context_reason_codes(actual.reason_codes)
                dataset_context_firing_count += len(context_codes)
                for rule_id in context_codes:
                    if rule_id not in known_rule_ids:
                        unknown_context_reason_codes[rule_id] += 1
                        continue
                    counts = rule_counts[rule_id]
                    counts["fired_count"] += 1
                    counts["actions"][action] += 1
                    counts["datasets"][spec.dataset_id] += 1
                    entity_row = counts["entities"][entity]
                    entity_row["fired_count"] += 1
                    entity_row["actions"][action] += 1
                    if is_candidate_tp:
                        counts["tp_fired"] += 1
                        entity_row["tp_fired"] += 1
                        if is_actionable:
                            counts["actionable_tp_fired"] += 1
                            entity_row["actionable_tp_fired"] += 1
                    elif is_candidate_fp:
                        counts["fp_fired"] += 1
                        entity_row["fp_fired"] += 1
                        if is_actionable:
                            counts["actionable_fp_fired"] += 1
                            entity_row["actionable_fp_fired"] += 1

        dataset_summaries.append(
            {
                "dataset_id": spec.dataset_id,
                "path": _safe_relpath(dataset_path, project_root),
                "records_processed": report.records_processed,
                "spans_detected": report.spans_detected,
                "spans_masked": report.spans_masked,
                "context_rule_firing_count": dataset_context_firing_count,
                "raw_pii_logging_count": report.raw_pii_logging_count,
                "invalid_offset_count": report.invalid_offset_count,
                "ner_mode": report.ner_mode,
            }
        )

    rule_rows = [
        _evidence_row(
            inventory_row=row,
            counts=rule_counts[row["rule_id"]],
            entity_totals=entity_totals,
            minimum_support=minimum_support,
        )
        for row in inventory["rules"]
    ]
    verdict_counts = Counter(row["verdict"] for row in rule_rows)
    payload: dict[str, Any] = {
        "report_type": "ContextRuleEvidenceExistingData",
        "version": "v0.2-single-turn",
        "phase": "Execution Phase 1. Baseline Evidence MVP",
        "scope": "M4 deterministic context scorer",
        "runtime_scoring_behavior_changed": False,
        "score_delta_changed": False,
        "minimum_support": minimum_support,
        "smoothing_alpha": SMOOTHING_ALPHA,
        "evidence_interpretation": {
            "direction_evidence": "candidate TP/FP split and smoothed likelihood ratio",
            "magnitude_evidence": "not evaluated in Phase 1; no delta sweep performed",
            "action_evidence": "observed action counts only; no action delta sweep performed",
            "public_corpus_used_for_score_tuning": False,
        },
        "dataset_summaries": dataset_summaries,
        "missing_datasets": missing_datasets,
        "rule_count": len(rule_rows),
        "verdict_counts": dict(sorted(verdict_counts.items())),
        "rules": sorted(rule_rows, key=lambda row: row["rule_id"]),
        "unknown_context_reason_codes": [
            {"rule_id": rule_id, "fired_count": count}
            for rule_id, count in sorted(unknown_context_reason_codes.items())
        ],
        "raw_pii_safety": {
            "raw_value_logged": False,
            "raw_pii_logging_count": raw_pii_counts["raw_pii_logging_count"],
            "response_raw_value_logged_count": raw_pii_counts[
                "response_raw_value_logged_count"
            ],
            "public_span_raw_value_logged_count": raw_pii_counts[
                "public_span_raw_value_logged_count"
            ],
            "audit_event_raw_value_logged_count": raw_pii_counts[
                "audit_event_raw_value_logged_count"
            ],
            "report_raw_text_leak_count": 0,
            "status": "pass",
        },
        "generated_at": _now(),
    }
    update_evidence_payload_safety(payload, tuple(loaded_cases), [payload])
    return EvidenceBuildResult(payload=payload, cases=tuple(loaded_cases))


def update_evidence_payload_safety(
    payload: dict[str, Any],
    cases: tuple[EvaluationCase, ...],
    report_payloads: list[object],
) -> None:
    """Update raw-text leak count in-place without exposing matching literals."""

    leak_count = count_report_raw_text_leaks(report_payloads, cases)
    safety = payload["raw_pii_safety"]
    safety["report_raw_text_leak_count"] = leak_count
    safety["status"] = (
        "pass"
        if leak_count == 0
        and safety["raw_pii_logging_count"] == 0
        and safety["response_raw_value_logged_count"] == 0
        and safety["public_span_raw_value_logged_count"] == 0
        and safety["audit_event_raw_value_logged_count"] == 0
        else "fail"
    )


def render_inventory_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Context Rule Inventory v1",
        "",
        f"- report_type: `{payload['report_type']}`",
        f"- phase: `{payload['phase']}`",
        f"- runtime_scoring_behavior_changed: `{str(payload['runtime_scoring_behavior_changed']).lower()}`",
        f"- rule_count: `{payload['rule_count']}`",
        f"- raw_value_logged: `{str(payload['raw_value_logged']).lower()}`",
        "",
        "| Rule ID | Family | Delta | Risk Upgrade | Effect Scope | Target Entities | Policy Interaction |",
        "|---|---|---:|---|---|---|---|",
    ]
    for row in payload["rules"]:
        lines.append(
            "| {rule_id} | {family} | {delta} | {risk} | {scope} | {targets} | {policy} |".format(
                rule_id=row["rule_id"],
                family=row["rule_family"],
                delta=_display_value(row["configured_delta"]),
                risk=", ".join(row["configured_risk_upgrade"] or ()) or "n/a",
                scope=row["effect_scope"],
                targets=", ".join(row["target_entities"]) or "n/a",
                policy=row["policy_interaction"],
            )
        )
    lines.append("")
    lines.append("No raw span text, case text, raw URLs, hashes, or token maps are stored.")
    return "\n".join(lines) + "\n"


def render_existing_evidence_markdown(payload: dict[str, Any]) -> str:
    safety = payload["raw_pii_safety"]
    lines = [
        "# Existing Context Rule Evidence v1",
        "",
        f"- report_type: `{payload['report_type']}`",
        f"- phase: `{payload['phase']}`",
        f"- runtime_scoring_behavior_changed: `{str(payload['runtime_scoring_behavior_changed']).lower()}`",
        f"- score_delta_changed: `{str(payload['score_delta_changed']).lower()}`",
        f"- minimum_support: `{payload['minimum_support']}`",
        f"- raw_pii_safety_status: `{safety['status']}`",
        f"- report_raw_text_leak_count: `{safety['report_raw_text_leak_count']}`",
        "",
        "## Dataset Summary",
        "",
        "| Dataset | Records | Spans | Masked | Context Firings | Raw PII Logs | Invalid Offsets | NER Mode |",
        "|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload["dataset_summaries"]:
        lines.append(
            "| {dataset_id} | {records} | {spans} | {masked} | {firings} | {raw_logs} | {offsets} | {ner_mode} |".format(
                dataset_id=row["dataset_id"],
                records=row["records_processed"],
                spans=row["spans_detected"],
                masked=row["spans_masked"],
                firings=row["context_rule_firing_count"],
                raw_logs=row["raw_pii_logging_count"],
                offsets=row["invalid_offset_count"],
                ner_mode=row["ner_mode"],
            )
        )
    if payload["missing_datasets"]:
        lines.extend(["", "Missing datasets were skipped:"])
        for row in payload["missing_datasets"]:
            lines.append(f"- `{row['dataset_id']}` at `{row['path']}`")

    lines.extend(
        [
            "",
            "## Rule Evidence",
            "",
            "| Rule ID | Family | Delta | Fired | TP | FP | Actionable TP | Actionable FP | Verdict |",
            "|---|---|---:|---:|---:|---:|---:|---:|---|",
        ]
    )
    for row in payload["rules"]:
        lines.append(
            "| {rule_id} | {family} | {delta} | {fired} | {tp} | {fp} | {atp} | {afp} | {verdict} |".format(
                rule_id=row["rule_id"],
                family=row["rule_family"],
                delta=_display_value(row["configured_delta"]),
                fired=row["fired_count"],
                tp=row["candidate_metrics"]["tp_fired"],
                fp=row["candidate_metrics"]["fp_fired"],
                atp=row["actionable_metrics"]["actionable_tp_fired"],
                afp=row["actionable_metrics"]["actionable_fp_fired"],
                verdict=row["verdict"],
            )
        )
    lines.extend(
        [
            "",
            "Direction evidence is based on aggregate candidate TP/FP split.",
            "Magnitude evidence is intentionally not evaluated in Phase 1; no score delta changed.",
            "Action evidence is limited to observed action counts; no action delta sweep was performed.",
        ]
    )
    return "\n".join(lines) + "\n"


def _stage_dataset_spec(data_root: Path, dataset_id: str) -> DatasetSpec:
    generated_path = data_root / "generated" / f"{dataset_id}.jsonl"
    if generated_path.exists():
        return DatasetSpec(dataset_id, generated_path)
    return DatasetSpec(dataset_id, data_root / "markers" / f"{dataset_id}.jsonl")


def _empty_rule_counter() -> dict[str, Any]:
    return {
        "fired_count": 0,
        "tp_fired": 0,
        "fp_fired": 0,
        "actionable_tp_fired": 0,
        "actionable_fp_fired": 0,
        "actions": Counter(),
        "datasets": Counter(),
        "entities": defaultdict(_empty_entity_counter),
    }


def _empty_entity_counter() -> dict[str, Any]:
    return {
        "fired_count": 0,
        "tp_fired": 0,
        "fp_fired": 0,
        "actionable_tp_fired": 0,
        "actionable_fp_fired": 0,
        "actions": Counter(),
    }


def _evidence_row(
    *,
    inventory_row: dict[str, Any],
    counts: dict[str, Any],
    entity_totals: dict[str, Counter[str]],
    minimum_support: int,
) -> dict[str, Any]:
    denominator_entities = _denominator_entities(inventory_row, counts, entity_totals)
    denominator = _sum_entity_totals(denominator_entities, entity_totals)
    p_rule_given_tp = _smoothed_probability(
        counts["tp_fired"],
        denominator["candidate_tp_total"],
    )
    p_rule_given_fp = _smoothed_probability(
        counts["fp_fired"],
        denominator["candidate_fp_total"],
    )
    likelihood_ratio = _ratio(p_rule_given_tp, p_rule_given_fp)
    log_likelihood_ratio = (
        round(math.log(likelihood_ratio), 6)
        if likelihood_ratio is not None and likelihood_ratio > 0
        else None
    )
    precision_when_fired = _precision(counts["tp_fired"], counts["fp_fired"])
    actionable_precision_when_fired = _precision(
        counts["actionable_tp_fired"],
        counts["actionable_fp_fired"],
    )
    verdict = _initial_verdict(
        inventory_row=inventory_row,
        fired_count=counts["fired_count"],
        likelihood_ratio=likelihood_ratio,
        minimum_support=minimum_support,
    )

    return {
        "rule_id": inventory_row["rule_id"],
        "rule_family": inventory_row["rule_family"],
        "target_entities": inventory_row["target_entities"],
        "configured_delta": inventory_row["configured_delta"],
        "configured_risk_upgrade": inventory_row["configured_risk_upgrade"],
        "effect_scope": inventory_row["effect_scope"],
        "policy_interaction": inventory_row["policy_interaction"],
        "fired_count": counts["fired_count"],
        "candidate_metrics": {
            "tp_fired": counts["tp_fired"],
            "fp_fired": counts["fp_fired"],
            "candidate_tp_total_for_targets": denominator["candidate_tp_total"],
            "candidate_fp_total_for_targets": denominator["candidate_fp_total"],
            "p_rule_given_tp": p_rule_given_tp,
            "p_rule_given_fp": p_rule_given_fp,
            "likelihood_ratio": likelihood_ratio,
            "log_likelihood_ratio": log_likelihood_ratio,
            "precision_when_fired": precision_when_fired,
        },
        "actionable_metrics": {
            "actionable_tp_fired": counts["actionable_tp_fired"],
            "actionable_fp_fired": counts["actionable_fp_fired"],
            "actionable_precision_when_fired": actionable_precision_when_fired,
            "actionable_fp_delta": None,
            "action_counts": dict(sorted(counts["actions"].items())),
        },
        "entity_breakdown": _entity_breakdown(
            denominator_entities,
            counts,
            entity_totals,
        ),
        "dataset_firing_counts": dict(sorted(counts["datasets"].items())),
        "evidence_levels": {
            "direction_evidence": _direction_status(verdict),
            "magnitude_evidence": "not_evaluated_phase_1",
            "action_evidence": "observed_counts_only_no_delta_sweep",
        },
        "suggested_delta": None,
        "verdict": verdict,
        "raw_value_logged": False,
    }


def _entity_breakdown(
    denominator_entities: tuple[str, ...],
    counts: dict[str, Any],
    entity_totals: dict[str, Counter[str]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for entity in denominator_entities:
        entity_counts = counts["entities"].get(entity, _empty_entity_counter())
        totals = entity_totals.get(entity, Counter())
        p_rule_given_tp = _smoothed_probability(
            entity_counts["tp_fired"],
            totals["candidate_tp_total"],
        )
        p_rule_given_fp = _smoothed_probability(
            entity_counts["fp_fired"],
            totals["candidate_fp_total"],
        )
        rows.append(
            {
                "entity_type": entity,
                "fired_count": entity_counts["fired_count"],
                "tp_fired": entity_counts["tp_fired"],
                "fp_fired": entity_counts["fp_fired"],
                "actionable_tp_fired": entity_counts["actionable_tp_fired"],
                "actionable_fp_fired": entity_counts["actionable_fp_fired"],
                "candidate_tp_total": totals["candidate_tp_total"],
                "candidate_fp_total": totals["candidate_fp_total"],
                "p_rule_given_tp": p_rule_given_tp,
                "p_rule_given_fp": p_rule_given_fp,
                "likelihood_ratio": _ratio(p_rule_given_tp, p_rule_given_fp),
                "action_counts": dict(sorted(entity_counts["actions"].items())),
            }
        )
    return rows


def _initial_verdict(
    *,
    inventory_row: dict[str, Any],
    fired_count: int,
    likelihood_ratio: float | None,
    minimum_support: int,
) -> str:
    if inventory_row["rule_family"] == "composite":
        return "policy_only_rule"
    if fired_count < minimum_support or likelihood_ratio is None:
        return "insufficient_support"
    configured_delta = inventory_row["configured_delta"]
    if configured_delta is None or configured_delta == 0:
        return "policy_only_rule"
    if configured_delta > 0:
        return "tune_magnitude" if likelihood_ratio > 1.0 else "direction_mismatch"
    return "tune_magnitude" if likelihood_ratio < 1.0 else "direction_mismatch"


def _direction_status(verdict: str) -> str:
    if verdict == "tune_magnitude":
        return "direction_supported"
    if verdict == "direction_mismatch":
        return "direction_mismatch"
    if verdict == "policy_only_rule":
        return "policy_interaction_only"
    return "insufficient_support"


def _denominator_entities(
    inventory_row: dict[str, Any],
    counts: dict[str, Any],
    entity_totals: dict[str, Counter[str]],
) -> tuple[str, ...]:
    observed = set(counts["entities"].keys())
    targets = set(inventory_row["target_entities"])
    if "ALL_CANDIDATES" in targets:
        targets = set(entity_totals.keys())
    denominator_entities = observed | {entity for entity in targets if entity in entity_totals}
    return tuple(sorted(denominator_entities))


def _sum_entity_totals(
    entities: tuple[str, ...],
    entity_totals: dict[str, Counter[str]],
) -> Counter[str]:
    total: Counter[str] = Counter()
    for entity in entities:
        total.update(entity_totals.get(entity, Counter()))
    return total


def _context_reason_codes(reason_codes: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(
        sorted(
            {
                code
                for code in reason_codes
                if code.startswith(CONTEXT_REASON_PREFIXES)
            }
        )
    )


def _smoothed_probability(fired: int, total: int) -> float | None:
    if total <= 0:
        return None
    return round((fired + SMOOTHING_ALPHA) / (total + 2 * SMOOTHING_ALPHA), 6)


def _ratio(left: float | None, right: float | None) -> float | None:
    if left is None or right is None or right == 0:
        return None
    return round(left / right, 6)


def _precision(tp: int, fp: int) -> float | None:
    denominator = tp + fp
    if denominator == 0:
        return None
    return round(tp / denominator, 6)


def _reverse_rule_targets(
    mapping: dict[EntityType, tuple[str, ...]],
) -> dict[str, tuple[str, ...]]:
    result: dict[str, list[str]] = defaultdict(list)
    for entity, rules in mapping.items():
        for rule in rules:
            result[rule].append(entity.value)
    return {rule: tuple(sorted(entities)) for rule, entities in result.items()}


def _policy_interaction_for_rule(rule_name: str, family: str) -> str:
    if family == "boost":
        return "strong_context_can_enable_policy_context_mask"
    if rule_name in {
        "example_context",
        "example_keyword_for_person",
        "weather_context_for_person",
        "public_phone_context",
        "code_or_log_context",
        "organization_not_person",
    }:
        return "negative_context_can_enable_policy_pass"
    return "score_only_before_policy_thresholds"


def _composite_reason_entities(
    composite_upgrades: dict[frozenset[str], str],
) -> tuple[str, ...]:
    return tuple(sorted({entity for key in composite_upgrades for entity in key}))


def _composite_key_to_string(key: frozenset[str]) -> str:
    return "+".join(sorted(key))


def _display_value(value: object) -> str:
    if value is None:
        return "n/a"
    return str(value)


def _safe_relpath(path: Path, project_root: Path) -> str:
    try:
        return path.resolve().relative_to(project_root.resolve()).as_posix()
    except ValueError:
        return path.name


def _now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


def dumps_json(payload: dict[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
