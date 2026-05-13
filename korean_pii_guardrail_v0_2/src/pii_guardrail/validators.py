"""Deterministic validators for structured Korean PII candidates."""

from __future__ import annotations

import ipaddress
import math
import re
import unicodedata
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class ValidationResult:
    is_valid: bool
    normalized: str
    score_key: str | None = None
    reason_codes: tuple[str, ...] = ()


MOBILE_PREFIXES = {"010", "011", "016", "017", "018", "019"}
LANDLINE_PREFIXES = {
    "02",
    "031",
    "032",
    "033",
    "041",
    "042",
    "043",
    "044",
    "051",
    "052",
    "053",
    "054",
    "055",
    "061",
    "062",
    "063",
    "064",
}
SERVICE_PHONE_PREFIXES = ("050", "070", "080", "15", "16", "18")
BUSINESS_REG_WEIGHTS = (1, 3, 7, 1, 3, 7, 1, 3, 5)
RRN_CHECKSUM_WEIGHTS = (2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4, 5)
SECRET_PREFIXES = ("sk-", "ghp_", "gho_", "xoxb-", "xoxp-", "AKIA")


@dataclass(frozen=True)
class BankAccountPattern:
    pattern_id: str
    segments: tuple[int, ...]
    prefixes: tuple[str, ...] = ()


@dataclass(frozen=True)
class BankAccountProfile:
    bank: str
    bank_code: str
    aliases: tuple[str, ...]
    patterns: tuple[BankAccountPattern, ...]


BANK_ACCOUNT_PROFILES = (
    BankAccountProfile(
        bank="국민은행",
        bank_code="004",
        aliases=("국민", "KB", "KB국민은행"),
        patterns=(
            BankAccountPattern("kb_6_2_6", (6, 2, 6)),
            BankAccountPattern("kb_3_2_4_3", (3, 2, 4, 3)),
        ),
    ),
    BankAccountProfile(
        bank="신한은행",
        bank_code="088",
        aliases=("신한", "SHINHAN"),
        patterns=(BankAccountPattern("shinhan_3_3_6", (3, 3, 6)),),
    ),
    BankAccountProfile(
        bank="우리은행",
        bank_code="020",
        aliases=("우리", "WOORI"),
        patterns=(
            BankAccountPattern("woori_3_6_2_3", (3, 6, 2, 3)),
            BankAccountPattern("woori_4_3_6", (4, 3, 6)),
        ),
    ),
    BankAccountProfile(
        bank="하나은행",
        bank_code="081",
        aliases=("하나", "KEB하나", "HANA"),
        patterns=(
            BankAccountPattern("hana_3_6_5", (3, 6, 5)),
            BankAccountPattern("hana_3_2_5_1", (3, 2, 5, 1)),
        ),
    ),
    BankAccountProfile(
        bank="농협은행",
        bank_code="011",
        aliases=("농협", "NH", "NH농협은행"),
        patterns=(
            BankAccountPattern("nh_3_2_6", (3, 2, 6)),
            BankAccountPattern("nh_3_4_4_2", (3, 4, 4, 2)),
        ),
    ),
    BankAccountProfile(
        bank="기업은행",
        bank_code="003",
        aliases=("기업", "IBK", "IBK기업은행"),
        patterns=(BankAccountPattern("ibk_3_6_2_3", (3, 6, 2, 3)),),
    ),
    BankAccountProfile(
        bank="카카오뱅크",
        bank_code="090",
        aliases=("카뱅", "카카오", "KAKAO"),
        patterns=(BankAccountPattern("kakao_4_2_7", (4, 2, 7), ("3333", "7979", "7942", "7777")),),
    ),
    BankAccountProfile(
        bank="토스뱅크",
        bank_code="092",
        aliases=("토스", "TOSS"),
        patterns=(BankAccountPattern("toss_4_4_4", (4, 4, 4), ("1000", "1001")),),
    ),
    BankAccountProfile(
        bank="케이뱅크",
        bank_code="089",
        aliases=("케이", "KBANK", "K뱅크"),
        patterns=(
            BankAccountPattern("kbank_3_3_6", (3, 3, 6)),
            BankAccountPattern("kbank_4_4_4", (4, 4, 4), ("1001", "1020")),
        ),
    ),
)


def digits_only(value: str) -> str:
    digits: list[str] = []
    for char in value:
        try:
            digits.append(str(unicodedata.digit(char)))
        except (TypeError, ValueError):
            continue
    return "".join(digits)


def is_repeated_or_placeholder_digits(digits: str) -> bool:
    return not digits or len(set(digits)) == 1 or digits in {"1234567890", "0123456789"}


def validate_rrn(value: str) -> ValidationResult:
    digits = digits_only(value)
    if len(digits) != 13 or not _valid_birth_date(digits[:6], digits[6], rrn=True):
        return ValidationResult(False, digits, reason_codes=("validator.rrn.invalid",))
    if not rrn_checksum_valid(digits):
        return ValidationResult(False, digits, reason_codes=("validator.rrn.checksum_invalid",))
    return ValidationResult(True, digits, "RRN", ("validator.rrn.valid", "validator.rrn.checksum_valid"))


