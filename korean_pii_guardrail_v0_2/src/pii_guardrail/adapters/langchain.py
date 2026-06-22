"""LangChain integration — in-process guardrail runnables.

Drop the Korean PII guardrail into any LangChain chain. No HTTP: the runnables
call the in-process engine directly.

Usage:
    from langchain_core.prompts import ChatPromptTemplate
    from pii_guardrail.adapters.langchain import mask_input, mask_output

    chain = prompt | mask_input() | llm | mask_output()
    # or guard an existing llm in one call:
    from pii_guardrail.adapters.langchain import protect
    safe_llm = protect(llm)

Behaviour (fail-closed): a BLOCK decision raises ``PIIBlocked`` so the chain
stops instead of forwarding raw PII. Otherwise the text/message content is
replaced with the masked version.

``langchain-core`` is an optional dependency:
    pip install korean-pii-guardrail[langchain]
"""
from __future__ import annotations

from typing import Any, Optional

from .core import GuardrailEngine, mask_text


def _mask_content(content: Any, *, stage: str, target: Optional[str], engine: Optional[GuardrailEngine]):
    """Mask str content or a list of multimodal text parts. Returns new content."""
    if isinstance(content, str):
        masked, _ = mask_text(content, stage=stage, output_target=target, engine=engine)
        return masked
    if isinstance(content, list):
        out = []
        for part in content:
            if isinstance(part, dict) and isinstance(part.get("text"), str):
                masked, _ = mask_text(part["text"], stage=stage, output_target=target, engine=engine)
                out.append({**part, "text": masked})
            else:
                out.append(part)
        return out
    return content


def _mask_one(value: Any, *, stage: str, target: Optional[str], engine: Optional[GuardrailEngine]):
    """Mask a str, a BaseMessage, a list of them, or a PromptValue."""
    from langchain_core.messages import BaseMessage

    if isinstance(value, str):
        return _mask_content(value, stage=stage, target=target, engine=engine)
    if isinstance(value, BaseMessage):
        masked = _mask_content(value.content, stage=stage, target=target, engine=engine)
        try:
            return value.model_copy(update={"content": masked})
        except Exception:  # noqa: BLE001 — older langchain / non-pydantic
            value.content = masked
            return value
    if isinstance(value, list):
        return [_mask_one(v, stage=stage, target=target, engine=engine) for v in value]
    # PromptValue → operate on its messages if available
    to_messages = getattr(value, "to_messages", None)
    if callable(to_messages):
        return _mask_one(to_messages(), stage=stage, target=target, engine=engine)
    return value


def mask_input(engine: Optional[GuardrailEngine] = None):
    """RunnableLambda that masks user input flowing INTO the model."""
    from langchain_core.runnables import RunnableLambda

    return RunnableLambda(
        lambda v: _mask_one(v, stage="input", target=None, engine=engine)
    ).with_config(run_name="korean_pii_mask_input")


def mask_output(engine: Optional[GuardrailEngine] = None):
    """RunnableLambda that masks model output flowing OUT of the model."""
    from langchain_core.runnables import RunnableLambda

    return RunnableLambda(
        lambda v: _mask_one(v, stage="output", target="external_output", engine=engine)
    ).with_config(run_name="korean_pii_mask_output")


def protect(llm: Any, engine: Optional[GuardrailEngine] = None):
    """Wrap an llm/runnable so input and output are both guarded:

        protect(llm) == mask_input() | llm | mask_output()
    """
    return mask_input(engine=engine) | llm | mask_output(engine=engine)
