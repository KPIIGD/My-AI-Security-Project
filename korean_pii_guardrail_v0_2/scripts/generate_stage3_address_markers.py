#!/usr/bin/env python3
"""Generate stage3 ADDRESS_UNIT/ADDRESS_FULL marker fixtures."""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass
from pathlib import Path


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


ADDRESS_UNIT_VALUES = (
    "서울시 강남구",
    "서울시 강남구 역삼동",
    "서울특별시 강남구 역삼동",
    "서울 강남구 삼성동",
    "서울 송파구 잠실동",
    "서울 마포구",
    "서울 종로구",
    "서울 중구 명동",
    "부산 해운대구",
    "부산광역시 수영구",
    "대구 중구",
    "경기도 분당구",
    "서울시 강남구 테헤란로",
    "서울 강남구 강남대로",
    "서울 송파구 올림픽로",
    "서울 마포구 마포대로",
    "서울 용산구 한강대로",
    "서울 종로구 세종대로",
    "서울 중구 을지로",
    "서울 강남구 봉은사로",
)

ADDRESS_FULL_VALUES = (
    "서울시 강남구 테헤란로 123",
    "서울시 강남구 테헤란로 123 5층",
    "서울 강남구 강남대로 152",
    "서울시 서초구 강남대로 77",
    "서울 송파구 올림픽로 300",
    "서울 마포구 마포대로 45",
    "서울 용산구 한강대로 100",
    "서울 종로구 세종대로 10",
    "서울 중구 을지로 50",
    "서울 강남구 봉은사로 21",
    "서울 강남구 역삼동 101동 1203호",
    "서울 송파구 잠실동 102동 903호",
    "테헤란로 123",
    "강남대로 152",
    "올림픽로 300",
    "마포대로 45 3층",
    "한강대로 100 12층",
    "압구정로 12",
    "도산대로 77",
    "선릉로 20 101동 303호",
)

HARD_NEGATIVE_ADDRESS_VALUES = (
    "서울",
    "서울시",
    "강남구",
    "서초구",
    "송파구",
    "마포구",
    "종로구",
    "중구",
    "부산",
    "해운대구",
    "테헤란로",
    "강남대로",
    "올림픽로",
    "마포대로",
    "한강대로",
    "세종대로",
    "을지로",
    "봉은사로",
    "명동",
    "역삼동",
)

ADDRESS_UNIT_TEMPLATES = (
    ("address_label", "주소는 <ADDRESS_UNIT risk=\"P2\">{value}</ADDRESS_UNIT>입니다."),
    ("residence_area", "거주지는 <ADDRESS_UNIT risk=\"P2\">{value}</ADDRESS_UNIT>로 등록되어 있습니다."),
    ("region_only", "지역 정보는 <ADDRESS_UNIT risk=\"P2\">{value}</ADDRESS_UNIT>까지 확인됩니다."),
    ("delivery_area", "배송 가능 지역은 <ADDRESS_UNIT risk=\"P2\">{value}</ADDRESS_UNIT>입니다."),
    ("consult_area", "상담 대상 지역 <ADDRESS_UNIT risk=\"P2\">{value}</ADDRESS_UNIT>를 남겼습니다."),
    ("application_area", "신청서의 거주 지역은 <ADDRESS_UNIT risk=\"P2\">{value}</ADDRESS_UNIT>입니다."),
    ("customer_area", "고객 주소 일부 <ADDRESS_UNIT risk=\"P2\">{value}</ADDRESS_UNIT>를 확인했습니다."),
    ("record_area", "상담 기록에는 <ADDRESS_UNIT risk=\"P2\">{value}</ADDRESS_UNIT> 거주로 남아 있습니다."),
    ("road_without_number", "주소 일부는 <ADDRESS_UNIT risk=\"P2\">{value}</ADDRESS_UNIT>까지만 입력됐습니다."),
    ("area_verification", "본인 확인 지역은 <ADDRESS_UNIT risk=\"P2\">{value}</ADDRESS_UNIT>입니다."),
)

