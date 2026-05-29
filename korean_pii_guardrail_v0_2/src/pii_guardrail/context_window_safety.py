"""Safe context-window collection for M4 coverage evidence.

The collector reads curated pages in memory, extracts sentences containing
approved context anchors, and writes only controlled classes plus URL hashes.
It never writes page bodies, raw URLs, raw candidate values, or raw spans.
"""

from __future__ import annotations

import datetime
import hashlib
import html
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .dictionary_loader import (
    load_field_label_terms,
    load_negative_context_terms,
    load_structured_context_terms,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
EVIDENCE_ROLE = "coverage_only_not_score_tuning"
SOURCE_TYPES = (
    "ecommerce_help",
    "institution_application",
    "healthcare_guide",
    "education_application",
    "enterprise_internal",
    "privacy_policy",
    "developer_docs",
    "synthetic_safe_template",
)

_RAW_PII_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    (
        "raw.email",
        re.compile(r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    ),
    ("raw.kr_phone", re.compile(r"(?<!\d)0\d{1,2}[-\s]?\d{3,4}[-\s]?\d{4}(?!\d)")),
    ("raw.rrn_like", re.compile(r"(?<!\d)\d{6}[-\s]?\d{7}(?!\d)")),
    (
        "raw.credit_card_like",
        re.compile(r"(?<!\d)(?:\d[ -]?){13,19}(?!\d)"),
    ),
    (
        "raw.account_like",
        re.compile(r"(?<!\d)(?!\d{4}-\d{2}-\d{2})\d{2,6}(?:[- ]\d{2,6}){2,4}(?!\d)"),
    ),
    (
        "raw.secret_like",
        re.compile(r"(?<![A-Za-z0-9_=-])(?:sk-[A-Za-z0-9_=-]{16,}|gh[po]_[A-Za-z0-9]{16,}|xox[bp]-[A-Za-z0-9-]{16,}|AKIA[0-9A-Z]{16})(?![A-Za-z0-9_=-])"),
    ),
)

_ENTITY_HINTS_BY_ANCHOR = {
    "name_label": ("PERSON_NAME",),
    "phone_label": ("PHONE_MOBILE", "PHONE_LANDLINE"),
    "email_label": ("EMAIL",),
    "address_label": ("ADDRESS_FULL", "ADDRESS_UNIT"),
    "account_label": ("BANK_ACCOUNT",),
    "organization_label": ("ORGANIZATION",),
    "medical_label": ("MEDICAL_RECORD_NO", "HOSPITAL", "HEALTH_INFO"),
    "order_id_label": (),
    "business_reg_no_label": ("BUSINESS_REG_NO",),
    "medical_record_no_label": ("MEDICAL_RECORD_NO",),
    "corporate_reg_no_label": ("CORPORATE_REG_NO",),
    "personal_reg_no_label": ("RRN", "FRN"),
    "passport_label": ("PASSPORT",),
    "driver_license_label": ("DRIVER_LICENSE",),
    "example_context": (),
    "weather_context": ("PERSON_NAME",),
    "public_number_context": ("PHONE_MOBILE", "PHONE_LANDLINE"),
    "code_context": ("PERSON_NAME", "ADDRESS_FULL", "ADDRESS_UNIT"),
    "business_name_context": ("PERSON_NAME", "ORGANIZATION"),
    "abstract_value_context": ("PERSON_NAME",),
}

_RULE_FAMILY_BY_ANCHOR_PREFIX = {
    "field": "field_label",
    "negative": "negative_context",
    "structured": "structured_identifier_context",
}

_TOKEN_CLASS_TERMS = {
    "order_context": ("주문", "배송", "수령", "송장", "결제", "환불", "purchase", "delivery"),
    "input_request": ("입력", "기재", "작성", "등록", "수정", "확인", "신청", "form", "input"),
    "support_context": ("문의", "고객센터", "콜센터", "상담", "support", "help"),
    "medical_context": ("환자", "병원", "진료", "차트", "의무기록", "health"),
    "education_context": ("학교", "입학", "장학", "학년", "교육"),
    "privacy_context": ("개인정보", "동의", "처리방침", "privacy"),
    "developer_context": ("debug", "error", "json", "로그", "변수", "stack"),
}


@dataclass(frozen=True)
class ContextWindowRow:
    source_type: str
    url_hash: str
    anchor_terms: tuple[str, ...]
    entity_hints: tuple[str, ...]
    left_token_classes: tuple[str, ...]
    right_token_classes: tuple[str, ...]
    contains_raw_pii: bool
    raw_value_logged: bool
    evidence_role: str = EVIDENCE_ROLE
    redaction_applied: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "source_type": self.source_type,
            "url_hash": self.url_hash,
            "anchor_terms": list(self.anchor_terms),
            "entity_hints": list(self.entity_hints),
            "left_token_classes": list(self.left_token_classes),
            "right_token_classes": list(self.right_token_classes),
            "contains_raw_pii": self.contains_raw_pii,
            "raw_value_logged": False,
            "evidence_role": self.evidence_role,
            "redaction_applied": self.redaction_applied,
        }


