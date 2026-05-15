"""M8 audit logger for Korean PII Guardrail v0.2.

Implements ``docs/09_COMPLIANCE_AND_AUDIT_SPEC`` with four guarantees:

1. **Hybrid HMAC key storage** — ``.env`` carries only key file *paths*, not
   key material. Actual key bytes live in ``.key`` files outside application
   config and are loaded into ``HMACKeyRing`` once at startup. The keyring
   never re-injects values into ``os.environ``. Multiple keys can co-exist
   for rotation; ``key_id`` is recorded in every event.
2. **Isolated audit logger** — uses ``logging.getLogger("audit")`` with
   ``propagate=False`` so audit records never reach root logger handlers
   (preventing cross-mix with ``app.log``). JSONL is written to a
   ``RotatingFileHandler`` (size-based) for disk safety. Retention
   (spec §4 ``retention_ttl_days``) is a separate concern handled by
   ``scripts/cleanup_audit_logs.py``.
3. **Two-layer raw PII zero defense** — ``AuditEvent`` dataclass enforces
   ``raw_value_logged=False`` and HMAC-prefixed ``value_hash`` at the
   structural layer. Immediately before each write the *serialized* payload
   is scanned with a high-precision Audit-Safe regex subset (phone / RRN /
   credit_card / email). A match raises ``AuditPayloadLeakError`` and the
   event is dropped (fail-closed).
4. **detector_ids vs reason_codes split** — ``detector_ids`` carries detailed
   matcher ids for analyst-level forensics; ``reason_codes`` only contains
   generalized rule families. Default emission excludes ``detector_ids`` so
   operators with file-read access cannot reconstruct re-identification
   hints. Verbose mode opts ``detector_ids`` back in for privileged review.

This module is self-contained: any pipeline component that has a resolved
``PIISpan`` and the original ``GuardrailRequest`` can call ``AuditLogger.emit``.
"""

from __future__ import annotations

import hashlib
import hmac
import json
import logging
import os
import re
import time
from collections.abc import Mapping
from dataclasses import dataclass
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .enums import Action, EntityType, OutputTarget, RiskLevel, Source
from .schema import AuditEvent, GuardrailRequest, PIISpan


# ============================================================
# HMAC keyring — hybrid .env path + .key file model
# ============================================================


class AuditKeyringError(ValueError):
    """Raised when HMAC keyring configuration is missing or invalid."""


@dataclass(frozen=True)
class HMACKey:
    """A single HMAC key + its public id. ``secret`` is in-memory only."""

    key_id: str
    secret: bytes