ADDRESS_FULL_TEMPLATES = (
    ("address_label", "주소는 <ADDRESS_FULL risk=\"P1\">{value}</ADDRESS_FULL>입니다.", "주소는 [ADDRESS_1]입니다."),
    ("delivery", "배송지는 <ADDRESS_FULL risk=\"P1\">{value}</ADDRESS_FULL>입니다.", "배송지는 [ADDRESS_1]입니다."),
    ("residence", "거주지 <ADDRESS_FULL risk=\"P1\">{value}</ADDRESS_FULL>에 살고 있습니다.", "거주지 [ADDRESS_1]에 살고 있습니다."),
    ("visit", "방문 주소 <ADDRESS_FULL risk=\"P1\">{value}</ADDRESS_FULL>로 와 주세요.", "방문 주소 [ADDRESS_1]로 와 주세요."),
    ("contract", "계약서 주소는 <ADDRESS_FULL risk=\"P1\">{value}</ADDRESS_FULL>입니다.", "계약서 주소는 [ADDRESS_1]입니다."),
    ("shipping", "택배 수령지는 <ADDRESS_FULL risk=\"P1\">{value}</ADDRESS_FULL>입니다.", "택배 수령지는 [ADDRESS_1]입니다."),
    ("patient", "환자 주소 <ADDRESS_FULL risk=\"P1\">{value}</ADDRESS_FULL> 확인 완료.", "환자 주소 [ADDRESS_1] 확인 완료."),
    ("guardian", "보호자 주소는 <ADDRESS_FULL risk=\"P1\">{value}</ADDRESS_FULL>입니다.", "보호자 주소는 [ADDRESS_1]입니다."),
    ("invoice", "청구서 발송 주소 <ADDRESS_FULL risk=\"P1\">{value}</ADDRESS_FULL>를 남겼습니다.", "청구서 발송 주소 [ADDRESS_1]를 남겼습니다."),
    ("move_in", "전입 주소는 <ADDRESS_FULL risk=\"P1\">{value}</ADDRESS_FULL>입니다.", "전입 주소는 [ADDRESS_1]입니다."),
)

HARD_NEGATIVE_ADDRESS_TEMPLATES = (
    ("travel", "오늘은 {value} 여행 코스를 정리했습니다.", "지역 일반 언급"),
    ("news", "{value} 관련 뉴스 제목을 요약했습니다.", "뉴스 지역명"),
    ("menu", "{value} 맛집 목록을 비교했습니다.", "맛집 지역명"),
    ("trend", "{value} 상권 트렌드를 분석했습니다.", "상권 분석"),
    ("weather", "{value} 날씨가 맑다고 합니다.", "날씨 지역명"),
    ("transport", "{value} 교통 상황을 확인했습니다.", "교통 정보"),
    ("guide", "{value} 관광 가이드를 작성했습니다.", "관광 가이드"),
    ("policy", "{value} 공공 정책 자료를 읽었습니다.", "정책 자료"),
    ("history", "{value} 지명의 유래를 설명했습니다.", "지명 설명"),
    ("label", "지도 라벨에는 {value}만 표시합니다.", "지도 라벨"),
)


def build_cases() -> list[CaseSpec]:
    cases: list[CaseSpec] = []

    for value_index, value in enumerate(ADDRESS_UNIT_VALUES, start=1):
        for template_index, (tag, template) in enumerate(ADDRESS_UNIT_TEMPLATES, start=1):
            text = template.format(value=value)
            clean = text.replace("<ADDRESS_UNIT risk=\"P2\">", "").replace("</ADDRESS_UNIT>", "")
            cases.append(
                CaseSpec(
                    id=f"stage3-address-unit-{value_index:02d}-{template_index:02d}",
                    marked_text=text,
                    expected_masked_text=clean,
                    tags=("stage3", "stage3_address", "address_unit_positive", tag),
                    bucket="address_unit_positive",
                    risk_focus="ADDRESS_UNIT recall and granularity",
                )
            )

    for value_index, value in enumerate(ADDRESS_FULL_VALUES, start=1):
        for template_index, (tag, template, expected_template) in enumerate(ADDRESS_FULL_TEMPLATES, start=1):
            cases.append(
                CaseSpec(
                    id=f"stage3-address-full-{value_index:02d}-{template_index:02d}",
                    marked_text=template.format(value=value),
                    expected_masked_text=expected_template,
                    tags=("stage3", "stage3_address", "address_full_positive", tag),
                    bucket="address_full_positive",
                    risk_focus="ADDRESS_FULL recall and granularity",
                )
            )

    for value_index, value in enumerate(HARD_NEGATIVE_ADDRESS_VALUES, start=1):
        for template_index, (tag, template, reason) in enumerate(HARD_NEGATIVE_ADDRESS_TEMPLATES, start=1):
            text = template.format(value=value)
            cases.append(
                CaseSpec(
                    id=f"stage3-address-neg-{value_index:02d}-{template_index:02d}",
                    marked_text=text,
                    expected_masked_text=text,
                    tags=("stage3", "stage3_address", "hard_negative_address", tag),
                    bucket="hard_negative_address",
                    risk_focus="ADDRESS false positive",
                    negative_reason=reason,
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
    parser = argparse.ArgumentParser(description="Generate stage3 address marker fixtures.")
    parser.add_argument(
        "--output",
        default="data/eval/markers/stage3_address_expanded.jsonl",
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
