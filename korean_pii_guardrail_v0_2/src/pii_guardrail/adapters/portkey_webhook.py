"""Portkey custom-webhook guardrail.

Portkey's "Webhook" guardrail calls an HTTP endpoint with the request/response
context and expects a verdict (+ optional transformed data). This adapter masks
PII in the chat messages and returns ``verdict=True`` with ``transformedData``
carrying the masked messages, or ``verdict=False`` when the guardrail blocks.

Run it:
    uvicorn pii_guardrail.adapters.portkey_webhook:app --port 8081
Then register https://.../guardrails/portkey as a Webhook guardrail in Portkey.

NOTE: Portkey's exact payload shape varies by version. This handles the common
OpenAI shape at ``request.json.messages``. The pure mapping lives in
:func:`process_portkey_payload` so it can be unit-tested and re-pathed easily.

``fastapi`` is an optional dep: pip install korean-pii-guardrail[adapters]

NOTE: no ``from __future__ import annotations`` — FastAPI must see ``Request``
as a real object (imported lazily inside ``create_app``).
"""

from typing import Optional

from .core import GuardrailEngine, PIIBlocked, get_engine, mask_openai_messages


def process_portkey_payload(
    body: dict, *, engine: Optional[GuardrailEngine] = None
) -> dict:
    """Map a Portkey webhook payload → Portkey webhook response.

    Pure function (no I/O) so it is unit-testable without a running Portkey."""
    req = (body or {}).get("request") or {}
    req_json = req.get("json") or {}
    messages = req_json.get("messages")
    if not isinstance(messages, list):
        return {"verdict": True, "transformed": False}

    try:
        masked, summaries = mask_openai_messages(messages, stage="input", engine=engine)
    except PIIBlocked as blk:
        return {
            "verdict": False,
            "transformed": False,
            "data": {"reason": "high-risk PII detected", "guardrail": blk.summary},
        }

    transformed = masked != messages
    new_req_json = dict(req_json)
    new_req_json["messages"] = masked
    return {
        "verdict": True,
        "transformed": transformed,
        "transformedData": {"request": {"json": new_req_json}},
        "data": {"guardrail": summaries},
    }


def create_app(engine: Optional[GuardrailEngine] = None):
    from fastapi import FastAPI, Request

    app = FastAPI(title="Korean PII Guardrail — Portkey Webhook", version="v0.2")

    @app.get("/health")
    def health() -> dict:
        eng = engine or get_engine()
        return {"status": "ok", "ner_mode": eng.ner_mode}

    @app.post("/guardrails/portkey")
    async def webhook(request: Request) -> dict:
        body = await request.json()
        return process_portkey_payload(body, engine=engine)

    return app


def __getattr__(name: str):
    if name == "app":
        return create_app()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
