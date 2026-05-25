#!/usr/bin/env python3
"""Generate deterministic stage-2 PHONE/EMAIL marker fixtures."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "eval" / "markers" / "stage2_contact_expanded.jsonl"


@dataclass(frozen=True)
class CaseSpec:
    id: str
    marked_text: str
    expected_masked_text: str
    tags: tuple[str, ...]
    bucket: str
    risk_focus: str
    negative_reason: str | None = None

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
        return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))


PHONE_VALUES = (
    "010-1111-2222",
    "010-2222-3333",
    "010-3333-4444",
    "010-4444-5555",
    "010-5555-6666",
    "010-6666-7777",
    "010-7777-8888",
    "010-8888-9999",
    "010-1234-5678",
    "010-2345-6789",
    "010 3456 7890",
    "01045678901",
    "011-123-4567",
    "016-234-5678",
    "02-123-4567",
    "031-234-5678",
    "051-345-6789",
    "032-456-7890",
    "042-555-6666",
    "064-123-4567",
)

EMAIL_VALUES = (
    "test@example.com",
    "sample@example.org",
    "dummy@example.net",
    "user@example.co.kr",
    "privacy@example.com",
    "hello@example.org",
    "dev@example.net",
    "qa@example.co.kr",
    "noreply@example.com",
    "format@example.org",
    "minsu.kim@synthetic.test",
    "seoyeon.lee@synthetic.test",
    "support@synthetic.test",
    "contact@synthetic.test",
    "case.user+1@synthetic.test",
    "owner.team@synthetic.test",
    "patient.demo@synthetic.test",
    "customer.demo@synthetic.test",
    "reply.demo@synthetic.test",
    "mail.demo@synthetic.test",
)

PHONE_NEGATIVE_TEMPLATES = (
    ("example_phone", "예시 전화번호는 {value}입니다.", "문서 예시 전화번호"),
    ("sample_phone", "샘플 연락처 {value}는 테스트 데이터입니다.", "샘플 전화번호"),
    ("dummy_phone", "더미 번호 {value}를 화면 예시에 표시합니다.", "더미 전화번호"),
    ("test_phone", "테스트 전화번호 {value}는 실제 사용자가 아닙니다.", "테스트 전화번호"),
    ("format_phone", "형식 설명: 휴대폰은 {value}처럼 입력합니다.", "형식 설명용 전화번호"),
    ("manual_phone", "매뉴얼 예제에는 {value}를 사용합니다.", "매뉴얼 예제 전화번호"),
    ("placeholder_phone", "placeholder 값은 {value}로 둡니다.", "placeholder 전화번호"),
    ("fixture_phone", "fixture payload의 phone 필드는 {value}입니다.", "fixture 전화번호"),
    ("doc_phone", "문서의 연락처 예시는 {value}입니다.", "문서 예시 전화번호"),
    ("ui_phone", "UI 목업에는 {value}를 회색 텍스트로 표시합니다.", "UI 목업 전화번호"),
    ("training_phone", "교육 자료 샘플 번호는 {value}입니다.", "교육 자료 전화번호"),
    ("validation_phone", "검증용 입력값 {value}를 사용합니다.", "검증용 전화번호"),
    ("storybook_phone", "스토리북 예제 번호는 {value}입니다.", "스토리북 전화번호"),
    ("seed_phone", "seed 데이터에는 {value}가 포함됩니다.", "seed 전화번호"),
    ("synthetic_phone", "synthetic 전화번호 {value}는 평가용입니다.", "synthetic 전화번호"),
    ("demo_phone", "데모 예시 화면의 번호는 {value}입니다.", "데모 예시 전화번호"),
    ("redaction_phone", "마스킹 테스트 번호 {value}를 입력했습니다.", "마스킹 테스트 전화번호"),
    ("template_phone", "템플릿 예시의 연락처 자리에는 {value}를 넣습니다.", "템플릿 예시 전화번호"),
    ("guide_phone", "가이드 문서 예시는 {value}입니다.", "가이드 예시 전화번호"),
    ("sandbox_phone", "샌드박스 예시 번호 {value}는 외부 발송 금지입니다.", "샌드박스 예시 전화번호"),
)

PHONE_POSITIVE_TEMPLATES = (
    ("contact", "연락처 <{entity} risk=\"P1\">{value}</{entity}>로 연락 주세요.", "연락처 [PHONE_1]로 연락 주세요."),
    ("phone_number", "전화번호는 <{entity} risk=\"P1\">{value}</{entity}>입니다.", "전화번호는 [PHONE_1]입니다."),
    ("callback", "회신 번호 <{entity} risk=\"P1\">{value}</{entity}>를 남겼습니다.", "회신 번호 [PHONE_1]를 남겼습니다."),
    ("customer_phone", "고객 연락처 <{entity} risk=\"P1\">{value}</{entity}> 확인 완료.", "고객 연락처 [PHONE_1] 확인 완료."),
    ("reservation_phone", "예약자 전화번호 <{entity} risk=\"P1\">{value}</{entity}>입니다.", "예약자 전화번호 [PHONE_1]입니다."),
    ("delivery_phone", "배송 연락처는 <{entity} risk=\"P1\">{value}</{entity}>입니다.", "배송 연락처는 [PHONE_1]입니다."),
    ("emergency_phone", "비상 연락망 <{entity} risk=\"P1\">{value}</{entity}>로 등록했습니다.", "비상 연락망 [PHONE_1]로 등록했습니다."),
    ("guardian_phone", "보호자 연락처 <{entity} risk=\"P1\">{value}</{entity}>입니다.", "보호자 연락처 [PHONE_1]입니다."),
    ("consult_phone", "상담 회신은 <{entity} risk=\"P1\">{value}</{entity}>로 부탁드립니다.", "상담 회신은 [PHONE_1]로 부탁드립니다."),
    ("office_phone", "사무실 전화번호 <{entity} risk=\"P1\">{value}</{entity}>로 전화 주세요.", "사무실 전화번호 [PHONE_1]로 전화 주세요."),
    ("direct_phone", "담당자 직통번호는 <{entity} risk=\"P1\">{value}</{entity}>입니다.", "담당자 직통번호는 [PHONE_1]입니다."),
    ("home_phone", "자택 전화 <{entity} risk=\"P1\">{value}</{entity}>로 확인했습니다.", "자택 전화 [PHONE_1]로 확인했습니다."),
    ("external_phone", "외부 연락 전화 <{entity} risk=\"P1\">{value}</{entity}>입니다.", "외부 연락 전화 [PHONE_1]입니다."),
    ("patient_phone", "환자 연락처 <{entity} risk=\"P1\">{value}</{entity}>입니다.", "환자 연락처 [PHONE_1]입니다."),
    ("sms_phone", "문자 수신 번호는 <{entity} risk=\"P1\">{value}</{entity}>입니다.", "문자 수신 번호는 [PHONE_1]입니다."),
)

EMAIL_NEGATIVE_TEMPLATES = (
    ("example_email", "예시 이메일은 {value}입니다.", "문서 예시 이메일"),
    ("sample_email", "샘플 메일 주소 {value}를 사용합니다.", "샘플 이메일"),
    ("dummy_email", "더미 이메일 {value}는 실제 계정이 아닙니다.", "더미 이메일"),
    ("test_email", "테스트 메일 {value}는 발송하지 않습니다.", "테스트 이메일"),
    ("format_email", "형식 설명: 이메일은 {value}처럼 입력합니다.", "형식 설명용 이메일"),
    ("manual_email", "매뉴얼 예제에는 {value}를 사용합니다.", "매뉴얼 예제 이메일"),
    ("placeholder_email", "placeholder 값은 {value}로 둡니다.", "placeholder 이메일"),
    ("fixture_email", "fixture payload의 email 필드는 {value}입니다.", "fixture 이메일"),
    ("doc_email", "문서의 전자우편 예시는 {value}입니다.", "문서 예시 이메일"),
    ("ui_email", "UI 목업에는 {value}를 회색 텍스트로 표시합니다.", "UI 목업 이메일"),
    ("training_email", "교육 자료 샘플 메일은 {value}입니다.", "교육 자료 이메일"),
    ("validation_email", "검증용 입력값 {value}를 사용합니다.", "검증용 이메일"),
    ("storybook_email", "스토리북 예제 메일은 {value}입니다.", "스토리북 이메일"),
    ("seed_email", "seed 데이터에는 {value}가 포함됩니다.", "seed 이메일"),
    ("synthetic_email", "synthetic 이메일 {value}는 평가용입니다.", "synthetic 이메일"),
)

EMAIL_POSITIVE_TEMPLATES = (
    ("email_label", "이메일 <EMAIL risk=\"P1\">{value}</EMAIL>로 회신 주세요.", "이메일 [EMAIL_1]로 회신 주세요."),
    ("mail_label", "메일 주소는 <EMAIL risk=\"P1\">{value}</EMAIL>입니다.", "메일 주소는 [EMAIL_1]입니다."),
    ("reply_email", "회신 주소 <EMAIL risk=\"P1\">{value}</EMAIL>를 남겼습니다.", "회신 주소 [EMAIL_1]를 남겼습니다."),
    ("account_email", "계정 이메일 <EMAIL risk=\"P1\">{value}</EMAIL> 확인 완료.", "계정 이메일 [EMAIL_1] 확인 완료."),
    ("customer_email", "고객 전자우편 <EMAIL risk=\"P1\">{value}</EMAIL>입니다.", "고객 전자우편 [EMAIL_1]입니다."),
    ("reservation_email", "예약 확인 메일은 <EMAIL risk=\"P1\">{value}</EMAIL>로 발송합니다.", "예약 확인 메일은 [EMAIL_1]로 발송합니다."),
    ("patient_email", "환자 보호자 이메일 <EMAIL risk=\"P1\">{value}</EMAIL>입니다.", "환자 보호자 이메일 [EMAIL_1]입니다."),
    ("consult_email", "상담 결과는 <EMAIL risk=\"P1\">{value}</EMAIL>로 보내 주세요.", "상담 결과는 [EMAIL_1]로 보내 주세요."),
    ("invoice_email", "청구서 수신 이메일 <EMAIL risk=\"P1\">{value}</EMAIL>입니다.", "청구서 수신 이메일 [EMAIL_1]입니다."),
    ("login_email", "로그인 ID 이메일은 <EMAIL risk=\"P1\">{value}</EMAIL>입니다.", "로그인 ID 이메일은 [EMAIL_1]입니다."),
)


def build_cases() -> list[CaseSpec]:
    cases: list[CaseSpec] = []
    for value_index, value in enumerate(PHONE_VALUES, start=1):
        for template_index, (tag, template, reason) in enumerate(PHONE_NEGATIVE_TEMPLATES, start=1):
            text = template.format(value=value)
            cases.append(
                CaseSpec(
                    id=f"stage2-phone-neg-{value_index:02d}-{template_index:02d}",
                    marked_text=text,
                    expected_masked_text=text,
                    tags=("stage2", "stage2_contact", "hard_negative_phone", tag),
                    bucket="hard_negative_phone",
                    risk_focus="PHONE false positive",
                    negative_reason=reason,
                )
            )

        for template_index, (tag, template, expected_template) in enumerate(PHONE_POSITIVE_TEMPLATES, start=1):
            marked_text = template.format(value=value, entity=_phone_entity(value))
            expected = expected_template
            cases.append(
                CaseSpec(
                    id=f"stage2-phone-pos-{value_index:02d}-{template_index:02d}",
                    marked_text=marked_text,
                    expected_masked_text=expected,
                    tags=("stage2", "stage2_contact", "phone_positive", tag),
                    bucket="phone_positive",
                    risk_focus="PHONE recall with contact context",
                )
            )

    for value_index, value in enumerate(EMAIL_VALUES, start=1):
        for template_index, (tag, template, reason) in enumerate(EMAIL_NEGATIVE_TEMPLATES, start=1):
            text = template.format(value=value)
            cases.append(
                CaseSpec(
                    id=f"stage2-email-neg-{value_index:02d}-{template_index:02d}",
                    marked_text=text,
                    expected_masked_text=text,
                    tags=("stage2", "stage2_contact", "hard_negative_email", tag),
                    bucket="hard_negative_email",
                    risk_focus="EMAIL false positive",
                    negative_reason=reason,
                )
            )

        for template_index, (tag, template, expected_template) in enumerate(EMAIL_POSITIVE_TEMPLATES, start=1):
            cases.append(
                CaseSpec(
                    id=f"stage2-email-pos-{value_index:02d}-{template_index:02d}",
                    marked_text=template.format(value=value),
                    expected_masked_text=expected_template,
                    tags=("stage2", "stage2_contact", "email_positive", tag),
                    bucket="email_positive",
                    risk_focus="EMAIL recall with contact context",
                )
            )
    return cases


def _phone_entity(value: str) -> str:
    digits = "".join(ch for ch in value if ch.isdigit())
    if digits.startswith(("010", "011", "016", "017", "018", "019")):
        return "PHONE_MOBILE"
    return "PHONE_LANDLINE"


def write_cases(cases: list[CaseSpec], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(case.to_json() for case in cases) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the stage-2 PHONE/EMAIL marker JSONL."
    )
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output marker JSONL path.")
    args = parser.parse_args()

    cases = build_cases()
    write_cases(cases, Path(args.output))
    counts: dict[str, int] = {}
    for case in cases:
        counts[case.bucket] = counts.get(case.bucket, 0) + 1
    print(
        "generated_cases="
        f"{len(cases)} "
        + " ".join(f"{key}={value}" for key, value in sorted(counts.items()))
        + f" output={args.output}"
    )


if __name__ == "__main__":
    main()
