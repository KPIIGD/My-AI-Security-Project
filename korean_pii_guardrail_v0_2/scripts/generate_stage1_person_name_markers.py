#!/usr/bin/env python3
"""Generate deterministic stage-1 PERSON_NAME marker fixtures.

The generated set is intentionally paired:

- hard_negative_name: the token looks name-like but is not a person.
- person_context_positive: the same token appears in a strong name context.

This lets later detector/context changes improve precision without silently
damaging recall.
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = PROJECT_ROOT / "data" / "eval" / "markers" / "stage1_person_name_expanded.jsonl"


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


NAME_LIKE_TOKENS = (
    "하늘",
    "사랑",
    "민수",
    "서연",
    "지훈",
    "유진",
    "도윤",
    "수빈",
    "길동",
    "보라",
    "아람",
    "나래",
    "초롱",
    "다온",
    "가온",
    "해솔",
    "윤서",
    "지민",
    "현우",
    "민재",
    "서준",
    "지우",
    "예린",
    "주원",
    "은서",
)

NEGATIVE_TEMPLATES = (
    ("weather", "오늘 {token}이 맑게 보입니다.", "{token}은 날씨나 하늘 상태를 설명하는 일반 표현"),
    ("abstract_noun", "{token}은 중요한 가치라는 문장 예시입니다.", "{token}은 추상 명사 또는 가치 표현"),
    ("project_name", "{token} 프로젝트는 내부 코드명입니다.", "{token}은 프로젝트 코드명"),
    ("model_name", "{token} 모델은 테스트용 분류기 이름입니다.", "{token}은 모델 이름"),
    ("store_name", "{token} 카페는 예시 상호입니다.", "{token}은 상호의 일부"),
    ("column_name", "{token} 점수는 샘플 데이터의 컬럼명입니다.", "{token}은 샘플 컬럼명"),
    ("document_example", "{token} 케이스는 문서 예제로만 사용합니다.", "{token}은 문서 예제명"),
    ("color_word", "{token}색 버튼을 누르면 다음 화면으로 이동합니다.", "{token}은 색상 표현의 일부"),
    ("compound_word", "{token}기 설정값은 기본값으로 둡니다.", "{token}은 기술 용어 일부"),
    ("dataset_name", "{token} 데이터셋은 synthetic fixture입니다.", "{token}은 데이터셋 이름"),
    ("file_name", "{token}.json 파일은 평가용 샘플입니다.", "{token}은 파일 이름"),
    ("class_name", "{token} 클래스는 테스트 코드에서만 사용합니다.", "{token}은 코드 클래스 이름"),
    ("branch_name", "{token} 브랜치는 실험용입니다.", "{token}은 브랜치 이름"),
    ("label_name", "{token} 라벨은 화면 표시용입니다.", "{token}은 UI 라벨"),
    ("metric_name", "{token} 지표는 대시보드 예시입니다.", "{token}은 지표명"),
    ("product_name", "{token} 패키지는 가상의 상품명입니다.", "{token}은 상품명"),
    ("team_name", "{token} 팀은 예시 조직명입니다.", "{token}은 팀 이름"),
    ("scenario_name", "{token} 시나리오는 부하 테스트용입니다.", "{token}은 시나리오 이름"),
    ("variable_name", "{token} 변수는 통계 예제에서만 등장합니다.", "{token}은 변수명"),
    ("screen_name", "{token} 화면은 디자인 시안 이름입니다.", "{token}은 화면 이름"),
)

POSITIVE_TEMPLATES = (
    ("customer_name", "고객명 {marker}, 연락처는 별도 확인 예정입니다.", "고객명 [PERSON_1], 연락처는 별도 확인 예정입니다."),
    ("owner_name", "담당자 {marker}에게 전달했습니다.", "담당자 [PERSON_1]에게 전달했습니다."),
    ("applicant_name", "신청자 이름은 {marker}입니다.", "신청자 이름은 [PERSON_1]입니다."),
    ("patient_name", "환자명 {marker}, 진료과는 내과입니다.", "환자명 [PERSON_1], 진료과는 내과입니다."),
    ("recipient_name", "수령인 {marker}은 오후에 방문합니다.", "수령인 [PERSON_1]은 오후에 방문합니다."),
    ("reservation_name", "예약자 {marker}님 확인 부탁드립니다.", "예약자 [PERSON_1]님 확인 부탁드립니다."),
    ("employee_name", "직원명 {marker}으로 등록되어 있습니다.", "직원명 [PERSON_1]으로 등록되어 있습니다."),
    ("guardian_name", "보호자 이름 {marker}을 확인했습니다.", "보호자 이름 [PERSON_1]을 확인했습니다."),
    ("inquirer_name", "문의자 {marker}이 다시 연락했습니다.", "문의자 [PERSON_1]이 다시 연락했습니다."),
    ("contract_owner", "계약 담당자는 {marker}입니다.", "계약 담당자는 [PERSON_1]입니다."),
    ("consultation_name", "상담 기록에는 {marker}님 요청으로 남겼습니다.", "상담 기록에는 [PERSON_1]님 요청으로 남겼습니다."),
    ("requester_name", "요청자 성명 {marker}으로 접수되었습니다.", "요청자 성명 [PERSON_1]으로 접수되었습니다."),
)


def build_cases() -> list[CaseSpec]:
    cases: list[CaseSpec] = []
    for token_index, token in enumerate(NAME_LIKE_TOKENS, start=1):
        for template_index, (tag, template, reason) in enumerate(NEGATIVE_TEMPLATES, start=1):
            text = template.format(token=token)
            cases.append(
                CaseSpec(
                    id=f"stage1-name-neg-{token_index:02d}-{template_index:02d}",
                    marked_text=text,
                    expected_masked_text=text,
                    tags=("stage1", "stage1_expanded", "hard_negative_name", tag),
                    bucket="hard_negative_name",
                    negative_reason=reason.format(token=token),
                    risk_focus="PERSON_NAME false positive",
                )
            )

    for token_index, token in enumerate(NAME_LIKE_TOKENS, start=1):
        marker = f'<PERSON_NAME risk="P1">{token}</PERSON_NAME>'
        for template_index, (tag, template, expected_template) in enumerate(POSITIVE_TEMPLATES, start=1):
            cases.append(
                CaseSpec(
                    id=f"stage1-name-pos-{token_index:02d}-{template_index:02d}",
                    marked_text=template.format(marker=marker),
                    expected_masked_text=expected_template,
                    tags=("stage1", "stage1_expanded", "person_context_positive", tag),
                    bucket="person_context_positive",
                    risk_focus="PERSON_NAME recall with strong context",
                )
            )
    return cases


def write_cases(cases: list[CaseSpec], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        "\n".join(case.to_json() for case in cases) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the stage-1 expanded PERSON_NAME marker JSONL."
    )
    parser.add_argument(
        "--output",
        default=str(DEFAULT_OUTPUT),
        help="Output marker JSONL path.",
    )
    args = parser.parse_args()

    cases = build_cases()
    write_cases(cases, Path(args.output))
    negative_count = sum(1 for case in cases if case.bucket == "hard_negative_name")
    positive_count = sum(1 for case in cases if case.bucket == "person_context_positive")
    print(
        "generated_cases="
        f"{len(cases)} negative={negative_count} positive={positive_count} output={args.output}"
    )


if __name__ == "__main__":
    main()
