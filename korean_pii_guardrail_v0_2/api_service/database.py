"""SQLite persistence for the local product console.

This store persists only safe public response data. Raw request text is never
stored, and detected raw span values are checked before a row is written.
"""

from __future__ import annotations

import json
import sqlite3
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


class RawPIIStorageError(RuntimeError):
    """Raised when a persistence payload still contains detected raw PII."""


@dataclass(frozen=True)
class LogRecord:
    request_id: str
    created_at: str
    text_length: int
    blocked: bool
    masked_text: str | None
    latency_ms: float
    detected_span_count: int
    masked_span_count: int
    policy_profile: str
    output_target: str
    entity_counts: dict[str, int]
    risk_counts: dict[str, int]
    action_counts: dict[str, int]
    spans: list[dict[str, Any]]
    audit_events: list[dict[str, Any]]
    encrypted_raw_text: dict[str, Any] | None = None
    encrypted_raw_key_hint: str | None = None
    raw_value_logged: bool = False

    def summary(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "created_at": self.created_at,
            "text_length": self.text_length,
            "blocked": self.blocked,
            "latency_ms": round(self.latency_ms, 2),
            "detected_span_count": self.detected_span_count,
            "masked_span_count": self.masked_span_count,
            "policy_profile": self.policy_profile,
            "output_target": self.output_target,
            "entity_counts": self.entity_counts,
            "risk_counts": self.risk_counts,
            "action_counts": self.action_counts,
            "encrypted_raw_available": self.encrypted_raw_text is not None,
            "encrypted_raw_key_hint": self.encrypted_raw_key_hint,
            "raw_value_logged": False,
        }


