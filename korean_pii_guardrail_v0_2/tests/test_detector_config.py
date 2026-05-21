from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from pii_guardrail.detector_config import DetectorPolicy, load_detector_policy
from pii_guardrail.enums import EntityType
from pii_guardrail.pipeline import GuardrailPipeline
from pii_guardrail.preprocess import preprocess_text
from pii_guardrail.regex_detectors import (
    CreditCardRegexDetector,
    EmailRegexDetector,
    PhoneRegexDetector,
    RRNRegexDetector,
)
from pii_guardrail.schema import GuardrailRequest
from pii_guardrail.validators import validate_business_reg_no, validate_credit_card, validate_rrn


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _request(raw: str) -> GuardrailRequest:
    return GuardrailRequest(text=raw, request_id="req-detector-config-test")


def _detect(detector: object, raw: str):
    return detector.detect(preprocess_text(raw), _request(raw))


def test_load_detector_policy_reads_regex_entity_and_checksum_settings(tmp_path: Path) -> None:
    path = tmp_path / "detectors.yaml"
    path.write_text(
        """
version: v0.2-single-turn
regex_detectors:
  regex.email:
    enabled: false
entities:
  EMAIL:
    enabled: false
validators:
  CREDIT_CARD:
    checksum: warn
""".strip(),
        encoding="utf-8",
    )

    with pytest.warns(RuntimeWarning, match="high-risk entity EMAIL"):
        policy = load_detector_policy(path)

    assert policy.regex_detector_enabled("regex.email") is False
    assert policy.regex_detector_enabled("regex.phone") is True
    assert policy.entity_enabled(EntityType.EMAIL) is False
    assert policy.entity_enabled(EntityType.PHONE_MOBILE) is True
    assert policy.checksum_mode(EntityType.CREDIT_CARD) == "warn"
    assert policy.checksum_mode(EntityType.RRN) == "strict"


def test_load_detector_policy_warns_when_high_risk_entity_is_disabled(tmp_path: Path) -> None:
    path = tmp_path / "detectors.yaml"
    path.write_text(
        """
version: v0.2-single-turn
entities:
  RRN:
    enabled: false
""".strip(),
        encoding="utf-8",
    )

    with pytest.warns(RuntimeWarning, match="high-risk entity RRN"):
        policy = load_detector_policy(path)

    assert policy.entity_enabled(EntityType.RRN) is False


def test_load_detector_policy_warns_for_unknown_or_malformed_config(tmp_path: Path) -> None:
    path = tmp_path / "detectors.yaml"
    path.write_text(
        """
version: v0.2-single-turn
regex_detectors:
  regex.unknown:
    enabled: false
  regex.email:
    enable: false
entities:
  NOT_AN_ENTITY:
    enabled: false
validators:
  NOT_A_VALIDATOR:
    checksum: warn
""".strip(),
        encoding="utf-8",
    )

    with pytest.warns(RuntimeWarning) as warnings:
        policy = load_detector_policy(path)

    messages = "\n".join(str(warning.message) for warning in warnings)
    assert "Unknown regex_detectors key ignored: regex.unknown" in messages
    assert "Unknown setting ignored for regex_detectors.regex.email: enable" in messages
    assert "Unknown entities key ignored: NOT_AN_ENTITY" in messages
    assert "Unknown checksum validator ignored: NOT_A_VALIDATOR" in messages
    assert policy.regex_detector_enabled("regex.email") is True


def test_load_detector_policy_checksum_mode_error_includes_context(tmp_path: Path) -> None:
    path = tmp_path / "detectors.yaml"
    path.write_text(
        """
version: v0.2-single-turn
validators:
  CREDIT_CARD:
    checksum: maybe
""".strip(),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="CREDIT_CARD\\.checksum.*maybe"):
        load_detector_policy(path)


def test_regex_detector_policy_can_disable_detector_id() -> None:
    policy = DetectorPolicy(regex_detectors_enabled={"regex.email": False})
    detector = EmailRegexDetector(detector_policy=policy)

    assert _detect(detector, "email test@example.com") == []


def test_entity_policy_filters_detector_output_by_entity_type() -> None:
    policy = DetectorPolicy(entities_enabled={EntityType.PHONE_MOBILE: False})
    detector = PhoneRegexDetector(detector_policy=policy)

    spans = _detect(detector, "mobile 010-1234-5678 office 02-123-4567")

    assert [span.entity_type for span in spans] == [EntityType.PHONE_LANDLINE]
    assert spans[0].text == "02-123-4567"


def test_checksum_warn_mode_emits_lower_confidence_rrn_candidate() -> None:
    policy = DetectorPolicy(checksum_modes={"RRN": "warn"})
    detector = RRNRegexDetector(detector_policy=policy)

    spans = _detect(detector, "rrn 900101-1234567")

    assert len(spans) == 1
    assert spans[0].entity_type is EntityType.RRN
    assert spans[0].score == 0.70
    assert "validator.rrn.checksum_warn" in spans[0].reason_codes


def test_checksum_warn_mode_emits_credit_card_pattern_candidate() -> None:
    policy = DetectorPolicy(checksum_modes={"CREDIT_CARD": "warn"})
    detector = CreditCardRegexDetector(detector_policy=policy)

    spans = _detect(detector, "card 4111-1111-1111-1112")

    assert len(spans) == 1
    assert spans[0].entity_type is EntityType.CREDIT_CARD
    assert spans[0].score == 0.45
    assert "validator.credit_card.luhn_warn" in spans[0].reason_codes


def test_validator_checksum_modes_keep_default_behavior_strict() -> None:
    assert not validate_rrn("900101-1234567").is_valid
    assert validate_rrn("900101-1234567", checksum_mode="warn").is_valid
    assert validate_credit_card("4111-1111-1111-1112", checksum_mode="warn").is_valid
    assert not validate_business_reg_no("123-45-67892", checksum_mode="strict").is_valid
    assert validate_business_reg_no("123-45-67892", checksum_mode="off").is_valid
    with pytest.raises(ValueError, match="RRN.*maybe"):
        validate_rrn("900101-1234567", checksum_mode="maybe")


def test_pipeline_from_config_dir_applies_detector_policy(tmp_path: Path) -> None:
    config_dir = tmp_path / "configs"
    shutil.copytree(PROJECT_ROOT / "configs", config_dir)
    (config_dir / "detectors.yaml").write_text(
        """
version: v0.2-single-turn
regex_detectors:
  regex.email:
    enabled: false
entities:
  PHONE_MOBILE:
    enabled: true
  EMAIL:
    enabled: true
validators:
  CREDIT_CARD:
    checksum: strict
""".strip(),
        encoding="utf-8",
    )
    pipeline = GuardrailPipeline.from_config_dir(config_dir)

    response = pipeline.process(_request("email test@example.com phone 010-1234-5678"))

    assert all(span.entity_type is not EntityType.EMAIL for span in response.spans)
    assert any(span.entity_type is EntityType.PHONE_MOBILE for span in response.spans)
    assert response.masked_text is not None
    assert "test@example.com" in response.masked_text
    assert "010-1234-5678" not in response.masked_text
