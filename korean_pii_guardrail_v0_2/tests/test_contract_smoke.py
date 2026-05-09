from pii_guardrail import Action, EntityType, PIISpan, RiskLevel
from pii_guardrail.schema import InvalidOffsetError


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
