from pii_guardrail.dictionary_detectors import DictionaryDetector
from pii_guardrail.dictionary_loader import (
    load_dictionary_base_scores,
    load_dictionary_lists,
)
from pii_guardrail.enums import Action, EntityType
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


def test_dictionary_lists_loads_expected_categories() -> None:
    lists = load_dictionary_lists()

    for category in (
        "surnames",
        "given_name_candidates",
        "relation_terms",
        "address_si_gu_dong",
        "road_names",
        "organization_suffixes",
        "brand_organizations",
        "school_suffixes",
        "hospital_suffixes",
        "bank_names",
    ):
        assert category in lists, category
        assert lists[category]

    assert "김" in lists["surnames"]
    assert "하늘" in lists["given_name_candidates"]
    assert "신한은행" in lists["bank_names"]


def test_dictionary_base_scores_match_spec() -> None:
    scores = load_dictionary_base_scores()

    assert scores["surname"] == 0.25
    assert scores["given_name_candidate"] == 0.35
    assert scores["full_name_pattern"] == 0.55
    assert scores["road_name"] == 0.65
    assert scores["hospital_suffix"] == 0.60


def test_person_name_detected_via_full_name_pattern() -> None:
    raw = "담당자 김민수에게 전달했습니다."
    spans = _by_entity(_detect(DictionaryDetector(), raw), EntityType.PERSON_NAME)

    assert len(spans) == 1
    _assert_dict_span_contract(raw, spans[0], EntityType.PERSON_NAME)
    assert spans[0].text == "김민수"
    assert spans[0].score == 0.55
    assert "dictionary.surname_given.match" in spans[0].reason_codes


def test_person_name_detected_via_given_name_candidate() -> None:
    raw = "고객명 하늘, 연락처 010-1111-2222."
    spans = _by_entity(_detect(DictionaryDetector(), raw), EntityType.PERSON_NAME)

    assert len(spans) == 1
    _assert_dict_span_contract(raw, spans[0], EntityType.PERSON_NAME)
    assert spans[0].text == "하늘"
    assert spans[0].score == 0.35
    assert "dictionary.given_name_candidate" in spans[0].reason_codes


def test_person_name_skipped_when_first_char_not_surname() -> None:
    raw = "테헤란로에서 만났습니다."
    spans = _by_entity(_detect(DictionaryDetector(), raw), EntityType.PERSON_NAME)

    assert spans == []


def test_family_relation_detected() -> None:
    raw = "어머니께서 보내주셨습니다."
    spans = _by_entity(_detect(DictionaryDetector(), raw), EntityType.FAMILY_RELATION)

    assert len(spans) == 1
    _assert_dict_span_contract(raw, spans[0], EntityType.FAMILY_RELATION)
    assert spans[0].text == "어머니"
    assert spans[0].score == 0.40


def test_address_si_gu_dong_chain_emits_address_unit() -> None:
    raw = "서울특별시 강남구 역삼동에 살아요."
    spans = _by_entity(_detect(DictionaryDetector(), raw), EntityType.ADDRESS_UNIT)

    assert len(spans) == 1
    _assert_dict_span_contract(raw, spans[0], EntityType.ADDRESS_UNIT)
    assert spans[0].text == "서울특별시 강남구 역삼동"
    assert spans[0].score == 0.45


def test_address_full_combines_si_gu_dong_road_and_number() -> None:
    raw = "서울시 강남구 테헤란로 152에 거주합니다."
    spans = _by_entity(_detect(DictionaryDetector(), raw), EntityType.ADDRESS_FULL)

    assert len(spans) == 1
    _assert_dict_span_contract(raw, spans[0], EntityType.ADDRESS_FULL)
    assert spans[0].text.startswith("서울시 강남구 테헤란로")
    assert "152" in spans[0].text
    assert spans[0].score == 0.65


def test_apartment_unit_pattern_emits_address_unit() -> None:
    raw = "택배는 101동 1203호로 받겠습니다."
    spans = _by_entity(_detect(DictionaryDetector(), raw), EntityType.ADDRESS_UNIT)

    assert any(span.text == "101동 1203호" for span in spans)


def test_organization_brand_match_emits_organization() -> None:
    raw = "삼성전자에 입사했습니다."
    spans = _by_entity(_detect(DictionaryDetector(), raw), EntityType.ORGANIZATION)

    assert len(spans) == 1
    _assert_dict_span_contract(raw, spans[0], EntityType.ORGANIZATION)
    assert spans[0].text == "삼성전자"
    assert "dictionary.organization.brand" in spans[0].reason_codes


def test_school_suffix_expands_korean_head() -> None:
    raw = "졸업한 곳은 서울대학교입니다."
    spans = _by_entity(_detect(DictionaryDetector(), raw), EntityType.SCHOOL)

    assert spans
    _assert_dict_span_contract(raw, spans[0], EntityType.SCHOOL)
    assert spans[0].text.endswith("대학교")
    assert "서울" in spans[0].text