def validate_frn(value: str) -> ValidationResult:
    digits = digits_only(value)
    if len(digits) != 13 or not _valid_birth_date(digits[:6], digits[6], rrn=False):
        return ValidationResult(False, digits, reason_codes=("validator.frn.invalid",))
    if not rrn_checksum_valid(digits):
        return ValidationResult(False, digits, reason_codes=("validator.frn.checksum_invalid",))
    return ValidationResult(True, digits, "FRN", ("validator.frn.valid", "validator.frn.checksum_valid"))


def rrn_check_digit(digits_12: str) -> str:
    if len(digits_12) != 12 or not digits_12.isdigit():
        raise ValueError("RRN checksum input must be the first 12 digits")
    weighted_sum = sum(int(digit) * weight for digit, weight in zip(digits_12, RRN_CHECKSUM_WEIGHTS, strict=True))
    return str((11 - (weighted_sum % 11)) % 10)


def rrn_checksum_valid(digits: str) -> bool:
    return len(digits) == 13 and digits.isdigit() and rrn_check_digit(digits[:12]) == digits[12]


def _valid_birth_date(yymmdd: str, gender_digit: str, *, rrn: bool) -> bool:
    if not yymmdd.isdigit() or not gender_digit.isdigit():
        return False

    if rrn:
        century_by_gender = {"9": 1800, "0": 1800, "1": 1900, "2": 1900, "3": 2000, "4": 2000}
    else:
        century_by_gender = {"5": 1900, "6": 1900, "7": 2000, "8": 2000}
    century = century_by_gender.get(gender_digit)
    if century is None:
        return False

    year = century + int(yymmdd[:2])
    month = int(yymmdd[2:4])
    day = int(yymmdd[4:6])
    try:
        date(year, month, day)
    except ValueError:
        return False
    return True


def validate_phone(value: str) -> ValidationResult:
    digits = digits_only(value)
    if _is_mobile_phone(digits):
        return ValidationResult(True, digits, "PHONE_MOBILE", ("validator.phone.mobile",))
    if _is_landline_phone(digits):
        return ValidationResult(True, digits, "PHONE_LANDLINE", ("validator.phone.landline",))
    return ValidationResult(False, digits, reason_codes=("validator.phone.invalid",))


def _is_mobile_phone(digits: str) -> bool:
    if len(digits) not in {10, 11}:
        return False
    if digits.startswith("010"):
        return len(digits) == 11
    return digits[:3] in MOBILE_PREFIXES


def _is_landline_phone(digits: str) -> bool:
    if digits.startswith(SERVICE_PHONE_PREFIXES):
        return False
    if digits.startswith("02"):
        return len(digits) in {9, 10}
    return len(digits) in {10, 11} and digits[:3] in LANDLINE_PREFIXES


def validate_email(value: str) -> ValidationResult:
    if len(value) > 254 or not re.fullmatch(r"[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+", value):
        return ValidationResult(False, value.lower(), reason_codes=("validator.email.invalid",))

    local, domain = value.rsplit("@", 1)
    labels = domain.split(".")
    if not local or len(local) > 64 or len(labels) < 2:
        return ValidationResult(False, value.lower(), reason_codes=("validator.email.invalid",))
    if not all(_valid_domain_label(label) for label in labels):
        return ValidationResult(False, value.lower(), reason_codes=("validator.email.invalid",))
    if len(labels[-1]) < 2 or not labels[-1].isalpha():
        return ValidationResult(False, value.lower(), reason_codes=("validator.email.invalid",))

    return ValidationResult(True, value.lower(), "EMAIL", ("validator.email.valid",))


def _valid_domain_label(label: str) -> bool:
    return bool(label) and len(label) <= 63 and not label.startswith("-") and not label.endswith("-")


def validate_credit_card(value: str) -> ValidationResult:
    digits = digits_only(value)
    if len(digits) < 13 or len(digits) > 19 or is_repeated_or_placeholder_digits(digits):
        return ValidationResult(False, digits, "CREDIT_CARD_PATTERN_ONLY", ("validator.credit_card.invalid",))
    if not luhn_checksum_valid(digits):
        return ValidationResult(False, digits, "CREDIT_CARD_PATTERN_ONLY", ("validator.credit_card.luhn_failed",))
    return ValidationResult(True, digits, "CREDIT_CARD_VALID", ("validator.credit_card.luhn_valid",))


def luhn_checksum_valid(digits: str) -> bool:
    if not digits.isdigit():
        return False
    total = 0
    parity = len(digits) % 2
    for index, char in enumerate(digits):
        number = int(char)
        if index % 2 == parity:
            number *= 2
            if number > 9:
                number -= 9
        total += number
    return total % 10 == 0


