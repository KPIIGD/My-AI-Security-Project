"""OpenAI-compatible reverse proxy — we *become* the gateway.

Point any OpenAI-compatible client's ``base_url`` at this app. It masks PII on
the way in, forwards to the real upstream, and masks PII on the way out. This
is the "generic reverse proxy" attachment form: it sits in front of *any*
provider without that provider needing a guardrail hook.

Run it:
    uvicorn pii_guardrail.adapters.reverse_proxy:app --port 8000

Then:
    client = OpenAI(base_url="http://localhost:8000/v1", api_key="sk-...")

env:
  OPENAI_BASE_URL   upstream base (default https://api.openai.com/v1)
  OPENAI_API_KEY    fallback upstream key when the client sends no Authorization
  PII_PROXY_TIMEOUT upstream timeout seconds (default 60)

Note: streaming is not yet supported — ``stream`` is forced off so input/output
can be scanned. ``fastapi`` / ``httpx`` are optional deps:
    pip install korean-pii-guardrail[adapters]

NOTE: no ``from __future__ import annotations`` — FastAPI must see ``Request``
as a real object (it is imported lazily inside ``create_app``; a string
annotation can't be resolved at module scope and is mis-read as a query param).
"""

import os
from typing import Optional

from .core import (
    GuardrailEngine,
    PIIBlocked,
    get_engine,
    mask_openai_messages,
    scan,
)

UPSTREAM = os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1")
TIMEOUT = float(os.environ.get("PII_PROXY_TIMEOUT", "60"))
# fail-closed: an output-scan failure REDACTS rather than returning raw output.
FAIL_OPEN = os.environ.get("PII_FAIL_OPEN", "0") == "1"
OUTPUT_BLOCKED_MSG = "[응답이 개인정보 보호 정책에 의해 차단되었습니다.]"


def _mask_output_content(text: str, engine):
    """Return the masked/redacted output content (fail-closed). Never raw."""
    try:
        result = scan(text, scan_stage="output", output_target="external_output", engine=engine)
    except Exception:  # noqa: BLE001 — fail-closed: never leak raw output
        return text if FAIL_OPEN else OUTPUT_BLOCKED_MSG
    if result.get("blocked"):
        return OUTPUT_BLOCKED_MSG
    masked = result.get("masked_text")
    return masked if masked is not None else text


def create_app(engine: Optional[GuardrailEngine] = None, *, upstream: Optional[str] = None):
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse
    import httpx

    base = (upstream or UPSTREAM).rstrip("/")
    app = FastAPI(title="Korean PII Guardrail Reverse Proxy", version="v0.2")

    @app.get("/health")
    def health() -> dict:
        eng = engine or get_engine()
        return {"status": "ok", "ner_mode": eng.ner_mode, "upstream": base}

    @app.post("/v1/chat/completions")
    async def chat_completions(request: Request):
        body = await request.json()
        body["stream"] = False  # streaming not supported; scan whole response

        messages = body.get("messages")
        if isinstance(messages, list):
            try:
                masked, _summaries = mask_openai_messages(
                    messages, stage="input", engine=engine
                )
            except PIIBlocked as blk:
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": {
                            "message": "blocked by Korean PII guardrail",
                            "type": "pii_blocked",
                            "guardrail": blk.summary,
                        }
                    },
                )
            body["messages"] = masked

        headers = {}
        auth = request.headers.get("authorization")
        if auth:
            headers["Authorization"] = auth
        elif os.environ.get("OPENAI_API_KEY"):
            headers["Authorization"] = f"Bearer {os.environ['OPENAI_API_KEY']}"

        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            up = await client.post(f"{base}/chat/completions", json=body, headers=headers)

        try:
            data = up.json()
        except Exception:  # noqa: BLE001 — non-JSON upstream error
            return JSONResponse(status_code=up.status_code, content={"error": up.text})

        # mask output (fail-closed: scan failure / BLOCK redacts, never raw)
        for choice in data.get("choices", []) or []:
            msg = choice.get("message")
            if not isinstance(msg, dict):
                continue
            content = msg.get("content")
            if isinstance(content, str) and content.strip():
                msg["content"] = _mask_output_content(content, engine)
            # tool-call arguments can carry PII too
            for tc in msg.get("tool_calls") or []:
                fn = tc.get("function") if isinstance(tc, dict) else None
                args = fn.get("arguments") if isinstance(fn, dict) else None
                if isinstance(args, str) and args.strip():
                    fn["arguments"] = _mask_output_content(args, engine)

        return JSONResponse(status_code=up.status_code, content=data)

    return app


def __getattr__(name: str):
    if name == "app":
        return create_app()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
