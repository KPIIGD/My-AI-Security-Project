import pytest

from pii_guardrail.enums import Action, EntityType, RiskLevel
from pii_guardrail.preprocess import preprocess_text
from pii_guardrail.regex_detectors import (
    BankAccountCandidateDetector,
    BusinessRegNoDetector,
    CorporateRegNoRegexDetector,
    CreditCardRegexDetector,
    DriverLicenseRegexDetector,
    EmailRegexDetector,
    FRNRegexDetector,
    LabeledIdentifierRegexDetector,
    NetworkIdentifierDetector,
    PassportRegexDetector,
    PhoneRegexDetector,
    RRNRegexDetector,
    SecretRegexDetector,
    deduplicate_spans,
    load_regex_base_scores,
)
from pii_guardrail.schema import GuardrailRequest, PIISpan


def _request(raw: str) -> GuardrailRequest:
    return GuardrailRequest(text=raw)


def _detect(detector: object, raw: str) -> list[PIISpan]:
    return detector.detect(preprocess_text(raw), _request(raw))


def _assert_span_contract(raw: str, span: PIISpan, entity_type: EntityType) -> None:
    span.validate_against(raw)
    assert span.text == raw[span.start : span.end]
    assert span.entity_type is entity_type
    assert span.action is Action.CANDIDATE
    assert "regex" in span.sources
    assert span.reason_codes
    assert span.detector_ids


def test_regex_scores_are_loaded_from_config() -> None:
    scores = load_regex_base_scores()

    assert scores["RRN"] == 0.98
    assert scores["FRN"] == 0.98
    assert scores["BUSINESS_REG_NO_PATTERN_ONLY"] == 0.75


def test_deduplicate_spans_keeps_max_score_and_unions_metadata() -> None:
    left = PIISpan(
        start=0,
        end=13,
        text="9001011234568",
        entity_type=EntityType.RRN,
        score=0.50,
        sources=("regex",),
        risk_level=RiskLevel.P0,
        reason_codes=("regex.rrn",),
        detector_ids=("regex.rrn.raw",),
    )
    right = PIISpan(
        start=0,
        end=13,
        text="9001011234568",
        entity_type=EntityType.RRN,
        score=0.98,
        sources=("validator",),
        risk_level=RiskLevel.P0,
        reason_codes=("validator.rrn.valid",),
        detector_ids=("regex.rrn.variant",),
    )

    [merged] = deduplicate_spans([left, right])

    assert merged.score == 0.98
    assert merged.sources == ("regex", "validator")
    assert merged.reason_codes == ("regex.rrn", "validator.rrn.valid")
    assert merged.detector_ids == ("regex.rrn.raw", "regex.rrn.variant")


def test_rrn_detector_returns_raw_candidate_span() -> None:
    raw = "주민번호는 900101-1234568 입니다."
    spans = _detect(RRNRegexDetector(), raw)

    assert len(spans) == 1
    _assert_span_contract(raw, spans[0], EntityType.RRN)
    assert spans[0].text == "900101-1234568"
    assert spans[0].score == 0.98
    assert "validator" in spans[0].sources


def test_rrn_detector_rejects_invalid_date_gender_and_length() -> None:
    detector = RRNRegexDetector()

    assert _detect(detector, "991332-1234567") == []
    assert _detect(detector, "900101-5234567") == []
    assert _detect(detector, "900101-123456") == []
    assert _detect(detector, "900101-1234567") == []


def test_rrn_detector_rejects_explicit_corporate_registration_context() -> None:
    raw = "\ubc95\uc778\ub4f1\ub85d\ubc88\ud638 110111-1000002 \ud655\uc778"

    assert _detect(RRNRegexDetector(), raw) == []


def test_rrn_detector_rejects_corporate_context_with_spacing_variant() -> None:
    raw = "\ubc95\uc778 \uc2dd\ubcc4\ubc88\ud638 110111-1000002\ub85c \uc800\uc7a5"

    assert _detect(RRNRegexDetector(), raw) == []


