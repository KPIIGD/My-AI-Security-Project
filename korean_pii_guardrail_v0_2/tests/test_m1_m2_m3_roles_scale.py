import pytest

from pii_guardrail.enums import Action, EntityType, RiskLevel
from pii_guardrail.korean_boundary import KoreanBoundaryCorrector
from pii_guardrail.preprocess import preprocess_text
from pii_guardrail.regex_detectors import BankAccountCandidateDetector, EmailRegexDetector, PhoneRegexDetector
from pii_guardrail.schema import GuardrailRequest, PIISpan


FULLWIDTH_DIGITS = str.maketrans("0123456789", "０１２３４５６７８９")
KOREAN_DIGITS = {
    "0": "공",
    "1": "일",
    "2": "이",
    "3": "삼",
    "4": "사",
    "5": "오",
    "6": "육",
    "7": "칠",
    "8": "팔",
    "9": "구",
}


def _fullwidth(value: str) -> str:
    return value.translate(FULLWIDTH_DIGITS)


def _korean_digits(value: str) -> str:
    return "".join(KOREAN_DIGITS[digit] for digit in value)


def _phone_number(index: int) -> tuple[str, str, str]:
    middle = f"{1000 + index:04d}"
    last = f"{2000 + index:04d}"
    return "010", middle, last


def _m1_fullwidth_cases() -> list[tuple[str, str]]:
    cases: list[tuple[str, str]] = []
    for index in range(80):
        prefix, middle, last = _phone_number(index)
        raw_phone = f"{_fullwidth(prefix)}－{_fullwidth(middle)}－{_fullwidth(last)}"
        cases.append((f"연락처 {raw_phone}", f"{prefix}-{middle}-{last}"))
    return cases


def _m1_zero_width_cases() -> list[tuple[str, str]]:
    cases: list[tuple[str, str]] = []
    for index in range(80, 160):
        prefix, middle, last = _phone_number(index)
        raw_phone = f"{prefix}\u200b-{middle[:2]}\u200b{middle[2:]}-{last}"
        cases.append((f"연락처 {raw_phone}", f"{prefix}-{middle}-{last}"))
    return cases


def _m1_korean_digit_cases() -> list[tuple[str, str]]:
    cases: list[tuple[str, str]] = []
    for index in range(40):
        prefix, middle, last = _phone_number(index)
        raw_phone = f"{_korean_digits(prefix)} {_korean_digits(middle)} {_korean_digits(last)}"
        cases.append((f"연락처는 {raw_phone}입니다.", f"{prefix}{middle}{last}"))
    return cases


def _m2_phone_cases() -> list[tuple[str, str]]:
    cases: list[tuple[str, str]] = []
    for index in range(140):
        prefix, middle, last = _phone_number(index)
        phone = f"{prefix}-{middle}-{last}"
        cases.append((f"연락처 {phone} 확인", phone))
    return cases


def _m2_email_cases() -> list[tuple[str, str]]:
    cases: list[tuple[str, str]] = []
    for index in range(120):
        email = f"user{index}.case+tag@example{index % 50}.co.kr"
        cases.append((f"메일 {email} 확인", email))
    return cases


def _m2_bank_account_cases() -> list[tuple[str, str]]:
    cases: list[tuple[str, str]] = []
    for index in range(80):
        account = f"{110 + index % 30:03d}-{100 + index:03d}-{100000 + index:06d}"
        cases.append((f"신한은행 계좌 {account} 확인", account))
    return cases


def _m3_phone_suffix_cases() -> list[tuple[str, str, str]]:
    suffixes = ("로", "으로", "입니다", "라고", "입니다.")
    cases: list[tuple[str, str, str]] = []
    for index in range(90):
        prefix, middle, last = _phone_number(index)
        phone = f"{prefix}-{middle}-{last}"
        suffix = suffixes[index % len(suffixes)]
        cases.append((f"연락처 {phone}{suffix} 확인", phone, suffix))
    return cases


def _m3_email_suffix_cases() -> list[tuple[str, str, str]]:
    suffixes = ("로", "입니다", "라고", "입니다.")
    cases: list[tuple[str, str, str]] = []
    for index in range(70):
        email = f"user{index}@example{index % 40}.com"
        suffix = suffixes[index % len(suffixes)]
        cases.append((f"메일 {email}{suffix} 확인", email, suffix))
    return cases


def _m3_person_trim_cases() -> list[tuple[str, str, str, str]]:
    suffixes = ("이", "에게", "님", "씨", "으로", "부터")
    cases: list[tuple[str, str, str, str]] = []
    for index in range(90):
        body = f"김민수{index}"
        suffix = suffixes[index % len(suffixes)]
        value = f"{body}{suffix}"
        cases.append((f"{value} 확인했습니다.", value, body, suffix))
    return cases


@pytest.mark.parametrize(("raw", "expected"), _m1_fullwidth_cases() + _m1_zero_width_cases())
def test_m1_normalization_preserves_raw_text_and_builds_offset_maps(raw: str, expected: str) -> None:
    preprocessed = preprocess_text(raw)

    assert preprocessed.raw_text == raw
    assert expected in preprocessed.normalized_text
    assert len(preprocessed.raw_to_norm) == len(raw)
    assert len(preprocessed.norm_to_raw) == len(preprocessed.normalized_text)


