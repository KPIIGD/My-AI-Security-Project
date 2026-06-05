"""Real-data dataset run support for the product console.

Raw dataset text is read only while processing a run. SQLite records contain
only aggregate counts, public span metadata, hashes, and raw-free summaries.
"""

from __future__ import annotations

import csv
import hashlib
import hmac
import io
import json
import os
import secrets
import sqlite3
import tempfile
import threading
import zipfile
from collections import Counter
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable
from uuid import uuid4

from fastapi import UploadFile
from pydantic import BaseModel, Field

from pii_guardrail.schema import GuardrailOptions, GuardrailRequest

from .database import RawPIIStorageError, assert_safe_persistence_payload


DEFAULT_REAL_DATA_ROOT = Path("C:/Users/andyw/Desktop/M4_raw_staging")
PARSER_PRESETS = (
    "generic_csv",
    "generic_jsonl",
    "plain_text_lines",
    "aihub_624_sjml_zip",
    "data_go_public_records_csv",
)
CSV_ENCODINGS = ("utf-8-sig", "cp949", "euc-kr")
MAX_UPLOAD_BYTES = 100 * 1024 * 1024
DEFAULT_ROW_LIMIT = 1_000
MAX_ROW_LIMIT = 50_000
ROW_HASH_KEY = os.getenv("KPG_ROW_HASH_KEY", "").encode("utf-8") or secrets.token_bytes(32)


class DatasetError(ValueError):
    """Raised for safe client-visible dataset errors."""

    code = "DATASET_ERROR"


class DatasetNotFoundError(DatasetError):
    code = "DATASET_NOT_FOUND"


class DatasetAccessError(DatasetError):
    code = "DATASET_ACCESS_DENIED"


class DatasetRunError(DatasetError):
    code = "DATASET_RUN_ERROR"


class NERNotReadyError(DatasetError):
    code = "NER_NOT_READY"


class RegisterLocalDatasetPayload(BaseModel):
    path: str = Field(..., min_length=1)


class DatasetRunPayload(BaseModel):
    dataset_id: str = Field(..., min_length=1)
    parser_preset: str = "generic_csv"
    text_columns: list[str] = Field(default_factory=list)
    id_column: str | None = None
    row_limit: int = Field(default=DEFAULT_ROW_LIMIT, ge=1, le=MAX_ROW_LIMIT)
    retention_policy: str = "discard_after_run"


@dataclass(frozen=True)
class DatasetRef:
    dataset_id: str
    path: Path
    source_kind: str
    display_name: str
    is_upload: bool = False


@dataclass(frozen=True)
class FieldSegment:
    name: str
    value: str
    start: int
    end: int


@dataclass(frozen=True)
class ParsedRecord:
    row_index: int
    raw_text: str
    fields: tuple[FieldSegment, ...]
    row_id_value: str | None = None