def url_hash(url: str) -> str:
    return "sha256:" + hashlib.sha256(url.encode("utf-8")).hexdigest()


def detect_raw_pii_like_values(text: str) -> tuple[str, ...]:
    """Return raw-PII pattern reason codes without exposing matched values."""

    return tuple(reason for reason, pattern in _RAW_PII_PATTERNS if pattern.search(text))


def redact_raw_pii_like_values(text: str) -> tuple[str, bool]:
    redacted = text
    redaction_applied = False
    for reason, pattern in _RAW_PII_PATTERNS:
        replacement = f"[{reason.upper()}_REDACTED]"
        redacted, count = pattern.subn(replacement, redacted)
        redaction_applied = redaction_applied or count > 0
    return redacted, redaction_applied


def build_context_window_row(
    *,
    source_type: str,
    url: str,
    sentence_text: str,
    project_root: Path = PROJECT_ROOT,
) -> ContextWindowRow | None:
    """Build a safe row from an in-memory sentence.

    Returns None when the sentence contains no known anchor class.
    """

    if source_type not in SOURCE_TYPES:
        raise ValueError("Unsupported source_type")

    redacted, redaction_applied = redact_raw_pii_like_values(sentence_text)
    anchor_terms = _anchor_classes(redacted, project_root)
    if not anchor_terms:
        return None

    first_anchor_index = _first_anchor_index(redacted, project_root)
    left_text = redacted[:first_anchor_index] if first_anchor_index is not None else ""
    right_text = redacted[first_anchor_index:] if first_anchor_index is not None else redacted
    entity_hints = sorted(
        {
            entity
            for anchor in anchor_terms
            for entity in _ENTITY_HINTS_BY_ANCHOR.get(_anchor_name(anchor), ())
        }
    )
    return ContextWindowRow(
        source_type=source_type,
        url_hash=url_hash(url),
        anchor_terms=anchor_terms,
        entity_hints=tuple(entity_hints),
        left_token_classes=_token_classes(left_text),
        right_token_classes=_token_classes(right_text),
        contains_raw_pii=bool(detect_raw_pii_like_values(redacted)),
        raw_value_logged=False,
        redaction_applied=redaction_applied,
    )


def extract_context_windows_from_html(
    *,
    html_text: str,
    source_type: str,
    url: str,
    project_root: Path = PROJECT_ROOT,
    max_windows: int = 50,
) -> tuple[ContextWindowRow, ...]:
    text = _strip_html(html_text)
    rows: list[ContextWindowRow] = []
    seen: set[tuple[Any, ...]] = set()
    for sentence in _sentence_candidates(text):
        row = build_context_window_row(
            source_type=source_type,
            url=url,
            sentence_text=sentence,
            project_root=project_root,
        )
        if row is None or row.contains_raw_pii:
            continue
        key = (
            row.source_type,
            row.url_hash,
            row.anchor_terms,
            row.entity_hints,
            row.left_token_classes,
            row.right_token_classes,
        )
        if key in seen:
            continue
        seen.add(key)
        rows.append(row)
        if len(rows) >= max_windows:
            break
    return tuple(rows)


