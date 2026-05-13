"""Regex-based structured PII candidate detectors."""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from pathlib import Path

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
    ) -> None:
        self.scores = dict(scores) if scores is not None else load_regex_base_scores()
        self.risk_levels = dict(risk_levels) if risk_levels is not None else load_entity_risk_levels()

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
    _ipv4_pattern = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")
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


class BankAccountCandidateDetector(BaseRegexDetector):
    detector_id = "regex.bank_account"
    _pattern = re.compile(r"(?<!\d)\d{2,6}(?:[- ]\d{2,6}){1,4}(?!\d)")

    def _detect(self, preprocessed: PreprocessResult) -> Iterable[PIISpan]:
        for match in iter_restored_matches(preprocessed, self._pattern):
            if _is_order_id_context(preprocessed.raw_text, match.start):
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


_ORDER_ID_CONTEXT_PATTERN = re.compile(
    r"(?:주문\s*(?:번호|ID)|거래\s*번호|예약\s*번호|order\s*(?:id|no|number))\s*[:#-]?\s*$",
    re.IGNORECASE,
)


def _is_order_id_context(raw_text: str, start: int) -> bool:
    prefix = raw_text[max(0, start - 32) : start]
    return bool(_ORDER_ID_CONTEXT_PATTERN.search(prefix))


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
