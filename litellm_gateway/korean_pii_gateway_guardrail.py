"""Korean PII Guardrail — LiteLLM custom guardrail 훅.

LiteLLM 게이트웨이로 들어오는 요청/나가는 응답의 텍스트를 PII 사이드카
(http://pii-guardrail:8080) 로 보내 마스킹/차단한다. 무거운 NER(torch/모델
1.3GB)는 사이드카에 격리되어 있고, 이 훅은 HTTP 호출만 한다.

동작:
  - pre_call : 사용자 입력 메시지를 검사 → BLOCK 이면 요청 거부, 아니면 masked_text 로 치환
  - post_call: LLM 응답 텍스트를 검사 → masked_text 로 치환 (출력 방어)
  - 두 경우 모두 탐지 요약(원문 없이 type/action/risk/HMAC hash 만)을 metadata 에
    실어 LiteLLM UI / Langfuse 로그에 남긴다 (no-raw-PII 경계 준수).

config.yaml 등록:
  guardrails:
    - guardrail_name: "korean-pii"
      litellm_params:
        guardrail: korean_pii_gateway_guardrail.KoreanPIIGuardrail
        mode: "pre_call"
        default_on: true
"""
from __future__ import annotations

import os
from typing import Any, Optional

import httpx

from litellm.integrations.custom_guardrail import CustomGuardrail

SIDECAR_URL = os.environ.get("PII_SIDECAR_URL", "http://pii-guardrail:8080")
APPLY_PATH = "/v1/pii/apply"
TIMEOUT_S = float(os.environ.get("PII_SIDECAR_TIMEOUT", "10"))


