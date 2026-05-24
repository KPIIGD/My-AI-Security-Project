from dataclasses import replace

import pytest

from pii_guardrail.enums import Action, EntityType, OutputTarget, RiskLevel
from pii_guardrail.policy import (
    PolicyConfigError,
    PolicyRouter,
    TransformationMethod,
    load_policy_config,
    load_risk_action_thresholds,
)
from pii_guardrail.schema import GuardrailRequest, PIISpan


def _request(raw: str, *, target: OutputTarget = OutputTarget.LLM_INPUT, profile: str = "strict") -> GuardrailRequest:
    return GuardrailRequest(text=raw, output_target=target, policy_profile=profile)


def _span(
    raw: str,
    value: str,
    entity_type: EntityType,
    risk_level: RiskLevel,
    *,
    score: float = 0.9,
    sources: tuple[str, ...] = ("regex",),
    reason_codes: tuple[str, ...] = ("test",),
    is_composite: bool = False,
) -> PIISpan:
    start = raw.index(value)
    return PIISpan(
        start=start,
        end=start + len(value),
        text=value,
        entity_type=entity_type,
        score=score,
        sources=sources,
        risk_level=risk_level,
        reason_codes=reason_codes,
        detector_ids=("test.detector",),
        is_composite=is_composite,
    )


def test_policy_config_loads_m7_mvp_scope() -> None:
    config = load_policy_config()
    thresholds = load_risk_action_thresholds()

    assert config.profiles == frozenset({"strict"})
    assert set(config.output_targets) == {
        OutputTarget.LLM_INPUT,
        OutputTarget.EXTERNAL_OUTPUT,
        OutputTarget.AUDIT_LOG,
    }
    assert config.output_targets[OutputTarget.AUDIT_LOG].default_method is TransformationMethod.HMAC_HASH
    assert config.entity_overrides[EntityType.RRN]["strict"] is TransformationMethod.LABEL_MASK
    assert config.entity_overrides[EntityType.FRN]["strict"] is TransformationMethod.FULL_REDACT
    assert thresholds.p1_mask_min_score == 0.75


def test_audit_log_target_hashes_every_span() -> None:
    raw = "연락처는 010-1234-5678입니다."
    span = _span(raw, "010-1234-5678", EntityType.PHONE_MOBILE, RiskLevel.P1)

    decision = PolicyRouter().select(span, _request(raw, target=OutputTarget.AUDIT_LOG))

    assert decision.action is Action.HASH
    assert decision.method is TransformationMethod.HMAC_HASH
    assert decision.output_target is OutputTarget.AUDIT_LOG


def test_api_key_secret_blocks_external_output() -> None:
    raw = "token sk-AbC123xYz987TokenValue"
    span = _span(raw, "sk-AbC123xYz987TokenValue", EntityType.API_KEY_SECRET, RiskLevel.P0)

    decision = PolicyRouter().select(span, _request(raw, target=OutputTarget.EXTERNAL_OUTPUT))

    assert decision.action is Action.BLOCK
    assert decision.method is TransformationMethod.BLOCK


def test_p0_structured_identifier_uses_full_redact_mask() -> None:
    raw = "외국인등록번호 900101-1234568"
    span = _span(raw, "900101-1234568", EntityType.FRN, RiskLevel.P0, score=0.98)

    decision = PolicyRouter().select(span, _request(raw))

    assert decision.action is Action.MASK
    assert decision.method is TransformationMethod.FULL_REDACT


def test_rrn_uses_label_mask_override() -> None:
    raw = "주민번호 900101-1234568"
    span = _span(raw, "900101-1234568", EntityType.RRN, RiskLevel.P0, score=0.98)

    decision = PolicyRouter().select(span, _request(raw))

    assert decision.action is Action.MASK
    assert decision.method is TransformationMethod.LABEL_MASK


def test_p1_masks_by_threshold_or_context() -> None:
    raw = "연락처 010-1234-5678 계좌 110-123-456789"
    phone = _span(raw, "010-1234-5678", EntityType.PHONE_MOBILE, RiskLevel.P1, score=0.94)
    account = _span(
        raw,
        "110-123-456789",
        EntityType.BANK_ACCOUNT,
        RiskLevel.P1,
        score=0.60,
        sources=("regex", "context"),
        reason_codes=("context.boost.field_label_account:계좌",),
    )

    router = PolicyRouter()

    assert router.select(phone, _request(raw)).action is Action.MASK
    assert router.select(account, _request(raw)).action is Action.MASK


def test_p1_low_score_without_context_passes() -> None:
    raw = "숫자 110-123-456789"
    span = _span(raw, "110-123-456789", EntityType.BANK_ACCOUNT, RiskLevel.P1, score=0.42)

    decision = PolicyRouter().select(span, _request(raw))

    assert decision.action is Action.PASS
    assert decision.method is TransformationMethod.PASS


def test_p2_and_p3_without_context_pass() -> None:
    raw = "OO고 42세"
    school = _span(raw, "OO고", EntityType.SCHOOL, RiskLevel.P2, score=0.88, sources=("dictionary",))
    age = _span(raw, "42세", EntityType.AGE, RiskLevel.P3, score=0.95, sources=("dictionary",))

    router = PolicyRouter()

    assert router.select(school, _request(raw)).action is Action.PASS
    assert router.select(age, _request(raw)).action is Action.PASS


def test_composite_span_masks_even_when_context_threshold_is_lower() -> None:
    raw = "성별 남, 학교 OO고"
    span = _span(
        raw,
        "OO고",
        EntityType.SCHOOL,
        RiskLevel.P2,
        score=0.76,
        sources=("dictionary",),
        is_composite=True,
    )

    decision = PolicyRouter().select(span, _request(raw))

    assert decision.action is Action.MASK
    assert decision.method is TransformationMethod.LABEL_MASK


def test_router_applies_action_metadata_without_raw_text() -> None:
    raw = "홍길동이 왔습니다."
    span = _span(raw, "홍길동", EntityType.PERSON_NAME, RiskLevel.P1, score=0.91, sources=("ner",))

    [routed] = PolicyRouter().route([span], _request(raw))
    public = routed.to_public().to_dict()

    assert routed.action is Action.MASK
    assert routed.policy_profile == "strict"
    assert routed.output_target is OutputTarget.LLM_INPUT
    assert "policy" in routed.sources
    assert "text" not in public


def test_unknown_policy_profile_fails_fast_without_raw_value() -> None:
    raw = "홍길동이 왔습니다."
    span = _span(raw, "홍길동", EntityType.PERSON_NAME, RiskLevel.P1)
    request = replace(_request(raw), policy_profile="balanced")

    with pytest.raises(PolicyConfigError) as exc_info:
        PolicyRouter().select(span, request)

    assert "홍길동" not in str(exc_info.value)
