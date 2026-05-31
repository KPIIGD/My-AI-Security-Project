"""Raw-free template inventory for M4 PERSON_NAME and ADDRESS coverage."""

from __future__ import annotations

import datetime
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .context_anchor_collector import (
    DOMAIN_TO_MATERIAL,
    VALID_ANCHOR_ENTITIES,
    VALID_ANCHOR_SHAPES,
)
from .context_source_inventory import ENTITY_TO_GROUP
from .context_window_safety import detect_raw_pii_like_values, scan_context_window_outputs


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "context_template_inventory_v1"
EVIDENCE_ROLE = "template_extraction_only_not_score_tuning"
TARGET_ENTITY_GROUPS = ("PERSON_NAME", "ADDRESS")
FIELD_LABEL_SOURCE = "raw_free_korean_field_label_template"
_URL_PATTERN = re.compile(r"\b(?:http[s]?|ftp)://\S+")
_FORBIDDEN_OUTPUT_KEYS = {
    "address_value",
    "candidate_value",
    "document_text",
    "html",
    "html_text",
    "page_body",
    "raw_address",
    "raw_name",
    "raw_sentence",
    "raw_text",
    "raw_url",
    "raw_value",
    "sentence",
    "span_text",
    "template_sentence",
    "template_text",
    "text",
    "url",
    "value",
}


@dataclass(frozen=True)
class ContextTemplateInventoryRow:
    template_id: str
    template_family: str
    entity_group: str
    anchor_entity: str
    anchor_shape: str
    source_domain: str
    field_label_terms: tuple[str, ...]
    left_context_terms: tuple[str, ...]
    right_context_terms: tuple[str, ...]
    template_structure: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        material_class = DOMAIN_TO_MATERIAL[self.source_domain]
        return {
            "schema_version": SCHEMA_VERSION,
            "template_id": self.template_id,
            "template_family": self.template_family,
            "entity_group": self.entity_group,
            "anchor_entity": self.anchor_entity,
            "anchor_shape": self.anchor_shape,
            "source_domain": self.source_domain,
            "material_class": material_class,
            "material_type": material_class,
            "evidence_lane": "template_extraction",
            "label_source": "codex_draft",
            "label_status": "review_needed",
            "field_label_source": FIELD_LABEL_SOURCE,
            "field_label_terms": list(self.field_label_terms),
            "left_context_terms": list(self.left_context_terms),
            "right_context_terms": list(self.right_context_terms),
            "template_structure": list(self.template_structure),
            "slot_mappings": [
                {
                    "slot_id": "slot_1",
                    "anchor_entity": self.anchor_entity,
                    "anchor_shape": self.anchor_shape,
                    "stored_value_policy": "shape_only_value_never_persisted",
                    "synthetic_insertion_allowed": True,
                }
            ],
            "usable_for_synthetic_insertion": True,
            "contains_raw_pii": False,
            "raw_value_logged": False,
            "raw_url_logged": False,
            "raw_sentence_logged": False,
            "page_body_stored": False,
            "candidate_value_stored": False,
            "evidence_role": EVIDENCE_ROLE,
        }


def build_context_template_inventory() -> list[dict[str, Any]]:
    rows = [row.to_dict() for row in _template_rows()]
    for row in rows:
        _validate_template_row(row)
    return rows


def context_template_inventory_jsonl(rows: Iterable[dict[str, Any]]) -> str:
    return "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
    )


