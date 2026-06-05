from __future__ import annotations

import json
import os
import re
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from api_service.app import create_app
from api_service.database import AuditStore
from api_service.datasets import DatasetManager
from api_service.service import CONFIG_DIR, ConsoleService
from pii_guardrail.pipeline import GuardrailPipeline, default_components


@pytest.mark.real_data
def test_real_data_csv_run_from_local_root_is_raw_free(tmp_path: Path) -> None:
    root_value = os.getenv("KPG_REAL_DATA_TEST_ROOT")
    if not root_value:
        pytest.skip("KPG_REAL_DATA_TEST_ROOT is not set")
    root = Path(root_value).expanduser().resolve()
    if not root.exists():
        pytest.skip("KPG_REAL_DATA_TEST_ROOT does not exist")
    candidate = _find_csv_with_identifier(root)
    if candidate is None:
        pytest.skip("No bounded CSV sample with phone/email-like value found")
    csv_path, raw_value = candidate

    client = _real_client(tmp_path, root)
    registered = client.post("/api/datasets/register-local", json={"path": str(csv_path)})
    assert registered.status_code == 200, registered.text
    dataset_id = registered.json()["dataset_id"]
    schema = client.get(f"/api/datasets/{dataset_id}/schema").json()
    assert schema["raw_preview_returned"] is False

    created = client.post(
        "/api/dataset-runs",
        json={
            "dataset_id": dataset_id,
            "parser_preset": "data_go_public_records_csv",
            "text_columns": [],
            "row_limit": 10,
        },
    )
    assert created.status_code == 200, created.text
    run = _wait_run(client, created.json()["run_id"])
    records = client.get(f"/api/dataset-runs/{run['run_id']}/records").json()["records"]
    serialized = json.dumps({"run": run, "records": records}, ensure_ascii=False)

    assert run["status"] == "completed"
    assert run["records_processed"] > 0
    assert raw_value not in serialized
    assert raw_value.encode("utf-8", errors="ignore") not in (tmp_path / "audit.sqlite3").read_bytes()


def _real_client(tmp_path: Path, allowed_root: Path) -> TestClient:
    store = AuditStore(tmp_path / "audit.sqlite3")
    pipeline = GuardrailPipeline(default_components(config_dir=CONFIG_DIR))
    service = ConsoleService(store=store, pipeline=pipeline, ner_mode="real:test")
    manager = DatasetManager(
        db_path=store.path,
        allowed_roots=[allowed_root],
        upload_dir=tmp_path / "uploads",
    )
    return TestClient(create_app(service=service, dataset_manager=manager))


def _wait_run(client: TestClient, run_id: str) -> dict:
    for _ in range(200):
        payload = client.get(f"/api/dataset-runs/{run_id}").json()
        if payload["status"] in {"completed", "failed", "cancelled"}:
            return payload
        time.sleep(0.05)
    raise AssertionError("real-data dataset run did not finish")


def _find_csv_with_identifier(root: Path) -> tuple[Path, str] | None:
    pattern = re.compile(
        r"(?:010-\d{3,4}-\d{4}|[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,})"
    )
    for path in sorted(root.rglob("*.csv")):
        text = _read_prefix(path, max_bytes=2_000_000)
        match = pattern.search(text)
        if match:
            return path, match.group(0)
    return None


def _read_prefix(path: Path, *, max_bytes: int) -> str:
    data = path.read_bytes()[:max_bytes]
    for encoding in ("utf-8-sig", "cp949", "euc-kr"):
        try:
            return data.decode(encoding)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")
