"""NER 데이터센터 — canonical 스키마 + 정규화/검증 헬퍼.

핵심 설계 (finance datacenter 와 다른 점):
  finance: raw 텍스트 = 신호 → "전부 다" 가 맞음.
  NER:     라벨 없으면 무용 + v2 가 31k→139k 로 KLUE 0.766→0.664 폭락.
           → 데이터센터는 "최대 수집" 이 아니라 "소스별 품질·라이선스·누설 게이트".

모든 collector 는 아래 7-way BIO 스키마로 정규화한 example 을 emit 한다.
example dict 계약 (학습 포맷과 동일 — scripts/data_prep_v4 와 호환):
  {
    "tokens":      list[str],   # char-level 토큰
    "labels":      list[int],   # LABEL2ID 정수 (학습 직접 투입)
    "label_names": list[str],   # BIO 문자열
    "sentence":    str,         # 원문
    "source":      str,         # collector id
  }
"""
from __future__ import annotations

import hashlib
import re

# v3/v4 학습과 동일한 7-way BIO (scripts/data_prep_v4.PII_LABELS 와 일치)
PII_LABELS = ["O", "B-NAME", "I-NAME", "B-ADDRESS", "I-ADDRESS", "B-ORG", "I-ORG"]
LABEL2ID = {label: idx for idx, label in enumerate(PII_LABELS)}
ID2LABEL = {idx: label for idx, label in enumerate(PII_LABELS)}

_WS_RE = re.compile(r"\s+")


def normalize_sentence(sentence: str) -> str:
    """dedup/누설 비교용 정규화 — 공백 통일 + strip. (원문 자체는 보존)"""
    return _WS_RE.sub(" ", sentence or "").strip()


def content_hash(sentence: str) -> str:
    """문장 기반 dedup 키. 같은 문장(공백차 무시) = 같은 hash.

    corpus4everyone 이 KLUE 파생이라 소스 간 중복/누설이 핵심 위험.
    문장 단위 hash 라야 KLUE val/test 누설을 잡을 수 있다.
    """
    return hashlib.sha256(normalize_sentence(sentence).encode("utf-8")).hexdigest()


def count_entities(label_names: list[str]) -> int:
    """B-* 개수 = entity span 개수."""
    return sum(1 for label in label_names if label.startswith("B-"))


def bio_is_valid(label_names: list[str]) -> bool:
    """BIO 시퀀스 무결성: I-X 앞에 B-X/I-X 가 와야 함 (B 없이 I 시작 X)."""
    prev = "O"
    for label in label_names:
        if label.startswith("I-"):
            entity = label[2:]
            if prev not in (f"B-{entity}", f"I-{entity}"):
                return False
        prev = label
    return True


def validate_example(example: dict) -> tuple[bool, str]:
    """collector example 계약 검증. (ok, reason)."""
    for key in ("tokens", "labels", "label_names", "sentence", "source"):
        if key not in example:
            return False, f"missing key: {key}"
    n = len(example["tokens"])
    if not (len(example["labels"]) == len(example["label_names"]) == n):
        return False, "tokens/labels/label_names 길이 불일치"
    if any(label not in PII_LABELS for label in example["label_names"]):
        return False, "알 수 없는 라벨"
    if not bio_is_valid(example["label_names"]):
        return False, "BIO 무효 시퀀스 (B 없이 I 시작)"
    return True, "ok"
