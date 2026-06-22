"""AWS Bedrock complement — client-side guard around the Converse API.

Bedrock Guardrails are a black box (you can't run our Korean detector *inside*
them). The honest attachment is to run our guardrail *beside* Bedrock: mask PII
in the prompt before ``converse(...)`` and mask PII in the model's reply, on the
client. Compose with Bedrock's own guardrails — ours runs first.

Usage:
    import boto3
    from pii_guardrail.adapters.bedrock import guard_bedrock

    client = guard_bedrock(boto3.client("bedrock-runtime", region_name="us-east-1"))
    client.converse(modelId="...", messages=[
        {"role": "user", "content": [{"text": "내 번호 010-1234-5678"}]}
    ])  # text is masked before it leaves your machine

Wraps the Converse API (the standard message schema). ``invoke_model`` bodies
are model-specific JSON — use Converse, or mask the prompt yourself with
``pii_guardrail.adapters.core.mask_text`` before ``invoke_model``.

Behaviour (fail-closed): a BLOCK on input raises ``PIIBlocked``; output is
redacted on block / scan failure (never raw) unless PII_FAIL_OPEN=1.

``boto3`` is an optional dependency: pip install boto3
"""
from __future__ import annotations

import os
from typing import Any, Optional

from .core import GuardrailEngine, mask_text, scan

_FAIL_OPEN = os.environ.get("PII_FAIL_OPEN", "0") == "1"
_OUTPUT_BLOCKED_MSG = "[응답이 개인정보 보호 정책에 의해 차단되었습니다.]"


def _mask_converse_messages(messages: list, engine: Optional[GuardrailEngine]) -> list:
    """Mask the ``content[].text`` blocks of Bedrock Converse messages."""
    out = []
    for m in messages or []:
        if not isinstance(m, dict):
            out.append(m)
            continue
        content = m.get("content")
        if isinstance(content, list):
            new_content = []
            for block in content:
                if isinstance(block, dict) and isinstance(block.get("text"), str):
                    masked, _ = mask_text(block["text"], stage="input", engine=engine)
                    new_content.append({**block, "text": masked})
                else:
                    new_content.append(block)
            out.append({**m, "content": new_content})
        else:
            out.append(m)
    return out


def _mask_out(text: str, engine: Optional[GuardrailEngine]) -> str:
    try:
        result = scan(text, scan_stage="output", output_target="external_output", engine=engine)
    except Exception:  # noqa: BLE001 — fail-closed
        return text if _FAIL_OPEN else _OUTPUT_BLOCKED_MSG
    if result.get("blocked"):
        return _OUTPUT_BLOCKED_MSG
    masked = result.get("masked_text")
    return masked if masked is not None else text


def _mask_converse_response(response: dict, engine: Optional[GuardrailEngine]) -> dict:
    try:
        blocks = response["output"]["message"]["content"]
    except (KeyError, TypeError):
        return response
    if isinstance(blocks, list):
        for block in blocks:
            if isinstance(block, dict) and isinstance(block.get("text"), str) and block["text"].strip():
                block["text"] = _mask_out(block["text"], engine)
    return response


def guard_bedrock(client: Any, *, engine: Optional[GuardrailEngine] = None, mask_output: bool = True) -> Any:
    """Wrap ``client.converse`` in place (fail-closed) and return the client."""
    original = client.converse
    if getattr(original, "_pii_guarded", False):  # idempotent: don't double-wrap
        return client

    def guarded_converse(*args: Any, **kwargs: Any) -> Any:
        messages = kwargs.get("messages")
        if isinstance(messages, list):
            kwargs["messages"] = _mask_converse_messages(messages, engine)
        response = original(*args, **kwargs)
        if mask_output and isinstance(response, dict):
            response = _mask_converse_response(response, engine)
        return response

    guarded_converse._pii_guarded = True  # type: ignore[attr-defined]
    client.converse = guarded_converse  # type: ignore[assignment]
    return client
