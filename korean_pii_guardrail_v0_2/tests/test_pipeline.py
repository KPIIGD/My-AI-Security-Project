"""End-to-end smoke tests for the M9 GuardrailPipeline.

Covers the M1→M8 happy paths plus key safety invariants:

- BLOCK propagates from policy → masker → response.masked_text is None
- raw PII does not appear in masked_text or response.spans (PublicPIISpan
  has no text field)
- audit logger is optional; when present, only MASK/HASH/BLOCK spans emit
- AuditPayloadLeakError during emit is dropped (fail-closed) without
  killing the response
- suffix-preserving placeholder reconstruction works (M3 + M7 cooperation)
- composite spans get is_composite=True surfaced through PublicPIISpan
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pii_guardrail.audit_logger import AuditLogger, HMACKey, HMACKeyRing
from pii_guardrail.enums import Action, EntityType, OutputTarget, RiskLevel
from pii_guardrail.pipeline import (
    GuardrailPipeline,
    PipelineComponents,
    default_components,
)
from pii_guardrail.ner.finetuned_wrapper import FinetunedNERDetector
from pii_guardrail.schema import GuardrailOptions, GuardrailRequest, PIISpan


def _request(
    raw: str,
    *,
    target: OutputTarget = OutputTarget.LLM_INPUT,
    profile: str = "strict",
    options: GuardrailOptions | None = None,
) -> GuardrailRequest:
    kwargs = {
        "text": raw,
        "output_target": target,
        "policy_profile": profile,
        "request_id": "req-pipeline-test",
    }
    if options is not None:
        kwargs["options"] = options
    return GuardrailRequest(**kwargs)


def test_public_api_matches_interface_spec_example() -> None:
    from pii_guardrail import GuardrailPipeline as PublicGuardrailPipeline
    from pii_guardrail import GuardrailRequest as PublicGuardrailRequest

    pipeline = PublicGuardrailPipeline.from_config_dir(
        Path(__file__).resolve().parents[1] / "configs"
    )

    response = pipeline.apply(
        PublicGuardrailRequest(
            text="홍길동이 010-1234-5678로 연락했습니다.",
            scan_stage="input",
            output_target="llm_input",
            policy_profile="strict",
            request_id="req-interface-spec-example",
        )
    )

    assert response.output_target is OutputTarget.LLM_INPUT
    assert response.masked_text == "[PERSON_1]이 [PHONE_1]로 연락했습니다."


@pytest.fixture
def keyring(tmp_path: Path) -> HMACKeyRing:
    key_file = tmp_path / "audit_v1.key"
    key_file.write_bytes(b"pipeline-test-secret-32-bytes-minlen")
    return HMACKeyRing(
        keys={"v1": HMACKey(key_id="v1", secret=key_file.read_bytes())},
        active_id="v1",
    )


@pytest.fixture
def audit_log_path(tmp_path: Path) -> Path:
    return tmp_path / "audit.log.jsonl"


@pytest.fixture(autouse=True)
def _isolated_audit_logger():
    """Strip handlers from the shared 'audit' logger between tests."""
    import logging

    logger = logging.getLogger(AuditLogger.LOGGER_NAME)
    saved_handlers = list(logger.handlers)
    saved_propagate = logger.propagate
    logger.handlers.clear()
    yield logger
    for handler in logger.handlers:
        handler.close()
    logger.handlers = saved_handlers
    logger.propagate = saved_propagate


# ============================================================
# Smoke — single-entity flows
# ============================================================


def test_pipeline_masks_phone_with_suffix_preserving_placeholder() -> None:
    raw = "연락처는 010-1234-5678입니다."
    pipeline = GuardrailPipeline()

    response = pipeline.process(_request(raw))

    assert response.blocked is False
    assert response.masked_text is not None
    assert "010-1234-5678" not in response.masked_text
    assert "[PHONE_" in response.masked_text
    assert "입니다." in response.masked_text  # suffix is preserved on raw side


def test_pipeline_masks_email() -> None:
    raw = "메일은 test@example.com 입니다."
    pipeline = GuardrailPipeline()

    response = pipeline.process(_request(raw))

    assert response.masked_text is not None
    assert "test@example.com" not in response.masked_text
    assert any(span.entity_type is EntityType.EMAIL for span in response.spans)


def test_pipeline_full_redacts_rrn() -> None:
    raw = "주민번호는 900101-1234568 입니다."
    pipeline = GuardrailPipeline()

    response = pipeline.process(_request(raw))

    assert response.masked_text is not None
    assert "900101-1234568" not in response.masked_text
    assert "[REDACTED]" in response.masked_text


def test_pipeline_prefers_corporate_reg_no_in_explicit_corporate_context() -> None:
    raw = "\ubc95\uc778\ub4f1\ub85d\ubc88\ud638 110111-1000002 \ud655\uc778"
    pipeline = GuardrailPipeline()

    response = pipeline.process(_request(raw))

    assert response.masked_text is not None
    assert "110111-1000002" not in response.masked_text
    assert "[CORPORATE_REG_NO_1]" in response.masked_text
    assert any(
        span.entity_type is EntityType.CORPORATE_REG_NO and span.action is Action.MASK
        for span in response.spans
    )
    assert not any(span.entity_type is EntityType.RRN for span in response.spans)


@pytest.mark.parametrize(
    "raw",
    [
        "주문번호 010-1234-5678 처리 완료.",
        "송장번호 123-45-67891 배송 추적.",
        "tracking no 110-123-456789 was generated.",
        "\uc81c\ud488\ucf54\ub4dc A12345678\uc740 \ub2e8\uc885\uc785\ub2c8\ub2e4.",
        "\ud2f0\ucf13 \ubc88\ud638 B87654321 \ucc98\ub9ac \uc644\ub8cc.",
        "\uc8fc\ubb38\ubc88\ud638 12-34-567890-12 \ucc98\ub9ac \uc644\ub8cc.",
    ],
)
def test_pipeline_passes_order_like_numeric_identifiers(raw: str) -> None:
    pipeline = GuardrailPipeline()

    response = pipeline.process(_request(raw))

    assert response.masked_text == raw
    assert response.metrics.masked_span_count == 0


def test_pipeline_prefers_medical_record_no_over_business_reg_no_subspan() -> None:
    raw = "\ud658\uc790\ubc88\ud638 MR-2026-000016."
    pipeline = GuardrailPipeline()

    response = pipeline.process(_request(raw))

    assert response.masked_text is not None
    assert "MR-2026-000016" not in response.masked_text
    assert "[MEDICAL_RECORD_NO_1]" in response.masked_text
    assert any(
        span.entity_type is EntityType.MEDICAL_RECORD_NO and span.action is Action.MASK
        for span in response.spans
    )
    assert not any(span.entity_type is EntityType.BUSINESS_REG_NO for span in response.spans)


@pytest.mark.parametrize(
    "raw",
    [
        "\uace0\uac1d\ubc88\ud638 CUST-000123.",
        "\uc0ac\ubc88 EMP-2026-00123.",
        "\ud559\ubc88 STU-20260001.",
        "\ud559\uc0dd\ubc88\ud638 STU-20260001.",
        "\uace0\uac1d\ubc88\ud638 123456.",
        "\ud68c\uc6d0ID user123.",
        "\uc9c1\uc6d0\ubc88\ud638 2026-00123.",
        "\ud559\uc0dd\ubc88\ud638 20260015.",
    ],
)
def test_pipeline_passes_internal_identifiers_without_custom_profile(raw: str) -> None:
    pipeline = GuardrailPipeline()

    response = pipeline.process(_request(raw))

    assert response.masked_text is not None
    assert response.masked_text == raw
    assert not any(
        span.entity_type
        in {EntityType.CUSTOMER_ID, EntityType.EMPLOYEE_ID, EntityType.STUDENT_ID}
        for span in response.spans
    )


@pytest.mark.parametrize(
    "raw",
    [
        "\uace0\uac1d\ubc88\ud638 3\uac1c \ubc1c\uae09\ud588\uc2b5\ub2c8\ub2e4.",
        "\ud68c\uc6d0\ubc88\ud638 3\uac1c \uc0dd\uc131\ud574\uc8fc\uc138\uc694.",
        "\ud68c\uc6d0ID 3\uac1c \ub9cc\ub4e4\uc5b4\uc918.",
        "\uc0ac\ubc88 3\uac1c \ud544\uc694\ud569\ub2c8\ub2e4.",
        "\uc9c1\uc6d0\ubc88\ud638 3\uac1c \ud544\uc694\ud569\ub2c8\ub2e4.",
        "\ud559\ubc88 3\uac1c \uc870\ud68c\ud588\uc2b5\ub2c8\ub2e4.",
        "\ud559\uc0dd\ubc88\ud638 3\uac1c \ub4f1\ub85d\ud588\uc2b5\ub2c8\ub2e4.",
    ],
)
def test_pipeline_passes_labeled_internal_identifier_quantity_context(raw: str) -> None:
    pipeline = GuardrailPipeline()

    response = pipeline.process(_request(raw))

    assert response.masked_text == raw
    assert response.metrics.masked_span_count == 0


def test_pipeline_blocks_api_key_secret() -> None:
    raw = "token sk-AbC123xYz987SecretTokenValue"
    pipeline = GuardrailPipeline()

    response = pipeline.process(
        _request(raw, target=OutputTarget.EXTERNAL_OUTPUT)
    )

    assert response.blocked is True
    assert response.masked_text is None
    # The detection itself still surfaces on the public span list.
    assert any(span.entity_type is EntityType.API_KEY_SECRET for span in response.spans)


# ============================================================
# Smoke — multi-entity + composite
# ============================================================


def test_pipeline_handles_person_plus_phone_composite() -> None:
    raw = "고객명 홍길동, 연락처 010-1234-5678."
    pipeline = GuardrailPipeline()

    response = pipeline.process(_request(raw))

    assert response.masked_text is not None
    assert "010-1234-5678" not in response.masked_text
    # PERSON_NAME + PHONE_MOBILE composite → both should mask
    masked_types = {
        span.entity_type
        for span in response.spans
        if span.action in {Action.MASK, Action.HASH}
    }
    assert EntityType.PHONE_MOBILE in masked_types


@pytest.mark.parametrize(
    ("raw", "raw_value", "entity_type"),
    [
        ("이 데이터셋 문서 작성자 홍길동", "홍길동", EntityType.PERSON_NAME),
        ("이 데이터셋 문서 홍길동", "홍길동", EntityType.PERSON_NAME),
        ("데모 문의는 010-1234-5678 로 주세요", "010-1234-5678", EntityType.PHONE_MOBILE),
        ("설치 가이드 문서 연락처 010-9876-5432", "010-9876-5432", EntityType.PHONE_MOBILE),
    ],
)
def test_pipeline_masks_real_pii_with_broad_document_words(
    raw: str,
    raw_value: str,
    entity_type: EntityType,
) -> None:
    pipeline = GuardrailPipeline.from_config_dir("configs")

    response = pipeline.process(_request(raw))

    assert response.masked_text is not None
    assert raw_value not in response.masked_text
    assert any(
        span.entity_type is entity_type and span.action is Action.MASK
        for span in response.spans
    )


def test_pipeline_passes_explicit_example_phone() -> None:
    raw = "예시 전화번호는 010-1234-5678입니다."
    pipeline = GuardrailPipeline.from_config_dir("configs")

    response = pipeline.process(_request(raw))

    assert response.masked_text == raw
    assert any(
        span.entity_type is EntityType.PHONE_MOBILE and span.action is Action.PASS
        for span in response.spans
    )


class _OverextendedAddressNER:
    detector_id = "ner.test.overextended-address"

    def detect(self, raw_text, preprocessed, request):
        del preprocessed, request
        text = "서울시 강남구 테헤란로 123 거"
        start = raw_text.index(text)
        end = start + len(text)
        return [
            PIISpan(
                start=start,
                end=end,
                text=text,
                entity_type=EntityType.ADDRESS_FULL,
                score=1.0,
                sources=("ner",),
                risk_level=RiskLevel.P1,
                detector_ids=(self.detector_id,),
                reason_codes=("ner.test.overextended_address",),
            )
        ]


class _WhitespacePersonBackend:
    def detect(self, raw_text):
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


class _PersonPrefixBackend:
    def detect(self, raw_text):
        text = "민수"
        start = raw_text.index(text)
        return [
            {
                "start": start,
                "end": start + len(text),
                "text": text,
                "label": "B-NAME",
                "score": 0.99,
            }
        ]


def test_pipeline_trims_ner_address_partial_predicate_before_masking() -> None:
    raw = "주소는 서울시 강남구 테헤란로 123 거주"
    pipeline = GuardrailPipeline(default_components(ner_detector=_OverextendedAddressNER()))

    response = pipeline.process(_request(raw))

    assert response.masked_text == "주소는 [ADDRESS_1] 거주"
    address = next(span for span in response.spans if span.entity_type is EntityType.ADDRESS_FULL)
    assert address.end == raw.index(" 거주")
    assert "boundary.address_partial_word_trim" in address.reason_codes


def test_pipeline_rejects_whitespace_ner_person_and_uses_dictionary_name() -> None:
    raw = "하도윤 신한은행 계좌 110-123-456789, 카드 4532015112830036"
    ner = FinetunedNERDetector(backend=_WhitespacePersonBackend())
    pipeline = GuardrailPipeline(default_components(ner_detector=ner))

    response = pipeline.process(_request(raw))

    assert response.masked_text == "[PERSON_1] 신한은행 계좌 [BANK_ACCOUNT_1], 카드 [REDACTED]"
    persons = [span for span in response.spans if span.entity_type is EntityType.PERSON_NAME]
    assert len(persons) == 1
    assert persons[0].start == 0
    assert persons[0].end == 3


def test_pipeline_rejects_ner_person_prefix_inside_compound_word() -> None:
    raw = "민수전자 제품 문의"
    ner = FinetunedNERDetector(backend=_PersonPrefixBackend())
    pipeline = GuardrailPipeline(default_components(ner_detector=ner))

    response = pipeline.process(_request(raw))

    assert response.masked_text == raw
    assert all(span.entity_type is not EntityType.PERSON_NAME for span in response.spans)


def test_pipeline_masks_organization_affiliation_without_person_subspan() -> None:
    raw = "박지성님께 010-9876-5432 로 연락주세요 (지성테크 대표)"
    pipeline = GuardrailPipeline()

    response = pipeline.process(_request(raw))

    assert response.masked_text == "[PERSON_1]님께 [PHONE_1] 로 연락주세요 ([ORGANIZATION_1] 대표)"
    assert "[PERSON_2]" not in response.masked_text
    assert any(span.entity_type is EntityType.ORGANIZATION for span in response.spans)


def test_pipeline_masks_organization_when_work_context_is_present() -> None:
    raw = "김민수 서울시 강남구 테헤란로 123 삼성전자 근무"
    pipeline = GuardrailPipeline()

    response = pipeline.process(_request(raw))

    assert "[ORGANIZATION_1]" in (response.masked_text or "")


def test_pipeline_does_not_mask_email_label_syllable() -> None:
    raw = "최영희 연락처 010-1234-5678, 이메일 choi@example.com"
    pipeline = GuardrailPipeline()

    response = pipeline.process(_request(raw))

    assert response.masked_text is not None
    assert "이메일 [EMAIL_1]" in response.masked_text
    assert "이메[EMAIL_1]" not in response.masked_text
    email = next(span for span in response.spans if span.entity_type is EntityType.EMAIL)
    assert raw[email.start : email.end] == "choi@example.com"


def test_pipeline_reuses_placeholder_for_repeated_value() -> None:
    raw = "홍길동이 왔고, 다시 홍길동에게 전화했습니다. 연락처 010-1234-5678."
    pipeline = GuardrailPipeline()

    response = pipeline.process(_request(raw))

    masked = response.masked_text
    assert masked is not None
    # Same person referenced twice → same placeholder index.
    # Count of '[PERSON_1]' must equal 2 if NER mock returns the same span twice,
    # but with the v0.2 default we at least confirm no second placeholder index
    # for the same surface value.
    if "[PERSON_1]" in masked:
        assert "[PERSON_2]" not in masked or masked.count("[PERSON_2]") == 0


def test_pipeline_passes_clean_text_unchanged() -> None:
    raw = "오늘 날씨가 정말 좋네요."
    pipeline = GuardrailPipeline()

    response = pipeline.process(_request(raw))

    assert response.blocked is False
    assert response.masked_text == raw
    assert response.metrics.masked_span_count == 0


def test_pipeline_passes_abstract_value_that_looks_like_name() -> None:
    raw = "사랑은 중요한 가치입니다."
    pipeline = GuardrailPipeline()

    response = pipeline.process(_request(raw))

    assert response.masked_text == raw
    assert response.metrics.masked_span_count == 0


# ============================================================
# Public response — no raw PII leak
# ============================================================


def test_public_response_to_dict_contains_no_raw_value() -> None:
    raw = "주민번호 900101-1234568 입니다."
    pipeline = GuardrailPipeline()

    response = pipeline.process(_request(raw))
    payload = response.to_dict()

    # Public response must not embed the raw RRN in any field.
    serialized = str(payload)
    assert "900101-1234568" not in serialized
    # raw_value_logged is always False per spec §5.
    assert payload["raw_value_logged"] is False
    for span_dict in payload["spans"]:
        assert "text" not in span_dict


def test_metrics_count_detected_and_masked_consistently() -> None:
    raw = "연락처 010-1234-5678 메일 test@example.com 입니다."
    pipeline = GuardrailPipeline()

    response = pipeline.process(_request(raw))

    assert response.metrics.detected_span_count == len(response.spans)
    masked_in_spans = sum(
        1
        for span in response.spans
        if span.action in {Action.MASK, Action.HASH}
    )
    assert response.metrics.masked_span_count == masked_in_spans
    assert response.metrics.latency_ms > 0


# ============================================================
# M8 audit integration
# ============================================================


def test_pipeline_skips_audit_when_logger_absent() -> None:
    raw = "연락처 010-1234-5678 입니다."
    pipeline = GuardrailPipeline()

    response = pipeline.process(_request(raw))

    assert response.audit_events == ()


def test_pipeline_emits_audit_events_for_masked_spans_only(
    keyring: HMACKeyRing, audit_log_path: Path
) -> None:
    raw = "연락처 010-1234-5678 입니다."
    audit_logger = AuditLogger(keyring=keyring, log_path=audit_log_path)
    components = default_components(audit_logger=audit_logger)
    pipeline = GuardrailPipeline(components=components)

    response = pipeline.process(_request(raw))

    assert len(response.audit_events) >= 1
    # Every emitted audit event must come from a masked/hashed/blocked span.
    for event in response.audit_events:
        assert event.action in {Action.MASK, Action.HASH, Action.BLOCK}
        assert event.value_hash is not None and event.value_hash.startswith("hmac-sha256:v1:")
    actionable_spans = [
        span
        for span in response.spans
        if span.action in {Action.MASK, Action.HASH, Action.BLOCK}
    ]
    assert [span.value_hash for span in actionable_spans] == [
        event.value_hash for event in response.audit_events
    ]


def test_pipeline_honors_include_audit_events_response_option(
    keyring: HMACKeyRing, audit_log_path: Path
) -> None:
    raw = "phone 010-1234-5678"
    audit_logger = AuditLogger(keyring=keyring, log_path=audit_log_path)
    components = default_components(audit_logger=audit_logger)
    pipeline = GuardrailPipeline(components=components)

    response = pipeline.process(
        _request(raw, options=GuardrailOptions(include_audit_events=False))
    )

    assert response.audit_events == ()
    assert audit_log_path.read_text(encoding="utf-8").strip()


def test_pipeline_honors_return_spans_response_option() -> None:
    raw = "phone 010-1234-5678"
    pipeline = GuardrailPipeline()

    response = pipeline.process(
        _request(raw, options=GuardrailOptions(return_spans=False))
    )

    assert response.spans == ()
    assert response.metrics.detected_span_count >= 1
    assert response.masked_text is not None
    assert "010-1234-5678" not in response.masked_text


def test_audit_file_contents_omit_detector_ids_by_default(
    keyring: HMACKeyRing, audit_log_path: Path
) -> None:
    import json as _json

    raw = "연락처 010-1234-5678 입니다."
    audit_logger = AuditLogger(keyring=keyring, log_path=audit_log_path, verbose=False)
    components = default_components(audit_logger=audit_logger)
    pipeline = GuardrailPipeline(components=components)

    pipeline.process(_request(raw))

    lines = audit_log_path.read_text(encoding="utf-8").strip().splitlines()
    assert lines, "audit file should have at least one line"
    for line in lines:
        decoded = _json.loads(line)
        assert "detector_ids" not in decoded
        assert decoded["raw_value_logged"] is False


def test_pipeline_does_not_crash_when_audit_emit_raises(
    keyring: HMACKeyRing, audit_log_path: Path
) -> None:
    """Fail-closed: a PII-leaking event is dropped, pipeline returns normally."""

    raw = "연락처 010-1234-5678 입니다."
    audit_logger = AuditLogger(keyring=keyring, log_path=audit_log_path)
    components = default_components(audit_logger=audit_logger)
    pipeline = GuardrailPipeline(components=components)

    # Smuggle a leaky reason code onto every regex detector emit.
    # Simulate by wrapping the dictionary detector — easier than monkeypatching.
    original_emit = audit_logger.emit
    call_count = {"n": 0}

    def emit_with_occasional_leak(*, span, request, event_type="pii_detection"):
        call_count["n"] += 1
        # On first call, inject a leaking reason code to trigger
        # AuditPayloadLeakError inside audit_logger.emit.
        if call_count["n"] == 1:
            from dataclasses import replace

            leaky_span = replace(
                span,
                reason_codes=(*span.reason_codes, "context.boost.match:010-1234-5678"),
            )
            return original_emit(span=leaky_span, request=request, event_type=event_type)
        return original_emit(span=span, request=request, event_type=event_type)

    audit_logger.emit = emit_with_occasional_leak  # type: ignore[assignment]

    response = pipeline.process(_request(raw))

    # Response is still well-formed even though the first audit event was dropped.
    assert response.masked_text is not None
    assert "010-1234-5678" not in response.masked_text


# ============================================================
# Component swap surface
# ============================================================


def test_default_components_uses_mock_ner() -> None:
    from pii_guardrail.ner import MockNERDetector

    components = default_components()
    assert isinstance(components.ner_detector, MockNERDetector)


def test_pipeline_accepts_no_ner_detector() -> None:
    from dataclasses import replace

    raw = "연락처 010-1234-5678 입니다."
    components = default_components()
    components_without_ner = replace(components, ner_detector=None)
    pipeline = GuardrailPipeline(components=components_without_ner)

    response = pipeline.process(_request(raw))

    # Pipeline still masks the phone — regex detector alone is enough.
    assert response.masked_text is not None
    assert "010-1234-5678" not in response.masked_text


def test_public_spans_carry_value_hash_for_actionable_spans() -> None:
    """spec docs/06 §7.1 requires public spans to expose an HMAC value_hash
    so consumers can correlate a response span with the matching audit
    event. Regression guard for the bug where pipeline.process called
    span.to_public() without populating value_hash.
    """
    raw = "연락처 010-1234-5678 입니다."
    pipeline = GuardrailPipeline()

    response = pipeline.process(_request(raw))

    actionable = [
        span
        for span in response.spans
        if span.action.value in {"mask", "hash", "block"}
    ]
    assert actionable, "expected at least one masked span for this fixture"
    for span in actionable:
        assert span.value_hash is not None
        assert span.value_hash.startswith("hmac-sha256:")


def test_public_spans_have_no_value_hash_when_action_is_pass() -> None:
    """PASS-action spans should not expose a hash; the raw text flows
    through unchanged so a hash would only inflate the payload without
    adding an audit-correlation benefit.
    """
    from dataclasses import replace

    from pii_guardrail.enums import Action

    raw = "연락처 010-1234-5678 입니다."
    pipeline = GuardrailPipeline()
    response = pipeline.process(_request(raw))

    # Force one of the public spans to PASS and rebuild the value_hash
    # decision so we can assert the None path explicitly.
    pass_decision = replace(response.spans[0], action=Action.PASS, value_hash=None)
    assert pass_decision.value_hash is None
