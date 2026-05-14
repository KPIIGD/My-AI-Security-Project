"""Dictionary-based PII candidate detectors for Korean text.

Dictionary detectors emit low-to-mid confidence ``PIISpan`` candidates that
``context_scorer`` later boosts or penalises. They are deliberately permissive:
final masking decisions belong to span resolver, context judge, and masker.
"""

from __future__ import annotations

import re
from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass

from .dictionary_loader import (
    load_dictionary_base_scores,
    load_dictionary_lists,
)
from .enums import Action, EntityType, RiskLevel, Source
from .interfaces import PreprocessResult
from .regex_detectors import deduplicate_spans, load_entity_risk_levels
from .schema import GuardrailRequest, PIISpan


_HANGUL_SYLLABLE_RANGE = ("가", "힣")
# Apartment unit must come with a 동 prefix to avoid false positives such as
# `2호선`, `3호점`, `1호기`. Trailing lookahead rejects further digits; non-
# particle Hangul after 호 is filtered in ``_detect_addresses`` so that
# josa/honorific (`호로`, `호와`, `호도`) still pass.
_APARTMENT_UNIT_PATTERN = re.compile(
    r"(?<!\d)\d{1,3}\s*동\s+\d{1,4}\s*호(?!\d)"
)
_ROAD_TRAILER_PATTERN = re.compile(
    r"\s*\d{1,4}(?:\s*-\s*\d{1,4})?(?:\s*번지)?(?:\s+\d{1,3}\s*동)?(?:\s+\d{1,4}\s*호)?"
)
# Characters that legitimately follow a Korean given name as a particle or
# honorific suffix. Anything else in Hangul is treated as a word continuation
# and rejected by the boundary check below.
_GIVEN_NAME_TRAILING_HANGUL = frozenset(
    "이가은는을를에와과도만한께서으로랑님씨군양"
)


def _has_word_boundary_before(raw_text: str, start: int) -> bool:
    """True when ``start`` does not sit inside a longer Hangul word."""

    if start <= 0:
        return True
    prev_char = raw_text[start - 1]
    low, high = _HANGUL_SYLLABLE_RANGE
    return not (low <= prev_char <= high)


def _has_word_boundary_after(raw_text: str, end: int) -> bool:
    """True when ``end`` ends the Hangul word (or is followed by a particle)."""

    if end >= len(raw_text):
        return True
    next_char = raw_text[end]
    low, high = _HANGUL_SYLLABLE_RANGE
    if not (low <= next_char <= high):
        return True
    return next_char in _GIVEN_NAME_TRAILING_HANGUL


# Characters that may follow an address unit and still keep it a valid address:
# josa particles (`로`, `에`, `에서`, `와`, `과`, `의`, `이`, `가`, `은`, `는`, `도`, `만`)
# and Korean sentence terminators. Anything else in Hangul (e.g. `선`, `점`,
# `차`, `실`, `기`) signals that the digit+호 sequence is part of a different
# word (subway line `2호선`, store `3호점`, etc.) and the match is rejected.
_ADDRESS_UNIT_TRAILING_HANGUL = frozenset("로에서와과의이가은는도만으한라까지부터")


def _is_address_unit_boundary(raw_text: str, end: int) -> bool:
    if end >= len(raw_text):
        return True
    next_char = raw_text[end]
    low, high = _HANGUL_SYLLABLE_RANGE
    if not (low <= next_char <= high):
        return True
    return next_char in _ADDRESS_UNIT_TRAILING_HANGUL


@dataclass(frozen=True)
class _Candidate:
    start: int
    end: int
    entity_type: EntityType
    score_key: str
    reason_codes: tuple[str, ...]


