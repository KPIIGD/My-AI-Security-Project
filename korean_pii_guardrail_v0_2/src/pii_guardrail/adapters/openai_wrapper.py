"""OpenAI Python SDK drop-in guard.

Wrap an ``openai.OpenAI`` / ``openai.AzureOpenAI`` client so every
``client.chat.completions.create(...)`` masks PII in the request messages
before sending and (optionally) masks PII in the response before returning.

Usage:
    from openai import OpenAI
    from pii_guardrail.adapters.openai_wrapper import guard_openai

    client = guard_openai(OpenAI())          # mutates + returns the same client
    client.chat.completions.create(model="gpt-4o", messages=[...])  # now guarded

This works against ANY OpenAI-compatible endpoint the SDK can talk to
(OpenAI, Azure OpenAI, vLLM, Ollama, LiteLLM, OpenRouter, ...), so it is the
in-process counterpart to the reverse proxy.

Behaviour (fail-closed): a BLOCK on input raises ``PIIBlocked``; output is
redacted on block or scan failure (never returned raw) unless PII_FAIL_OPEN=1.

``openai`` is an optional dependency: pip install openai
"""
from __future__ import annotations

import os
from typing import Any, Optional

from .core import GuardrailEngine, mask_openai_messages, scan

_FAIL_OPEN = os.environ.get("PII_FAIL_OPEN", "0") == "1"
_OUTPUT_BLOCKED_MSG = "[응답이 개인정보 보호 정책에 의해 차단되었습니다.]"


def _mask_output_text(text: str, engine: Optional[GuardrailEngine]) -> str:
    try:
        result = scan(text, scan_stage="output", output_target="external_output", engine=engine)
    except Exception:  # noqa: BLE001 — fail-closed
        return text if _FAIL_OPEN else _OUTPUT_BLOCKED_MSG
    if result.get("blocked"):
        return _OUTPUT_BLOCKED_MSG
    masked = result.get("masked_text")
    return masked if masked is not None else text


def _mask_response(response: Any, engine: Optional[GuardrailEngine]) -> Any:
    """Mask assistant content on a ChatCompletion object (best-effort, in place)."""
    try:
        for choice in getattr(response, "choices", None) or []:
            msg = getattr(choice, "message", None)
            content = getattr(msg, "content", None) if msg is not None else None
            if isinstance(content, str) and content.strip():
                msg.content = _mask_output_text(content, engine)
    except Exception:  # noqa: BLE001 — never break a returned response object
        pass
    return response


def guard_openai(
    client: Any,
    *,
    engine: Optional[GuardrailEngine] = None,
    mask_output: bool = True,
) -> Any:
    """Wrap ``client.chat.completions.create`` in place and return the client."""
    completions = client.chat.completions
    original = completions.create
    if getattr(original, "_pii_guarded", False):  # idempotent: don't double-wrap
        return client

    def guarded_create(*args: Any, **kwargs: Any) -> Any:
        messages = kwargs.get("messages")
        if isinstance(messages, list):
            # raises PIIBlocked on a block → caller sees a hard failure (fail-closed)
            kwargs["messages"], _ = mask_openai_messages(
                messages, stage="input", engine=engine
            )
        response = original(*args, **kwargs)
        if mask_output:
            response = _mask_response(response, engine)
        return response

    guarded_create._pii_guarded = True  # type: ignore[attr-defined]
    completions.create = guarded_create  # type: ignore[assignment]
    return client
