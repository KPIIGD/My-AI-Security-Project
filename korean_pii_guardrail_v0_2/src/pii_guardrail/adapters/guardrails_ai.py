"""Guardrails AI integration — in-process Validator.

Embed the Korean PII guardrail inside a Guardrails AI ``Guard``. No HTTP: the
validator calls the in-process engine directly. This is the "library embed"
attachment form (the one the HTTP sidecar can't cover).

Usage:
    from guardrails import Guard
    from pii_guardrail.adapters.guardrails_ai import KoreanPIIValidator

    guard = Guard().use(KoreanPIIValidator(on_fail="fix"))
    outcome = guard.validate("내 번호는 010-1234-5678 이야")
    outcome.validated_output   # → masked text when on_fail="fix"

``guardrails-ai`` is an optional dependency:
    pip install korean-pii-guardrail[guardrails]
"""
from __future__ import annotations

from typing import Any, Optional

from .core import GuardrailEngine, public_summary, scan


def _load_guardrails():
    """Import the Guardrails AI primitives across supported versions."""
    try:  # guardrails >= 0.4
        from guardrails.validator_base import Validator, register_validator
    except Exception:  # pragma: no cover - older layout
        from guardrails.validators import Validator, register_validator
    try:  # guardrails >= 0.4
        from guardrails.classes.validation.validation_result import (
            FailResult,
            PassResult,
        )
    except Exception:  # pragma: no cover - older layout
        from guardrails.validators import FailResult, PassResult
    return Validator, register_validator, PassResult, FailResult


try:
    _Validator, _register_validator, _PassResult, _FailResult = _load_guardrails()
except Exception as exc:  # noqa: BLE001
    raise ImportError(
        "guardrails-ai is required for KoreanPIIValidator. "
        "install: pip install korean-pii-guardrail[guardrails]"
    ) from exc


@_register_validator(name="guardrails/korean-pii", data_type="string")
class KoreanPIIValidator(_Validator):
    """Detect + mask (or block) Korean PII in a string.

    ``on_fail="fix"``    → replaces the value with the masked text.
    ``on_fail="exception"`` → raises when PII is found.
    A BLOCK decision always fails with no fix value (no safe masked form).
    """

    def __init__(
        self,
        *,
        policy_profile: str = "strict",
        scan_stage: str = "input",
        engine: Optional[GuardrailEngine] = None,
        on_fail: Optional[Any] = None,
        **kwargs: Any,
    ) -> None:
        # Store init args on super() so Guardrails can serialize/rehydrate.
        super().__init__(
            on_fail=on_fail,
            policy_profile=policy_profile,
            scan_stage=scan_stage,
            **kwargs,
        )
        self._policy_profile = policy_profile
        self._scan_stage = scan_stage
        self._engine = engine

    def validate(self, value: Any, metadata: Optional[dict] = None):
        text = value if isinstance(value, str) else str(value)
        result = scan(
            text,
            scan_stage=self._scan_stage,
            policy_profile=self._policy_profile,
            engine=self._engine,
        )
        if metadata is not None:
            metadata.setdefault("korean_pii_guardrail", []).append(
                public_summary(result, role="user", stage=self._scan_stage)
            )
        if result.get("blocked"):
            return _FailResult(
                error_message="High-risk PII detected; blocked by Korean PII guardrail."
            )
        masked = result.get("masked_text")
        if masked is not None and masked != text:
            return _FailResult(
                error_message="PII detected and masked by Korean PII guardrail.",
                fix_value=masked,
            )
        return _PassResult()
