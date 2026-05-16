"""Tests for M8 audit logger.

Coverage targets:

- HMACKeyRing hybrid model (env path + .key file, no env material)
- HMACKeyRing rotation + back-verification
- AuditPayloadLeakError messages never contain matched raw text
- scan_audit_payload scans caller-controlled string metadata by default while
  excluding value_hash / key_id and non-string numeric metadata
- AuditLogger writes JSONL, defaults to detector_ids stripped, verbose
  mode opts them back in
- AuditLogger validates span offsets before hashing or writing
- AuditLogger preserves span sources without adding validator provenance
- request_id=None is materialized once per GuardrailRequest object
- AuditLogger.propagate=False so audit lines never reach root logger
- AuditLogger isolates different log_path sinks even with mixed verbosity
- AuditLogger handler is not duplicated across re-inits on the same path
- fail-closed: emit raises and does not write when a PII pattern matches
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
from pathlib import Path

import pytest

from pii_guardrail.audit_logger import (
    AuditKeyringError,
    AuditLogger,
    AuditPayloadLeakError,
    HMACKey,
    HMACKeyRing,
    scan_audit_payload,
)
from pii_guardrail.enums import Action, EntityType, OutputTarget, RiskLevel
from pii_guardrail.schema import GuardrailRequest, InvalidOffsetError, PIISpan


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def key_dir(tmp_path: Path) -> Path:
    keys = tmp_path / "keys"
    keys.mkdir()
    return keys


@pytest.fixture
def v1_key_file(key_dir: Path) -> Path:
    path = key_dir / "audit_hmac_v1.key"
    path.write_bytes(b"v1-secret-do-not-share-32-bytes-min-len")
    return path


@pytest.fixture
def v2_key_file(key_dir: Path) -> Path:
    path = key_dir / "audit_hmac_v2.key"
    path.write_bytes(b"v2-secret-do-not-share-32-bytes-min-len")
    return path


@pytest.fixture
def keyring(v1_key_file: Path) -> HMACKeyRing:
    return HMACKeyRing(
        keys={"v1": HMACKey(key_id="v1", secret=v1_key_file.read_bytes())},
        active_id="v1",
    )


@pytest.fixture(autouse=True)
def _isolated_audit_logger():
    """Reset audit namespace loggers between tests so handlers don't pile up."""
    saved_state = {
        logger.name: (list(logger.handlers), logger.propagate, logger.level)
        for logger in _audit_loggers()
    }
    for logger in _audit_loggers():
        logger.handlers.clear()
    yield
    for logger in _audit_loggers():
        for handler in logger.handlers:
            handler.close()
        logger.handlers.clear()
        if logger.name in saved_state:
            handlers, propagate, level = saved_state[logger.name]
            logger.handlers = handlers
            logger.propagate = propagate
            logger.setLevel(level)
        else:
            logger.propagate = True
            logger.setLevel(logging.NOTSET)


def _span(
    raw: str,
    value: str,
    entity_type: EntityType = EntityType.PHONE_MOBILE,
    *,
    risk_level: RiskLevel = RiskLevel.P1,
    action: Action = Action.MASK,
    sources: tuple[str, ...] = ("regex",),
    detector_ids: tuple[str, ...] = ("regex.phone.kr",),
    reason_codes: tuple[str, ...] = ("regex.phone",),
    score: float = 0.94,
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
        action=action,
        reason_codes=reason_codes,
        detector_ids=detector_ids,
    )


def _request(raw: str) -> GuardrailRequest:
    return GuardrailRequest(text=raw, request_id="req-test-0001")


def _audit_loggers() -> list[logging.Logger]:
    prefix = f"{AuditLogger.LOGGER_NAME}."
    names = {AuditLogger.LOGGER_NAME}
    names.update(
        name
        for name, value in logging.root.manager.loggerDict.items()
        if isinstance(value, logging.Logger) and name.startswith(prefix)
    )
    return [logging.getLogger(name) for name in sorted(names)]


