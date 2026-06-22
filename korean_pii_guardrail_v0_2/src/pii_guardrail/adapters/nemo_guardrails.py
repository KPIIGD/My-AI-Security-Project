"""NVIDIA NeMo Guardrails integration — custom action.

NeMo Guardrails lets you register custom actions and call them from Colang
flows (input/output rails). This exposes the Korean PII guardrail as the
``korean_pii_mask`` action.

Usage (Python):
    from nemoguardrails import LLMRails, RailsConfig
    from pii_guardrail.adapters.nemo_guardrails import register

    rails = LLMRails(RailsConfig.from_path("./config"))
    register(rails)   # registers the korean_pii_mask action

Colang (config/rails.co):
    define flow korean pii input
      $masked = execute korean_pii_mask(text=$user_message)
      # use $masked downstream; if blocked, refuse

The action returns ``{"text", "blocked", "summary"}`` — ``text`` is the masked
string (no raw PII in ``summary``). It is fail-closed: ``blocked=True`` means
the flow should refuse rather than forward.

The action itself only needs the in-process engine, so this module imports
fine without ``nemoguardrails`` installed; ``register`` needs the package.
"""
from __future__ import annotations

from typing import Optional

from .core import GuardrailEngine, public_summary, scan

_engine: Optional[GuardrailEngine] = None


def set_action_engine(engine: Optional[GuardrailEngine]) -> None:
    """Bind a specific engine for the action (defaults to the env singleton)."""
    global _engine
    _engine = engine


async def korean_pii_mask(text: str = "", stage: str = "input") -> dict:
    """NeMo custom action: mask/inspect ``text`` for Korean PII (fail-closed)."""
    if not isinstance(text, str) or not text.strip():
        return {"text": text, "blocked": False, "summary": None}
    target = "external_output" if stage == "output" else None
    try:
        result = scan(text, scan_stage=stage, output_target=target, engine=_engine)
    except Exception:  # noqa: BLE001 — fail-closed: a scan error blocks, never passes raw
        return {"text": None, "blocked": True, "summary": None}
    summary = public_summary(result, role="user", stage=stage)
    if result.get("blocked"):
        return {"text": None, "blocked": True, "summary": summary}
    masked = result.get("masked_text")
    return {"text": masked if masked is not None else text, "blocked": False, "summary": summary}


def register(rails, *, name: str = "korean_pii_mask") -> None:
    """Register the action on an ``LLMRails`` instance."""
    rails.register_action(korean_pii_mask, name)
