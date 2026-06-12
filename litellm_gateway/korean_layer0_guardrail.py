"""
Layer 0 — Korean PII Normalizer + Detector Guardrail
=====================================================
LiteLLM CustomGuardrail (pre_call) 래퍼.

동작:
  1. 입력 텍스트를 KoreanNormalizer로 정규화 (변이 공격 복원)
  2. 정규화된 텍스트를 KoreanPIIDetector로 추가 탐지
  3. 탐지된 PII가 있으면 차단 (BLOCK) 또는 마스킹 (MASK)

config.yaml에 등록:
  guardrails:
    - guardrail_name: "korean-layer0"
      litellm_params:
        guardrail: korean_layer0_guardrail.KoreanLayer0Guard
        mode: "pre_call"

Usage standalone:
  python korean_layer0_guardrail.py  # 데모 실행
"""

import traceback
from typing import Optional

from korean_normalizer import KoreanNormalizer
from korean_pii_detector import KoreanPIIDetector


# ═══════════════════════════════════════════════════════════
# Layer 0 Core Logic (LiteLLM 독립 사용 가능)
# ═══════════════════════════════════════════════════════════

class KoreanLayer0:
    """
    한국어 PII 방어 Layer 0.
    1단계: 정규화 (변이 복원)
    2단계: 키워드/패턴 탐지 (텍스트형 PII)
    """

    def __init__(self, mode="block", threshold=1):
        """
        Args:
            mode: "block" (PII 발견 시 차단) or "mask" (PII 마스킹 후 통과)
            threshold: 최소 탐지 건수 (이 이상이면 action 실행)
        """
        self.normalizer = KoreanNormalizer()
        self.detector = KoreanPIIDetector()
        self.mode = mode
        self.threshold = threshold

    def process(self, text: str) -> dict:
        """
        입력 텍스트를 처리.

        Returns:
            {
                "original": 원본,
                "normalized": 정규화된 텍스트,
                "findings": [PIIFinding, ...],
                "has_pii": bool,
                "action": "PASS" | "BLOCK" | "MASK",
                "output": 최종 출력 텍스트,
            }
        """
        # Step 1: 정규화
        normalized = self.normalizer.normalize(text)

        # Step 2: 탐지 (정규화된 텍스트에서)
        findings = self.detector.detect(normalized)

        # Step 3: Action 결정
        has_pii = len(findings) >= self.threshold

        if not has_pii:
            return {
                "original": text,
                "normalized": normalized,
                "findings": [],
                "has_pii": False,
                "action": "PASS",
                "output": normalized,  # 정규화된 텍스트로 교체 (downstream 가드레일 도움)
            }

        if self.mode == "block":
            finding_types = list(set(f.pii_type for f in findings))
            return {
                "original": text,
                "normalized": normalized,
                "findings": [{"type": f.pii_type, "value": f.value[:30],
                              "keyword": f.context_keyword} for f in findings],
                "has_pii": True,
                "action": "BLOCK",
                "output": None,
                "block_reason": f"Korean PII detected: {', '.join(finding_types)}",
            }
        else:  # mask
            masked = self.detector.mask(normalized)
            return {
                "original": text,
                "normalized": normalized,
                "findings": [{"type": f.pii_type, "value": f.value[:30],
                              "keyword": f.context_keyword} for f in findings],
                "has_pii": True,
                "action": "MASK",
                "output": masked,
            }


# ═══════════════════════════════════════════════════════════
# LiteLLM GuardrailCallback 래퍼
# ═══════════════════════════════════════════════════════════

from litellm.integrations.custom_guardrail import CustomGuardrail
from litellm.types.guardrails import GuardrailEventHooks


