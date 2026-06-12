"""
Layer 4 — GPT-4o PII Judge
LiteLLM Custom Guardrail for Korean PII Detection in LLM outputs
"""

import os
import json
import time
import logging
from typing import Optional, List

from litellm.integrations.custom_guardrail import CustomGuardrail
from litellm.types.guardrails import PiiEntityType
from litellm.llms.custom_httpx.http_handler import (
    get_async_httpx_client,
    httpxSpecialProvider,
)

logger = logging.getLogger(__name__)


JUDGE_SYSTEM_PROMPT = """당신은 PII(개인식별정보) 탐지 전문가입니다.
주어진 텍스트에 개인식별정보가 포함되어 있는지 판정하세요.

## 탐지 대상 PII 유형
1. 한국 주민등록번호 (YYMMDD-NNNNNNN 형식 또는 변형)
2. 한국 전화번호 (010-XXXX-XXXX, 02-XXX-XXXX, 031-XXX-XXXX 등)
3. 한국인 이름 (2~4글자 한국어 성명)
4. 한국 주소 (시/구/동/로/길 포함)
5. 이메일 주소
6. 신용카드/체크카드 번호 (16자리)
7. 은행 계좌번호
8. 여권번호 (M/S + 8자리)
9. 운전면허번호
10. 사업자등록번호 (XXX-XX-XXXXX)
11. 외국인등록번호
12. 건강보험번호
13. 군번

## 특별 지시
- 자모 분해 형태 (예: ㅈㅜㅁㅣㄴ = 주민) 도 PII 맥락이면 탐지
- 초성 형태 (예: ㅈㅁㄷㄹㅂㅎ = 주민등록번호) 도 탐지
- 야민정음 (예: 즈민뜽록 = 주민등록) 도 탐지
- 코드스위칭 (예: jumin deungrok = 주민등록) 도 탐지
- 부분 마스킹 (예: 010-****-5678) 도 탐지
- 숫자+문맥 조합으로 PII 추론 가능한 경우도 포함

## 응답 형식
반드시 아래 JSON 형식만 출력하세요. 다른 텍스트는 절대 포함하지 마세요.
{
  "contains_pii": true,
  "confidence": 0.95,
  "entities": [
    {
      "type": "KR_RRN",
      "value": "탐지된 값",
      "confidence": 0.98
    }
  ],
  "reasoning": "판정 근거 한 줄"
}

PII가 없으면:
{
  "contains_pii": false,
  "confidence": 0.95,
  "entities": [],
  "reasoning": "PII 미발견"
}"""

JUDGE_USER_PROMPT = """아래 텍스트에서 PII를 탐지하세요:

---
{text}
---"""


