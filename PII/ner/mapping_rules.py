"""
NER → PII 라벨 매핑 룰 + ADDRESS 후처리.

체크포인트별 라벨 스키마 차이를 PII 라벨로 통일.
W1 D3 sanity check 후 실제 스키마 보고 보강.
"""
from __future__ import annotations
import re

from schema import PIISpan, DEFAULT_RISK


# 체크포인트별 라벨 → PII 라벨 매핑
# (W1 D3에 실제 id2label 보고 update)
LABEL_MAP = {
    # KLUE-NER 표준 (PER/LOC/ORG/MISC)
    "PER": "NAME",
    "LOC": "ADDRESS",
    "ORG": "ORG",

    # 모두의 말뭉치 NER (Leo97)
    "PS": "NAME",      # Person
    "PS_NAME": "NAME",
    "LC": "ADDRESS",   # Location
    "LCP": "ADDRESS",  # 정치·행정구역
    "LCG": "ADDRESS",  # 지명
    "OG": "ORG",
    "OGG_ECONOMY": "ORG",
    "OGG_EDUCATION": "ORG",

    # KPF-bert-ner (확인 필요)
    # 일반 BIO 접두사
    "B-PER": "NAME", "I-PER": "NAME",
    "B-LOC": "ADDRESS", "I-LOC": "ADDRESS",
    "B-ORG": "ORG", "I-ORG": "ORG",

    # KLUE-NER 14-label 스키마
    "PS_OTHERS": "NAME",
    "LCP_COUNTRY": "ADDRESS",
    "LCP_PROVINCE": "ADDRESS",
    "LCP_CITY": "ADDRESS",

    # 제외 (NER 학습 X, 결정론 분리)
    # DT_*, TI_*, QT_* 류는 무시
}


def map_ner_label(raw_label: str) -> str | None:
    """체크포인트 라벨 → PII 타입. 모르는 라벨은 None."""
    # BIO 접두 제거
    if raw_label.startswith(("B-", "I-")):
        bare = raw_label[2:]
    else:
        bare = raw_label

    # 직접 매핑
    if bare in LABEL_MAP:
        return LABEL_MAP[bare]

    # prefix 매핑 (예: "PS_NAME" → PERSON)
    for key, value in LABEL_MAP.items():
        if bare.startswith(key + "_") or bare.startswith(key):
            return value

    return None


# ─────────────────────────────────────────────────────────────────
# ADDRESS 후처리 — 행정구역 단위 boundary 정규화
# NER이 "서울"/"강남구"/"테헤란로 152" 분리 출력 시 full span으로 병합
# ─────────────────────────────────────────────────────────────────

ADDR_HIERARCHY_PATTERN = re.compile(
    # 시·도 → 시·군·구 → 동·읍·면·리 → 도로명+번지 → 동·호
    r"((?:[가-힣]+(?:특별시|광역시|특별자치시|도))?\s*"
    r"(?:[가-힣]+(?:시|군|구))?\s*"
    r"(?:[가-힣]+(?:동|읍|면|리|로|길))\s*\d*(?:[-\s]\d+)?\s*"
    r"(?:\d+동\s*\d+호)?)"
)


def merge_address_spans(spans: list[PIISpan], text: str, max_gap: int = 5) -> list[PIISpan]:
    """인접한 ADDRESS span 병합.

    예: ["서울", "강남구", "테헤란로 152"] → ["서울 강남구 테헤란로 152"]
    """
    if not spans:
        return spans

    addr_spans = sorted([s for s in spans if s.type == "ADDRESS"],
                        key=lambda s: s.start)
    other_spans = [s for s in spans if s.type != "ADDRESS"]

    if not addr_spans:
        return spans

    merged = []
    current_start = addr_spans[0].start
    current_end = addr_spans[0].end
    current_conf_sum = addr_spans[0].confidence
    current_count = 1
    current_sources = [addr_spans[0].source]

    for sp in addr_spans[1:]:
        # 사이에 의미있는 토큰이 max_gap 이내?
        gap_text = text[current_end:sp.start]
        if len(gap_text.strip()) <= max_gap and not re.search(r"[.!?]", gap_text):
            # 병합
            current_end = sp.end
            current_conf_sum += sp.confidence
            current_count += 1
            current_sources.append(sp.source)
        else:
            # flush + 새 시작
            merged.append(_make_address_span(
                current_start, current_end, text,
                current_conf_sum / current_count, current_sources
            ))
            current_start = sp.start
            current_end = sp.end
            current_conf_sum = sp.confidence
            current_count = 1
            current_sources = [sp.source]

    # 마지막 flush
    merged.append(_make_address_span(
        current_start, current_end, text,
        current_conf_sum / current_count, current_sources
    ))

    return other_spans + merged


