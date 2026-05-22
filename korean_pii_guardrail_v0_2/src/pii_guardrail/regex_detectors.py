"""Regex-based structured PII candidate detectors."""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from .dictionary_loader import load_structured_context_terms
from .enums import Action, EntityType, RiskLevel, Source
from .interfaces import PreprocessResult, TextVariant
from .preprocess import NormalizationMapError, restore_variant_span
from .schema import GuardrailRequest, PIISpan
from .validators import (
    validate_api_secret,
    validate_bank_account_profile,
    validate_business_reg_no,
    validate_credit_card,
    validate_email,
    validate_frn,
    validate_ip_address,
    validate_mac_address,
    validate_phone,
    validate_rrn,
)


DEFAULT_CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs"


@dataclass(frozen=True)
class RestoredMatch:
    start: int
    end: int
    text: str
    target_name: str
    matched_text: str


@dataclass(frozen=True)
class CandidateSpec:
    entity_type: EntityType
    score_key: str
    reason_codes: tuple[str, ...]
    detector_id: str
    sources: tuple[str, ...]


class BaseRegexDetector:
    detector_id = "regex.base"
    source = Source.REGEX.value

    def __init__(
        self,
        *,
        scores: Mapping[str, float] | None = None,
        risk_levels: Mapping[EntityType, RiskLevel] | None = None,
        structured_context_terms: Mapping[str, tuple[str, ...]] | None = None,
    ) -> None:
        self.scores = dict(scores) if scores is not None else load_regex_base_scores()
        self.risk_levels = dict(risk_levels) if risk_levels is not None else load_entity_risk_levels()
        self.structured_context_terms = (
            dict(structured_context_terms)
            if structured_context_terms is not None
            else load_structured_context_terms()
        )

    def detect(self, preprocessed: PreprocessResult, request: GuardrailRequest) -> list[PIISpan]:
        del request
        spans = list(self._detect(preprocessed))
        return deduplicate_spans(spans)

    def _detect(self, preprocessed: PreprocessResult) -> Iterable[PIISpan]:
        raise NotImplementedError

    def _make_span(self, raw_text: str, match: RestoredMatch, spec: CandidateSpec) -> PIISpan:
        score = self.scores[spec.score_key]
        span = PIISpan(
            start=match.start,
            end=match.end,
            text=match.text,
            entity_type=spec.entity_type,
            score=score,
            sources=spec.sources,
            risk_level=self.risk_levels[spec.entity_type],
            action=Action.CANDIDATE,
            reason_codes=spec.reason_codes,
            detector_ids=(spec.detector_id,),
        )
        span.validate_against(raw_text)
        return span


class RRNRegexDetector(BaseRegexDetector):
    detector_id = "regex.rrn"
    _pattern = re.compile(r"(?<!\d)\d{6}\s*-?\s*\d{7}(?!\d)")

    def _detect(self, preprocessed: PreprocessResult) -> Iterable[PIISpan]:
        for match in iter_restored_matches(preprocessed, self._pattern):
            is_corporate_context = _is_corporate_reg_no_context(
                preprocessed.raw_text,
                match.start,
                self.structured_context_terms,
            )
            is_personal_context = _is_personal_reg_no_context(
                preprocessed.raw_text,
                match.start,
                self.structured_context_terms,
            )
            if is_corporate_context and not is_personal_context:
                continue
            validation = validate_rrn(match.matched_text)
            if not validation.is_valid:
                continue
            yield self._make_span(
                preprocessed.raw_text,
                match,
                CandidateSpec(
                    EntityType.RRN,
                    validation.score_key or "RRN",
                    ("regex.rrn", *validation.reason_codes),
                    self.detector_id,
                    (Source.REGEX.value, Source.VALIDATOR.value),
                ),
            )


class FRNRegexDetector(BaseRegexDetector):
    detector_id = "regex.frn"
    _pattern = re.compile(r"(?<!\d)\d{6}\s*-?\s*\d{7}(?!\d)")

    def _detect(self, preprocessed: PreprocessResult) -> Iterable[PIISpan]:
        for match in iter_restored_matches(preprocessed, self._pattern):
            is_corporate_context = _is_corporate_reg_no_context(
                preprocessed.raw_text,
                match.start,
                self.structured_context_terms,
            )
            is_personal_context = _is_personal_reg_no_context(
                preprocessed.raw_text,
                match.start,
                self.structured_context_terms,
            )
            if is_corporate_context and not is_personal_context:
                continue
            validation = validate_frn(match.matched_text)
            if not validation.is_valid:
                continue
            yield self._make_span(
                preprocessed.raw_text,
                match,
                CandidateSpec(
                    EntityType.FRN,
                    validation.score_key or "FRN",
                    ("regex.frn", *validation.reason_codes),
                    self.detector_id,
                    (Source.REGEX.value, Source.VALIDATOR.value),
                ),
            )


