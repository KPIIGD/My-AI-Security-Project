import pytest

from pii_guardrail.enums import Action, EntityType, RiskLevel
from pii_guardrail.korean_boundary import KoreanBoundaryCorrector
from pii_guardrail.preprocess import preprocess_text
from pii_guardrail.regex_detectors import BankAccountCandidateDetector, EmailRegexDetector, PhoneRegexDetector
from pii_guardrail.schema import GuardrailRequest, PIISpan


def _span(raw: str, value: str, entity_type: EntityType = EntityType.PERSON_NAME) -> PIISpan:
    start = raw.index(value)
    end = start + len(value)
    return PIISpan(
        start=start,
        end=end,
        text=raw[start:end],
        entity_type=entity_type,
        score=0.81,
        sources=("ner",),
        risk_level=RiskLevel.P1,
        action=Action.CANDIDATE,
        normalized="stale-normalized",
        reason_codes=("ner.mock",),
        detector_ids=("ner.mock",),
        policy_profile="strict",
    )


def _correct(raw: str, span: PIISpan) -> PIISpan:
    corrected = KoreanBoundaryCorrector().correct(span, preprocess_text(raw))
    corrected.validate_against(raw)
    return corrected


def _detect_and_correct(detector: object, raw: str) -> tuple[PIISpan, PIISpan]:
    preprocessed = preprocess_text(raw)
    [detected] = detector.detect(preprocessed, GuardrailRequest(text=raw))
    corrected = KoreanBoundaryCorrector().correct(detected, preprocessed)
    corrected.validate_against(raw)
    return detected, corrected


def test_trims_josa_from_person_span() -> None:
    raw = "홍길동이 왔습니다."
    corrected = _correct(raw, _span(raw, "홍길동이"))

    assert corrected.text == "홍길동"
    assert corrected.end == len("홍길동")
    assert corrected.suffix == "이"
    assert corrected.normalized is None
    assert corrected.reason_codes == ("ner.mock", "boundary.suffix_trim", "suffix.josa")


def test_trims_longest_person_josa_suffix() -> None:
    raw = "김민수에게 연락하세요."
    corrected = _correct(raw, _span(raw, "김민수에게"))

    assert corrected.text == "김민수"
    assert corrected.suffix == "에게"
    assert corrected.reason_codes[-2:] == ("boundary.suffix_trim", "suffix.josa")


def test_trims_honorific_from_person_span() -> None:
    raw = "김민수님 확인했습니다."
    corrected = _correct(raw, _span(raw, "김민수님"))

    assert corrected.text == "김민수"
    assert corrected.suffix == "님"
    assert corrected.reason_codes[-2:] == ("boundary.suffix_trim", "suffix.honorific")


def test_does_not_trim_person_name_to_one_syllable_body() -> None:
    raw = "고객명 사랑님 확인했습니다."
    corrected = _correct(raw, _span(raw, "사랑"))

    assert corrected.text == "사랑"
    assert corrected.suffix == "님"
    assert corrected.reason_codes[-2:] == ("boundary.suffix_lookahead", "suffix.honorific")


def test_address_road_name_final_ro_is_not_trimmed_as_josa() -> None:
    raw = "주소 일부는 서울시 강남구 테헤란로까지만 입력됐습니다."
    span = _span(raw, "서울시 강남구 테헤란로", EntityType.ADDRESS_UNIT)
    span = PIISpan(
        start=span.start,
        end=span.end,
        text=span.text,
        entity_type=span.entity_type,
        score=span.score,
        sources=span.sources,
        risk_level=RiskLevel.P2,
        action=span.action,
        reason_codes=("dictionary.address_unit", "dictionary.address.road_name_without_number"),
        detector_ids=span.detector_ids,
    )

    corrected = _correct(raw, span)

    assert corrected.text == "서울시 강남구 테헤란로"
    assert corrected.suffix == "까지만"
    assert "boundary.suffix_lookahead" in corrected.reason_codes
    assert corrected.reason_codes[-1] == "suffix.josa"