class KoreanPIIGuardrail(CustomGuardrail):
    def __init__(self, **kwargs: Any) -> None:
        self.sidecar_url = SIDECAR_URL.rstrip("/") + APPLY_PATH
        # fail-closed: 사이드카 호출 실패 시 BLOCK (PII 가 그냥 새는 것보다 안전).
        # 데모/개발에서 통과시키고 싶으면 PII_FAIL_OPEN=1.
        self.fail_open = os.environ.get("PII_FAIL_OPEN", "0") == "1"
        super().__init__(**kwargs)

    # ── 사이드카 호출 ─────────────────────────────────────────
    async def _scan(self, text: str, *, scan_stage: str) -> Optional[dict]:
        if not text or not text.strip():
            return None
        payload = {"text": text, "policy_profile": "strict", "scan_stage": scan_stage}
        try:
            async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
                resp = await client.post(self.sidecar_url, json=payload)
                resp.raise_for_status()
                return resp.json()
        except Exception as exc:  # noqa: BLE001
            if self.fail_open:
                return None
            raise self._blocked(
                f"PII 가드레일 사이드카 호출 실패 (fail-closed): {type(exc).__name__}"
            ) from exc

    @staticmethod
    def _blocked(detail: str) -> Exception:
        """요청 차단용 예외. 가능하면 HTTP 400, 아니면 일반 예외."""
        try:
            from fastapi import HTTPException

            return HTTPException(status_code=400, detail=detail)
        except Exception:  # noqa: BLE001
            return Exception(detail)

    @staticmethod
    def _summary(result: dict, *, role: str, stage: str) -> dict:
        """metadata 로그용 요약 — 원문 없이 type/action/risk/HMAC hash 만."""
        spans = result.get("spans", []) or []
        metrics = result.get("metrics", {}) or {}
        return {
            "engine": "korean-pii-guardrail-v0.2",
            "ner_mode": result.get("ner_mode"),
            "stage": stage,
            "role": role,
            "blocked": result.get("blocked", False),
            "detected_span_count": metrics.get("detected_span_count"),
            "masked_span_count": metrics.get("masked_span_count"),
            "latency_ms": metrics.get("latency_ms"),
            "entities": [
                {
                    "type": s.get("entity_type"),
                    "action": s.get("action"),
                    "risk_level": s.get("risk_level"),
                    "value_hash": s.get("value_hash"),
                }
                for s in spans
            ],
        }

    @staticmethod
    def _log(data: dict, summary: dict) -> None:
        meta = data.setdefault("metadata", {})
        meta.setdefault("korean_pii_guardrail", []).append(summary)

    # ── 메시지 content 헬퍼 (string + multimodal list 모두 지원) ──
    @staticmethod
    def _iter_text_parts(content: Any):
        """(setter 가능한) 텍스트 조각을 (get, set) 형태로 순회."""
        if isinstance(content, str):
            yield content, None
        elif isinstance(content, list):
            for i, part in enumerate(content):
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    yield part["text"], i

    # ── pre_call: 입력 마스킹/차단 ───────────────────────────
    async def async_pre_call_hook(
        self,
        user_api_key_dict,
        cache,
        data: dict,
        call_type,
    ):
        messages = data.get("messages")
        if not messages:
            return data

        for m in messages:
            content = m.get("content")
            role = m.get("role", "user")
            # string content
            if isinstance(content, str):
                result = await self._scan(content, scan_stage="input")
                if result is None:
                    continue
                self._log(data, self._summary(result, role=role, stage="input"))
                if result.get("blocked"):
                    raise self._blocked(
                        "고위험 개인정보(PII) 다수 탐지로 요청이 차단되었습니다."
                    )
                if result.get("masked_text") is not None:
                    m["content"] = result["masked_text"]
            # multimodal list content
            elif isinstance(content, list):
                for idx, part in enumerate(content):
                    if not (isinstance(part, dict) and isinstance(part.get("text"), str)):
                        continue
                    result = await self._scan(part["text"], scan_stage="input")
                    if result is None:
                        continue
                    self._log(data, self._summary(result, role=role, stage="input"))
                    if result.get("blocked"):
                        raise self._blocked(
                            "고위험 개인정보(PII) 다수 탐지로 요청이 차단되었습니다."
                        )
                    if result.get("masked_text") is not None:
                        content[idx]["text"] = result["masked_text"]

        return data

    # ── post_call: 출력 마스킹 (방어적) ──────────────────────
    async def async_post_call_success_hook(
        self,
        data: dict,
        user_api_key_dict,
        response,
    ):
        try:
            choices = getattr(response, "choices", None)
            if not choices:
                return response
            for choice in choices:
                msg = getattr(choice, "message", None)
                content = getattr(msg, "content", None) if msg is not None else None
                if not isinstance(content, str) or not content.strip():
                    continue
                result = await self._scan(content, scan_stage="output")
                if result is None:
                    continue
                self._log(data, self._summary(result, role="assistant", stage="output"))
                if result.get("masked_text") is not None and not result.get("blocked"):
                    msg.content = result["masked_text"]
        except Exception:  # noqa: BLE001 — 출력 마스킹 실패가 응답 자체를 깨면 안 됨
            pass
        return response

    # ── apply_guardrail: Test Playground / /guardrails/apply_guardrail 용 ──
    # LiteLLM UI 의 "Test Guardrail" 버튼과 generic guardrail API 가 부르는 경로.
    # async_pre_call_hook 과 별개라 이걸 구현해야 Playground 에서도 마스킹된다.
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
        masked_texts = []
        for t in texts:
            if not isinstance(t, str) or not t.strip():
                masked_texts.append(t)
                continue
            result = await self._scan(t, scan_stage=stage)
            if result is None:
                masked_texts.append(t)
                continue
            self._log(request_data, self._summary(result, role="user", stage=stage))
            if result.get("blocked"):
                raise self._blocked(
                    "고위험 개인정보(PII) 다수 탐지로 요청이 차단되었습니다."
                )
            masked_texts.append(
                result["masked_text"] if result.get("masked_text") is not None else t
            )

        inputs["texts"] = masked_texts
        return inputs
