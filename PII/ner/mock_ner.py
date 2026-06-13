"""
Mock NER — 실제 모델 결정 전, Pipeline Owner가 W3부터 통합 시작 가능하도록.

A-primary 결정(W2 화 EOD)되면 ner_wrapper.py로 교체.
인터페이스(NerInterface)는 동일 → 교체 시 import 한 줄만 변경.

NER Owner 책임:
- 이 파일 + ner_wrapper.py(추후) 가 동일한 NerInterface 구현 보장
- raw text char offset 정확성 (Pipeline Owner와 분쟁 원천 방지)
"""
from __future__ import annotations
import re
from typing import Protocol

from schema import PIISpan, DEFAULT_RISK


class NerInterface(Protocol):
    """모든 NER 구현체가 따라야 할 계약."""

    def predict(self, text: str) -> list[PIISpan]:
        """raw text → PIISpan 리스트.

        보장사항:
        - 반환 PIISpan의 start/end는 raw text 기준
        - text[span.start:span.end] == span.text
        - confidence ∈ [0.0, 1.0]
        - source는 "ner:<model_name>" 형식
        - detector == "ner"
        """
        ...


class MockNER:
    """W3 통합 테스트용 mock. 단순 정규식으로 NAME/ADDRESS/ORG 흉내."""

    def __init__(self):
        # 흔한 한국 성씨 (mock 용 — 실제 NER에선 모델이 학습)
        self._common_surnames = {
            "김", "이", "박", "최", "정", "강", "조", "윤", "장", "임",
            "한", "오", "서, 신", "권", "황", "안", "송", "전", "홍", "유",
        }
        # 행정구역 keywords
        self._addr_keywords = [
            "서울특별시", "부산광역시", "대구광역시", "인천광역시",
            "광주광역시", "대전광역시", "울산광역시", "세종특별자치시",
            "강남구", "서초구", "마포구", "성동구", "강북구", "노원구",
            "역삼동", "삼성동", "신촌동", "압구정동",
        ]
        # 회사 패턴
        self._org_pattern = re.compile(
            r"((?:\(주\))?(?:삼성전자|LG전자|SK하이닉스|현대자동차|네이버|카카오|"
            r"포스코|한화|롯데|신세계|GS|두산|코오롱)|"
            r"(?:[가-힣]{2,4}(?:대학교|대학|병원|연구소|공사|공단)))"
        )
        # 이름 패턴 (성 + 1~2자 이름)
        surnames = "|".join(sorted(self._common_surnames, key=len, reverse=True))
        self._name_pattern = re.compile(
            f"({surnames})([가-힣]{{1,3}})"
        )
        # 주소 패턴 (지역명 기반)
        addr_keys = "|".join(sorted(self._addr_keywords, key=len, reverse=True))
        self._addr_pattern = re.compile(f"({addr_keys})")

    @property
    def source(self) -> str:
        return "ner:mock-v1"

    def predict(self, text: str) -> list[PIISpan]:
        """mock NER inference. 단순 패턴 매칭으로 PIISpan 흉내."""
        spans: list[PIISpan] = []

        # NAME (성 + 이름 패턴)
        for m in self._name_pattern.finditer(text):
            full = m.group(0)
            spans.append(PIISpan(
                start=m.start(),
                end=m.end(),
                type="NAME",
                text=full,
                confidence=0.85,  # mock confidence
                source=self.source,
                detector="ner",
                risk_level=DEFAULT_RISK.get("NAME", "P1"),
                reason_codes=("mock:surname_match",),
            ))

        # ADDRESS (행정구역 매칭, 인접 LOC 토큰 병합 시뮬)
        addr_matches = list(self._addr_pattern.finditer(text))
        if addr_matches:
            # 인접한 ADDRESS keyword들 병합 (행정구역 단위 boundary 정규화 mock)
            i = 0
            while i < len(addr_matches):
                start = addr_matches[i].start()
                end = addr_matches[i].end()
                while i + 1 < len(addr_matches) and addr_matches[i + 1].start() <= end + 5:
                    end = addr_matches[i + 1].end()
                    i += 1
                full = text[start:end]
                spans.append(PIISpan(
                    start=start,
                    end=end,
                    type="ADDRESS",
                    text=full,
                    confidence=0.80,
                    source=self.source,
                    detector="ner",
                    risk_level=DEFAULT_RISK.get("ADDRESS", "P1"),
                    reason_codes=("mock:addr_keyword_merge",),
                ))
                i += 1

        # ORG
        for m in self._org_pattern.finditer(text):
            full = m.group(0)
            spans.append(PIISpan(
                start=m.start(),
                end=m.end(),
                type="ORG",
                text=full,
                confidence=0.78,
                source=self.source,
                detector="ner",
                risk_level=DEFAULT_RISK.get("ORG", "P2"),
                reason_codes=("mock:org_pattern",),
            ))

        return spans


def get_ner() -> NerInterface:
    """factory — 추후 ner_wrapper.py로 교체."""
    return MockNER()


# CLI 데모
if __name__ == "__main__":
    ner = get_ner()
    samples = [
        "홍길동이 010-1234-5678로 연락했습니다.",
        "삼성전자 인사팀 김과장은 서울 강남구에 거주합니다.",
        "고려대학교 박지영 교수에게 문의하세요.",
        "(주)카카오 본사는 판교에 있습니다.",
    ]
    for s in samples:
        print(f"\n📝 {s}")
        for sp in ner.predict(s):
            print(f"   [{sp.type:<8}] '{sp.text}' @ ({sp.start},{sp.end}) conf={sp.confidence}")