class PhoneRegexDetector(BaseRegexDetector):
    detector_id = "regex.phone"
    _pattern = re.compile(r"(?<!\d)0\d{1,2}[\s-]?\d{3,4}[\s-]?\d{4}(?!\d)")

    def _detect(self, preprocessed: PreprocessResult) -> Iterable[PIISpan]:
        for match in iter_restored_matches(preprocessed, self._pattern):
            if _is_order_id_context(
                preprocessed.raw_text,
                match.start,
                self.structured_context_terms,
            ):
                continue
            validation = validate_phone(match.matched_text)
            if not validation.is_valid or validation.score_key is None:
                continue
            entity_type = EntityType(validation.score_key)
            yield self._make_span(
                preprocessed.raw_text,
                match,
                CandidateSpec(
                    entity_type,
                    validation.score_key,
                    ("regex.phone", *validation.reason_codes),
                    self.detector_id,
                    (Source.REGEX.value, Source.VALIDATOR.value),
                ),
            )


class EmailRegexDetector(BaseRegexDetector):
    detector_id = "regex.email"
    _pattern = re.compile(r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")

    def _detect(self, preprocessed: PreprocessResult) -> Iterable[PIISpan]:
        for match in iter_restored_matches(preprocessed, self._pattern):
            validation = validate_email(match.matched_text)
            if not validation.is_valid:
                continue
            yield self._make_span(
                preprocessed.raw_text,
                match,
                CandidateSpec(
                    EntityType.EMAIL,
                    validation.score_key or "EMAIL",
                    ("regex.email", *validation.reason_codes),
                    self.detector_id,
                    (Source.REGEX.value, Source.VALIDATOR.value),
                ),
            )


class NetworkIdentifierDetector(BaseRegexDetector):
    detector_id = "regex.network"
    _ipv4_pattern = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?!\d)(?!\.\d)")
    _ipv6_pattern = re.compile(r"(?<![A-Fa-f0-9:])(?:[A-Fa-f0-9]{0,4}:){2,}[A-Fa-f0-9:]{0,4}(?![A-Fa-f0-9:])")
    _mac_pattern = re.compile(r"(?<![0-9A-Fa-f])(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}(?![0-9A-Fa-f])")

    def _detect(self, preprocessed: PreprocessResult) -> Iterable[PIISpan]:
        for pattern in (self._ipv4_pattern, self._ipv6_pattern):
            for match in iter_restored_matches(preprocessed, pattern):
                validation = validate_ip_address(match.matched_text)
                if not validation.is_valid or validation.score_key is None:
                    continue
                yield self._make_span(
                    preprocessed.raw_text,
                    match,
                    CandidateSpec(
                        EntityType.IP_ADDRESS,
                        validation.score_key,
                        ("regex.ip", *validation.reason_codes),
                        self.detector_id,
                        (Source.REGEX.value, Source.VALIDATOR.value),
                    ),
                )

        for match in iter_restored_matches(preprocessed, self._mac_pattern):
            validation = validate_mac_address(match.matched_text)
            if not validation.is_valid or validation.score_key is None:
                continue
            yield self._make_span(
                preprocessed.raw_text,
                match,
                CandidateSpec(
                    EntityType.MAC_ADDRESS,
                    validation.score_key,
                    ("regex.mac", *validation.reason_codes),
                    self.detector_id,
                    (Source.REGEX.value, Source.VALIDATOR.value),
                ),
            )


