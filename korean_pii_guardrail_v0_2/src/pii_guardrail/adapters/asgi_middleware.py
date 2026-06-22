"""ASGI middleware — embed the guardrail in your own FastAPI/Starlette app.

Drop this in front of an OpenAI-compatible app you own. It masks PII in the
request ``messages`` (and blocks high-risk PII) and masks PII in the JSON
response. No HTTP hop — it calls the in-process engine.

Usage:
    from fastapi import FastAPI
    from pii_guardrail.adapters.asgi_middleware import PIIGuardrailMiddleware

    app = FastAPI()
    app.add_middleware(PIIGuardrailMiddleware)   # guards /v1/chat/completions

Behaviour (fail-closed): a BLOCK on input returns HTTP 400; a BLOCK / scan
failure on output redacts the content (never raw) unless PII_FAIL_OPEN=1.

Note: buffers the response to scan it, so streaming (SSE) responses are not
masked — use the reverse proxy or SDK wrapper for streaming. Only JSON bodies
on the configured paths are touched.
"""
from __future__ import annotations

import json
import os
from typing import Iterable, Optional

from .core import GuardrailEngine, PIIBlocked, mask_openai_messages, scan

_FAIL_OPEN = os.environ.get("PII_FAIL_OPEN", "0") == "1"
_OUTPUT_BLOCKED_MSG = "[응답이 개인정보 보호 정책에 의해 차단되었습니다.]"


def _mask_out(text: str, engine: Optional[GuardrailEngine]) -> str:
    try:
        result = scan(text, scan_stage="output", output_target="external_output", engine=engine)
    except Exception:  # noqa: BLE001 — fail-closed
        return text if _FAIL_OPEN else _OUTPUT_BLOCKED_MSG
    if result.get("blocked"):
        return _OUTPUT_BLOCKED_MSG
    masked = result.get("masked_text")
    return masked if masked is not None else text


def _mask_response_body(raw: bytes, engine: Optional[GuardrailEngine]) -> bytes:
    try:
        data = json.loads(raw)
    except Exception:  # noqa: BLE001 — not JSON (or gzip): leave untouched
        return raw
    try:
        for choice in data.get("choices", []) or []:
            msg = choice.get("message")
            if not isinstance(msg, dict):
                continue
            content = msg.get("content")
            if isinstance(content, str) and content.strip():
                msg["content"] = _mask_out(content, engine)
            for tc in msg.get("tool_calls") or []:
                fn = tc.get("function") if isinstance(tc, dict) else None
                args = fn.get("arguments") if isinstance(fn, dict) else None
                if isinstance(args, str) and args.strip():
                    fn["arguments"] = _mask_out(args, engine)
    except Exception:  # noqa: BLE001 — never corrupt the response on a bug
        return raw
    return json.dumps(data).encode("utf-8")


class PIIGuardrailMiddleware:
    def __init__(
        self,
        app,
        *,
        engine: Optional[GuardrailEngine] = None,
        paths: Iterable[str] = ("/v1/chat/completions",),
        mask_response: bool = True,
    ) -> None:
        self.app = app
        self.engine = engine
        self.paths = set(paths)
        self.mask_response = mask_response

    async def __call__(self, scope, receive, send):
        if (
            scope.get("type") != "http"
            or scope.get("method") != "POST"
            or scope.get("path") not in self.paths
        ):
            await self.app(scope, receive, send)
            return

        # Strip Accept-Encoding so the downstream app returns UNCOMPRESSED JSON we
        # can actually scan. Without this, a gzip/br response body would fail to
        # parse and (fail-open) pass raw PII through. We buffer the whole response
        # anyway, so there is no streaming/compression benefit lost.
        if self.mask_response:
            scope = dict(scope)
            scope["headers"] = [
                (k, v) for (k, v) in scope.get("headers", []) if k.lower() != b"accept-encoding"
            ]

        body = await self._read_body(receive)
        new_body = body
        try:
            data = json.loads(body) if body else None
        except Exception:  # noqa: BLE001
            data = None
        if isinstance(data, dict) and isinstance(data.get("messages"), list):
            try:
                data["messages"], _ = mask_openai_messages(
                    data["messages"], stage="input", engine=self.engine
                )
            except PIIBlocked as blk:
                await self._send_json(
                    send,
                    400,
                    {
                        "error": {
                            "type": "pii_blocked",
                            "message": "blocked by Korean PII guardrail",
                            "guardrail": blk.summary,
                        }
                    },
                )
                return
            new_body = json.dumps(data).encode("utf-8")

        receive = self._replay_receive(new_body)
        if not self.mask_response:
            await self.app(scope, receive, send)
            return
        await self.app(scope, receive, self._masking_send(send))

    @staticmethod
    async def _read_body(receive) -> bytes:
        chunks = []
        while True:
            message = await receive()
            if message["type"] != "http.request":
                break
            chunks.append(message.get("body", b""))
            if not message.get("more_body", False):
                break
        return b"".join(chunks)

    @staticmethod
    def _replay_receive(body: bytes):
        sent = False

        async def receive():
            nonlocal sent
            if not sent:
                sent = True
                return {"type": "http.request", "body": body, "more_body": False}
            return {"type": "http.disconnect"}

        return receive

    def _masking_send(self, send):
        state = {"start": None, "chunks": []}

        async def wrapped(message):
            if message["type"] == "http.response.start":
                state["start"] = message
                return
            if message["type"] == "http.response.body":
                state["chunks"].append(message.get("body", b""))
                if message.get("more_body", False):
                    return
                full = b"".join(state["chunks"])
                start = state["start"] or {"type": "http.response.start", "status": 200, "headers": []}
                in_headers = start.get("headers", [])
                # We stripped Accept-Encoding, but if the app compressed anyway we
                # can't scan the body — fail-closed (redact) rather than pass raw.
                compressed = any(
                    k.lower() == b"content-encoding" and v.strip().lower() not in (b"", b"identity")
                    for (k, v) in in_headers
                )
                if compressed and not _FAIL_OPEN:
                    new = json.dumps({"error": {"type": "pii_unmaskable", "message": _OUTPUT_BLOCKED_MSG}}).encode("utf-8")
                    headers = [
                        (k, v) for (k, v) in in_headers
                        if k.lower() not in (b"content-length", b"content-encoding", b"content-type")
                    ]
                    headers.append((b"content-type", b"application/json"))
                else:
                    new = _mask_response_body(full, self.engine)
                    headers = [(k, v) for (k, v) in in_headers if k.lower() != b"content-length"]
                headers.append((b"content-length", str(len(new)).encode("latin-1")))
                await send({**start, "headers": headers})
                await send({"type": "http.response.body", "body": new, "more_body": False})
                return
            await send(message)

        return wrapped

    @staticmethod
    async def _send_json(send, status: int, payload: dict) -> None:
        body = json.dumps(payload).encode("utf-8")
        await send(
            {
                "type": "http.response.start",
                "status": status,
                "headers": [
                    (b"content-type", b"application/json"),
                    (b"content-length", str(len(body)).encode("latin-1")),
                ],
            }
        )
        await send({"type": "http.response.body", "body": body, "more_body": False})
