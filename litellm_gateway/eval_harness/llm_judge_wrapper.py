# -*- coding: utf-8 -*-
"""
deepeval 용 LLM 래퍼 — 무료모델(Groq/OpenRouter via litellm) 백엔드.
deepeval G-Eval 등 메트릭을 $0 으로 돌리기 위함. deepeval 미설치면 import 안 해도 됨.

사용 예 (deepeval 설치 시):
    from eval_harness.llm_judge_wrapper import FreeJudge
    from deepeval.metrics import GEval
    from deepeval.test_case import LLMTestCase, LLMTestCaseParams

    metric = GEval(
        name="PII 탐지 정확성",
        criteria="출력이 입력의 PII 를 올바르게 탐지/마스킹했는가. raw PII 누출이 있으면 0점.",
        evaluation_params=[LLMTestCaseParams.INPUT, LLMTestCaseParams.ACTUAL_OUTPUT],
        model=FreeJudge("groq_gptoss"),
    )
"""
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))
from multi_ai.ask import _ask, MODELS, LABEL  # noqa: E402

try:
    from deepeval.models.base_model import DeepEvalBaseLLM
except Exception:  # deepeval 미설치 — 폴백 더미
    class DeepEvalBaseLLM:  # type: ignore
        pass


class FreeJudge(DeepEvalBaseLLM):
    """deepeval 호환 무료모델 judge. 동기/비동기 모두 _ask 로 위임."""

    def __init__(self, model_key: str = "groq_gptoss"):
        if model_key not in MODELS:
            raise ValueError(f"알 수 없는 모델 키: {model_key} (가능: {list(MODELS)})")
        self.model_key = model_key

    def load_model(self):
        return self

    def generate(self, prompt: str, schema=None) -> str:
        return _ask(self.model_key, prompt)

    async def a_generate(self, prompt: str, schema=None) -> str:
        return _ask(self.model_key, prompt)

    def get_model_name(self) -> str:
        return f"FreeJudge:{LABEL.get(self.model_key, self.model_key)}"
