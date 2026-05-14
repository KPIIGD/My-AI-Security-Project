import json
from pathlib import Path

from pii_guardrail import Action, EntityType, OutputTarget, PIISpan, RiskLevel
from pii_guardrail.schema import InvalidOffsetError


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_pii_span_validates_raw_offset() -> None:
    raw = "홍길동이 신청했습니다."
    span = PIISpan(
        start=0,
        end=3,
        text="홍길동",
        entity_type=EntityType.PERSON_NAME,
        score=0.91,
        sources=("ner",),
        risk_level=RiskLevel.P1,
        action=Action.CANDIDATE,
        reason_codes=("test",),
    )
    span.validate_against(raw)


def test_pii_span_rejects_invalid_offset() -> None:
    raw = "홍길동이 신청했습니다."
    span = PIISpan(
        start=0,
        end=4,
        text="홍길동",
        entity_type=EntityType.PERSON_NAME,
        score=0.91,
        sources=("ner",),
        risk_level=RiskLevel.P1,
        action=Action.CANDIDATE,
        reason_codes=("test",),
    )
    try:
        span.validate_against(raw)
    except InvalidOffsetError:
        return
    raise AssertionError("Invalid offset should raise InvalidOffsetError")


def test_public_span_excludes_raw_text() -> None:
    span = PIISpan(
        start=0,
        end=3,
        text="홍길동",
        entity_type=EntityType.PERSON_NAME,
        score=0.91,
        sources=("ner",),
        risk_level=RiskLevel.P1,
        action=Action.MASK,
        reason_codes=("test",),
    )
    public = span.to_public(value_hash="hmac-sha256:key-v1:test")
    data = public.to_dict()
    assert "text" not in data
    assert data["raw_value_logged"] is False


def test_m7_gateway_contract_enums_are_mvp_scoped() -> None:
    assert [target.value for target in OutputTarget] == [
        "llm_input",
        "external_output",
        "audit_log",
    ]
    assert [action.value for action in Action] == [
        "candidate",
        "pass",
        "mask",
        "hash",
        "block",
    ]


def test_m7_gateway_json_schemas_are_mvp_scoped() -> None:
    request_schema = json.loads(
        (PROJECT_ROOT / "schemas" / "guardrail_request.schema.json").read_text(
            encoding="utf-8"
        )
    )
    span_schema = json.loads(
        (PROJECT_ROOT / "schemas" / "pii_span.schema.json").read_text(encoding="utf-8")
    )

    assert request_schema["properties"]["output_target"]["enum"] == [
        "llm_input",
        "external_output",
        "audit_log",
    ]
    assert request_schema["properties"]["policy_profile"]["enum"] == ["strict"]
    assert span_schema["properties"]["action"]["enum"] == [
        "candidate",
        "pass",
        "mask",
        "hash",
        "block",
    ]


def test_m7_gateway_openapi_and_policy_config_are_mvp_scoped() -> None:
    openapi_text = (PROJECT_ROOT / "api" / "openapi.yaml").read_text(encoding="utf-8")
    policy_text = (PROJECT_ROOT / "configs" / "policy_profiles.yaml").read_text(encoding="utf-8")

    assert "enum: [llm_input, external_output, audit_log]" in openapi_text
    assert "enum: [candidate, pass, mask, hash, block]" in openapi_text
    assert "enum: [strict]" in openapi_text
    assert "mvp_scope: llm_gateway" in policy_text
    assert "  strict:" in policy_text
    assert "  audit_log:" in policy_text

    unsupported_terms = [
        "internal_ui",
        "analytics_ai_training",
        "pseudonymize",
        "review",
        "balanced",
    ]
    for term in unsupported_terms:
        assert term not in openapi_text
        assert term not in policy_text
