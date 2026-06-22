"""Gateway adapters for the Korean PII Guardrail.

One core engine (:mod:`pii_guardrail.adapters.core`), attached to every gateway
two ways:

  in-process (Python import, no HTTP)
      - scan() / mask_text() / mask_openai_messages()          (any code embed)
      - KoreanPIIValidator                                     (Guardrails AI)

  HTTP (run a server, gateways POST to it)
      - create_sidecar_app()        /v1/pii/apply  ← LiteLLM, Azure APIM, ...
      - create_reverse_proxy_app()  /v1/chat/completions (we become the gateway)
      - create_portkey_app()        /guardrails/portkey  (Portkey webhook)
      - KoreanPIIGuardrail          LiteLLM CustomGuardrail hook

The dep-free core symbols import eagerly. The rest are resolved lazily via
``__getattr__`` so importing this package never requires fastapi / httpx /
guardrails / litellm unless you actually use that adapter.
"""
from __future__ import annotations

from .core import (
    GuardrailEngine,
    NERLoadError,
    PIIBlocked,
    get_engine,
    mask_openai_messages,
    mask_text,
    public_summary,
    scan,
    set_engine,
)

# name → (submodule, attribute) resolved on first access
_LAZY = {
    "create_sidecar_app": ("sidecar", "create_app"),
    "create_reverse_proxy_app": ("reverse_proxy", "create_app"),
    "create_portkey_app": ("portkey_webhook", "create_app"),
    "process_portkey_payload": ("portkey_webhook", "process_portkey_payload"),
    "KoreanPIIValidator": ("guardrails_ai", "KoreanPIIValidator"),
    "KoreanPIIGuardrail": ("litellm_hook", "KoreanPIIGuardrail"),
}

__all__ = [
    "GuardrailEngine",
    "NERLoadError",
    "PIIBlocked",
    "get_engine",
    "set_engine",
    "scan",
    "mask_text",
    "mask_openai_messages",
    "public_summary",
    *_LAZY.keys(),
]


def __getattr__(name: str):
    if name in _LAZY:
        import importlib

        mod, attr = _LAZY[name]
        module = importlib.import_module(f".{mod}", __name__)
        return getattr(module, attr)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(__all__)