class CreditCardRegexDetector(BaseRegexDetector):
    detector_id = "regex.credit_card"
    _pattern = re.compile(r"(?<!\d)(?:\d[\s-]?){13,19}(?!\d)")

    def _detect(self, preprocessed: PreprocessResult) -> Iterable[PIISpan]:
        for match in iter_restored_matches(preprocessed, self._pattern):
            if _is_non_card_structured_context(
                preprocessed.raw_text,
                match.start,
                self.structured_context_terms,
            ):
                continue
            validation = validate_credit_card(match.matched_text)
            if not validation.is_valid or validation.score_key != "CREDIT_CARD_VALID":
                continue
            yield self._make_span(
                preprocessed.raw_text,
                match,
                CandidateSpec(
                    EntityType.CREDIT_CARD,
                    validation.score_key,
                    ("regex.credit_card", *validation.reason_codes),
                    self.detector_id,
                    (Source.REGEX.value, Source.VALIDATOR.value),
                ),
            )


class BusinessRegNoDetector(BaseRegexDetector):
    detector_id = "regex.business_reg_no"
    _pattern = re.compile(r"(?<!\d)\d{3}-?\d{2}-?\d{5}(?!\d)")

    def _detect(self, preprocessed: PreprocessResult) -> Iterable[PIISpan]:
        for match in iter_restored_matches(preprocessed, self._pattern):
            if _is_order_id_context(
                preprocessed.raw_text,
                match.start,
                self.structured_context_terms,
            ):
                continue
            if _is_account_context(
                preprocessed.raw_text,
                match.start,
                self.structured_context_terms,
            ) and not _is_business_reg_no_context(
                preprocessed.raw_text,
                match.start,
                self.structured_context_terms,
            ):
                continue
            if _is_medical_record_no_context(
                preprocessed.raw_text,
                match.start,
                self.structured_context_terms,
            ):
                continue
            if validate_phone(match.matched_text).is_valid:
                continue
            validation = validate_business_reg_no(match.matched_text)
            if not validation.is_valid or validation.score_key is None:
                continue
            yield self._make_span(
                preprocessed.raw_text,
                match,
                CandidateSpec(
                    EntityType.BUSINESS_REG_NO,
                    validation.score_key,
                    ("regex.business_reg_no", *validation.reason_codes),
                    self.detector_id,
                    (Source.REGEX.value, Source.VALIDATOR.value),
                ),
            )


class PassportRegexDetector(BaseRegexDetector):
    detector_id = "regex.passport"
    _pattern = re.compile(r"(?<![A-Z0-9])[A-Z]\d{8}(?![A-Z0-9])", re.IGNORECASE)

    def _detect(self, preprocessed: PreprocessResult) -> Iterable[PIISpan]:
        for match in iter_restored_matches(preprocessed, self._pattern):
            yield self._make_span(
                preprocessed.raw_text,
                match,
                CandidateSpec(
                    EntityType.PASSPORT,
                    "PASSPORT",
                    ("regex.passport", "regex.passport.pattern"),
                    self.detector_id,
                    (Source.REGEX.value,),
                ),
            )


class DriverLicenseRegexDetector(BaseRegexDetector):
    detector_id = "regex.driver_license"
    _pattern = re.compile(r"(?<!\d)\d{2}-\d{2}-\d{6}-\d{2}(?!\d)")

    def _detect(self, preprocessed: PreprocessResult) -> Iterable[PIISpan]:
        for match in iter_restored_matches(preprocessed, self._pattern):
            yield self._make_span(
                preprocessed.raw_text,
                match,
                CandidateSpec(
                    EntityType.DRIVER_LICENSE,
                    "DRIVER_LICENSE",
                    ("regex.driver_license", "regex.driver_license.pattern"),
                    self.detector_id,
                    (Source.REGEX.value,),
                ),
            )


class CorporateRegNoRegexDetector(BaseRegexDetector):
    detector_id = "regex.corporate_reg_no"
    _pattern = re.compile(r"(?<!\d)(?:110111|110114|110115|110121|134511)-?\d{7}(?!\d)")

    def _detect(self, preprocessed: PreprocessResult) -> Iterable[PIISpan]:
        for match in iter_restored_matches(preprocessed, self._pattern):
            yield self._make_span(
                preprocessed.raw_text,
                match,
                CandidateSpec(
                    EntityType.CORPORATE_REG_NO,
                    "CORPORATE_REG_NO",
                    ("regex.corporate_reg_no", "regex.corporate_reg_no.pattern"),
                    self.detector_id,
                    (Source.REGEX.value,),
                ),
            )


