"""Korean PII Guardrail — sidecar service.

LiteLLM 게이트웨이가 HTTP로 호출하는 PII 탐지/마스킹 사이드카.
v0.2 GuardrailPipeline(real NER v3 탑재)을 그대로 래핑한다.

엔드포인트:
  GET  /health        → 기동/NER 모드 확인
  POST /v1/pii/apply  → {text, policy_profile?, scan_stage?} → GuardrailResponse.to_dict()

설계 원칙(프로젝트 no-raw-PII 경계):
  - 응답은 GuardrailResponse.to_dict() 그대로. PublicPIISpan 은 원문 없이
    (start,end,length,type,score,action,value_hash[HMAC]) 만 담아 raw PII 비노출.
  - 마스킹된 텍스트(masked_text)만 LLM 입력으로 전달된다.

환경변수:
  PII_CONFIG_DIR   v0.2 configs 디렉터리 (default /pkg/configs)
  NER_MODEL_PATH   NER v3 모델 디렉터리 (default /models/ner_v3)
  PII_ALLOW_MOCK   "1" 이면 real NER 로드 실패 시 mock 으로 fallback (기본 fail-closed)
"""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI
from pydantic import BaseModel

from pii_guardrail.pipeline import GuardrailPipeline, default_components
from pii_guardrail.schema import GuardrailRequest

CONFIG_DIR = os.environ.get("PII_CONFIG_DIR", "/pkg/configs")
NER_MODEL_PATH = os.environ.get("NER_MODEL_PATH", "/models/ner_v3")
ALLOW_MOCK = os.environ.get("PII_ALLOW_MOCK", "0") == "1"


class NERLoadError(RuntimeError):
    """real NER v3 로드 실패 (fail-closed)."""


def build_pipeline() -> tuple[GuardrailPipeline, str]:
    """real NER v3 를 탑재한 파이프라인을 만든다. 기본 fail-closed.

    데모(demo/app.py)의 build_pipeline 과 동일한 배선을 서버용으로 옮긴 것.
    """
    try:
        from pii_guardrail.ner.finetuned_wrapper import FinetunedNERDetector

        calib = Path(NER_MODEL_PATH) / "calibration.json"
        ner = FinetunedNERDetector(
            model_path=NER_MODEL_PATH,
            calibration_path=str(calib) if calib.exists() else None,
        )
        pipe = GuardrailPipeline(
            default_components(config_dir=CONFIG_DIR, ner_detector=ner)
        )
        # warmup — 모델 lazy-load 강제. 여기서 죽으면 real NER 미작동으로 간주.
        pipe.process(GuardrailRequest(text="홍길동 010-1234-5678"))
        return pipe, f"real-ner-v3 ({NER_MODEL_PATH})"
    except Exception as exc:  # noqa: BLE001 — fail-closed 판단용
        if not ALLOW_MOCK:
            raise NERLoadError(
                f"real NER v3 로드 실패: {exc}. "
                "mock 으로 강제 실행하려면 PII_ALLOW_MOCK=1 설정."
            ) from exc
        pipe = GuardrailPipeline(default_components(config_dir=CONFIG_DIR))
        return pipe, f"mock-ner (real 로드 실패: {exc})"


app = FastAPI(title="Korean PII Guardrail Sidecar", version="v0.2")
PIPELINE: GuardrailPipeline | None = None
NER_MODE: str = "(미초기화)"


@app.on_event("startup")
def _startup() -> None:
    global PIPELINE, NER_MODE
    PIPELINE, NER_MODE = build_pipeline()
    print(f"[sidecar] pipeline ready — NER: {NER_MODE}", flush=True)


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok" if PIPELINE is not None else "loading",
        "ner_mode": NER_MODE,
        "config_dir": CONFIG_DIR,
    }


class ApplyRequest(BaseModel):
    text: str
    policy_profile: str = "strict"
    scan_stage: str = "input"          # "input" | "output"
    output_target: str | None = None   # 예: "llm_input" | "llm_output"
    request_id: str | None = None


@app.post("/v1/pii/apply")
def apply(req: ApplyRequest) -> dict:
    if PIPELINE is None:  # startup 전 호출 방어
        return {"error": "pipeline not ready", "ner_mode": NER_MODE}

    kwargs: dict = {
        "text": req.text,
        "policy_profile": req.policy_profile,
        "scan_stage": req.scan_stage,
        "request_id": req.request_id,
    }
    if req.output_target:
        kwargs["output_target"] = req.output_target

    response = PIPELINE.process(GuardrailRequest(**kwargs))
    out = response.to_dict()
    out["ner_mode"] = NER_MODE
    return out
