"""
ADDRESS span 후처리 v2 — 행정구역 hierarchy 기반 정교 병합.

KLUE-NER LOC가 분리 출력하는 한국 주소를 full span으로 묶기.
- 시·도 (서울특별시, 경기도)
- 시·군·구 (강남구, 수원시)
- 동·읍·면·리 (역삼동, 청담동)
- 도로명·길 (테헤란로, 강남대로, ○○길)
- 번지·번호 (123, 152-3)
- 동·호 (101동 1203호)
"""
from __future__ import annotations
import re
from typing import Tuple

# 행정구역 suffix 패턴
ADDR_SUFFIXES = [
    r"특별시", r"광역시", r"특별자치시", r"특별자치도",
    r"시", r"도",                                   # 시·도 (단, 서울/부산 같은 short는 제외)
    r"구", r"군",                                    # 시·군·구
    r"읍", r"면", r"동", r"리",                      # 동·읍·면·리
    r"로", r"길",                                    # 도로명
]

# 동·호 패턴 (아파트·빌라)
UNIT_PATTERN = re.compile(r"\d+\s*(?:동|호|차|단지)")

# 번지 패턴
LOTNO_PATTERN = re.compile(r"\d+(?:[-/]\d+)?\s*(?:번지)?")

# 도로명 + 번지
ROAD_FULL_PATTERN = re.compile(
    r"[가-힣A-Za-z0-9]+(?:로|길)\s*\d+(?:[-/]\d+)?"
)


def _is_continuation(prev_end: int, next_start: int, sentence: str,
                     max_gap: int = 6) -> bool:
    """두 span 사이가 ADDRESS 연속의 일부인가?"""
    gap = sentence[prev_end:next_start]
    # 너무 길거나 문장 종결 부호가 있으면 X
    if len(gap) > max_gap:
        return False
    if any(c in gap for c in ".!?\n"):
        return False
    # 콤마는 OK ("서울, 강남구")
    return True


def _expand_to_road_lotno(end: int, sentence: str) -> int:
    """ADDRESS span 끝에서 도로명·번지·동호수까지 확장."""
    rest = sentence[end:]
    # 도로명+번지 (테헤란로 152, 강남대로 123)
    m = ROAD_FULL_PATTERN.match(rest.lstrip())
    if m:
        end = end + len(rest) - len(rest.lstrip()) + m.end()
        rest = sentence[end:]

    # 콤마/공백 후 동·호 (101동 1203호)
    stripped = rest.lstrip(", ")
    offset = len(rest) - len(stripped)
    unit_m = UNIT_PATTERN.match(stripped)
    if unit_m:
        end = end + offset + unit_m.end()
        rest = sentence[end:]
        # 연속된 unit (101동 1203호)
        stripped2 = rest.lstrip(" ")
        offset2 = len(rest) - len(stripped2)
        unit_m2 = UNIT_PATTERN.match(stripped2)
        if unit_m2:
            end = end + offset2 + unit_m2.end()

    # 단순 번지 (지번 주소)
    rest = sentence[end:]
    stripped = rest.lstrip(" ")
    offset = len(rest) - len(stripped)
    lot_m = LOTNO_PATTERN.match(stripped)
    if lot_m and lot_m.group(0).strip():
        end = end + offset + lot_m.end()

    return end


def merge_address_spans_v2(spans: list[tuple], sentence: str) -> list[tuple]:
    """v1 단순 max_gap 병합 → v2 행정구역 hierarchy 기반 + 도로명·번지·동호수 확장.

    Args:
        spans: list of (start, end, type) tuples
        sentence: original text

    Returns:
        post-processed spans
    """
    if not spans:
        return spans

    addr = sorted([s for s in spans if s[2] == "ADDRESS"], key=lambda s: s[0])
    other = [s for s in spans if s[2] != "ADDRESS"]
    if not addr:
        return spans

    # 1단계: 인접 ADDRESS span 병합 (max_gap=6)
    merged = []
    cs, ce, ct = addr[0]
    for s, e, t in addr[1:]:
        if _is_continuation(ce, s, sentence):
            ce = e
        else:
            merged.append((cs, ce, ct))
            cs, ce, ct = s, e, t
    merged.append((cs, ce, ct))

    # 2단계: 각 span 끝을 도로명+번지+동호수로 확장
    expanded = []
    for s, e, t in merged:
        new_end = _expand_to_road_lotno(e, sentence)
        expanded.append((s, new_end, t))

    # 3단계: 확장 후 다시 인접 병합 (도로명까지 포함된 span끼리 합치기)
    final = []
    cs, ce, ct = expanded[0]
    for s, e, t in expanded[1:]:
        if s <= ce + 1 or _is_continuation(ce, s, sentence, max_gap=3):
            ce = max(ce, e)
        else:
            final.append((cs, ce, ct))
            cs, ce, ct = s, e, t
    final.append((cs, ce, ct))

    return other + final


# ─────────────────────────────────────────────────────────
# 데모 테스트
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    # 가상의 NER 출력 (KLUE LOC를 우리 ADDRESS로 매핑한 후 상태)
    test_cases = [
        {
            "sentence": "주소는 서울특별시 강남구 테헤란로 152 입니다.",
            "spans": [(4, 9, "ADDRESS"), (10, 13, "ADDRESS")],
            # gold: (4, 22, "ADDRESS")  ← "서울특별시 강남구 테헤란로 152"
        },
        {
            "sentence": "경기도 수원시 영통구 광교로 25에 거주합니다.",
            "spans": [(0, 3, "ADDRESS"), (4, 7, "ADDRESS"), (8, 11, "ADDRESS")],
        },
        {
            "sentence": "주소: 서울 강남구 청담동 123-45, 101동 1203호",
            "spans": [(4, 6, "ADDRESS"), (7, 10, "ADDRESS"), (11, 14, "ADDRESS")],
        },
        {
            "sentence": "홍길동은 서울에 살고 김철수는 부산에 산다.",
            "spans": [(5, 7, "ADDRESS"), (15, 17, "ADDRESS")],
            # 두 별개 주소 — 병합 X
        },
    ]

    for tc in test_cases:
        print(f"\n📝 {tc['sentence']}")
        print(f"   raw spans:    {tc['spans']}")
        merged = merge_address_spans_v2(tc['spans'], tc['sentence'])
        print(f"   merged:       {merged}")
        for s, e, t in merged:
            print(f"     [{t}] '{tc['sentence'][s:e]}'")
