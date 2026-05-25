#!/usr/bin/env python3
"""Run the v0.2 release-gate evaluation with generated synthetic payloads.

Default scope is five release-gate buckets, 1,000 cases each:

- structured_pii
- name_address_affiliation
- single_turn_composite
- adversarial_boundary
- hard_negative

The generated dataset contains synthetic raw PII fixtures. Reports and failure
analysis outputs are raw-text-free.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import sys
import time
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pii_guardrail.audit_logger import AuditLogger, HMACKey, HMACKeyRing
from pii_guardrail.enums import EntityType, RiskLevel
from pii_guardrail.evaluation_harness import (
    CaseResult,
    EvaluationCase,
    EvaluationLabel,
    EvaluationReport,
    EvaluationRunner,
    build_audit_safety_report,
    count_report_raw_text_leaks,
    failure_analysis_jsonl,
)
from pii_guardrail.ner import FinetunedNERDetector, NERDependencyError
from pii_guardrail.pipeline import GuardrailPipeline
from pii_guardrail.schema import GuardrailRequest
from pii_guardrail.validators import rrn_check_digit


DEFAULT_REAL_NER_MODEL_PATH = "vmaca123/korean-pii-ner-v3"
DEFAULT_CASES_PER_BUCKET = 1000
DEFAULT_DATASET_OUTPUT = PROJECT_ROOT / "data" / "eval" / "generated" / "release_gate_v0_2_5000.jsonl"
DEFAULT_REPORT_OUTPUT = PROJECT_ROOT / "reports" / "release_gate_v0_2.json"
DEFAULT_FAILURE_OUTPUT = PROJECT_ROOT / "reports" / "failure_cases_release_gate_v0_2.jsonl"
DEFAULT_AUDIT_SAFETY_OUTPUT = PROJECT_ROOT / "reports" / "audit_safety_release_gate_v0_2.json"
DEFAULT_AUDIT_LOG_OUTPUT = PROJECT_ROOT / "reports" / "audit_release_gate_v0_2.jsonl"


K = {
    "customer_name": "\uace0\uac1d\uba85",
    "name": "\uc774\ub984",
    "contact": "\uc5f0\ub77d\ucc98",
    "phone": "\uc804\ud654\ubc88\ud638",
    "address_label": "\uc8fc\uc18c",
    "account": "\uacc4\uc88c",
    "deposit": "\uc785\uae08",
    "patient_no": "\ud658\uc790\ubc88\ud638",
    "hospital": "\ubcd1\uc6d0",
    "dob": "\uc0dd\ub144\uc6d4\uc77c",
    "school": "\ud559\uad50",
    "lives": "\uac70\uc8fc\ud569\ub2c8\ub2e4",
    "belongs": "\uc18c\uc18d\uc785\ub2c8\ub2e4",
    "is": "\uc785\ub2c8\ub2e4",
    "example": "\uc608\uc2dc",
    "sample": "\uc0d8\ud50c",
    "today": "\uc624\ub298",
    "sky": "\ud558\ub298",
    "clear": "\ub9d1\ub124\uc694",
    "love": "\uc0ac\ub791",
    "important": "\uc911\uc694\ud55c \uac00\uce58\uc785\ub2c8\ub2e4",
    "call_center": "\uace0\uac1d\uc13c\ud130",
    "store_name": "\uc0c1\ud638",
    "cafe": "\uce74\ud398",
    "privacy": "\uac1c\uc778\uc815\ubcf4",
    "mask_test": "\ub9c8\uc2a4\ud06c \ud14c\uc2a4\ud2b8",
}

NAMES = (
    "\ud64d\uae38\ub3d9",
    "\uae40\ubbfc\uc218",
    "\uc774\uc11c\uc5f0",
    "\ubc15\uc9c0\ud6c8",
    "\ucd5c\uc720\uc9c4",
    "\uc815\ud558\ub298",
    "\uac15\ub3c4\uc724",
    "\uc870\uc218\ube48",
    "\uc724\uc9c0\ud638",
    "\uc7a5\ubbfc\uc9c0",
)
ADDRESSES = (
    "\uc11c\uc6b8\uc2dc \uac15\ub0a8\uad6c \ud14c\ud5e4\ub780\ub85c",
    "\uc11c\uc6b8\uc2dc \uc1a1\ud30c\uad6c \uc62c\ub9bc\ud53d\ub85c",
    "\ubd80\uc0b0\uc2dc \ud574\uc6b4\ub300\uad6c \ud574\uc6b4\ub300\ub85c",
    "\ub300\uad6c\uc2dc \uc218\uc131\uad6c \ub2ec\uad6c\ubc8c\ub300\ub85c",
    "\uc778\ucc9c\uc2dc \ub0a8\ub3d9\uad6c \ubbf8\ub798\ub85c",
)
ADDRESS_UNITS = (
    "\uc11c\uc6b8\uc2dc \uac15\ub0a8\uad6c",
    "\ubd80\uc0b0\uc2dc \ud574\uc6b4\ub300\uad6c",
    "\uc778\ucc9c\uc2dc \ub0a8\ub3d9\uad6c",
)
ORGS = (
    "\uc0bc\uc131\uc804\uc790",
    "LG\uc804\uc790",
    "\uce74\uce74\uc624",
    "\ub124\uc774\ubc84",
    "\ud604\ub300\uc790\ub3d9\ucc28",
)
SCHOOLS = (
    "\uc11c\uc6b8\ub300\ud559\uad50",
    "\uc5f0\uc138\ub300\ud559\uad50",
    "\ud55c\uad6d\uace0\ub4f1\ud559\uad50",
)
HOSPITALS = (
    "\uc11c\uc6b8\ubcd1\uc6d0",
    "\uc911\uc559\ubcd1\uc6d0",
    "\uc138\ube0c\ub780\uc2a4\ubcd1\uc6d0",
)
RELATIONS = (
    "\uc544\ubc84\uc9c0",
    "\uc5b4\uba38\ub2c8",
    "\ubc30\uc6b0\uc790",
    "\uc790\ub140",
)


@dataclass(frozen=True)
class CaseBuild:
    text: str
    labels: tuple[EvaluationLabel, ...]


class CaseComposer:
    def __init__(self) -> None:
        self.parts: list[str] = []
        self.labels: list[EvaluationLabel] = []

    @property
    def pos(self) -> int:
        return sum(len(part) for part in self.parts)

    def text(self, value: str) -> None:
        self.parts.append(value)

    def span(
        self,
        value: str,
        entity_type: EntityType,
        risk_level: RiskLevel,
        *,
        suffix: str | None = None,
    ) -> None:
        start = self.pos
        self.parts.append(value)
        self.labels.append(
            EvaluationLabel(
                start=start,
                end=start + len(value),
                entity_type=entity_type,
                risk_level=risk_level,
                suffix=suffix,
            )
        )

    def build(self) -> CaseBuild:
        return CaseBuild("".join(self.parts), tuple(self.labels))


def _case(
    case_id: str,
    bucket: str,
    built: CaseBuild,
    *tags: str,
) -> EvaluationCase:
    return EvaluationCase(
        id=case_id,
        text=built.text,
        labels=built.labels,
        tags=(bucket, *tags),
    )


def _single_span_case(
    *,
    case_id: str,
    bucket: str,
    prefix: str,
    value: str,
    entity_type: EntityType,
    risk_level: RiskLevel,
    suffix: str = "",
    tail: str = ".",
    tags: tuple[str, ...] = (),
) -> EvaluationCase:
    c = CaseComposer()
    c.text(prefix)
    c.span(value, entity_type, risk_level, suffix=suffix or None)
    c.text(suffix)
    c.text(tail)
    return _case(case_id, bucket, c.build(), *tags)


def _luhn_check_digit(prefix: str) -> str:
    for digit in "0123456789":
        candidate = prefix + digit
        total = 0
        parity = len(candidate) % 2
        for index, char in enumerate(candidate):
            number = int(char)
            if index % 2 == parity:
                number *= 2
                if number > 9:
                    number -= 9
            total += number
        if total % 10 == 0:
            return digit
    raise ValueError("Unable to generate Luhn check digit")


def _business_check_digit(first_9: str) -> str:
    weights = (1, 3, 7, 1, 3, 7, 1, 3, 5)
    weighted_sum = sum(int(digit) * weight for digit, weight in zip(first_9[:8], weights[:8], strict=True))
    ninth_product = int(first_9[8]) * weights[8]
    weighted_sum += ninth_product // 10 + ninth_product % 10
    return str((10 - (weighted_sum % 10)) % 10)


def _rrn(i: int, *, foreigner: bool = False) -> str:
    year = 1970 + (i % 50)
    month = 1 + (i % 12)
    day = 1 + (i % 28)
    birth = dt.date(year, month, day).strftime("%y%m%d")
    if foreigner:
        gender = "5" if year < 2000 else "7"
    else:
        gender = "1" if year < 2000 else "3"
    first_12 = birth + gender + f"{(i * 7919) % 100000:05d}"
    return first_12[:6] + "-" + first_12[6:] + rrn_check_digit(first_12)


def _credit_card(i: int) -> str:
    first_15 = "411111" + f"{(i * 104729) % 1_000_000_000:09d}"
    digits = first_15 + _luhn_check_digit(first_15)
    return f"{digits[:4]}-{digits[4:8]}-{digits[8:12]}-{digits[12:]}"


def _business_reg_no(i: int) -> str:
    first_9 = f"{100000000 + ((i * 37) % 899999999):09d}"
    digits = first_9 + _business_check_digit(first_9)
    return f"{digits[:3]}-{digits[3:5]}-{digits[5:]}"


def _api_key(i: int) -> str:
    tail = f"AbC{i:06d}xYz987SecretTokenValue"
    return "sk-" + tail


def _phone_mobile(i: int) -> str:
    return f"010-{1000 + (i % 9000):04d}-{1000 + ((i * 7) % 9000):04d}"


def _phone_landline(i: int) -> str:
    return f"02-{2000 + (i % 7000):04d}-{1000 + ((i * 11) % 9000):04d}"


def _email(i: int) -> str:
    return f"user{i:04d}.gate@example{i % 97}.com"


def _bank_account(i: int) -> str:
    return f"{100000 + (i % 900000):06d}-{10 + (i % 89):02d}-{100000 + ((i * 13) % 900000):06d}"


def _mac(i: int) -> str:
    octets = [(i + j * 17) % 256 for j in range(6)]
    return ":".join(f"{octet:02X}" for octet in octets)


def _structured_case(i: int) -> EvaluationCase:
    bucket = "structured_pii"
    kind = i % 17
    if kind == 0:
        return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix="RRN ", value=_rrn(i), entity_type=EntityType.RRN, risk_level=RiskLevel.P0, tags=("rrn",))
    if kind == 1:
        return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix="FRN ", value=_rrn(i, foreigner=True), entity_type=EntityType.FRN, risk_level=RiskLevel.P0, tags=("frn",))
    if kind == 2:
        return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix=f"{K['contact']} ", value=_phone_mobile(i), entity_type=EntityType.PHONE_MOBILE, risk_level=RiskLevel.P1, tags=("phone",))
    if kind == 3:
        return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix=f"{K['phone']} ", value=_phone_landline(i), entity_type=EntityType.PHONE_LANDLINE, risk_level=RiskLevel.P1, tags=("phone",))
    if kind == 4:
        return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix="email ", value=_email(i), entity_type=EntityType.EMAIL, risk_level=RiskLevel.P1, tags=("email",))
    if kind == 5:
        return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix="card ", value=_credit_card(i), entity_type=EntityType.CREDIT_CARD, risk_level=RiskLevel.P0, tags=("credit_card",))
    if kind == 6:
        return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix=f"{K['account']} ", value=_bank_account(i), entity_type=EntityType.BANK_ACCOUNT, risk_level=RiskLevel.P1, tags=("bank_account",))
    if kind == 7:
        return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix="business ", value=_business_reg_no(i), entity_type=EntityType.BUSINESS_REG_NO, risk_level=RiskLevel.P1, tags=("business_reg_no",))
    if kind == 8:
        return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix="secret ", value=_api_key(i), entity_type=EntityType.API_KEY_SECRET, risk_level=RiskLevel.P0, tags=("secret",))
    if kind == 9:
        return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix="ip ", value=f"8.8.{i % 255}.{(i * 3) % 255}", entity_type=EntityType.IP_ADDRESS, risk_level=RiskLevel.P2, tags=("ip",))
    if kind == 10:
        return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix="mac ", value=_mac(i), entity_type=EntityType.MAC_ADDRESS, risk_level=RiskLevel.P2, tags=("mac",))
    if kind == 11:
        return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix="passport ", value=f"M{i % 10}{(1234567 + i) % 10000000:07d}", entity_type=EntityType.PASSPORT, risk_level=RiskLevel.P0, tags=("passport",))
    if kind == 12:
        return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix="driver license ", value=f"12-{10 + i % 80:02d}-{100000 + i:06d}-01", entity_type=EntityType.DRIVER_LICENSE, risk_level=RiskLevel.P0, tags=("driver_license",))
    if kind == 13:
        return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix=f"{K['patient_no']} ", value=f"MR-{2026}-{i:06d}", entity_type=EntityType.MEDICAL_RECORD_NO, risk_level=RiskLevel.P1, tags=("medical_record",))
    if kind == 14:
        return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix="corp ", value=f"110111-{1000000 + i:07d}", entity_type=EntityType.CORPORATE_REG_NO, risk_level=RiskLevel.P1, tags=("corporate_reg_no",))
    if kind == 15:
        return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix="vehicle ", value=f"{10 + i % 80}\uac00{1000 + i % 9000}", entity_type=EntityType.VEHICLE_REG_NO, risk_level=RiskLevel.P1, tags=("vehicle_reg_no",))
    return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix="device ", value=f"device-{i:04d}-A1B2C3", entity_type=EntityType.DEVICE_ID, risk_level=RiskLevel.P2, tags=("device_id",))


def _name_address_case(i: int) -> EvaluationCase:
    bucket = "name_address_affiliation"
    kind = i % 8
    name = NAMES[i % len(NAMES)]
    address = f"{ADDRESSES[i % len(ADDRESSES)]} {10 + i % 200}"
    if kind == 0:
        return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix="", value=name, entity_type=EntityType.PERSON_NAME, risk_level=RiskLevel.P1, suffix="\uc740", tail=f" {K['is']}.", tags=("person_name", "boundary"))
    if kind == 1:
        c = CaseComposer()
        c.span(name, EntityType.PERSON_NAME, RiskLevel.P1, suffix="\uc740")
        c.text("\uc740 ")
        c.span(address, EntityType.ADDRESS_FULL, RiskLevel.P1, suffix="\uc5d0")
        c.text(f"\uc5d0 {K['lives']}.")
        return _case(f"{bucket}-{i:04d}", bucket, c.build(), "address_full", "person_context")
    if kind == 2:
        return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix=f"{K['address_label']} ", value=ADDRESS_UNITS[i % len(ADDRESS_UNITS)], entity_type=EntityType.ADDRESS_UNIT, risk_level=RiskLevel.P2, tail=".", tags=("address_unit",))
    if kind == 3:
        c = CaseComposer()
        c.span(name, EntityType.PERSON_NAME, RiskLevel.P1, suffix="\uc740")
        c.text("\uc740 ")
        c.span(ORGS[i % len(ORGS)], EntityType.ORGANIZATION, RiskLevel.P2)
        c.text(f" {K['belongs']}.")
        return _case(f"{bucket}-{i:04d}", bucket, c.build(), "organization", "person_context")
    if kind == 4:
        return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix=f"{K['school']} ", value=SCHOOLS[i % len(SCHOOLS)], entity_type=EntityType.SCHOOL, risk_level=RiskLevel.P2, tail=".", tags=("school",))
    if kind == 5:
        return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix=f"{K['hospital']} ", value=HOSPITALS[i % len(HOSPITALS)], entity_type=EntityType.HOSPITAL, risk_level=RiskLevel.P2, tail=".", tags=("hospital",))
    if kind == 6:
        c = CaseComposer()
        c.span(RELATIONS[i % len(RELATIONS)], EntityType.FAMILY_RELATION, RiskLevel.P2)
        c.text(f" {K['contact']} ")
        c.span(_phone_mobile(i), EntityType.PHONE_MOBILE, RiskLevel.P1)
        c.text(".")
        return _case(f"{bucket}-{i:04d}", bucket, c.build(), "family_relation", "contact")
    c = CaseComposer()
    c.text(f"{K['name']} ")
    c.span(name, EntityType.PERSON_NAME, RiskLevel.P1)
    c.text(f", {K['address_label']} ")
    c.span(address, EntityType.ADDRESS_FULL, RiskLevel.P1)
    c.text(".")
    return _case(f"{bucket}-{i:04d}", bucket, c.build(), "person_name", "address_context")


def _composite_case(i: int) -> EvaluationCase:
    bucket = "single_turn_composite"
    kind = i % 7
    name = NAMES[i % len(NAMES)]
    c = CaseComposer()
    if kind == 0:
        c.span(name, EntityType.PERSON_NAME, RiskLevel.P1)
        c.text(f"\uc758 {K['contact']} ")
        c.span(_phone_mobile(i), EntityType.PHONE_MOBILE, RiskLevel.P1)
    elif kind == 1:
        c.span(name, EntityType.PERSON_NAME, RiskLevel.P1)
        c.text(" email ")
        c.span(_email(i), EntityType.EMAIL, RiskLevel.P1)
    elif kind == 2:
        c.span(name, EntityType.PERSON_NAME, RiskLevel.P1)
        c.text(f"\uc740 ")
        c.span(f"{ADDRESSES[i % len(ADDRESSES)]} {20 + i % 300}", EntityType.ADDRESS_FULL, RiskLevel.P1)
        c.text(f"\uc5d0 {K['lives']}")
    elif kind == 3:
        c.span(name, EntityType.PERSON_NAME, RiskLevel.P1)
        c.text(f" {K['account']} ")
        c.span(_bank_account(i), EntityType.BANK_ACCOUNT, RiskLevel.P1)
    elif kind == 4:
        c.text(f"{K['patient_no']} ")
        c.span(f"MR-{2026}-{i:06d}", EntityType.MEDICAL_RECORD_NO, RiskLevel.P1)
        c.text(f", {K['contact']} ")
        c.span(_phone_mobile(i), EntityType.PHONE_MOBILE, RiskLevel.P1)
    elif kind == 5:
        c.text(f"{K['patient_no']} ")
        c.span(f"MR-{2026}-{i:06d}", EntityType.MEDICAL_RECORD_NO, RiskLevel.P1)
        c.text(", ")
        c.span(HOSPITALS[i % len(HOSPITALS)], EntityType.HOSPITAL, RiskLevel.P2)
    else:
        c.text(f"{K['dob']} ")
        c.span(f"{1980 + i % 35}\ub144 {1 + i % 12}\uc6d4 {1 + i % 28}\uc77c", EntityType.DOB, RiskLevel.P2)
        c.text(", ")
        c.span(ADDRESS_UNITS[i % len(ADDRESS_UNITS)], EntityType.ADDRESS_UNIT, RiskLevel.P2)
        c.text(", ")
        c.span(SCHOOLS[i % len(SCHOOLS)], EntityType.SCHOOL, RiskLevel.P2)
    c.text(".")
    return _case(f"{bucket}-{i:04d}", bucket, c.build(), "single_turn_composite")


def _fullwidth_digits(value: str) -> str:
    result = []
    for char in value:
        if char.isdigit():
            result.append(chr(ord("\uff10") + int(char)))
        else:
            result.append(char)
    return "".join(result)


def _adversarial_case(i: int) -> EvaluationCase:
    bucket = "adversarial_boundary"
    kind = i % 8
    name = NAMES[i % len(NAMES)]
    if kind == 0:
        c = CaseComposer()
        c.span(name, EntityType.PERSON_NAME, RiskLevel.P1, suffix="\uc774")
        c.text(f"\uc774 {K['contact']} ")
        c.span(_phone_mobile(i), EntityType.PHONE_MOBILE, RiskLevel.P1)
        c.text(".")
        return _case(f"{bucket}-{i:04d}", bucket, c.build(), "josa_boundary", "contact")
    if kind == 1:
        return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix=f"{K['contact']} ", value=_phone_mobile(i), entity_type=EntityType.PHONE_MOBILE, risk_level=RiskLevel.P1, suffix="\ub85c", tail=".", tags=("suffix_boundary",))
    if kind == 2:
        value = _fullwidth_digits(_phone_mobile(i))
        return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix=f"{K['phone']} ", value=value, entity_type=EntityType.PHONE_MOBILE, risk_level=RiskLevel.P1, tags=("nfkc_digits",))
    if kind == 3:
        value = _rrn(i).replace("-", " - ")
        return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix="RRN ", value=value, entity_type=EntityType.RRN, risk_level=RiskLevel.P0, tags=("spaced_digits",))
    if kind == 4:
        value = _phone_mobile(i).replace("-", "\u2011")
        return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix=f"{K['phone']} ", value=value, entity_type=EntityType.PHONE_MOBILE, risk_level=RiskLevel.P1, tags=("dash_normalization",))
    if kind == 5:
        value = _phone_mobile(i).replace("-", "\u200b-\u200b")
        return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix=f"{K['phone']} ", value=value, entity_type=EntityType.PHONE_MOBILE, risk_level=RiskLevel.P1, tags=("zero_width",))
    if kind == 6:
        value = f"{ADDRESSES[i % len(ADDRESSES)]} {100 + i % 800}\ubc88\uc9c0"
        return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix="", value=value, entity_type=EntityType.ADDRESS_FULL, risk_level=RiskLevel.P1, suffix="\uc5d0", tail=f" {K['lives']}.", tags=("address_boundary",))
    value = _credit_card(i).replace("-", " ")
    return _single_span_case(case_id=f"{bucket}-{i:04d}", bucket=bucket, prefix="card ", value=value, entity_type=EntityType.CREDIT_CARD, risk_level=RiskLevel.P0, tags=("digit_spacing",))


def _hard_negative_case(i: int) -> EvaluationCase:
    bucket = "hard_negative"
    variants = (
        f"{K['today']} {K['sky']}\uc774 {K['clear']}.",
        f"{K['love']}\uc740 {K['important']}.",
        f"{K['example']} {K['phone']} 010-0000-0000{K['is']}.",
        f"{K['call_center']} \ubc88\ud638\ub294 1588-{1000 + i % 9000}\uc785\ub2c8\ub2e4.",
        f"{K['sample']} email user@example.com.",
        f"debug token value is sample-{i:04d}.",
        f"{K['store_name']} {NAMES[i % len(NAMES)]}{K['cafe']} \uc624\ud508.",
        f"order id {100000 + i} is ready.",
    )
    return EvaluationCase(
        id=f"{bucket}-{i:04d}",
        text=variants[i % len(variants)],
        labels=(),
        tags=(bucket, "hard_negative"),
    )


def generate_release_gate_cases(cases_per_bucket: int) -> list[EvaluationCase]:
    generators = (
        _structured_case,
        _name_address_case,
        _composite_case,
        _adversarial_case,
        _hard_negative_case,
    )
    cases: list[EvaluationCase] = []
    for generator in generators:
        for i in range(cases_per_bucket):
            cases.append(generator(i))
    return cases


def write_cases_jsonl(cases: list[EvaluationCase], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    for case in cases:
        payload: dict[str, object] = {
            "id": case.id,
            "text": case.text,
            "labels": [
                {
                    "start": label.start,
                    "end": label.end,
                    "entity_type": label.entity_type.value,
                    "risk_level": label.risk_level.value,
                    **({"suffix": label.suffix} if label.suffix else {}),
                }
                for label in case.labels
            ],
            "tags": list(case.tags),
        }
        lines.append(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _prepare_audit_log_output(path: Path) -> Path:
    if not path.exists():
        return path
    try:
        path.unlink()
        return path
    except PermissionError:
        stamp = dt.datetime.now(dt.UTC).strftime("%Y%m%dT%H%M%SZ")
        return path.with_name(f"{path.stem}.{stamp}{path.suffix}")


def _safe_report_summary(report: EvaluationReport, *, purpose_id: str) -> dict[str, object]:
    payload = report.to_safe_dict(purpose_id=purpose_id)
    return {
        "dataset_id": payload["dataset_id"],
        "records_processed": payload["records_processed"],
        "blocked_count": payload["blocked_count"],
        "spans_detected": payload["spans_detected"],
        "spans_masked": payload["spans_masked"],
        "high_risk_recall": payload["high_risk_recall"],
        "boundary_accuracy": payload["boundary_accuracy"],
        "overall": payload["overall"],
        "per_entity": payload["per_entity"],
        "release_gate": payload["release_gate"],
        "raw_pii_logging_count": payload["raw_pii_logging_count"],
        "invalid_offset_count": payload["invalid_offset_count"],
        "deterministic_latency_ms": payload["deterministic_latency_ms"],
        "real_ner_latency_ms": payload["real_ner_latency_ms"],
        "ner_detector": payload["ner_detector"],
        "residual_risk_notes": payload["residual_risk_notes"],
        "spurious_detections": payload["spurious_detections"],
    }


def _bucket_from_case(case: EvaluationCase) -> str:
    return case.tags[0] if case.tags else "unknown"


def _label_counts(cases: list[EvaluationCase]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for case in cases:
        for label in case.labels:
            counts[label.entity_type.value] += 1
    return dict(sorted(counts.items()))


def _action_counts(results: list[CaseResult]) -> dict[str, int]:
    counts: Counter[str] = Counter()
    for result in results:
        for match in result.matches:
            if match.actual is not None:
                counts[match.actual.action.value] += 1
    return dict(sorted(counts.items()))


def evaluate_once(
    *,
    cases: list[EvaluationCase],
    pipeline: GuardrailPipeline,
    progress_interval: int,
) -> tuple[EvaluationRunner, list[CaseResult]]:
    runner = EvaluationRunner(pipeline)
    results: list[CaseResult] = []
    total = len(cases)
    started = time.perf_counter()
    for index, case in enumerate(cases, start=1):
        request = GuardrailRequest(text=case.text, request_id=f"release-gate-{case.id}")
        response = pipeline.process(request)
        results.append(runner._build_case_result(case, response))  # noqa: SLF001
        if progress_interval and index % progress_interval == 0:
            elapsed = time.perf_counter() - started
            print(f"processed {index}/{total} cases in {elapsed:.1f}s", flush=True)
    return runner, results


def build_reports(
    *,
    runner: EvaluationRunner,
    cases: list[EvaluationCase],
    results: list[CaseResult],
    purpose_id: str,
) -> tuple[EvaluationReport, dict[str, object]]:
    combined = runner._aggregate("release_gate_v0_2", cases, results)  # noqa: SLF001
    cases_by_bucket: dict[str, list[EvaluationCase]] = defaultdict(list)
    results_by_bucket: dict[str, list[CaseResult]] = defaultdict(list)
    case_by_id = {case.id: case for case in cases}
    for result in results:
        case = case_by_id[result.case_id]
        bucket = _bucket_from_case(case)
        cases_by_bucket[bucket].append(case)
        results_by_bucket[bucket].append(result)

    bucket_reports = {}
    for bucket in sorted(cases_by_bucket):
        report = runner._aggregate(  # noqa: SLF001
            f"release_gate_v0_2_{bucket}",
            cases_by_bucket[bucket],
            results_by_bucket[bucket],
        )
        bucket_reports[bucket] = _safe_report_summary(report, purpose_id=purpose_id)
        bucket_reports[bucket]["label_counts"] = _label_counts(cases_by_bucket[bucket])
        bucket_reports[bucket]["action_counts"] = _action_counts(results_by_bucket[bucket])

    payload = combined.to_safe_dict(purpose_id=purpose_id)
    payload["payload_generation"] = {
        "synthetic": True,
        "raw_data_policy": "synthetic fixtures only; no production PII",
        "bucket_counts": {
            bucket: len(bucket_cases)
            for bucket, bucket_cases in sorted(cases_by_bucket.items())
        },
        "total_cases": len(cases),
        "label_counts": _label_counts(cases),
    }
    payload["action_counts"] = _action_counts(results)
    payload["per_bucket"] = bucket_reports
    return combined, payload


def build_pipeline(
    *,
    config_dir: Path,
    audit_log_output: Path,
    ner_model_path: str,
    ner_calibration_path: str | None,
) -> GuardrailPipeline:
    audit_log_output.parent.mkdir(parents=True, exist_ok=True)
    keyring = HMACKeyRing(
        keys={
            "release-gate-v1": HMACKey(
                key_id="release-gate-v1",
                secret=b"release-gate-synthetic-hmac-key-v0.2-32-bytes",
            )
        },
        active_id="release-gate-v1",
    )
    audit_logger = AuditLogger(keyring=keyring, log_path=audit_log_output)
    return GuardrailPipeline.from_config_dir(
        config_dir,
        ner_detector=FinetunedNERDetector(
            model_path=ner_model_path,
            calibration_path=ner_calibration_path,
        ),
        audit_logger=audit_logger,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate 1,000 synthetic cases per release-gate bucket and evaluate with real NER."
    )
    parser.add_argument("--cases-per-bucket", type=int, default=DEFAULT_CASES_PER_BUCKET)
    parser.add_argument("--config-dir", type=Path, default=PROJECT_ROOT / "configs")
    parser.add_argument("--dataset-output", type=Path, default=DEFAULT_DATASET_OUTPUT)
    parser.add_argument("--report-output", type=Path, default=DEFAULT_REPORT_OUTPUT)
    parser.add_argument("--failure-output", type=Path, default=DEFAULT_FAILURE_OUTPUT)
    parser.add_argument("--audit-safety-output", type=Path, default=DEFAULT_AUDIT_SAFETY_OUTPUT)
    parser.add_argument("--audit-log-output", type=Path, default=DEFAULT_AUDIT_LOG_OUTPUT)
    parser.add_argument("--ner-model-path", default=DEFAULT_REAL_NER_MODEL_PATH)
    parser.add_argument("--ner-calibration-path")
    parser.add_argument("--progress-interval", type=int, default=250)
    parser.add_argument("--purpose-id", default="ko_pii_guardrail_v0_2_release_gate")
    args = parser.parse_args()

    if args.cases_per_bucket <= 0:
        parser.error("--cases-per-bucket must be positive")

    cases = generate_release_gate_cases(args.cases_per_bucket)
    write_cases_jsonl(cases, args.dataset_output)
    print(f"Wrote synthetic dataset: {args.dataset_output} ({len(cases)} cases)", flush=True)

    args.audit_log_output = _prepare_audit_log_output(args.audit_log_output)

    try:
        pipeline = build_pipeline(
            config_dir=args.config_dir,
            audit_log_output=args.audit_log_output,
            ner_model_path=args.ner_model_path,
            ner_calibration_path=args.ner_calibration_path,
        )
        runner, results = evaluate_once(
            cases=cases,
            pipeline=pipeline,
            progress_interval=args.progress_interval,
        )
    except NERDependencyError as exc:
        raise SystemExit(f"Release gate failed to start real NER: {exc}") from exc

    report, payload = build_reports(
        runner=runner,
        cases=cases,
        results=results,
        purpose_id=args.purpose_id,
    )

    args.report_output.parent.mkdir(parents=True, exist_ok=True)
    report_text = json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    args.report_output.write_text(report_text, encoding="utf-8")

    failure_text = failure_analysis_jsonl(report)
    args.failure_output.parent.mkdir(parents=True, exist_ok=True)
    args.failure_output.write_text(failure_text, encoding="utf-8")

    audit_log_text = (
        args.audit_log_output.read_text(encoding="utf-8")
        if args.audit_log_output.exists()
        else ""
    )
    leak_count = count_report_raw_text_leaks(
        [report_text, failure_text, audit_log_text],
        cases,
    )
    audit_safety = build_audit_safety_report(
        report,
        report_raw_text_leak_count=leak_count,
        safe_report_generated=True,
    )
    args.audit_safety_output.parent.mkdir(parents=True, exist_ok=True)
    args.audit_safety_output.write_text(
        json.dumps(audit_safety.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)
        + "\n",
        encoding="utf-8",
    )

    print(f"Wrote release gate report: {args.report_output}", flush=True)
    print(f"Wrote failure analysis report: {args.failure_output}", flush=True)
    print(f"Wrote audit safety report: {args.audit_safety_output}", flush=True)
    print(f"Wrote audit log: {args.audit_log_output}", flush=True)
    print(
        "release_gate_status="
        f"{payload['release_gate']['overall_status']} "
        f"records={payload['records_processed']} "
        f"overall_recall={payload['overall']['recall']} "
        f"overall_f1={payload['overall']['f1']} "
        f"raw_pii_leaks={leak_count}",
        flush=True,
    )


if __name__ == "__main__":
    main()
