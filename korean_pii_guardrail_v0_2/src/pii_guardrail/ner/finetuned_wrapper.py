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

_PERSON_ALLOWED_TRAILING_SUFFIXES = tuple(
    sorted(
        (
            "\ub2d8",
            "\uc528",
            "\uad70",
            "\uc591",
            "\uc774",
            "\uac00",
            "\uc740",
            "\ub294",
            "\uc744",
            "\ub97c",
            "\uc5d0\uac8c",
            "\ud55c\ud14c",
            "\uaed8\uc11c",
            "\uaed8",
            "\uc5d0\uc11c",
            "\uc73c\ub85c",
            "\ub85c",
            "\uc640",
            "\uacfc",
            "\uc774\ub791",
            "\ub791",
            "\ud558\uace0",
            "\ub3c4",
            "\ub9cc",
            "\ubd80\ud130",
            "\uae4c\uc9c0",
            "\ubcf4\ub2e4",
            "\ucc98\ub7fc",
            "\uc774\ub77c\uace0",
            "\ub77c\uace0",
            "\uc774\ub77c\ub294",
            "\ub77c\ub294",
            "\uc785\ub2c8\ub2e4",
            "\uc785\ub2c8\ub2e4.",
            "\ud300\uc7a5",
            "\uacfc\uc7a5",
            "\ubd80\uc7a5",
            "\ucc28\uc7a5",
            "\ub300\ub9ac",
            "\uc774\uc0ac",
            "\ub300\ud45c",
            "\uad50\uc218",
            "\ubcc0\ud638\uc0ac",
            "\uc758\uc0ac",
            "\uac04\ud638\uc0ac",
            "\uc0c1\ub2f4\uc0ac",
            "\uc6d0\uc7a5",
        ),
        key=len,
        reverse=True,
    )
)


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
            span = self._candidate_to_span(candidate, raw_text)
            if span is None:
                continue
            span.validate_against(raw_text)
            spans.append(span)
        return spans

    def _ensure_backend(self) -> Any:
        if self._backend is not None:
            return self._backend

        try:
            module = importlib.import_module("pii_guardrail.ner.owner_wrapper")
            detector_cls = getattr(module, "FinetunedKoreanNERDetector")
        except (ImportError, AttributeError) as exc:
            raise NERDependencyError(
                "Fine-tuned NER v3 runtime is unavailable. Install the optional 'ner' extra "
                "and ensure pii_guardrail.ner.owner_wrapper is importable, or inject a backend."
            ) from exc

        try:
            self._backend = detector_cls(
                model_path=self.model_path,
                calibration_path=self.calibration_path,
            )
        except TypeError:
            self._backend = detector_cls(model_path=self.model_path)
        return self._backend

    def _candidate_to_span(self, candidate: dict[str, Any] | PIISpan, raw_text: str) -> PIISpan | None:
        if isinstance(candidate, PIISpan):
            if candidate.entity_type not in set(NER_V3_LABEL_TO_ENTITY_TYPE.values()):
                return None
            if candidate.entity_type is EntityType.PERSON_NAME and not _is_valid_person_candidate(
                raw_text,
                candidate.start,
                candidate.end,
                candidate.text,
            ):
                return None
            return candidate

        entity_type = self._candidate_entity_type(candidate)
        if entity_type is None:
            return None
        start = int(candidate["start"])
        end = int(candidate["end"])
        candidate_text = str(candidate["text"])
        if entity_type is EntityType.PERSON_NAME and not _is_valid_person_candidate(
            raw_text,
            start,
            end,
            candidate_text,
        ):
            return None

        score = float(candidate["score"])
        reason_codes = tuple(candidate.get("reason_codes") or ("ner.argmax", "ner.softmax_mean"))
        threshold = self.thresholds.get(entity_type)
        if threshold is not None:
            threshold_reason = "ner.threshold_met" if score >= threshold else "ner.below_entity_threshold"
            reason_codes = (*reason_codes, threshold_reason)

        return PIISpan(
            start=start,
            end=end,
            text=candidate_text,
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


def _contains_whitespace(value: str) -> bool:
    return any(ch.isspace() for ch in value)


def _is_valid_person_candidate(raw_text: str, start: int, end: int, value: str) -> bool:
    if _contains_whitespace(value):
        return False
    if start < 0 or end > len(raw_text) or start >= end:
        return False
    if raw_text[start:end] != value:
        return False
    if start > 0 and _is_word_char(raw_text[start - 1]):
        return False

    trailing_word = _trailing_word_after(raw_text, end)
    if not trailing_word:
        return True
    return _is_allowed_person_suffix_chain(trailing_word)


def _trailing_word_after(raw_text: str, start: int) -> str:
    cursor = start
    while cursor < len(raw_text) and _is_word_char(raw_text[cursor]):
        cursor += 1
    return raw_text[start:cursor]


def _is_allowed_person_suffix_chain(value: str) -> bool:
    cursor = 0
    while cursor < len(value):
        for suffix in _PERSON_ALLOWED_TRAILING_SUFFIXES:
            if value.startswith(suffix, cursor):
                cursor += len(suffix)
                break
        else:
            return False
    return True


def _is_word_char(value: str) -> bool:
    return value == "_" or value.isalnum()
