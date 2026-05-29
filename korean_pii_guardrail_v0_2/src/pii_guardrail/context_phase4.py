"""Phase 4 context rule metrics, delta sweep, and policy audit reports."""

from __future__ import annotations

import json
import shutil
import tempfile
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .context_calibration import DATASET_VERSION, SPLITS
from .context_evidence import (
    DatasetSpec,
    build_context_rule_inventory,
    build_existing_context_rule_evidence,
    dumps_json,
)
from .dictionary_loader import load_context_boosts, load_context_penalties
from .evaluation_harness import (
    EvaluationReport,
    EvaluationRunner,
    count_report_raw_text_leaks,
    load_jsonl_cases,
)
from .pipeline import GuardrailPipeline


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PHASE4_MINIMUM_SUPPORT = 50
PHASE4_CANDIDATE_IMPACT_KEYS = (
    "spans_detected",
    "overall_precision",
    "overall_recall",
)
PHASE4_ACTION_IMPACT_KEYS = (
    "spans_masked",
    "actionable_precision",
    "actionable_recall",
    "high_risk_recall",
    "actionable_high_risk_recall",
)
CONTEXT_BAND_BY_LOGLR = (
    (2.0, "strong_positive", "strong_boost"),
    (1.0, "positive", "normal_boost"),
    (0.4, "weak_positive", "small_boost"),
    (-0.4, "neutral_or_mixed", "no_score_effect_or_review"),
    (-1.0, "weak_negative", "small_penalty"),
    (-2.0, "negative", "normal_penalty"),
)


@dataclass(frozen=True)
class Phase4BuildResult:
    rule_evidence: dict[str, Any]
    delta_sweep: dict[str, Any]
    tuning_markdown: str
    policy_markdown: str


def build_phase4_reports(project_root: Path = PROJECT_ROOT) -> Phase4BuildResult:
    """Build all Phase 4 reports without changing runtime config files."""

    rule_evidence = build_context_rule_evidence_v1(project_root)
    delta_sweep = build_context_delta_sweep_v1(project_root, rule_evidence)
    tuning_markdown = render_context_score_tuning_markdown(rule_evidence, delta_sweep)
    policy_markdown = render_context_policy_interaction_markdown(rule_evidence)
    return Phase4BuildResult(
        rule_evidence=rule_evidence,
        delta_sweep=delta_sweep,
        tuning_markdown=tuning_markdown,
        policy_markdown=policy_markdown,
    )


