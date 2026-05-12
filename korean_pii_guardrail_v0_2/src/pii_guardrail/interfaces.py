"""Protocol interfaces for detectors and pipeline components."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol

from .schema import GuardrailRequest, PIISpan


@dataclass(frozen=True)
class TextVariant:
    name: str
    text: str
    variant_to_raw: tuple[int | None, ...]
    variant_to_raw_span: tuple[tuple[int, int] | None, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class TokenSpan:
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class SentenceSpan:
    start: int
    end: int
    text: str


@dataclass(frozen=True)
class PreprocessResult:
    raw_text: str
    normalized_text: str
    variants: tuple[TextVariant, ...]
    norm_to_raw: tuple[int | None, ...]
    raw_to_norm: tuple[int | None, ...]
    sentences: tuple[SentenceSpan, ...]
    eojeols: tuple[TokenSpan, ...]


class Detector(Protocol):
    detector_id: str
    source: str

    def detect(self, preprocessed: PreprocessResult, request: GuardrailRequest) -> list[PIISpan]:
        """Return candidate PIISpans with raw-text offsets."""
        ...


class BoundaryCorrector(Protocol):
    def correct(self, span: PIISpan, preprocessed: PreprocessResult) -> PIISpan:
        """Return a corrected PIISpan with suffix split when applicable."""
        ...


class SpanResolver(Protocol):
    def resolve(self, spans: list[PIISpan], preprocessed: PreprocessResult, request: GuardrailRequest) -> list[PIISpan]:
        """Resolve duplicates, overlaps, and single-turn composite escalation."""
        ...


class Masker(Protocol):
    def apply(self, raw_text: str, spans: list[PIISpan], request: GuardrailRequest) -> str | None:
        """Return masked text or None when the response is blocked."""
        ...
