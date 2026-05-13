"""Contract test for `pii_guardrail.ner.owner_wrapper.FinetunedKoreanNERDetector`.

이 테스트는 NER Owner wrapper 의 인터페이스 호환성과 출력 dict 형식만 검증한다.
실제 transformers/torch runtime 이나 모델 weight 다운로드 없이 동작하도록
backend monkey-patch 를 사용한다. 모델 활성화 검증은 M9 통합 단계에서 별도.
"""
from __future__ import annotations

import importlib

import pytest


_REQUIRED_DICT_KEYS = {
    "start", "end", "text", "entity_type", "score",
    "sources", "risk_level", "detector_ids", "reason_codes",
}

_ALLOWED_ENTITY_TYPES = {"PERSON_NAME", "ADDRESS_FULL", "ORGANIZATION"}


def test_module_is_importable():
    module = importlib.import_module("pii_guardrail.ner.owner_wrapper")
    assert hasattr(module, "FinetunedKoreanNERDetector")
    assert hasattr(module, "LABEL_TO_ENTITY_TYPE")
    assert hasattr(module, "ENTITY_TO_RISK_LEVEL")
    assert hasattr(module, "SIDO_PREFIXES")
    assert hasattr(module, "NAME_SUFFIX_PATTERN")


def test_label_to_entity_type_mapping():
    from pii_guardrail.ner.owner_wrapper import LABEL_TO_ENTITY_TYPE
    assert LABEL_TO_ENTITY_TYPE == {
        "NAME": "PERSON_NAME",
        "ADDRESS": "ADDRESS_FULL",
        "ORG": "ORGANIZATION",
    }
    assert set(LABEL_TO_ENTITY_TYPE.values()) == _ALLOWED_ENTITY_TYPES


def test_entity_risk_level_mapping():
    from pii_guardrail.ner.owner_wrapper import ENTITY_TO_RISK_LEVEL
    assert ENTITY_TO_RISK_LEVEL["PERSON_NAME"] == "P1"
    assert ENTITY_TO_RISK_LEVEL["ADDRESS_FULL"] == "P1"
    assert ENTITY_TO_RISK_LEVEL["ORGANIZATION"] == "P2"


def test_sido_prefixes_include_major_metros():
    from pii_guardrail.ner.owner_wrapper import SIDO_PREFIXES
    for sido in ("서울특별시", "부산광역시", "경기도", "제주특별자치도", "서울", "부산"):
        assert sido in SIDO_PREFIXES


def test_name_suffix_pattern_matches_josa():
    from pii_guardrail.ner.owner_wrapper import NAME_SUFFIX_PATTERN
    cases = ["이고", "이며", "에게", "한테", "에서", "이가", "은", "는", "님", "씨"]
    for suffix in cases:
        m = NAME_SUFFIX_PATTERN.search(f"홍길동{suffix}")
        assert m is not None, f"NAME_SUFFIX_PATTERN missed: {suffix}"
        assert m.group(1) == suffix


# ────────────────────────────────────────────────────────────
# Heuristic split — backend 없이 직접 호출
# ────────────────────────────────────────────────────────────
class _DummyDetector:
    """heuristic 메서드만 단독 호출하려는 mock — __init__ 생략."""

    def __init__(self):
        from pii_guardrail.ner.owner_wrapper import (
            LABEL_TO_ENTITY_TYPE, ENTITY_TO_RISK_LEVEL,
            SIDO_PREFIXES, NAME_SUFFIX_PATTERN,
        )
        self._sido = SIDO_PREFIXES
        self._suffix_pat = NAME_SUFFIX_PATTERN
        self.per_entity_threshold = {
            "PERSON_NAME": 0.0,
            "ADDRESS_FULL": 0.0,
            "ORGANIZATION": 0.0,
        }


def test_heuristic_split_separates_name_from_address():
    """모델 자체 처리되지 않은 conjunctive 케이스 → wrapper heuristic 분리."""
    from pii_guardrail.ner.owner_wrapper import FinetunedKoreanNERDetector

    raw_text = "안녕하세요, 저는 홍길동이고 서울시 강남구 테헤란로 152에 거주합니다."
    # 모델이 잘못 묶은 span (v1 한계 시나리오)
    bad_spans = [{"ner_type": "ADDRESS", "start": 10, "end": 32, "score": 1.0}]

    # 직접 인스턴스화 skip — heuristic 메서드만 직접 호출
    det = FinetunedKoreanNERDetector.__new__(FinetunedKoreanNERDetector)
    result = det._split_address_name_conjunction(bad_spans, raw_text)

    assert len(result) == 2
    name_span = next(s for s in result if s["ner_type"] == "NAME")
    addr_span = next(s for s in result if s["ner_type"] == "ADDRESS")
    assert raw_text[name_span["start"]:name_span["end"]] == "홍길동"
    assert raw_text[addr_span["start"]:addr_span["end"]].startswith("서울시")
    assert addr_span["_heuristic_split"] is True