def context_windows_jsonl(rows: Iterable[ContextWindowRow]) -> str:
    return "".join(
        json.dumps(row.to_dict(), ensure_ascii=False, sort_keys=True) + "\n"
        for row in rows
    )


def build_context_term_distribution(rows: Iterable[ContextWindowRow]) -> dict[str, Any]:
    row_list = list(rows)
    by_source_type = Counter(row.source_type for row in row_list)
    by_anchor_term: Counter[str] = Counter()
    by_rule_family: Counter[str] = Counter()
    by_entity_hint: Counter[str] = Counter()
    redaction_applied_count = 0
    for row in row_list:
        redaction_applied_count += int(row.redaction_applied)
        for anchor in row.anchor_terms:
            by_anchor_term[anchor] += 1
            by_rule_family[_rule_family(anchor)] += 1
        for entity in row.entity_hints:
            by_entity_hint[entity] += 1

    return {
        "report_type": "ContextTermDistribution",
        "version": "v0.2-single-turn",
        "phase": "Execution Phase 2. Safe Context Coverage",
        "evidence_role": EVIDENCE_ROLE,
        "public_corpus_used_for_score_tuning": False,
        "total_rows": len(row_list),
        "redaction_applied_count": redaction_applied_count,
        "by_source_type": dict(sorted(by_source_type.items())),
        "by_rule_family": dict(sorted(by_rule_family.items())),
        "by_anchor_term": dict(sorted(by_anchor_term.items())),
        "by_entity_hint": dict(sorted(by_entity_hint.items())),
        "raw_value_logged": False,
        "generated_at": _now(),
    }


def build_context_corpus_safety_report(
    *,
    rows: Iterable[ContextWindowRow],
    report_payloads: Iterable[object],
    source_urls: Iterable[str],
) -> dict[str, Any]:
    row_list = list(rows)
    scan = scan_context_window_outputs(
        rows=row_list,
        report_payloads=report_payloads,
        source_urls=source_urls,
    )
    return {
        "report_type": "ContextCorpusSafetyReport",
        "version": "v0.2-single-turn",
        "phase": "Execution Phase 2. Safe Context Coverage",
        "evidence_role": EVIDENCE_ROLE,
        "total_rows": len(row_list),
        "contains_raw_pii_true_count": scan["contains_raw_pii_true_count"],
        "raw_pii_leak_count": scan["raw_pii_leak_count"],
        "raw_url_logged_count": scan["raw_url_logged_count"],
        "raw_value_logged_count": scan["raw_value_logged_count"],
        "page_body_stored": False,
        "public_corpus_used_for_score_tuning": False,
        "status": "pass" if scan["status"] == "pass" else "fail",
        "reason_codes": scan["reason_codes"],
        "generated_at": _now(),
    }


