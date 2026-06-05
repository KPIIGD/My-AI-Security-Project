"""Request models for the local product-console API."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from pii_guardrail.schema import GuardrailOptions, GuardrailRequest


class GuardrailOptionsPayload(BaseModel):
    return_spans: bool = True
    include_audit_events: bool = True
    allow_experimental_entities: bool = False

    def to_core(self) -> GuardrailOptions:
        return GuardrailOptions(
            return_spans=self.return_spans,
            include_audit_events=self.include_audit_events,
            allow_experimental_entities=self.allow_experimental_entities,
        )


class ApplyRequestPayload(BaseModel):
    text: str = Field(..., min_length=1)
    scan_stage: str = "input"
    output_target: str = "llm_input"
    policy_profile: str = "strict"
    request_id: str | None = None
    document_id: str | None = None
    purpose_id: str | None = "console_local_analysis"
    domain: str | None = "general"
    locale: str = "ko-KR"
    options: GuardrailOptionsPayload = Field(default_factory=GuardrailOptionsPayload)
    encrypted_raw_logging_key: str | None = None
    encrypted_raw_key_hint: str | None = None

    def to_core(self) -> GuardrailRequest:
        return GuardrailRequest(
            text=self.text,
            scan_stage=self.scan_stage,
            output_target=self.output_target,
            policy_profile=self.policy_profile,
            request_id=self.request_id,
            document_id=self.document_id,
            purpose_id=self.purpose_id,
            domain=self.domain,
            locale=self.locale,
            options=self.options.to_core(),
        )


class TraceRequestPayload(ApplyRequestPayload):
    reveal_raw: bool = False


class BatchRequestPayload(BaseModel):
    texts: list[str] = Field(default_factory=list)
    lines: str | None = None
    limit: int = 200
    scan_stage: str = "input"
    output_target: str = "llm_input"
    policy_profile: str = "strict"
    purpose_id: str | None = "console_local_batch"
    domain: str | None = "general"
    options: GuardrailOptionsPayload = Field(default_factory=GuardrailOptionsPayload)
    encrypted_raw_logging_key: str | None = None
    encrypted_raw_key_hint: str | None = None

    def iter_texts(self) -> list[str]:
        values = [text.strip() for text in self.texts if text and text.strip()]
        if self.lines:
            values.extend(line.strip() for line in self.lines.splitlines() if line.strip())
        return values[: max(1, min(self.limit, 1000))]

    def to_apply_payload(self, text: str, *, request_id: str | None = None) -> ApplyRequestPayload:
        return ApplyRequestPayload(
            text=text,
            scan_stage=self.scan_stage,
            output_target=self.output_target,
            policy_profile=self.policy_profile,
            request_id=request_id,
            purpose_id=self.purpose_id,
            domain=self.domain,
            options=self.options,
            encrypted_raw_logging_key=self.encrypted_raw_logging_key,
            encrypted_raw_key_hint=self.encrypted_raw_key_hint,
        )


class DecryptLogPayload(BaseModel):
    decrypt_key: str


class ErrorPayload(BaseModel):
    detail: str
    raw_value_logged: bool = False


JsonDict = dict[str, Any]