def build_context_template_inventory_safety_report(
    rows: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    row_list = list(rows)
    inventory_text = context_template_inventory_jsonl(row_list)
    scan = scan_context_window_outputs(
        rows=[_SafetyRow(row) for row in row_list],
        report_payloads=[inventory_text],
        source_urls=[],
    )
    by_entity_group = Counter(str(row["entity_group"]) for row in row_list)
    by_anchor_entity = Counter(str(row["anchor_entity"]) for row in row_list)
    by_source_domain = Counter(str(row["source_domain"]) for row in row_list)
    entity_group_domain_counts = {
        entity_group: len(
            {
                str(row["source_domain"])
                for row in row_list
                if row.get("entity_group") == entity_group
            }
        )
        for entity_group in TARGET_ENTITY_GROUPS
    }
    forbidden_key_count = _forbidden_key_count(row_list)
    raw_sentence_logged_count = sum(
        1 for row in row_list if bool(row.get("raw_sentence_logged", False))
    )
    unusable_template_count = sum(
        1 for row in row_list if not bool(row.get("usable_for_synthetic_insertion"))
    )
    invalid_template_count = sum(1 for row in row_list if _row_validation_errors(row))

    reason_codes = list(scan["reason_codes"])
    if forbidden_key_count:
        reason_codes.append("context_template_inventory.forbidden_key.fail")
    if raw_sentence_logged_count:
        reason_codes.append("context_template_inventory.raw_sentence_logged.fail")
    if unusable_template_count:
        reason_codes.append("context_template_inventory.unusable_template.fail")
    if invalid_template_count:
        reason_codes.append("context_template_inventory.invalid_row.fail")
    if not all(entity_group_domain_counts[group] >= 5 for group in TARGET_ENTITY_GROUPS):
        reason_codes.append("context_template_inventory.needs_template_extraction")
    reason_codes = sorted(set(reason_codes))
    if reason_codes == ["context_corpus.safety.pass"]:
        status = "pass"
    else:
        status = "fail"

    return {
        "report_type": "ContextTemplateInventorySafetyReport",
        "schema_version": SCHEMA_VERSION,
        "phase": "Phase 3. Template Extraction For PERSON_NAME And ADDRESS",
        "evidence_role": EVIDENCE_ROLE,
        "template_count": len(row_list),
        "by_entity_group": dict(sorted(by_entity_group.items())),
        "by_anchor_entity": dict(sorted(by_anchor_entity.items())),
        "by_source_domain": dict(sorted(by_source_domain.items())),
        "entity_group_domain_counts": entity_group_domain_counts,
        "contains_raw_pii_true_count": scan["contains_raw_pii_true_count"],
        "raw_pii_leak_count": scan["raw_pii_leak_count"],
        "raw_url_logged_count": scan["raw_url_logged_count"],
        "raw_value_logged_count": scan["raw_value_logged_count"],
        "raw_sentence_logged_count": raw_sentence_logged_count,
        "forbidden_key_count": forbidden_key_count,
        "unusable_template_count": unusable_template_count,
        "invalid_template_count": invalid_template_count,
        "slot_value_materialized": False,
        "page_body_stored": False,
        "candidate_value_stored": False,
        "template_sentence_stored": False,
        "runtime_scoring_behavior_changed": False,
        "score_delta_changed": False,
        "context_rule_changed": False,
        "score_tuning_allowed_by_this_phase": False,
        "phase_exit_gate": {
            "status": status,
            "checks": {
                "person_name_templates_present": by_entity_group["PERSON_NAME"] > 0,
                "address_templates_present": by_entity_group["ADDRESS"] > 0,
                "person_name_domain_count_at_least_5": (
                    entity_group_domain_counts["PERSON_NAME"] >= 5
                ),
                "address_domain_count_at_least_5": (
                    entity_group_domain_counts["ADDRESS"] >= 5
                ),
                "raw_pii_safety_pass": scan["status"] == "pass",
                "raw_sentence_absent": raw_sentence_logged_count == 0,
                "forbidden_keys_absent": forbidden_key_count == 0,
                "all_templates_usable": unusable_template_count == 0,
                "all_rows_valid": invalid_template_count == 0,
            },
            "failure_verdicts": ["template_extraction_gate_pass"]
            if status == "pass"
            else reason_codes,
        },
        "status": status,
        "reason_codes": reason_codes,
        "generated_at": _now(),
    }


def render_context_template_inventory_markdown(
    rows: Iterable[dict[str, Any]],
    safety_report: dict[str, Any],
) -> str:
    row_list = list(rows)
    by_entity_group = Counter(str(row["entity_group"]) for row in row_list)
    domain_counts = safety_report["entity_group_domain_counts"]
    lines = [
        "# M4 Phase 3 Raw-Free Template Inventory",
        "",
        "This report summarizes controlled field-label templates only. It stores no raw names, raw addresses, raw sentences, raw URLs, or recoverable values.",
        "",
        f"- phase_exit_status: {safety_report['phase_exit_gate']['status']}",
        f"- template_count: {len(row_list)}",
        f"- PERSON_NAME_templates: {by_entity_group['PERSON_NAME']}",
        f"- ADDRESS_templates: {by_entity_group['ADDRESS']}",
        f"- PERSON_NAME_domain_count: {domain_counts['PERSON_NAME']}",
        f"- ADDRESS_domain_count: {domain_counts['ADDRESS']}",
        f"- raw_pii_leak_count: {safety_report['raw_pii_leak_count']}",
        f"- raw_sentence_logged_count: {safety_report['raw_sentence_logged_count']}",
        f"- score_tuning_allowed_by_this_phase: {str(safety_report['score_tuning_allowed_by_this_phase']).lower()}",
        "",
        "## Template Entity Mappings",
        "",
        "| template_id | entity_group | anchor_entity | anchor_shape | source_domain |",
        "| --- | --- | --- | --- | --- |",
    ]
    for row in row_list:
        lines.append(
            "| {template_id} | {entity_group} | {anchor_entity} | {anchor_shape} | {source_domain} |".format(
                **row
            )
        )
    lines.append("")
    return "\n".join(lines)


def write_context_template_inventory_artifacts(
    *,
    output_path: Path,
    safety_output_path: Path,
    report_output_path: Path,
) -> dict[str, Any]:
    rows = build_context_template_inventory()
    safety_report = build_context_template_inventory_safety_report(rows)
    inventory_text = context_template_inventory_jsonl(rows)
    safety_text = json.dumps(
        safety_report,
        ensure_ascii=False,
        indent=2,
        sort_keys=True,
    ) + "\n"
    report_text = render_context_template_inventory_markdown(rows, safety_report)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    safety_output_path.parent.mkdir(parents=True, exist_ok=True)
    report_output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(inventory_text, encoding="utf-8")
    safety_output_path.write_text(safety_text, encoding="utf-8")
    report_output_path.write_text(report_text, encoding="utf-8")
    if safety_report["status"] != "pass":
        raise ValueError("context template inventory safety failed")
    return safety_report


def _template_rows() -> tuple[ContextTemplateInventoryRow, ...]:
    return (
        ContextTemplateInventoryRow(
            template_id="tpl_person_customer_support_001",
            template_family="field_label_value_context",
            entity_group="PERSON_NAME",
            anchor_entity="PERSON_NAME",
            anchor_shape="korean_name_3_syllable",
            source_domain="customer_support",
            field_label_terms=("고객명", "성명"),
            left_context_terms=("문의자", "접수"),
            right_context_terms=("확인", "상담"),
            template_structure=("DOMAIN_CONTEXT", "FIELD_LABEL", "PII_SLOT", "ACTION_CONTEXT"),
        ),
        ContextTemplateInventoryRow(
            template_id="tpl_person_ecommerce_001",
            template_family="field_label_value_context",
            entity_group="PERSON_NAME",
            anchor_entity="PERSON_NAME",
            anchor_shape="korean_name_3_syllable",
            source_domain="ecommerce",
            field_label_terms=("수령인", "주문자"),
            left_context_terms=("배송", "주문"),
            right_context_terms=("확인", "입력"),
            template_structure=("DOMAIN_CONTEXT", "FIELD_LABEL", "PII_SLOT", "ACTION_CONTEXT"),
        ),
        ContextTemplateInventoryRow(
            template_id="tpl_person_healthcare_001",
            template_family="field_label_value_context",
            entity_group="PERSON_NAME",
            anchor_entity="PERSON_NAME",
            anchor_shape="korean_name_3_syllable",
            source_domain="healthcare",
            field_label_terms=("환자명", "보호자명"),
            left_context_terms=("예약", "접수"),
            right_context_terms=("진료", "확인"),
            template_structure=("DOMAIN_CONTEXT", "FIELD_LABEL", "PII_SLOT", "ACTION_CONTEXT"),
        ),
        ContextTemplateInventoryRow(
            template_id="tpl_person_finance_001",
            template_family="field_label_value_context",
            entity_group="PERSON_NAME",
            anchor_entity="PERSON_NAME",
            anchor_shape="korean_name_3_syllable",
            source_domain="finance",
            field_label_terms=("예금주", "신청인"),
            left_context_terms=("환불", "계좌"),
            right_context_terms=("인증", "확인"),
            template_structure=("DOMAIN_CONTEXT", "FIELD_LABEL", "PII_SLOT", "ACTION_CONTEXT"),
        ),
        ContextTemplateInventoryRow(
            template_id="tpl_person_education_001",
            template_family="field_label_value_context",
            entity_group="PERSON_NAME",
            anchor_entity="PERSON_NAME",
            anchor_shape="korean_name_3_syllable",
            source_domain="education",
            field_label_terms=("학생명", "지원자명"),
            left_context_terms=("신청", "등록"),
            right_context_terms=("학적", "접수"),
            template_structure=("DOMAIN_CONTEXT", "FIELD_LABEL", "PII_SLOT", "ACTION_CONTEXT"),
        ),
        ContextTemplateInventoryRow(
            template_id="tpl_person_public_services_001",
            template_family="field_label_value_context",
            entity_group="PERSON_NAME",
            anchor_entity="PERSON_NAME",
            anchor_shape="korean_name_3_syllable",
            source_domain="public_services",
            field_label_terms=("민원인", "신청인"),
            left_context_terms=("민원", "서류"),
            right_context_terms=("발급", "검토"),
            template_structure=("DOMAIN_CONTEXT", "FIELD_LABEL", "PII_SLOT", "ACTION_CONTEXT"),
        ),
        ContextTemplateInventoryRow(
            template_id="tpl_person_enterprise_internal_001",
            template_family="field_label_value_context",
            entity_group="PERSON_NAME",
            anchor_entity="PERSON_NAME",
            anchor_shape="korean_name_3_syllable",
            source_domain="enterprise_internal",
            field_label_terms=("직원명", "담당자"),
            left_context_terms=("요청", "승인"),
            right_context_terms=("처리", "부서"),
            template_structure=("DOMAIN_CONTEXT", "FIELD_LABEL", "PII_SLOT", "ACTION_CONTEXT"),
        ),
        ContextTemplateInventoryRow(
            template_id="tpl_address_customer_support_001",
            template_family="field_label_value_context",
            entity_group="ADDRESS",
            anchor_entity="ADDRESS_FULL",
            anchor_shape="road_address_shape",
            source_domain="customer_support",
            field_label_terms=("방문지", "서비스 주소"),
            left_context_terms=("출장", "접수"),
            right_context_terms=("방문", "확인"),
            template_structure=("DOMAIN_CONTEXT", "FIELD_LABEL", "PII_SLOT", "ACTION_CONTEXT"),
        ),
        ContextTemplateInventoryRow(
            template_id="tpl_address_ecommerce_001",
            template_family="field_label_value_context",
            entity_group="ADDRESS",
            anchor_entity="ADDRESS_FULL",
            anchor_shape="road_address_shape",
            source_domain="ecommerce",
            field_label_terms=("배송지", "수령 주소"),
            left_context_terms=("배송", "주문"),
            right_context_terms=("변경", "확인"),
            template_structure=("DOMAIN_CONTEXT", "FIELD_LABEL", "PII_SLOT", "ACTION_CONTEXT"),
        ),
        ContextTemplateInventoryRow(
            template_id="tpl_address_healthcare_001",
            template_family="field_label_value_context",
            entity_group="ADDRESS",
            anchor_entity="ADDRESS_FULL",
            anchor_shape="road_address_shape",
            source_domain="healthcare",
            field_label_terms=("거주지", "환자 주소"),
            left_context_terms=("접수", "문진"),
            right_context_terms=("확인", "기록"),
            template_structure=("DOMAIN_CONTEXT", "FIELD_LABEL", "PII_SLOT", "ACTION_CONTEXT"),
        ),
        ContextTemplateInventoryRow(
            template_id="tpl_address_finance_001",
            template_family="field_label_value_context",
            entity_group="ADDRESS",
            anchor_entity="ADDRESS_FULL",
            anchor_shape="road_address_shape",
            source_domain="finance",
            field_label_terms=("거주지", "청구 주소"),
            left_context_terms=("본인", "확인"),
            right_context_terms=("심사", "등록"),
            template_structure=("DOMAIN_CONTEXT", "FIELD_LABEL", "PII_SLOT", "ACTION_CONTEXT"),
        ),
        ContextTemplateInventoryRow(
            template_id="tpl_address_education_001",
            template_family="field_label_value_context",
            entity_group="ADDRESS",
            anchor_entity="ADDRESS_FULL",
            anchor_shape="road_address_shape",
            source_domain="education",
            field_label_terms=("거주지", "보호자 주소"),
            left_context_terms=("원서", "등록"),
            right_context_terms=("통학", "확인"),
            template_structure=("DOMAIN_CONTEXT", "FIELD_LABEL", "PII_SLOT", "ACTION_CONTEXT"),
        ),
        ContextTemplateInventoryRow(
            template_id="tpl_address_public_services_001",
            template_family="field_label_value_context",
            entity_group="ADDRESS",
            anchor_entity="ADDRESS_FULL",
            anchor_shape="road_address_shape",
            source_domain="public_services",
            field_label_terms=("주소", "신청 주소"),
            left_context_terms=("민원", "신청"),
            right_context_terms=("발급", "검토"),
            template_structure=("DOMAIN_CONTEXT", "FIELD_LABEL", "PII_SLOT", "ACTION_CONTEXT"),
        ),
        ContextTemplateInventoryRow(
            template_id="tpl_address_enterprise_internal_001",
            template_family="field_label_value_context",
            entity_group="ADDRESS",
            anchor_entity="ADDRESS_UNIT",
            anchor_shape="address_unit_shape",
            source_domain="enterprise_internal",
            field_label_terms=("근무지", "사무실 위치"),
            left_context_terms=("시설", "요청"),
            right_context_terms=("배정", "확인"),
            template_structure=("DOMAIN_CONTEXT", "FIELD_LABEL", "PII_SLOT", "ACTION_CONTEXT"),
        ),
    )


def _validate_template_row(row: dict[str, Any]) -> None:
    errors = _row_validation_errors(row)
    if errors:
        raise ValueError(f"Invalid context template row {row.get('template_id')}: {errors}")


def _row_validation_errors(row: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if row.get("entity_group") not in TARGET_ENTITY_GROUPS:
        errors.append("unsupported_entity_group")
    if row.get("anchor_entity") not in VALID_ANCHOR_ENTITIES:
        errors.append("unsupported_anchor_entity")
    if row.get("anchor_shape") not in VALID_ANCHOR_SHAPES:
        errors.append("unsupported_anchor_shape")
    if ENTITY_TO_GROUP.get(str(row.get("anchor_entity"))) != row.get("entity_group"):
        errors.append("entity_group_mismatch")
    if row.get("material_class") != DOMAIN_TO_MATERIAL.get(str(row.get("source_domain"))):
        errors.append("material_class_mismatch")
    if row.get("material_type") != row.get("material_class"):
        errors.append("material_type_mismatch")
    for field in ("field_label_terms", "left_context_terms", "right_context_terms"):
        values = row.get(field)
        if not isinstance(values, list) or not values:
            errors.append(f"{field}_missing")
            continue
        if not all(isinstance(value, str) and _is_safe_term(value) for value in values):
            errors.append(f"{field}_unsafe")
    if _forbidden_key_count([row]):
        errors.append("forbidden_output_key")
    serialized = json.dumps(row, ensure_ascii=False, sort_keys=True)
    if detect_raw_pii_like_values(serialized):
        errors.append("raw_pii_like_value")
    if _URL_PATTERN.search(serialized):
        errors.append("raw_url_like_value")
    return errors


def _is_safe_term(value: str) -> bool:
    return (
        bool(value.strip())
        and len(value) <= 32
        and "\n" not in value
        and "\r" not in value
        and "\t" not in value
        and not detect_raw_pii_like_values(value)
        and not _URL_PATTERN.search(value)
    )


def _forbidden_key_count(rows: Iterable[dict[str, Any]]) -> int:
    return sum(1 for row in rows for key in _iter_keys(row) if key in _FORBIDDEN_OUTPUT_KEYS)


def _iter_keys(value: object) -> Iterable[str]:
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _iter_keys(child)
    elif isinstance(value, list):
        for child in value:
            yield from _iter_keys(child)


def _now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


@dataclass(frozen=True)
class _SafetyRow:
    payload: dict[str, Any]

    @property
    def contains_raw_pii(self) -> bool:
        return bool(self.payload.get("contains_raw_pii", False))

    @property
    def raw_value_logged(self) -> bool:
        return bool(self.payload.get("raw_value_logged", False))
