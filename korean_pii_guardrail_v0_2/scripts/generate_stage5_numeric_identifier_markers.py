#!/usr/bin/env python3
"""Generate stage5 numeric identifier marker fixtures."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


BUSINESS_REG_WEIGHTS = (1, 3, 7, 1, 3, 7, 1, 3, 5)


@dataclass(frozen=True)
class CaseSpec:
    id: str
    marked_text: str
    expected_masked_text: str
    tags: tuple[str, ...]
    bucket: str
    risk_focus: str
    negative_reason: str | None = None
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
        if self.negative_reason is not None:
            payload["negative_reason"] = self.negative_reason
        if self.notes is not None:
            payload["notes"] = self.notes
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


BUSINESS_FIRST_9 = (
    "123456789",
    "220816251",
    "101864751",
    "214880023",
    "312850174",
    "503810842",
    "607820735",
    "120817263",
    "117811234",
    "409860271",
)

BUSINESS_CONTEXT_TEMPLATES = (
    (
        "business_label",
        "사업자등록번호 <BUSINESS_REG_NO risk=\"P1\">{value}</BUSINESS_REG_NO> 확인 완료.",
        "사업자등록번호 [BUSINESS_REG_NO_1] 확인 완료.",
    ),
    (
        "business_no_short",
        "사업자번호는 <BUSINESS_REG_NO risk=\"P1\">{value}</BUSINESS_REG_NO>입니다.",
        "사업자번호는 [BUSINESS_REG_NO_1]입니다.",
    ),
    (
        "tax_invoice",
        "세금계산서 사업자등록번호: <BUSINESS_REG_NO risk=\"P1\">{value}</BUSINESS_REG_NO>",
        "세금계산서 사업자등록번호: [BUSINESS_REG_NO_1]",
    ),
    (
        "vendor_onboarding",
        "거래처 사업자번호 <BUSINESS_REG_NO risk=\"P1\">{value}</BUSINESS_REG_NO>를 등록했습니다.",
        "거래처 사업자번호 [BUSINESS_REG_NO_1]를 등록했습니다.",
    ),
    (
        "settlement_team",
        "정산팀이 공급자 사업자등록번호 <BUSINESS_REG_NO risk=\"P1\">{value}</BUSINESS_REG_NO>를 검토했습니다.",
        "정산팀이 공급자 사업자등록번호 [BUSINESS_REG_NO_1]를 검토했습니다.",
    ),
    (
        "merchant_profile",
        "가맹점 사업자번호 <BUSINESS_REG_NO risk=\"P1\">{value}</BUSINESS_REG_NO> 저장.",
        "가맹점 사업자번호 [BUSINESS_REG_NO_1] 저장.",
    ),
    (
        "biz_reg_en",
        "business registration number <BUSINESS_REG_NO risk=\"P1\">{value}</BUSINESS_REG_NO> verified.",
        "business registration number [BUSINESS_REG_NO_1] verified.",
    ),
    (
        "brn_en",
        "BRN <BUSINESS_REG_NO risk=\"P1\">{value}</BUSINESS_REG_NO> was submitted.",
        "BRN [BUSINESS_REG_NO_1] was submitted.",
    ),
    (
        "supplier_record",
        "공급사 등록번호 <BUSINESS_REG_NO risk=\"P1\">{value}</BUSINESS_REG_NO> 입력 완료.",
        "공급사 등록번호 [BUSINESS_REG_NO_1] 입력 완료.",
    ),
    (
        "merchant_tax_id",
        "merchant tax id <BUSINESS_REG_NO risk=\"P1\">{value}</BUSINESS_REG_NO> checked.",
        "merchant tax id [BUSINESS_REG_NO_1] checked.",
    ),
)

BANK_ACCOUNT_VALUES = (
    ("국민은행", "123456-12-123456"),
    ("국민은행", "123-12-1234-123"),
    ("신한은행", "110-123-456789"),
    ("신한은행", "220-456-789012"),
    ("우리은행", "100-123456-12-345"),
    ("우리은행", "1000-123-456789"),
    ("하나은행", "123-123456-12345"),
    ("하나은행", "123-12-12345-1"),
    ("농협은행", "123-12-123456"),
    ("농협은행", "123-1234-1234-12"),
    ("기업은행", "003-123456-12-345"),
    ("기업은행", "220-654321-98-765"),
    ("카카오뱅크", "3333-12-1234567"),
    ("카카오뱅크", "7979-34-7654321"),
    ("토스뱅크", "1000-1234-5678"),
    ("토스뱅크", "1001-8765-4321"),
    ("케이뱅크", "123-123-123456"),
    ("케이뱅크", "1001-1234-5678"),
    ("KB", "987654-32-987654"),
    ("NH", "321-4321-8765-43"),
)

BANK_CONTEXT_TEMPLATES = (
    (
        "account_label",
        "{bank} 계좌 <BANK_ACCOUNT risk=\"P1\">{value}</BANK_ACCOUNT>로 입금해 주세요.",
        "{bank} 계좌 [BANK_ACCOUNT_1]로 입금해 주세요.",
    ),
    (
        "refund_account",
        "환불계좌는 {bank} <BANK_ACCOUNT risk=\"P1\">{value}</BANK_ACCOUNT>입니다.",
        "환불계좌는 {bank} [BANK_ACCOUNT_1]입니다.",
    ),
    (
        "transfer_account",
        "이체 대상 계좌번호: {bank} <BANK_ACCOUNT risk=\"P1\">{value}</BANK_ACCOUNT>",
        "이체 대상 계좌번호: {bank} [BANK_ACCOUNT_1]",
    ),
    (
        "settlement_account",
        "정산 계좌 {bank} <BANK_ACCOUNT risk=\"P1\">{value}</BANK_ACCOUNT> 확인.",
        "정산 계좌 {bank} [BANK_ACCOUNT_1] 확인.",
    ),
    (
        "deposit_request",
        "입금 계좌는 {bank} <BANK_ACCOUNT risk=\"P1\">{value}</BANK_ACCOUNT>로 안내했습니다.",
        "입금 계좌는 {bank} [BANK_ACCOUNT_1]로 안내했습니다.",
    ),
    (
        "bank_account_en",
        "{bank} bank account <BANK_ACCOUNT risk=\"P1\">{value}</BANK_ACCOUNT> verified.",
        "{bank} bank account [BANK_ACCOUNT_1] verified.",
    ),
    (
        "account_no_en",
        "account no {bank} <BANK_ACCOUNT risk=\"P1\">{value}</BANK_ACCOUNT> was saved.",
        "account no {bank} [BANK_ACCOUNT_1] was saved.",
    ),
    (
        "vendor_account",
        "거래처 지급 계좌 {bank} <BANK_ACCOUNT risk=\"P1\">{value}</BANK_ACCOUNT> 등록.",
        "거래처 지급 계좌 {bank} [BANK_ACCOUNT_1] 등록.",
    ),
    (
        "payroll_account",
        "급여 이체 계좌 {bank} <BANK_ACCOUNT risk=\"P1\">{value}</BANK_ACCOUNT> 확인.",
        "급여 이체 계좌 {bank} [BANK_ACCOUNT_1] 확인.",
    ),
    (
        "billing_account",
        "청구서 입금계좌 {bank} <BANK_ACCOUNT risk=\"P1\">{value}</BANK_ACCOUNT> 표기.",
        "청구서 입금계좌 {bank} [BANK_ACCOUNT_1] 표기.",
    ),
)

PHONE_VALUES = (
    ("PHONE_MOBILE", "010-1234-5678"),
    ("PHONE_MOBILE", "010-2345-6789"),
    ("PHONE_MOBILE", "010 3456 7890"),
    ("PHONE_MOBILE", "010-4567-8901"),
    ("PHONE_MOBILE", "011-123-4567"),
    ("PHONE_MOBILE", "016-234-5678"),
    ("PHONE_MOBILE", "017-345-6789"),
    ("PHONE_MOBILE", "018-456-7890"),
    ("PHONE_MOBILE", "019-567-8901"),
    ("PHONE_MOBILE", "010-6789-0123"),
    ("PHONE_LANDLINE", "02-123-4567"),
    ("PHONE_LANDLINE", "02-2345-6789"),
    ("PHONE_LANDLINE", "031-123-4567"),
    ("PHONE_LANDLINE", "032-234-5678"),
    ("PHONE_LANDLINE", "042-345-6789"),
    ("PHONE_LANDLINE", "051-456-7890"),
    ("PHONE_LANDLINE", "053-567-8901"),
    ("PHONE_LANDLINE", "061-678-9012"),
    ("PHONE_LANDLINE", "064-789-0123"),
    ("PHONE_LANDLINE", "044-123-4567"),
)

PHONE_CONTEXT_TEMPLATES = (
    (
        "contact_label",
        "연락처 <{entity} risk=\"P1\">{value}</{entity}> 확인 부탁드립니다.",
        "연락처 [PHONE_1] 확인 부탁드립니다.",
    ),
    (
        "phone_label",
        "전화번호는 <{entity} risk=\"P1\">{value}</{entity}>입니다.",
        "전화번호는 [PHONE_1]입니다.",
    ),
    (
        "mobile_label",
        "휴대폰 <{entity} risk=\"P1\">{value}</{entity}>로 안내했습니다.",
        "휴대폰 [PHONE_1]로 안내했습니다.",
    ),
    (
        "callback",
        "콜백 번호 <{entity} risk=\"P1\">{value}</{entity}> 저장.",
        "콜백 번호 [PHONE_1] 저장.",
    ),
    (
        "customer_contact",
        "고객 연락처: <{entity} risk=\"P1\">{value}</{entity}>",
        "고객 연락처: [PHONE_1]",
    ),
    (
        "sms_number",
        "문자 발송 번호 <{entity} risk=\"P1\">{value}</{entity}> 확인.",
        "문자 발송 번호 [PHONE_1] 확인.",
    ),
    (
        "contact_en",
        "contact phone <{entity} risk=\"P1\">{value}</{entity}> verified.",
        "contact phone [PHONE_1] verified.",
    ),
    (
        "phone_no_en",
        "phone no <{entity} risk=\"P1\">{value}</{entity}> was submitted.",
        "phone no [PHONE_1] was submitted.",
    ),
    (
        "receiver_phone",
        "수령인 전화번호 <{entity} risk=\"P1\">{value}</{entity}> 입력.",
        "수령인 전화번호 [PHONE_1] 입력.",
    ),
    (
        "protected_contact",
        "보호 대상 연락처 <{entity} risk=\"P1\">{value}</{entity}> 마스킹 필요.",
        "보호 대상 연락처 [PHONE_1] 마스킹 필요.",
    ),
)

NEGATIVE_IDENTIFIER_CONTEXT_TEMPLATES = (
    "주문번호 {value} 처리 완료.",
    "주문ID {value} 상태를 조회했습니다.",
    "예약번호 {value}로 체크인합니다.",
    "접수번호 {value}는 상담 큐 번호입니다.",
    "송장번호 {value} 배송 추적.",
    "운송장번호 {value}를 입력하세요.",
    "결제번호 {value} 승인 완료.",
    "거래번호 {value}는 내부 정산 키입니다.",
    "order id {value} is ready.",
    "tracking no {value} was generated.",
)

NEGATIVE_VALUES = (
    "123-45-67891",
    "220-81-62517",
    "101-86-47510",
    "214-88-00235",
    "312-85-01741",
    "503-81-08424",
    "607-82-07351",
    "120-81-72630",
    "117-81-12343",
    "409-86-02714",
    "010-1234-5678",
    "010-2345-6789",
    "010 3456 7890",
    "011-123-4567",
    "016-234-5678",
    "02-123-4567",
    "031-123-4567",
    "032-234-5678",
    "042-345-6789",
    "051-456-7890",
    "110-123-456789",
    "123456-12-123456",
    "123-12-1234-123",
    "100-123456-12-3",
    "1000-123-456789",
    "123-123456-12345",
    "123-12-12345-1",
    "3333-12-1234567",
    "1000-1234-5678",
    "1001-1234-5678",
)


def build_cases() -> list[CaseSpec]:
    cases: list[CaseSpec] = []

    business_values = _business_values()
    for value_index, value in enumerate(business_values, start=1):
        valid = _business_reg_no_checksum_valid(_digits_only(value))
        notes = "checksum valid" if valid else "pattern-only business number"
        for template_index, (tag, template, expected) in enumerate(BUSINESS_CONTEXT_TEMPLATES, start=1):
            cases.append(
                CaseSpec(
                    id=f"stage5-business-pos-{value_index:02d}-{template_index:02d}",
                    marked_text=template.format(value=value),
                    expected_masked_text=expected,
                    tags=("stage5", "stage5_numeric_identifier", "business_context_positive", tag),
                    bucket="business_context_positive",
                    risk_focus="BUSINESS_REG_NO recall under explicit business context",
                    notes=notes,
                )
            )

    for value_index, (bank, value) in enumerate(BANK_ACCOUNT_VALUES, start=1):
        for template_index, (tag, template, expected) in enumerate(BANK_CONTEXT_TEMPLATES, start=1):
            cases.append(
                CaseSpec(
                    id=f"stage5-bank-pos-{value_index:02d}-{template_index:02d}",
                    marked_text=template.format(bank=bank, value=value),
                    expected_masked_text=expected.format(bank=bank),
                    tags=("stage5", "stage5_numeric_identifier", "bank_account_positive", tag),
                    bucket="bank_account_positive",
                    risk_focus="BANK_ACCOUNT recall under explicit account context",
                )
            )

    for value_index, (entity, value) in enumerate(PHONE_VALUES, start=1):
        for template_index, (tag, template, expected) in enumerate(PHONE_CONTEXT_TEMPLATES, start=1):
            cases.append(
                CaseSpec(
                    id=f"stage5-phone-pos-{value_index:02d}-{template_index:02d}",
                    marked_text=template.format(entity=entity, value=value),
                    expected_masked_text=expected,
                    tags=("stage5", "stage5_numeric_identifier", "phone_positive", tag),
                    bucket="phone_positive",
                    risk_focus="PHONE recall under explicit contact context",
                )
            )

    for value_index, value in enumerate(NEGATIVE_VALUES, start=1):
        for template_index, template in enumerate(NEGATIVE_IDENTIFIER_CONTEXT_TEMPLATES, start=1):
            text = template.format(value=value)
            cases.append(
                CaseSpec(
                    id=f"stage5-order-neg-{value_index:02d}-{template_index:02d}",
                    marked_text=text,
                    expected_masked_text=text,
                    tags=("stage5", "stage5_numeric_identifier", "hard_negative_numeric_identifier"),
                    bucket="hard_negative_numeric_identifier",
                    risk_focus="ORDER_ID-like numeric identifiers must not become PII",
                    negative_reason="order, receipt, invoice, tracking, or payment identifier",
                )
            )

    return cases


def write_cases(cases: list[CaseSpec], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(case.to_json() for case in cases) + "\n",
        encoding="utf-8",
    )


def _business_values() -> tuple[str, ...]:
    valid_values = tuple(_format_business_reg_no(first_9 + _business_check_digit(first_9)) for first_9 in BUSINESS_FIRST_9)
    pattern_only_values = tuple(_with_invalid_business_check_digit(value) for value in valid_values)
    return valid_values + pattern_only_values


def _format_business_reg_no(value: str) -> str:
    return f"{value[:3]}-{value[3:5]}-{value[5:]}"


def _with_invalid_business_check_digit(value: str) -> str:
    digits = _digits_only(value)
    invalid_check = (int(digits[-1]) + 1) % 10
    return _format_business_reg_no(digits[:-1] + str(invalid_check))


def _business_check_digit(first_9: str) -> str:
    if len(first_9) != 9 or not first_9.isdigit():
        raise ValueError("first_9 must contain exactly 9 digits")
    weighted_sum = sum(int(digit) * weight for digit, weight in zip(first_9[:8], BUSINESS_REG_WEIGHTS[:8], strict=True))
    ninth_product = int(first_9[8]) * BUSINESS_REG_WEIGHTS[8]
    weighted_sum += ninth_product // 10 + ninth_product % 10
    return str((10 - (weighted_sum % 10)) % 10)


def _business_reg_no_checksum_valid(digits: str) -> bool:
    return len(digits) == 10 and digits.isdigit() and _business_check_digit(digits[:9]) == digits[9]


def _digits_only(value: str) -> str:
    return "".join(char for char in value if char.isdigit())


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate stage5 numeric identifier marker fixtures.")
    parser.add_argument(
        "--output",
        default="data/eval/markers/stage5_numeric_identifier_expanded.jsonl",
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