_LABEL_SEPARATOR = r"\s*[:#-]?\s*"
_CUSTOMER_LABELS = (
    "(?:\uace0\uac1d\ubc88\ud638|\ud68c\uc6d0\ubc88\ud638|"
    "\uace0\uac1dID|\ud68c\uc6d0ID|customer\\s*(?:id|no|number))"
)
_EMPLOYEE_LABELS = "(?:\uc0ac\ubc88|\uc9c1\uc6d0\ubc88\ud638|employee\\s*(?:id|no|number))"
_STUDENT_LABELS = "(?:\ud559\ubc88|student\\s*(?:id|no|number))"
_MEDICAL_LABELS = (
    "(?:\ud658\uc790\ubc88\ud638|\ucc28\ud2b8\ubc88\ud638|"
    "\uc9c4\ub8cc\uae30\ub85d\ubc88\ud638|\uc758\ubb34\uae30\ub85d\ubc88\ud638|"
    "medical\\s*(?:record|id|no|number)|MRN)"
)
_DOB_LABELS = "(?:\uc0dd\ub144\uc6d4\uc77c|DOB|date\\s*of\\s*birth)"
_DEVICE_LABELS = "(?:device(?:\\s*(?:id|no|number))?|\uae30\uae30ID|\uc7a5\uce58ID|\ub2e8\ub9d0ID)"
_VEHICLE_LABELS = (
    "(?:vehicle(?:\\s*(?:registration|reg|id|no|number))?|"
    "\ucc28\ub7c9\ubc88\ud638|\ucc28\ub7c9\ub4f1\ub85d\ubc88\ud638)"
)
_HANGUL_SYLLABLE_CLASS = f"{chr(0xAC00)}-{chr(0xD7A3)}"


class LabeledIdentifierRegexDetector(BaseRegexDetector):
    detector_id = "regex.labeled_identifier"
    _rules = (
        (
            re.compile(_CUSTOMER_LABELS + _LABEL_SEPARATOR + r"(?P<value>CUST-\d{6})", re.IGNORECASE),
            CandidateSpec(
                EntityType.CUSTOMER_ID,
                "CUSTOMER_ID_WITH_LABEL",
                ("regex.customer_id", "regex.customer_id.with_label"),
                "regex.customer_id",
                (Source.REGEX.value,),
            ),
        ),
        (
            re.compile(_EMPLOYEE_LABELS + _LABEL_SEPARATOR + r"(?P<value>EMP-\d{4}-\d{5})", re.IGNORECASE),
            CandidateSpec(
                EntityType.EMPLOYEE_ID,
                "EMPLOYEE_ID_WITH_LABEL",
                ("regex.employee_id", "regex.employee_id.with_label"),
                "regex.employee_id",
                (Source.REGEX.value,),
            ),
        ),
        (
            re.compile(_STUDENT_LABELS + _LABEL_SEPARATOR + r"(?P<value>STU-\d{8})", re.IGNORECASE),
            CandidateSpec(
                EntityType.STUDENT_ID,
                "STUDENT_ID_WITH_LABEL",
                ("regex.student_id", "regex.student_id.with_label"),
                "regex.student_id",
                (Source.REGEX.value,),
            ),
        ),
        (
            re.compile(_MEDICAL_LABELS + _LABEL_SEPARATOR + r"(?P<value>MR-\d{4}-\d{6})", re.IGNORECASE),
            CandidateSpec(
                EntityType.MEDICAL_RECORD_NO,
                "MEDICAL_RECORD_NO_WITH_LABEL",
                ("regex.medical_record_no", "regex.medical_record_no.with_label"),
                "regex.medical_record_no",
                (Source.REGEX.value,),
            ),
        ),
        (
            re.compile(
                _DOB_LABELS
                + _LABEL_SEPARATOR
                + r"(?P<value>(?:19|20)\d{2}\s*\uB144\s*\d{1,2}\s*\uC6D4\s*\d{1,2}\s*\uC77C|(?:19|20)\d{2}-\d{2}-\d{2})",
                re.IGNORECASE,
            ),
            CandidateSpec(
                EntityType.DOB,
                "DOB_WITH_LABEL",
                ("regex.dob", "regex.dob.with_label"),
                "regex.dob",
                (Source.REGEX.value,),
            ),
        ),
        (
            re.compile(_DEVICE_LABELS + _LABEL_SEPARATOR + r"(?P<value>device-[A-Za-z0-9-]{8,})", re.IGNORECASE),
            CandidateSpec(
                EntityType.DEVICE_ID,
                "DEVICE_ID_WITH_LABEL",
                ("regex.device_id", "regex.device_id.with_label"),
                "regex.device_id",
                (Source.REGEX.value,),
            ),
        ),
        (
            re.compile(
                _VEHICLE_LABELS
                + _LABEL_SEPARATOR
                + rf"(?P<value>\d{{2,3}}[{_HANGUL_SYLLABLE_CLASS}]\d{{4}})",
                re.IGNORECASE,
            ),
            CandidateSpec(
                EntityType.VEHICLE_REG_NO,
                "VEHICLE_REG_NO_WITH_LABEL",
                ("regex.vehicle_reg_no", "regex.vehicle_reg_no.with_label"),
                "regex.vehicle_reg_no",
                (Source.REGEX.value,),
            ),
        ),
    )

    def _detect(self, preprocessed: PreprocessResult) -> Iterable[PIISpan]:
        for pattern, spec in self._rules:
            for match in iter_restored_group_matches(preprocessed, pattern, "value"):
                yield self._make_span(preprocessed.raw_text, match, spec)


