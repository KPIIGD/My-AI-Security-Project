"""Deterministic context scorer for Korean PII Guardrail v0.2.

The scorer reads candidate ``PIISpan`` instances from the detector layer,
inspects the surrounding sentence for field labels, co-occurring entities,
honorifics, negative contexts, and single-turn composite evidence, then
emits new spans with adjusted score, evidence ``reason_codes``, and the
``is_composite`` flag.

It performs no LLM calls, no external lookups, and never reads previous
turns or RAG context, in line with ``docs/04_CONTEXT_POLICY_SPEC.md``.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace

from .dictionary_loader import (
    load_composite_upgrades,
    load_context_boosts,
    load_context_penalties,
    load_dictionary_lists,
    load_field_label_terms,
    load_honorific_terms,
    load_negative_context_terms,
)
from .enums import EntityType, Source
from .interfaces import PreprocessResult, SentenceSpan
from .schema import PIISpan


_BOOST_RULES_BY_ENTITY: dict[EntityType, tuple[str, ...]] = {
    EntityType.PERSON_NAME: (
        "field_label_name",
        "title_after_name",
        "phone_cooccur_for_person",
        "address_cooccur_for_person",
    ),
    EntityType.PHONE_MOBILE: ("field_label_phone",),
    EntityType.PHONE_LANDLINE: ("field_label_phone",),
    EntityType.ADDRESS_FULL: ("field_label_address", "full_address_detail"),
    EntityType.ADDRESS_UNIT: ("field_label_address",),
    EntityType.ORGANIZATION: ("organization_affiliation_context",),
    EntityType.BANK_ACCOUNT: ("field_label_account", "bank_cooccur"),
    EntityType.MEDICAL_RECORD_NO: ("medical_label",),
    EntityType.HOSPITAL: ("medical_label",),
    EntityType.HEALTH_INFO: ("medical_label",),
}

_PENALTY_RULES_BY_ENTITY: dict[EntityType, tuple[str, ...]] = {
    EntityType.PERSON_NAME: (
        "example_keyword_for_person",
        "weather_context_for_person",
        "code_or_log_context",
        "organization_not_person",
        "abstract_value_context_for_person",
    ),
    EntityType.PHONE_MOBILE: ("public_phone_context",),
    EntityType.PHONE_LANDLINE: ("public_phone_context",),
    EntityType.ADDRESS_FULL: ("code_or_log_context",),
    EntityType.ADDRESS_UNIT: ("code_or_log_context",),
    EntityType.IP_ADDRESS: ("private_ip",),
}

_FIELD_LABEL_GROUP_BY_RULE = {
    "field_label_name": "name_label",
    "field_label_phone": "phone_label",
    "field_label_address": "address_label",
    "field_label_account": "account_label",
    "organization_affiliation_context": "organization_label",
    "medical_label": "medical_label",
}

_NEGATIVE_GROUP_BY_RULE = {
    "weather_context_for_person": "weather_context",
    "public_phone_context": "public_number_context",
    "code_or_log_context": "code_context",
    "organization_not_person": "business_name_context",
    "abstract_value_context_for_person": "abstract_value_context",
}

_EXAMPLE_PENALTY_RULE = "example_context"
_EXAMPLE_NEGATIVE_GROUP = "example_context"


class ContextScorer:
    """Apply deterministic context boosts/penalties and mark composites."""

    detector_id = "context.korean"
    source = Source.CONTEXT.value

    def __init__(
        self,
        *,
        boosts: Mapping[str, float] | None = None,
        penalties: Mapping[str, float] | None = None,
        field_label_terms: Mapping[str, tuple[str, ...]] | None = None,
        negative_terms: Mapping[str, tuple[str, ...]] | None = None,
        honorifics: Mapping[str, tuple[str, ...]] | None = None,
        bank_names: tuple[str, ...] | None = None,
        composite_upgrades: Mapping[frozenset[str], str] | None = None,
    ) -> None:
        self.boosts = dict(boosts) if boosts is not None else load_context_boosts()
        self.penalties = dict(penalties) if penalties is not None else load_context_penalties()
        self.field_label_terms = (
            dict(field_label_terms)
            if field_label_terms is not None
            else load_field_label_terms()
        )
        self.negative_terms = (
            dict(negative_terms)
            if negative_terms is not None
            else load_negative_context_terms()
        )
        self.honorifics = (
            dict(honorifics) if honorifics is not None else load_honorific_terms()
        )
        if bank_names is not None:
            self.bank_names = tuple(bank_names)
        else:
            self.bank_names = load_dictionary_lists().get("bank_names", ())
        self.composite_upgrades = (
            dict(composite_upgrades)
            if composite_upgrades is not None
            else load_composite_upgrades()
        )

    # --------------------------------------------------------------- Score

    def score(
        self, spans: list[PIISpan], preprocessed: PreprocessResult
    ) -> list[PIISpan]:
        if not spans:
            return []
        raw_text = preprocessed.raw_text
        sentences = preprocessed.sentences or (
            SentenceSpan(start=0, end=len(raw_text), text=raw_text),
        )

        sentence_index_per_span = [
            self._locate_sentence_index(span, sentences) for span in spans
        ]

        result: list[PIISpan] = []
        for idx, span in enumerate(spans):
            sentence_idx = sentence_index_per_span[idx]
            sentence = sentences[sentence_idx]
            peers = [
                spans[j]
                for j in range(len(spans))
                if j != idx and sentence_index_per_span[j] == sentence_idx
            ]
            result.append(self._adjust_span(span, sentence, peers, raw_text))
        return result

    # --------------------------------------------------------------- Adjust

    def _adjust_span(
        self,
        span: PIISpan,
        sentence: SentenceSpan,
        peers: list[PIISpan],
        raw_text: str,
    ) -> PIISpan:
        sentence_text = sentence.text
        evidence_codes: list[str] = list(span.reason_codes)
        delta = 0.0

        for rule in _BOOST_RULES_BY_ENTITY.get(span.entity_type, ()):
            evidence = self._evaluate_boost(rule, span, sentence_text, peers, raw_text)
            if evidence is not None:
                delta += self.boosts.get(rule, 0.0)
                evidence_codes.append(f"context.boost.{rule}")

        for rule in _PENALTY_RULES_BY_ENTITY.get(span.entity_type, ()):
            evidence = self._evaluate_penalty(rule, span, sentence_text)
            if evidence is not None:
                delta += self.penalties.get(rule, 0.0)
                evidence_codes.append(f"context.penalty.{rule}")

        if self._match_example_context(sentence, span, raw_text) is not None:
            delta += self.penalties.get(_EXAMPLE_PENALTY_RULE, 0.0)
            evidence_codes.append(f"context.penalty.{_EXAMPLE_PENALTY_RULE}")

        is_composite = span.is_composite
        composite_marked = False
        if self.composite_upgrades and peers:
            peer_types = {p.entity_type.value for p in peers}
            sentence_types = peer_types | {span.entity_type.value}
            for upgrade_key in self.composite_upgrades:
                if span.entity_type.value not in upgrade_key:
                    continue
                if not upgrade_key.issubset(sentence_types):
                    continue
                is_composite = True
                if not composite_marked:
                    peers_in_key = sorted(upgrade_key - {span.entity_type.value})
                    for peer_type in peers_in_key:
                        evidence_codes.append(f"context.composite.{peer_type}")
                    composite_marked = True
                    break

        final_score = max(0.0, min(1.0, span.score + delta))
        merged_sources = self._append_unique(span.sources, Source.CONTEXT.value)
        merged_detector_ids = self._append_unique(span.detector_ids, self.detector_id)

        return replace(
            span,
            score=final_score,
            sources=merged_sources,
            reason_codes=tuple(evidence_codes),
            detector_ids=merged_detector_ids,
            is_composite=is_composite,
        )

    # --------------------------------------------------------------- Evidence

    def _evaluate_boost(
        self,
        rule: str,
        span: PIISpan,
        sentence_text: str,
        peers: list[PIISpan],
        raw_text: str,
    ) -> str | None:
        if (
            rule == "field_label_phone"
            and self._match_term_in_group(
                sentence_text,
                self.negative_terms,
                _EXAMPLE_NEGATIVE_GROUP,
            )
            is not None
        ):
            return None
        if rule == "field_label_name":
            return self._match_left_field_label(
                span, raw_text, self.field_label_terms, "name_label"
            )
        if rule in _FIELD_LABEL_GROUP_BY_RULE:
            return self._match_term_in_group(
                sentence_text, self.field_label_terms, _FIELD_LABEL_GROUP_BY_RULE[rule]
            )
        if rule == "title_after_name":
            return self._match_title_after(span, raw_text)
        if rule == "phone_cooccur_for_person":
            for peer in peers:
                if peer.entity_type in {EntityType.PHONE_MOBILE, EntityType.PHONE_LANDLINE}:
                    return peer.entity_type.value
            return None
        if rule == "address_cooccur_for_person":
            for peer in peers:
                if peer.entity_type in {EntityType.ADDRESS_FULL, EntityType.ADDRESS_UNIT}:
                    return peer.entity_type.value
            return None
        if rule == "bank_cooccur":
            for bank in self.bank_names:
                if bank and bank in sentence_text:
                    return bank
            return None
        if rule == "full_address_detail":
            text = span.text
            if any(token in text for token in ("동", "호", "번지", "로", "길")):
                return "address_components"
            return None
        return None

    def _evaluate_penalty(
        self,
        rule: str,
        span: PIISpan,
        sentence_text: str,
    ) -> str | None:
        if rule == "example_keyword_for_person":
            if span.text in self.negative_terms.get(_EXAMPLE_NEGATIVE_GROUP, ()):
                return "example_keyword"
            return None
        if rule in _NEGATIVE_GROUP_BY_RULE:
            return self._match_term_in_group(
                sentence_text, self.negative_terms, _NEGATIVE_GROUP_BY_RULE[rule]
            )
        if rule == "private_ip":
            for prefix in ("10.", "127.", "192.168.", "172.16.", "172.17.", "172.18.",
                           "172.19.", "172.20.", "172.21.", "172.22.", "172.23.",
                           "172.24.", "172.25.", "172.26.", "172.27.", "172.28.",
                           "172.29.", "172.30.", "172.31."):
                if span.text.startswith(prefix):
                    return "private_subnet"
            return None
        return None

    @staticmethod
    def _match_term_in_group(
        sentence_text: str,
        groups: Mapping[str, tuple[str, ...]],
        group_name: str,
    ) -> str | None:
        for term in groups.get(group_name, ()):
            if term and term in sentence_text:
                return term
        return None

    def _match_example_context(
        self,
        sentence: SentenceSpan,
        span: PIISpan,
        raw_text: str,
    ) -> str | None:
        left = raw_text[sentence.start : span.start]
        right = raw_text[span.end : sentence.end]
        return self._match_term_in_group(
            f"{left} {right}",
            self.negative_terms,
            _EXAMPLE_NEGATIVE_GROUP,
        )

    def _match_title_after(self, span: PIISpan, raw_text: str) -> str | None:
        window = raw_text[span.end : span.end + 8]
        for suffix in self.honorifics.get("person_suffixes", ()):
            if suffix and suffix in window:
                return suffix
        for title in self.honorifics.get("job_titles", ()):
            if title and title in window:
                return title
        return None

    @staticmethod
    def _match_left_field_label(
        span: PIISpan,
        raw_text: str,
        groups: Mapping[str, tuple[str, ...]],
        group_name: str,
    ) -> str | None:
        window = raw_text[max(0, span.start - 24) : span.start]
        return ContextScorer._match_term_in_group(window, groups, group_name)

    @staticmethod
    def _append_unique(existing: tuple[str, ...], value: str) -> tuple[str, ...]:
        if value in existing:
            return existing
        return (*existing, value)

    @staticmethod
    def _locate_sentence_index(span: PIISpan, sentences: tuple[SentenceSpan, ...]) -> int:
        for idx, sentence in enumerate(sentences):
            if sentence.start <= span.start < sentence.end:
                return idx
            if sentence.start <= span.start and span.end <= sentence.end:
                return idx
        return len(sentences) - 1