def _handlers_for_log_path(log_path: Path) -> list[logging.Handler]:
    target = log_path.resolve()
    return [
        handler
        for logger in _audit_loggers()
        for handler in logger.handlers
        if getattr(handler, "baseFilename", None) is not None
        and Path(getattr(handler, "baseFilename")).resolve() == target
    ]


def _read_jsonl(log_path: Path) -> list[dict[str, object]]:
    if not log_path.exists():
        return []
    return [
        json.loads(line)
        for line in log_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


# ============================================================
# HMACKeyRing — hybrid env path + .key file
# ============================================================


def test_keyring_from_env_loads_active_key_and_versioned_keys(
    monkeypatch: pytest.MonkeyPatch, v1_key_file: Path, v2_key_file: Path
) -> None:
    monkeypatch.setenv("AUDIT_HMAC_KEY_ACTIVE", "v2")
    monkeypatch.setenv("AUDIT_HMAC_KEY_PATH_V1", str(v1_key_file))
    monkeypatch.setenv("AUDIT_HMAC_KEY_PATH_V2", str(v2_key_file))

    ring = HMACKeyRing.from_env()

    assert ring.active_key_id == "v2"
    assert set(ring.known_key_ids) == {"v1", "v2"}


def test_keyring_from_env_rejects_missing_active_id(
    monkeypatch: pytest.MonkeyPatch, v1_key_file: Path
) -> None:
    monkeypatch.delenv("AUDIT_HMAC_KEY_ACTIVE", raising=False)
    monkeypatch.setenv("AUDIT_HMAC_KEY_PATH_V1", str(v1_key_file))

    with pytest.raises(AuditKeyringError) as exc_info:
        HMACKeyRing.from_env()

    # Critically: the error must not leak the key file path or its bytes.
    assert str(v1_key_file) not in str(exc_info.value)
    assert "secret" not in str(exc_info.value).lower()


def test_keyring_from_env_rejects_missing_key_file(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("AUDIT_HMAC_KEY_ACTIVE", "v1")
    monkeypatch.setenv("AUDIT_HMAC_KEY_PATH_V1", str(tmp_path / "does-not-exist.key"))

    with pytest.raises(AuditKeyringError):
        HMACKeyRing.from_env()


def test_keyring_from_env_rejects_empty_key_file(
    monkeypatch: pytest.MonkeyPatch, key_dir: Path
) -> None:
    empty = key_dir / "empty.key"
    empty.write_bytes(b"")
    monkeypatch.setenv("AUDIT_HMAC_KEY_ACTIVE", "v1")
    monkeypatch.setenv("AUDIT_HMAC_KEY_PATH_V1", str(empty))

    with pytest.raises(AuditKeyringError):
        HMACKeyRing.from_env()


def test_keyring_from_env_rejects_key_file_shorter_than_minimum(
    monkeypatch: pytest.MonkeyPatch, key_dir: Path
) -> None:
    short = key_dir / "short.key"
    short.write_bytes(b"a" * (HMACKeyRing.MIN_KEY_BYTES - 1))
    monkeypatch.setenv("AUDIT_HMAC_KEY_ACTIVE", "v1")
    monkeypatch.setenv("AUDIT_HMAC_KEY_PATH_V1", str(short))

    with pytest.raises(AuditKeyringError) as exc_info:
        HMACKeyRing.from_env()

    assert str(HMACKeyRing.MIN_KEY_BYTES) in str(exc_info.value)
    assert str(short) not in str(exc_info.value)


def test_keyring_from_env_preserves_key_file_bytes_exactly(
    monkeypatch: pytest.MonkeyPatch, key_dir: Path
) -> None:
    raw_key = b"\n" + (b"0123456789abcdef" * 2) + b" \t\r\n"
    key_file = key_dir / "whitespace.key"
    key_file.write_bytes(raw_key)
    monkeypatch.setenv("AUDIT_HMAC_KEY_ACTIVE", "v1")
    monkeypatch.setenv("AUDIT_HMAC_KEY_PATH_V1", str(key_file))

    ring = HMACKeyRing.from_env()
    expected_hex = hmac.new(raw_key, b"value", hashlib.sha256).hexdigest()

    assert ring.sign("value") == f"hmac-sha256:v1:{expected_hex}"


def test_keyring_from_env_requires_at_least_one_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("AUDIT_HMAC_KEY_ACTIVE", "v1")
    # No AUDIT_HMAC_KEY_PATH_* env vars set.
    for env_name in list(__import__("os").environ):
        if env_name.startswith("AUDIT_HMAC_KEY_PATH_"):
            monkeypatch.delenv(env_name, raising=False)

    with pytest.raises(AuditKeyringError):
        HMACKeyRing.from_env(env={"AUDIT_HMAC_KEY_ACTIVE": "v1"})


def test_keyring_sign_produces_hmac_prefixed_digest(keyring: HMACKeyRing) -> None:
    digest = keyring.sign("010-1234-5678")

    assert digest.startswith("hmac-sha256:v1:")
    # Hex digest segment is 64 hex chars for SHA-256.
    hex_part = digest.rsplit(":", maxsplit=1)[-1]
    assert len(hex_part) == 64
    assert all(c in "0123456789abcdef" for c in hex_part)


def test_keyring_sign_is_deterministic_for_same_input(keyring: HMACKeyRing) -> None:
    assert keyring.sign("hello") == keyring.sign("hello")
    assert keyring.sign("hello") != keyring.sign("world")


def test_keyring_supports_rotation_back_verification(
    v1_key_file: Path, v2_key_file: Path
) -> None:
    ring = HMACKeyRing(
        keys={
            "v1": HMACKey(key_id="v1", secret=v1_key_file.read_bytes()),
            "v2": HMACKey(key_id="v2", secret=v2_key_file.read_bytes()),
        },
        active_id="v2",
    )

    active_digest = ring.sign("010-1234-5678")
    legacy_digest = ring.sign("010-1234-5678", key_id="v1")

    assert active_digest.startswith("hmac-sha256:v2:")
    assert legacy_digest.startswith("hmac-sha256:v1:")
    assert active_digest != legacy_digest


def test_keyring_rejects_unknown_key_id(keyring: HMACKeyRing) -> None:
    with pytest.raises(AuditKeyringError):
        keyring.sign("value", key_id="v99")


def test_keyring_init_rejects_empty_keys_dict() -> None:
    with pytest.raises(AuditKeyringError):
        HMACKeyRing(keys={}, active_id="v1")


def test_keyring_init_accepts_default_minimum_key_length() -> None:
    ring = HMACKeyRing(
        keys={
            "v1": HMACKey(
                key_id="v1",
                secret=b"a" * HMACKeyRing.MIN_KEY_BYTES,
            )
        },
        active_id="v1",
    )

    assert ring.sign("value").startswith("hmac-sha256:v1:")


def test_keyring_init_rejects_secret_shorter_than_default_minimum() -> None:
    with pytest.raises(AuditKeyringError) as exc_info:
        HMACKeyRing(
            keys={
                "v1": HMACKey(
                    key_id="v1",
                    secret=b"a" * (HMACKeyRing.MIN_KEY_BYTES - 1),
                )
            },
            active_id="v1",
        )

    assert str(HMACKeyRing.MIN_KEY_BYTES) in str(exc_info.value)


def test_keyring_init_rejects_active_id_not_in_keys() -> None:
    with pytest.raises(AuditKeyringError):
        HMACKeyRing(
            keys={"v1": HMACKey(key_id="v1", secret=b"secret")},
            active_id="v2",
        )


# ============================================================
# scan_audit_payload — Audit-Safe regex + field whitelist
# ============================================================


def test_scan_passes_clean_payload() -> None:
    scan_audit_payload({
        "event_type": "pii_detection",
        "entity_type": "PERSON_NAME",
        "reason_codes": ["regex.phone", "context.boost.field_label"],
        "value_hash": "hmac-sha256:v1:a1b2c3d4",
        "request_id": "req-test-0001",
    })


def test_scan_rejects_phone_pattern_in_reason_codes() -> None:
    with pytest.raises(AuditPayloadLeakError) as exc_info:
        scan_audit_payload({
            "event_type": "pii_detection",
            "reason_codes": ["context.boost.match:010-1234-5678"],
        })

    # The exception message must name the pattern but not the matched value.
    assert "phone_mobile_kr" in str(exc_info.value)
    assert "010-1234-5678" not in str(exc_info.value)


def test_scan_rejects_email_pattern() -> None:
    with pytest.raises(AuditPayloadLeakError) as exc_info:
        scan_audit_payload({
            "event_type": "pii_detection",
            "reason_codes": ["user@example.com"],
        })

    assert "email" in str(exc_info.value)
    assert "user@example.com" not in str(exc_info.value)


def test_scan_rejects_rrn_pattern() -> None:
    with pytest.raises(AuditPayloadLeakError):
        scan_audit_payload({
            "event_type": "pii_detection",
            "reason_codes": ["900101-1234567"],
        })


def test_scan_rejects_credit_card_pattern() -> None:
    with pytest.raises(AuditPayloadLeakError):
        scan_audit_payload({
            "event_type": "pii_detection",
            "reason_codes": ["1234-5678-9012-3456"],
        })


@pytest.mark.parametrize(
    ("pattern_name", "raw_value"),
    [
        ("api_key_secret", "sk-AbC123xYz987TokenValue"),
        ("bank_account", "110-123-456789"),
        ("business_reg_no", "123-45-67890"),
        ("ip_address", "8.8.8.8"),
        ("mac_address", "AA:BB:CC:DD:EE:FF"),
    ],
)
def test_scan_rejects_structured_pii_examples_without_leaking_value(
    pattern_name: str, raw_value: str
) -> None:
    with pytest.raises(AuditPayloadLeakError) as exc_info:
        scan_audit_payload({
            "event_type": "pii_detection",
            "reason_codes": [f"context.leak:{raw_value}"],
        })

    message = str(exc_info.value)
    assert pattern_name in message
    assert raw_value not in message


def test_scan_ignores_value_hash_field_even_when_hex_runs_look_numeric() -> None:
    # Hex digest could contain stretches of digits that match patterns; the
    # scanner must skip this field to avoid false positives.
    scan_audit_payload({
        "event_type": "pii_detection",
        "value_hash": "hmac-sha256:v1:0123456789012345678901234567890123456789",
        "reason_codes": ["regex.phone"],
    })


def test_scan_ignores_key_id_field_even_when_it_looks_like_mac_address() -> None:
    scan_audit_payload({
        "event_type": "pii_detection",
        "key_id": "AA:BB:CC:DD:EE:FF",
        "reason_codes": ["regex.mac"],
    })


def test_scan_skips_non_string_numeric_metadata() -> None:
    scan_audit_payload({
        "event_type": "pii_detection",
        "timestamp_epoch": 1234567890.123,
        "score": 8.8,
        "span_length": 110123456789,
        "numeric_tuple": (1234567890, 110123456789),
        "numeric_list": [1234567890, 110123456789],
        "reason_codes": ["regex.phone"],
    })


def test_scan_allows_non_pii_request_id_field() -> None:
    scan_audit_payload({
        "event_type": "pii_detection",
        "request_id": "req-20260514-0102030405060708",
        "reason_codes": ["regex.phone"],
    })


def test_scan_rejects_request_id_containing_raw_phone_without_leaking_value() -> None:
    raw_value = "010-1234-5678"

    with pytest.raises(AuditPayloadLeakError) as exc_info:
        scan_audit_payload({
            "event_type": "pii_detection",
            "request_id": raw_value,
            "reason_codes": ["regex.phone"],
        })

    message = str(exc_info.value)
    assert "phone_mobile_kr" in message
    assert raw_value not in message


def test_scan_handles_list_and_tuple_values() -> None:
    with pytest.raises(AuditPayloadLeakError):
        scan_audit_payload({
            "event_type": "pii_detection",
            "reason_codes": ("context.boost", "010-1234-5678"),
        })


# ============================================================
# AuditLogger — JSONL sink, propagate=False, fail-closed
# ============================================================


def test_emit_writes_single_jsonl_line(
    keyring: HMACKeyRing, tmp_path: Path
) -> None:
    log_path = tmp_path / "audit.log.jsonl"
    raw = "연락처 010-1234-5678 입니다."
    span = _span(raw, "010-1234-5678")
    logger = AuditLogger(keyring=keyring, log_path=log_path)

    event = logger.emit(span=span, request=_request(raw))

    written = log_path.read_text(encoding="utf-8").strip().splitlines()
    assert len(written) == 1
    decoded = json.loads(written[0])
    assert decoded["event_type"] == "pii_detection"
    assert decoded["entity_type"] == "PHONE_MOBILE"
    assert decoded["action"] == "mask"
    assert decoded["value_hash"].startswith("hmac-sha256:v1:")
    assert decoded["raw_value_logged"] is False
    assert decoded["key_id"] == "v1"
    assert event.span_length == len("010-1234-5678")


def test_emit_reuses_effective_request_id_when_request_id_is_none(
    keyring: HMACKeyRing, tmp_path: Path
) -> None:
    log_path = tmp_path / "audit.log.jsonl"
    raw = "연락처 010-1234-5678, 메일 test@example.com 입니다."
    request = GuardrailRequest(text=raw, request_id=None)
    phone_span = _span(raw, "010-1234-5678")
    email_span = _span(
        raw,
        "test@example.com",
        entity_type=EntityType.EMAIL,
        detector_ids=("regex.email",),
        reason_codes=("regex.email",),
    )
    logger = AuditLogger(keyring=keyring, log_path=log_path)

    first = logger.emit(span=phone_span, request=request)
    second = logger.emit(span=email_span, request=request)

    assert request.request_id is None
    assert first.request_id == second.request_id == request.effective_request_id
    records = _read_jsonl(log_path)
    assert [record["request_id"] for record in records] == [
        request.effective_request_id,
        request.effective_request_id,
    ]


def test_emit_preserves_explicit_request_id(
    keyring: HMACKeyRing, tmp_path: Path
) -> None:
    log_path = tmp_path / "audit.log.jsonl"
    raw = "연락처 010-1234-5678 입니다."
    request = _request(raw)
    span = _span(raw, "010-1234-5678")
    logger = AuditLogger(keyring=keyring, log_path=log_path)

    event = logger.emit(span=span, request=request)

    assert event.request_id == "req-test-0001"
    assert event.request_id == request.effective_request_id


def test_emit_default_does_not_log_detailed_detector_ids(
    keyring: HMACKeyRing, tmp_path: Path
) -> None:
    log_path = tmp_path / "audit.log.jsonl"
    raw = "연락처 010-1234-5678 입니다."
    span = _span(raw, "010-1234-5678", detector_ids=("regex.phone.kr",))
    logger = AuditLogger(keyring=keyring, log_path=log_path, verbose=False)

    event = logger.emit(span=span, request=_request(raw))

    assert event.detector_ids == ()
    assert "detector_ids" not in event.to_dict()
    decoded = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert "detector_ids" not in decoded
    # reason_codes stays so analysts can see source family.
    assert "regex.phone" in decoded["reason_codes"]


def test_emit_verbose_mode_includes_detector_ids(
    keyring: HMACKeyRing, tmp_path: Path
) -> None:
    log_path = tmp_path / "audit.log.jsonl"
    raw = "연락처 010-1234-5678 입니다."
    span = _span(raw, "010-1234-5678", detector_ids=("regex.phone.kr",))
    logger = AuditLogger(keyring=keyring, log_path=log_path, verbose=True)

    event = logger.emit(span=span, request=_request(raw))

    assert event.detector_ids == ("regex.phone.kr",)
    assert event.to_dict()["detector_ids"] == ["regex.phone.kr"]
    decoded = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert decoded["detector_ids"] == ["regex.phone.kr"]


def test_emit_validates_span_against_request_text_before_write(
    keyring: HMACKeyRing, tmp_path: Path
) -> None:
    log_path = tmp_path / "audit.log.jsonl"
    raw = "고객명 홍길동 입니다."
    span = PIISpan(
        start=0,
        end=4,
        text="홍길동",
        entity_type=EntityType.PERSON_NAME,
        score=0.91,
        sources=("ner",),
        risk_level=RiskLevel.P1,
        action=Action.MASK,
        detector_ids=("ner.finetuned",),
        reason_codes=("ner.argmax",),
    )
    logger = AuditLogger(keyring=keyring, log_path=log_path)

    with pytest.raises(InvalidOffsetError):
        logger.emit(span=span, request=_request(raw))

    assert _read_jsonl(log_path) == []


def test_emit_preserves_sources_without_auto_validator(
    keyring: HMACKeyRing, tmp_path: Path
) -> None:
    log_path = tmp_path / "audit.log.jsonl"
    raw = "연락처 010-1234-5678 입니다."
    span = _span(raw, "010-1234-5678", sources=("regex",))
    logger = AuditLogger(keyring=keyring, log_path=log_path)

    event = logger.emit(span=span, request=_request(raw))

    assert event.sources == ("regex",)
    assert _read_jsonl(log_path)[0]["sources"] == ["regex"]


def test_emit_preserves_existing_validator_source(
    keyring: HMACKeyRing, tmp_path: Path
) -> None:
    log_path = tmp_path / "audit.log.jsonl"
    raw = "연락처 010-1234-5678 입니다."
    span = _span(raw, "010-1234-5678", sources=("regex", "validator"))
    logger = AuditLogger(keyring=keyring, log_path=log_path)

    event = logger.emit(span=span, request=_request(raw))

    assert event.sources == ("regex", "validator")
    assert _read_jsonl(log_path)[0]["sources"] == ["regex", "validator"]


def test_audit_logger_isolates_different_log_paths_with_mixed_verbosity(
    keyring: HMACKeyRing, tmp_path: Path
) -> None:
    non_verbose_path = tmp_path / "audit-default.log.jsonl"
    verbose_path = tmp_path / "audit-verbose.log.jsonl"
    raw = "연락처 010-1234-5678 입니다."
    span = _span(
        raw,
        "010-1234-5678",
        detector_ids=("regex.phone.kr", "context.korean"),
    )
    non_verbose_logger = AuditLogger(
        keyring=keyring,
        log_path=non_verbose_path,
        verbose=False,
    )
    verbose_logger = AuditLogger(
        keyring=keyring,
        log_path=verbose_path,
        verbose=True,
    )

    verbose_logger.emit(span=span, request=_request(raw))

    verbose_records = _read_jsonl(verbose_path)
    assert len(verbose_records) == 1
    assert verbose_records[0]["detector_ids"] == [
        "regex.phone.kr",
        "context.korean",
    ]
    assert _read_jsonl(non_verbose_path) == []

    non_verbose_logger.emit(span=span, request=_request(raw))

    non_verbose_records = _read_jsonl(non_verbose_path)
    assert len(non_verbose_records) == 1
    assert "detector_ids" not in non_verbose_records[0]
    assert _read_jsonl(verbose_path) == verbose_records


def test_audit_logger_same_log_path_reinit_does_not_duplicate_handlers(
    keyring: HMACKeyRing, tmp_path: Path
) -> None:
    log_path = tmp_path / "audit.log.jsonl"
    raw = "연락처 010-1234-5678 입니다."
    span = _span(raw, "010-1234-5678", detector_ids=("regex.phone.kr",))
    non_verbose_logger = AuditLogger(
        keyring=keyring,
        log_path=log_path,
        verbose=False,
    )
    verbose_logger = AuditLogger(
        keyring=keyring,
        log_path=log_path,
        verbose=True,
    )

    assert len(_handlers_for_log_path(log_path)) == 1

    verbose_logger.emit(span=span, request=_request(raw))
    records = _read_jsonl(log_path)
    assert len(records) == 1
    assert records[0]["detector_ids"] == ["regex.phone.kr"]

    non_verbose_logger.emit(span=span, request=_request(raw))
    records = _read_jsonl(log_path)
    assert len(records) == 2
    assert "detector_ids" not in records[1]


def test_emit_forces_raw_value_logged_false_even_if_upstream_set_true(
    keyring: HMACKeyRing, tmp_path: Path
) -> None:
    log_path = tmp_path / "audit.log.jsonl"
    raw = "연락처 010-1234-5678 입니다."
    span = _span(raw, "010-1234-5678")
    logger = AuditLogger(keyring=keyring, log_path=log_path)

    event = logger.build_event(span=span, request=_request(raw))
    decoded = logger._to_log_dict(event)

    assert decoded["raw_value_logged"] is False


def test_emit_fail_closed_when_reason_codes_contain_phone(
    keyring: HMACKeyRing, tmp_path: Path
) -> None:
    log_path = tmp_path / "audit.log.jsonl"
    raw = "연락처 010-1234-5678 입니다."
    # Inject a leaky reason_code that smuggles raw phone into the event.
    span = _span(
        raw,
        "010-1234-5678",
        reason_codes=("regex.phone", "context.boost.match:010-1234-5678"),
    )
    logger = AuditLogger(keyring=keyring, log_path=log_path)

    with pytest.raises(AuditPayloadLeakError):
        logger.emit(span=span, request=_request(raw))

    # The log file must not have been touched (fail-closed).
    assert not log_path.exists() or log_path.read_text(encoding="utf-8") == ""


def test_emit_fail_closed_when_request_id_contains_phone(
    keyring: HMACKeyRing, tmp_path: Path
) -> None:
    log_path = tmp_path / "audit.log.jsonl"
    raw = "?곕씫泥?010-1234-5678 ?낅땲??"
    span = _span(raw, "010-1234-5678")
    request = GuardrailRequest(text=raw, request_id="010-1234-5678")
    logger = AuditLogger(keyring=keyring, log_path=log_path)

    with pytest.raises(AuditPayloadLeakError) as exc_info:
        logger.emit(span=span, request=request)

    message = str(exc_info.value)
    assert "phone_mobile_kr" in message
    assert "010-1234-5678" not in message
    assert not log_path.exists() or log_path.read_text(encoding="utf-8") == ""


def test_audit_logger_propagate_is_disabled(
    keyring: HMACKeyRing, tmp_path: Path
) -> None:
    logger = AuditLogger(keyring=keyring, log_path=tmp_path / "audit.log.jsonl")

    base_logger = logging.getLogger(AuditLogger.LOGGER_NAME)
    assert base_logger.propagate is False
    assert logger._logger.propagate is False


def test_audit_logger_does_not_duplicate_handlers_on_reinit(
    keyring: HMACKeyRing, tmp_path: Path
) -> None:
    log_path = tmp_path / "audit.log.jsonl"
    AuditLogger(keyring=keyring, log_path=log_path)
    AuditLogger(keyring=keyring, log_path=log_path)

    assert len(_handlers_for_log_path(log_path)) == 1


def test_audit_lines_do_not_appear_on_root_logger(
    keyring: HMACKeyRing, tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    raw = "연락처 010-1234-5678 입니다."
    span = _span(raw, "010-1234-5678")
    logger = AuditLogger(keyring=keyring, log_path=tmp_path / "audit.log.jsonl")

    with caplog.at_level(logging.DEBUG, logger=""):
        logger.emit(span=span, request=_request(raw))

    # Root logger capture must not see any audit-prefixed messages.
    for record in caplog.records:
        assert record.name != AuditLogger.LOGGER_NAME
        assert not record.name.startswith(f"{AuditLogger.LOGGER_NAME}.")


def test_emit_event_span_length_matches_raw_offset_window(
    keyring: HMACKeyRing, tmp_path: Path
) -> None:
    raw = "고객명 홍길동 입니다."
    span = _span(
        raw,
        "홍길동",
        entity_type=EntityType.PERSON_NAME,
        detector_ids=("ner.finetuned",),
        reason_codes=("ner.argmax",),
    )
    logger = AuditLogger(keyring=keyring, log_path=tmp_path / "audit.log.jsonl")

    event = logger.emit(span=span, request=_request(raw))

    assert event.span_length == 3  # 3 Hangul chars