def scan_context_window_outputs(
    *,
    rows: Iterable[ContextWindowRow],
    report_payloads: Iterable[object],
    source_urls: Iterable[str],
) -> dict[str, Any]:
    row_list = list(rows)
    report_strings = tuple(_iter_strings(report_payloads))
    raw_pii_leak_count = sum(
        1
        for reason, pattern in _RAW_PII_PATTERNS
        if any(pattern.search(text) for text in report_strings)
    )
    raw_url_logged_count = sum(
        1
        for source_url in source_urls
        if source_url and any(source_url in text for text in report_strings)
    )
    contains_raw_pii_true_count = sum(1 for row in row_list if row.contains_raw_pii)
    raw_value_logged_count = sum(1 for row in row_list if row.raw_value_logged)

    reason_codes: list[str] = []
    if contains_raw_pii_true_count:
        reason_codes.append("context_corpus.contains_raw_pii.fail")
    if raw_pii_leak_count:
        reason_codes.append("context_corpus.raw_pii_leak.fail")
    if raw_url_logged_count:
        reason_codes.append("context_corpus.raw_url_logged.fail")
    if raw_value_logged_count:
        reason_codes.append("context_corpus.raw_value_logged.fail")
    if not reason_codes:
        reason_codes.append("context_corpus.safety.pass")

    return {
        "contains_raw_pii_true_count": contains_raw_pii_true_count,
        "raw_pii_leak_count": raw_pii_leak_count,
        "raw_url_logged_count": raw_url_logged_count,
        "raw_value_logged_count": raw_value_logged_count,
        "reason_codes": reason_codes,
        "status": "pass" if reason_codes == ["context_corpus.safety.pass"] else "fail",
    }


def _anchor_classes(sentence_text: str, project_root: Path) -> tuple[str, ...]:
    anchors: set[str] = set()
    config_dir = project_root / "configs"
    for group, terms in load_field_label_terms(config_dir / "context_rules.yaml").items():
        if _contains_any(sentence_text, terms):
            anchors.add(f"field:{group}")
    for group, terms in load_negative_context_terms(config_dir / "context_rules.yaml").items():
        if _contains_any(sentence_text, terms):
            anchors.add(f"negative:{group}")
    for group, terms in load_structured_context_terms(config_dir / "context_rules.yaml").items():
        if _contains_any(sentence_text, terms):
            anchors.add(f"structured:{group}")
    return tuple(sorted(anchors))


def _first_anchor_index(sentence_text: str, project_root: Path) -> int | None:
    config_dir = project_root / "configs"
    indexes: list[int] = []
    for groups in (
        load_field_label_terms(config_dir / "context_rules.yaml"),
        load_negative_context_terms(config_dir / "context_rules.yaml"),
        load_structured_context_terms(config_dir / "context_rules.yaml"),
    ):
        for terms in groups.values():
            for term in terms:
                index = sentence_text.find(term)
                if index >= 0:
                    indexes.append(index)
    return min(indexes) if indexes else None


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    lowered = text.lower()
    return any(term and term.lower() in lowered for term in terms)


def _anchor_name(anchor: str) -> str:
    return anchor.split(":", 1)[-1]


def _rule_family(anchor: str) -> str:
    prefix = anchor.split(":", 1)[0]
    return _RULE_FAMILY_BY_ANCHOR_PREFIX.get(prefix, "unknown")


def _token_classes(text: str) -> tuple[str, ...]:
    classes = [
        class_name
        for class_name, terms in _TOKEN_CLASS_TERMS.items()
        if _contains_any(text, terms)
    ]
    return tuple(sorted(classes))


def _strip_html(html_text: str) -> str:
    without_scripts = re.sub(
        r"(?is)<(script|style|noscript).*?</\1>",
        " ",
        html_text,
    )
    without_tags = re.sub(r"(?s)<[^>]+>", " ", without_scripts)
    unescaped = html.unescape(without_tags)
    return re.sub(r"\s+", " ", unescaped).strip()


def _sentence_candidates(text: str) -> tuple[str, ...]:
    parts = re.split(r"(?<=[.!?。？！])\s+|[\r\n]+", text)
    return tuple(part.strip() for part in parts if len(part.strip()) >= 4)


def _iter_strings(payloads: Iterable[object]) -> Iterable[str]:
    for payload in payloads:
        if isinstance(payload, str):
            yield payload
        elif isinstance(payload, dict):
            yield json.dumps(payload, ensure_ascii=False, sort_keys=True)
        elif isinstance(payload, (list, tuple, set)):
            yield json.dumps(list(payload), ensure_ascii=False, sort_keys=True)
        else:
            yield str(payload)


def _now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()
