from pii_guardrail.dictionary_detectors import DictionaryDetector
from pii_guardrail.context_scorer import ContextScorer
from pii_guardrail.dictionary_loader import load_entity_priority
from pii_guardrail.enums import Action, EntityType, RiskLevel
from pii_guardrail.korean_boundary import KoreanBoundaryCorrector
from pii_guardrail.preprocess import preprocess_text
from pii_guardrail.regex_detectors import (
    EmailRegexDetector,
    PhoneRegexDetector,
)
from pii_guardrail.schema import GuardrailRequest, PIISpan
from pii_guardrail.span_resolver import SpanResolver


def _request(raw: str) -> GuardrailRequest:
    return GuardrailRequest(text=raw)


def _make_span(
    raw: str,
    value: str,
    entity_type: EntityType,
    *,
    score: float = 0.7,
    risk_level: RiskLevel = RiskLevel.P1,
    sources: tuple[str, ...] = ("test",),
    reason_codes: tuple[str, ...] = ("test.candidate",),
    detector_ids: tuple[str, ...] = ("test",),
    is_composite: bool = False,
    occurrence: int = 1,
) -> PIISpan:
    cursor = -1
    for _ in range(occurrence):
        cursor = raw.index(value, cursor + 1)
    start = cursor
    return PIISpan(
        start=start,
        end=start + len(value),
        text=value,
        entity_type=entity_type,
        score=score,
        sources=sources,
        risk_level=risk_level,
        action=Action.CANDIDATE,
        reason_codes=reason_codes,
        detector_ids=detector_ids,
        is_composite=is_composite,
    )


def _by_type(spans, entity_type: EntityType) -> list[PIISpan]:
    return [s for s in spans if s.entity_type is entity_type]


# ---------------------------------------------------------- priority + smoke


def test_priority_order_includes_email_before_person_name() -> None:
    order = load_entity_priority()

    assert "EMAIL" in order
    assert "PERSON_NAME" in order
    assert order.index("EMAIL") < order.index("PERSON_NAME")


def test_resolve_empty_returns_empty() -> None:
    pre = preprocess_text("아무것도 없음.")

    assert SpanResolver().resolve([], pre, _request("아무것도 없음.")) == []


# ---------------------------------------------------------- duplicate merge


def test_duplicate_spans_collapse_with_max_score_and_union_metadata() -> None:
    raw = "이름 김민수 입니다."
    pre = preprocess_text(raw)
    left = _make_span(
        raw, "김민수", EntityType.PERSON_NAME,
        score=0.55, sources=("dictionary",), reason_codes=("dictionary.surname_given.match",),
        detector_ids=("dictionary.korean",),
    )
    right = _make_span(
        raw, "김민수", EntityType.PERSON_NAME,
        score=0.81, sources=("ner",), reason_codes=("ner.argmax",),
        detector_ids=("ner.finetuned",),
    )

    [resolved] = SpanResolver().resolve([left, right], pre, _request(raw))

    assert resolved.score == 0.81
    assert "dictionary" in resolved.sources and "ner" in resolved.sources
    assert "dictionary.surname_given.match" in resolved.reason_codes
    assert "ner.argmax" in resolved.reason_codes
    assert "dictionary.korean" in resolved.detector_ids
    assert "ner.finetuned" in resolved.detector_ids


# ---------------------------------------------------------- overlap priority


def test_email_substring_beats_person_name_candidate() -> None:
    raw = "메일은 test@example.com입니다."
    pre = preprocess_text(raw)
    email_span = _make_span(raw, "test@example.com", EntityType.EMAIL, score=0.92)
    person_span = _make_span(raw, "test", EntityType.PERSON_NAME, score=0.35)

    resolved = SpanResolver().resolve([email_span, person_span], pre, _request(raw))

    assert [s.entity_type for s in resolved] == [EntityType.EMAIL]
    assert "resolver.overlap.kept" in resolved[0].reason_codes


def test_school_reclassifies_overlapping_organization_candidate() -> None:
    raw = "출신은 서울대학교입니다."
    pre = preprocess_text(raw)
    org_span = _make_span(raw, "서울대학교", EntityType.ORGANIZATION, score=0.5)
    school_span = _make_span(raw, "서울대학교", EntityType.SCHOOL, score=0.55)

    resolved = SpanResolver().resolve([org_span, school_span], pre, _request(raw))

    assert [s.entity_type for s in resolved] == [EntityType.SCHOOL]


