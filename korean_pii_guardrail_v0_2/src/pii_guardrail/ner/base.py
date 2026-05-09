"""NER detector protocol.

NER outputs are candidates only. They must still pass boundary correction, context scoring,
span resolution, and policy routing.
"""

from __future__ import annotations

from typing import Protocol

from pii_guardrail.interfaces import PreprocessResult
from pii_guardrail.schema import GuardrailRequest, PIISpan


class BaseNERDetector(Protocol):
    detector_id: str

    def detect(self, raw_text: str, preprocessed: PreprocessResult, request: GuardrailRequest) -> list[PIISpan]:
        """Return NER candidate spans with raw-text offsets and calibrated confidence."""
        ...