def _make_address_span(start: int, end: int, text: str,
                       conf: float, sources: list[str]) -> PIISpan:
    return PIISpan(
        start=start,
        end=end,
        type="ADDRESS",
        text=text[start:end],
        confidence=conf,
        source=sources[0] if len(sources) == 1 else "ner:merged",
        detector="ner",
        risk_level=DEFAULT_RISK["ADDRESS"],
        reason_codes=tuple([f"merge_count:{len(sources)}"]),
    )


# ─────────────────────────────────────────────────────────────────
# Boundary correction — 조사·호칭·어미 분리 (NAME 한정)
# 추후 korean_boundary.py로 분리될 수 있음 (Pipeline Owner와 협의)
# ─────────────────────────────────────────────────────────────────

JOSA_PATTERN = re.compile(
    # 격조사 + 보조사 (자주 나오는 것 위주)
    r"(이가|에게서|로부터|으로|에게|에서|와|과|도|는|은|을|를|이|가|로|의|만|"
    r"이라|이라고|라는|이라는|이며|라며|이며|랑|이랑)$"
)
HONORIFIC_PATTERN = re.compile(r"(님|씨|선생님|교수님|박사님|사장님|이사님)$")
VOCATIVE_PATTERN = re.compile(r"(아|야|어|이여|시여)$")


def split_name_boundary(span: PIISpan) -> PIISpan:
    """NAME span에서 조사·호칭·어미 분리.

    예: "홍길동이" → text="홍길동", suffix="이"
        "홍길동님" → text="홍길동", suffix="님"
    """
    if span.type != "NAME":
        return span

    text = span.text
    suffix = ""

    for pat in (HONORIFIC_PATTERN, VOCATIVE_PATTERN, JOSA_PATTERN):
        m = pat.search(text)
        if m:
            suffix = m.group(0)
            text = text[:m.start()]
            break  # 한 종류만 분리

    if not suffix:
        return span

    # 새 span 생성 (frozen이라 dataclasses.replace 사용)
    from dataclasses import replace
    return replace(
        span,
        end=span.end - len(suffix),
        text=text,
        suffix=suffix,
        reason_codes=span.reason_codes + (f"split:{suffix}",),
    )


def apply_boundary_correction(spans: list[PIISpan]) -> list[PIISpan]:
    """전체 span 리스트에 boundary correction 적용."""
    return [split_name_boundary(s) if s.type == "NAME" else s for s in spans]


# ─────────────────────────────────────────────────────────────────
# 통합 후처리 파이프라인
# ─────────────────────────────────────────────────────────────────

def postprocess_ner_output(spans: list[PIISpan], text: str) -> list[PIISpan]:
    """NER raw spans → 최종 NER PIISpan 리스트.

    1. ADDRESS 병합 (인접 LOC 토큰)
    2. NAME boundary correction (조사·호칭 분리)
    """
    spans = merge_address_spans(spans, text)
    spans = apply_boundary_correction(spans)
    return spans


# CLI 데모
if __name__ == "__main__":
    from mock_ner import get_ner

    ner = get_ner()
    samples = [
        "홍길동이 삼성전자 인사팀에 입사했다.",
        "서울 강남구 역삼동 테헤란로 152에 거주합니다.",
        "박지영님은 고려대학교 교수입니다.",
        "김민수씨에게 연락 부탁드려요.",
    ]
    for s in samples:
        raw = ner.predict(s)
        post = postprocess_ner_output(raw, s)
        print(f"\n📝 {s}")
        print(f"   raw: {[(sp.type, sp.text) for sp in raw]}")
        print(f"   post: {[(sp.type, sp.text, sp.suffix) for sp in post]}")