class DatasetRunStore:
    """SQLite store for raw-free dataset run metadata."""

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
                CREATE TABLE IF NOT EXISTS dataset_runs (
                    run_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    completed_at TEXT,
                    status TEXT NOT NULL,
                    dataset_id TEXT NOT NULL,
                    dataset_label TEXT NOT NULL,
                    source_kind TEXT NOT NULL,
                    parser_preset TEXT NOT NULL,
                    row_limit INTEGER NOT NULL,
                    retention_policy TEXT NOT NULL,
                    text_columns_json TEXT NOT NULL,
                    id_column TEXT,
                    ner_mode TEXT NOT NULL,
                    records_processed INTEGER NOT NULL DEFAULT 0,
                    records_failed INTEGER NOT NULL DEFAULT 0,
                    blocked_count INTEGER NOT NULL DEFAULT 0,
                    detected_span_count INTEGER NOT NULL DEFAULT 0,
                    masked_span_count INTEGER NOT NULL DEFAULT 0,
                    average_latency_ms REAL NOT NULL DEFAULT 0,
                    entity_counts_json TEXT NOT NULL DEFAULT '{}',
                    risk_counts_json TEXT NOT NULL DEFAULT '{}',
                    action_counts_json TEXT NOT NULL DEFAULT '{}',
                    error_code TEXT,
                    error_message TEXT,
                    raw_value_logged INTEGER NOT NULL DEFAULT 0
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS dataset_run_records (
                    run_id TEXT NOT NULL,
                    row_index INTEGER NOT NULL,
                    row_id_hash TEXT NOT NULL,
                    masked_text TEXT NOT NULL,
                    blocked INTEGER NOT NULL,
                    latency_ms REAL NOT NULL,
                    detected_span_count INTEGER NOT NULL,
                    masked_span_count INTEGER NOT NULL,
                    entity_counts_json TEXT NOT NULL,
                    risk_counts_json TEXT NOT NULL,
                    action_counts_json TEXT NOT NULL,
                    spans_json TEXT NOT NULL,
                    error_code TEXT,
                    raw_value_logged INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY (run_id, row_index)
                )
                """
            )
            conn.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_dataset_runs_created_at
                ON dataset_runs(created_at DESC)
                """
            )

    def create_run(
        self,
        *,
        run_id: str,
        dataset: DatasetRef,
        payload: DatasetRunPayload,
        ner_mode: str,
    ) -> dict[str, Any]:
        now = datetime.now(UTC).isoformat()
        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO dataset_runs (
                    run_id, created_at, status, dataset_id, dataset_label,
                    source_kind, parser_preset, row_limit, retention_policy,
                    text_columns_json, id_column, ner_mode
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    now,
                    "queued",
                    dataset.dataset_id,
                    _safe_dataset_label(dataset),
                    dataset.source_kind,
                    payload.parser_preset,
                    payload.row_limit,
                    payload.retention_policy,
                    json.dumps(payload.text_columns, ensure_ascii=False),
                    payload.id_column,
                    ner_mode,
                ),
            )
        return self.get_run(run_id) or {}

    def mark_running(self, run_id: str) -> None:
        with self._connect() as conn:
            conn.execute("UPDATE dataset_runs SET status = ? WHERE run_id = ?", ("running", run_id))

    def insert_record(self, run_id: str, row: dict[str, Any], *, raw_text: str) -> None:
        payload = {
            "masked_text": row["masked_text"],
            "entity_counts": row["entity_counts"],
            "risk_counts": row["risk_counts"],
            "action_counts": row["action_counts"],
            "spans": row["spans"],
        }
        assert_safe_persistence_payload(payload, raw_text=raw_text, spans=row["spans"])
        with self._connect() as conn:
            conn.execute(
                """
                INSERT OR REPLACE INTO dataset_run_records (
                    run_id, row_index, row_id_hash, masked_text, blocked,
                    latency_ms, detected_span_count, masked_span_count,
                    entity_counts_json, risk_counts_json, action_counts_json,
                    spans_json, error_code, raw_value_logged
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    run_id,
                    row["row_index"],
                    row["row_id_hash"],
                    row["masked_text"],
                    int(row["blocked"]),
                    row["latency_ms"],
                    row["detected_span_count"],
                    row["masked_span_count"],
                    json.dumps(row["entity_counts"], ensure_ascii=False, sort_keys=True),
                    json.dumps(row["risk_counts"], ensure_ascii=False, sort_keys=True),
                    json.dumps(row["action_counts"], ensure_ascii=False, sort_keys=True),
                    json.dumps(row["spans"], ensure_ascii=False, sort_keys=True),
                    row.get("error_code"),
                    0,
                ),
            )

    def update_progress(self, run_id: str, aggregate: dict[str, Any]) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE dataset_runs
                SET records_processed = ?, records_failed = ?, blocked_count = ?,
                    detected_span_count = ?, masked_span_count = ?,
                    average_latency_ms = ?, entity_counts_json = ?,
                    risk_counts_json = ?, action_counts_json = ?
                WHERE run_id = ?
                """,
                (
                    aggregate["records_processed"],
                    aggregate["records_failed"],
                    aggregate["blocked_count"],
                    aggregate["detected_span_count"],
                    aggregate["masked_span_count"],
                    aggregate["average_latency_ms"],
                    json.dumps(aggregate["entity_counts"], ensure_ascii=False, sort_keys=True),
                    json.dumps(aggregate["risk_counts"], ensure_ascii=False, sort_keys=True),
                    json.dumps(aggregate["action_counts"], ensure_ascii=False, sort_keys=True),
                    run_id,
                ),
            )

    def complete_run(self, run_id: str, *, status: str = "completed") -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE dataset_runs SET status = ?, completed_at = ? WHERE run_id = ?",
                (status, datetime.now(UTC).isoformat(), run_id),
            )

    def fail_run(self, run_id: str, *, code: str, message: str) -> None:
        with self._connect() as conn:
            conn.execute(
                """
                UPDATE dataset_runs
                SET status = ?, completed_at = ?, error_code = ?, error_message = ?
                WHERE run_id = ?
                """,
                ("failed", datetime.now(UTC).isoformat(), code, message, run_id),
            )

    def list_runs(self, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM dataset_runs
                ORDER BY created_at DESC
                LIMIT ? OFFSET ?
                """,
                (max(1, min(limit, 200)), max(0, offset)),
            ).fetchall()
        return [_run_from_row(row) for row in rows]

    def get_run(self, run_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM dataset_runs WHERE run_id = ?", (run_id,)).fetchone()
        return _run_from_row(row) if row else None

    def list_records(self, run_id: str, *, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT * FROM dataset_run_records
                WHERE run_id = ?
                ORDER BY row_index ASC
                LIMIT ? OFFSET ?
                """,
                (run_id, max(1, min(limit, 500)), max(0, offset)),
            ).fetchall()
        return [_record_from_row(row) for row in rows]


