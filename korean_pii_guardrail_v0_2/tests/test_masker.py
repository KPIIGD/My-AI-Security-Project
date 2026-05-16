import pytest

from pii_guardrail.audit_logger import HMACKey, HMACKeyRing
from pii_guardrail.enums import EntityType, OutputTarget, RiskLevel
from pii_guardrail.masker import HmacHashProvider, MaskingError, SuffixPreservingMasker
from pii_guardrail.schema import GuardrailRequest, InvalidOffsetError, PIISpan


def _request(raw: str, *, target: OutputTarget = OutputTarget.LLM_INPUT) -> GuardrailRequest:
    return GuardrailRequest(text=raw, output_target=target)


def _span(
    raw: str,
    value: str,
    entity_type: EntityType,
    risk_level: RiskLevel,
    *,
    start_offset: int | None = None,
    score: float = 0.91,
    sources: tuple[str, ...] = ("regex",),
    reason_codes: tuple[str, ...] = ("test",),
    is_composite: bool = False,
    suffix: str | None = None,
) -> PIISpan:
    start = raw.index(value) if start_offset is None else start_offset
    return PIISpan(
        start=start,
        end=start + len(value),
        text=value,
        entity_type=entity_type,
        score=score,
        sources=sources,
        risk_level=risk_level,
        suffix=suffix,
        reason_codes=reason_codes,
        detector_ids=("test.detector",),
        is_composite=is_composite,
    )


def test_suffix_preserving_label_mask_reconstruction() -> None:
    raw = "홍길동이 010-1234-5678로 연락했습니다."
    spans = [
        _span(raw, "홍길동", EntityType.PERSON_NAME, RiskLevel.P1, sources=("ner",), suffix="이"),
        _span(raw, "010-1234-5678", EntityType.PHONE_MOBILE, RiskLevel.P1, suffix="로"),
    ]

    masked = SuffixPreservingMasker().apply(raw, spans, _request(raw))

    assert masked == "[PERSON_1]이 [PHONE_1]로 연락했습니다."


def test_same_value_reuses_placeholder_within_request() -> None:
    raw = "홍길동이 왔고 홍길동에게 전화했습니다."
    first = _span(raw, "홍길동", EntityType.PERSON_NAME, RiskLevel.P1, sources=("ner",), suffix="이")
    second_start = raw.index("홍길동", first.end)
    second = _span(
        raw,
        "홍길동",
        EntityType.PERSON_NAME,
        RiskLevel.P1,
        start_offset=second_start,
        sources=("ner",),
        suffix="에게",
    )

    masked = SuffixPreservingMasker().apply(raw, [first, second], _request(raw))

    assert masked == "[PERSON_1]이 왔고 [PERSON_1]에게 전화했습니다."


def test_different_values_increment_entity_placeholder_index() -> None:
    raw = "홍길동과 김민수가 왔습니다."
    spans = [
        _span(raw, "홍길동", EntityType.PERSON_NAME, RiskLevel.P1, sources=("ner",)),
        _span(raw, "김민수", EntityType.PERSON_NAME, RiskLevel.P1, sources=("ner",)),
    ]

    masked = SuffixPreservingMasker().apply(raw, spans, _request(raw))

    assert masked == "[PERSON_1]과 [PERSON_2]가 왔습니다."


def test_audit_log_target_replaces_value_with_hmac_digest() -> None:
    raw = "연락처는 010-1234-5678입니다."
    span = _span(raw, "010-1234-5678", EntityType.PHONE_MOBILE, RiskLevel.P1)
    masker = SuffixPreservingMasker(
        hash_provider=HmacHashProvider(key=b"test-secret", key_id="key-v1")
    )

    masked = masker.apply(raw, [span], _request(raw, target=OutputTarget.AUDIT_LOG))

    assert masked is not None
    assert "010-1234-5678" not in masked
    assert masked.startswith("연락처는 hmac-sha256:key-v1:")
    assert masked.endswith("입니다.")


def test_audit_log_target_accepts_hmac_keyring_hash_provider() -> None:
    raw = "phone 010-1234-5678 done"
    span = _span(raw, "010-1234-5678", EntityType.PHONE_MOBILE, RiskLevel.P1)
    keyring = HMACKeyRing(
        keys={
            "v1": HMACKey(
                key_id="v1",
                secret=b"a" * HMACKeyRing.MIN_KEY_BYTES,
            )
        },
        active_id="v1",
    )
    masker = SuffixPreservingMasker(hash_provider=keyring)

    masked = masker.apply(raw, [span], _request(raw, target=OutputTarget.AUDIT_LOG))

    assert masked == f"phone {keyring.sign('010-1234-5678')} done"
    assert keyring.digest("010-1234-5678") == keyring.sign("010-1234-5678")


def test_api_key_secret_blocks_response() -> None:
    raw = "token sk-AbC123xYz987TokenValue"
    span = _span(raw, "sk-AbC123xYz987TokenValue", EntityType.API_KEY_SECRET, RiskLevel.P0)

    masked = SuffixPreservingMasker().apply(
        raw, [span], _request(raw, target=OutputTarget.EXTERNAL_OUTPUT)
    )

    assert masked is None


def test_p0_full_redact_uses_redacted_token() -> None:
    raw = "주민번호 900101-1234568"
    span = _span(raw, "900101-1234568", EntityType.RRN, RiskLevel.P0, score=0.98)

    masked = SuffixPreservingMasker().apply(raw, [span], _request(raw))

    assert masked == "주민번호 [REDACTED]"


def test_pass_action_leaves_text_unchanged() -> None:
    raw = "OO고"
    span = _span(raw, "OO고", EntityType.SCHOOL, RiskLevel.P2, score=0.55, sources=("dictionary",))

    masked = SuffixPreservingMasker().apply(raw, [span], _request(raw))

    assert masked == raw


def test_overlapping_maskable_spans_are_rejected() -> None:
    raw = "abcdef"
    spans = [
        _span(raw, "abcd", EntityType.PHONE_MOBILE, RiskLevel.P1),
        _span(raw, "cdef", EntityType.EMAIL, RiskLevel.P1),
    ]

    with pytest.raises(MaskingError) as exc_info:
        SuffixPreservingMasker().apply(raw, spans, _request(raw))

    assert "abcdef" not in str(exc_info.value)


def test_invalid_offset_rejects_without_raw_value_in_error() -> None:
    raw = "홍길동이 왔습니다."
    span = PIISpan(
        start=0,
        end=3,
        text="김민수",
        entity_type=EntityType.PERSON_NAME,
        score=0.91,
        sources=("ner",),
        risk_level=RiskLevel.P1,
    )

    with pytest.raises(InvalidOffsetError) as exc_info:
        SuffixPreservingMasker().apply(raw, [span], _request(raw))

    assert "홍길동" not in str(exc_info.value)
    assert "김민수" not in str(exc_info.value)
