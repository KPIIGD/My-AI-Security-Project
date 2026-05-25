#!/usr/bin/env python3
"""Generate stage4 CORPORATE_REG_NO/RRN marker fixtures."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


WEIGHTS = (2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4, 5)


@dataclass(frozen=True)
class CaseSpec:
    id: str
    marked_text: str
    expected_masked_text: str
    tags: tuple[str, ...]
    bucket: str
    risk_focus: str
    notes: str | None = None

    def to_json(self) -> str:
        payload: dict[str, object] = {
            "id": self.id,
            "marked_text": self.marked_text,
            "expected_masked_text": self.expected_masked_text,
            "tags": list(self.tags),
            "bucket": self.bucket,
            "risk_focus": self.risk_focus,
        }
        if self.notes is not None:
            payload["notes"] = self.notes
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


CORPORATE_FIRST_12 = (
    "110111100000",
    "110111123456",
    "110111200000",
    "110111300000",
    "110114100123",
    "110114200123",
    "110115100456",
    "110115200456",
    "110121100789",
    "110121200789",
)

CORPORATE_PATTERN_VALUES = (
    "110111-1234567",
    "110114-7654321",
    "110115-2345678",
    "110121-3456789",
    "134511-4567890",
    "110111-9876543",
    "110114-8765432",
    "110115-7654321",
    "110121-6543210",
    "134511-5432109",
)

RRN_FIRST_12 = (
    "900101123456",
    "850505212345",
    "010101312345",
    "990101412345",
    "760707134567",
    "820303245678",
    "020202356789",
    "040404467890",
    "110111100000",
    "110111200000",
    "920229123456",
    "000229312345",
    "880808198765",
    "930909287654",
    "050505376543",
    "060606465432",
    "790101112233",
    "810202223344",
    "030303334455",
    "070707445566",
)

CORPORATE_CONTEXT_TEMPLATES = (
    (
        "corporate_label",
        "\ubc95\uc778\ub4f1\ub85d\ubc88\ud638 <CORPORATE_REG_NO risk=\"P1\">{value}</CORPORATE_REG_NO> \ud655\uc778 \uc644\ub8cc.",
        "\ubc95\uc778\ub4f1\ub85d\ubc88\ud638 [CORPORATE_REG_NO_1] \ud655\uc778 \uc644\ub8cc.",
    ),
    (
        "registry_no",
        "\ub4f1\uae30\ubc88\ud638\ub294 <CORPORATE_REG_NO risk=\"P1\">{value}</CORPORATE_REG_NO>\uc785\ub2c8\ub2e4.",
        "\ub4f1\uae30\ubc88\ud638\ub294 [CORPORATE_REG_NO_1]\uc785\ub2c8\ub2e4.",
    ),
    (
        "legal_team",
        "\ubc95\ubb34\ud300\uc774 \ubc95\uc778\ubc88\ud638 <CORPORATE_REG_NO risk=\"P1\">{value}</CORPORATE_REG_NO>\ub97c \uac80\ud1a0\ud588\uc2b5\ub2c8\ub2e4.",
        "\ubc95\ubb34\ud300\uc774 \ubc95\uc778\ubc88\ud638 [CORPORATE_REG_NO_1]\ub97c \uac80\ud1a0\ud588\uc2b5\ub2c8\ub2e4.",
    ),
    (
        "partner_company",
        "\uac70\ub798\ucc98 \ubc95\uc778\ub4f1\ub85d\ubc88\ud638: <CORPORATE_REG_NO risk=\"P1\">{value}</CORPORATE_REG_NO>",
        "\uac70\ub798\ucc98 \ubc95\uc778\ub4f1\ub85d\ubc88\ud638: [CORPORATE_REG_NO_1]",
    ),
    (
        "company_registration",
        "\ud68c\uc0ac \ub4f1\ub85d\ubc88\ud638 <CORPORATE_REG_NO risk=\"P1\">{value}</CORPORATE_REG_NO> \uc870\ud68c \uc131\uacf5.",
        "\ud68c\uc0ac \ub4f1\ub85d\ubc88\ud638 [CORPORATE_REG_NO_1] \uc870\ud68c \uc131\uacf5.",
    ),
    (
        "registry_document",
        "\ub4f1\uae30\ubd80 \ubc95\uc778\ubc88\ud638 <CORPORATE_REG_NO risk=\"P1\">{value}</CORPORATE_REG_NO>\ub97c \uae30\ub85d\ud588\uc2b5\ub2c8\ub2e4.",
        "\ub4f1\uae30\ubd80 \ubc95\uc778\ubc88\ud638 [CORPORATE_REG_NO_1]\ub97c \uae30\ub85d\ud588\uc2b5\ub2c8\ub2e4.",
    ),
    (
        "contract_review",
        "\uacc4\uc57d\uc11c\uc758 \ubc95\uc778\ub4f1\ub85d\ubc88\ud638 <CORPORATE_REG_NO risk=\"P1\">{value}</CORPORATE_REG_NO> \ud45c\uae30\ub97c \ud655\uc778.",
        "\uacc4\uc57d\uc11c\uc758 \ubc95\uc778\ub4f1\ub85d\ubc88\ud638 [CORPORATE_REG_NO_1] \ud45c\uae30\ub97c \ud655\uc778.",
    ),
    (
        "corporate_reg_no_en",
        "corporate reg no <CORPORATE_REG_NO risk=\"P1\">{value}</CORPORATE_REG_NO> checked.",
        "corporate reg no [CORPORATE_REG_NO_1] checked.",
    ),
    (
        "corp_number_en",
        "corp number <CORPORATE_REG_NO risk=\"P1\">{value}</CORPORATE_REG_NO> verified.",
        "corp number [CORPORATE_REG_NO_1] verified.",
    ),
    (
        "legal_entity_no",
        "\ubc95\uc778 \uc2dd\ubcc4\ubc88\ud638 <CORPORATE_REG_NO risk=\"P1\">{value}</CORPORATE_REG_NO>\ub85c \uc800\uc7a5\ud588\uc2b5\ub2c8\ub2e4.",
        "\ubc95\uc778 \uc2dd\ubcc4\ubc88\ud638 [CORPORATE_REG_NO_1]\ub85c \uc800\uc7a5\ud588\uc2b5\ub2c8\ub2e4.",
    ),
)

RRN_CONTEXT_TEMPLATES = (
    (
        "rrn_label",
        "\uc8fc\ubbfc\ub4f1\ub85d\ubc88\ud638 <RRN risk=\"P0\">{value}</RRN> \ud655\uc778.",
        "\uc8fc\ubbfc\ub4f1\ub85d\ubc88\ud638 [REDACTED] \ud655\uc778.",
    ),
    (
        "jumin_no",
        "\uc8fc\ubbfc\ubc88\ud638\ub294 <RRN risk=\"P0\">{value}</RRN>\uc785\ub2c8\ub2e4.",
        "\uc8fc\ubbfc\ubc88\ud638\ub294 [REDACTED]\uc785\ub2c8\ub2e4.",
    ),
    (
        "identity_check",
        "\ubcf8\uc778 \ud655\uc778\uc6a9 \uc8fc\ubbfc\ub4f1\ub85d\ubc88\ud638 <RRN risk=\"P0\">{value}</RRN>\ub97c \uc785\ub825\ud588\uc2b5\ub2c8\ub2e4.",
        "\ubcf8\uc778 \ud655\uc778\uc6a9 \uc8fc\ubbfc\ub4f1\ub85d\ubc88\ud638 [REDACTED]\ub97c \uc785\ub825\ud588\uc2b5\ub2c8\ub2e4.",
    ),
    (
        "customer_rrn",
        "\uace0\uac1d \uc8fc\ubbfc\ub4f1\ub85d\ubc88\ud638: <RRN risk=\"P0\">{value}</RRN>",
        "\uace0\uac1d \uc8fc\ubbfc\ub4f1\ub85d\ubc88\ud638: [REDACTED]",
    ),
    (
        "verification_rrn",
        "\uc778\uc99d \uc694\uccad\uc5d0 \uc8fc\ubbfc\ubc88\ud638 <RRN risk=\"P0\">{value}</RRN>\uac00 \ud3ec\ud568\ub418\uc5c8\uc2b5\ub2c8\ub2e4.",
        "\uc778\uc99d \uc694\uccad\uc5d0 \uc8fc\ubbfc\ubc88\ud638 [REDACTED]\uac00 \ud3ec\ud568\ub418\uc5c8\uc2b5\ub2c8\ub2e4.",
    ),
    (
        "guardian_rrn",
        "\ubc95\uc815\ub300\ub9ac\uc778 \uc8fc\ubbfc\ub4f1\ub85d\ubc88\ud638 <RRN risk=\"P0\">{value}</RRN> \ud655\uc778.",
        "\ubc95\uc815\ub300\ub9ac\uc778 \uc8fc\ubbfc\ub4f1\ub85d\ubc88\ud638 [REDACTED] \ud655\uc778.",
    ),
    (
        "resident_registration_en",
        "resident registration number <RRN risk=\"P0\">{value}</RRN> verified.",
        "resident registration number [REDACTED] verified.",
    ),
    (
        "rrn_en",
        "RRN <RRN risk=\"P0\">{value}</RRN> was submitted.",
        "RRN [REDACTED] was submitted.",
    ),
    (
        "application_rrn",
        "\uc2e0\uccad\uc11c\uc758 \uc8fc\ubbfc\ub4f1\ub85d\ubc88\ud638 <RRN risk=\"P0\">{value}</RRN>\ub97c \ub9c8\uc2a4\ud06c\ud569\ub2c8\ub2e4.",
        "\uc2e0\uccad\uc11c\uc758 \uc8fc\ubbfc\ub4f1\ub85d\ubc88\ud638 [REDACTED]\ub97c \ub9c8\uc2a4\ud06c\ud569\ub2c8\ub2e4.",
    ),
    (
        "profile_rrn",
        "\ud504\ub85c\ud544\uc5d0 \uc8fc\ubbfc\ubc88\ud638 <RRN risk=\"P0\">{value}</RRN>\uac00 \uc788\uc2b5\ub2c8\ub2e4.",
        "\ud504\ub85c\ud544\uc5d0 \uc8fc\ubbfc\ubc88\ud638 [REDACTED]\uac00 \uc788\uc2b5\ub2c8\ub2e4.",
    ),
)


def build_cases() -> list[CaseSpec]:
    cases: list[CaseSpec] = []
    corporate_values = _corporate_values()
    rrn_values = _rrn_values()

    for value_index, value in enumerate(corporate_values, start=1):
        conflict = value_index <= len(CORPORATE_FIRST_12)
        notes = (
            "also passes RRN checksum; explicit corporate context must keep CORPORATE_REG_NO"
            if conflict
            else "corporate pattern value"
        )
        for template_index, (tag, template, expected) in enumerate(CORPORATE_CONTEXT_TEMPLATES, start=1):
            cases.append(
                CaseSpec(
                    id=f"stage4-corporate-pos-{value_index:02d}-{template_index:02d}",
                    marked_text=template.format(value=value),
                    expected_masked_text=expected,
                    tags=("stage4", "stage4_corporate_rrn", "corporate_context_positive", tag),
                    bucket="corporate_context_positive",
                    risk_focus="CORPORATE_REG_NO versus RRN type confusion",
                    notes=notes,
                )
            )

    for value_index, value in enumerate(rrn_values, start=1):
        conflict = value.startswith(("110111-", "110114-", "110115-", "110121-", "134511-"))
        notes = (
            "also matches corporate prefix; explicit RRN context must keep RRN"
            if conflict
            else "valid RRN checksum value"
        )
        for template_index, (tag, template, expected) in enumerate(RRN_CONTEXT_TEMPLATES, start=1):
            cases.append(
                CaseSpec(
                    id=f"stage4-rrn-pos-{value_index:02d}-{template_index:02d}",
                    marked_text=template.format(value=value),
                    expected_masked_text=expected,
                    tags=("stage4", "stage4_corporate_rrn", "rrn_context_positive", tag),
                    bucket="rrn_context_positive",
                    risk_focus="RRN recall under explicit RRN context",
                    notes=notes,
                )
            )

    return cases


def write_cases(cases: list[CaseSpec], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(case.to_json() for case in cases) + "\n",
        encoding="utf-8",
    )


def _corporate_values() -> tuple[str, ...]:
    conflict_values = tuple(_format_13_digits(first_12 + _rrn_check_digit(first_12)) for first_12 in CORPORATE_FIRST_12)
    return conflict_values + CORPORATE_PATTERN_VALUES


def _rrn_values() -> tuple[str, ...]:
    return tuple(_format_13_digits(first_12 + _rrn_check_digit(first_12)) for first_12 in RRN_FIRST_12)


def _format_13_digits(value: str) -> str:
    return f"{value[:6]}-{value[6:]}"


def _rrn_check_digit(first_12: str) -> str:
    if len(first_12) != 12 or not first_12.isdigit():
        raise ValueError("first_12 must contain exactly 12 digits")
    total = sum(int(digit) * weight for digit, weight in zip(first_12, WEIGHTS, strict=True))
    return str((11 - (total % 11)) % 10)


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate stage4 corporate/RRN marker fixtures.")
    parser.add_argument(
        "--output",
        default="data/eval/markers/stage4_corporate_rrn_expanded.jsonl",
        help="Output marker JSONL path.",
    )
    args = parser.parse_args()

    cases = build_cases()
    write_cases(cases, Path(args.output))
    counts: dict[str, int] = {}
    for case in cases:
        counts[case.bucket] = counts.get(case.bucket, 0) + 1
    print(
        "generated_cases="
        + str(len(cases))
        + " "
        + " ".join(f"{bucket}={counts[bucket]}" for bucket in sorted(counts))
    )


if __name__ == "__main__":
    main()
