"""FastAPI entrypoint for the local Korean PII Guardrail product console."""

from __future__ import annotations

import os
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, Query, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware

from .crypto import DecryptionError
from .database import AuditStore, RawPIIStorageError
from .datasets import (
    DatasetError,
    DatasetManager,
    DatasetRunPayload,
    RegisterLocalDatasetPayload,
)
from .models import ApplyRequestPayload, BatchRequestPayload, DecryptLogPayload, TraceRequestPayload
from .service import ConsoleService, PROJECT_ROOT

MAX_TEXT_LENGTH = 20_000
DEFAULT_DB_PATH = PROJECT_ROOT / "data" / "console" / "audit.sqlite3"


def create_app(
    *,
    db_path: str | Path | None = None,
    service: ConsoleService | None = None,
    dataset_manager: DatasetManager | None = None,
) -> FastAPI:
    resolved_db_path = Path(
        db_path or os.getenv("KPG_CONSOLE_DB", str(DEFAULT_DB_PATH))
    )
    api = FastAPI(
        title="Korean PII Guardrail Console API",
        version="v0.2-single-turn",
    )
    api.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://127.0.0.1:5173",
            "http://localhost:5173",
            "http://127.0.0.1:3000",
            "http://localhost:3000",
        ],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    console_service = service or ConsoleService(store=AuditStore(resolved_db_path))
    api.state.console_service = console_service
    api.state.dataset_manager = dataset_manager or DatasetManager(
        db_path=console_service.store.path
    )

    @api.get("/api/health")
    def health() -> dict:
        payload = _service(api).health()
        payload["real_data"] = _datasets(api).config()
        return payload

    @api.post("/api/pii/apply")
    def apply_guardrail(payload: ApplyRequestPayload) -> dict:
        _validate_text(payload.text)
        try:
            return _service(api).apply(payload)
        except RawPIIStorageError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            ) from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @api.post("/api/pii/trace")
    def trace_guardrail(payload: TraceRequestPayload) -> dict:
        _validate_text(payload.text)
        try:
            return _service(api).trace(payload)
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @api.post("/api/pii/batch")
    def batch_guardrail(payload: BatchRequestPayload) -> dict:
        texts = payload.iter_texts()
        if not texts:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch request requires at least one non-empty text",
            )
        for text in texts:
            _validate_text(text)
        try:
            return _service(api).batch(payload)
        except RawPIIStorageError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=str(exc),
            ) from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @api.get("/api/logs")
    def logs(
        limit: int = Query(default=100, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
    ) -> dict:
        store = _service(api).store
        return {
            "records": store.list_logs(limit=limit, offset=offset),
            "raw_value_logged": False,
        }

    @api.get("/api/logs/{request_id}")
    def log_detail(request_id: str) -> dict:
        record = _service(api).store.get_log(request_id)
        if record is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found")
        return record

    @api.post("/api/logs/{request_id}/decrypt")
    def decrypt_log(request_id: str, payload: DecryptLogPayload) -> dict:
        try:
            return _service(api).decrypt_log(request_id, decrypt_key=payload.decrypt_key)
        except KeyError as exc:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Log not found") from exc
        except DecryptionError as exc:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc

    @api.get("/api/metrics")
    def metrics() -> dict:
        return _service(api).store.metrics()

    @api.post("/api/datasets/upload")
    async def upload_dataset(file: UploadFile = File(...)) -> dict:
        try:
            return await _datasets(api).register_upload(file)
        except DatasetError as exc:
            raise _dataset_http_error(exc) from exc

    @api.post("/api/datasets/register-local")
    def register_local_dataset(payload: RegisterLocalDatasetPayload) -> dict:
        try:
            return _datasets(api).register_local(payload)
        except DatasetError as exc:
            raise _dataset_http_error(exc) from exc

    @api.get("/api/datasets/{dataset_id}/schema")
    def dataset_schema(dataset_id: str) -> dict:
        try:
            return _datasets(api).schema(dataset_id)
        except DatasetError as exc:
            raise _dataset_http_error(exc) from exc

    @api.post("/api/dataset-runs")
    def create_dataset_run(payload: DatasetRunPayload) -> dict:
        try:
            return _datasets(api).start_run(payload, service=_service(api))
        except DatasetError as exc:
            raise _dataset_http_error(exc) from exc

    @api.get("/api/dataset-runs")
    def dataset_runs(
        limit: int = Query(default=50, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
    ) -> dict:
        return {
            "records": _datasets(api).list_runs(limit=limit, offset=offset),
            "raw_value_logged": False,
        }

    @api.get("/api/dataset-runs/{run_id}")
    def dataset_run_detail(run_id: str) -> dict:
        try:
            return _datasets(api).get_run(run_id)
        except DatasetError as exc:
            raise _dataset_http_error(exc) from exc

    @api.get("/api/dataset-runs/{run_id}/records")
    def dataset_run_records(
        run_id: str,
        limit: int = Query(default=100, ge=1, le=500),
        offset: int = Query(default=0, ge=0),
    ) -> dict:
        try:
            return {
                "records": _datasets(api).list_records(
                    run_id,
                    limit=limit,
                    offset=offset,
                ),
                "raw_value_logged": False,
            }
        except DatasetError as exc:
            raise _dataset_http_error(exc) from exc

    @api.post("/api/dataset-runs/{run_id}/cancel")
    def cancel_dataset_run(run_id: str) -> dict:
        try:
            return _datasets(api).cancel(run_id)
        except DatasetError as exc:
            raise _dataset_http_error(exc) from exc

    return api


def _service(api: FastAPI) -> ConsoleService:
    return api.state.console_service


def _datasets(api: FastAPI) -> DatasetManager:
    return api.state.dataset_manager


def _dataset_http_error(exc: DatasetError) -> HTTPException:
    status_code = status.HTTP_400_BAD_REQUEST
    if exc.code == "DATASET_NOT_FOUND":
        status_code = status.HTTP_404_NOT_FOUND
    elif exc.code == "NER_NOT_READY":
        status_code = status.HTTP_409_CONFLICT
    elif exc.code == "DATASET_ACCESS_DENIED":
        status_code = status.HTTP_403_FORBIDDEN
    return HTTPException(
        status_code=status_code,
        detail={
            "code": exc.code,
            "message": str(exc),
            "raw_value_logged": False,
        },
    )


def _validate_text(text: str) -> None:
    if not text.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="text must not be empty",
        )
    if len(text) > MAX_TEXT_LENGTH:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"text exceeds {MAX_TEXT_LENGTH} characters",
        )


app = create_app()