class HMACKeyRing:
    """Hybrid HMAC key storage for audit value hashing.

    Reads key file *paths* from environment variables and loads each key's
    bytes into memory. The path indirection plus loading-into-attribute (never
    back into ``os.environ``) avoids three failure modes:

    - ``env var only``: keys leak via ``/proc/<pid>/environ``, ``ps auxe``,
      and CI/CD debug logs (spec §7 ``Key storage | application config와 분리``
      violation).
    - ``file with chmod 600 only``: ineffective on Windows NTFS without
      explicit ``icacls`` setup, and POSIX perms are not preserved across
      git checkouts.
    - ``KMS``: per-event KMS calls add network latency and IAM debugging
      overhead beyond the project's threat model.

    Active key id selection:
        ``AUDIT_HMAC_KEY_ACTIVE=v1``

    Key path entries (one per key version):
        ``AUDIT_HMAC_KEY_PATH_V1=./keys/audit_hmac_v1.key``
        ``AUDIT_HMAC_KEY_PATH_V2=./keys/audit_hmac_v2.key``

    Rotation strategy is manual: ship a new ``.key`` file, register its path
    in the new env var, flip ``AUDIT_HMAC_KEY_ACTIVE`` to its id. Old keys
    remain available for back-verification but are not used to sign new
    events.
    """

    ENV_ACTIVE_KEY_ID = "AUDIT_HMAC_KEY_ACTIVE"
    ENV_KEY_PATH_PREFIX = "AUDIT_HMAC_KEY_PATH_"

    def __init__(self, *, keys: Mapping[str, HMACKey], active_id: str) -> None:
        if not keys:
            raise AuditKeyringError("HMAC keyring requires at least one key")
        normalized = {kid.lower(): key for kid, key in keys.items()}
        active_normalized = active_id.lower()
        if active_normalized not in normalized:
            raise AuditKeyringError("Active HMAC key id is not present in the ring")
        self._keys: dict[str, HMACKey] = dict(normalized)
        self._active_id: str = active_normalized

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> "HMACKeyRing":
        env_map = os.environ if env is None else env
        active = env_map.get(cls.ENV_ACTIVE_KEY_ID)
        if not active:
            raise AuditKeyringError(
                f"Missing env var {cls.ENV_ACTIVE_KEY_ID} — set the active HMAC key id"
            )

        keys: dict[str, HMACKey] = {}
        for env_name, raw_path in env_map.items():
            if not env_name.startswith(cls.ENV_KEY_PATH_PREFIX):
                continue
            if not raw_path:
                raise AuditKeyringError(
                    f"Env var {env_name} is empty — must point to a key file"
                )
            key_id = env_name[len(cls.ENV_KEY_PATH_PREFIX) :].lower()
            path = Path(raw_path)
            if not path.is_file():
                raise AuditKeyringError(
                    f"HMAC key file referenced by {env_name} does not exist"
                )
            secret = path.read_bytes().strip()
            if not secret:
                raise AuditKeyringError(
                    f"HMAC key file referenced by {env_name} is empty"
                )
            keys[key_id] = HMACKey(key_id=key_id, secret=secret)

        if not keys:
            raise AuditKeyringError(
                f"No keys found — define at least one {cls.ENV_KEY_PATH_PREFIX}<ID> env var"
            )

        return cls(keys=keys, active_id=active)

    @property
    def active_key_id(self) -> str:
        return self._active_id

    @property
    def known_key_ids(self) -> tuple[str, ...]:
        return tuple(sorted(self._keys))

    def sign(self, value: str, *, key_id: str | None = None) -> str:
        """Return ``hmac-sha256:<key_id>:<hexdigest>`` for the given value.

        ``key_id=None`` selects the active key. The format mirrors the
        contract used by ``M7 SuffixPreservingMasker`` so audit hashes are
        comparable with masker output for the same value.
        """
        chosen = (key_id or self._active_id).lower()
        if chosen not in self._keys:
            raise AuditKeyringError("Unknown HMAC key id")
        secret = self._keys[chosen].secret
        digest = hmac.new(secret, value.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"hmac-sha256:{chosen}:{digest}"


# ============================================================
# Audit-Safe regex scan — high-precision PII subset + field whitelist
# ============================================================


class AuditPayloadLeakError(ValueError):
    """Raised when a serialized audit payload matches a raw PII pattern.

    The exception message intentionally identifies only the matched pattern
    *name*, never the matched text — otherwise the exception itself would
    leak the very raw value the audit logger refuses to record.
    """


# High-precision Korean PII patterns. Deliberately NOT the full Layer 0 set:
# the Layer 0 regex bank includes broad NAME and ADDRESS patterns that would
# false-positive against value hashes, request ids, and entity_type / source
# enum strings inside audit payloads.
_AUDIT_SAFE_PATTERNS: dict[str, re.Pattern[str]] = {
    "phone_mobile_kr": re.compile(r"\b01[016789][-\s]?\d{3,4}[-\s]?\d{4}\b"),
    "phone_landline_kr": re.compile(r"\b0[2-6]\d?[-\s]?\d{3,4}[-\s]?\d{4}\b"),
    "rrn_kr": re.compile(r"\b\d{6}[-\s][1-4]\d{6}\b"),
    "credit_card": re.compile(r"\b\d{4}[-\s]\d{4}[-\s]\d{4}[-\s]\d{4}\b"),
    "email": re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"),
}


# Fields excluded from regex scan. These are controlled metadata that never
# carry raw PII but can trigger false positives against the patterns above:
#   - value_hash: 64-char hex digest that may include 13-digit numeric runs
#   - request_id / key_id: opaque ids that may include 16-digit numeric runs
#   - timestamp_epoch / score / span_length: numeric, not regex-relevant
_SCAN_EXCLUDED_FIELDS: frozenset[str] = frozenset({
    "value_hash",
    "request_id",
    "key_id",
    "timestamp_epoch",
    "score",
    "span_length",
})


def _scannable_text(event_dict: Mapping[str, object]) -> str:
    """Concatenate audit fields that can carry raw PII for regex scan.

    Numeric metadata and hash-style ids are excluded to avoid false positives
    against value hashes whose hex digits could otherwise match the credit
    card or phone patterns.
    """
    parts: list[str] = []
    for key, value in event_dict.items():
        if key in _SCAN_EXCLUDED_FIELDS:
            continue
        if isinstance(value, (list, tuple)):
            parts.extend(str(item) for item in value)
        elif isinstance(value, bool):
            parts.append(str(value))
        else:
            parts.append(str(value))
    return " ".join(parts)


def scan_audit_payload(event_dict: Mapping[str, object]) -> None:
    """Fail-closed PII leak scan over an audit event dict.

    Applied to controlled fields only (see ``_SCAN_EXCLUDED_FIELDS``).
    Raises ``AuditPayloadLeakError`` with the pattern *name* — never the
    matched text — so the exception itself cannot leak the offending value.
    """
    text = _scannable_text(event_dict)
    for name, pattern in _AUDIT_SAFE_PATTERNS.items():
        if pattern.search(text):
            raise AuditPayloadLeakError(
                f"Audit payload matches audit-safe pattern: {name}"
            )


# ============================================================
# AuditLogger — isolated named logger + size-rotating JSONL sink
# ============================================================


class AuditLogger:
    """Emit audit events to an isolated JSONL log file.

    ``logging.getLogger("audit")`` with ``propagate=False`` keeps audit
    records out of root logger handlers, so an accidental
    ``logger.info(raw_text)`` elsewhere in the application cannot leak raw
    PII into the audit stream. The sink is size-rotating; calendar-based
    retention is enforced by ``scripts/cleanup_audit_logs.py``.

    ``verbose=False`` (default) drops ``detector_ids`` from the serialized
    record. Per spec §8 the detailed detector ids are only available to
    privileged reviewers with original-data access; storing them in the
    default audit file would defeat the purpose of the generalized
    ``reason_codes`` field.
    """

    LOGGER_NAME = "audit"
    DEFAULT_MAX_BYTES = 100 * 1024 * 1024  # 100 MB per file
    DEFAULT_BACKUP_COUNT = 10

    def __init__(
        self,
        *,
        keyring: HMACKeyRing,
        log_path: Path,
        max_bytes: int = DEFAULT_MAX_BYTES,
        backup_count: int = DEFAULT_BACKUP_COUNT,
        verbose: bool = False,
    ) -> None:
        self._keyring = keyring
        self._verbose = verbose
        self._log_path = Path(log_path)
        self._log_path.parent.mkdir(parents=True, exist_ok=True)

        logger = logging.getLogger(self.LOGGER_NAME)
        logger.setLevel(logging.INFO)
        logger.propagate = False

        target = str(self._log_path.resolve())
        existing = any(
            getattr(handler, "baseFilename", None) == target
            for handler in logger.handlers
        )
        if not existing:
            handler = RotatingFileHandler(
                self._log_path,
                maxBytes=max_bytes,
                backupCount=backup_count,
                encoding="utf-8",
            )
            handler.setFormatter(logging.Formatter("%(message)s"))
            logger.addHandler(handler)

        self._logger = logger

    @property
    def log_path(self) -> Path:
        return self._log_path

    @property
    def verbose(self) -> bool:
        return self._verbose

    def build_event(
        self,
        *,
        span: PIISpan,
        request: GuardrailRequest,
        event_type: str = "pii_detection",
    ) -> AuditEvent:
        """Construct an AuditEvent from a resolved PIISpan + request.

        The span's raw text is HMAC-hashed via the active key. The raw text
        is used only as the input to the HMAC function and is never stored
        on the event or referenced by the dict view.
        """
        value_hash = self._keyring.sign(span.text)
        sources_with_audit = _append_unique(span.sources, Source.VALIDATOR.value)
        return AuditEvent(
            event_type=event_type,
            entity_type=span.entity_type,
            score=span.score,
            risk_level=span.risk_level,
            action=span.action,
            request_id=request.effective_request_id,
            timestamp_epoch=time.time(),
            policy_profile=request.policy_profile,
            output_target=request.output_target,
            sources=sources_with_audit,
            detector_ids=span.detector_ids,
            value_hash=value_hash,
            span_length=span.end - span.start,
            reason_codes=span.reason_codes,
            raw_value_logged=False,
        )

    def emit(
        self,
        *,
        span: PIISpan,
        request: GuardrailRequest,
        event_type: str = "pii_detection",
    ) -> AuditEvent:
        """Build, scan, and write a single audit event.

        Returns the constructed ``AuditEvent`` so callers can attach it to
        ``GuardrailResponse.audit_events`` without re-building. Raises
        ``AuditPayloadLeakError`` if the audit-safe regex scan fires; in
        that case the file write is skipped entirely (fail-closed).
        """
        event = self.build_event(span=span, request=request, event_type=event_type)
        payload_dict = self._to_log_dict(event)
        scan_audit_payload(payload_dict)
        self._logger.info(json.dumps(payload_dict, ensure_ascii=False, separators=(",", ":")))
        return event

    def _to_log_dict(self, event: AuditEvent) -> dict[str, object]:
        """Render the event for file writing.

        Always strips ``detector_ids`` unless verbose mode is on. Always
        stamps ``key_id`` so each line is verifiable against a specific
        keyring version, and always forces ``raw_value_logged=False`` as a
        second-line defense against an upstream caller setting it True.
        """
        data = event.to_dict()
        data["key_id"] = self._keyring.active_key_id
        data["raw_value_logged"] = False
        if not self._verbose:
            data.pop("detector_ids", None)
        return data


def _append_unique(existing: tuple[str, ...], value: str) -> tuple[str, ...]:
    if value in existing:
        return existing
    return (*existing, value)


__all__ = [
    "AuditKeyringError",
    "AuditLogger",
    "AuditPayloadLeakError",
    "HMACKey",
    "HMACKeyRing",
    "scan_audit_payload",
]
