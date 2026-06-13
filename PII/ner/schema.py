"""
PIISpan contract — NER Owner와 Pipeline Owner의 공통 인터페이스.

deck slide 38 기반 + 2026-05-08 토론 확장:
- start/end는 raw text char offset (token offset 금지)
- raw PII는 hash로만 저장 (운영 원칙)
- confidence + source + detector 추가 → Span Ledger 충돌 해결 근거

NER Owner 책임: NER 결과 → mapped PIISpan까지
Pipeline Owner 책임: regex > NER > dict > tier4 충돌 병합 (Span Ledger)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Literal


# v0 라벨 스키마 (라벨 가이드와 동기화 필수)
PII_TYPES = Literal[
    # NER 학습 클래스 (KLUE-NER PER/LOC/OG → 매핑)
    "NAME",        # 사람 이름
    "ADDRESS",     # 주소 (행정구역 + 도로명 + 동호수)
    "ORG",         # 조직 (회사·학교·병원·기관)

    # 결정론 분리 클래스 (사전 + 정규식, NER 학습 X)
    "TITLE",       # 직책 (대리/과장/팀장/원장)
    "DEPT",        # 부서 (인사팀/개발팀/R&D센터)
    "DISEASE",     # 진단명/처방약 (KCD-8 사전)
    "CONTACT",     # 통합 후처리용 (regex 결과 표시)

    # 정규식 전담 (Tier 1 정형 PII)
    "RRN",         # 주민등록번호
    "FRN",         # 외국인등록번호
    "PHONE",       # 전화번호
    "EMAIL",       # 이메일
    "CREDIT_CARD",
    "BANK_ACCOUNT",
    "API_KEY",
    "PASSPORT",
    "DRIVER_LICENSE",
]

# 위험도 (P0 가장 높음, P3 가장 낮음)
RISK_LEVEL = Literal["P0", "P1", "P2", "P3"]

# 탐지기 출처 (Span Ledger 충돌 해결용)
DETECTOR = Literal["ner", "regex", "dict", "tier4", "session"]


@dataclass(frozen=True)
class PIISpan:
    """detector가 반환하는 단일 PII span.

    핵심 불변식:
    - start/end는 raw text char offset (정규화 후 offset 금지)
    - end는 exclusive (text[start:end] 가능)
    - text는 raw text의 substring (디버깅·로깅에 hash로 변환됨)
    - confidence: NER softmax max prob, regex/dict는 1.0

    raw PII는 직접 저장 X. text 필드는 메모리에서만 사용,
    영속 저장 시 hash(text)로 치환됨 (운영 원칙).
    """

    start: int                          # raw text char offset, inclusive
    end: int                            # raw text char offset, exclusive
    type: str                           # PII_TYPES 중 하나
    text: str                           # 원문 substring (디버깅용, 로그에 hash로 치환)
    confidence: float                   # 0.0 ~ 1.0
    source: str                         # "ner:kpf-bert-v1" | "regex:rrn_v2" | "dict:disease_v27" | "tier4:3slot"
    detector: str                       # DETECTOR 중 하나
    risk_level: str = "P2"              # P0/P1/P2/P3 (기본 중간)
    suffix: str = ""                    # 분리된 조사·호칭·어미 ("이", "에게", "님")
    reason_codes: tuple = field(default_factory=tuple)  # 판정 근거 ("ctx_boost:고객명", "neg_ctx:날씨" 등)

    def __post_init__(self):
        # 불변식 검증
        if self.start < 0:
            raise ValueError(f"start must be >= 0, got {self.start}")
        if self.end <= self.start:
            raise ValueError(f"end must be > start, got start={self.start} end={self.end}")
        if not (0.0 <= self.confidence <= 1.0):
            raise ValueError(f"confidence must be 0.0~1.0, got {self.confidence}")
        if self.detector not in {"ner", "regex", "dict", "tier4", "session"}:
            raise ValueError(f"detector must be one of ner/regex/dict/tier4/session, got {self.detector}")

    def to_dict(self) -> dict:
        """직렬화 (로그·DB 저장 시 text는 hash로 치환됨)."""
        return {
            "start": self.start,
            "end": self.end,
            "type": self.type,
            "text_hash": hash(self.text),  # raw PII 저장 금지
            "confidence": self.confidence,
            "source": self.source,
            "detector": self.detector,
            "risk_level": self.risk_level,
            "suffix": self.suffix,
            "reason_codes": list(self.reason_codes),
        }

    @property
    def length(self) -> int:
        return self.end - self.start

    def overlaps(self, other: PIISpan) -> bool:
        """다른 span과 char range overlap?"""
        return not (self.end <= other.start or other.end <= self.start)


# 위험도 ↔ 타입 기본 매핑 (Span Ledger에서 사용)
DEFAULT_RISK = {
    "RRN": "P0", "FRN": "P0", "PASSPORT": "P0", "DRIVER_LICENSE": "P0",
    "CREDIT_CARD": "P0", "BANK_ACCOUNT": "P0", "API_KEY": "P0",
    "PHONE": "P1", "EMAIL": "P1", "NAME": "P1", "ADDRESS": "P1",
    "ORG": "P2", "TITLE": "P2", "DEPT": "P2", "DISEASE": "P2",
    "CONTACT": "P1",
}


# Detector 우선순위 (Span Ledger 충돌 해결, 숫자 클수록 우선)
DETECTOR_PRIORITY = {
    "regex": 4,   # 정규식이 가장 결정론적 (Tier 1)
    "ner": 3,     # NER이 그다음 (NAME/ADDR/ORG)
    "dict": 2,    # 사전 매칭
    "tier4": 1,   # 룰 기반 quasi-id (risk_flag만, mask X)
    "session": 0, # 세션 누적 (옵션)
}
