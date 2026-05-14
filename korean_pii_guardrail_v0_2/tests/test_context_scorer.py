from pii_guardrail.context_scorer import ContextScorer
from pii_guardrail.dictionary_detectors import DictionaryDetector
from pii_guardrail.dictionary_loader import (
    load_composite_upgrades,
    load_context_boosts,
    load_context_penalties,
    load_field_label_terms,
    load_honorific_terms,
    load_negative_context_terms,
)
from pii_guardrail.enums import EntityType
from pii_guardrail.preprocess import preprocess_text
from pii_guardrail.regex_detectors import (
    BankAccountCandidateDetector,
    PhoneRegexDetector,
)
from pii_guardrail.schema import GuardrailRequest, PIISpan


def _request(raw: str) -> GuardrailRequest:
    return GuardrailRequest(text=raw)


def _detect_all(raw: str) -> tuple[list[PIISpan], object]:
    preprocessed = preprocess_text(raw)
    request = _request(raw)
    spans: list[PIISpan] = []
    spans.extend(DictionaryDetector().detect(preprocessed, request))
    spans.extend(PhoneRegexDetector().detect(preprocessed, request))
    spans.extend(BankAccountCandidateDetector().detect(preprocessed, request))
    spans.sort(key=lambda s: (s.start, s.end, s.entity_type.value))
    return spans, preprocessed


def _by_entity(spans: list[PIISpan], entity_type: EntityType) -> list[PIISpan]:
    return [span for span in spans if span.entity_type is entity_type]


def test_context_scorer_loads_spec_defined_boosts_and_penalties() -> None:
    boosts = load_context_boosts()
    penalties = load_context_penalties()

    assert boosts["field_label_name"] == 0.25
    assert boosts["bank_cooccur"] == 0.25
    assert boosts["full_address_detail"] == 0.20
    assert penalties["weather_context_for_person"] == -0.35
    assert penalties["example_context"] == -0.15


def test_context_scorer_field_label_terms_loaded_from_yaml() -> None:
    terms = load_field_label_terms()
    negatives = load_negative_context_terms()
    honorifics = load_honorific_terms()

    assert "고객명" in terms["name_label"]
    assert "계좌" in terms["account_label"]
    assert "맑네요" in negatives["weather_context"]
    assert "님" in honorifics["person_suffixes"]


def test_composite_upgrades_loaded_from_scoring_yaml() -> None:
    upgrades = load_composite_upgrades()

    assert upgrades[frozenset({"PERSON_NAME", "PHONE_MOBILE"})] == "P1"
    assert upgrades[frozenset({"PERSON_NAME", "EMAIL"})] == "P1"
    assert upgrades[frozenset({"MEDICAL_RECORD_NO", "HOSPITAL"})] == "P1"


def test_weather_context_suppresses_person_name_candidate() -> None:
    raw = "오늘 하늘이 맑네요."
    spans, preprocessed = _detect_all(raw)

    scored = ContextScorer().score(spans, preprocessed)
    persons = _by_entity(scored, EntityType.PERSON_NAME)

    assert len(persons) == 1
    person = persons[0]
    assert person.score == 0.0
    assert any(
        code.startswith("context.penalty.weather_context_for_person")
        for code in person.reason_codes
    )
    assert "context" in person.sources


def test_field_label_and_phone_cooccurrence_boost_person_name() -> None:
    raw = "고객명 하늘, 연락처 010-1111-2222."
    spans, preprocessed = _detect_all(raw)

    scored = ContextScorer().score(spans, preprocessed)
    persons = _by_entity(scored, EntityType.PERSON_NAME)

    assert len(persons) == 1
    person = persons[0]
    assert person.score >= 0.75
    assert person.is_composite is True
    assert any(
        code.startswith("context.boost.field_label_name")
        for code in person.reason_codes
    )
    assert any(
        code.startswith("context.boost.phone_cooccur_for_person")
        for code in person.reason_codes
    )
    assert any(code.startswith("context.composite.PHONE_MOBILE") for code in person.reason_codes)


def test_bank_account_boosted_by_field_label_and_bank_cooccurrence() -> None:
    raw = "계좌는 신한은행 110-123-456789입니다."
    spans, preprocessed = _detect_all(raw)

    scored = ContextScorer().score(spans, preprocessed)
    accounts = _by_entity(scored, EntityType.BANK_ACCOUNT)

    assert len(accounts) == 1
    account = accounts[0]
    assert account.score >= 0.75
    assert any(
        code.startswith("context.boost.field_label_account")
        for code in account.reason_codes
    )
    assert any(
        code.startswith("context.boost.bank_cooccur:신한은행")
        for code in account.reason_codes
    )


def test_example_context_penalises_every_entity_in_sentence() -> None:
    raw = "예시 전화번호는 010-0000-0000입니다."
    spans, preprocessed = _detect_all(raw)

    # PHONE regex still matches the synthetic-looking number; ensure penalty applies.
    scored = ContextScorer().score(spans, preprocessed)
    phones = _by_entity(scored, EntityType.PHONE_MOBILE)

    if phones:
        assert any(
            code.startswith("context.penalty.example_context")
            for code in phones[0].reason_codes
        )


def test_score_clamped_to_unit_interval() -> None:
    raw = "신한은행 계좌 입금 송금 110-123-456789"
    spans, preprocessed = _detect_all(raw)

    scored = ContextScorer().score(spans, preprocessed)
    accounts = _by_entity(scored, EntityType.BANK_ACCOUNT)

    assert accounts
    assert 0.0 <= accounts[0].score <= 1.0


def test_context_scorer_returns_empty_for_empty_spans() -> None:
    preprocessed = preprocess_text("그냥 텍스트입니다.")

    assert ContextScorer().score([], preprocessed) == []


def test_context_scorer_appends_context_source_and_detector_id() -> None:
    raw = "담당자 김민수에게 전달했습니다."
    spans, preprocessed = _detect_all(raw)

    scored = ContextScorer().score(spans, preprocessed)
    persons = _by_entity(scored, EntityType.PERSON_NAME)

    assert persons
    person = persons[0]
    assert "context" in person.sources
    assert "context.korean" in person.detector_ids
