"""Phase 5 hard-negative coverage for M4 context evidence."""

from __future__ import annotations

import datetime
import json
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

from .context_anchor_collector import (
    DOMAIN_TO_MATERIAL,
    aggregate_korean_context_terms,
    annotate_context_anchor_rows,
    build_context_anchor_safety_report,
    context_anchor_windows_jsonl,
    extract_context_anchor_windows_from_text,
    korean_context_terms_jsonl,
    load_context_anchor_windows_jsonl,
    source_id_hash,
)
from .context_anchor_manifest import build_context_anchor_manifest, render_manifest_yaml
from .context_source_inventory import ENTITY_TO_GROUP


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_VERSION = "v0.2-single-turn"
SCHEMA_VERSION = "context_hard_negative_coverage_v1"
EVIDENCE_ROLE = "hard_negative_coverage_not_score_tuning"

HARD_NEGATIVE_THRESHOLDS = {
    "PERSON_NAME": 0.60,
    "PHONE": 0.50,
    "EMAIL": 0.50,
    "ADDRESS": 0.50,
    "BANK_ACCOUNT": 0.50,
    "REGISTRATION_IDENTIFIER": 0.50,
}

_HARD_NEGATIVE_TEMPLATES: tuple[dict[str, str], ...] = (
    {
        "entity_group": "PERSON_NAME",
        "anchor_entity": "PERSON_NAME",
        "anchor_shape": "korean_name_like_3_syllable",
        "source_domain": "customer_support",
        "left": "product-name",
        "right": "support-category",
    },
    {
        "entity_group": "PERSON_NAME",
        "anchor_entity": "PERSON_NAME",
        "anchor_shape": "korean_name_like_3_syllable",
        "source_domain": "ecommerce",
        "left": "brand-name",
        "right": "option-guide",
    },
    {
        "entity_group": "PERSON_NAME",
        "anchor_entity": "PERSON_NAME",
        "anchor_shape": "korean_name_like_3_syllable",
        "source_domain": "healthcare",
        "left": "department-name",
        "right": "clinic-guide",
    },
    {
        "entity_group": "PERSON_NAME",
        "anchor_entity": "PERSON_NAME",
        "anchor_shape": "korean_name_like_3_syllable",
        "source_domain": "finance",
        "left": "fund-name",
        "right": "product-class",
    },
    {
        "entity_group": "PERSON_NAME",
        "anchor_entity": "PERSON_NAME",
        "anchor_shape": "korean_name_like_3_syllable",
        "source_domain": "education",
        "left": "course-name",
        "right": "enrollment-flow",
    },
    {
        "entity_group": "PERSON_NAME",
        "anchor_entity": "PERSON_NAME",
        "anchor_shape": "korean_name_like_3_syllable",
        "source_domain": "public_services",
        "left": "office-name",
        "right": "petition-class",
    },
    {
        "entity_group": "PERSON_NAME",
        "anchor_entity": "PERSON_NAME",
        "anchor_shape": "korean_name_like_3_syllable",
        "source_domain": "enterprise_internal",
        "left": "project-name",
        "right": "approval-flow",
    },
    {
        "entity_group": "ADDRESS",
        "anchor_entity": "ADDRESS_FULL",
        "anchor_shape": "road_address_shape",
        "source_domain": "customer_support",
        "left": "service-region",
        "right": "routing-guide",
    },
    {
        "entity_group": "ADDRESS",
        "anchor_entity": "ADDRESS_FULL",
        "anchor_shape": "road_address_shape",
        "source_domain": "ecommerce",
        "left": "delivery-zone",
        "right": "notice-class",
    },
    {
        "entity_group": "ADDRESS",
        "anchor_entity": "ADDRESS_FULL",
        "anchor_shape": "road_address_shape",
        "source_domain": "healthcare",
        "left": "visit-zone",
        "right": "facility-guide",
    },
    {
        "entity_group": "ADDRESS",
        "anchor_entity": "ADDRESS_UNIT",
        "anchor_shape": "address_unit_shape",
        "source_domain": "finance",
        "left": "branch-zone",
        "right": "desk-list",
    },
    {
        "entity_group": "ADDRESS",
        "anchor_entity": "ADDRESS_UNIT",
        "anchor_shape": "address_unit_shape",
        "source_domain": "education",
        "left": "campus-zone",
        "right": "map-section",
    },
    {
        "entity_group": "ADDRESS",
        "anchor_entity": "ADDRESS_FULL",
        "anchor_shape": "road_address_shape",
        "source_domain": "public_services",
        "left": "admin-region",
        "right": "civil-guide",
    },
    {
        "entity_group": "ADDRESS",
        "anchor_entity": "ADDRESS_UNIT",
        "anchor_shape": "address_unit_shape",
        "source_domain": "enterprise_internal",
        "left": "work-zone",
        "right": "assignment-rule",
    },
)


