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
SECRET_PREFIXES = ("sk-", "ghp_", "gho_", "xoxb-", "xoxp-", "AKIA")


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
    return ValidationResult(True, digits, "RRN", ("validator.rrn.valid",))


def validate_frn(value: str) -> ValidationResult:
    digits = digits_only(value)
    if len(digits) != 13 or not _valid_birth_date(digits[:6], digits[6], rrn=False):
        return ValidationResult(False, digits, reason_codes=("validator.frn.invalid",))
    return ValidationResult(True, digits, "FRN", ("validator.frn.valid",))


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