class DictionaryDetector:
    """Detect Korean PII candidates by lookup against curated dictionaries."""

    detector_id = "dictionary.korean"
    source = Source.DICTIONARY.value

    def __init__(
        self,
        *,
        dictionaries: Mapping[str, tuple[str, ...]] | None = None,
        scores: Mapping[str, float] | None = None,
        risk_levels: Mapping[EntityType, RiskLevel] | None = None,
    ) -> None:
        self.dictionaries = (
            dict(dictionaries) if dictionaries is not None else load_dictionary_lists()
        )
        self.scores = dict(scores) if scores is not None else load_dictionary_base_scores()
        self.risk_levels = (
            dict(risk_levels) if risk_levels is not None else load_entity_risk_levels()
        )

        self._surnames = frozenset(self.dictionaries.get("surnames", ()))
        self._given_names = tuple(
            sorted(self.dictionaries.get("given_name_candidates", ()), key=len, reverse=True)
        )
        self._relations = tuple(
            sorted(self.dictionaries.get("relation_terms", ()), key=len, reverse=True)
        )
        self._si_gu_dong = tuple(
            sorted(self.dictionaries.get("address_si_gu_dong", ()), key=len, reverse=True)
        )
        self._road_names = tuple(
            sorted(self.dictionaries.get("road_names", ()), key=len, reverse=True)
        )
        self._organization_suffixes = tuple(
            sorted(self.dictionaries.get("organization_suffixes", ()), key=len, reverse=True)
        )
        self._brand_organizations = tuple(
            sorted(self.dictionaries.get("brand_organizations", ()), key=len, reverse=True)
        )
        self._school_suffixes = tuple(
            sorted(self.dictionaries.get("school_suffixes", ()), key=len, reverse=True)
        )
        self._hospital_suffixes = tuple(
            sorted(self.dictionaries.get("hospital_suffixes", ()), key=len, reverse=True)
        )

    # ------------------------------------------------------------------ Protocol

    def detect(self, preprocessed: PreprocessResult, request: GuardrailRequest) -> list[PIISpan]:
        del request
        raw_text = preprocessed.raw_text
        candidates: list[_Candidate] = []

        consumed_address: set[tuple[int, int]] = set()
        for candidate in self._detect_addresses(raw_text):
            candidates.append(candidate)
            consumed_address.add((candidate.start, candidate.end))

        candidates.extend(self._detect_affiliations(raw_text))
        candidates.extend(self._detect_relations(raw_text))
        candidates.extend(self._detect_person_names(raw_text, consumed_address))

        return deduplicate_spans(self._build_span(raw_text, c) for c in candidates)

    # ------------------------------------------------------------------ Build

    def _build_span(self, raw_text: str, candidate: _Candidate) -> PIISpan:
        score = self.scores[candidate.score_key]
        text = raw_text[candidate.start : candidate.end]
        span = PIISpan(
            start=candidate.start,
            end=candidate.end,
            text=text,
            entity_type=candidate.entity_type,
            score=score,
            sources=(Source.DICTIONARY.value,),
            risk_level=self.risk_levels[candidate.entity_type],
            action=Action.CANDIDATE,
            reason_codes=candidate.reason_codes,
            detector_ids=(self.detector_id,),
        )
        span.validate_against(raw_text)
        return span

    # ------------------------------------------------------------------ Person

    def _detect_person_names(
        self, raw_text: str, consumed: set[tuple[int, int]]
    ) -> Iterator[_Candidate]:
        emitted: set[tuple[int, int]] = set()

        for given in self._given_names:
            if not given:
                continue
            start = 0
            while True:
                index = raw_text.find(given, start)
                if index < 0:
                    break
                given_end = index + len(given)
                start = given_end

                if index > 0 and raw_text[index - 1] in self._surnames:
                    span_start = index - 1
                    span_end = given_end
                    key = (span_start, span_end)
                    if key in emitted:
                        continue
                    if any(cs <= span_start and span_end <= ce for (cs, ce) in consumed):
                        continue
                    if not _has_word_boundary_before(raw_text, span_start):
                        continue
                    if not _has_word_boundary_after(raw_text, span_end):
                        continue
                    emitted.add(key)
                    yield _Candidate(
                        start=span_start,
                        end=span_end,
                        entity_type=EntityType.PERSON_NAME,
                        score_key="full_name_pattern",
                        reason_codes=(
                            "dictionary.person",
                            "dictionary.surname_given.match",
                        ),
                    )
                    continue

                key = (index, given_end)
                if key in emitted:
                    continue
                if any(es <= index and given_end <= ee for (es, ee) in emitted):
                    continue
                if any(cs <= index and given_end <= ce for (cs, ce) in consumed):
                    continue
                if not _has_word_boundary_before(raw_text, index):
                    continue
                if not _has_word_boundary_after(raw_text, given_end):
                    continue
                emitted.add(key)
                yield _Candidate(
                    start=index,
                    end=given_end,
                    entity_type=EntityType.PERSON_NAME,
                    score_key="given_name_candidate",
                    reason_codes=(
                        "dictionary.person",
                        "dictionary.given_name_candidate",
                    ),
                )

    # ------------------------------------------------------------------ Relation

    def _detect_relations(self, raw_text: str) -> Iterator[_Candidate]:
        for term in self._relations:
            if not term:
                continue
            start = 0
            while True:
                index = raw_text.find(term, start)
                if index < 0:
                    break
                end = index + len(term)
                start = end
                yield _Candidate(
                    start=index,
                    end=end,
                    entity_type=EntityType.FAMILY_RELATION,
                    score_key="relation_term",
                    reason_codes=(
                        "dictionary.family_relation",
                        "dictionary.family_relation.match",
                    ),
                )

    # ------------------------------------------------------------------ Address

    def _detect_addresses(self, raw_text: str) -> Iterator[_Candidate]:
        consumed_ranges: list[tuple[int, int]] = []

        cursor = 0
        text_len = len(raw_text)
        while cursor < text_len:
            chain = self._match_si_gu_dong_chain(raw_text, cursor)
            if chain is None:
                cursor += 1
                continue
            chain_start, chain_end = chain
            extended_end = self._extend_with_road_and_unit(raw_text, chain_end)
            if extended_end > chain_end:
                yield _Candidate(
                    start=chain_start,
                    end=extended_end,
                    entity_type=EntityType.ADDRESS_FULL,
                    score_key="road_name",
                    reason_codes=("dictionary.address_full", "dictionary.address.road_name"),
                )
                consumed_ranges.append((chain_start, extended_end))
                cursor = extended_end
            else:
                yield _Candidate(
                    start=chain_start,
                    end=chain_end,
                    entity_type=EntityType.ADDRESS_UNIT,
                    score_key="address_si_gu_dong",
                    reason_codes=("dictionary.address_unit", "dictionary.address.si_gu_dong"),
                )
                consumed_ranges.append((chain_start, chain_end))
                cursor = chain_end

        for match in _APARTMENT_UNIT_PATTERN.finditer(raw_text):
            if any(cs <= match.start() and match.end() <= ce for (cs, ce) in consumed_ranges):
                continue
            if not _is_address_unit_boundary(raw_text, match.end()):
                continue
            yield _Candidate(
                start=match.start(),
                end=match.end(),
                entity_type=EntityType.ADDRESS_UNIT,
                score_key="apartment_unit",
                reason_codes=("dictionary.address_unit", "dictionary.address.apartment_unit"),
            )

    def _match_si_gu_dong_chain(
        self, raw_text: str, start: int
    ) -> tuple[int, int] | None:
        chain_start = self._skip_whitespace(raw_text, start)
        first = self._match_prefix_token(raw_text, chain_start, self._si_gu_dong)
        if first is None:
            return None
        cursor = first
        while True:
            next_pos = self._skip_whitespace(raw_text, cursor)
            if next_pos == cursor or next_pos >= len(raw_text):
                break
            extended = self._match_prefix_token(raw_text, next_pos, self._si_gu_dong)
            if extended is None:
                break
            cursor = extended
        return chain_start, cursor

    def _extend_with_road_and_unit(self, raw_text: str, start: int) -> int:
        skip = self._skip_whitespace(raw_text, start)
        road_end = self._match_prefix_token(raw_text, skip, self._road_names)
        if road_end is None:
            return start
        cursor = road_end
        trailer = _ROAD_TRAILER_PATTERN.match(raw_text, cursor)
        if trailer:
            cursor = trailer.end()
        return cursor

    # ------------------------------------------------------------------ Affiliation

    def _detect_affiliations(self, raw_text: str) -> Iterator[_Candidate]:
        seen: set[tuple[int, int]] = set()

        for brand in self._brand_organizations:
            if not brand:
                continue
            start = 0
            while True:
                index = raw_text.find(brand, start)
                if index < 0:
                    break
                end = index + len(brand)
                start = end
                if (index, end) in seen:
                    continue
                seen.add((index, end))
                yield _Candidate(
                    start=index,
                    end=end,
                    entity_type=EntityType.ORGANIZATION,
                    score_key="organization_suffix",
                    reason_codes=(
                        "dictionary.organization",
                        "dictionary.organization.brand",
                    ),
                )

        yield from self._iter_suffix_entities(
            raw_text,
            self._school_suffixes,
            EntityType.SCHOOL,
            "school_suffix",
            "dictionary.school",
            seen,
        )
        yield from self._iter_suffix_entities(
            raw_text,
            self._hospital_suffixes,
            EntityType.HOSPITAL,
            "hospital_suffix",
            "dictionary.hospital",
            seen,
        )
        yield from self._iter_suffix_entities(
            raw_text,
            self._organization_suffixes,
            EntityType.ORGANIZATION,
            "organization_suffix",
            "dictionary.organization",
            seen,
        )

    def _iter_suffix_entities(
        self,
        raw_text: str,
        suffixes: Iterable[str],
        entity_type: EntityType,
        score_key: str,
        reason_prefix: str,
        seen: set[tuple[int, int]],
    ) -> Iterator[_Candidate]:
        for suffix in suffixes:
            if not suffix:
                continue
            start = 0
            while True:
                index = raw_text.find(suffix, start)
                if index < 0:
                    break
                end = index + len(suffix)
                start = end
                head_start = self._expand_korean_head(raw_text, index)
                if head_start >= index:
                    continue
                span_key = (head_start, end)
                if span_key in seen:
                    continue
                if any(s <= head_start and end <= e for (s, e) in seen):
                    continue
                seen.add(span_key)
                yield _Candidate(
                    start=head_start,
                    end=end,
                    entity_type=entity_type,
                    score_key=score_key,
                    reason_codes=(reason_prefix, f"{reason_prefix}.suffix_match"),
                )

    # ------------------------------------------------------------------ Helpers

    @staticmethod
    def _skip_whitespace(raw_text: str, start: int) -> int:
        cursor = start
        text_len = len(raw_text)
        while cursor < text_len and raw_text[cursor].isspace():
            cursor += 1
        return cursor

    @staticmethod
    def _match_prefix_token(raw_text: str, start: int, tokens: Iterable[str]) -> int | None:
        for token in tokens:
            if not token:
                continue
            if raw_text.startswith(token, start):
                return start + len(token)
        return None

    @staticmethod
    def _expand_korean_head(raw_text: str, suffix_start: int) -> int:
        cursor = suffix_start
        low, high = _HANGUL_SYLLABLE_RANGE
        while cursor > 0:
            ch = raw_text[cursor - 1]
            if low <= ch <= high or "A" <= ch <= "Z" or "a" <= ch <= "z" or ch.isdigit():
                cursor -= 1
                continue
            break
        return cursor