class DatasetManager:
    """In-memory dataset registry plus background run orchestration."""

    def __init__(
        self,
        *,
        db_path: str | Path,
        allowed_roots: list[Path] | None = None,
        upload_dir: str | Path | None = None,
    ) -> None:
        self.store = DatasetRunStore(db_path)
        self.allowed_roots = allowed_roots or _allowed_roots_from_env()
        self.upload_dir = Path(upload_dir or Path(tempfile.gettempdir()) / "kpg_console_uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)
        self._datasets: dict[str, DatasetRef] = {}
        self._cancelled: set[str] = set()
        self._lock = threading.Lock()

    def config(self) -> dict[str, Any]:
        return {
            "allowed_roots": [str(root) for root in self.allowed_roots],
            "upload_max_bytes": MAX_UPLOAD_BYTES,
            "raw_retention_enabled": False,
            "real_ner_required": True,
            "parser_presets": list(PARSER_PRESETS),
            "default_row_limit": DEFAULT_ROW_LIMIT,
            "max_row_limit": MAX_ROW_LIMIT,
        }

    async def register_upload(self, file: UploadFile) -> dict[str, Any]:
        suffix = Path(file.filename or "dataset").suffix.lower()
        dataset_id = f"ds_{uuid4().hex}"
        target = self.upload_dir / f"{dataset_id}{suffix or '.data'}"
        written = 0
        try:
            with target.open("wb") as handle:
                while True:
                    chunk = await file.read(1024 * 1024)
                    if not chunk:
                        break
                    written += len(chunk)
                    if written > MAX_UPLOAD_BYTES:
                        raise DatasetRunError("upload exceeds 100MB limit")
                    handle.write(chunk)
        except Exception:
            target.unlink(missing_ok=True)
            raise
        ref = DatasetRef(
            dataset_id=dataset_id,
            path=target,
            source_kind="upload",
            display_name=_clean_display_name(file.filename or target.name),
            is_upload=True,
        )
        self._put_dataset(ref)
        return _dataset_ref_payload(ref, size_bytes=written)

    def register_local(self, payload: RegisterLocalDatasetPayload) -> dict[str, Any]:
        path = Path(payload.path).expanduser().resolve()
        if not path.exists():
            raise DatasetNotFoundError("dataset path does not exist")
        if not any(_is_relative_to(path, root) for root in self.allowed_roots):
            raise DatasetAccessError("dataset path is outside allowed roots")
        ref = DatasetRef(
            dataset_id=f"ds_{uuid4().hex}",
            path=path,
            source_kind="local",
            display_name=_clean_display_name(path.name or "local dataset"),
            is_upload=False,
        )
        self._put_dataset(ref)
        return _dataset_ref_payload(ref, size_bytes=_safe_size(path))

    def schema(self, dataset_id: str) -> dict[str, Any]:
        dataset = self._get_dataset(dataset_id)
        return inspect_dataset_schema(dataset)

    def start_run(self, payload: DatasetRunPayload, *, service: Any) -> dict[str, Any]:
        dataset = self._get_dataset(payload.dataset_id)
        try:
            if not getattr(service, "ner_enabled", False):
                raise NERNotReadyError("real NER is required for dataset runs")
            if payload.parser_preset not in PARSER_PRESETS:
                raise DatasetRunError("unsupported parser preset")
            if payload.retention_policy != "discard_after_run":
                raise DatasetRunError("raw retention is disabled without access control")
        except DatasetError:
            self._discard_upload(dataset)
            raise
        run_id = f"run_{uuid4().hex}"
        run = self.store.create_run(
            run_id=run_id,
            dataset=dataset,
            payload=payload,
            ner_mode=str(service.ner_mode),
        )
        thread = threading.Thread(
            target=self._run_dataset,
            args=(run_id, dataset, payload, service),
            daemon=True,
        )
        thread.start()
        return run

    def cancel(self, run_id: str) -> dict[str, Any]:
        with self._lock:
            self._cancelled.add(run_id)
        run = self.store.get_run(run_id)
        if run is None:
            raise DatasetNotFoundError("dataset run not found")
        return run

    def list_runs(self, *, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        return self.store.list_runs(limit=limit, offset=offset)

    def get_run(self, run_id: str) -> dict[str, Any]:
        run = self.store.get_run(run_id)
        if run is None:
            raise DatasetNotFoundError("dataset run not found")
        return run

    def list_records(self, run_id: str, *, limit: int = 100, offset: int = 0) -> list[dict[str, Any]]:
        if self.store.get_run(run_id) is None:
            raise DatasetNotFoundError("dataset run not found")
        return self.store.list_records(run_id, limit=limit, offset=offset)

    def _put_dataset(self, ref: DatasetRef) -> None:
        with self._lock:
            self._datasets[ref.dataset_id] = ref

    def _get_dataset(self, dataset_id: str) -> DatasetRef:
        with self._lock:
            dataset = self._datasets.get(dataset_id)
        if dataset is None:
            raise DatasetNotFoundError("dataset is not registered in this server session")
        return dataset

    def _is_cancelled(self, run_id: str) -> bool:
        with self._lock:
            return run_id in self._cancelled

    def _run_dataset(
        self,
        run_id: str,
        dataset: DatasetRef,
        payload: DatasetRunPayload,
        service: Any,
    ) -> None:
        aggregate = _empty_aggregate()
        self.store.mark_running(run_id)
        try:
            for parsed in iter_dataset_records(
                dataset.path,
                parser_preset=payload.parser_preset,
                text_columns=tuple(payload.text_columns),
                id_column=payload.id_column,
            ):
                if self._is_cancelled(run_id):
                    self.store.complete_run(run_id, status="cancelled")
                    return
                if aggregate["records_processed"] >= payload.row_limit:
                    break
                if not parsed.raw_text.strip():
                    continue
                request = GuardrailRequest(
                    text=parsed.raw_text,
                    purpose_id="console_real_data_run",
                    domain="real_data_test",
                    options=GuardrailOptions(return_spans=True, include_audit_events=False),
                )
                response_payload = service.pipeline.process(request).to_dict()
                row = build_dataset_record(response_payload, parsed)
                self.store.insert_record(run_id, row, raw_text=parsed.raw_text)
                _merge_row_into_aggregate(aggregate, row)
                self.store.update_progress(run_id, aggregate)
            self.store.complete_run(run_id, status="completed")
        except RawPIIStorageError as exc:
            self.store.fail_run(run_id, code="RAW_PII_STORAGE_BLOCKED", message=str(exc))
        except Exception as exc:
            self.store.fail_run(
                run_id,
                code=type(exc).__name__,
                message="dataset run failed without logging source text",
            )
        finally:
            if dataset.is_upload:
                self._discard_upload(dataset)

    def _discard_upload(self, dataset: DatasetRef) -> None:
        if not dataset.is_upload:
            return
        dataset.path.unlink(missing_ok=True)
        with self._lock:
            self._datasets.pop(dataset.dataset_id, None)


def inspect_dataset_schema(dataset: DatasetRef) -> dict[str, Any]:
    path = dataset.path
    file_type = _file_type(path)
    columns: list[str] = []
    encodings: list[str] = []
    row_count_estimate = 0
    parser_presets = _suggest_presets(dataset, file_type)
    if path.is_dir():
        files = _iter_supported_files(path)
        row_count_estimate = len(files)
    elif file_type == "csv":
        text, encoding = _read_text_file(path)
        columns = _csv_columns(text)
        encodings = [encoding]
        row_count_estimate = _count_text_rows(text)
    elif file_type == "jsonl":
        text, encoding = _read_text_file(path)
        columns = _jsonl_columns(text)
        encodings = [encoding]
        row_count_estimate = _count_text_rows(text)
    elif file_type == "txt":
        text, encoding = _read_text_file(path)
        encodings = [encoding]
        row_count_estimate = _count_text_rows(text)
    elif file_type == "zip":
        with zipfile.ZipFile(path) as archive:
            names = [info.filename for info in archive.infolist() if not info.is_dir()]
        row_count_estimate = len(names)
        columns = _zip_candidate_columns(dataset)
    return {
        "dataset_id": dataset.dataset_id,
        "source_kind": dataset.source_kind,
        "display_name": dataset.display_name,
        "file_type": file_type,
        "columns": columns,
        "row_count_estimate": row_count_estimate,
        "encoding_candidates": encodings or list(CSV_ENCODINGS),
        "parser_presets": parser_presets,
        "raw_preview_returned": False,
        "raw_value_logged": False,
    }


def iter_dataset_records(
    path: Path,
    *,
    parser_preset: str,
    text_columns: tuple[str, ...],
    id_column: str | None,
) -> Iterable[ParsedRecord]:
    files = _files_for_preset(path, parser_preset)
    row_index = 0
    for file_path in files:
        if parser_preset in {"generic_csv", "data_go_public_records_csv"}:
            iterator = _iter_csv_records(file_path, text_columns=text_columns, id_column=id_column)
        elif parser_preset == "generic_jsonl":
            iterator = _iter_jsonl_records(file_path, text_columns=text_columns, id_column=id_column)
        elif parser_preset == "plain_text_lines":
            iterator = _iter_text_line_records(file_path)
        elif parser_preset == "aihub_624_sjml_zip":
            iterator = _iter_aihub_zip_records(file_path)
        else:
            raise DatasetRunError("unsupported parser preset")
        for parsed in iterator:
            yield ParsedRecord(
                row_index=row_index,
                raw_text=parsed.raw_text,
                fields=parsed.fields,
                row_id_value=parsed.row_id_value,
            )
            row_index += 1


def build_dataset_record(response: dict[str, Any], parsed: ParsedRecord) -> dict[str, Any]:
    spans = list(response.get("spans") or [])
    metrics = response.get("metrics") or {}
    entity_counts = Counter(span.get("entity_type", "UNKNOWN") for span in spans)
    risk_counts = Counter(span.get("risk_level", "UNKNOWN") for span in spans)
    action_counts = Counter(span.get("action", "unknown") for span in spans)
    row = {
        "row_index": parsed.row_index,
        "row_id_hash": _row_id_hash(parsed),
        "masked_text": _safe_field_summary(parsed.fields, spans),
        "blocked": bool(response.get("blocked")),
        "latency_ms": float(metrics.get("latency_ms", 0.0)),
        "detected_span_count": int(metrics.get("detected_span_count", len(spans))),
        "masked_span_count": int(metrics.get("masked_span_count", 0)),
        "entity_counts": dict(entity_counts),
        "risk_counts": dict(risk_counts),
        "action_counts": dict(action_counts),
        "spans": spans,
        "raw_value_logged": False,
    }
    assert_safe_persistence_payload(
        {
            "masked_text": row["masked_text"],
            "entity_counts": row["entity_counts"],
            "risk_counts": row["risk_counts"],
            "action_counts": row["action_counts"],
            "spans": row["spans"],
        },
        raw_text=parsed.raw_text,
        spans=spans,
    )
    return row


def _iter_csv_records(path: Path, *, text_columns: tuple[str, ...], id_column: str | None) -> Iterable[ParsedRecord]:
    for text in _read_text_sources(path, extensions=(".csv", ".tsv")):
        dialect = _sniff_dialect(text)
        reader = csv.DictReader(io.StringIO(text), dialect=dialect)
        if not reader.fieldnames:
            continue
        selected = tuple(col for col in text_columns if col in reader.fieldnames) or tuple(reader.fieldnames)
        for row in reader:
            yield _compose_record(row, selected, id_column=id_column)


def _iter_jsonl_records(path: Path, *, text_columns: tuple[str, ...], id_column: str | None) -> Iterable[ParsedRecord]:
    for text in _read_text_sources(path, extensions=(".jsonl",)):
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                yield _compose_record({"text": line}, ("text",), id_column=None)
                continue
            if isinstance(payload, dict):
                string_fields = {str(key): str(value) for key, value in payload.items() if value is not None}
                selected = tuple(col for col in text_columns if col in string_fields) or tuple(string_fields.keys())
                yield _compose_record(string_fields, selected, id_column=id_column)


def _iter_text_line_records(path: Path) -> Iterable[ParsedRecord]:
    for text in _read_text_sources(path, extensions=(".txt", ".log", ".json", ".jsonl", ".csv")):
        for line in text.splitlines():
            if line.strip():
                yield _compose_record({"text": line.strip()}, ("text",), id_column=None)


def _iter_aihub_zip_records(path: Path) -> Iterable[ParsedRecord]:
    zip_paths = [path] if path.is_file() else [file for file in _iter_supported_files(path) if file.suffix.lower() == ".zip"]
    for zip_path in zip_paths:
        with zipfile.ZipFile(zip_path) as archive:
            for info in archive.infolist():
                if info.is_dir() or not info.filename.lower().endswith(".json"):
                    continue
                try:
                    with archive.open(info) as handle:
                        payload = json.load(handle)
                except Exception:
                    continue
                for fields in _extract_aihub_fields(payload):
                    yield _compose_record(fields, tuple(fields.keys()), id_column=None)


def _extract_aihub_fields(payload: Any) -> Iterable[dict[str, str]]:
    sjml = payload.get("SJML") if isinstance(payload, dict) else None
    text_rows = sjml.get("text") if isinstance(sjml, dict) else None
    if not isinstance(text_rows, list):
        return
    for row_group in text_rows:
        rows = row_group if isinstance(row_group, list) else [row_group]
        for row in rows:
            if not isinstance(row, dict):
                continue
            fields = {
                key: value.strip()
                for key in ("title", "subtitle", "content")
                if isinstance((value := row.get(key)), str) and value.strip()
            }
            if fields:
                yield fields


def _compose_record(
    row: dict[str, Any],
    columns: tuple[str, ...],
    *,
    id_column: str | None,
) -> ParsedRecord:
    parts: list[str] = []
    fields: list[FieldSegment] = []
    cursor = 0
    for column in columns:
        value = str(row.get(column, "") or "").strip()
        if not value:
            continue
        safe_column = _safe_field_name(column)
        prefix = f"{safe_column}: "
        parts.append(prefix)
        cursor += len(prefix)
        start = cursor
        parts.append(value)
        cursor += len(value)
        end = cursor
        fields.append(FieldSegment(name=safe_column, value=value, start=start, end=end))
        parts.append("\n")
        cursor += 1
    raw_text = "".join(parts).strip()
    if not raw_text:
        raw_text = "empty: [NO_TEXT]"
        fields = (FieldSegment(name="empty", value="[NO_TEXT]", start=7, end=16),)
    return ParsedRecord(
        row_index=0,
        raw_text=raw_text,
        fields=tuple(fields),
        row_id_value=str(row.get(id_column, "")) if id_column and row.get(id_column) is not None else None,
    )


def _safe_field_summary(fields: tuple[FieldSegment, ...], spans: list[dict[str, Any]]) -> str:
    lines: list[str] = []
    for field in fields:
        field_spans = [
            span
            for span in spans
            if _span_overlap(field.start, field.end, int(span.get("start", -1)), int(span.get("end", -1)))
        ]
        if not field_spans:
            lines.append(f"{field.name}: [NO_DETECTED_PII len={len(field.value)}]")
            continue
        tokens = [
            f"[{span.get('entity_type', 'PII')}:{span.get('action', 'unknown')}]"
            for span in field_spans
        ]
        lines.append(f"{field.name}: {' '.join(tokens)}")
    return "\n".join(lines) if lines else "[NO_FIELDS]"


def _read_text_sources(path: Path, *, extensions: tuple[str, ...]) -> Iterable[str]:
    if path.is_dir():
        for file_path in _iter_supported_files(path):
            if file_path.suffix.lower() in extensions:
                yield _read_text_file(file_path)[0]
            elif file_path.suffix.lower() == ".zip":
                yield from _read_zip_text_entries(file_path, extensions=extensions)
        return
    if path.suffix.lower() == ".zip":
        yield from _read_zip_text_entries(path, extensions=extensions)
        return
    if path.suffix.lower() in extensions:
        yield _read_text_file(path)[0]


def _read_zip_text_entries(path: Path, *, extensions: tuple[str, ...]) -> Iterable[str]:
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            if info.is_dir() or Path(info.filename).suffix.lower() not in extensions:
                continue
            with archive.open(info) as handle:
                data = handle.read()
            yield _decode_bytes(data)[0]


def _read_text_file(path: Path) -> tuple[str, str]:
    return _decode_bytes(path.read_bytes())


def _decode_bytes(data: bytes) -> tuple[str, str]:
    for encoding in CSV_ENCODINGS:
        try:
            return data.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace"), "utf-8-replace"


def _csv_columns(text: str) -> list[str]:
    reader = csv.reader(io.StringIO(text), dialect=_sniff_dialect(text))
    try:
        return [_safe_field_name(value) for value in next(reader)]
    except StopIteration:
        return []


def _jsonl_columns(text: str) -> list[str]:
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            return [_safe_field_name(str(key)) for key in payload.keys()]
    return []


def _zip_candidate_columns(dataset: DatasetRef) -> list[str]:
    if _looks_like_aihub_624_zip(dataset):
        return ["title", "subtitle", "content"]
    return []


def _sniff_dialect(text: str) -> csv.Dialect:
    sample = text[:8192]
    try:
        return csv.Sniffer().sniff(sample, delimiters=",\t|;")
    except csv.Error:
        return csv.excel_tab if "\t" in sample else csv.excel


def _files_for_preset(path: Path, parser_preset: str) -> list[Path]:
    if path.is_file():
        return [path]
    if parser_preset in {"generic_csv", "data_go_public_records_csv"}:
        suffixes = {".csv", ".tsv", ".zip"}
    elif parser_preset == "generic_jsonl":
        suffixes = {".jsonl", ".zip"}
    elif parser_preset == "plain_text_lines":
        suffixes = {".txt", ".log", ".json", ".jsonl", ".csv"}
    else:
        suffixes = {".zip"}
    return [file for file in _iter_supported_files(path) if file.suffix.lower() in suffixes]


def _iter_supported_files(path: Path) -> list[Path]:
    suffixes = {".csv", ".tsv", ".jsonl", ".json", ".txt", ".log", ".zip"}
    return [file for file in sorted(path.rglob("*")) if file.is_file() and file.suffix.lower() in suffixes]


def _file_type(path: Path) -> str:
    if path.is_dir():
        return "directory"
    suffix = path.suffix.lower()
    if suffix in {".csv", ".tsv"}:
        return "csv"
    if suffix == ".jsonl":
        return "jsonl"
    if suffix == ".txt":
        return "txt"
    if suffix == ".zip":
        return "zip"
    return suffix.lstrip(".") or "unknown"


def _suggest_presets(dataset: DatasetRef, file_type: str) -> list[str]:
    if file_type == "zip" and _looks_like_aihub_624_zip(dataset):
        return ["aihub_624_sjml_zip"]
    if file_type == "csv":
        return ["data_go_public_records_csv", "generic_csv"]
    if file_type == "jsonl":
        return ["generic_jsonl"]
    if file_type == "txt":
        return ["plain_text_lines"]
    if file_type == "directory":
        return list(PARSER_PRESETS)
    return list(PARSER_PRESETS)


def _looks_like_aihub_624_zip(dataset: DatasetRef) -> bool:
    names = {dataset.path.name.lower(), dataset.display_name.lower()}
    return bool(names & {"ts1.zip", "vs1.zip"})


def _count_text_rows(text: str) -> int:
    return sum(1 for line in text.splitlines() if line.strip())


def _allowed_roots_from_env() -> list[Path]:
    configured = os.getenv("KPG_REAL_DATA_ROOTS")
    if configured:
        roots = [Path(part).expanduser().resolve() for part in configured.split(os.pathsep) if part.strip()]
    else:
        roots = [DEFAULT_REAL_DATA_ROOT.resolve()]
    return roots


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _dataset_ref_payload(ref: DatasetRef, *, size_bytes: int) -> dict[str, Any]:
    return {
        "dataset_id": ref.dataset_id,
        "source_kind": ref.source_kind,
        "display_name": ref.display_name,
        "size_bytes": size_bytes,
        "raw_path_returned": False,
        "raw_value_logged": False,
    }


def _safe_dataset_label(dataset: DatasetRef) -> str:
    return f"{dataset.source_kind}:{_file_type(dataset.path)}"


def _clean_display_name(value: str) -> str:
    safe = value.replace("\r", " ").replace("\n", " ").strip()
    return safe[:120] or "dataset"


def _safe_field_name(value: str) -> str:
    safe = str(value).replace("\r", " ").replace("\n", " ").strip()
    return safe[:80] or "field"


def _safe_size(path: Path) -> int:
    if path.is_file():
        return path.stat().st_size
    return 0


def _row_id_hash(parsed: ParsedRecord) -> str:
    source = parsed.row_id_value or f"{parsed.row_index}:{parsed.raw_text}"
    return hmac.new(
        ROW_HASH_KEY,
        source.encode("utf-8", errors="ignore"),
        hashlib.sha256,
    ).hexdigest()[:24]


def _span_overlap(a_start: int, a_end: int, b_start: int, b_end: int) -> bool:
    return a_start < b_end and b_start < a_end


def _empty_aggregate() -> dict[str, Any]:
    return {
        "records_processed": 0,
        "records_failed": 0,
        "blocked_count": 0,
        "detected_span_count": 0,
        "masked_span_count": 0,
        "latency_sum_ms": 0.0,
        "average_latency_ms": 0.0,
        "entity_counts": {},
        "risk_counts": {},
        "action_counts": {},
    }


def _merge_row_into_aggregate(aggregate: dict[str, Any], row: dict[str, Any]) -> None:
    aggregate["records_processed"] += 1
    aggregate["blocked_count"] += int(row["blocked"])
    aggregate["detected_span_count"] += int(row["detected_span_count"])
    aggregate["masked_span_count"] += int(row["masked_span_count"])
    aggregate["latency_sum_ms"] += float(row["latency_ms"])
    aggregate["average_latency_ms"] = aggregate["latency_sum_ms"] / aggregate["records_processed"]
    _merge_counts(aggregate["entity_counts"], row["entity_counts"])
    _merge_counts(aggregate["risk_counts"], row["risk_counts"])
    _merge_counts(aggregate["action_counts"], row["action_counts"])


def _merge_counts(target: dict[str, int], source: dict[str, int]) -> None:
    for key, value in source.items():
        target[str(key)] = target.get(str(key), 0) + int(value)


def _run_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "run_id": row["run_id"],
        "created_at": row["created_at"],
        "completed_at": row["completed_at"],
        "status": row["status"],
        "dataset_id": row["dataset_id"],
        "dataset_label": row["dataset_label"],
        "source_kind": row["source_kind"],
        "parser_preset": row["parser_preset"],
        "row_limit": row["row_limit"],
        "retention_policy": row["retention_policy"],
        "text_columns": json.loads(row["text_columns_json"]),
        "id_column": row["id_column"],
        "ner_mode": row["ner_mode"],
        "records_processed": row["records_processed"],
        "records_failed": row["records_failed"],
        "blocked_count": row["blocked_count"],
        "detected_span_count": row["detected_span_count"],
        "masked_span_count": row["masked_span_count"],
        "average_latency_ms": row["average_latency_ms"],
        "entity_counts": _json_obj(row["entity_counts_json"]),
        "risk_counts": _json_obj(row["risk_counts_json"]),
        "action_counts": _json_obj(row["action_counts_json"]),
        "error_code": row["error_code"],
        "error_message": row["error_message"],
        "raw_value_logged": False,
    }


def _record_from_row(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "run_id": row["run_id"],
        "row_index": row["row_index"],
        "row_id_hash": row["row_id_hash"],
        "masked_text": row["masked_text"],
        "blocked": bool(row["blocked"]),
        "latency_ms": row["latency_ms"],
        "detected_span_count": row["detected_span_count"],
        "masked_span_count": row["masked_span_count"],
        "entity_counts": _json_obj(row["entity_counts_json"]),
        "risk_counts": _json_obj(row["risk_counts_json"]),
        "action_counts": _json_obj(row["action_counts_json"]),
        "spans": json.loads(row["spans_json"]),
        "error_code": row["error_code"],
        "raw_value_logged": False,
    }


def _json_obj(value: str) -> dict[str, int]:
    decoded = json.loads(value)
    if not isinstance(decoded, dict):
        return {}
    return {str(key): int(val) for key, val in decoded.items()}