def test_captures_numeric_pii_lookahead_josa_without_changing_offsets() -> None:
    raw = "연락처 010-1234-5678로 전화하세요."
    span = _span(raw, "010-1234-5678", EntityType.PHONE_MOBILE)
    corrected = _correct(raw, span)

    assert corrected.text == "010-1234-5678"
    assert corrected.start == span.start
    assert corrected.end == span.end
    assert corrected.suffix == "로"
    assert corrected.normalized == "stale-normalized"
    assert corrected.reason_codes[-2:] == ("boundary.suffix_lookahead", "suffix.josa")


def test_captures_longest_numeric_pii_lookahead_josa() -> None:
    raw = "계좌 110-123-456789으로 입금하세요."
    span = _span(raw, "110-123-456789", EntityType.BANK_ACCOUNT)
    corrected = _correct(raw, span)

    assert corrected.text == "110-123-456789"
    assert corrected.suffix == "으로"
    assert corrected.reason_codes[-2:] == ("boundary.suffix_lookahead", "suffix.josa")


def test_captures_email_lookahead_ending_without_changing_offsets() -> None:
    raw = "메일 test@example.com입니다"
    span = _span(raw, "test@example.com", EntityType.EMAIL)
    corrected = _correct(raw, span)

    assert corrected.text == "test@example.com"
    assert corrected.start == span.start
    assert corrected.end == span.end
    assert corrected.suffix == "입니다"
    assert corrected.reason_codes[-2:] == ("boundary.suffix_lookahead", "suffix.ending")


@pytest.mark.parametrize(
    ("detector", "raw", "expected_text"),
    (
        (PhoneRegexDetector(), "연락처 010-1234-5678입니다.", "010-1234-5678"),
        (EmailRegexDetector(), "메일 test@example.com입니다.", "test@example.com"),
        (BankAccountCandidateDetector(), "계좌 신한은행 110-123-456789입니다.", "110-123-456789"),
    ),
)
def test_terminal_punctuation_is_not_included_in_ending_suffix(
    detector: object,
    raw: str,
    expected_text: str,
) -> None:
    _, corrected = _detect_and_correct(detector, raw)

    assert corrected.text == expected_text
    assert corrected.text == raw[corrected.start : corrected.end]
    assert corrected.suffix == "입니다"
    assert raw[corrected.end :].startswith("입니다.")
    assert corrected.reason_codes[-2:] == ("boundary.suffix_lookahead", "suffix.ending")


@pytest.mark.parametrize(
    ("entity_type", "raw", "body"),
    (
        (EntityType.HOSPITAL, "병원은 서울중앙병원입니다.", "서울중앙병원"),
        (EntityType.ORGANIZATION, "기관은 한국정보보호원입니다.", "한국정보보호원"),
        (EntityType.SCHOOL, "학교는 한국대학교입니다.", "한국대학교"),
        (EntityType.ADDRESS_FULL, "주소는 서울시 강남구 테헤란로 123입니다.", "서울시 강남구 테헤란로 123"),
        (EntityType.ADDRESS_UNIT, "동네는 역삼동입니다.", "역삼동"),
    ),
)
def test_text_entities_capture_ending_suffix_without_terminal_punctuation(
    entity_type: EntityType,
    raw: str,
    body: str,
) -> None:
    span = _span(raw, body, entity_type)
    corrected = _correct(raw, span)

    assert corrected.text == body
    assert corrected.text == raw[corrected.start : corrected.end]
    assert corrected.suffix == "입니다"
    assert raw[corrected.end :].startswith("입니다.")
    assert corrected.reason_codes[-2:] == ("boundary.suffix_lookahead", "suffix.ending")


