from pii_guardrail.validators import (
    business_reg_no_checksum_valid,
    luhn_checksum_valid,
    validate_api_secret,
    validate_business_reg_no,
    validate_credit_card,
    validate_email,
    validate_frn,
    validate_ip_address,
    validate_mac_address,
    validate_phone,
    validate_rrn,
)


def test_rrn_validator_accepts_valid_birth_date_gender_and_length() -> None:
    result = validate_rrn("900101-1234567")

    assert result.is_valid
    assert result.normalized == "9001011234567"
    assert result.score_key == "RRN"


def test_rrn_validator_normalizes_unicode_digits() -> None:
    result = validate_rrn("９００１０１－１２３４５６７")

    assert result.is_valid
    assert result.normalized == "9001011234567"


def test_rrn_validator_rejects_invalid_date_gender_and_length() -> None:
    assert not validate_rrn("991332-1234567").is_valid
    assert not validate_rrn("900101-5234567").is_valid
    assert not validate_rrn("900101-123456").is_valid


def test_frn_validator_accepts_foreigner_gender_digits() -> None:
    result = validate_frn("900101-5123456")

    assert result.is_valid
    assert result.normalized == "9001015123456"
    assert result.score_key == "FRN"


def test_frn_validator_rejects_rrn_gender_digits() -> None:
    assert not validate_frn("900101-1234567").is_valid


def test_phone_validator_classifies_mobile_and_landline() -> None:
    mobile = validate_phone("010-1234-5678")
    landline = validate_phone("02-123-4567")

    assert mobile.is_valid
    assert mobile.score_key == "PHONE_MOBILE"
    assert landline.is_valid
    assert landline.score_key == "PHONE_LANDLINE"


def test_phone_validator_rejects_service_like_or_invalid_numbers() -> None:
    assert not validate_phone("1588-1234").is_valid
    assert not validate_phone("010-123-456").is_valid
    assert not validate_phone("050-1234-5678").is_valid


def test_email_validator_accepts_domain_shape() -> None:
    result = validate_email("test.user+case@example.co.kr")

    assert result.is_valid
    assert result.normalized == "test.user+case@example.co.kr"
    assert result.score_key == "EMAIL"


def test_email_validator_rejects_invalid_domains() -> None:
    assert not validate_email("test@example").is_valid
    assert not validate_email("test@-example.com").is_valid
    assert not validate_email("test@example.c").is_valid


def test_luhn_checksum_validator() -> None:
    assert luhn_checksum_valid("4111111111111111")
    assert not luhn_checksum_valid("4111111111111112")


def test_credit_card_validator_accepts_luhn_only() -> None:
    valid = validate_credit_card("4111-1111-1111-1111")
    invalid = validate_credit_card("4111-1111-1111-1112")

    assert valid.is_valid
    assert valid.score_key == "CREDIT_CARD_VALID"
    assert not invalid.is_valid
    assert invalid.score_key == "CREDIT_CARD_PATTERN_ONLY"


def test_business_reg_no_checksum_helper() -> None:
    assert business_reg_no_checksum_valid("1234567891")
    assert not business_reg_no_checksum_valid("1234567890")


def test_business_reg_no_validator_distinguishes_valid_and_pattern_only() -> None:
    valid = validate_business_reg_no("123-45-67891")
    pattern_only = validate_business_reg_no("123-45-67892")

    assert valid.is_valid
    assert valid.score_key == "BUSINESS_REG_NO_VALID"
    assert pattern_only.is_valid
    assert pattern_only.score_key == "BUSINESS_REG_NO_PATTERN_ONLY"


def test_business_reg_no_validator_rejects_bad_shape_and_placeholders() -> None:
    assert not validate_business_reg_no("12-345-67890").is_valid
    assert not validate_business_reg_no("000-00-00000").is_valid
    assert not validate_business_reg_no("123456789").is_valid


def test_ip_validator_classifies_public_and_private_addresses() -> None:
    public = validate_ip_address("8.8.8.8")
    private = validate_ip_address("192.168.0.1")
    ipv6 = validate_ip_address("2001:4860:4860::8888")

    assert public.is_valid
    assert public.score_key == "IP_ADDRESS_PUBLIC"
    assert private.is_valid
    assert private.score_key == "IP_ADDRESS_PRIVATE"
    assert ipv6.is_valid
    assert ipv6.score_key == "IP_ADDRESS_PUBLIC"


def test_ip_validator_rejects_invalid_address() -> None:
    assert not validate_ip_address("999.999.999.999").is_valid


def test_mac_validator_accepts_colon_and_hyphen_forms() -> None:
    colon = validate_mac_address("AA:BB:CC:DD:EE:FF")
    hyphen = validate_mac_address("aa-bb-cc-dd-ee-ff")

    assert colon.is_valid
    assert colon.normalized == "aa:bb:cc:dd:ee:ff"
    assert hyphen.is_valid
    assert hyphen.normalized == "aa:bb:cc:dd:ee:ff"


def test_mac_validator_rejects_invalid_form() -> None:
    assert not validate_mac_address("AA:BB:CC:DD:EE").is_valid
    assert not validate_mac_address("GG:BB:CC:DD:EE:FF").is_valid


def test_api_secret_validator_uses_prefix_length_mix_and_entropy() -> None:
    valid = validate_api_secret("sk-AbC123xYz987TokenValue")
    low_entropy = validate_api_secret("sk-aaaaaaaaaaaaaaaaaaaa")
    no_prefix = validate_api_secret("token-AbC123xYz987TokenValue")

    assert valid.is_valid
    assert valid.score_key == "API_KEY_SECRET"
    assert not low_entropy.is_valid
    assert not no_prefix.is_valid
