"""Placeholder for a future fine-tuned Korean NER wrapper."""

from __future__ import annotations

from pii_guardrail.interfaces import PreprocessResult
from pii_guardrail.schema import GuardrailRequest, PIISpan


class FinetunedNERDetector:
    detector_id = "ner.finetuned.placeholder"

    def __init__(self, model_path: str, label_mapping: dict[str, str]) -> None:
        self.model_path = model_path
        self.label_mapping = label_mapping

    def detect(self, raw_text: str, preprocessed: PreprocessResult, request: GuardrailRequest) -> list[PIISpan]:
        raise NotImplementedError(
            "Real NER integration is intentionally deferred until the deterministic core is stable."
        )