def build_context_rule_evidence_v1(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    dataset_specs = (
        *default_phase4_existing_dataset_specs(project_root),
        *context_calibration_dataset_specs(project_root),
    )
    evidence_result = build_existing_context_rule_evidence(
        project_root,
        dataset_specs=dataset_specs,
        minimum_support=PHASE4_MINIMUM_SUPPORT,
    )
    payload = evidence_result.payload
    payload["report_type"] = "ContextRuleEvidence"
    payload["phase"] = "Execution Phase 4. Rule Metrics and Delta Sweep"
    payload["minimum_support"] = PHASE4_MINIMUM_SUPPORT
    payload["score_delta_changed"] = False
    payload["runtime_scoring_behavior_changed"] = False
    payload["evidence_interpretation"] = {
        "direction_evidence": "candidate TP/FP split, smoothed LR/logLR, and precision_when_fired",
        "magnitude_evidence": "delta sweep report; proposed runtime changes require later review",
        "action_evidence": "action-level precision/recall comparison in delta sweep",
        "public_corpus_used_for_score_tuning": False,
    }
    domain_breakdown = build_calibration_domain_breakdown(project_root)
    for row in payload["rules"]:
        _add_precision_lift(row)
        metrics = row["candidate_metrics"]
        loglr = metrics.get("log_likelihood_ratio")
        row["direction_band"] = _direction_band(loglr)
        row["proposed_delta_band"] = _proposed_delta_band(loglr)
        row["domain_breakdown"] = domain_breakdown.get(row["rule_id"], [])
    update_payload_leak_safety(payload, project_root)
    return payload


def default_phase4_existing_dataset_specs(
    project_root: Path = PROJECT_ROOT,
) -> tuple[DatasetSpec, ...]:
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


def context_calibration_dataset_specs(
    project_root: Path = PROJECT_ROOT,
) -> tuple[DatasetSpec, ...]:
    data_root = project_root / "data" / "eval" / "generated"
    return tuple(
        DatasetSpec(
            f"{DATASET_VERSION}_{split}",
            data_root / f"{DATASET_VERSION}_{split}.jsonl",
        )
        for split in SPLITS
    )


def build_calibration_domain_breakdown(
    project_root: Path = PROJECT_ROOT,
) -> dict[str, list[dict[str, Any]]]:
    rows: dict[str, dict[tuple[str, str], Counter[str]]] = defaultdict(
        lambda: defaultdict(Counter)
    )
    pipeline = GuardrailPipeline.from_config_dir(project_root / "configs")
    runner = EvaluationRunner(pipeline)
    for spec in context_calibration_dataset_specs(project_root):
        if not spec.path.exists():
            continue
        records = [
            json.loads(line)
            for line in spec.path.read_text(encoding="utf-8").splitlines()
            if line.strip()
        ]
        cases = load_jsonl_cases(spec.path)
        report = runner.evaluate(cases, dataset_id=spec.dataset_id)
        metadata_by_id = {record["id"]: record for record in records}
        for case_result in report.case_results:
            metadata = metadata_by_id.get(case_result.case_id, {})
            domain = str(metadata.get("domain", "unknown"))
            bucket = str(metadata.get("bucket", "unknown"))
            for match in case_result.matches:
                if match.actual is None:
                    continue
                for rule_id in sorted(
                    code
                    for code in match.actual.reason_codes
                    if code.startswith(
                        ("context.boost.", "context.penalty.", "context.composite.")
                    )
                ):
                    row = rows[rule_id][(domain, bucket)]
                    row["fired_count"] += 1
                    if match.match_type in {"exact", "partial"}:
                        row["tp_fired"] += 1
                    elif match.match_type == "spurious":
                        row["fp_fired"] += 1
    return {
        rule_id: [
            {
                "domain": domain,
                "bucket": bucket,
                "fired_count": counts["fired_count"],
                "tp_fired": counts["tp_fired"],
                "fp_fired": counts["fp_fired"],
            }
            for (domain, bucket), counts in sorted(rule_rows.items())
        ]
        for rule_id, rule_rows in rows.items()
    }


def build_context_delta_sweep_v1(
    project_root: Path,
    rule_evidence: dict[str, Any],
) -> dict[str, Any]:
    boosts = load_context_boosts(project_root / "configs" / "scoring.yaml")
    penalties = load_context_penalties(project_root / "configs" / "scoring.yaml")
    rule_rows = rule_evidence["rules"]
    eligible = [row for row in rule_rows if _is_delta_sweep_eligible(row)]
    calibration_paths = {
        split: project_root
        / "data"
        / "eval"
        / "generated"
        / f"{DATASET_VERSION}_{split}.jsonl"
        for split in SPLITS
    }
    baseline_metrics = {
        split: _evaluate_config(project_root / "configs", path, f"baseline_{split}")
        for split, path in calibration_paths.items()
    }

    sweep_rows: list[dict[str, Any]] = []
    for row in eligible:
        rule_name = row["rule_id"].split(".")[-1]
        section = "context_boosts" if row["rule_family"] == "boost" else "context_penalties"
        current_delta = (
            boosts.get(rule_name)
            if row["rule_family"] == "boost"
            else penalties.get(rule_name)
        )
        if current_delta is None:
            continue
        candidates = _candidate_grid(row["rule_family"], current_delta)
        candidate_rows = []
        for candidate_delta in candidates:
            with tempfile.TemporaryDirectory(prefix="context_delta_") as tmp:
                config_dir = Path(tmp) / "configs"
                shutil.copytree(project_root / "configs", config_dir)
                _rewrite_context_delta(
                    config_dir / "scoring.yaml",
                    section=section,
                    rule_name=rule_name,
                    new_delta=candidate_delta,
                )
                metrics_by_split = {
                    split: _evaluate_config(config_dir, path, f"{row['rule_id']}_{split}")
                    for split, path in calibration_paths.items()
                }
            candidate_rows.append(
                {
                    "candidate_delta": candidate_delta,
                    "metrics_by_split": metrics_by_split,
                    "impact_deltas_by_split": _impact_deltas_by_split(
                        baseline_metrics,
                        metrics_by_split,
                    ),
                    "passes_release_constraints": _passes_release_constraints(
                        baseline_metrics,
                        metrics_by_split,
                    ),
                }
            )
        selected = _select_conservative_candidate(current_delta, candidate_rows)
        sweep_rows.append(
            {
                "rule_id": row["rule_id"],
                "rule_family": row["rule_family"],
                "current_delta": current_delta,
                "candidate_grid": candidates,
                "candidate_results": candidate_rows,
                "selected_delta": selected,
                "config_change_proposed": selected != current_delta,
                "selection_reason": (
                    "conservative_current_delta_kept"
                    if selected == current_delta
                    else "candidate_passed_dev_constraints"
                ),
            }
        )

    return {
        "report_type": "ContextDeltaSweep",
        "version": "v0.2-single-turn",
        "phase": "Execution Phase 4. Rule Metrics and Delta Sweep",
        "runtime_scoring_behavior_changed": False,
        "score_delta_changed": False,
        "public_corpus_used_for_score_tuning": False,
        "baseline_metrics": baseline_metrics,
        "eligible_rule_count": len(eligible),
        "swept_rule_count": len(sweep_rows),
        "rules": sweep_rows,
        "config_changes_proposed": [
            {
                "rule_id": row["rule_id"],
                "current_delta": row["current_delta"],
                "selected_delta": row["selected_delta"],
            }
            for row in sweep_rows
            if row["config_change_proposed"]
        ],
        "unchanged_rule_reasons": [
            {
                "rule_id": row["rule_id"],
                "reason": (
                    "policy_only_rule"
                    if row["rule_family"] == "composite"
                    else "insufficient_support_or_direction_review"
                ),
            }
            for row in rule_rows
            if not _is_delta_sweep_eligible(row)
        ],
    }


def render_context_score_tuning_markdown(
    rule_evidence: dict[str, Any],
    delta_sweep: dict[str, Any],
) -> str:
    lines = [
        "# Context Score Tuning v1",
        "",
        "- phase: `Execution Phase 4. Rule Metrics and Delta Sweep`",
        "- runtime_scoring_behavior_changed: `false`",
        "- score_delta_changed: `false`",
        "- public_corpus_used_for_score_tuning: `false`",
        f"- eligible_rule_count: `{delta_sweep['eligible_rule_count']}`",
        f"- config_changes_proposed: `{len(delta_sweep['config_changes_proposed'])}`",
        "",
        (
            "Direction evidence comes from LR/logLR and precision_when_fired. "
            "Magnitude evidence comes from the delta sweep. Action evidence "
            "comes from action-level metrics in the sweep."
        ),
        "",
        "## Proposed Config Changes",
        "",
    ]
    if not delta_sweep["config_changes_proposed"]:
        lines.append("No runtime scoring config changes are proposed in Phase 4.")
    else:
        lines.extend(["| Rule | Current | Proposed |", "|---|---:|---:|"])
        for row in delta_sweep["config_changes_proposed"]:
            lines.append(
                f"| {row['rule_id']} | {row['current_delta']} | {row['selected_delta']} |"
            )

    lines.extend(
        [
            "",
            "## Delta Sweep Summary",
            "",
            "| Rule | Current | Selected | Reason | Candidates |",
            "|---|---:|---:|---|---:|",
        ]
    )
    for row in delta_sweep["rules"]:
        lines.append(
            "| {rule} | {current} | {selected} | {reason} | {count} |".format(
                rule=row["rule_id"],
                current=row["current_delta"],
                selected=row["selected_delta"],
                reason=row["selection_reason"],
                count=len(row["candidate_results"]),
            )
        )

    lines.extend(
        [
            "",
            "## Rule Summary",
            "",
            "| Rule | Fired | logLR | Precision Lift | Direction Band | Proposed Delta Band | Verdict |",
            "|---|---:|---:|---:|---|---|---|",
        ]
    )
    for row in rule_evidence["rules"]:
        metrics = row["candidate_metrics"]
        lines.append(
            "| {rule} | {fired} | {loglr} | {lift} | {direction} | {band} | {verdict} |".format(
                rule=row["rule_id"],
                fired=row["fired_count"],
                loglr=_display(metrics.get("log_likelihood_ratio")),
                lift=_display(metrics.get("precision_lift")),
                direction=row["direction_band"],
                band=row["proposed_delta_band"],
                verdict=row["verdict"],
            )
        )
    return "\n".join(lines) + "\n"


def render_context_policy_interaction_markdown(
    rule_evidence: dict[str, Any],
) -> str:
    lines = [
        "# Context Policy Interaction v1",
        "",
        "- phase: `Execution Phase 4. Rule Metrics and Delta Sweep`",
        "- score deltas and policy overrides are separated.",
        "- policy-only rules are not forced into score calibration.",
        "",
        "| Rule | Effect Scope | Policy Interaction | Action Counts | Calibration Domains |",
        "|---|---|---|---|---|",
    ]
    for row in rule_evidence["rules"]:
        action_counts = row["actionable_metrics"].get("action_counts", {})
        domains = sorted({item["domain"] for item in row.get("domain_breakdown", [])})
        lines.append(
            "| {rule} | {scope} | {policy} | {actions} | {domains} |".format(
                rule=row["rule_id"],
                scope=row["effect_scope"],
                policy=row["policy_interaction"],
                actions=", ".join(
                    f"{key}:{value}" for key, value in action_counts.items()
                )
                or "none",
                domains=", ".join(domains) or "none",
            )
        )
    return "\n".join(lines) + "\n"


def write_phase4_reports(
    project_root: Path = PROJECT_ROOT,
) -> tuple[Phase4BuildResult, dict[str, Path]]:
    result = build_phase4_reports(project_root)
    paths = {
        "rule_evidence_json": project_root / "reports" / "context_rule_evidence_v1.json",
        "rule_evidence_md": project_root / "reports" / "context_rule_evidence_v1.md",
        "delta_sweep_json": project_root / "reports" / "context_delta_sweep_v1.json",
        "tuning_md": project_root / "reports" / "context_score_tuning_v1.md",
        "policy_md": project_root / "reports" / "context_policy_interaction_v1.md",
    }
    paths["rule_evidence_json"].write_text(
        dumps_json(result.rule_evidence),
        encoding="utf-8",
    )
    paths["rule_evidence_md"].write_text(
        _render_rule_evidence_markdown(result.rule_evidence),
        encoding="utf-8",
    )
    paths["delta_sweep_json"].write_text(
        dumps_json(result.delta_sweep),
        encoding="utf-8",
    )
    paths["tuning_md"].write_text(result.tuning_markdown, encoding="utf-8")
    paths["policy_md"].write_text(result.policy_markdown, encoding="utf-8")
    return result, paths


def update_payload_leak_safety(payload: dict[str, Any], project_root: Path) -> None:
    cases = []
    for spec in (
        *default_phase4_existing_dataset_specs(project_root),
        *context_calibration_dataset_specs(project_root),
    ):
        if spec.path.exists():
            cases.extend(load_jsonl_cases(spec.path))
    leak_count = count_report_raw_text_leaks([payload], cases)
    payload["raw_pii_safety"]["report_raw_text_leak_count"] = leak_count
    safety_checks = (
        leak_count == 0,
        payload["raw_pii_safety"]["raw_pii_logging_count"] == 0,
        payload["raw_pii_safety"]["response_raw_value_logged_count"] == 0,
        payload["raw_pii_safety"]["public_span_raw_value_logged_count"] == 0,
        payload["raw_pii_safety"]["audit_event_raw_value_logged_count"] == 0,
        payload["raw_pii_safety"]["raw_value_logged"] is False,
    )
    payload["raw_pii_safety"]["status"] = "pass" if all(safety_checks) else "fail"


def _add_precision_lift(row: dict[str, Any]) -> None:
    metrics = row["candidate_metrics"]
    target_baseline_precision = _precision(
        metrics["candidate_tp_total_for_targets"],
        metrics["candidate_fp_total_for_targets"],
    )
    precision_when_fired = metrics.get("precision_when_fired")
    metrics["target_baseline_precision"] = target_baseline_precision
    metrics["precision_lift"] = _ratio_or_none(
        precision_when_fired,
        target_baseline_precision,
    )


def _evaluate_config(
    config_dir: Path,
    dataset_path: Path,
    dataset_id: str,
) -> dict[str, Any]:
    report = EvaluationRunner(
        GuardrailPipeline.from_config_dir(config_dir)
    ).evaluate(load_jsonl_cases(dataset_path), dataset_id=dataset_id)
    return _safe_metric_summary(report)


def _safe_metric_summary(report: EvaluationReport) -> dict[str, Any]:
    overall = report.overall_metrics
    actionable = report.actionable_overall_metrics
    return {
        "records_processed": report.records_processed,
        "spans_detected": report.spans_detected,
        "spans_masked": report.spans_masked,
        "overall_precision": round(overall.precision, 4),
        "overall_recall": round(overall.recall, 4),
        "actionable_precision": round(actionable.precision, 4),
        "actionable_recall": round(actionable.recall, 4),
        "high_risk_recall": round(report.high_risk_recall, 4),
        "actionable_high_risk_recall": round(report.actionable_high_risk_recall, 4),
        "raw_pii_logging_count": report.raw_pii_logging_count,
        "invalid_offset_count": report.invalid_offset_count,
    }


def _impact_deltas_by_split(
    baseline: dict[str, dict[str, Any]],
    candidate: dict[str, dict[str, Any]],
) -> dict[str, dict[str, dict[str, float | int]]]:
    return {
        split: {
            "candidate_level": _metric_deltas(
                baseline[split],
                candidate[split],
                PHASE4_CANDIDATE_IMPACT_KEYS,
            ),
            "action_level": _metric_deltas(
                baseline[split],
                candidate[split],
                PHASE4_ACTION_IMPACT_KEYS,
            ),
        }
        for split in ("train", "dev", "test")
    }


def _metric_deltas(
    baseline: dict[str, Any],
    candidate: dict[str, Any],
    keys: tuple[str, ...],
) -> dict[str, float | int]:
    deltas: dict[str, float | int] = {}
    for key in keys:
        delta = candidate[key] - baseline[key]
        deltas[f"{key}_delta"] = (
            round(delta, 4)
            if isinstance(baseline[key], float) or isinstance(candidate[key], float)
            else delta
        )
    return deltas


def _passes_release_constraints(
    baseline: dict[str, dict[str, Any]],
    candidate: dict[str, dict[str, Any]],
) -> bool:
    for split in ("train", "dev"):
        base = baseline[split]
        row = candidate[split]
        if row["raw_pii_logging_count"] != 0 or row["invalid_offset_count"] != 0:
            return False
        if row["actionable_high_risk_recall"] < base["actionable_high_risk_recall"]:
            return False
        if row["high_risk_recall"] < base["high_risk_recall"]:
            return False
    return True


def _select_conservative_candidate(
    current_delta: float,
    candidate_rows: list[dict[str, Any]],
) -> float:
    if any(row["candidate_delta"] == current_delta for row in candidate_rows):
        return current_delta
    passing = [row for row in candidate_rows if row["passes_release_constraints"]]
    if not passing:
        return current_delta
    return min(passing, key=lambda row: abs(row["candidate_delta"] - current_delta))[
        "candidate_delta"
    ]


def _is_delta_sweep_eligible(row: dict[str, Any]) -> bool:
    return (
        row["rule_family"] in {"boost", "penalty"}
        and row["fired_count"] >= PHASE4_MINIMUM_SUPPORT
        and row["verdict"] == "tune_magnitude"
    )


def _candidate_grid(rule_family: str, current_delta: float) -> list[float]:
    if rule_family == "boost":
        if current_delta >= 0.20:
            grid = [0.20, 0.25, 0.30, 0.35]
        else:
            grid = [0.10, 0.15, 0.20, 0.25, 0.30]
    else:
        if current_delta <= -0.25:
            grid = [-0.25, -0.30, -0.35, -0.40]
        else:
            grid = [-0.10, -0.15, -0.20, -0.25, -0.30]
    return sorted({round(value, 2) for value in (*grid, current_delta)})


def _rewrite_context_delta(
    path: Path,
    *,
    section: str,
    rule_name: str,
    new_delta: float,
) -> None:
    lines = path.read_text(encoding="utf-8").splitlines()
    in_section = False
    rewritten: list[str] = []
    replaced = False
    for line in lines:
        stripped = line.strip()
        if not line.startswith(" "):
            in_section = stripped == f"{section}:"
            rewritten.append(line)
            continue
        if in_section and line.startswith("  ") and not line.startswith("    "):
            key, sep, _ = stripped.partition(":")
            if sep and key == rule_name:
                rewritten.append(f"  {rule_name}: {new_delta:.2f}")
                replaced = True
                continue
        rewritten.append(line)
    if not replaced:
        raise ValueError(f"Rule not found in scoring config: {rule_name}")
    path.write_text("\n".join(rewritten) + "\n", encoding="utf-8")


def _direction_band(loglr: float | None) -> str:
    if loglr is None:
        return "insufficient_support"
    if loglr <= -2.0:
        return "strong_negative"
    for threshold, band, _ in CONTEXT_BAND_BY_LOGLR:
        if loglr >= threshold:
            return band
    return "negative"


def _proposed_delta_band(loglr: float | None) -> str:
    if loglr is None:
        return "insufficient_support"
    if loglr <= -2.0:
        return "strong_penalty"
    for threshold, _, band in CONTEXT_BAND_BY_LOGLR:
        if loglr >= threshold:
            return band
    return "normal_penalty"


def _render_rule_evidence_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Context Rule Evidence v1",
        "",
        f"- phase: `{payload['phase']}`",
        f"- rule_count: `{payload['rule_count']}`",
        f"- raw_pii_safety_status: `{payload['raw_pii_safety']['status']}`",
        f"- report_raw_text_leak_count: `{payload['raw_pii_safety']['report_raw_text_leak_count']}`",
        "",
        "| Rule | Fired | TP | FP | LR | logLR | Precision | Precision Lift | Verdict |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in payload["rules"]:
        metrics = row["candidate_metrics"]
        lines.append(
            (
                "| {rule} | {fired} | {tp} | {fp} | {lr} | {loglr} | "
                "{precision} | {lift} | {verdict} |"
            ).format(
                rule=row["rule_id"],
                fired=row["fired_count"],
                tp=metrics["tp_fired"],
                fp=metrics["fp_fired"],
                lr=_display(metrics.get("likelihood_ratio")),
                loglr=_display(metrics.get("log_likelihood_ratio")),
                precision=_display(metrics.get("precision_when_fired")),
                lift=_display(metrics.get("precision_lift")),
                verdict=row["verdict"],
            )
        )
    return "\n".join(lines) + "\n"


def _stage_dataset_spec(data_root: Path, dataset_id: str) -> DatasetSpec:
    generated_path = data_root / "generated" / f"{dataset_id}.jsonl"
    if generated_path.exists():
        return DatasetSpec(dataset_id, generated_path)
    return DatasetSpec(dataset_id, data_root / "markers" / f"{dataset_id}.jsonl")


def _display(value: Any) -> str:
    if value is None:
        return "n/a"
    return str(value)


def _precision(tp_count: int, fp_count: int) -> float | None:
    denominator = tp_count + fp_count
    if denominator == 0:
        return None
    return round(tp_count / denominator, 6)


def _ratio_or_none(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator in (None, 0):
        return None
    return round(numerator / denominator, 6)