class AuditStore:
    """Small SQLite store for local-console audit metadata."""

    def __init__(self, db_path: str | Path) -> None:
        self.path = Path(db_path).expanduser().resolve()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS guardrail_requests (
                    request_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    text_length INTEGER NOT NULL,
                    blocked INTEGER NOT NULL,
                    masked_text TEXT,
                    latency_ms REAL NOT NULL,
                    detected_span_count INTEGER NOT NULL,
                    masked_span_count INTEGER NOT NULL,
                    policy_profile TEXT NOT NULL,
                    output_target TEXT NOT NULL,
                    entity_counts_json TEXT NOT NULL,
                    risk_counts_json TEXT NOT NULL,
                    action_counts_json TEXT NOT NULL,
                    spans_json TEXT NOT NULL,
                    audit_events_json TEXT NOT NULL,
                    encrypted_raw_text_json TEXT,
                    encrypted_raw_key_hint TEXT,
                    raw_value_logged INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            self._ensure_column(conn, "encrypted_raw_text_json", "TEXT")
            self._ensure_column(conn, "encrypted_raw_key_hint", "TEXT")
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_guardrail_requests_created_at
                ON guardrail_requests(created_at DESC)
                """
            )

    def insert(self, record: LogRecord, *, raw_text: str) -> None:
        payload = {
            "masked_text": record.masked_text,
            "entity_counts": record.entity_counts,
            "risk_counts": record.risk_counts,
            "action_counts": record.action_counts,
            "spans": record.spans,
            "audit_events": record.audit_events,
            "encrypted_raw_text": record.encrypted_raw_text,
            "encrypted_raw_key_hint": record.encrypted_raw_key_hint,
        }
        _assert_detected_values_absent(payload, raw_text=raw_text, spans=record.spans)
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO guardrail_requests (
                    request_id, created_at, text_length, blocked, masked_text,
                    latency_ms, detected_span_count, masked_span_count,
                    policy_profile, output_target, entity_counts_json,
                    risk_counts_json, action_counts_json, spans_json,
                    audit_events_json, encrypted_raw_text_json,
                    encrypted_raw_key_hint, raw_value_logged
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    record.request_id,
                    record.created_at,
                    record.text_length,
                    int(record.blocked),
                    record.masked_text,
                    record.latency_ms,
                    record.detected_span_count,
                    record.masked_span_count,
                    record.policy_profile,
                    record.output_target,
                    json.dumps(record.entity_counts, ensure_ascii=False, sort_keys=True),
                    json.dumps(record.risk_counts, ensure_ascii=False, sort_keys=True),
                    json.dumps(record.action_counts, ensure_ascii=False, sort_keys=True),
                    json.dumps(record.spans, ensure_ascii=False, sort_keys=True),
                    json.dumps(record.audit_events, ensure_ascii=False, sort_keys=True),
                    (
                        json.dumps(
                            record.encrypted_raw_text,
                            ensure_ascii=False,
                            sort_keys=True,
                        )
                        if record.encrypted_raw_text is not None
                        else None
                    ),
                    record.encrypted_raw_key_hint,
                    0,
                ),
            )

    def list_logs(self, *, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        limit = max(1, min(limit, 500))
        offset = max(0, offset)
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT request_id, created_at, text_length, blocked, latency_ms,
                       detected_span_count, masked_span_count, policy_profile,
                       output_target, entity_counts_json, risk_counts_json,
                       action_counts_json, encrypted_raw_text_json,
                       encrypted_raw_key_hint, raw_value_logged
                FROM guardrail_requests
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (limit, offset),
            ).fetchall()
        return [_summary_from_row(row) for row in rows]

    def get_log(self, request_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT * FROM guardrail_requests WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        if row is None:
            return None
        return _detail_from_row(row)

    def get_encrypted_raw_text(self, request_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT encrypted_raw_text_json FROM guardrail_requests WHERE request_id = ?",
                (request_id,),
            ).fetchone()
        if row is None or row["encrypted_raw_text_json"] is None:
            return None
        decoded = json.loads(row["encrypted_raw_text_json"])
        if not isinstance(decoded, dict):
            return None
        return decoded

    def metrics(self) -> dict[str, Any]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT blocked, latency_ms, detected_span_count, masked_span_count,
                       entity_counts_json, risk_counts_json, action_counts_json
                FROM guardrail_requests
                """
            ).fetchall()
        entity_counts: Counter[str] = Counter()
        risk_counts: Counter[str] = Counter()
        action_counts: Counter[str] = Counter()
        latencies: list[float] = []
        total = len(rows)
        blocked = 0
        detected_spans = 0
        masked_spans = 0
        for row in rows:
            blocked += int(row["blocked"])
            detected_spans += int(row["detected_span_count"])
            masked_spans += int(row["masked_span_count"])
            latencies.append(float(row["latency_ms"]))
            entity_counts.update(_json_obj(row["entity_counts_json"]))
            risk_counts.update(_json_obj(row["risk_counts_json"]))
            action_counts.update(_json_obj(row["action_counts_json"]))
        return {
            "total_requests": total,
            "blocked_requests": blocked,
            "block_rate": (blocked / total) if total else 0.0,
            "detected_span_count": detected_spans,
            "masked_span_count": masked_spans,
            "average_latency_ms": (sum(latencies) / len(latencies)) if latencies else 0.0,
            "entity_counts": dict(entity_counts),
            "risk_counts": dict(risk_counts),
            "action_counts": dict(action_counts),
            "raw_value_logged": False,
        }

    @staticmethod
    def _ensure_column(conn: sqlite3.Connection, column_name: str, column_type: str) -> None:
        columns = {
            str(row["name"])
            for row in conn.execute("PRAGMA table_info(guardrail_requests)").fetchall()
        }
        if column_name not in columns:
            conn.execute(f"ALTER TABLE guardrail_requests ADD COLUMN {column_name} {column_type}")


