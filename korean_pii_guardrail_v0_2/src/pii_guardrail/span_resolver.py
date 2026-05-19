"""Span resolver for Korean PII Guardrail v0.2.

Implements ``docs/02_ARCHITECTURE_SPEC`` §L6 in four ordered steps:

1. **Duplicate merge** — collapse spans sharing ``(start, end, entity_type)``
   into a single span carrying ``max(score)`` and the union of
   ``sources``/``detector_ids``/``reason_codes``.
2. **Overlap resolution** — group overlapping spans into connected
   components (Union-Find on the overlap graph), then iteratively pick
   the best winner inside each component using
   ``(priority_index asc, length desc, score desc, start asc)`` until
   no candidates remain. This handles ``EMAIL > PERSON_NAME substring``
   and ``SCHOOL/HOSPITAL > ORGANIZATION reclassify`` cases automatically.
   It also avoids the greedy pitfall where a broad mid-span eliminates
   a valid non-overlapping span via chain overlap, and never folds
   metadata across different raw offsets in same-type ties.
3. **ADDRESS fragment merge** — adjacent ``ADDRESS_UNIT``/``ADDRESS_FULL``
   spans separated only by whitespace are folded into a single
   ``ADDRESS_FULL`` span with a fresh ``resolver.address.fragment_merge``
   reason code.
4. **Composite escalation** — for spans where ``is_composite`` was already
   marked by ``context_scorer``, apply ``single_turn_composite.upgrades``
   from ``configs/scoring.yaml`` to upgrade ``risk_level`` (e.g.
   ``PERSON_NAME + PHONE_MOBILE`` → ``P1``).

The resolver never touches ``action``, ``policy_profile``, or the masked
output. Those decisions belong to the policy router and masker.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import replace

from .dictionary_loader import load_composite_upgrades, load_entity_priority
from .enums import EntityType, RiskLevel, Source
from .interfaces import PreprocessResult, SentenceSpan
from .regex_detectors import load_entity_risk_levels
from .schema import GuardrailRequest, PIISpan


_ADDRESS_TYPES = frozenset({EntityType.ADDRESS_FULL, EntityType.ADDRESS_UNIT})
_RISK_ORDER = ("P3", "P2", "P1", "P0")


class SpanResolver:
    """Resolve detector candidate spans into a final span set."""

    detector_id = "resolver.korean"
    source = Source.RESOLVER.value

    def __init__(
        self,
        *,
        priority_order: tuple[EntityType, ...] | None = None,
        composite_upgrades: Mapping[frozenset[str], str] | None = None,
        risk_levels: Mapping[EntityType, RiskLevel] | None = None,
    ) -> None:
        if priority_order is None:
            priority_order = tuple(EntityType(name) for name in load_entity_priority())
        if not priority_order:
            raise ValueError("priority_order must not be empty")
        self.priority_order = priority_order
        self._priority_index = {et: idx for idx, et in enumerate(priority_order)}
        self.composite_upgrades = (
            dict(composite_upgrades)
            if composite_upgrades is not None
            else load_composite_upgrades()
        )
        self.risk_levels = (
            dict(risk_levels)
            if risk_levels is not None
            else load_entity_risk_levels()
        )

    # ----------------------------------------------------------- Public API

    def resolve(
        self,
        spans: list[PIISpan],
        preprocessed: PreprocessResult,
        request: GuardrailRequest,
    ) -> list[PIISpan]:
        del request
        if not spans:
            return []
        merged = self._merge_duplicates(spans)
        kept = self._resolve_overlaps(merged)
        kept = self._merge_address_fragments(kept, preprocessed.raw_text)
        kept = self._escalate_composites(kept, preprocessed)
        return sorted(kept, key=lambda s: (s.start, s.end, s.entity_type.value))

    # -------------------------------------------------------------- Steps

    def _merge_duplicates(self, spans: list[PIISpan]) -> list[PIISpan]:
        bucket: dict[tuple[int, int, EntityType], PIISpan] = {}
        for span in spans:
            key = (span.start, span.end, span.entity_type)
            existing = bucket.get(key)
            if existing is None:
                bucket[key] = span
                continue
            bucket[key] = self._fold(existing, span)
        return list(bucket.values())

    def _resolve_overlaps(self, spans: list[PIISpan]) -> list[PIISpan]:
        if not spans:
            return []
        components = self._build_overlap_components(spans)
        result: list[PIISpan] = []
        for comp in components:
            if len(comp) == 1:
                # No conflict in this component — preserve span unchanged.
                # resolver.overlap.kept is reserved for spans that actually
                # survived an overlap conflict (PR #14 P3 fix).
                result.append(comp[0])
                continue
            winners = self._select_winners_in_component(comp)
            for winner in winners:
                result.append(self._mark_kept(winner))
        return result

    def _build_overlap_components(self, spans: list[PIISpan]) -> list[list[PIISpan]]:
        """Group spans into connected components by overlap graph.

        Two spans are in the same component if any chain of pairwise overlaps
        connects them. Used to avoid the greedy chain-overlap pitfall where
        A-B overlap, B-C overlap, A-C disjoint leads to A being dropped when
        B loses to C (PR #14 P1-2 fix).
        """
        n = len(spans)
        parent = list(range(n))

        def find(x: int) -> int:
            while parent[x] != x:
                parent[x] = parent[parent[x]]
                x = parent[x]
            return x

        def union(x: int, y: int) -> None:
            rx, ry = find(x), find(y)
            if rx != ry:
                parent[rx] = ry

        for i in range(n):
            for j in range(i + 1, n):
                if _overlaps(spans[i], spans[j]):
                    union(i, j)

        groups: dict[int, list[PIISpan]] = {}
        for i, span in enumerate(spans):
            groups.setdefault(find(i), []).append(span)
        return list(groups.values())

    def _select_winners_in_component(self, comp: list[PIISpan]) -> list[PIISpan]:
        """Iteratively pick non-overlapping winners within a connected component.

        Sort remaining by (priority_index asc, length desc, score desc, start asc),
        pick best, remove all overlapping with it, repeat. This guarantees that
        when a broad mid-span is eliminated by a higher-priority winner, the
        other valid spans that only overlapped via that mid-span are recovered
        (PR #14 P1-2 fix). Same-type same-length ties are broken by score then
        start, never by folding metadata across different offsets
        (PR #14 P1-1 fix).
        """
        remaining = list(comp)
        winners: list[PIISpan] = []
        while remaining:
            remaining.sort(key=self._win_key)
            winner = remaining.pop(0)
            winners.append(winner)
            remaining = [s for s in remaining if not _overlaps(s, winner)]
        return winners

    def _win_key(self, span: PIISpan) -> tuple[int, int, float, int]:
        # Lower priority_index wins → ascending.
        # Longer span wins → invert with negative length.
        # Higher score wins → invert with negative score.
        # Earlier start as deterministic tie-break.
        return (
            self._priority_index.get(span.entity_type, len(self.priority_order)),
            -(span.end - span.start),
            -span.score,
            span.start,
        )

    def _merge_address_fragments(
        self, spans: list[PIISpan], raw_text: str
    ) -> list[PIISpan]:
        address_spans = sorted(
            (s for s in spans if s.entity_type in _ADDRESS_TYPES),
            key=lambda s: s.start,
        )
        if len(address_spans) < 2:
            return spans

        non_address = [s for s in spans if s.entity_type not in _ADDRESS_TYPES]
        merged: list[PIISpan] = []
        current = address_spans[0]
        for nxt in address_spans[1:]:
            gap_text = raw_text[current.end : nxt.start]
            if current.end <= nxt.start and gap_text.strip() == "":
                combined_text = raw_text[current.start : nxt.end]
                current = PIISpan(
                    start=current.start,
                    end=nxt.end,
                    text=combined_text,
                    entity_type=EntityType.ADDRESS_FULL,
                    score=max(current.score, nxt.score),
                    sources=_union(
                        current.sources, nxt.sources, (Source.RESOLVER.value,)
                    ),
                    risk_level=self.risk_levels.get(
                        EntityType.ADDRESS_FULL, current.risk_level
                    ),
                    action=current.action,
                    reason_codes=_union(
                        current.reason_codes,
                        nxt.reason_codes,
                        ("resolver.address.fragment_merge",),
                    ),
                    detector_ids=_union(
                        current.detector_ids, nxt.detector_ids, (self.detector_id,)
                    ),
                    is_composite=current.is_composite or nxt.is_composite,
                    suffix=nxt.suffix or current.suffix,
                )
                current.validate_against(raw_text)
            else:
                merged.append(current)
                current = nxt
        merged.append(current)
        return non_address + merged

    def _escalate_composites(
        self, spans: list[PIISpan], preprocessed: PreprocessResult
    ) -> list[PIISpan]:
        if not self.composite_upgrades or len(spans) < 2:
            return spans
        sentences = preprocessed.sentences or (
            SentenceSpan(
                start=0,
                end=len(preprocessed.raw_text),
                text=preprocessed.raw_text,
            ),
        )
        sentence_idx = [self._sentence_index_for(s, sentences) for s in spans]

        result: list[PIISpan] = []
        for i, span in enumerate(spans):
            same_sentence_peer_types = {
                spans[j].entity_type.value
                for j in range(len(spans))
                if j != i and sentence_idx[j] == sentence_idx[i]
            }
            sentence_types = same_sentence_peer_types | {span.entity_type.value}

            # Collect every composite rule that matches in this sentence,
            # independent of whether it would raise the risk level. The
            # is_composite flag must reflect membership in any composite,
            # because downstream policy/audit/evaluation may key off it
            # even when the risk level cannot increase further
            # (PR #14 P2 fix).
            matched_levels: list[str] = []
            for upgrade_key, level in self.composite_upgrades.items():
                if span.entity_type.value not in upgrade_key:
                    continue
                if not upgrade_key.issubset(sentence_types):
                    continue
                matched_levels.append(level)

            if not matched_levels:
                result.append(span)
                continue

            # Risk level upgrade is conditional: only when the highest
            # matched level is strictly higher than the current level.
            best_upgrade: str | None = None
            for level in matched_levels:
                if not self._is_higher(level, span.risk_level):
                    continue
                if best_upgrade is None or self._is_higher(level, RiskLevel(best_upgrade)):
                    best_upgrade = level

            if best_upgrade is not None:
                new_risk = RiskLevel(best_upgrade)
                new_reason = _append(
                    span.reason_codes,
                    f"resolver.composite.upgrade:{best_upgrade}",
                )
            else:
                new_risk = span.risk_level
                new_reason = _append(span.reason_codes, "resolver.composite.match")

            result.append(
                replace(
                    span,
                    risk_level=new_risk,
                    reason_codes=new_reason,
                    detector_ids=_append(span.detector_ids, self.detector_id),
                    is_composite=True,
                )
            )
        return result

    # ----------------------------------------------------------- Helpers

    def _fold(self, a: PIISpan, b: PIISpan) -> PIISpan:
        return replace(
            a,
            score=max(a.score, b.score),
            sources=_union(a.sources, b.sources),
            reason_codes=_union(a.reason_codes, b.reason_codes),
            detector_ids=_union(a.detector_ids, b.detector_ids),
            is_composite=a.is_composite or b.is_composite,
            suffix=a.suffix or b.suffix,
        )

    def _mark_kept(self, span: PIISpan) -> PIISpan:
        return replace(
            span,
            reason_codes=_append(span.reason_codes, "resolver.overlap.kept"),
            detector_ids=_append(span.detector_ids, self.detector_id),
        )

    def _is_higher(self, new_level: str, current: RiskLevel) -> bool:
        try:
            return _RISK_ORDER.index(new_level) > _RISK_ORDER.index(current.value)
        except ValueError:
            return False

    @staticmethod
    def _sentence_index_for(
        span: PIISpan, sentences: tuple[SentenceSpan, ...]
    ) -> int:
        for idx, sentence in enumerate(sentences):
            if sentence.start <= span.start < sentence.end:
                return idx
            if sentence.start <= span.start and span.end <= sentence.end:
                return idx
        return len(sentences) - 1


# ---------------------------------------------------------- module helpers


def _overlaps(a: PIISpan, b: PIISpan) -> bool:
    return not (a.end <= b.start or a.start >= b.end)


def _union(*sequences: Iterable[str]) -> tuple[str, ...]:
    result: list[str] = []
    for seq in sequences:
        for item in seq:
            if item not in result:
                result.append(item)
    return tuple(result)


def _append(existing: tuple[str, ...], value: str) -> tuple[str, ...]:
    if value in existing:
        return existing
    return (*existing, value)