def test_heuristic_skip_when_already_sido():
    """ADDRESS span 이 이미 시·도 prefix 로 시작하면 split 안 함."""
    from pii_guardrail.ner.owner_wrapper import FinetunedKoreanNERDetector

    raw_text = "서울시 강남구 테헤란로 152"
    clean_spans = [{"ner_type": "ADDRESS", "start": 0, "end": len(raw_text), "score": 1.0}]

    det = FinetunedKoreanNERDetector.__new__(FinetunedKoreanNERDetector)
    result = det._split_address_name_conjunction(clean_spans, raw_text)
    assert len(result) == 1
    assert result[0]["ner_type"] == "ADDRESS"
    assert "_heuristic_split" not in result[0]


def test_bio_to_spans_basic():
    """BIO → contiguous char span 변환 검증."""
    from pii_guardrail.ner.owner_wrapper import FinetunedKoreanNERDetector

    det = FinetunedKoreanNERDetector.__new__(FinetunedKoreanNERDetector)
    det.id2label = {0: "O", 1: "B-NAME", 2: "I-NAME", 3: "B-ADDRESS",
                    4: "I-ADDRESS", 5: "B-ORG", 6: "I-ORG"}

    # word_ids: [None, 0, 1, 2, 3, 4, 5, None]
    # pred_ids: [O, O, B-NAME, I-NAME, I-NAME, O, O, O]
    word_ids = [None, 0, 1, 2, 3, 4, 5, None]
    pred_ids = [0, 0, 1, 2, 2, 0, 0, 0]
    pred_probs = [[0.0] * 7 for _ in range(8)]
    for i in [2, 3, 4]:
        pred_probs[i][pred_ids[i]] = 0.95

    spans = det._bio_to_spans(pred_ids, pred_probs, word_ids, offset=0)
    assert len(spans) == 1
    assert spans[0]["ner_type"] == "NAME"
    assert spans[0]["start"] == 1
    assert spans[0]["end"] == 4


def test_postprocess_output_dict_keys():
    """`_postprocess_spans` 출력이 finetuned_wrapper.py 가 기대하는 dict 키 contract."""
    from pii_guardrail.ner.owner_wrapper import FinetunedKoreanNERDetector

    det = FinetunedKoreanNERDetector.__new__(FinetunedKoreanNERDetector)
    det.per_entity_threshold = {
        "PERSON_NAME": 0.5, "ADDRESS_FULL": 0.5, "ORGANIZATION": 0.5,
    }

    raw_text = "홍길동입니다."
    raw_spans = [{"ner_type": "NAME", "start": 0, "end": 3, "score": 0.92}]
    out = det._postprocess_spans(raw_spans, raw_text)

    assert len(out) == 1
    span = out[0]
    assert set(span.keys()) >= _REQUIRED_DICT_KEYS
    assert span["entity_type"] == "PERSON_NAME"
    assert span["entity_type"] in _ALLOWED_ENTITY_TYPES
    assert span["text"] == raw_text[span["start"]:span["end"]]
    assert isinstance(span["sources"], tuple)
    assert isinstance(span["detector_ids"], tuple)
    assert isinstance(span["reason_codes"], tuple)
    assert len(span["reason_codes"]) >= 1
    assert 0.0 <= span["score"] <= 1.0


def test_postprocess_filters_below_threshold():
    """per-entity threshold 미달 span 은 emit 안 됨."""
    from pii_guardrail.ner.owner_wrapper import FinetunedKoreanNERDetector

    det = FinetunedKoreanNERDetector.__new__(FinetunedKoreanNERDetector)
    det.per_entity_threshold = {"PERSON_NAME": 0.99}

    raw_spans = [{"ner_type": "NAME", "start": 0, "end": 3, "score": 0.50}]
    out = det._postprocess_spans(raw_spans, "홍길동")
    assert out == []


def test_unknown_ner_type_dropped():
    """LABEL_TO_ENTITY_TYPE 에 매핑 없는 type 은 emit 안 됨."""
    from pii_guardrail.ner.owner_wrapper import FinetunedKoreanNERDetector

    det = FinetunedKoreanNERDetector.__new__(FinetunedKoreanNERDetector)
    det.per_entity_threshold = {"PERSON_NAME": 0.0}

    raw_spans = [{"ner_type": "UNKNOWN_TYPE", "start": 0, "end": 3, "score": 0.99}]
    out = det._postprocess_spans(raw_spans, "abc")
    assert out == []