def test_hospital_reclassifies_overlapping_organization_candidate() -> None:
    raw = "근무지는 서울중앙병원입니다."
    pre = preprocess_text(raw)
    org_span = _make_span(raw, "서울중앙병원", EntityType.ORGANIZATION, score=0.5)
    hospital_span = _make_span(raw, "서울중앙병원", EntityType.HOSPITAL, score=0.6)

    resolved = SpanResolver().resolve([org_span, hospital_span], pre, _request(raw))

    assert [s.entity_type for s in resolved] == [EntityType.HOSPITAL]


def test_same_type_overlap_keeps_longer_span() -> None:
    raw = "서울 강남구 역삼동에서 만났습니다."
    pre = preprocess_text(raw)
    short = _make_span(raw, "서울 강남구", EntityType.ADDRESS_UNIT, score=0.45)
    long = _make_span(raw, "서울 강남구 역삼동", EntityType.ADDRESS_UNIT, score=0.45)

    resolved = SpanResolver().resolve([short, long], pre, _request(raw))

    assert len(resolved) == 1
    assert resolved[0].text == "서울 강남구 역삼동"


# ---------------------------------------------------------- ADDRESS merge


def test_adjacent_address_units_separated_by_whitespace_merge_to_address_full() -> None:
    raw = "배송지: 서울 강남구 역삼동 101동 1203호"
    pre = preprocess_text(raw)
    si_gu_dong = _make_span(raw, "서울 강남구 역삼동", EntityType.ADDRESS_UNIT, score=0.45)
    apartment = _make_span(raw, "101동 1203호", EntityType.ADDRESS_UNIT, score=0.70)

    resolved = SpanResolver().resolve([si_gu_dong, apartment], pre, _request(raw))

    assert len(resolved) == 1
    merged = resolved[0]
    assert merged.entity_type is EntityType.ADDRESS_FULL
    assert merged.text == "서울 강남구 역삼동 101동 1203호"
    assert merged.score == 0.70
    assert "resolver.address.fragment_merge" in merged.reason_codes
    assert merged.risk_level is RiskLevel.P1
    merged.validate_against(raw)


def test_address_fragments_separated_by_punctuation_do_not_merge() -> None:
    raw = "거주지는 서울 강남구, 사무실은 강남대로 152."
    pre = preprocess_text(raw)
    a = _make_span(raw, "서울 강남구", EntityType.ADDRESS_UNIT, score=0.45)
    b = _make_span(raw, "강남대로 152", EntityType.ADDRESS_FULL, score=0.65)

    resolved = SpanResolver().resolve([a, b], pre, _request(raw))

    assert len(resolved) == 2
    assert {s.entity_type for s in resolved} == {EntityType.ADDRESS_UNIT, EntityType.ADDRESS_FULL}


# ---------------------------------------------------------- composite escalation


def test_person_phone_composite_escalates_person_to_p1() -> None:
    raw = "고객명 박정민 연락처 010-1111-2222."
    pre = preprocess_text(raw)
    person = _make_span(
        raw, "박정민", EntityType.PERSON_NAME,
        score=0.55, risk_level=RiskLevel.P1, is_composite=True,
    )
    phone = _make_span(
        raw, "010-1111-2222", EntityType.PHONE_MOBILE,
        score=0.94, risk_level=RiskLevel.P1,
    )

    resolved = SpanResolver().resolve([person, phone], pre, _request(raw))
    by_type = {s.entity_type: s for s in resolved}

    person_out = by_type[EntityType.PERSON_NAME]
    # PERSON_NAME default is P1 already, so no level change but the resolver
    # should still leave is_composite True.
    assert person_out.is_composite is True


def test_composite_upgrade_raises_risk_level_when_pair_is_higher_risk() -> None:
    raw = "환자번호 PT-2026-0001 병원 서울중앙병원."
    pre = preprocess_text(raw)
    mrn = _make_span(
        raw, "PT-2026-0001", EntityType.MEDICAL_RECORD_NO,
        score=0.82, risk_level=RiskLevel.P2, is_composite=True,
    )
    hospital = _make_span(
        raw, "서울중앙병원", EntityType.HOSPITAL,
        score=0.60, risk_level=RiskLevel.P2, is_composite=True,
    )

    resolved = SpanResolver().resolve([mrn, hospital], pre, _request(raw))
    hospital_out = next(s for s in resolved if s.entity_type is EntityType.HOSPITAL)

    # MEDICAL_RECORD_NO + HOSPITAL → P1 per scoring.yaml composite_upgrades
    assert hospital_out.risk_level is RiskLevel.P1
    assert any(
        code.startswith("resolver.composite.upgrade:")
        for code in hospital_out.reason_codes
    )


