"""Mock NER detector for pipeline integration tests.

This mock intentionally implements only simple deterministic examples. It is not a real NER model.
"""

from __future__ import annotations

from pii_guardrail.enums import EntityType, RiskLevel
from pii_guardrail.interfaces import PreprocessResult
from pii_guardrail.schema import GuardrailRequest, PIISpan


class MockNERDetector:
    detector_id = "mock_ner.v0"

    def detect(self, raw_text: str, preprocessed: PreprocessResult, request: GuardrailRequest) -> list[PIISpan]:
        spans: list[PIISpan] = []
        for name in ("홍길동", "김민수", "하늘"):
            idx = raw_text.find(name)
            if idx >= 0:
                spans.append(
                    PIISpan(
                        start=idx,
                        end=idx + len(name),
                        text=raw_text[idx : idx + len(name)],
                        entity_type=EntityType.PERSON_NAME,
                        score=0.65 if name == "하늘" else 0.85,
                        sources=("ner",),
                        risk_level=RiskLevel.P1,
                        detector_ids=(self.detector_id,),
                        reason_codes=("mock_ner.person", "mock_ner.uncalibrated"),
                    )
                )
        return spans