@pytest.mark.parametrize(
    ("entity_type", "raw", "body"),
    (
        (EntityType.HOSPITAL, "병원은 서울중앙병원입니다.", "서울중앙병원"),
        (EntityType.ORGANIZATION, "기관은 한국정보보호원입니다.", "한국정보보호원"),
        (EntityType.SCHOOL, "학교는 한국대학교입니다.", "한국대학교"),
        (EntityType.ADDRESS_FULL, "주소는 서울시 강남구 테헤란로 123입니다.", "서울시 강남구 테헤란로 123"),
        (EntityType.ADDRESS_UNIT, "동네는 역삼동입니다.", "역삼동"),
    ),
)
def test_text_entities_trim_internal_ending_suffix(
    entity_type: EntityType,
    raw: str,
    body: str,
) -> None:
    span = _span(raw, f"{body}입니다", entity_type)
    corrected = _correct(raw, span)

    assert corrected.text == body
    assert corrected.text == raw[corrected.start : corrected.end]
    assert corrected.suffix == "입니다"
    assert corrected.normalized is None
    assert corrected.reason_codes[-2:] == ("boundary.suffix_trim", "suffix.ending")


def test_address_trim_partial_predicate_after_road_number() -> None:
    raw = "주소는 서울시 강남구 테헤란로 123 거주"
    body = "서울시 강남구 테헤란로 123"
    overextended = f"{body} 거"
    corrected = _correct(raw, _span(raw, overextended, EntityType.ADDRESS_FULL))

    assert corrected.text == body
    assert corrected.text == raw[corrected.start : corrected.end]
    assert corrected.suffix is None
    assert raw[corrected.end :].startswith(" 거주")
    assert corrected.normalized is None
    assert corrected.reason_codes[-1] == "boundary.address_partial_word_trim"


@pytest.mark.parametrize(
    ("raw", "value", "body", "entity_type", "expected_suffix", "expected_reason_tail"),
    (
        ("김민수에게서 확인했습니다.", "김민수에게서", "김민수", EntityType.PERSON_NAME, "에게서", ("suffix.compound_josa",)),
        ("김민수께서는 확인했습니다.", "김민수께서는", "김민수", EntityType.PERSON_NAME, "께서는", ("suffix.compound_josa",)),
        ("병원은 서울중앙병원에서도 확인했습니다.", "서울중앙병원에서도", "서울중앙병원", EntityType.HOSPITAL, "에서도", ("suffix.compound_josa",)),
        ("기관은 한국정보보호원이라고 확인했습니다.", "한국정보보호원이라고", "한국정보보호원", EntityType.ORGANIZATION, "이라고", ("suffix.quotative",)),
        ("홍길동입니다", "홍길동입니다", "홍길동", EntityType.PERSON_NAME, "입니다", ("suffix.ending",)),
    ),
)
def test_trims_curated_compound_suffix_from_overextended_spans(
    raw: str,
    value: str,
    body: str,
    entity_type: EntityType,
    expected_suffix: str,
    expected_reason_tail: tuple[str, ...],
) -> None:
    corrected = _correct(raw, _span(raw, value, entity_type))

    assert corrected.text == body
    assert corrected.text == raw[corrected.start : corrected.end]
    assert corrected.suffix == expected_suffix
    assert corrected.normalized is None
    assert corrected.reason_codes[1] == "boundary.suffix_trim"
    assert corrected.reason_codes[-len(expected_reason_tail) :] == expected_reason_tail


@pytest.mark.parametrize(
    ("raw", "body", "entity_type", "expected_suffix", "expected_reason_tail"),
    (
        ("메일 test@example.com이라는 값입니다.", "test@example.com", EntityType.EMAIL, "이라는", ("suffix.quotative",)),
        ("기관은 한국정보보호원이라고 했습니다.", "한국정보보호원", EntityType.ORGANIZATION, "이라고", ("suffix.quotative",)),
        ("병원은 서울중앙병원에서도 확인했습니다.", "서울중앙병원", EntityType.HOSPITAL, "에서도", ("suffix.compound_josa",)),
        ("담당자는 김민수에게서 확인했습니다.", "김민수", EntityType.PERSON_NAME, "에게서", ("suffix.compound_josa",)),
        ("담당자는 김민수에게서도 확인했습니다.", "김민수", EntityType.PERSON_NAME, "에게서도", ("suffix.compound_josa", "suffix.josa")),
    ),
)
def test_captures_curated_compound_suffix_by_lookahead(
    raw: str,
    body: str,
    entity_type: EntityType,
    expected_suffix: str,
    expected_reason_tail: tuple[str, ...],
) -> None:
    corrected = _correct(raw, _span(raw, body, entity_type))

    assert corrected.text == body
    assert corrected.text == raw[corrected.start : corrected.end]
    assert corrected.suffix == expected_suffix
    assert corrected.reason_codes[1] == "boundary.suffix_lookahead"
    assert corrected.reason_codes[-len(expected_reason_tail) :] == expected_reason_tail