def test_rrn_detector_keeps_explicit_rrn_context_for_corporate_prefix_value() -> None:
    raw = "\uc8fc\ubbfc\ub4f1\ub85d\ubc88\ud638 110111-1000002 \ud655\uc778"
    spans = _detect(RRNRegexDetector(), raw)

    assert len(spans) == 1
    _assert_span_contract(raw, spans[0], EntityType.RRN)


def test_frn_detector_rejects_explicit_corporate_registration_context() -> None:
    raw = "\ub4f1\uae30\ubc88\ud638\ub294 110121-6543210\uc785\ub2c8\ub2e4."

    assert _detect(FRNRegexDetector(), raw) == []


def test_frn_detector_returns_raw_candidate_span() -> None:
    raw = "외국인등록번호 900101-5123450"
    spans = _detect(FRNRegexDetector(), raw)

    assert len(spans) == 1
    _assert_span_contract(raw, spans[0], EntityType.FRN)
    assert spans[0].text == "900101-5123450"
    assert spans[0].score == 0.98
    assert "validator" in spans[0].sources


def test_frn_detector_rejects_rrn_gender_digit() -> None:
    assert _detect(FRNRegexDetector(), "900101-1234568") == []
    assert _detect(FRNRegexDetector(), "900101-5123456") == []


@pytest.mark.parametrize(
    ("detector", "raw", "entity_type", "expected_text"),
    [
        (RRNRegexDetector(), "９００１０１－１２３４５６８", EntityType.RRN, "９００１０１－１２３４５６８"),
        (RRNRegexDetector(), "9 0 0 1 0 1 - 1 2 3 4 5 6 8", EntityType.RRN, "9 0 0 1 0 1 - 1 2 3 4 5 6 8"),
        (FRNRegexDetector(), "９００１０１－５１２３４５０", EntityType.FRN, "９００１０１－５１２３４５０"),
    ],
)
def test_rrn_frn_detectors_restore_m1_variant_spans(
    detector: object,
    raw: str,
    entity_type: EntityType,
    expected_text: str,
) -> None:
    spans = _detect(detector, raw)

    assert len(spans) == 1
    _assert_span_contract(raw, spans[0], entity_type)
    assert spans[0].text == expected_text


def test_phone_detector_classifies_mobile_and_landline() -> None:
    raw = "휴대폰 010-1234-5678, 사무실 02-123-4567"
    spans = _detect(PhoneRegexDetector(), raw)

    assert [span.entity_type for span in spans] == [EntityType.PHONE_MOBILE, EntityType.PHONE_LANDLINE]
    assert [span.text for span in spans] == ["010-1234-5678", "02-123-4567"]
    for span in spans:
        _assert_span_contract(raw, span, span.entity_type)
        assert "validator" in span.sources


def test_phone_detector_accepts_spaced_mobile_number() -> None:
    raw = "연락처 010 3456 7890로 연락 주세요."
    spans = _detect(PhoneRegexDetector(), raw)

    assert len(spans) == 1
    _assert_span_contract(raw, spans[0], EntityType.PHONE_MOBILE)
    assert spans[0].text == "010 3456 7890"


def test_phone_detector_rejects_service_like_examples() -> None:
    detector = PhoneRegexDetector()

    assert _detect(detector, "대표번호 1588-1234") == []
    assert _detect(detector, "인터넷전화 070-1234-5678") == []


@pytest.mark.parametrize(
    "raw",
    [
        "주문번호 010-1234-5678 처리 완료.",
        "접수번호 010 3456 7890는 상담 큐 번호입니다.",
        "tracking no 02-123-4567 was generated.",
    ],
)
def test_phone_detector_rejects_order_like_identifier_contexts(raw: str) -> None:
    assert _detect(PhoneRegexDetector(), raw) == []


def test_email_detector_returns_full_email_only() -> None:
    raw = "메일은 test.user+case@example.co.kr입니다."
    spans = _detect(EmailRegexDetector(), raw)

    assert len(spans) == 1
    _assert_span_contract(raw, spans[0], EntityType.EMAIL)
    assert spans[0].text == "test.user+case@example.co.kr"
    assert "validator" in spans[0].sources


def test_email_detector_rejects_invalid_domains() -> None:
    detector = EmailRegexDetector()

    assert _detect(detector, "메일 test@example") == []
    assert _detect(detector, "메일 test@-example.com") == []


