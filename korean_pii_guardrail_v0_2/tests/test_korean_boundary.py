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
