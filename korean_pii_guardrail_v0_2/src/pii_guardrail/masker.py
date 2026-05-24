"""M7 suffix-preserving masking engine and HMAC hash provider."""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from typing import Protocol, runtime_checkable

from .enums import Action, EntityType
from .policy import PolicyDecision, PolicyRouter, TransformationMethod
from .schema import GuardrailRequest, PIISpan


class MaskingError(ValueError):
    """Raised when resolved spans cannot be masked deterministically."""


@runtime_checkable
class HashProvider(Protocol):
    """Minimal hash provider interface consumed by SuffixPreservingMasker.

    ``@runtime_checkable`` is applied so callers can use
    ``isinstance(provider, HashProvider)`` for adapter selection without
    a ``TypeError``. The check is structural (only the presence of
    ``digest`` is verified, not its signature), so subclasses and ad-hoc
    objects with a ``digest`` callable both satisfy it.
    """

    def digest(self, value: str) -> str:
        """Return a deterministic digest for a raw PII value."""


@dataclass(frozen=True)
class HmacHashProvider:
    """Deterministic HMAC-SHA256 value hasher.

    The default key is only for local deterministic behavior. Production key
    management remains a later security integration task.
    """

    key: bytes | str = b"local-dev-only-m7-key"
    key_id: str = "local-dev"

    def digest(self, value: str) -> str:
        key = self.key.encode("utf-8") if isinstance(self.key, str) else self.key
        digest = hmac.new(key, value.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"hmac-sha256:{self.key_id}:{digest}"


class SuffixPreservingMasker:
    """Apply M7 policy decisions to raw text without consuming suffixes."""

    full_redact_token = "[REDACTED]"

    def __init__(
        self,
        *,
        policy_router: PolicyRouter | None = None,
        hash_provider: HashProvider | None = None,
    ) -> None:
        self.policy_router = policy_router or PolicyRouter()
        self.hash_provider = hash_provider or HmacHashProvider()

    def apply(self, raw_text: str, spans: list[PIISpan], request: GuardrailRequest) -> str | None:
        if raw_text != request.text:
            raise MaskingError("Masking raw text does not match request text")

        decisions = [(span, self.policy_router.select(span, request)) for span in spans]
        for span, _ in decisions:
            span.validate_against(raw_text)

        if any(decision.action is Action.BLOCK for _, decision in decisions):
            return None

        replacements = [
            (span, decision, self._replacement_for(span, decision))
            for span, decision in decisions
            if decision.action in {Action.MASK, Action.HASH}
        ]
        self._validate_non_overlapping([span for span, _, _ in replacements])

        placeholder_state = _PlaceholderState(self.policy_router.policy_config.placeholder_format)
        replacement_by_span: list[tuple[PIISpan, str]] = []
        for span, decision, replacement in replacements:
            if replacement is None:
                replacement = placeholder_state.placeholder_for(span)
            replacement_by_span.append((span, replacement))

        return self._reconstruct(raw_text, replacement_by_span)

    def _replacement_for(self, span: PIISpan, decision: PolicyDecision) -> str | None:
        if decision.method is TransformationMethod.FULL_REDACT:
            return self.full_redact_token
        if decision.method is TransformationMethod.HMAC_HASH:
            return self.hash_provider.digest(span.text)
        if decision.method is TransformationMethod.LABEL_MASK:
            return None
        if decision.method is TransformationMethod.PASS:
            return span.text
        if decision.method is TransformationMethod.BLOCK:
            return None
        raise MaskingError("Unsupported transformation method")

    @staticmethod
    def _validate_non_overlapping(spans: list[PIISpan]) -> None:
        ordered = sorted(spans, key=lambda span: (span.start, span.end))
        previous: PIISpan | None = None
        for span in ordered:
            if previous is not None and span.start < previous.end:
                raise MaskingError("Overlapping spans cannot be masked safely")
            previous = span

    @staticmethod
    def _reconstruct(raw_text: str, replacements: list[tuple[PIISpan, str]]) -> str:
        if not replacements:
            return raw_text

        parts: list[str] = []
        cursor = 0
        for span, replacement in sorted(replacements, key=lambda item: (item[0].start, item[0].end)):
            parts.append(raw_text[cursor : span.start])
            parts.append(replacement)
            cursor = span.end
        parts.append(raw_text[cursor:])
        return "".join(parts)


class _PlaceholderState:
    def __init__(self, placeholder_format: str) -> None:
        self.placeholder_format = placeholder_format
        self.index_by_family: dict[str, int] = {}
        self.placeholder_by_value: dict[tuple[str, str], str] = {}

    def placeholder_for(self, span: PIISpan) -> str:
        family = _entity_family(span.entity_type)
        key = (family, span.text)
        existing = self.placeholder_by_value.get(key)
        if existing is not None:
            return existing

        index = self.index_by_family.get(family, 0) + 1
        self.index_by_family[family] = index
        placeholder = self.placeholder_format.format(entity_family=family, index=index)
        self.placeholder_by_value[key] = placeholder
        return placeholder


def _entity_family(entity_type: EntityType) -> str:
    if entity_type is EntityType.PERSON_NAME:
        return "PERSON"
    if entity_type in {EntityType.PHONE_MOBILE, EntityType.PHONE_LANDLINE}:
        return "PHONE"
    if entity_type in {EntityType.ADDRESS_FULL, EntityType.ADDRESS_UNIT}:
        return "ADDRESS"
    if entity_type is EntityType.RRN:
        return "RRN"
    if entity_type in {EntityType.FRN, EntityType.PASSPORT, EntityType.DRIVER_LICENSE}:
        return "ID"
    if entity_type is EntityType.API_KEY_SECRET:
        return "SECRET"
    return entity_type.value
