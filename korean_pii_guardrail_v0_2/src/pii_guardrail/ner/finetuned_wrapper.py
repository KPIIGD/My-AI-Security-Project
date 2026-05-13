"""Adapter for the fine-tuned Korean PII NER v3 artifact.

The heavy model runtime is optional. This module keeps the package importable without
``transformers``/``torch`` and adapts the NER owner's wrapper output into PIISpan objects.
"""

from __future__ import annotations

import importlib
import json
from pathlib import Path
from typing import Any

from pii_guardrail.enums import EntityType, RiskLevel
from pii_guardrail.interfaces import PreprocessResult
from pii_guardrail.schema import GuardrailRequest, PIISpan


NER_V3_LABEL_TO_ENTITY_TYPE: dict[str, EntityType] = {
    "NAME": EntityType.PERSON_NAME,
    "ADDRESS": EntityType.ADDRESS_FULL,
    "ORG": EntityType.ORGANIZATION,
}

NER_V3_THRESHOLDS: dict[EntityType, float] = {
    EntityType.PERSON_NAME: 0.85,
    EntityType.ADDRESS_FULL: 0.80,
    EntityType.ORGANIZATION: 0.75,
}

NER_V3_RISK_LEVELS: dict[EntityType, RiskLevel] = {
    EntityType.PERSON_NAME: RiskLevel.P1,
    EntityType.ADDRESS_FULL: RiskLevel.P1,
    EntityType.ORGANIZATION: RiskLevel.P2,
}


class NERDependencyError(RuntimeError):
    """Raised when the optional real NER runtime or artifact is unavailable."""


class FinetunedNERDetector:
    detector_id = "ner.finetuned.klue-roberta-large-v3"

    def __init__(
        self,
        model_path: str = "vmaca123/korean-pii-ner-v3",
        calibration_path: str | None = None,
        label_mapping: dict[str, str] | None = None,
        thresholds: dict[EntityType | str, float] | None = None,
        backend: Any | None = None,
    ) -> None:
        self.model_path = model_path
        self.calibration_path = calibration_path
        self.label_mapping = self._coerce_label_mapping(label_mapping)
        self.thresholds = self._load_thresholds(calibration_path, thresholds)
        self._backend = backend

    @classmethod
    def _coerce_label_mapping(cls, label_mapping: dict[str, str] | None) -> dict[str, EntityType]:
        if label_mapping is None:
            return dict(NER_V3_LABEL_TO_ENTITY_TYPE)
        coerced: dict[str, EntityType] = {}
        for label, entity_type in label_mapping.items():
            normalized = cls._normalize_ner_label(label)
            try:
                coerced[normalized] = EntityType(entity_type)
            except ValueError:
                continue
        return coerced

    @staticmethod
    def _normalize_ner_label(label: str) -> str:
        if label.startswith(("B-", "I-")):
            return label[2:]
        return label

    @staticmethod
    def _coerce_thresholds(thresholds: dict[EntityType | str, float] | None) -> dict[EntityType, float]:
        merged = dict(NER_V3_THRESHOLDS)
        if thresholds is None:
            return merged
        for entity_type, value in thresholds.items():
            merged[EntityType(entity_type)] = float(value)
        return merged

    def _load_thresholds(
        self,
        calibration_path: str | None,
        thresholds: dict[EntityType | str, float] | None,
    ) -> dict[EntityType, float]:
        merged = self._coerce_thresholds(thresholds)
        if calibration_path is None:
            return merged

        path = Path(calibration_path)
        if not path.exists():
            return merged

        data = json.loads(path.read_text(encoding="utf-8"))
        raw_thresholds = data.get("per_entity_thresholds") or data.get("thresholds") or {}
        for entity_type, value in raw_thresholds.items():
            try:
                merged[EntityType(entity_type)] = float(value)
            except ValueError:
                continue
        return merged

    def detect(self, raw_text: str, preprocessed: PreprocessResult, request: GuardrailRequest) -> list[PIISpan]:
        backend = self._ensure_backend()
        raw_candidates = backend.detect(raw_text)

        spans: list[PIISpan] = []
        for candidate in raw_candidates:
            span = self._candidate_to_span(candidate)
            if span is None:
                continue
            span.validate_against(raw_text)
            spans.append(span)
        return spans

    def _ensure_backend(self) -> Any:
        if self._backend is not None:
            return self._backend

        try:
            module = importlib.import_module("ner_wrapper")
            detector_cls = getattr(module, "FinetunedKoreanNERDetector")
        except (ImportError, AttributeError) as exc:
            raise NERDependencyError(
                "Fine-tuned NER v3 runtime is unavailable. Install the optional 'ner' extra "
                "and provide the NER owner's ner_wrapper.py artifact or inject a backend."
            ) from exc

        try:
            self._backend = detector_cls(
                model_path=self.model_path,
                calibration_path=self.calibration_path,
            )
        except TypeError:
            self._backend = detector_cls(model_path=self.model_path)
        return self._backend

    def _candidate_to_span(self, candidate: dict[str, Any] | PIISpan) -> PIISpan | None:
        if isinstance(candidate, PIISpan):
            if candidate.entity_type not in set(NER_V3_LABEL_TO_ENTITY_TYPE.values()):
                return None
            return candidate

        entity_type = self._candidate_entity_type(candidate)
        if entity_type is None:
            return None

        score = float(candidate["score"])
        reason_codes = tuple(candidate.get("reason_codes") or ("ner.argmax", "ner.softmax_mean"))
        threshold = self.thresholds.get(entity_type)
        if threshold is not None:
            threshold_reason = "ner.threshold_met" if score >= threshold else "ner.below_entity_threshold"
            reason_codes = (*reason_codes, threshold_reason)

        return PIISpan(
            start=int(candidate["start"]),
            end=int(candidate["end"]),
            text=str(candidate["text"]),
            entity_type=entity_type,
            score=score,
            sources=tuple(candidate.get("sources") or ("ner",)),
            risk_level=self._candidate_risk_level(candidate, entity_type),
            detector_ids=tuple(candidate.get("detector_ids") or (self.detector_id,)),
            reason_codes=reason_codes,
        )

    def _candidate_entity_type(self, candidate: dict[str, Any]) -> EntityType | None:
        raw_entity_type = candidate.get("entity_type")
        if raw_entity_type is not None:
            try:
                entity_type = EntityType(raw_entity_type)
            except ValueError:
                return None
            if entity_type in set(NER_V3_LABEL_TO_ENTITY_TYPE.values()):
                return entity_type
            return None

        raw_label = candidate.get("label")
        if raw_label is None:
            return None
        return self.label_mapping.get(self._normalize_ner_label(str(raw_label)))

    @staticmethod
    def _candidate_risk_level(candidate: dict[str, Any], entity_type: EntityType) -> RiskLevel:
        raw_risk_level = candidate.get("risk_level")
        if raw_risk_level is not None:
            try:
                return RiskLevel(raw_risk_level)
            except ValueError:
                pass
        return NER_V3_RISK_LEVELS[entity_type]