def test_hospital_suffix_expands_korean_head() -> None:
    raw = "환자는 서울중앙병원에서 치료받았습니다."
    spans = _by_entity(_detect(DictionaryDetector(), raw), EntityType.HOSPITAL)

    assert spans
    _assert_dict_span_contract(raw, spans[0], EntityType.HOSPITAL)
    assert spans[0].text == "서울중앙병원"


def test_dictionary_detector_emits_no_spans_for_unrelated_korean_text() -> None:
    raw = "오늘 점심은 무엇을 먹을까요?"
    spans = _detect(DictionaryDetector(), raw)

    assert spans == []


# ----------------------------------------------------------- review-fix regressions


def test_given_name_inside_longer_korean_word_is_not_matched() -> None:
    """Issue from PR #10 review: names inside longer words must not be emitted."""

    for raw in (
        "유진학교에 다닙니다.",
        "유진한국어 수업입니다.",
        "김민수학교에 다닙니다.",
    ):
        persons = _by_entity(_detect(DictionaryDetector(), raw), EntityType.PERSON_NAME)

        assert persons == []


def test_given_name_followed_by_josa_still_matches() -> None:
    """Boundary check must still allow full josa/honorific suffixes."""

    cases = (
        ("고객명 유진한테 연락했습니다.", "유진", DictionaryDetector()),
        ("담당자 김민수에게 전달했습니다.", "김민수", DictionaryDetector()),
        ("담당자 김민수에게서 확인했습니다.", "김민수", DictionaryDetector()),
        ("담당자 김민수에게는 전달했습니다.", "김민수", DictionaryDetector()),
        ("담당자 김민수한테서 확인했습니다.", "김민수", DictionaryDetector()),
        ("담당자 김민수께서는 확인했습니다.", "김민수", DictionaryDetector()),
        ("고객명 하늘이 신청했습니다.", "하늘", DictionaryDetector()),
        ("고객명 하늘입니다.", "하늘", DictionaryDetector()),
    )

    for raw, expected, detector in cases:
        persons = _by_entity(_detect(detector, raw), EntityType.PERSON_NAME)

        assert len(persons) == 1
        assert persons[0].text == expected

    dictionaries = dict(load_dictionary_lists())
    dictionaries["given_name_candidates"] = (
        *dictionaries["given_name_candidates"],
        "윤정",
    )
    raw = "고객명 윤정씨가 신청했습니다."
    persons = _by_entity(
        _detect(DictionaryDetector(dictionaries=dictionaries), raw),
        EntityType.PERSON_NAME,
    )

    assert len(persons) == 1
    assert persons[0].text == "윤정"


def test_apartment_unit_does_not_match_subway_line_pattern() -> None:
    """Issue from PR #10 review: non-address 호 continuations are rejected."""

    for raw in (
        "지하철 2호선 타고 갑니다.",
        "매장은 3호점입니다.",
        "장비는 1호기입니다.",
        "부대 앞 101동 1203호부대에서 만났습니다.",
    ):
        units = _by_entity(_detect(DictionaryDetector(), raw), EntityType.ADDRESS_UNIT)

        assert units == []


def test_apartment_unit_still_matches_when_followed_by_josa() -> None:
    cases = (
        ("주소는 1203호입니다.", "1203호"),
        ("택배는 1203호로 받겠습니다.", "1203호"),
        ("택배는 1203호에서 받겠습니다.", "1203호"),
        ("택배는 1203호에서는 받겠습니다.", "1203호"),
        ("택배는 1203호에서도 받겠습니다.", "1203호"),
        ("택배는 1203호부터 보관합니다.", "1203호"),
        ("택배는 1203호까지 보내주세요.", "1203호"),
        ("택배는 1203호까지도 보내주세요.", "1203호"),
        ("택배는 101동 1203호로 받겠습니다.", "101동 1203호"),
        ("주소는 역삼동 1203호입니다.", "1203호"),
    )

    for raw, expected in cases:
        units = _by_entity(_detect(DictionaryDetector(), raw), EntityType.ADDRESS_UNIT)

        assert any(span.text == expected for span in units), raw


def test_reason_codes_do_not_leak_matched_term() -> None:
    """Issue 1: rule ids only, no matched text such as '어머니' or term names."""

    raw = "어머니께서 보내주셨습니다. 서울중앙병원에서 만났습니다."
    spans = _detect(DictionaryDetector(), raw)

    for span in spans:
        for code in span.reason_codes:
            assert "어머니" not in code, code
            assert "서울중앙" not in code, code
            assert ":" not in code or code.endswith("match"), code