class GPT4oPIIJudge(CustomGuardrail):
    """Layer 4 — GPT-4o/GPT-4o-mini PII Judge"""

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: Optional[str] = None,
        **kwargs,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.api_base = api_base or "https://api.openai.com/v1"
        self.model = os.getenv("PII_JUDGE_MODEL", "gpt-4o-mini")
        self.block_threshold = float(os.getenv("PII_JUDGE_THRESHOLD", "0.7"))
        self.max_tokens = int(os.getenv("PII_JUDGE_MAX_TOKENS", "1000"))

        logger.info(
            f"[Layer4] GPT-4o PII Judge initialized | "
            f"model={self.model} | threshold={self.block_threshold}"
        )

        super().__init__(**kwargs)

    async def apply_guardrail(self, **kwargs):
        """LiteLLM /guardrails/apply_guardrail API 호환."""
        inputs = kwargs.get("inputs", None)
        text = kwargs.get("text", "")

        texts = []
        if inputs is not None:
            if isinstance(inputs, dict) and "texts" in inputs:
                texts = list(inputs["texts"])
            elif isinstance(inputs, str):
                texts = [inputs]
        elif text:
            texts = [text]

        if not texts:
            if inputs is not None:
                return inputs if isinstance(inputs, dict) else {"texts": []}
            return {"texts": []}

        result_texts = []
        for t in texts:
            if not t or not t.strip() or len(t.strip()) < 5:
                result_texts.append(t)
                continue

            try:
                result = await self._call_judge(t)
                self._log_result(result, t)

                if self._should_block(result):
                    raise Exception(self._format_block_message(result))

                result_texts.append(t)

            except Exception as e:
                if "[Layer4 PII Judge]" in str(e):
                    raise
                logger.error(f"[Layer4] Judge error (fail-open): {e}")
                result_texts.append(t)

        return {"texts": result_texts}

    async def async_post_call_success_hook(
        self,
        data: dict,
        user_api_key_dict,
        response,
    ):
        """post_call 모드에서 LLM 응답 후 호출."""
        response_text = self._extract_response_text(response)

        if not response_text or len(response_text.strip()) < 5:
            return

        try:
            result = await self._call_judge(response_text)
            self._log_result(result, response_text)

            if self._should_block(result):
                raise Exception(self._format_block_message(result))

        except Exception as e:
            if "[Layer4 PII Judge]" in str(e):
                raise
            logger.error(f"[Layer4] post_call Judge error (fail-open): {e}")

    def _extract_response_text(self, response) -> str:
        try:
            if hasattr(response, "choices") and response.choices:
                choice = response.choices[0]
                if hasattr(choice, "message") and hasattr(choice.message, "content"):
                    return choice.message.content or ""
                if hasattr(choice, "text"):
                    return choice.text or ""
            if isinstance(response, dict):
                choices = response.get("choices", [])
                if choices:
                    message = choices[0].get("message", {})
                    return message.get("content", "") if isinstance(message, dict) else ""
            return str(response)
        except Exception as e:
            logger.warning(f"[Layer4] Failed to extract response text: {e}")
            return ""

    def _should_block(self, result: dict) -> bool:
        return (
            result.get("contains_pii", False)
            and result.get("confidence", 0) >= self.block_threshold
        )

    def _format_block_message(self, result: dict) -> str:
        entities_summary = ", ".join(
            f"{e.get('type', 'UNKNOWN')}({e.get('confidence', 0):.2f})"
            for e in result.get("entities", [])
        )
        return (
            f"[Layer4 PII Judge] PII detected in output | "
            f"model={self.model} | "
            f"confidence={result.get('confidence')} | "
            f"entities=[{entities_summary}] | "
            f"reason={result.get('reasoning', 'N/A')}"
        )

    def _log_result(self, result: dict, text: str):
        logger.info(
            f"[Layer4] Judge result | "
            f"contains_pii={result.get('contains_pii')} | "
            f"confidence={result.get('confidence')} | "
            f"entities={len(result.get('entities', []))} | "
            f"model={self.model} | "
            f"text_len={len(text)}"
        )

    async def _call_judge(self, text: str) -> dict:
        client = get_async_httpx_client(
            llm_provider=httpxSpecialProvider.GuardrailCallback
        )

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }

        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": JUDGE_SYSTEM_PROMPT},
                {"role": "user", "content": JUDGE_USER_PROMPT.format(text=text)},
            ],
            "max_tokens": self.max_tokens,
            "temperature": 0,
            "response_format": {"type": "json_object"},
        }

        response = await client.post(
            f"{self.api_base}/chat/completions",
            headers=headers,
            json=payload,
            timeout=30.0,
        )

        if response.status_code != 200:
            raise Exception(
                f"OpenAI API error: {response.status_code} - {response.text}"
            )

        data = response.json()
        content = data["choices"][0]["message"]["content"]

        content = content.strip()
        if content.startswith("```"):
            content = content.split("\n", 1)[1] if "\n" in content else content
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

        try:
            result = json.loads(content)
        except json.JSONDecodeError:
            logger.warning(f"[Layer4] JSON parse failed: {content[:200]}")
            result = {
                "contains_pii": False,
                "confidence": 0,
                "entities": [],
                "reasoning": "JSON parse error — defaulting to safe",
            }

        return result
