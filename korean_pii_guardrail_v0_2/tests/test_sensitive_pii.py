"""Tests for PIPA Article 23 sensitive-information text PII.

Covers the layer_0 -> v0.2 port: dictionary detection of HEALTH_INFO /
RELIGIOUS_BELIEF / SEXUAL_ORIENTATION / POLITICAL_OPINION values, the
context-label gating that decides masking, and the FP-safe behaviour where a
bare value with no nearby label PASSes instead of being masked.
"""

from pii_guardrail.dictionary_detectors import DictionaryDetector
from pii_guardrail.enums import Action, EntityType
from pii_guardrail.pipeline import GuardrailPipeline
from pii_guardrail.preprocess import preprocess_text
from pii_guardrail.schema import GuardrailRequest, PIISpan


def _request(raw: str) -> GuardrailRequest:
    return GuardrailRequest(text=raw)


def _detect(detector: DictionaryDetector, raw: str) -> list[PIISpan]:
    return detector.detect(preprocess_text(raw), _request(raw))


def _by_entity(spans: list[PIISpan], entity_type: EntityType) -> list[PIISpan]:
    return [span for span in spans if span.entity_type is entity_type]


def _assert_dict_span_contract(raw: str, span: PIISpan, entity_type: EntityType) -> None:
    span.validate_against(raw)
    assert span.text == raw[span.start : span.end]
    assert span.entity_type is entity_type
    assert span.action is Action.CANDIDATE
    assert "dictionary" in span.sources
    assert span.detector_ids == ("dictionary.korean",)
    assert span.reason_codes


# --------------------------------------------------------------- detection (M2.5)


def test_health_subtypes_detected_with_subtype_reason_codes() -> None:
    cases = (
        ("견과류 알레르기가 있습니다.", "견과류", "dictionary.health.allergy"),
        ("진단명은 당뇨병입니다.", "당뇨병", "dictionary.health.diagnosis"),
        ("처방받은 약은 아토르바스타틴입니다.", "아토르바스타틴", "dictionary.health.prescription"),
        ("과거 척추융합술을 받았습니다.", "척추융합술", "dictionary.health.surgery"),
        ("등록된 장애는 시각장애입니다.", "시각장애", "dictionary.health.disability"),
        ("혈액형은 AB형Rh-입니다.", "AB형Rh-", "dictionary.health.blood"),
        ("진단: 공황장애 치료 중", "공황장애", "dictionary.health.mental"),
    )
    detector = DictionaryDetector()
    for raw, expected_value, expected_reason in cases:
        spans = _by_entity(_detect(detector, raw), EntityType.HEALTH_INFO)
        assert any(span.text == expected_value for span in spans), raw
        span = next(span for span in spans if span.text == expected_value)
        _assert_dict_span_contract(raw, span, EntityType.HEALTH_INFO)
        assert expected_reason in span.reason_codes


def test_religion_orientation_political_detected() -> None:
    detector = DictionaryDetector()
    for raw, value, entity_type in (
        ("종교는 불교입니다.", "불교", EntityType.RELIGIOUS_BELIEF),
        ("성적지향은 동성애입니다.", "동성애", EntityType.SEXUAL_ORIENTATION),
        ("지지정당은 국민의힘입니다.", "국민의힘", EntityType.POLITICAL_OPINION),
    ):
        spans = _by_entity(_detect(detector, raw), entity_type)
        assert len(spans) == 1, raw
        _assert_dict_span_contract(raw, spans[0], entity_type)
        assert spans[0].text == value


def test_longer_value_wins_over_substring() -> None:
    raw = "진단명은 제2형 당뇨병입니다."
    spans = _by_entity(_detect(DictionaryDetector(), raw), EntityType.HEALTH_INFO)
    assert len(spans) == 1
    assert spans[0].text == "제2형 당뇨병"


def test_value_inside_longer_korean_word_is_not_matched() -> None:
    # left word-boundary guard: '소아당뇨병' must not surface a '당뇨병' span.
    spans = _by_entity(_detect(DictionaryDetector(), "소아당뇨병 환자군 통계"), EntityType.HEALTH_INFO)
    assert spans == []


def test_no_sensitive_spans_for_unrelated_text() -> None:
    raw = "오늘 점심 메뉴를 무엇으로 정할지 고민입니다."
    spans = _detect(DictionaryDetector(), raw)
    assert _by_entity(spans, EntityType.HEALTH_INFO) == []
    assert _by_entity(spans, EntityType.RELIGIOUS_BELIEF) == []