class BankAccountCandidateDetector(BaseRegexDetector):
    detector_id = "regex.bank_account"
    _pattern = re.compile(r"(?<!\d)\d{2,6}(?:[- ]\d{1,7}){1,4}(?!\d)")

    def _detect(self, preprocessed: PreprocessResult) -> Iterable[PIISpan]:
        for match in iter_restored_matches(preprocessed, self._pattern):
            if _is_order_id_context(
                preprocessed.raw_text,
                match.start,
                self.structured_context_terms,
            ):
                continue
            if validate_phone(match.matched_text).is_valid:
                continue
            validation = validate_bank_account_profile(match.matched_text)
            if not validation.is_valid or validation.score_key is None:
                continue
            yield self._make_span(
                preprocessed.raw_text,
                match,
                CandidateSpec(
                    EntityType.BANK_ACCOUNT,
                    validation.score_key,
                    ("regex.bank_account.pattern_only", *validation.reason_codes),
                    self.detector_id,
                    (Source.REGEX.value, Source.VALIDATOR.value),
                ),
            )


class SecretRegexDetector(BaseRegexDetector):
    detector_id = "regex.secret"
    _pattern = re.compile(r"(?<![A-Za-z0-9_=-])(?:sk-[A-Za-z0-9_=-]{16,}|gh[po]_[A-Za-z0-9]{16,}|xox[bp]-[A-Za-z0-9-]{16,}|AKIA[0-9A-Z]{16})(?![A-Za-z0-9_=-])")

    def _detect(self, preprocessed: PreprocessResult) -> Iterable[PIISpan]:
        for match in iter_restored_matches(preprocessed, self._pattern):
            validation = validate_api_secret(match.matched_text)
            if not validation.is_valid or validation.score_key is None:
                continue
            yield self._make_span(
                preprocessed.raw_text,
                match,
                CandidateSpec(
                    EntityType.API_KEY_SECRET,
                    validation.score_key,
                    ("regex.secret", *validation.reason_codes),
                    self.detector_id,
                    (Source.REGEX.value, Source.VALIDATOR.value),
                ),
            )


def iter_restored_matches(preprocessed: PreprocessResult, pattern: re.Pattern[str]) -> Iterator[RestoredMatch]:
    raw_text = preprocessed.raw_text
    for match in pattern.finditer(raw_text):
        yield RestoredMatch(match.start(), match.end(), raw_text[match.start() : match.end()], "raw", match.group(0))

    for variant in _scan_variants(preprocessed):
        for match in pattern.finditer(variant.text):
            try:
                start, end = restore_variant_span(variant, match.start(), match.end())
            except NormalizationMapError:
                continue
            if start < 0 or end > len(raw_text) or start >= end:
                continue
            yield RestoredMatch(start, end, raw_text[start:end], variant.name, match.group(0))


def iter_restored_group_matches(
    preprocessed: PreprocessResult,
    pattern: re.Pattern[str],
    group: str,
) -> Iterator[RestoredMatch]:
    raw_text = preprocessed.raw_text
    for match in pattern.finditer(raw_text):
        start, end = match.span(group)
        if start < 0 or end <= start:
            continue
        yield RestoredMatch(start, end, raw_text[start:end], "raw", match.group(group))

    for variant in _scan_variants(preprocessed):
        for match in pattern.finditer(variant.text):
            variant_start, variant_end = match.span(group)
            if variant_start < 0 or variant_end <= variant_start:
                continue
            try:
                start, end = restore_variant_span(variant, variant_start, variant_end)
            except NormalizationMapError:
                continue
            if start < 0 or end > len(raw_text) or start >= end:
                continue
            yield RestoredMatch(start, end, raw_text[start:end], variant.name, match.group(group))


