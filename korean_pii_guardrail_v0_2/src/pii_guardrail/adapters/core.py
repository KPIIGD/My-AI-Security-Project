"""Gateway-agnostic engine + facade for the Korean PII Guardrail.

Every gateway adapter — the LiteLLM hook, the HTTP sidecar, the Guardrails AI
validator, the OpenAI-compatible reverse proxy, the Portkey webhook, the Azure
APIM policy — funnels through ONE entry point here. That keeps detection /
masking behaviour and the project's no-raw-PII boundary identical everywhere.

There are exactly two attachment primitives:

  - in-process : ``import`` and call :func:`scan` / :func:`mask_text` directly.
                 No HTTP. Used by the Guardrails AI validator and any code embed.
  - HTTP       : run the sidecar (:func:`pii_guardrail.adapters.sidecar.create_app`)
                 and POST text to ``/v1/pii/apply``. Used by LiteLLM, Portkey,
                 Azure APIM, the reverse proxy, and anything network-attached.

This module has **no** heavy third-party dependency (no fastapi / httpx / torch).
The real NER v3 model is loaded lazily and only when ``NER_MODEL_PATH`` is set;
otherwise the pipeline runs with regex + dictionary detectors (still masks
RRN / phone / card / account / secret / Korean-keyword PII) and reports
``ner_mode="mock-ner"`` so the degraded mode is always visible in logs.

Environment variables:
  PII_CONFIG_DIR    v0.2 configs dir. Auto-located from the package if unset.
  NER_MODEL_PATH    NER v3 model dir. If unset, NER is not loaded (regex/dict only).
  PII_ALLOW_MOCK    "1" → fall back to mock if real NER load fails. Default
                    fail-closed (raise) when NER_MODEL_PATH is set but unusable.
"""
from __future__ import annotations

import copy
import os
import threading
from pathlib import Path
from typing import Any, Optional

from ..pipeline import GuardrailPipeline, default_components
from ..schema import GuardrailRequest


class NERLoadError(RuntimeError):
    """Real NER v3 load failed and PII_ALLOW_MOCK is not set (fail-closed)."""


class PIIBlocked(Exception):
    """Raised by :func:`mask_text` / :func:`mask_openai_messages` when the
    policy router blocks the text. ``summary`` carries the no-raw-PII detection
    summary so adapters can log/return it without leaking raw PII."""

    def __init__(self, summary: dict) -> None:
        self.summary = summary
        super().__init__("blocked by Korean PII guardrail")


def _env_config_dir() -> Optional[str]:
    """Return the configs dir: explicit env > packaged ``configs/`` > None.

    ``None`` lets :func:`default_components` use built-in defaults so the
    library still works without the YAML config bundle.
    """
    explicit = os.environ.get("PII_CONFIG_DIR")
    if explicit:
        return explicit
    # src/pii_guardrail/adapters/core.py -> parents[3] == repo root
    candidate = Path(__file__).resolve().parents[3] / "configs"
    if candidate.is_dir():
        return str(candidate)
    return None


class GuardrailEngine:
    """Thin wrapper around :class:`GuardrailPipeline` that records the NER mode
    and exposes the single :meth:`scan` used by every adapter.

    Stateless w.r.t. requests — one instance is safe to share across threads
    and concurrent requests (the v0.2 detectors are stateless)."""

    def __init__(self, pipeline: GuardrailPipeline, ner_mode: str) -> None:
        self.pipeline = pipeline
        self.ner_mode = ner_mode

    @classmethod
    def from_env(cls) -> "GuardrailEngine":
        config_dir = _env_config_dir()
        model_path = os.environ.get("NER_MODEL_PATH", "").strip()
        allow_mock = os.environ.get("PII_ALLOW_MOCK", "0") == "1"

        if model_path and Path(model_path).exists():
            try:
                from ..ner.finetuned_wrapper import FinetunedNERDetector

                calib = Path(model_path) / "calibration.json"
                ner = FinetunedNERDetector(
                    model_path=model_path,
                    calibration_path=str(calib) if calib.exists() else None,
                )
                pipe = GuardrailPipeline(
                    default_components(config_dir=config_dir, ner_detector=ner)
                )
                pipe.process(GuardrailRequest(text="홍길동 010-1234-5678"))  # warmup
                return cls(pipe, f"real-ner-v3 ({model_path})")
            except Exception as exc:  # noqa: BLE001 — fail-closed decision
                if not allow_mock:
                    raise NERLoadError(
                        f"real NER v3 load failed: {exc}. "
                        "set PII_ALLOW_MOCK=1 to fall back to mock."
                    ) from exc
                pipe = GuardrailPipeline(default_components(config_dir=config_dir))
                return cls(pipe, f"mock-ner (real load failed: {exc})")

        if model_path and not allow_mock:
            raise NERLoadError(
                f"NER_MODEL_PATH set but not found: {model_path}. "
                "set PII_ALLOW_MOCK=1 to fall back to mock."
            )

        pipe = GuardrailPipeline(default_components(config_dir=config_dir))
        mode = "mock-ner" if config_dir else "mock-ner (built-in defaults)"
        return cls(pipe, mode)

    def scan(
        self,
        text: str,
        *,
        scan_stage: str = "input",
        policy_profile: str = "strict",
        output_target: Optional[str] = None,
        request_id: Optional[str] = None,
    ) -> dict:
        if not text or not text.strip():
            return {
                "blocked": False,
                "masked_text": text,
                "spans": [],
                "metrics": {},
                "ner_mode": self.ner_mode,
                "skipped": True,
            }
        kwargs: dict[str, Any] = {
            "text": text,
            "scan_stage": scan_stage,
            "policy_profile": policy_profile,
        }
        if output_target:
            kwargs["output_target"] = output_target
        if request_id:
            kwargs["request_id"] = request_id
        out = self.pipeline.process(GuardrailRequest(**kwargs)).to_dict()
        out["ner_mode"] = self.ner_mode
        return out


