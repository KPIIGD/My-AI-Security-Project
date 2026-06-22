"""LiteLLM custom guardrail hook.

Attach the Korean PII guardrail to a LiteLLM proxy. Two modes:

  - in-process (default): the hook calls the in-process engine directly.
  - HTTP sidecar: set ``PII_SIDECAR_URL`` to isolate the heavy NER model in a
    separate container; the hook then POSTs to ``/v1/pii/apply``.

Behaviour:
  - pre_call  : mask/block user input messages.
  - post_call : mask LLM output text (defensive).
  - apply_guardrail : the path the LiteLLM "Test Guardrail" playground and the
    generic ``/guardrails/apply_guardrail`` API use.

All paths log a no-raw-PII summary into ``data["metadata"]`` for the LiteLLM
UI / Langfuse, and are fail-closed (set ``PII_FAIL_OPEN=1`` to pass on errors).

config.yaml:
    guardrails:
      - guardrail_name: "korean-pii"
        litellm_params:
          guardrail: pii_guardrail.adapters.litellm_hook.KoreanPIIGuardrail
          mode: "pre_call"
          default_on: true

``litellm`` is an optional dep: pip install korean-pii-guardrail[litellm]
"""
from __future__ import annotations

import asyncio
import os
from typing import Any, Optional

from .core import public_summary
from .core import scan as _scan_inproc

SIDECAR_URL = os.environ.get("PII_SIDECAR_URL")  # set → HTTP mode, else in-process
APPLY_PATH = "/v1/pii/apply"
TIMEOUT_S = float(os.environ.get("PII_SIDECAR_TIMEOUT", "10"))

try:
    from litellm.integrations.custom_guardrail import CustomGuardrail
except Exception as exc:  # noqa: BLE001
    raise ImportError(
        "litellm is required for KoreanPIIGuardrail. "
        "install: pip install korean-pii-guardrail[litellm]"
    ) from exc


