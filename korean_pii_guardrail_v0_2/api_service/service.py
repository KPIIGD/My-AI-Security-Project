"""Application service for the Korean PII Guardrail console API."""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any

from pii_guardrail.pipeline import GuardrailPipeline, default_components

from .crypto import decrypt_raw_text, encrypt_raw_text
from .database import AuditStore, build_log_record
from .models import ApplyRequestPayload, BatchRequestPayload, TraceRequestPayload

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "configs"
DEMO_DIR = PROJECT_ROOT / "demo"
if str(DEMO_DIR) not in sys.path:
    sys.path.insert(0, str(DEMO_DIR))

from pipeline_trace import trace_pipeline  # noqa: E402


class ConsoleService:
    def __init__(
        self,
        *,
        store: AuditStore,
        pipeline: GuardrailPipeline | None = None,
        ner_mode: str | None = None,
    ) -> None:
        if pipeline is None:
            pipeline, resolved_mode = build_pipeline_from_env()
        else:
            resolved_mode = ner_mode or "test-injected"
        self.store = store
        self.pipeline = pipeline
        self.ner_mode = resolved_mode

    @property
    def ner_enabled(self) -> bool:
        return self.ner_mode.startswith("real")

    def health(self) -> dict[str, Any]:
        return {
            "status": "ok",
            "version": "v0.2-single-turn",
            "loaded_profiles": ["strict"],
            "ner_enabled": self.ner_enabled,
            "ner_mode": self.ner_mode,
            "db_path": str(self.store.path),
            "raw_value_logged": False,
        }

    def apply(self, payload: ApplyRequestPayload) -> dict[str, Any]:
        request = payload.to_core()
        response = self.pipeline.process(request)
        response_payload = response.to_dict()
        encrypted_raw = None
        encrypted_key_hint = None
        if payload.encrypted_raw_logging_key:
            encrypted = encrypt_raw_text(
                payload.text,
                operator_key=payload.encrypted_raw_logging_key,
                request_id=str(response_payload["request_id"]),
                key_hint=payload.encrypted_raw_key_hint,
            )
            encrypted_raw = encrypted.envelope
            encrypted_key_hint = encrypted.key_hint
        record = build_log_record(
            response_payload,
            raw_text=payload.text,
            encrypted_raw_text=encrypted_raw,
            encrypted_raw_key_hint=encrypted_key_hint,
        )
        self.store.insert(record, raw_text=payload.text)
        response_payload["summary"] = record.summary()
        response_payload["encrypted_raw_available"] = encrypted_raw is not None
        response_payload["encrypted_raw_key_hint"] = encrypted_key_hint
        return response_payload

    def trace(self, payload: TraceRequestPayload) -> dict[str, Any]:
        request = payload.to_core()
        trace = trace_pipeline(self.pipeline, request, reveal_raw=False)
        data = trace.to_dict()
        data["masked_text"] = trace.masked_text
        data["reveal_raw"] = False
        data["raw_value_logged"] = False
        return data

    def batch(self, payload: BatchRequestPayload) -> dict[str, Any]:
        rows: list[dict[str, Any]] = []
        for idx, text in enumerate(payload.iter_texts()):
            apply_payload = payload.to_apply_payload(text)
            result = self.apply(apply_payload)
            summary = dict(result["summary"])
            summary["idx"] = idx
            rows.append(summary)
        metrics = self._aggregate_rows(rows)
        return {
            "n": len(rows),
            "records": rows,
            "aggregate": metrics,
            "raw_value_logged": False,
        }

    def decrypt_log(self, request_id: str, *, decrypt_key: str) -> dict[str, Any]:
        detail = self.store.get_log(request_id)
        if detail is None:
            raise KeyError("Log not found")
        envelope = self.store.get_encrypted_raw_text(request_id)
        if envelope is None:
            raise ValueError("암호화 원문 로그가 없습니다.")
        decrypted_text = decrypt_raw_text(
            envelope,
            operator_key=decrypt_key,
            request_id=request_id,
        )
        return {
            "request_id": request_id,
            "decrypted_text": decrypted_text,
            "encrypted_raw_available": True,
            "raw_value_logged": False,
        }

    def _aggregate_rows(self, rows: list[dict[str, Any]]) -> dict[str, Any]:
        total = len(rows)
        blocked = sum(1 for row in rows if row["blocked"])
        detected = sum(int(row["detected_span_count"]) for row in rows)
        masked = sum(int(row["masked_span_count"]) for row in rows)
        latency_values = [float(row["latency_ms"]) for row in rows]
        entity_counts: dict[str, int] = {}
        action_counts: dict[str, int] = {}
        risk_counts: dict[str, int] = {}
        for row in rows:
            _merge_counts(entity_counts, row.get("entity_counts") or {})
            _merge_counts(action_counts, row.get("action_counts") or {})
            _merge_counts(risk_counts, row.get("risk_counts") or {})
        return {
            "total_requests": total,
            "blocked_requests": blocked,
            "block_rate": (blocked / total) if total else 0.0,
            "detected_span_count": detected,
            "masked_span_count": masked,
            "average_latency_ms": (
                sum(latency_values) / len(latency_values) if latency_values else 0.0
            ),
            "entity_counts": entity_counts,
            "risk_counts": risk_counts,
            "action_counts": action_counts,
            "raw_value_logged": False,
        }


def build_pipeline_from_env() -> tuple[GuardrailPipeline, str]:
    use_real = _truthy(os.getenv("KPG_USE_REAL_NER", "0"))
    allow_mock = _truthy(os.getenv("KPG_ALLOW_MOCK_NER", "1"))
    if use_real:
        try:
            from pii_guardrail.ner.finetuned_wrapper import FinetunedNERDetector

            model_path = os.getenv("KPG_NER_MODEL_PATH", "vmaca123/korean-pii-ner-v3")
            ner = FinetunedNERDetector(model_path=model_path)
            return (
                GuardrailPipeline.from_config_dir(CONFIG_DIR, ner_detector=ner),
                f"real:{model_path}",
            )
        except Exception as exc:
            if not allow_mock:
                raise RuntimeError("real NER load failed for console API") from exc
            return (
                GuardrailPipeline(default_components(config_dir=CONFIG_DIR)),
                f"mock-fallback:{type(exc).__name__}",
            )
    return GuardrailPipeline(default_components(config_dir=CONFIG_DIR)), "mock"


def _merge_counts(target: dict[str, int], source: dict[str, int]) -> None:
    for key, value in source.items():
        target[str(key)] = target.get(str(key), 0) + int(value)


def _truthy(value: str) -> bool:
    return value.strip().lower() in {"1", "true", "yes", "on"}