# ── process-wide singleton ────────────────────────────────────────────────
_ENGINE: Optional[GuardrailEngine] = None
_LOCK = threading.Lock()


def get_engine() -> GuardrailEngine:
    """Return the process-wide engine, building it from env on first use."""
    global _ENGINE
    if _ENGINE is None:
        with _LOCK:
            if _ENGINE is None:
                _ENGINE = GuardrailEngine.from_env()
    return _ENGINE


def set_engine(engine: Optional[GuardrailEngine]) -> None:
    """Override (or reset, with ``None``) the process-wide engine.

    Useful for tests and for callers that build a custom-wired pipeline."""
    global _ENGINE
    _ENGINE = engine


# ── facade functions every adapter calls ──────────────────────────────────
def scan(
    text: str,
    *,
    scan_stage: str = "input",
    policy_profile: str = "strict",
    output_target: Optional[str] = None,
    request_id: Optional[str] = None,
    engine: Optional[GuardrailEngine] = None,
) -> dict:
    """Scan one text. Returns ``GuardrailResponse.to_dict()`` plus ``ner_mode``.

    Empty/whitespace text returns a benign passthrough dict."""
    return (engine or get_engine()).scan(
        text,
        scan_stage=scan_stage,
        policy_profile=policy_profile,
        output_target=output_target,
        request_id=request_id,
    )


def public_summary(result: dict, *, role: str = "user", stage: str = "input") -> dict:
    """Build a no-raw-PII detection summary for logging / metadata.

    Contains only type / action / risk_level / HMAC value_hash — never raw text.
    """
    spans = result.get("spans") or []
    metrics = result.get("metrics") or {}
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


def mask_text(
    text: str,
    *,
    stage: str = "input",
    policy_profile: str = "strict",
    role: str = "user",
    output_target: Optional[str] = None,
    engine: Optional[GuardrailEngine] = None,
) -> tuple[str, dict]:
    """Return ``(masked_or_original_text, summary)``.

    Pass ``output_target="external_output"`` for output-stage scans so the
    external-output policy boundary applies. Raises :class:`PIIBlocked`
    (carrying the summary) when the policy blocks."""
    result = scan(
        text,
        scan_stage=stage,
        policy_profile=policy_profile,
        output_target=output_target,
        engine=engine,
    )
    summary = public_summary(result, role=role, stage=stage)
    if result.get("blocked"):
        raise PIIBlocked(summary)
    masked = result.get("masked_text")
    return (masked if masked is not None else text), summary


def mask_openai_messages(
    messages: list,
    *,
    stage: str = "input",
    policy_profile: str = "strict",
    engine: Optional[GuardrailEngine] = None,
) -> tuple[list, list]:
    """Mask PII in an OpenAI-style ``messages`` list.

    Returns ``(masked_messages_copy, summaries)`` — the input is **not**
    mutated. Handles both string content and multimodal list content.
    Raises :class:`PIIBlocked` when any message blocks."""
    out = copy.deepcopy(messages)
    summaries: list[dict] = []
    for m in out:
        if not isinstance(m, dict):
            continue
        content = m.get("content")
        role = m.get("role", "user")
        if isinstance(content, str):
            masked, summ = mask_text(
                content, stage=stage, policy_profile=policy_profile, role=role, engine=engine
            )
            m["content"] = masked
            summaries.append(summ)
        elif isinstance(content, list):
            for part in content:
                if isinstance(part, dict) and isinstance(part.get("text"), str):
                    masked, summ = mask_text(
                        part["text"],
                        stage=stage,
                        policy_profile=policy_profile,
                        role=role,
                        engine=engine,
                    )
                    part["text"] = masked
                    summaries.append(summ)
    return out, summaries
