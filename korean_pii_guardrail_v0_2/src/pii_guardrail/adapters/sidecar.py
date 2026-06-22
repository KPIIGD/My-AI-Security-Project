"""HTTP sidecar — the single HTTP contract every network gateway calls.

Run it:
    uvicorn pii_guardrail.adapters.sidecar:app --host 0.0.0.0 --port 8080

Endpoints:
    GET  /health        → {status, ner_mode}
    POST /v1/pii/apply  → {text, policy_profile?, scan_stage?, output_target?,
                           request_id?} → GuardrailResponse.to_dict() + ner_mode

The response is the no-raw-PII payload: ``masked_text`` plus public spans
(start/end/length/type/risk/action/HMAC value_hash) — never raw PII.

LiteLLM, Portkey, Azure APIM and the reverse proxy all reuse this one contract,
which is why "build the sidecar once and ①③ are mostly reuse" holds.

``fastapi`` / ``uvicorn`` are optional deps: pip install korean-pii-guardrail[adapters]

NOTE: no ``from __future__ import annotations`` here — FastAPI must see the
route parameter types as real objects (the request model is defined inside
``create_app`` for lazy deps; string annotations can't be resolved at module
scope and would be mis-read as query params).
"""

from contextlib import asynccontextmanager
from typing import Optional

from .core import GuardrailEngine, get_engine


def create_app(engine: Optional[GuardrailEngine] = None):
    """Build the sidecar FastAPI app. ``engine`` defaults to the env singleton."""
    from fastapi import FastAPI
    from pydantic import BaseModel

    @asynccontextmanager
    async def lifespan(_app):
        # Surface fail-closed NER load errors at boot, not on first request.
        eng = engine or get_engine()
        # ASCII only — Windows consoles (cp949) crash on non-ASCII at startup.
        print(f"[sidecar] pipeline ready - NER: {eng.ner_mode}", flush=True)
        yield

    app = FastAPI(title="Korean PII Guardrail Sidecar", version="v0.2", lifespan=lifespan)

    class ApplyRequest(BaseModel):
        text: str
        policy_profile: str = "strict"
        scan_stage: str = "input"  # "input" | "output"
        output_target: Optional[str] = None
        request_id: Optional[str] = None

    @app.get("/health")
    def health() -> dict:
        eng = engine or get_engine()
        return {"status": "ok", "ner_mode": eng.ner_mode}

    @app.post("/v1/pii/apply")
    def apply(req: ApplyRequest) -> dict:
        eng = engine or get_engine()
        return eng.scan(
            req.text,
            scan_stage=req.scan_stage,
            policy_profile=req.policy_profile,
            output_target=req.output_target,
            request_id=req.request_id,
        )

    return app


def __getattr__(name: str):
    # Lazy module-level ``app`` so ``uvicorn ...:app`` works without importing
    # fastapi at module import time.
    if name == "app":
        return create_app()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