class KoreanPIIGuardrail(CustomGuardrail):
    # Shown to the end user when the model OUTPUT is blocked — never the raw text.
    _OUTPUT_BLOCKED_MSG = "[응답이 개인정보 보호 정책에 의해 차단되었습니다.]"

    def __init__(self, **kwargs: Any) -> None:
        self.sidecar_url = (
            SIDECAR_URL.rstrip("/") + APPLY_PATH if SIDECAR_URL else None
        )
        # fail-closed: a guardrail failure BLOCKs rather than leak PII.
        self.fail_open = os.environ.get("PII_FAIL_OPEN", "0") == "1"
        super().__init__(**kwargs)

    # ── scan via sidecar (HTTP) or engine (in-process) ────────────────────
    async def _scan(
        self, text: str, *, scan_stage: str, output_target: Optional[str] = None
    ) -> Optional[dict]:
        if not text or not text.strip():
            return None
        if self.sidecar_url:
            import httpx

            payload = {
                "text": text,
                "policy_profile": "strict",
                "scan_stage": scan_stage,
            }
            if output_target:
                payload["output_target"] = output_target
            try:
                async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
                    resp = await client.post(self.sidecar_url, json=payload)
                    resp.raise_for_status()
                    return resp.json()
            except Exception as exc:  # noqa: BLE001
                if self.fail_open:
                    return None
                raise self._blocked(
                    f"PII guardrail sidecar call failed (fail-closed): {type(exc).__name__}"
                ) from exc
        # in-process — offload the CPU-bound pipeline off the event loop so a
        # busy proxy doesn't serialize every request / stall health checks.
        try:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None,
                lambda: _scan_inproc(
                    text,
                    scan_stage=scan_stage,
                    policy_profile="strict",
                    output_target=output_target,
                ),
            )
        except Exception as exc:  # noqa: BLE001
            if self.fail_open:
                return None
            raise self._blocked(
                f"PII guardrail engine failed (fail-closed): {type(exc).__name__}"
            ) from exc

    @staticmethod
    def _blocked(detail: str) -> Exception:
        try:
            from fastapi import HTTPException

            return HTTPException(status_code=400, detail=detail)
        except Exception:  # noqa: BLE001
            return Exception(detail)

    @staticmethod
    def _log(data: dict, summary: dict) -> None:
        meta = data.setdefault("metadata", {})
        meta.setdefault("korean_pii_guardrail", []).append(summary)

    # ── pre_call: input mask/block ────────────────────────────────────────
    async def async_pre_call_hook(self, user_api_key_dict, cache, data: dict, call_type):
        messages = data.get("messages")
        if not messages:
            return data
        for m in messages:
            content = m.get("content")
            role = m.get("role", "user")
            if isinstance(content, str):
                result = await self._scan(content, scan_stage="input")
                if result is None:
                    continue
                self._log(data, public_summary(result, role=role, stage="input"))
                if result.get("blocked"):
                    raise self._blocked("고위험 개인정보(PII) 다수 탐지로 요청이 차단되었습니다.")
                if result.get("masked_text") is not None:
                    m["content"] = result["masked_text"]
            elif isinstance(content, list):
                for idx, part in enumerate(content):
                    if not (isinstance(part, dict) and isinstance(part.get("text"), str)):
                        continue
                    result = await self._scan(part["text"], scan_stage="input")
                    if result is None:
                        continue
                    self._log(data, public_summary(result, role=role, stage="input"))
                    if result.get("blocked"):
                        raise self._blocked(
                            "고위험 개인정보(PII) 다수 탐지로 요청이 차단되었습니다."
                        )
                    if result.get("masked_text") is not None:
                        content[idx]["text"] = result["masked_text"]
        return data

    # ── post_call: output mask (fail-closed) ──────────────────────────────
    # scan_stage="output" uses output_target="external_output" so the policy's
    # external-output boundary (e.g. block API_KEY_SECRET) applies on the way out.
    # A scan failure or a BLOCK decision REDACTS the content — it never returns
    # the raw model output (unless PII_FAIL_OPEN=1).
    async def async_post_call_success_hook(self, data: dict, user_api_key_dict, response):
        choices = getattr(response, "choices", None)
        if not choices:
            return response
        for choice in choices:
            msg = getattr(choice, "message", None)
            if msg is None:
                continue
            content = getattr(msg, "content", None)
            if isinstance(content, str) and content.strip():
                try:
                    result = await self._scan(
                        content, scan_stage="output", output_target="external_output"
                    )
                except Exception:  # noqa: BLE001 — fail-closed: never leak raw output
                    if not self.fail_open:
                        msg.content = self._OUTPUT_BLOCKED_MSG
                else:
                    if result is not None:
                        self._log(
                            data, public_summary(result, role="assistant", stage="output")
                        )
                        if result.get("blocked"):
                            msg.content = self._OUTPUT_BLOCKED_MSG
                        elif result.get("masked_text") is not None:
                            msg.content = result["masked_text"]
            # tool-call arguments can carry PII too
            await self._mask_tool_calls(getattr(msg, "tool_calls", None))
        return response

    async def _mask_tool_calls(self, tool_calls) -> None:
        """Mask PII in tool-call argument strings (fail-closed)."""
        for tc in tool_calls or []:
            fn = getattr(tc, "function", None)
            args = getattr(fn, "arguments", None) if fn is not None else None
            if not isinstance(args, str) or not args.strip():
                continue
            try:
                result = await self._scan(
                    args, scan_stage="output", output_target="external_output"
                )
            except Exception:  # noqa: BLE001 — fail-closed
                if not self.fail_open:
                    fn.arguments = "{}"
                continue
            if result is None:
                continue
            if result.get("blocked"):
                fn.arguments = "{}"
            elif result.get("masked_text") is not None:
                fn.arguments = result["masked_text"]

    # ── apply_guardrail: Test Playground / generic guardrail API ──────────
    async def apply_guardrail(
        self,
        inputs: dict,
        request_data: dict,
        input_type: str,
        logging_obj=None,
    ) -> dict:
        texts = inputs.get("texts") if isinstance(inputs, dict) else None
        if not texts:
            return inputs
        stage = "output" if input_type == "response" else "input"
        target = "external_output" if stage == "output" else None
        masked_texts = []
        for t in texts:
            if not isinstance(t, str) or not t.strip():
                masked_texts.append(t)
                continue
            result = await self._scan(t, scan_stage=stage, output_target=target)
            if result is None:
                masked_texts.append(t)
                continue
            self._log(request_data, public_summary(result, role="user", stage=stage))
            if result.get("blocked"):
                raise self._blocked("고위험 개인정보(PII) 다수 탐지로 요청이 차단되었습니다.")
            masked_texts.append(
                result["masked_text"] if result.get("masked_text") is not None else t
            )
        inputs["texts"] = masked_texts
        return inputs
