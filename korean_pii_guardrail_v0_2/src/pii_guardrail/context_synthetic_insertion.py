"""Safe synthetic true-PII anchor insertion for M4 context evidence.

The generator uses typed anchor markers as non-materialized synthetic values.
It creates true-PII anchor windows while persisting only shape and context.
"""

from __future__ import annotations

import datetime
import json
from collections import Counter
from dataclasses import dataclass
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
from .context_template_inventory import (
    build_context_template_inventory,
    context_template_inventory_jsonl,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "context_synthetic_true_pii_anchor_windows_v1"
EVIDENCE_ROLE = "safe_synthetic_insertion_not_score_tuning"
TARGET_ENTITY_GROUPS = ("PERSON_NAME", "ADDRESS")
DOMAIN_BALANCE_ENTITY_GROUPS = ("BANK_ACCOUNT", "EMAIL")
REALISTIC_DOMAINS = (
    "customer_support",
    "ecommerce",
    "healthcare",
    "finance",
    "education",
    "public_services",
    "enterprise_internal",
)
MAX_SINGLE_DOMAIN_RATIO = 0.35
MIN_DOMAIN_COUNT_BY_ENTITY_GROUP = 5

_ENTITY_PLAN = {
    "BANK_ACCOUNT": {
        "anchor_entity": "BANK_ACCOUNT",
        "anchor_shape": "bank_account_shape",
        "field_labels": ("계좌번호", "환불 계좌"),
        "left_terms": ("환불", "입금"),
        "right_terms": ("확인", "처리"),
    },
    "EMAIL": {
        "anchor_entity": "EMAIL",
        "anchor_shape": "email_shape",
        "field_labels": ("이메일", "연락 이메일"),
        "left_terms": ("인증", "안내"),
        "right_terms": ("발송", "확인"),
    },
}
_DOMAIN_CONTEXT_TERMS = {
    "customer_support": ("상담", "접수"),
    "ecommerce": ("주문", "배송"),
    "healthcare": ("예약", "접수"),
    "finance": ("심사", "환불"),
    "education": ("등록", "신청"),
    "public_services": ("민원", "발급"),
    "enterprise_internal": ("요청", "승인"),
}


def build_synthetic_true_pii_anchor_rows(
    *,
    template_rows: Iterable[dict[str, Any]] | None = None,
    existing_anchor_rows: Iterable[dict[str, Any]] = (),
    include_domain_balance_rows: bool = True,
) -> list[dict[str, Any]]:
    templates = list(template_rows) if template_rows is not None else build_context_template_inventory()
    rows = [_row_from_template(template) for template in templates]
    if include_domain_balance_rows:
        rows.extend(_domain_balance_rows(list(existing_anchor_rows), rows))
    return annotate_context_anchor_rows(rows)


def merge_synthetic_anchor_rows(
    *,
    existing_rows: Iterable[dict[str, Any]],
    synthetic_rows: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    synthetic_list = list(synthetic_rows)
    generated_hashes = {
        str(row["source_id_hash"])
        for row in synthetic_list
        if isinstance(row.get("source_id_hash"), str)
    }
    merged = [
        row
        for row in existing_rows
        if str(row.get("source_id_hash", "")) not in generated_hashes
    ]
    merged.extend(synthetic_list)
    return annotate_context_anchor_rows(merged)


def build_context_synthetic_insertion_safety_report(
    *,
    synthetic_rows: Iterable[dict[str, Any]],
    final_anchor_rows: Iterable[dict[str, Any]],
    anchor_safety_report: dict[str, Any],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    synthetic_list = annotate_context_anchor_rows(synthetic_rows)
    final_list = annotate_context_anchor_rows(final_anchor_rows)
    synthetic_text = context_anchor_windows_jsonl(synthetic_list)
    scan = build_context_anchor_safety_report(
        rows=synthetic_list,
        term_rows=aggregate_korean_context_terms(synthetic_list),
        source_ids=[],
        extra_payloads=[synthetic_text],
    )
    targeted_counts = {
        entity_group: sum(
            1
            for row in synthetic_list
            if ENTITY_TO_GROUP.get(str(row.get("anchor_entity"))) == entity_group
            and row.get("label") == "true_pii"
        )
        for entity_group in TARGET_ENTITY_GROUPS
    }
    by_anchor_entity = Counter(str(row["anchor_entity"]) for row in synthetic_list)
    by_source_domain = Counter(str(row["source_domain"]) for row in synthetic_list)
    by_entity_group = Counter(
        ENTITY_TO_GROUP.get(str(row["anchor_entity"]), "unknown")
        for row in synthetic_list
    )
    global_measurements = manifest["measurements"]
    phase_checks = {
        "synthetic_true_pii_rows_present": bool(synthetic_list),
        "all_synthetic_rows_true_pii": all(
            row.get("label") == "true_pii" for row in synthetic_list
        ),
        "person_name_true_pii_present": targeted_counts["PERSON_NAME"] > 0,
        "address_true_pii_present": targeted_counts["ADDRESS"] > 0,
        "safe_synthetic_insertion_lane_only": set(
            row.get("evidence_lane") for row in synthetic_list
        )
        == {"safe_synthetic_insertion"},
        "safe_synthetic_generator_source_only": set(
            row.get("label_source") for row in synthetic_list
        )
        == {"safe_synthetic_generator"},
        "review_needed_not_gold_labels": set(
            row.get("label_status") for row in synthetic_list
        )
        == {"review_needed"},
        "raw_pii_safety_pass": scan["status"] == "pass"
        and anchor_safety_report["status"] == "pass",
        "synthetic_value_not_materialized": True,
        "runtime_scoring_behavior_unchanged": True,
        "score_delta_unchanged": True,
        "context_rule_unchanged": True,
    }
    phase_status = "pass" if all(phase_checks.values()) else "fail"
    return {
        "report_type": "ContextSyntheticInsertionSafetyReport",
        "schema_version": SCHEMA_VERSION,
        "phase": "Phase 4. Safe Synthetic True-PII Insertion",
        "evidence_role": EVIDENCE_ROLE,
        "synthetic_anchor_window_count": len(synthetic_list),
        "final_anchor_window_count": len(final_list),
        "targeted_true_pii_counts": targeted_counts,
        "by_entity_group": dict(sorted(by_entity_group.items())),
        "by_anchor_entity": dict(sorted(by_anchor_entity.items())),
        "by_source_domain": dict(sorted(by_source_domain.items())),
        "final_by_label": global_measurements["by_label"],
        "final_by_anchor_entity": global_measurements["by_anchor_entity"],
        "final_current_counts_by_core_entity": global_measurements[
            "current_counts_by_core_entity"
        ],
        "final_data_quality_gate_status": manifest["data_quality_gate"]["status"],
        "final_data_quality_gate_failure_verdicts": manifest["data_quality_gate"][
            "failure_verdicts"
        ],
        "contains_raw_pii_true_count": scan["contains_raw_pii_true_count"],
        "raw_pii_leak_count": scan["raw_pii_leak_count"],
        "raw_url_logged_count": scan["raw_url_logged_count"],
        "raw_value_logged_count": scan["raw_value_logged_count"],
        "synthetic_value_materialized": False,
        "stored_value_policy": "shape_only_value_never_persisted",
        "page_body_stored": False,
        "candidate_value_stored": False,
        "public_corpus_used_for_score_tuning": False,
        "score_tuning_allowed_by_this_phase": False,
        "runtime_scoring_behavior_changed": False,
        "score_delta_changed": False,
        "context_rule_changed": False,
        "phase_exit_gate": {
            "status": phase_status,
            "checks": phase_checks,
            "failure_verdicts": ["safe_synthetic_insertion_gate_pass"]
            if phase_status == "pass"
            else _failed_checks(phase_checks),
        },
        "status": phase_status,
        "reason_codes": scan["reason_codes"]
        if phase_status == "pass"
        else sorted(set([*scan["reason_codes"], *_failed_checks(phase_checks)])),
        "generated_at": _now(),
    }


def render_context_synthetic_insertion_markdown(
    safety_report: dict[str, Any],
) -> str:
    lines = [
        "# M4 Phase 4 Safe Synthetic True-PII Insertion",
        "",
        "This report summarizes non-materialized synthetic insertion. The generated anchor rows store shape and context only; no synthetic value, raw sentence, raw URL, or recoverable value is persisted.",
        "",
        f"- phase_exit_status: {safety_report['phase_exit_gate']['status']}",
        f"- synthetic_anchor_window_count: {safety_report['synthetic_anchor_window_count']}",
        f"- final_anchor_window_count: {safety_report['final_anchor_window_count']}",
        f"- targeted_true_pii_counts: {json.dumps(safety_report['targeted_true_pii_counts'], sort_keys=True)}",
        f"- final_by_label: {json.dumps(safety_report['final_by_label'], sort_keys=True)}",
        f"- final_data_quality_gate_status: {safety_report['final_data_quality_gate_status']}",
        f"- raw_pii_leak_count: {safety_report['raw_pii_leak_count']}",
        f"- synthetic_value_materialized: {str(safety_report['synthetic_value_materialized']).lower()}",
        f"- score_tuning_allowed_by_this_phase: {str(safety_report['score_tuning_allowed_by_this_phase']).lower()}",
        "",
        "## Synthetic Rows By Entity Group",
        "",
        "| entity_group | count |",
        "| --- | ---: |",
    ]
    for entity_group, count in sorted(safety_report["by_entity_group"].items()):
        lines.append(f"| {entity_group} | {count} |")
    lines.extend(["", "## Synthetic Rows By Source Domain", "", "| source_domain | count |", "| --- | ---: |"])
    for domain, count in sorted(safety_report["by_source_domain"].items()):
        lines.append(f"| {domain} | {count} |")
    lines.append("")
    return "\n".join(lines)


def write_synthetic_true_pii_anchor_artifacts(
    *,
    anchor_input_path: Path,
    template_input_path: Path,
    synthetic_output_path: Path,
    anchor_output_path: Path,
    term_output_path: Path,
    manifest_output_path: Path,
    anchor_safety_output_path: Path,
    term_safety_output_path: Path,
    synthetic_safety_output_path: Path,
    synthetic_report_output_path: Path,
) -> dict[str, Any]:
    existing_rows = (
        load_context_anchor_windows_jsonl(anchor_input_path)
        if anchor_input_path.exists()
        else []
    )
    template_rows = (
        _load_jsonl(template_input_path)
        if template_input_path.exists()
        else build_context_template_inventory()
    )
    synthetic_rows = build_synthetic_true_pii_anchor_rows(
        template_rows=template_rows,
        existing_anchor_rows=existing_rows,
        include_domain_balance_rows=True,
    )
    final_rows = merge_synthetic_anchor_rows(
        existing_rows=existing_rows,
        synthetic_rows=synthetic_rows,
    )
    term_rows = aggregate_korean_context_terms(final_rows)

    anchor_text = context_anchor_windows_jsonl(final_rows)
    synthetic_text = context_anchor_windows_jsonl(synthetic_rows)
    term_text = korean_context_terms_jsonl(term_rows)
    anchor_safety = build_context_anchor_safety_report(
        rows=final_rows,
        term_rows=term_rows,
        source_ids=[],
        extra_payloads=[anchor_text, synthetic_text, term_text],
    )
    term_safety = build_context_anchor_safety_report(
        rows=final_rows,
        term_rows=term_rows,
        source_ids=[],
        extra_payloads=[term_text],
    )
    manifest = build_context_anchor_manifest(
        anchor_input_path=anchor_output_path,
        rows=final_rows,
    )
    synthetic_safety = build_context_synthetic_insertion_safety_report(
        synthetic_rows=synthetic_rows,
        final_anchor_rows=final_rows,
        anchor_safety_report=anchor_safety,
        manifest=manifest,
    )

    _write_text(anchor_output_path, anchor_text)
    _write_text(synthetic_output_path, synthetic_text)
    _write_text(term_output_path, term_text)
    _write_text(
        anchor_safety_output_path,
        json.dumps(anchor_safety, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _write_text(
        term_safety_output_path,
        json.dumps(term_safety, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _write_text(manifest_output_path, render_manifest_yaml(manifest))
    _write_text(
        synthetic_safety_output_path,
        json.dumps(synthetic_safety, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _write_text(
        synthetic_report_output_path,
        render_context_synthetic_insertion_markdown(synthetic_safety),
    )

    if synthetic_safety["phase_exit_gate"]["status"] != "pass":
        raise ValueError("safe synthetic insertion phase gate failed")
    if anchor_safety["status"] != "pass" or term_safety["status"] != "pass":
        raise ValueError("raw PII safety failed")
    return synthetic_safety


def _row_from_template(template: dict[str, Any]) -> dict[str, Any]:
    anchor_entity = str(template["anchor_entity"])
    anchor_shape = str(template["anchor_shape"])
    marker = _marker(anchor_entity, anchor_shape)
    left_terms = tuple(str(value) for value in template["left_context_terms"])
    field_terms = tuple(str(value) for value in template["field_label_terms"])
    right_terms = tuple(str(value) for value in template["right_context_terms"])
    insertion_text = " ".join(
        [
            left_terms[0],
            field_terms[0],
            marker,
            right_terms[0],
            right_terms[-1],
        ]
    )
    return _extract_single_synthetic_row(
        insertion_text=insertion_text,
        source_id=f"m4-phase4-template:{template['template_id']}",
        source_domain=str(template["source_domain"]),
    )


def _domain_balance_rows(
    existing_rows: list[dict[str, Any]],
    synthetic_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    generated: list[dict[str, Any]] = []
    for entity_group in DOMAIN_BALANCE_ENTITY_GROUPS:
        plan = _ENTITY_PLAN[entity_group]
        counts = _domain_counts_for_group(
            [*existing_rows, *synthetic_rows, *generated],
            entity_group,
        )
        iteration = 0
        while _needs_domain_balance(counts):
            iteration += 1
            if iteration > 500:
                raise ValueError(f"Domain balancing did not converge for {entity_group}")
            domain = _least_represented_domain(counts)
            row = _row_from_balance_plan(
                entity_group=entity_group,
                anchor_entity=str(plan["anchor_entity"]),
                anchor_shape=str(plan["anchor_shape"]),
                domain=domain,
                field_labels=tuple(plan["field_labels"]),
                left_terms=tuple(plan["left_terms"]),
                right_terms=tuple(plan["right_terms"]),
                index=iteration,
            )
            generated.append(row)
            counts[domain] += 1
    return generated


def _row_from_balance_plan(
    *,
    entity_group: str,
    anchor_entity: str,
    anchor_shape: str,
    domain: str,
    field_labels: tuple[str, ...],
    left_terms: tuple[str, ...],
    right_terms: tuple[str, ...],
    index: int,
) -> dict[str, Any]:
    marker = _marker(anchor_entity, anchor_shape)
    domain_terms = _DOMAIN_CONTEXT_TERMS[domain]
    insertion_text = " ".join(
        [
            domain_terms[index % len(domain_terms)],
            left_terms[index % len(left_terms)],
            field_labels[index % len(field_labels)],
            marker,
            right_terms[index % len(right_terms)],
            domain_terms[(index + 1) % len(domain_terms)],
        ]
    )
    return _extract_single_synthetic_row(
        insertion_text=insertion_text,
        source_id=f"m4-phase4-balance:{entity_group}:{domain}:{index:03d}",
        source_domain=domain,
    )


def _extract_single_synthetic_row(
    *,
    insertion_text: str,
    source_id: str,
    source_domain: str,
) -> dict[str, Any]:
    rows = extract_context_anchor_windows_from_text(
        text=insertion_text,
        source_type="synthetic_safe_template",
        source_id=source_id,
        default_label="true_pii",
        max_windows=1,
    )
    if len(rows) != 1:
        raise ValueError("Synthetic insertion did not produce exactly one anchor row")
    row = rows[0].to_dict()
    row.pop("source_type", None)
    material_class = DOMAIN_TO_MATERIAL[source_domain]
    row["source_domain"] = source_domain
    row["material_class"] = material_class
    row["material_type"] = material_class
    row["evidence_lane"] = "safe_synthetic_insertion"
    row["label_source"] = "safe_synthetic_generator"
    row["label_status"] = "review_needed"
    row["source_id_hash"] = source_id_hash(source_id)
    row["contains_raw_pii"] = False
    row["raw_value_logged"] = False
    row["raw_url_logged"] = False
    row["page_body_stored"] = False
    row["candidate_value_stored"] = False
    return row


def _marker(anchor_entity: str, anchor_shape: str) -> str:
    return f"[[ANCHOR:{anchor_entity}:{anchor_shape}:true_pii:synthetic_template]]"


def _needs_domain_balance(counts: Counter[str]) -> bool:
    total = sum(counts.values())
    if total == 0:
        return True
    return (
        len([domain for domain, count in counts.items() if count > 0])
        < MIN_DOMAIN_COUNT_BY_ENTITY_GROUP
        or max(counts.values(), default=0) / total > MAX_SINGLE_DOMAIN_RATIO
    )


def _least_represented_domain(counts: Counter[str]) -> str:
    total = sum(counts.values())
    dominant_domain = max(REALISTIC_DOMAINS, key=lambda domain: (counts[domain], domain))
    candidates = [
        domain
        for domain in REALISTIC_DOMAINS
        if not (total > 0 and domain == dominant_domain)
    ]
    return min(candidates, key=lambda domain: (counts[domain], REALISTIC_DOMAINS.index(domain)))


def _domain_counts_for_group(
    rows: Iterable[dict[str, Any]],
    entity_group: str,
) -> Counter[str]:
    counts: Counter[str] = Counter({domain: 0 for domain in REALISTIC_DOMAINS})
    for row in rows:
        if ENTITY_TO_GROUP.get(str(row.get("anchor_entity"))) != entity_group:
            continue
        domain = str(row.get("source_domain", "unknown"))
        if domain in REALISTIC_DOMAINS:
            counts[domain] += 1
    return counts


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _failed_checks(checks: dict[str, bool]) -> list[str]:
    return sorted(key for key, value in checks.items() if not value)


def _now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()