@pytest.mark.parametrize(("raw", "expected_variant_text"), _m1_korean_digit_cases())
def test_m1_korean_digit_variant_stays_in_preprocess_layer(raw: str, expected_variant_text: str) -> None:
    preprocessed = preprocess_text(raw)
    variant_texts = {variant.name: variant.text for variant in preprocessed.variants}

    assert expected_variant_text in variant_texts["korean_digit_restored"]
    assert not hasattr(preprocessed, "entity_type")
    assert not hasattr(preprocessed, "action")


@pytest.mark.parametrize(("raw", "expected_text"), _m2_phone_cases())
def test_m2_phone_detector_returns_candidate_only(raw: str, expected_text: str) -> None:
    preprocessed = preprocess_text(raw)
    [span] = PhoneRegexDetector().detect(preprocessed, GuardrailRequest(text=raw))

    span.validate_against(raw)
    assert span.text == expected_text
    assert span.entity_type is EntityType.PHONE_MOBILE
    assert span.action is Action.CANDIDATE
    assert span.suffix is None


@pytest.mark.parametrize(("raw", "expected_text"), _m2_email_cases())
def test_m2_email_detector_returns_candidate_only(raw: str, expected_text: str) -> None:
    preprocessed = preprocess_text(raw)
    [span] = EmailRegexDetector().detect(preprocessed, GuardrailRequest(text=raw))

    span.validate_against(raw)
    assert span.text == expected_text
    assert span.entity_type is EntityType.EMAIL
    assert span.action is Action.CANDIDATE
    assert span.suffix is None


@pytest.mark.parametrize(("raw", "expected_text"), _m2_bank_account_cases())
def test_m2_bank_account_detector_returns_low_score_candidate_only(raw: str, expected_text: str) -> None:
    preprocessed = preprocess_text(raw)
    [span] = BankAccountCandidateDetector().detect(preprocessed, GuardrailRequest(text=raw))

    span.validate_against(raw)
    assert span.text == expected_text
    assert span.entity_type is EntityType.BANK_ACCOUNT
    assert span.action is Action.CANDIDATE
    assert span.score == 0.42
    assert span.suffix is None


@pytest.mark.parametrize(("raw", "expected_text", "expected_suffix"), _m3_phone_suffix_cases())
def test_m3_boundary_captures_phone_suffix_without_changing_detector_role(
    raw: str,
    expected_text: str,
    expected_suffix: str,
) -> None:
    preprocessed = preprocess_text(raw)
    [detected] = PhoneRegexDetector().detect(preprocessed, GuardrailRequest(text=raw))
    corrected = KoreanBoundaryCorrector().correct(detected, preprocessed)

    corrected.validate_against(raw)
    assert detected.suffix is None
    assert corrected.text == expected_text
    assert corrected.start == detected.start
    assert corrected.end == detected.end
    assert corrected.suffix == expected_suffix
    assert corrected.score == detected.score
    assert corrected.action is Action.CANDIDATE


@pytest.mark.parametrize(("raw", "expected_text", "expected_suffix"), _m3_email_suffix_cases())
def test_m3_boundary_captures_email_suffix_without_changing_detector_role(
    raw: str,
    expected_text: str,
    expected_suffix: str,
) -> None:
    preprocessed = preprocess_text(raw)
    [detected] = EmailRegexDetector().detect(preprocessed, GuardrailRequest(text=raw))
    corrected = KoreanBoundaryCorrector().correct(detected, preprocessed)

    corrected.validate_against(raw)
    assert detected.suffix is None
    assert corrected.text == expected_text
    assert corrected.start == detected.start
    assert corrected.end == detected.end
    assert corrected.suffix == expected_suffix
    assert corrected.score == detected.score
    assert corrected.action is Action.CANDIDATE


@pytest.mark.parametrize(("raw", "value", "expected_text", "expected_suffix"), _m3_person_trim_cases())
def test_m3_boundary_trims_person_suffix_without_scoring_or_policy(
    raw: str,
    value: str,
    expected_text: str,
    expected_suffix: str,
) -> None:
    start = raw.index(value)
    original = PIISpan(
        start=start,
        end=start + len(value),
        text=value,
        entity_type=EntityType.PERSON_NAME,
        score=0.73,
        sources=("ner",),
        risk_level=RiskLevel.P1,
        action=Action.CANDIDATE,
        reason_codes=("ner.mock",),
        detector_ids=("ner.mock",),
    )
    corrected = KoreanBoundaryCorrector().correct(original, preprocess_text(raw))

    corrected.validate_against(raw)
    assert corrected.text == expected_text
    assert corrected.suffix == expected_suffix
    assert corrected.score == original.score
    assert corrected.action is original.action
    assert corrected.risk_level is original.risk_level
    assert "boundary.suffix_trim" in corrected.reason_codes
