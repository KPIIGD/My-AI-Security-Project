"""Core dataclasses for Korean PII Guardrail v0.2.

Important: PIISpan.text is internal-only. Do not log it or include it in public API responses.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from time import time
from typing import Any
from uuid import uuid4

from .enums import Action, EntityType, OutputTarget, RiskLevel, ScanStage


class InvalidOffsetError(ValueError):
    """Raised when a detector returns offsets that do not match the raw text."""


@dataclass(frozen=True)
class PIISpan:
    start: int
    end: int
    text: str
    entity_type: EntityType
    score: float
    sources: tuple[str, ...]
    risk_level: RiskLevel
    action: Action = Action.CANDIDATE
    normalized: str | None = None
    suffix: str | None = None
    reason_codes: tuple[str, ...] = ()
    detector_ids: tuple[str, ...] = ()
    is_composite: bool = False
    policy_profile: str | None = None
    output_target: OutputTarget | None = None

    def validate_against(self, raw_text: str) -> None:
        if self.start < 0 or self.end < self.start or self.end > len(raw_text):
            raise InvalidOffsetError(f"Invalid span offsets: {self.start}:{self.end}")
        if raw_text[self.start:self.end] != self.text:
            raise InvalidOffsetError("Span text does not match raw text at start/end offsets")
        if not (0.0 <= self.score <= 1.0):
            raise ValueError("PIISpan.score must be between 0.0 and 1.0")

    def to_public(self, value_hash: str | None = None) -> "PublicPIISpan":
        return PublicPIISpan(
            start=self.start,
            end=self.end,
            span_length=self.end - self.start,
            entity_type=self.entity_type,
            score=self.score,
            risk_level=self.risk_level,
            action=self.action,
            suffix=self.suffix,
            is_composite=self.is_composite,
            sources=self.sources,
            detector_ids=self.detector_ids,
            reason_codes=self.reason_codes,
            value_hash=value_hash,
            raw_value_logged=False,
        )


@dataclass(frozen=True)
class PublicPIISpan:
    start: int
    end: int
    span_length: int
    entity_type: EntityType
    score: float
    risk_level: RiskLevel
    action: Action
    suffix: str | None = None
    is_composite: bool = False
    sources: tuple[str, ...] = ()
    detector_ids: tuple[str, ...] = ()
    reason_codes: tuple[str, ...] = ()
    value_hash: str | None = None
    raw_value_logged: bool = False

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["entity_type"] = self.entity_type.value
        data["risk_level"] = self.risk_level.value
        data["action"] = self.action.value
        data["sources"] = list(self.sources)
        data["detector_ids"] = list(self.detector_ids)
        data["reason_codes"] = list(self.reason_codes)
        data["raw_value_logged"] = False
        return data


@dataclass(frozen=True)
class GuardrailOptions:
    return_spans: bool = True
    include_audit_events: bool = True
    allow_experimental_entities: bool = False
    fail_on_invalid_offset: bool = True
    mask_suffix_preserving: bool = True


@dataclass(frozen=True)
class GuardrailRequest:
    text: str
    scan_stage: ScanStage = ScanStage.INPUT
    output_target: OutputTarget = OutputTarget.LLM_INPUT
    policy_profile: str = "strict"
    request_id: str | None = None
    document_id: str | None = None
    purpose_id: str | None = None
    domain: str | None = None
    locale: str = "ko-KR"
    options: GuardrailOptions = field(default_factory=GuardrailOptions)
    _effective_request_id: str = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        if not self.text:
            raise ValueError("GuardrailRequest.text must not be empty")
        if self.scan_stage not in {ScanStage.INPUT, ScanStage.OUTPUT}:
            raise ValueError("v0.2 supports input/output scan_stage only")
        object.__setattr__(self, "_effective_request_id", self.request_id or str(uuid4()))

    @property
    def effective_request_id(self) -> str:
        return self._effective_request_id


@dataclass(frozen=True)
class AuditEvent:
    event_type: str
    entity_type: EntityType
    score: float
    risk_level: RiskLevel
    action: Action
    request_id: str | None = None
    timestamp_epoch: float = field(default_factory=time)
    policy_profile: str | None = None
    output_target: OutputTarget | None = None
    sources: tuple[str, ...] = ()
    detector_ids: tuple[str, ...] = ()
    value_hash: str | None = None
    span_length: int | None = None
    reason_codes: tuple[str, ...] = ()
    raw_value_logged: bool = False

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["entity_type"] = self.entity_type.value
        data["risk_level"] = self.risk_level.value
        data["action"] = self.action.value
        if self.output_target is not None:
            data["output_target"] = self.output_target.value
        data["sources"] = list(self.sources)
        data["detector_ids"] = list(self.detector_ids)
        data["reason_codes"] = list(self.reason_codes)
        data["raw_value_logged"] = False
        return data


@dataclass(frozen=True)
class ResponseMetrics:
    latency_ms: float
    detected_span_count: int
    masked_span_count: int


@dataclass(frozen=True)
class GuardrailResponse:
    request_id: str
    blocked: bool
    masked_text: str | None
    spans: tuple[PublicPIISpan, ...]
    audit_events: tuple[AuditEvent, ...]
    metrics: ResponseMetrics
    policy_profile: str
    output_target: OutputTarget
    raw_value_logged: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "blocked": self.blocked,
            "masked_text": self.masked_text,
            "spans": [span.to_dict() for span in self.spans],
            "audit_events": [event.to_dict() for event in self.audit_events],
            "metrics": asdict(self.metrics),
            "policy_profile": self.policy_profile,
            "output_target": self.output_target.value,
            "raw_value_logged": False,
        }