def validate_business_reg_no(value: str) -> ValidationResult:
    if "-" in value and not re.fullmatch(r"\d{3}-\d{2}-\d{5}", value):
        return ValidationResult(False, digits_only(value), reason_codes=("validator.business_reg_no.invalid_format",))

    digits = digits_only(value)
    if len(digits) != 10 or is_repeated_or_placeholder_digits(digits):
        return ValidationResult(False, digits, reason_codes=("validator.business_reg_no.invalid_format",))
    if business_reg_no_checksum_valid(digits):
        return ValidationResult(
            True,
            digits,
            "BUSINESS_REG_NO_VALID",
            ("validator.business_reg_no.checksum_valid",),
        )
    return ValidationResult(
        True,
        digits,
        "BUSINESS_REG_NO_PATTERN_ONLY",
        ("validator.business_reg_no.pattern_only",),
    )


def business_reg_no_checksum_valid(digits: str) -> bool:
    if len(digits) != 10 or not digits.isdigit():
        return False
    weighted_sum = sum(int(digit) * weight for digit, weight in zip(digits[:8], BUSINESS_REG_WEIGHTS[:8], strict=True))
    ninth_product = int(digits[8]) * BUSINESS_REG_WEIGHTS[8]
    weighted_sum += ninth_product // 10 + ninth_product % 10
    check_digit = (10 - (weighted_sum % 10)) % 10
    return check_digit == int(digits[9])


def validate_bank_account_profile(
    value: str,
    *,
    bank: str | None = None,
    bank_code: str | None = None,
) -> ValidationResult:
    digits = digits_only(value)
    if len(digits) < 9 or len(digits) > 16 or is_repeated_or_placeholder_digits(digits):
        return ValidationResult(False, digits, reason_codes=("validator.bank_account.invalid_format",))

    profiles = _candidate_bank_profiles(bank)
    for profile in profiles:
        if bank_code and bank_code != profile.bank_code:
            continue
        for pattern in profile.patterns:
            if _match_bank_account_pattern(value, pattern):
                return ValidationResult(
                    True,
                    digits,
                    "BANK_ACCOUNT_PATTERN_ONLY",
                    (f"validator.bank_account.profile.{pattern.pattern_id}",),
                )

    return ValidationResult(False, digits, reason_codes=("validator.bank_account.profile_mismatch",))


def _candidate_bank_profiles(bank: str | None) -> tuple[BankAccountProfile, ...]:
    if bank is None or not bank.strip():
        return BANK_ACCOUNT_PROFILES
    normalized_bank = bank.strip()
    return tuple(
        profile
        for profile in BANK_ACCOUNT_PROFILES
        if normalized_bank == profile.bank or normalized_bank in profile.aliases
    )


def _match_bank_account_pattern(value: str, pattern: BankAccountPattern) -> bool:
    stripped = value.strip().replace(" ", "")
    if "-" in stripped:
        parts = stripped.split("-")
        if len(parts) != len(pattern.segments):
            return False
        if any(not part.isdigit() for part in parts):
            return False
        if any(len(part) != pattern.segments[index] for index, part in enumerate(parts)):
            return False
        return not pattern.prefixes or any(parts[0].startswith(prefix) for prefix in pattern.prefixes)

    digits = digits_only(stripped)
    if digits != stripped or len(digits) != sum(pattern.segments):
        return False
    return not pattern.prefixes or any(digits.startswith(prefix) for prefix in pattern.prefixes)


def validate_ip_address(value: str) -> ValidationResult:
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return ValidationResult(False, value, reason_codes=("validator.ip.invalid",))

    if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast:
        return ValidationResult(True, str(ip), "IP_ADDRESS_PRIVATE", ("validator.ip.private",))
    return ValidationResult(True, str(ip), "IP_ADDRESS_PUBLIC", ("validator.ip.public",))


def validate_mac_address(value: str) -> ValidationResult:
    if not re.fullmatch(r"[0-9A-Fa-f]{2}([:-])[0-9A-Fa-f]{2}(?:\1[0-9A-Fa-f]{2}){4}", value):
        return ValidationResult(False, value.lower(), reason_codes=("validator.mac.invalid",))
    normalized = value.replace("-", ":").lower()
    return ValidationResult(True, normalized, "MAC_ADDRESS", ("validator.mac.valid",))


def validate_api_secret(value: str) -> ValidationResult:
    if not value.startswith(SECRET_PREFIXES) or len(value) < 20:
        return ValidationResult(False, value[:4], reason_codes=("validator.secret.invalid",))
    tail = value[4:] if value.startswith("AKIA") else value.split("-", 1)[-1].split("_", 1)[-1]
    if not re.fullmatch(r"[A-Za-z0-9_=-]+", tail):
        return ValidationResult(False, value[:4], reason_codes=("validator.secret.invalid",))
    if _character_class_count(tail) < 2 or shannon_entropy(tail) < 3.0:
        return ValidationResult(False, value[:4], reason_codes=("validator.secret.low_entropy",))
    return ValidationResult(True, value[:4], "API_KEY_SECRET", ("validator.secret.valid",))


def _character_class_count(value: str) -> int:
    checks = (
        any(char.islower() for char in value),
        any(char.isupper() for char in value),
        any(char.isdigit() for char in value),
        any(char in "_=-" for char in value),
    )
    return sum(checks)


def shannon_entropy(value: str) -> float:
    if not value:
        return 0.0
    entropy = 0.0
    for char in set(value):
        probability = value.count(char) / len(value)
        entropy -= probability * math.log2(probability)
    return entropy