def build_log_record(
    response: dict[str, Any],
    *,
    raw_text: str,
    encrypted_raw_text: dict[str, Any] | None = None,
    encrypted_raw_key_hint: str | None = None,
) -> LogRecord:
    spans = list(response.get("spans") or [])
    audit_events = list(response.get("audit_events") or [])
    entity_counts = Counter(span.get("entity_type", "UNKNOWN") for span in spans)
    risk_counts = Counter(span.get("risk_level", "UNKNOWN") for span in spans)
    action_counts = Counter(span.get("action", "unknown") for span in spans)
    metrics = response.get("metrics") or {}
    safe_masked_text = _safe_persisted_masked_text(
        response.get("masked_text"),
        raw_text=raw_text,
        spans=spans,
    )
    safe_encrypted_raw_key_hint = _safe_persisted_masked_text(
        encrypted_raw_key_hint,
        raw_text=raw_text,
        spans=spans,
    )
    return LogRecord(
        request_id=str(response["request_id"]),
        created_at=datetime.now(UTC).isoformat(),
        text_length=len(raw_text),
        blocked=bool(response.get("blocked")),
        masked_text=safe_masked_text,
        latency_ms=float(metrics.get("latency_ms", 0.0)),
        detected_span_count=int(metrics.get("detected_span_count", len(spans))),
        masked_span_count=int(metrics.get("masked_span_count", 0)),
        policy_profile=str(response.get("policy_profile", "strict")),
        output_target=str(response.get("output_target", "llm_input")),
        entity_counts=dict(entity_counts),
        risk_counts=dict(risk_counts),
        action_counts=dict(action_counts),
        spans=spans,
        audit_events=audit_events,
        encrypted_raw_text=encrypted_raw_text,
        encrypted_raw_key_hint=safe_encrypted_raw_key_hint,
    )


def _safe_persisted_masked_text(
    masked_text: str | None,
    *,
    raw_text: str,
    spans: list[dict[str, Any]],
) -> str | None:
    if masked_text is None:
        return None
    safe = masked_text
    for span in spans:
        start = int(span.get("start", -1))
        end = int(span.get("end", -1))
        if start < 0 or end <= start or end > len(raw_text):
            continue
        raw_value = raw_text[start:end]
        if raw_value:
            safe = safe.replace(raw_value, f"[UNSTORED_{span.get('entity_type', 'PII')}]")
    return safe


def _assert_detected_values_absent(
    payload: dict[str, Any],
    *,
    raw_text: str,
    spans: list[dict[str, Any]],
) -> None:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    for span in spans:
        start = int(span.get("start", -1))
        end = int(span.get("end", -1))
        if start < 0 or end <= start or end > len(raw_text):
            continue
        raw_value = raw_text[start:end]
        if raw_value and raw_value in serialized:
            entity_type = span.get("entity_type", "UNKNOWN")
            raise RawPIIStorageError(
                f"persistence payload contains detected raw value for {entity_type}"
            )


def assert_safe_persistence_payload(
    payload: dict[str, Any],
    *,
    raw_text: str,
    spans: list[dict[str, Any]],
) -> None:
    """Public wrapper for console stores that persist raw-free derived payloads."""

    _assert_detected_values_absent(payload, raw_text=raw_text, spans=spans)


def _json_obj(value: str) -> dict[str, int]:
    decoded = json.loads(value)
    if not isinstance(decoded, dict):
        return {}
    return {str(k): int(v) for k, v in decoded.items()}


def _summary_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "request_id": row["request_id"],
        "created_at": row["created_at"],
        "text_length": row["text_length"],
        "blocked": bool(row["blocked"]),
        "latency_ms": row["latency_ms"],
        "detected_span_count": row["detected_span_count"],
        "masked_span_count": row["masked_span_count"],
        "policy_profile": row["policy_profile"],
        "output_target": row["output_target"],
        "entity_counts": _json_obj(row["entity_counts_json"]),
        "risk_counts": _json_obj(row["risk_counts_json"]),
        "action_counts": _json_obj(row["action_counts_json"]),
        "encrypted_raw_available": row["encrypted_raw_text_json"] is not None,
        "encrypted_raw_key_hint": row["encrypted_raw_key_hint"],
        "raw_value_logged": False,
    }


def _detail_from_row(row: sqlite3.Row) -> dict[str, Any]:
    data = _summary_from_row(row)
    data.update(
        {
            "masked_text": row["masked_text"],
            "spans": json.loads(row["spans_json"]),
            "audit_events": json.loads(row["audit_events_json"]),
        }
    )
    return data
