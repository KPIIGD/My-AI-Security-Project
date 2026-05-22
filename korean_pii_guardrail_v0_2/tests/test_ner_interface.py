import re
from pathlib import Path

import pytest

from pii_guardrail.enums import EntityType, RiskLevel
from pii_guardrail.interfaces import PreprocessResult
from pii_guardrail.ner import FinetunedNERDetector, NERDependencyError
from pii_guardrail.ner.finetuned_wrapper import NER_V3_LABEL_TO_ENTITY_TYPE, NER_V3_THRESHOLDS
from pii_guardrail.schema import GuardrailRequest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _preprocessed(raw_text: str) -> PreprocessResult:
    return PreprocessResult(
        raw_text=raw_text,
        normalized_text=raw_text,
        variants=(),
        norm_to_raw=tuple(range(len(raw_text))),
        raw_to_norm=tuple(range(len(raw_text))),
        sentences=(),
        eojeols=(),
    )


def test_ner_v3_direct_entity_mapping_is_minimal() -> None:
    assert NER_V3_LABEL_TO_ENTITY_TYPE == {
        "NAME": EntityType.PERSON_NAME,
        "ADDRESS": EntityType.ADDRESS_FULL,
        "ORG": EntityType.ORGANIZATION,
    }
    assert NER_V3_THRESHOLDS == {
        EntityType.PERSON_NAME: 0.85,
        EntityType.ADDRESS_FULL: 0.80,
        EntityType.ORGANIZATION: 0.75,
    }


def test_entity_config_routes_ner_only_to_v3_direct_entities() -> None:
    config_text = (PROJECT_ROOT / "configs" / "entities.yaml").read_text(encoding="utf-8")

    ner_routed_entities = set()
    current_entity = None
    for line in config_text.splitlines():
        entity_match = re.match(r"^  ([A-Z_]+):$", line)
        if entity_match:
            current_entity = entity_match.group(1)
            continue
        if current_entity and "detectors:" in line and "ner" in line:
            ner_routed_entities.add(current_entity)

    assert ner_routed_entities == {"PERSON_NAME", "ADDRESS_FULL", "ORGANIZATION"}


def test_scoring_config_records_ner_v3_threshold_metadata() -> None:
    scoring_text = (PROJECT_ROOT / "configs" / "scoring.yaml").read_text(encoding="utf-8")

    assert "ner_v3:" in scoring_text
    assert "direct_entities: [PERSON_NAME, ADDRESS_FULL, ORGANIZATION]" in scoring_text
    assert "calibration_status: uncalibrated_threshold_only" in scoring_text
    assert "PERSON_NAME: 0.85" in scoring_text
    assert "ADDRESS_FULL: 0.80" in scoring_text
    assert "ORGANIZATION: 0.75" in scoring_text


class FakeNERBackend:
    def detect(self, raw_text: str) -> list[dict[str, object]]:
        return [
            {
                "start": 0,
                "end": 3,
                "text": raw_text[0:3],
                "label": "B-NAME",
                "score": 0.91,
            },
            {
                "start": 4,
                "end": 8,
                "text": raw_text[4:8],
                "entity_type": "HOSPITAL",
                "score": 0.99,
            },
        ]


class WhitespacePersonBackend:
    def detect(self, raw_text: str) -> list[dict[str, object]]:
        text = "윤 신한"
        start = raw_text.index(text)
        return [
            {
                "start": start,
                "end": start + len(text),
                "text": text,
                "label": "B-NAME",
                "score": 0.96,
            }
        ]


class PrefixPersonBackend:
    def __init__(self, text: str) -> None:
        self.text = text

    def detect(self, raw_text: str) -> list[dict[str, object]]:
        start = raw_text.index(self.text)
        return [
            {
                "start": start,
                "end": start + len(self.text),
                "text": self.text,
                "label": "B-NAME",
                "score": 0.96,
            }
        ]


def test_finetuned_ner_adapter_converts_only_v3_direct_candidates() -> None:
    raw_text = "홍길동 서울병원"
    detector = FinetunedNERDetector(backend=FakeNERBackend())

    spans = detector.detect(raw_text, _preprocessed(raw_text), GuardrailRequest(text=raw_text))

    assert len(spans) == 1
    assert spans[0].start == 0
    assert spans[0].end == 3
    assert spans[0].text == "홍길동"
    assert spans[0].entity_type is EntityType.PERSON_NAME
    assert spans[0].risk_level is RiskLevel.P1
    assert spans[0].sources == ("ner",)
    assert "ner.threshold_met" in spans[0].reason_codes


def test_finetuned_ner_adapter_rejects_whitespace_person_candidates() -> None:
    raw_text = "하도윤 신한은행"
    detector = FinetunedNERDetector(backend=WhitespacePersonBackend())

    spans = detector.detect(raw_text, _preprocessed(raw_text), GuardrailRequest(text=raw_text))

    assert spans == []


def test_finetuned_ner_adapter_rejects_person_prefix_inside_compound_word() -> None:
    raw_text = "\ubbfc\uc218\uc804\uc790 \uc81c\ud488 \ubb38\uc758"
    detector = FinetunedNERDetector(backend=PrefixPersonBackend("\ubbfc\uc218"))

    spans = detector.detect(raw_text, _preprocessed(raw_text), GuardrailRequest(text=raw_text))

    assert spans == []


def test_finetuned_ner_adapter_rejects_person_syllable_inside_word() -> None:
    raw_text = "\uc9c0\uc131\uadf8\ub8f9 \uc2e0\uc785\uc0ac\uc6d0"
    detector = FinetunedNERDetector(backend=PrefixPersonBackend("\uc6d0"))

    spans = detector.detect(raw_text, _preprocessed(raw_text), GuardrailRequest(text=raw_text))

    assert spans == []


def test_finetuned_ner_adapter_keeps_person_before_honorific_josa() -> None:
    raw_text = "\ubc15\uc9c0\uc131\ub2d8\uaed8 \uc5f0\ub77d\uc8fc\uc138\uc694"
    detector = FinetunedNERDetector(backend=PrefixPersonBackend("\ubc15\uc9c0\uc131"))

    spans = detector.detect(raw_text, _preprocessed(raw_text), GuardrailRequest(text=raw_text))

    assert len(spans) == 1
    assert spans[0].text == "\ubc15\uc9c0\uc131"
    assert spans[0].entity_type is EntityType.PERSON_NAME


def test_finetuned_ner_adapter_requires_optional_backend_for_real_detection(monkeypatch: pytest.MonkeyPatch) -> None:
    def _missing_module(_name: str) -> object:
        raise ImportError("missing ner wrapper")

    monkeypatch.setattr("pii_guardrail.ner.finetuned_wrapper.importlib.import_module", _missing_module)
    detector = FinetunedNERDetector()
    raw_text = "홍길동"

    with pytest.raises(NERDependencyError):
        detector.detect(raw_text, _preprocessed(raw_text), GuardrailRequest(text=raw_text))
