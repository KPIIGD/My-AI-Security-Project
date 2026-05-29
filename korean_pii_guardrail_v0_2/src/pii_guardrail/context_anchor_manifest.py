"""Diversity manifest for M4 raw-free anchor context windows."""

from __future__ import annotations

import datetime
import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Iterable

from .context_anchor_collector import (
    DOMAIN_TO_MATERIAL,
    SCHEMA_VERSION,
    build_context_anchor_safety_report,
    context_anchor_windows_jsonl,
    load_context_anchor_windows_jsonl,
)
from .context_source_inventory import (
    CORE_ENTITY_GROUPS,
    ENTITY_TO_GROUP,
    MATERIAL_CLASSES,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_VERSION = "v0.2-single-turn"
MAX_SINGLE_DOMAIN_RATIO = 0.35
MIN_DOMAIN_COUNT_BY_CORE_ENTITY = 5
MIN_REALISTIC_INPUT_LIKE_RATIO = 0.70
MAX_GENERAL_WEB_OR_EXPLANATORY_RATIO = 0.30
MAX_EXAMPLE_OR_SAMPLE_DOCUMENT_RATIO = 0.15
MAX_DUPLICATE_ANCHOR_WINDOW_RATIO = 0.05
MAX_UNKNOWN_LABEL_RATIO = 0.15


def build_context_anchor_manifest(
    *,
    anchor_input_path: Path,
    rows: Iterable[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    input_exists = rows is not None or anchor_input_path.exists()
    row_list = list(rows) if rows is not None else (
        load_context_anchor_windows_jsonl(anchor_input_path) if input_exists else []
    )
    measurements = _build_measurements(row_list)
    safety = build_context_anchor_safety_report(
        rows=row_list,
        term_rows=[],
        source_ids=[],
        extra_payloads=[context_anchor_windows_jsonl(row_list)],
    )
    gate = _data_quality_gate(
        input_exists=input_exists,
        row_count=len(row_list),
        measurements=measurements,
        safety=safety,
    )
    return {
        "manifest_type": "ContextAnchorWindowsManifest",
        "schema_version": SCHEMA_VERSION,
        "version": REPORT_VERSION,
        "stage": "1.4 diversity manifest",
        "anchor_input_exists": input_exists,
        "anchor_input_path": "data/context_corpus/context_anchor_windows_v1.jsonl",
        "runtime_scoring_behavior_changed": False,
        "score_delta_changed": False,
        "context_rule_changed": False,
        "public_corpus_used_for_score_tuning": False,
        "score_tuning_allowed_by_this_manifest": False,
        "measurements": measurements,
        "raw_free_scan": {
            "status": safety["status"],
            "raw_pii_leak_count": safety["raw_pii_leak_count"],
            "raw_url_logged_count": safety["raw_url_logged_count"],
            "raw_value_logged_count": safety["raw_value_logged_count"],
            "contains_raw_pii_true_count": safety["contains_raw_pii_true_count"],
            "page_body_stored": False,
            "candidate_value_stored": False,
            "invalid_offset_count": 0,
            "reason_codes": safety["reason_codes"],
        },
        "data_quality_gate": gate,
        "generated_at": _now(),
    }


def write_context_anchor_manifest(
    *,
    anchor_input_path: Path,
    output_path: Path,
) -> dict[str, Any]:
    payload = build_context_anchor_manifest(anchor_input_path=anchor_input_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(render_manifest_yaml(payload), encoding="utf-8")
    return payload


def render_manifest_yaml(payload: dict[str, Any]) -> str:
    """Render JSON-compatible YAML without adding a YAML dependency."""

    return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"


def _build_measurements(rows: list[dict[str, Any]]) -> dict[str, Any]:
    by_entity_group_domain: dict[str, Counter[str]] = {
        entity_group: Counter() for entity_group in CORE_ENTITY_GROUPS
    }
    by_entity_group_label: dict[str, Counter[str]] = {
        entity_group: Counter() for entity_group in CORE_ENTITY_GROUPS
    }
    by_source_domain = Counter(str(row.get("source_domain", "unknown")) for row in rows)
    by_material_class = Counter(str(row.get("material_class", "unknown")) for row in rows)
    by_label = Counter(str(row.get("label", "unknown")) for row in rows)
    by_entity = Counter(str(row.get("anchor_entity", "unknown")) for row in rows)
    invalid_anchor_row_count = 0

    for row in rows:
        entity = str(row.get("anchor_entity", "unknown"))
        entity_group = ENTITY_TO_GROUP.get(entity)
        domain = str(row.get("source_domain", "unknown"))
        material_class = str(row.get("material_class", "unknown"))
        label = str(row.get("label", "unknown"))
        if entity_group is None:
            invalid_anchor_row_count += 1
            continue
        by_entity_group_domain[entity_group][domain] += 1
        by_entity_group_label[entity_group][label] += 1
        if DOMAIN_TO_MATERIAL.get(domain) != material_class:
            invalid_anchor_row_count += 1

    duplicate_count, duplicate_ratio = _duplicate_measurement(rows)
    total = len(rows)
    domain_count_by_core_entity = {
        entity_group: len(counter)
        for entity_group, counter in by_entity_group_domain.items()
    }
    max_single_domain_ratio_by_core_entity = {
        entity_group: _max_counter_ratio(counter)
        for entity_group, counter in by_entity_group_domain.items()
    }
    domain_ratio_gate_by_core_entity = {
        entity_group: (
            domain_count_by_core_entity[entity_group] >= MIN_DOMAIN_COUNT_BY_CORE_ENTITY
            and max_single_domain_ratio_by_core_entity[entity_group]
            <= MAX_SINGLE_DOMAIN_RATIO
        )
        for entity_group in CORE_ENTITY_GROUPS
    }
    return {
        "total_anchor_windows": total,
        "by_anchor_entity": dict(sorted(by_entity.items())),
        "by_source_domain": dict(sorted(by_source_domain.items())),
        "by_material_class": {
            material_class: by_material_class.get(material_class, 0)
            for material_class in MATERIAL_CLASSES
        },
        "by_label": {
            "true_pii": by_label.get("true_pii", 0),
            "non_pii": by_label.get("non_pii", 0),
            "unknown": by_label.get("unknown", 0),
        },
        "label_counts_by_core_entity": {
            entity_group: dict(sorted(counter.items()))
            for entity_group, counter in by_entity_group_label.items()
        },
        "domain_counts_by_core_entity": {
            entity_group: dict(sorted(counter.items()))
            for entity_group, counter in by_entity_group_domain.items()
        },
        "domain_count_by_core_entity": domain_count_by_core_entity,
        "max_single_domain_ratio_by_core_entity": max_single_domain_ratio_by_core_entity,
        "domain_ratio_gate_by_core_entity": domain_ratio_gate_by_core_entity,
        "material_ratios": {
            material_class: _ratio(by_material_class.get(material_class, 0), total)
            for material_class in MATERIAL_CLASSES
        },
        "duplicate_anchor_window_count": duplicate_count,
        "duplicate_anchor_window_ratio": duplicate_ratio,
        "unknown_label_ratio": _ratio(by_label.get("unknown", 0), total),
        "invalid_anchor_row_count": invalid_anchor_row_count,
        "invalid_offset_count": 0,
        "offsets_stored": False,
    }


def _data_quality_gate(
    *,
    input_exists: bool,
    row_count: int,
    measurements: dict[str, Any],
    safety: dict[str, Any],
) -> dict[str, Any]:
    criteria = {
        "raw_pii_leak_count": 0,
        "invalid_offset_count": 0,
        "min_domain_count_by_core_entity": MIN_DOMAIN_COUNT_BY_CORE_ENTITY,
        "max_single_domain_ratio": MAX_SINGLE_DOMAIN_RATIO,
        "min_realistic_input_like_ratio": MIN_REALISTIC_INPUT_LIKE_RATIO,
        "max_general_web_or_explanatory_ratio": MAX_GENERAL_WEB_OR_EXPLANATORY_RATIO,
        "max_example_or_sample_document_ratio": MAX_EXAMPLE_OR_SAMPLE_DOCUMENT_RATIO,
        "max_duplicate_anchor_window_ratio": MAX_DUPLICATE_ANCHOR_WINDOW_RATIO,
        "max_unknown_label_ratio_when_labels_present": MAX_UNKNOWN_LABEL_RATIO,
    }
    material_ratios = measurements["material_ratios"]
    checks = {
        "anchor_input_exists": input_exists,
        "has_anchor_windows": row_count > 0,
        "raw_pii_leak_count_zero": safety["raw_pii_leak_count"] == 0,
        "raw_url_logged_count_zero": safety["raw_url_logged_count"] == 0,
        "raw_value_logged_count_zero": safety["raw_value_logged_count"] == 0,
        "invalid_offset_count_zero": measurements["invalid_offset_count"] == 0,
        "invalid_anchor_row_count_zero": measurements["invalid_anchor_row_count"] == 0,
        "min_domain_count_by_core_entity": all(
            count >= MIN_DOMAIN_COUNT_BY_CORE_ENTITY
            for count in measurements["domain_count_by_core_entity"].values()
        ),
        "max_single_domain_ratio_by_core_entity": all(
            ratio <= MAX_SINGLE_DOMAIN_RATIO
            for ratio in measurements["max_single_domain_ratio_by_core_entity"].values()
        ),
        "min_realistic_input_like_ratio": (
            material_ratios["realistic_input_like"] >= MIN_REALISTIC_INPUT_LIKE_RATIO
        ),
        "max_general_web_or_explanatory_ratio": (
            material_ratios["general_web_or_explanatory"]
            <= MAX_GENERAL_WEB_OR_EXPLANATORY_RATIO
        ),
        "max_example_or_sample_document_ratio": (
            material_ratios["example_or_sample"]
            <= MAX_EXAMPLE_OR_SAMPLE_DOCUMENT_RATIO
        ),
        "max_duplicate_anchor_window_ratio": (
            measurements["duplicate_anchor_window_ratio"]
            <= MAX_DUPLICATE_ANCHOR_WINDOW_RATIO
        ),
        "max_unknown_label_ratio_when_labels_present": (
            measurements["unknown_label_ratio"] <= MAX_UNKNOWN_LABEL_RATIO
        ),
    }
    failure_verdicts = _failure_verdicts(checks)
    return {
        "status": "pass" if all(checks.values()) else "fail",
        "checks": checks,
        "pass_criteria": criteria,
        "failure_verdicts": failure_verdicts,
        "score_tuning_allowed_by_this_phase": False,
    }


def _failure_verdicts(checks: dict[str, bool]) -> list[str]:
    verdicts: list[str] = []
    if not checks["anchor_input_exists"] or not checks["has_anchor_windows"]:
        verdicts.append("needs_anchor_corpus")
    if not checks["min_domain_count_by_core_entity"]:
        verdicts.append("needs_more_data")
    if not checks["max_single_domain_ratio_by_core_entity"]:
        verdicts.append("needs_domain_split")
    if not all(
        checks[key]
        for key in (
            "raw_pii_leak_count_zero",
            "raw_url_logged_count_zero",
            "raw_value_logged_count_zero",
        )
    ):
        verdicts.append("raw_pii_safety_failure")
    if not checks["invalid_anchor_row_count_zero"]:
        verdicts.append("invalid_anchor_rows")
    if not all(
        checks[key]
        for key in (
            "min_realistic_input_like_ratio",
            "max_general_web_or_explanatory_ratio",
            "max_example_or_sample_document_ratio",
        )
    ):
        verdicts.append("needs_material_mix")
    if not checks["max_duplicate_anchor_window_ratio"]:
        verdicts.append("needs_deduplication")
    if not checks["max_unknown_label_ratio_when_labels_present"]:
        verdicts.append("needs_labels")
    if not verdicts:
        verdicts.append("data_quality_gate_pass")
    return verdicts


def _duplicate_measurement(rows: list[dict[str, Any]]) -> tuple[int, float]:
    counts: defaultdict[str, int] = defaultdict(int)
    for row in rows:
        counts[json.dumps(row, ensure_ascii=False, sort_keys=True)] += 1
    duplicate_count = sum(count - 1 for count in counts.values() if count > 1)
    return duplicate_count, _ratio(duplicate_count, len(rows))


def _max_counter_ratio(counter: Counter[str]) -> float:
    total = sum(counter.values())
    return _ratio(max(counter.values(), default=0), total)


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)


def _now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()