def test_network_detector_emits_public_private_ip_and_mac() -> None:
    raw = "public 8.8.8.8 private 192.168.0.1 mac AA:BB:CC:DD:EE:FF"
    spans = _detect(NetworkIdentifierDetector(), raw)

    assert [(span.entity_type, span.text) for span in spans] == [
        (EntityType.IP_ADDRESS, "8.8.8.8"),
        (EntityType.IP_ADDRESS, "192.168.0.1"),
        (EntityType.MAC_ADDRESS, "AA:BB:CC:DD:EE:FF"),
    ]
    assert spans[0].score == 0.72
    assert spans[1].score == 0.45
    assert spans[2].score == 0.70
    for span in spans:
        _assert_span_contract(raw, span, span.entity_type)
        assert "validator" in span.sources


def test_network_detector_allows_sentence_period_after_ipv4() -> None:
    raw = "ip 8.8.9.27."
    spans = _detect(NetworkIdentifierDetector(), raw)

    assert len(spans) == 1
    _assert_span_contract(raw, spans[0], EntityType.IP_ADDRESS)
    assert spans[0].text == "8.8.9.27"


def test_network_detector_supports_ipv6_and_rejects_invalid_ip() -> None:
    raw = "dns 2001:4860:4860::8888 bad 999.999.999.999"
    spans = _detect(NetworkIdentifierDetector(), raw)

    assert len(spans) == 1
    _assert_span_contract(raw, spans[0], EntityType.IP_ADDRESS)
    assert spans[0].text == "2001:4860:4860::8888"


def test_credit_card_detector_emits_only_luhn_valid_cards() -> None:
    raw = "카드 4111-1111-1111-1111, 오타 4111-1111-1111-1112"
    spans = _detect(CreditCardRegexDetector(), raw)

    assert len(spans) == 1
    _assert_span_contract(raw, spans[0], EntityType.CREDIT_CARD)
    assert spans[0].text == "4111-1111-1111-1111"
    assert spans[0].score == 0.96
    assert "validator" in spans[0].sources


def test_credit_card_detector_rejects_repeated_placeholder() -> None:
    assert _detect(CreditCardRegexDetector(), "카드 0000-0000-0000-0000") == []


@pytest.mark.parametrize(
    "raw",
    [
        "\uacc4\uc88c 100106-27-101378",
        "\ud658\ubd88\uacc4\uc88c\ub294 KB 4111-1111-1111-1111",
        "corp 110111-1000217",
        "\ub4f1\uae30\ubc88\ud638\ub294 110121-6543210",
        "\ud68c\uc0ac \ub4f1\ub85d\ubc88\ud638 134511-5432109",
    ],
)
def test_credit_card_detector_rejects_non_card_structured_context(raw: str) -> None:
    assert _detect(CreditCardRegexDetector(), raw) == []


def test_business_reg_no_detector_emits_valid_and_pattern_only_candidates() -> None:
    raw = "사업자 123-45-67891, 후보 123-45-67892"
    spans = _detect(BusinessRegNoDetector(), raw)

    assert [span.text for span in spans] == ["123-45-67891", "123-45-67892"]
    assert [span.score for span in spans] == [0.92, 0.75]
    for span in spans:
        _assert_span_contract(raw, span, EntityType.BUSINESS_REG_NO)
        assert "validator" in span.sources


def test_business_reg_no_detector_rejects_phone_number_shape() -> None:
    assert _detect(BusinessRegNoDetector(), "\uc5f0\ub77d\ucc98 011-12-34567") == []


def test_business_reg_no_detector_rejects_placeholders() -> None:
    assert _detect(BusinessRegNoDetector(), "사업자 000-00-00000") == []


@pytest.mark.parametrize(
    "raw",
    [
        "주문번호 123-45-67891 처리 완료.",
        "송장번호 220-81-62517 배송 추적.",
        "invoice no 101-86-47510 was generated.",
    ],
)
def test_business_reg_no_detector_rejects_order_like_identifier_contexts(raw: str) -> None:
    assert _detect(BusinessRegNoDetector(), raw) == []