@pytest.mark.parametrize(
    ("raw", "body", "entity_type"),
    (
        ("홍길동이라면 확인이 필요합니다.", "홍길동", EntityType.PERSON_NAME),
        ("메일 test@example.com이라고요 확인했습니다.", "test@example.com", EntityType.EMAIL),
    ),
)
def test_does_not_capture_partial_unsupported_suffix(
    raw: str,
    body: str,
    entity_type: EntityType,
) -> None:
    span = _span(raw, body, entity_type)
    corrected = _correct(raw, span)

    assert corrected == span
    assert corrected.suffix is None


def test_does_not_apply_disallowed_honorific_to_email() -> None:
    raw = "메일 test@example.com님"
    span = _span(raw, "test@example.com", EntityType.EMAIL)
    corrected = _correct(raw, span)

    assert corrected == span
    assert corrected.suffix is None


def test_does_not_correct_entities_without_boundary_rules() -> None:
    raw = "secret sk-AbC123xYz987TokenValue로"
    span = _span(raw, "sk-AbC123xYz987TokenValue", EntityType.API_KEY_SECRET)
    corrected = _correct(raw, span)

    assert corrected == span
    assert corrected.suffix is None


def test_correction_is_idempotent_and_does_not_duplicate_reason_codes() -> None:
    raw = "홍길동이 왔습니다."
    corrector = KoreanBoundaryCorrector()
    first = corrector.correct(_span(raw, "홍길동이"), preprocess_text(raw))
    second = corrector.correct(first, preprocess_text(raw))

    assert second == first
    assert second.reason_codes.count("boundary.suffix_trim") == 1
    assert second.reason_codes.count("suffix.josa") == 1


def test_phone_detector_span_can_be_boundary_corrected() -> None:
    raw = "연락처 010-1234-5678로 전화하세요."
    detected, corrected = _detect_and_correct(PhoneRegexDetector(), raw)

    assert detected.text == "010-1234-5678"
    assert corrected.text == detected.text
    assert corrected.suffix == "로"
    assert corrected.score == detected.score
    assert corrected.action is detected.action


def test_email_detector_span_can_be_boundary_corrected() -> None:
    raw = "메일 test@example.com입니다"
    detected, corrected = _detect_and_correct(EmailRegexDetector(), raw)

    assert detected.text == "test@example.com"
    assert corrected.text == detected.text
    assert corrected.suffix == "입니다"
    assert corrected.score == detected.score
    assert corrected.action is detected.action


def test_bank_account_detector_span_can_be_boundary_corrected() -> None:
    raw = "신한은행 계좌 110-123-456789로 입금하세요."
    detected, corrected = _detect_and_correct(BankAccountCandidateDetector(), raw)

    assert detected.text == "110-123-456789"
    assert corrected.text == detected.text
    assert corrected.suffix == "로"
    assert corrected.score == detected.score
    assert corrected.action is detected.action


def test_public_span_includes_suffix_without_raw_text() -> None:
    raw = "연락처 010-1234-5678로 전화하세요."
    _, corrected = _detect_and_correct(PhoneRegexDetector(), raw)
    public = corrected.to_public()
    public_data = public.to_dict()

    assert public.suffix == "로"
    assert public_data["suffix"] == "로"
    assert "text" not in public_data