def test_composite_escalation_skipped_across_sentence_boundary() -> None:
    raw = "박정민은 학생이다. 010-1111-2222."
    pre = preprocess_text(raw)
    person = _make_span(
        raw, "박정민", EntityType.PERSON_NAME,
        score=0.55, risk_level=RiskLevel.P1, is_composite=False,
    )
    phone = _make_span(
        raw, "010-1111-2222", EntityType.PHONE_MOBILE,
        score=0.94, risk_level=RiskLevel.P1,
    )

    resolved = SpanResolver().resolve([person, phone], pre, _request(raw))
    person_out = next(s for s in resolved if s.entity_type is EntityType.PERSON_NAME)

    # different sentences → no composite upgrade
    assert person_out.is_composite is False


def test_three_way_composite_escalates_to_p1() -> None:
    """Issue from PR #10 review: DOB + ADDRESS_UNIT + SCHOOL composite must escalate."""

    raw = "신청자 정보: 1995년 3월 1일, 서울 강남구 역삼동 거주, 서울고등학교 졸업."
    pre = preprocess_text(raw)
    dob = _make_span(
        raw, "1995년 3월 1일", EntityType.DOB,
        score=0.65, risk_level=RiskLevel.P2,
    )
    address_unit = _make_span(
        raw, "서울 강남구 역삼동", EntityType.ADDRESS_UNIT,
        score=0.45, risk_level=RiskLevel.P2,
    )
    school = _make_span(
        raw, "서울고등학교", EntityType.SCHOOL,
        score=0.55, risk_level=RiskLevel.P2,
    )

    resolved = SpanResolver().resolve([dob, address_unit, school], pre, _request(raw))

    # all three should escalate to P1 because they form a quasi-identifier triplet
    by_type = {s.entity_type: s for s in resolved}
    assert by_type[EntityType.DOB].risk_level is RiskLevel.P1
    assert by_type[EntityType.ADDRESS_UNIT].risk_level is RiskLevel.P1
    assert by_type[EntityType.SCHOOL].risk_level is RiskLevel.P1
    for span in resolved:
        assert any(
            code.startswith("resolver.composite.upgrade:")
            for code in span.reason_codes
        )
        assert span.is_composite is True


# ---------------------------------------------------------- pipeline


def test_full_pipeline_resolves_email_person_collision() -> None:
    raw = "메일은 test@example.com입니다."
    pre = preprocess_text(raw)
    req = _request(raw)
    spans = []
    spans.extend(DictionaryDetector().detect(pre, req))
    spans.extend(EmailRegexDetector().detect(pre, req))
    spans.extend(PhoneRegexDetector().detect(pre, req))
    spans = [KoreanBoundaryCorrector().correct(s, pre) for s in spans]
    spans = ContextScorer().score(spans, pre)
    resolved = SpanResolver().resolve(spans, pre, req)

    types = {s.entity_type for s in resolved}
    assert EntityType.EMAIL in types
    # PERSON candidates (if any) inside the email body should be removed
    person_inside_email = [
        s for s in resolved
        if s.entity_type is EntityType.PERSON_NAME and any(
            e.entity_type is EntityType.EMAIL and e.start <= s.start and s.end <= e.end
            for e in resolved
        )
    ]
    assert person_inside_email == []


def test_full_pipeline_merges_address_fragments_case_0016_pattern() -> None:
    raw = "배송지: 서울 강남구 역삼동 101동 1203호"
    pre = preprocess_text(raw)
    req = _request(raw)
    spans = DictionaryDetector().detect(pre, req)
    resolved = SpanResolver().resolve(spans, pre, req)

    full_addresses = [s for s in resolved if s.entity_type is EntityType.ADDRESS_FULL]
    assert any("역삼동" in s.text and "101동" in s.text and "1203호" in s.text for s in full_addresses)


def test_resolver_does_not_touch_score_or_action_on_passthrough() -> None:
    raw = "단일 후보만 있는 텍스트입니다."
    pre = preprocess_text(raw)
    person = _make_span(
        raw, "단일", EntityType.PERSON_NAME,
        score=0.42, risk_level=RiskLevel.P1,
    )

    [resolved] = SpanResolver().resolve([person], pre, _request(raw))

    assert resolved.score == 0.42
    assert resolved.action is Action.CANDIDATE
    # resolver may append its own detector id but the original must be preserved
    assert "test" in resolved.detector_ids