def _scan_variants(preprocessed: PreprocessResult) -> tuple[TextVariant, ...]:
    variants = list(preprocessed.variants)
    if not any(variant.name == "normalized" for variant in variants):
        spans = tuple(None if idx is None else (idx, idx + 1) for idx in preprocessed.norm_to_raw)
        variants.insert(
            0,
            TextVariant(
                name="normalized",
                text=preprocessed.normalized_text,
                variant_to_raw=preprocessed.norm_to_raw,
                variant_to_raw_span=spans,
            ),
        )
    return tuple(variants)


_ORDER_ID_LABEL_GROUP = "order_id_label"
_ACCOUNT_LABEL_GROUP = "account_label"
_BUSINESS_REG_LABEL_GROUP = "business_reg_no_label"
_MEDICAL_RECORD_LABEL_GROUP = "medical_record_no_label"
_CORPORATE_REG_LABEL_GROUP = "corporate_reg_no_label"
_PERSONAL_REG_LABEL_GROUP = "personal_reg_no_label"
_LABEL_TRAILER = r"\s*(?::|#|-|\uc740|\ub294|\uc774|\uac00)?\s*$"


def _is_order_id_context(
    raw_text: str,
    start: int,
    structured_context_terms: Mapping[str, tuple[str, ...]],
) -> bool:
    prefix = raw_text[max(0, start - 32) : start]
    return _matches_immediate_label_context(
        prefix,
        structured_context_terms,
        _ORDER_ID_LABEL_GROUP,
    )


def _is_account_context(
    raw_text: str,
    start: int,
    structured_context_terms: Mapping[str, tuple[str, ...]],
) -> bool:
    segment = _field_segment_before(raw_text, start)
    return _matches_field_segment_label_context(
        segment,
        structured_context_terms,
        _ACCOUNT_LABEL_GROUP,
    )


def _is_business_reg_no_context(
    raw_text: str,
    start: int,
    structured_context_terms: Mapping[str, tuple[str, ...]],
) -> bool:
    prefix = raw_text[max(0, start - 64) : start]
    return _matches_immediate_label_context(
        prefix,
        structured_context_terms,
        _BUSINESS_REG_LABEL_GROUP,
    )


def _is_medical_record_no_context(
    raw_text: str,
    start: int,
    structured_context_terms: Mapping[str, tuple[str, ...]],
) -> bool:
    prefix = raw_text[max(0, start - 64) : start]
    return _matches_immediate_label_context(
        prefix,
        structured_context_terms,
        _MEDICAL_RECORD_LABEL_GROUP,
        suffix=r"\s*(?:MR\s*-\s*)?$",
    )


def _is_non_card_structured_context(
    raw_text: str,
    start: int,
    structured_context_terms: Mapping[str, tuple[str, ...]],
) -> bool:
    return any(
        (
            _is_corporate_reg_no_context(raw_text, start, structured_context_terms),
            _is_business_reg_no_context(raw_text, start, structured_context_terms),
            _is_account_context(raw_text, start, structured_context_terms),
            _is_order_id_context(raw_text, start, structured_context_terms),
        )
    )


def _is_corporate_reg_no_context(
    raw_text: str,
    start: int,
    structured_context_terms: Mapping[str, tuple[str, ...]],
) -> bool:
    prefix = raw_text[max(0, start - 64) : start]
    return _matches_immediate_label_context(
        prefix,
        structured_context_terms,
        _CORPORATE_REG_LABEL_GROUP,
    )


def _is_personal_reg_no_context(
    raw_text: str,
    start: int,
    structured_context_terms: Mapping[str, tuple[str, ...]],
) -> bool:
    prefix = raw_text[max(0, start - 64) : start]
    return _matches_immediate_label_context(
        prefix,
        structured_context_terms,
        _PERSONAL_REG_LABEL_GROUP,
    )


def _matches_immediate_label_context(
    prefix: str,
    structured_context_terms: Mapping[str, tuple[str, ...]],
    group_name: str,
    *,
    suffix: str = _LABEL_TRAILER,
) -> bool:
    terms = structured_context_terms.get(group_name, ())
    pattern = _compile_label_context_pattern(tuple(terms), suffix=suffix)
    return bool(pattern.search(prefix))