def test_reason_codes_do_not_leak_matched_value() -> None:
    raw = "진단명은 당뇨병이고 종교는 불교입니다."
    spans = _detect(DictionaryDetector(), raw)
    assert spans
    for span in spans:
        for code in span.reason_codes:
            assert "당뇨병" not in code, code
            assert "불교" not in code, code
            assert ":" not in code or code.endswith("match"), code


# --------------------------------------------------------------- pipeline gating


def _process(raw: str):
    return GuardrailPipeline().process(_request(raw))


def test_health_value_with_label_is_masked() -> None:
    raw = "환자의 진단명은 당뇨병입니다."
    response = _process(raw)
    assert response.blocked is False
    assert response.masked_text is not None
    assert "[HEALTH_INFO_1]" in response.masked_text
    assert "당뇨병" not in response.masked_text


def test_religion_value_with_label_is_masked() -> None:
    raw = "그 사람의 종교는 불교입니다."
    response = _process(raw)
    assert response.masked_text is not None
    assert "[RELIGIOUS_BELIEF_1]" in response.masked_text
    assert "불교" not in response.masked_text


def test_orientation_and_political_with_label_are_masked() -> None:
    for raw, placeholder, raw_value in (
        ("그의 성적지향은 동성애라고 합니다.", "[SEXUAL_ORIENTATION_1]", "동성애"),
        ("그는 지지정당이 국민의힘이라고 밝혔다.", "[POLITICAL_OPINION_1]", "국민의힘"),
    ):
        response = _process(raw)
        assert response.masked_text is not None
        assert placeholder in response.masked_text, raw
        assert raw_value not in response.masked_text, raw


def test_bare_sensitive_value_without_label_passes() -> None:
    # FP-safe / precision-oriented: no nearby context label -> not masked.
    raw = "오늘 당뇨병 관련 건강 뉴스를 읽었습니다."
    response = _process(raw)
    assert response.blocked is False
    assert response.masked_text == raw  # unchanged
    assert "당뇨병" in response.masked_text


def test_bare_religion_mention_without_label_passes() -> None:
    raw = "불교는 한국 문화에 큰 영향을 주었습니다."
    response = _process(raw)
    assert response.masked_text == raw
    assert "불교" in response.masked_text


# --------------------------------------------------------------- boundary regressions


def test_compound_words_do_not_produce_sensitive_spans() -> None:
    # right word-boundary guard: a sensitive value that is only a prefix of a
    # longer compound noun must not surface a span.
    detector = DictionaryDetector()
    for raw in (
        "기독교인 봉사 모임 공지입니다.",       # 기독교 + 인
        "진보당원 명단을 정리했습니다.",         # 진보당 + 원
        "조현병동 입원 절차를 안내합니다.",      # 조현병 + 동
        "백내장수술실 예약이 가득 찼습니다.",    # 백내장수술 / 백내장 + 수/실
    ):
        spans = _detect(detector, raw)
        assert _by_entity(spans, EntityType.HEALTH_INFO) == [], raw
        assert _by_entity(spans, EntityType.RELIGIOUS_BELIEF) == [], raw
        assert _by_entity(spans, EntityType.POLITICAL_OPINION) == [], raw


def test_disability_with_label_is_masked() -> None:
    raw = "장애인 등록 정보: 시각장애"
    response = _process(raw)
    assert response.masked_text is not None
    assert "[HEALTH_INFO_1]" in response.masked_text
    assert "시각장애" not in response.masked_text


def test_value_followed_by_comparative_or_listing_particle_is_detected() -> None:
    # recall: comparative/listing/limiting particles must not be mistaken for a
    # compound-noun continuation (보다/나/뿐/처럼/마저 ...).
    detector = DictionaryDetector()
    for raw, value, entity_type in (
        ("당뇨병보다 고혈압이 더 위험합니다.", "당뇨병", EntityType.HEALTH_INFO),
        ("종교는 불교나 천주교 중 하나입니다.", "불교", EntityType.RELIGIOUS_BELIEF),
        ("우울증뿐 아니라 불안장애도 있다고 합니다.", "우울증", EntityType.HEALTH_INFO),
    ):
        spans = _by_entity(_detect(detector, raw), entity_type)
        assert any(span.text == value for span in spans), raw