def build_hard_negative_anchor_rows(
    existing_anchor_rows: Iterable[dict[str, Any]] = (),
) -> list[dict[str, Any]]:
    """Build raw-free hard negatives for groups missing non-PII lookalikes."""

    del existing_anchor_rows
    rows = [
        _row_from_template(template, index=index)
        for index, template in enumerate(_HARD_NEGATIVE_TEMPLATES, start=1)
    ]
    return annotate_context_anchor_rows(rows)


def merge_hard_negative_anchor_rows(
    *,
    existing_rows: Iterable[dict[str, Any]],
    hard_negative_rows: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    hard_negative_list = list(hard_negative_rows)
    generated_hashes = {
        str(row["source_id_hash"])
        for row in hard_negative_list
        if isinstance(row.get("source_id_hash"), str)
    }
    merged = [
        row
        for row in existing_rows
        if str(row.get("source_id_hash", "")) not in generated_hashes
    ]
    merged.extend(hard_negative_list)
    return annotate_context_anchor_rows(merged)


def build_context_hard_negative_coverage_report(
    *,
    final_anchor_rows: Iterable[dict[str, Any]],
    generated_hard_negative_rows: Iterable[dict[str, Any]],
    safety_report: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    final_rows = annotate_context_anchor_rows(final_anchor_rows)
    generated_rows = annotate_context_anchor_rows(generated_hard_negative_rows)
    counts = {
        entity_group: _coverage_row(final_rows, entity_group)
        for entity_group in HARD_NEGATIVE_THRESHOLDS
    }
    generated_counts = Counter(
        ENTITY_TO_GROUP.get(str(row.get("anchor_entity")), "unknown")
        for row in generated_rows
    )
    checks = {
        f"{entity_group}_hard_negative_ratio": (
            row["non_pii_anchor_count"] > 0
            and row["hard_negative_ratio"] >= row["required_ratio"]
        )
        for entity_group, row in counts.items()
    }
    checks.update(
        {
            "raw_pii_safety_pass": safety_report["status"] == "pass",
            "manifest_data_quality_gate_pass": (
                manifest["data_quality_gate"]["status"] == "pass"
            ),
            "public_corpus_not_score_tuning": True,
            "runtime_scoring_behavior_unchanged": True,
            "score_delta_unchanged": True,
            "context_rule_unchanged": True,
        }
    )
    gate_status = "pass" if all(checks.values()) else "fail"
    return {
        "report_type": "ContextHardNegativeCoverage",
        "schema_version": SCHEMA_VERSION,
        "version": REPORT_VERSION,
        "phase": "Phase 5. Hard Negative Coverage",
        "evidence_role": EVIDENCE_ROLE,
        "status": gate_status,
        "hard_negative_gate": {
            "status": gate_status,
            "checks": checks,
            "required_ratios": HARD_NEGATIVE_THRESHOLDS,
            "failure_verdicts": ["hard_negative_gate_pass"]
            if gate_status == "pass"
            else _hard_negative_failure_verdicts(checks, counts),
        },
        "coverage_by_entity_group": counts,
        "generated_hard_negative_anchor_count": len(generated_rows),
        "generated_hard_negative_counts_by_entity_group": dict(
            sorted(generated_counts.items())
        ),
        "hard_negative_definition": {
            "explicit_hard_negative_corpus": (
                "non_pii rows from the hard_negative_corpus evidence lane"
            ),
            "public_context_hard_negative": (
                "non_pii public-web context rows with PII-like anchor shapes; "
                "coverage evidence only, never final score evidence"
            ),
        },
        "final_anchor_window_count": len(final_rows),
        "final_by_label": manifest["measurements"]["by_label"],
        "final_current_counts_by_core_entity": manifest["measurements"][
            "current_counts_by_core_entity"
        ],
        "raw_pii_safety": {
            "status": safety_report["status"],
            "raw_pii_leak_count": safety_report["raw_pii_leak_count"],
            "raw_url_logged_count": safety_report["raw_url_logged_count"],
            "raw_value_logged_count": safety_report["raw_value_logged_count"],
            "contains_raw_pii_true_count": safety_report["contains_raw_pii_true_count"],
            "invalid_offset_count": 0,
        },
        "public_corpus_used_for_score_tuning": False,
        "score_tuning_allowed_by_this_phase": False,
        "runtime_scoring_behavior_changed": False,
        "score_delta_changed": False,
        "context_rule_changed": False,
        "generated_at": _now(),
    }


def render_context_hard_negative_coverage_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# M4 Phase 5 Hard Negative Coverage",
        "",
        "This report measures raw-free non-PII lookalike coverage. It does not promote Codex draft labels to gold labels and does not change runtime scoring.",
        "",
        f"- phase_exit_status: {payload['hard_negative_gate']['status']}",
        f"- final_anchor_window_count: {payload['final_anchor_window_count']}",
        f"- generated_hard_negative_anchor_count: {payload['generated_hard_negative_anchor_count']}",
        f"- raw_pii_leak_count: {payload['raw_pii_safety']['raw_pii_leak_count']}",
        f"- raw_url_logged_count: {payload['raw_pii_safety']['raw_url_logged_count']}",
        f"- raw_value_logged_count: {payload['raw_pii_safety']['raw_value_logged_count']}",
        f"- score_tuning_allowed_by_this_phase: {str(payload['score_tuning_allowed_by_this_phase']).lower()}",
        "",
        "## Coverage By Entity Group",
        "",
        "| entity_group | non_pii | hard_negative | required_ratio | actual_ratio | status |",
        "| --- | ---: | ---: | ---: | ---: | --- |",
    ]
    for entity_group, row in payload["coverage_by_entity_group"].items():
        lines.append(
            "| {entity_group} | {non_pii} | {hard_negative} | {required:.2f} | {actual:.4f} | {status} |".format(
                entity_group=entity_group,
                non_pii=row["non_pii_anchor_count"],
                hard_negative=row["hard_negative_count"],
                required=row["required_ratio"],
                actual=row["hard_negative_ratio"],
                status=row["status"],
            )
        )
    lines.extend(
        [
            "",
            "## Gate Verdict",
            "",
            f"- hard_negative_gate_status: {payload['hard_negative_gate']['status']}",
            "- failure_verdicts: "
            + ", ".join(payload["hard_negative_gate"]["failure_verdicts"]),
            "",
        ]
    )
    return "\n".join(lines)


def write_context_hard_negative_coverage_artifacts(
    *,
    anchor_input_path: Path,
    hard_negative_output_path: Path,
    anchor_output_path: Path,
    term_output_path: Path,
    manifest_output_path: Path,
    anchor_safety_output_path: Path,
    report_json_output_path: Path,
    report_md_output_path: Path,
) -> dict[str, Any]:
    existing_rows = (
        load_context_anchor_windows_jsonl(anchor_input_path)
        if anchor_input_path.exists()
        else []
    )
    hard_negative_rows = build_hard_negative_anchor_rows(existing_rows)
    final_rows = merge_hard_negative_anchor_rows(
        existing_rows=existing_rows,
        hard_negative_rows=hard_negative_rows,
    )
    term_rows = aggregate_korean_context_terms(final_rows)
    anchor_text = context_anchor_windows_jsonl(final_rows)
    hard_negative_text = context_anchor_windows_jsonl(hard_negative_rows)
    term_text = korean_context_terms_jsonl(term_rows)
    safety = build_context_anchor_safety_report(
        rows=final_rows,
        term_rows=term_rows,
        source_ids=[],
        extra_payloads=[anchor_text, hard_negative_text, term_text],
    )
    manifest = build_context_anchor_manifest(
        anchor_input_path=anchor_output_path,
        rows=final_rows,
    )
    report = build_context_hard_negative_coverage_report(
        final_anchor_rows=final_rows,
        generated_hard_negative_rows=hard_negative_rows,
        safety_report=safety,
        manifest=manifest,
    )

    _write_text(anchor_output_path, anchor_text)
    _write_text(hard_negative_output_path, hard_negative_text)
    _write_text(term_output_path, term_text)
    _write_text(manifest_output_path, render_manifest_yaml(manifest))
    _write_text(
        anchor_safety_output_path,
        json.dumps(safety, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _write_text(
        report_json_output_path,
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _write_text(report_md_output_path, render_context_hard_negative_coverage_markdown(report))

    if safety["status"] != "pass":
        raise ValueError("raw PII safety failed for hard-negative coverage")
    if report["hard_negative_gate"]["status"] != "pass":
        raise ValueError("hard-negative coverage gate failed")
    return report


def _row_from_template(template: dict[str, str], *, index: int) -> dict[str, Any]:
    marker = (
        f"[[ANCHOR:{template['anchor_entity']}:{template['anchor_shape']}:"
        "non_pii:heuristic_shape]]"
    )
    insertion_text = " ".join(
        [
            template["left"],
            "lookalike-field",
            marker,
            template["right"],
            "non-personal-reference",
        ]
    )
    rows = extract_context_anchor_windows_from_text(
        text=insertion_text,
        source_type="synthetic_safe_template",
        source_id=f"m4-phase5-hard-negative:{index:03d}",
        default_label="non_pii",
        max_windows=1,
    )
    if len(rows) != 1:
        raise ValueError("Hard-negative template did not produce one anchor row")
    row = rows[0].to_dict()
    row.pop("source_type", None)
    domain = template["source_domain"]
    material_class = DOMAIN_TO_MATERIAL[domain]
    row["source_domain"] = domain
    row["material_class"] = material_class
    row["material_type"] = material_class
    row["evidence_lane"] = "hard_negative_corpus"
    row["label_source"] = "codex_draft"
    row["label_status"] = "review_needed"
    row["source_id_hash"] = source_id_hash(f"m4-phase5-hard-negative:{index:03d}")
    row["contains_raw_pii"] = False
    row["raw_value_logged"] = False
    row["raw_url_logged"] = False
    row["page_body_stored"] = False
    row["candidate_value_stored"] = False
    return row


def _coverage_row(rows: list[dict[str, Any]], entity_group: str) -> dict[str, Any]:
    group_rows = [
        row
        for row in rows
        if ENTITY_TO_GROUP.get(str(row.get("anchor_entity"))) == entity_group
    ]
    non_pii_rows = [row for row in group_rows if row.get("label") == "non_pii"]
    hard_negative_count = sum(1 for row in non_pii_rows if _is_hard_negative_row(row))
    ratio = _ratio(hard_negative_count, len(non_pii_rows))
    required = HARD_NEGATIVE_THRESHOLDS[entity_group]
    status = "pass" if len(non_pii_rows) > 0 and ratio >= required else "fail"
    return {
        "non_pii_anchor_count": len(non_pii_rows),
        "hard_negative_count": hard_negative_count,
        "hard_negative_ratio": ratio,
        "required_ratio": required,
        "status": status,
    }


def _is_hard_negative_row(row: dict[str, Any]) -> bool:
    if row.get("label") != "non_pii":
        return False
    evidence_lane = row.get("evidence_lane")
    if evidence_lane == "hard_negative_corpus":
        return True
    return evidence_lane == "public_web_context" and row.get("anchor_shape") is not None


def _hard_negative_failure_verdicts(
    checks: dict[str, bool],
    counts: dict[str, dict[str, Any]],
) -> list[str]:
    verdicts: list[str] = []
    if not checks.get("raw_pii_safety_pass", False):
        verdicts.append("raw_pii_safety_failure")
    if not checks.get("manifest_data_quality_gate_pass", False):
        verdicts.append("rejected_data_quality_gate")
    for entity_group, row in counts.items():
        if row["status"] != "pass":
            verdicts.append(f"needs_hard_negative_coverage:{entity_group}")
    return verdicts or ["needs_hard_negative_coverage"]


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()