def _matches_field_segment_label_context(
    segment: str,
    structured_context_terms: Mapping[str, tuple[str, ...]],
    group_name: str,
) -> bool:
    terms = structured_context_terms.get(group_name, ())
    pattern = _compile_label_context_pattern(tuple(terms), suffix=r"")
    return bool(pattern.search(segment))


def _field_segment_before(raw_text: str, start: int, *, window: int = 64) -> str:
    prefix = raw_text[max(0, start - window) : start]
    last_separator = max(prefix.rfind(separator) for separator in ("\n", "\r", ",", ";", ".", "|"))
    if last_separator == -1:
        return prefix
    return prefix[last_separator + 1 :]


@lru_cache(maxsize=128)
def _compile_label_context_pattern(
    terms: tuple[str, ...],
    *,
    suffix: str,
) -> re.Pattern[str]:
    term_patterns = tuple(
        _label_term_pattern(term)
        for term in sorted((term.strip() for term in terms), key=len, reverse=True)
        if term.strip()
    )
    if not term_patterns:
        return re.compile(r"(?!x)x")
    return re.compile(r"(?:" + "|".join(term_patterns) + r")" + suffix, re.IGNORECASE)


def _label_term_pattern(term: str) -> str:
    return r"\s*".join(re.escape(part) for part in term.split())


def deduplicate_spans(spans: Iterable[PIISpan]) -> list[PIISpan]:
    merged: dict[tuple[int, int, EntityType], PIISpan] = {}
    for span in spans:
        key = (span.start, span.end, span.entity_type)
        existing = merged.get(key)
        if existing is None:
            merged[key] = span
            continue
        merged[key] = _merge_duplicate_span(existing, span)
    return sorted(merged.values(), key=lambda span: (span.start, span.end, span.entity_type.value))


def _merge_duplicate_span(left: PIISpan, right: PIISpan) -> PIISpan:
    return PIISpan(
        start=left.start,
        end=left.end,
        text=left.text,
        entity_type=left.entity_type,
        score=max(left.score, right.score),
        sources=_ordered_union(left.sources, right.sources),
        risk_level=left.risk_level,
        action=Action.CANDIDATE,
        reason_codes=_ordered_union(left.reason_codes, right.reason_codes),
        detector_ids=_ordered_union(left.detector_ids, right.detector_ids),
        is_composite=left.is_composite or right.is_composite,
        policy_profile=left.policy_profile or right.policy_profile,
        output_target=left.output_target or right.output_target,
    )


def _ordered_union(left: tuple[str, ...], right: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for item in (*left, *right):
        if item not in result:
            result.append(item)
    return tuple(result)


def load_regex_base_scores(path: Path | None = None) -> dict[str, float]:
    config_path = path or DEFAULT_CONFIG_DIR / "scoring.yaml"
    return _load_simple_yaml_mapping(config_path, "regex_base_scores", value_parser=float)


def load_entity_risk_levels(path: Path | None = None) -> dict[EntityType, RiskLevel]:
    config_path = path or DEFAULT_CONFIG_DIR / "entities.yaml"
    raw_levels = _load_entity_risk_level_mapping(config_path)
    return {EntityType(entity): RiskLevel(risk_level) for entity, risk_level in raw_levels.items()}


def _load_simple_yaml_mapping(path: Path, section: str, *, value_parser: type[float]) -> dict[str, float]:
    values: dict[str, float] = {}
    in_section = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" ") and line.rstrip(":") == section:
            in_section = True
            continue
        if in_section and not line.startswith(" "):
            break
        if in_section:
            key, separator, value = line.strip().partition(":")
            if not separator:
                continue
            values[key] = value_parser(value.strip())
    if not values:
        raise ValueError(f"Missing config section: {section}")
    return values


def _load_entity_risk_level_mapping(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    in_entities = False
    current_entity: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if line == "entities:":
            in_entities = True
            continue
        if in_entities and not line.startswith(" "):
            break
        if not in_entities:
            continue
        if line.startswith("  ") and not line.startswith("    ") and stripped.endswith(":"):
            current_entity = stripped[:-1]
            continue
        if current_entity and line.startswith("    risk_level:"):
            values[current_entity] = stripped.split(":", 1)[1].strip()
    if not values:
        raise ValueError("Missing entity risk levels")
    return values