class KoreanLayer0Guard(CustomGuardrail):
    """LiteLLM pre_call guardrail."""

    def __init__(self, **kwargs):
        self.layer0 = KoreanLayer0(mode="block", threshold=1)
        self.event_hook = GuardrailEventHooks.pre_call
        super().__init__(**kwargs)

    async def async_pre_call_hook(self, data, user_api_key_dict, call_type):
        """pre_call: LLM에 보내기 전 입력 검사."""
        try:
            messages = data.get("messages", [])
            if not messages:
                return data

            last_msg = messages[-1]
            content = last_msg.get("content", "")

            if not content or not isinstance(content, str):
                return data

            result = self.layer0.process(content)

            if result["action"] == "BLOCK":
                from litellm.exceptions import RejectedRequestError
                raise RejectedRequestError(
                    message=f"[Layer0] {result.get('block_reason', 'Korean PII detected')}",
                    model="",
                    llm_provider="",
                )
            elif result["action"] == "MASK":
                messages[-1]["content"] = result["output"]
                data["messages"] = messages
            elif result["action"] == "PASS":
                if result["normalized"] != content:
                    messages[-1]["content"] = result["normalized"]
                    data["messages"] = messages

            return data

        except Exception as e:
            if "RejectedRequestError" in str(type(e)):
                raise
            print(f"[Layer0] Error: {e}")
            traceback.print_exc()
            return data  # fail-open

    async def apply_guardrail(self, inputs, request_data, input_type, logging_obj=None):
        # GenericGuardrailAPIInputs is a TypedDict — access via dict API, never attributes.
        from fastapi import HTTPException
        try:
            texts = inputs.get("texts", []) if isinstance(inputs, dict) else []
            if not texts:
                return inputs

            processed_texts = []
            block_reasons = []
            for text in texts:
                result = self.layer0.process(text)
                if result["action"] == "BLOCK":
                    block_reasons.append(result.get("block_reason", "Korean PII detected"))
                    processed_texts.append(text)
                else:
                    processed_texts.append(result.get("output") or text)

            if block_reasons:
                raise HTTPException(
                    status_code=400,
                    detail=f"[Layer0] {'; '.join(block_reasons)}",
                )

            inputs["texts"] = processed_texts
            return inputs

        except HTTPException:
            raise
        except Exception as e:
            print(f"[Layer0] apply_guardrail error: {e}")
            traceback.print_exc()
            return inputs


# ═══════════════════════════════════════════════════════════
# CLI Demo
# ═══════════════════════════════════════════════════════════

def _demo():
    layer0 = KoreanLayer0(mode="block", threshold=1)

    tests = [
        # Layer 0 정규화 → downstream에서 잡힘
        ("L1 jamo",       "내 ㅈㅜㅁㅣㄴ번호는 900101-1234567"),
        ("L2 zwsp",       "주민번호: 9\u200B0\u200B0\u200B1\u200B0\u200B1-1234567"),
        ("L3 sep_dot",    "900101.1234567"),

        # Layer 0 detector가 직접 잡음 (기존 가드레일 우회 케이스)
        ("처방약",         "하도윤 처방 아토르바스타틴 20mg 1일 2회"),
        ("알레르기",       "김한결 견과류 알레르기"),
        ("세션토큰",       "Session SESSION_0bd6ijhj65y2joweuyyjfyvs"),
        ("사건번호",       "사건번호 2023가합30039"),
        ("연봉",          "최영희 연봉 7409만원"),
        ("가족",          "김영진 가족: 부: 박철대(1961), 모: 최정순(1976)"),
        ("GPS",           "위치 37.5170°N, 129.0520°E"),

        # 정상 텍스트 → PASS
        ("정상",          "오늘 회의는 3시에 시작합니다"),
        ("정상2",         "프로젝트 마감일은 다음 주 금요일입니다"),
    ]

    print("=" * 70)
    print("  Layer 0 — Korean PII Normalizer + Detector")
    print("=" * 70)

    for label, text in tests:
        result = layer0.process(text)
        action = result["action"]
        emoji = {"PASS": "✅", "BLOCK": "🔴", "MASK": "🟡"}[action]

        print(f"\n[{label}] {emoji} {action}")
        print(f"  IN : {text[:80]}")
        if result["normalized"] != text:
            print(f"  NRM: {result['normalized'][:80]}")
        if result["findings"]:
            for f in result["findings"]:
                print(f"  → {f['type']:15s} | {f['value']}")


if __name__ == "__main__":
    _demo()