def test_business_reg_no_detector_rejects_medical_record_number_context() -> None:
    assert _detect(BusinessRegNoDetector(), "\ud658\uc790\ubc88\ud638 MR-2026-000016.") == []


def test_business_reg_no_detector_keeps_business_label_after_account_field() -> None:
    raw = "\uc815\uc0b0 \uacc4\uc88c 110-123-456789, \uc0ac\uc5c5\uc790\ub4f1\ub85d\ubc88\ud638 123-45-67891"
    spans = _detect(BusinessRegNoDetector(), raw)

    assert [span.text for span in spans] == ["123-45-67891"]
    _assert_span_contract(raw, spans[0], EntityType.BUSINESS_REG_NO)


def test_business_reg_no_detector_rejects_account_field_with_intermediate_bank_name() -> None:
    raw = "\ud658\ubd88\uacc4\uc88c\ub294 KB 123-45-67891\uc785\ub2c8\ub2e4."

    assert _detect(BusinessRegNoDetector(), raw) == []


@pytest.mark.parametrize(
    ("detector", "raw", "entity_type", "expected_text"),
    [
        (PassportRegexDetector(), "passport M11234567.", EntityType.PASSPORT, "M11234567"),
        (DriverLicenseRegexDetector(), "driver 12-34-123456-01.", EntityType.DRIVER_LICENSE, "12-34-123456-01"),
        (CorporateRegNoRegexDetector(), "corp 110111-1234567.", EntityType.CORPORATE_REG_NO, "110111-1234567"),
    ],
)
def test_structured_identifier_detectors_emit_raw_spans(
    detector: object,
    raw: str,
    entity_type: EntityType,
    expected_text: str,
) -> None:
    spans = _detect(detector, raw)

    assert len(spans) == 1
    _assert_span_contract(raw, spans[0], entity_type)
    assert spans[0].text == expected_text


@pytest.mark.parametrize(
    ("raw", "entity_type", "expected_text"),
    [
        ("\uace0\uac1d\ubc88\ud638 CUST-000123.", EntityType.CUSTOMER_ID, "CUST-000123"),
        ("\uc0ac\ubc88 EMP-2026-00123.", EntityType.EMPLOYEE_ID, "EMP-2026-00123"),
        ("\ud559\ubc88 STU-20260001.", EntityType.STUDENT_ID, "STU-20260001"),
        ("\ud658\uc790\ubc88\ud638 MR-2026-000123.", EntityType.MEDICAL_RECORD_NO, "MR-2026-000123"),
        ("\uc0dd\ub144\uc6d4\uc77c 1988\ub144 3\uc6d4 9\uc77c.", EntityType.DOB, "1988\ub144 3\uc6d4 9\uc77c"),
        ("device device-0001-A1B2C3.", EntityType.DEVICE_ID, "device-0001-A1B2C3"),
        ("vehicle 12\uac001234.", EntityType.VEHICLE_REG_NO, "12\uac001234"),
    ],
)
def test_labeled_identifier_detector_emits_value_only_raw_spans(
    raw: str,
    entity_type: EntityType,
    expected_text: str,
) -> None:
    spans = _detect(LabeledIdentifierRegexDetector(), raw)

    assert len(spans) == 1
    _assert_span_contract(raw, spans[0], entity_type)
    assert spans[0].text == expected_text


def test_labeled_identifier_detector_requires_label() -> None:
    raw = "CUST-000123 EMP-2026-00123 STU-20260001 MR-2026-000123"

    assert _detect(LabeledIdentifierRegexDetector(), raw) == []


def test_bank_account_detector_emits_low_score_pattern_only_candidate() -> None:
    raw = "신한은행 계좌 110-123-456789로 입금"
    spans = _detect(BankAccountCandidateDetector(), raw)

    assert len(spans) == 1
    _assert_span_contract(raw, spans[0], EntityType.BANK_ACCOUNT)
    assert spans[0].text == "110-123-456789"
    assert spans[0].score == 0.42
    assert spans[0].sources == ("regex", "validator")


