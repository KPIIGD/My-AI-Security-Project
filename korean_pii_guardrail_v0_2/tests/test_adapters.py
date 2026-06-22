"""Tests for the gateway adapters (pii_guardrail.adapters).

Uses a real engine wired to the repo configs but with mock NER (no 1.3GB
model needed). Covers the dep-free core facade, the in-process Guardrails AI
validator, and the HTTP adapters (sidecar / reverse proxy / Portkey / LiteLLM)
via FastAPI's TestClient. Adapters whose optional deps are missing are skipped.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from pii_guardrail.adapters import core
from pii_guardrail.pipeline import GuardrailPipeline, default_components

CONFIG_DIR = str(Path(__file__).resolve().parents[1] / "configs")

PHONE_TEXT = "내 번호 010-1234-5678 이야"
PHONE_RAW = "010-1234-5678"
CLEAN_TEXT = "안녕하세요 반갑습니다 오늘 날씨 좋네요"


@pytest.fixture()
def engine() -> core.GuardrailEngine:
    """Real pipeline + configs + mock NER (fast, deterministic, no model)."""
    return core.GuardrailEngine(
        GuardrailPipeline(default_components(config_dir=CONFIG_DIR)),
        "mock-test",
    )


class _BlockingEngine:
    """Duck-typed engine that always blocks — for the BLOCK / PIIBlocked path."""

    ner_mode = "blocking-test"

    def scan(self, text, **kwargs):  # noqa: ANN001
        return {
            "blocked": True,
            "masked_text": None,
            "spans": [
                {
                    "entity_type": "RRN",
                    "action": "block",
                    "risk_level": "P0",
                    "value_hash": "deadbeef",
                }
            ],
            "metrics": {"detected_span_count": 1, "masked_span_count": 0},
            "ner_mode": self.ner_mode,
        }


class _FailingEngine:
    """Duck-typed engine that raises — for the fail-closed (engine error) path."""

    ner_mode = "failing-test"

    def scan(self, text, **kwargs):  # noqa: ANN001
        raise RuntimeError("engine boom")


# ── core facade ───────────────────────────────────────────────────────────
def test_scan_masks_phone(engine):
    r = core.scan(PHONE_TEXT, engine=engine)
    assert r["blocked"] is False
    assert r["masked_text"] != PHONE_TEXT
    assert PHONE_RAW not in r["masked_text"]
    assert r["metrics"]["detected_span_count"] >= 1
    assert any("PHONE" in s["entity_type"] for s in r["spans"])


def test_scan_clean_passthrough(engine):
    r = core.scan(CLEAN_TEXT, engine=engine)
    assert r["blocked"] is False
    assert r["masked_text"] == CLEAN_TEXT
    assert r["spans"] == []


def test_scan_empty_is_skipped(engine):
    r = core.scan("   ", engine=engine)
    assert r["skipped"] is True
    assert r["masked_text"] == "   "


def test_public_summary_has_no_raw_pii(engine):
    r = core.scan(PHONE_TEXT, engine=engine)
    summary = core.public_summary(r, role="user", stage="input")
    blob = json.dumps(summary, ensure_ascii=False)
    assert PHONE_RAW not in blob
    assert "01012345678" not in blob
    assert summary["detected_span_count"] >= 1
    assert summary["entities"][0]["value_hash"]  # HMAC present, raw absent


def test_mask_text_returns_masked(engine):
    masked, summary = core.mask_text(PHONE_TEXT, engine=engine)
    assert PHONE_RAW not in masked
    assert summary["blocked"] is False


def test_mask_text_raises_on_block():
    with pytest.raises(core.PIIBlocked) as exc:
        core.mask_text(PHONE_TEXT, engine=_BlockingEngine())
    assert exc.value.summary["blocked"] is True


def test_mask_openai_messages_does_not_mutate_input(engine):
    messages = [{"role": "user", "content": PHONE_TEXT}]
    masked, summaries = core.mask_openai_messages(messages, engine=engine)
    assert messages[0]["content"] == PHONE_TEXT  # original untouched
    assert PHONE_RAW not in masked[0]["content"]
    assert len(summaries) == 1


def test_mask_openai_messages_handles_multimodal(engine):
    messages = [
        {"role": "user", "content": [{"type": "text", "text": PHONE_TEXT}]}
    ]
    masked, _ = core.mask_openai_messages(messages, engine=engine)
    assert PHONE_RAW not in masked[0]["content"][0]["text"]


def test_set_engine_resets():
    core.set_engine(_BlockingEngine())
    assert core.get_engine().ner_mode == "blocking-test"
    core.set_engine(None)  # reset to lazy env-built singleton


# ── sidecar (fastapi) ─────────────────────────────────────────────────────
def test_sidecar_health_and_apply(engine):
    fastapi = pytest.importorskip("fastapi")
    from fastapi.testclient import TestClient

    from pii_guardrail.adapters import create_sidecar_app

    client = TestClient(create_sidecar_app(engine=engine))

    h = client.get("/health")
    assert h.status_code == 200
    assert h.json()["status"] == "ok"

    r = client.post("/v1/pii/apply", json={"text": PHONE_TEXT})
    assert r.status_code == 200
    body = r.json()
    assert body["blocked"] is False
    assert PHONE_RAW not in body["masked_text"]


# ── reverse proxy (fastapi) ───────────────────────────────────────────────
def test_reverse_proxy_health(engine):
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from pii_guardrail.adapters import create_reverse_proxy_app

    client = TestClient(create_reverse_proxy_app(engine=engine))
    h = client.get("/health")
    assert h.status_code == 200
    assert h.json()["status"] == "ok"


def test_reverse_proxy_blocks_before_upstream():
    pytest.importorskip("fastapi")
    pytest.importorskip("httpx")
    from fastapi.testclient import TestClient

    from pii_guardrail.adapters import create_reverse_proxy_app

    # Blocking engine → 400 returned before any upstream call is attempted.
    client = TestClient(create_reverse_proxy_app(engine=_BlockingEngine()))
    r = client.post(
        "/v1/chat/completions",
        json={"model": "gpt-4o", "messages": [{"role": "user", "content": "x"}]},
    )
    assert r.status_code == 400
    assert r.json()["error"]["type"] == "pii_blocked"


# ── portkey webhook ───────────────────────────────────────────────────────
def test_portkey_payload_masks(engine):
    from pii_guardrail.adapters import process_portkey_payload

    body = {"request": {"json": {"messages": [{"role": "user", "content": PHONE_TEXT}]}}}
    out = process_portkey_payload(body, engine=engine)
    assert out["verdict"] is True
    assert out["transformed"] is True
    masked = out["transformedData"]["request"]["json"]["messages"][0]["content"]
    assert PHONE_RAW not in masked


def test_portkey_payload_blocks():
    from pii_guardrail.adapters import process_portkey_payload

    body = {"request": {"json": {"messages": [{"role": "user", "content": "x"}]}}}
    out = process_portkey_payload(body, engine=_BlockingEngine())
    assert out["verdict"] is False


def test_portkey_payload_no_messages_passes(engine):
    from pii_guardrail.adapters import process_portkey_payload

    out = process_portkey_payload({"request": {"json": {}}}, engine=engine)
    assert out["verdict"] is True
    assert out["transformed"] is False


# ── litellm hook ──────────────────────────────────────────────────────────
def test_litellm_apply_guardrail_masks(engine):
    pytest.importorskip("litellm")
    import asyncio

    from pii_guardrail.adapters import KoreanPIIGuardrail

    core.set_engine(engine)  # hook uses the in-process global engine
    try:
        guard = KoreanPIIGuardrail()
        inputs = {"texts": [PHONE_TEXT]}
        out = asyncio.run(guard.apply_guardrail(inputs, {}, "request"))
        assert PHONE_RAW not in out["texts"][0]
    finally:
        core.set_engine(None)


# ── guardrails AI validator (optional) ────────────────────────────────────
def test_guardrails_validator_masks(engine):
    pytest.importorskip("guardrails")
    from pii_guardrail.adapters import KoreanPIIValidator

    validator = KoreanPIIValidator(engine=engine)
    result = validator.validate(PHONE_TEXT, {})
    # FailResult with a fix_value carrying the masked text.
    fix = getattr(result, "fix_value", None)
    assert fix is not None
    assert PHONE_RAW not in fix


# ── output-path fail-closed (regression guards for the P0 fix) ─────────────
def test_reverse_proxy_output_masks_phone(engine):
    from pii_guardrail.adapters.reverse_proxy import _mask_output_content

    out = _mask_output_content(PHONE_TEXT, engine)
    assert PHONE_RAW not in out


def test_reverse_proxy_output_redacts_on_block():
    from pii_guardrail.adapters.reverse_proxy import OUTPUT_BLOCKED_MSG, _mask_output_content

    # BLOCK on output must redact, never return the raw model text.
    assert _mask_output_content("주민번호 노출 응답", _BlockingEngine()) == OUTPUT_BLOCKED_MSG


def test_reverse_proxy_output_fail_closed_on_scan_error():
    from pii_guardrail.adapters.reverse_proxy import OUTPUT_BLOCKED_MSG, _mask_output_content

    # Engine error on output scan must redact (fail-closed), not return raw.
    assert _mask_output_content("raw output text", _FailingEngine()) == OUTPUT_BLOCKED_MSG


def test_litellm_post_call_masks_content_and_tool_calls(engine):
    pytest.importorskip("litellm")
    import asyncio
    import types

    from pii_guardrail.adapters import KoreanPIIGuardrail

    core.set_engine(engine)
    try:
        guard = KoreanPIIGuardrail()
        fn = types.SimpleNamespace(arguments=PHONE_TEXT)
        msg = types.SimpleNamespace(
            content=PHONE_TEXT, tool_calls=[types.SimpleNamespace(function=fn)]
        )
        resp = types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])
        out = asyncio.run(guard.async_post_call_success_hook({}, None, resp))
        assert PHONE_RAW not in out.choices[0].message.content
        assert PHONE_RAW not in out.choices[0].message.tool_calls[0].function.arguments
    finally:
        core.set_engine(None)


def test_litellm_post_call_redacts_blocked_output():
    pytest.importorskip("litellm")
    import asyncio
    import types

    from pii_guardrail.adapters import KoreanPIIGuardrail

    core.set_engine(_BlockingEngine())
    try:
        guard = KoreanPIIGuardrail()
        msg = types.SimpleNamespace(content="raw model output", tool_calls=None)
        resp = types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])
        out = asyncio.run(guard.async_post_call_success_hook({}, None, resp))
        assert out.choices[0].message.content == guard._OUTPUT_BLOCKED_MSG
    finally:
        core.set_engine(None)


def test_litellm_post_call_fail_closed_on_engine_error():
    pytest.importorskip("litellm")
    import asyncio
    import types

    from pii_guardrail.adapters import KoreanPIIGuardrail

    core.set_engine(_FailingEngine())
    try:
        guard = KoreanPIIGuardrail()  # PII_FAIL_OPEN unset → fail-closed
        msg = types.SimpleNamespace(content="raw model output", tool_calls=None)
        resp = types.SimpleNamespace(choices=[types.SimpleNamespace(message=msg)])
        out = asyncio.run(guard.async_post_call_success_hook({}, None, resp))
        assert out.choices[0].message.content == guard._OUTPUT_BLOCKED_MSG
    finally:
        core.set_engine(None)