@pytest.mark.parametrize(
    "raw",
    [
        "하나은행 계좌 123-12-12345-1로 입금",
        "카카오뱅크 계좌 3333-12-1234567로 입금",
    ],
)
def test_bank_account_detector_supports_profile_segment_lengths(raw: str) -> None:
    spans = _detect(BankAccountCandidateDetector(), raw)

    assert len(spans) == 1
    _assert_span_contract(raw, spans[0], EntityType.BANK_ACCOUNT)


def test_bank_account_detector_rejects_short_or_placeholder_numbers() -> None:
    detector = BankAccountCandidateDetector()

    assert _detect(detector, "계좌 12-345") == []
    assert _detect(detector, "계좌 000-000-0000") == []


@pytest.mark.parametrize(
    "raw",
    [
        "연락처 010-1234-5678",
        "연락처 010 3456 7890",
        "연락처 010\u200b-1234\u200b-5678",
        "카드 4111-1111-1111-1111",
        "사업자 123-45-67891",
        "주민번호 900101-1234568",
        "외국인등록번호 900101-5123450",
        "주문번호 2026-0001-1234",
        "접수번호 1000-1234-5678",
        "tracking no 110-123-456789",
    ],
)
def test_bank_account_detector_rejects_non_account_structured_identifiers(raw: str) -> None:
    assert _detect(BankAccountCandidateDetector(), raw) == []


def test_secret_detector_accepts_synthetic_secret_only() -> None:
    raw = "secret sk-AbC123xYz987TokenValue"
    spans = _detect(SecretRegexDetector(), raw)

    assert len(spans) == 1
    _assert_span_contract(raw, spans[0], EntityType.API_KEY_SECRET)
    assert spans[0].text == "sk-AbC123xYz987TokenValue"
    assert spans[0].score == 0.99
    assert "validator" in spans[0].sources


def test_secret_detector_rejects_low_entropy_or_missing_prefix() -> None:
    detector = SecretRegexDetector()

    assert _detect(detector, "secret sk-aaaaaaaaaaaaaaaaaaaa") == []
    assert _detect(detector, "secret token-AbC123xYz987TokenValue") == []


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("010\u200b-1234\u200b-5678", "010\u200b-1234\u200b-5678"),
        ("０１０－１２３４－５６７８", "０１０－１２３４－５６７８"),
        ("010 - 1234 - 5678", "010 - 1234 - 5678"),
        ("연락처는 공일공 일이삼사 오육칠팔입니다.", "공일공 일이삼사 오육칠팔"),
    ],
)
def test_phone_detector_restores_m1_variant_spans(raw: str, expected: str) -> None:
    spans = _detect(PhoneRegexDetector(), raw)

    assert len(spans) == 1
    _assert_span_contract(raw, spans[0], EntityType.PHONE_MOBILE)
    assert spans[0].text == expected


@pytest.mark.parametrize(
    "raw",
    [
        "주 민 번 호 900101-1234568",
        "ㅈㅁㅂㅎ는 900101-1234568",
        "jumin beonho 900101-1234568",
        "즈민뜽록볜훟 900101-1234568",
    ],
)
def test_rrn_detector_finds_structured_pii_near_m1_restored_keywords(raw: str) -> None:
    spans = _detect(RRNRegexDetector(), raw)

    assert len(spans) == 1
    _assert_span_contract(raw, spans[0], EntityType.RRN)
    assert spans[0].text == "900101-1234568"


def test_m2_detectors_do_not_classify_restored_korean_keywords_themselves() -> None:
    raw = "ㅈㅁㅂㅎ jumin beonho 즈민뜽록볜훟 주 민 번 호"
    detectors = (
        RRNRegexDetector(),
        FRNRegexDetector(),
        PhoneRegexDetector(),
        EmailRegexDetector(),
        NetworkIdentifierDetector(),
        CreditCardRegexDetector(),
        BusinessRegNoDetector(),
        PassportRegexDetector(),
        DriverLicenseRegexDetector(),
        CorporateRegNoRegexDetector(),
        LabeledIdentifierRegexDetector(),
        BankAccountCandidateDetector(),
        SecretRegexDetector(),
    )

    for detector in detectors:
        assert _detect(detector, raw) == []
