from __future__ import annotations

import io
import json
import sqlite3
import time
import zipfile
from pathlib import Path

from fastapi.testclient import TestClient

from api_service.app import create_app
from api_service.database import AuditStore
from api_service.datasets import DatasetManager
from api_service.service import CONFIG_DIR, ConsoleService
from pii_guardrail.pipeline import GuardrailPipeline, default_components


def _mock_client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(db_path=tmp_path / "audit.sqlite3"))


def _real_client(tmp_path: Path) -> TestClient:
    store = AuditStore(tmp_path / "audit.sqlite3")
    pipeline = GuardrailPipeline(default_components(config_dir=CONFIG_DIR))
    service = ConsoleService(store=store, pipeline=pipeline, ner_mode="real:test")
    manager = DatasetManager(
        db_path=store.path,
        allowed_roots=[tmp_path],
        upload_dir=tmp_path / "uploads",
    )
    return TestClient(create_app(service=service, dataset_manager=manager))


def _upload_csv(client: TestClient, body: str, filename: str = "records.csv") -> str:
    response = client.post(
        "/api/datasets/upload",
        files={"file": (filename, body.encode("utf-8"), "text/csv")},
    )
    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["raw_path_returned"] is False
    return payload["dataset_id"]


def _wait_run(client: TestClient, run_id: str) -> dict:
    for _ in range(100):
        payload = client.get(f"/api/dataset-runs/{run_id}").json()
        if payload["status"] in {"completed", "failed", "cancelled"}:
            return payload
        time.sleep(0.03)
    raise AssertionError("dataset run did not finish")


def test_dataset_run_requires_real_ner(tmp_path: Path) -> None:
    client = _mock_client(tmp_path)
    dataset_id = _upload_csv(client, "name,phone\nuser,010-1234-5678\n")

    response = client.post(
        "/api/dataset-runs",
        json={
            "dataset_id": dataset_id,
            "parser_preset": "generic_csv",
            "text_columns": ["name", "phone"],
            "row_limit": 1,
        },
    )

    assert response.status_code == 409
    payload = response.json()
    assert payload["detail"]["code"] == "NER_NOT_READY"
    assert payload["detail"]["raw_value_logged"] is False


def test_upload_csv_schema_run_and_records_are_raw_free(tmp_path: Path) -> None:
    client = _real_client(tmp_path)
    dataset_id = _upload_csv(
        client,
        "name,phone,note\n"
        "Hong Gil Dong,010-1234-5678,call me\n"
        "Kim,010-9876-5432,shipping\n",
    )

    schema = client.get(f"/api/datasets/{dataset_id}/schema").json()
    assert schema["columns"] == ["name", "phone", "note"]
    assert schema["raw_preview_returned"] is False

    response = client.post(
        "/api/dataset-runs",
        json={
            "dataset_id": dataset_id,
            "parser_preset": "generic_csv",
            "text_columns": ["name", "phone", "note"],
            "id_column": "phone",
            "row_limit": 2,
        },
    )
    assert response.status_code == 200, response.text
    run = _wait_run(client, response.json()["run_id"])

    assert run["status"] == "completed"
    assert run["records_processed"] == 2
    assert run["detected_span_count"] >= 2
    assert run["raw_value_logged"] is False

    records = client.get(f"/api/dataset-runs/{run['run_id']}/records").json()["records"]
    serialized = json.dumps({"run": run, "records": records}, ensure_ascii=False)
    assert "010-1234-5678" not in serialized
    assert "010-9876-5432" not in serialized
    assert "Hong Gil Dong" not in serialized
    assert "call me" not in serialized
    assert all(row["raw_value_logged"] is False for row in records)
    assert all("row_id_hash" in row and "phone" not in row["row_id_hash"] for row in records)

    db_bytes = (tmp_path / "audit.sqlite3").read_bytes()
    assert b"010-1234-5678" not in db_bytes
    assert b"010-9876-5432" not in db_bytes
    assert b"Hong Gil Dong" not in db_bytes
    assert b"call me" not in db_bytes


def test_register_local_cp949_csv_under_allowed_root(tmp_path: Path) -> None:
    client = _real_client(tmp_path)
    csv_path = tmp_path / "public_records.csv"
    csv_path.write_bytes("company,phone\nshop,010-1111-2222\n".encode("cp949"))

    registered = client.post(
        "/api/datasets/register-local",
        json={"path": str(csv_path)},
    )

    assert registered.status_code == 200, registered.text
    payload = registered.json()
    assert payload["source_kind"] == "local"
    assert payload["raw_path_returned"] is False
    schema = client.get(f"/api/datasets/{payload['dataset_id']}/schema").json()
    assert schema["columns"] == ["company", "phone"]
    assert schema["encoding_candidates"] == ["utf-8-sig"]


def test_upload_jsonl_text_and_aihub_zip_runs_without_raw_payloads(tmp_path: Path) -> None:
    client = _real_client(tmp_path)

    jsonl_id = _upload_file(
        client,
        "items.jsonl",
        b'{"memo":"email user@example.com"}\n',
        "application/jsonl",
    )
    txt_id = _upload_file(
        client,
        "items.txt",
        "contact 010-2222-3333\n".encode("utf-8"),
        "text/plain",
    )
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(
            "sample.json",
            json.dumps(
                {
                    "SJML": {
                        "text": [
                            [
                                {
                                    "title": "safe title",
                                    "subtitle": "",
                                    "content": "mail zip@example.com",
                                }
                            ]
                        ]
                    }
                },
                ensure_ascii=False,
            ),
        )
    zip_id = _upload_file(client, "TS1.zip", zip_buffer.getvalue(), "application/zip")

    runs = [
        _create_and_wait(client, jsonl_id, "generic_jsonl", ["memo"]),
        _create_and_wait(client, txt_id, "plain_text_lines", []),
        _create_and_wait(client, zip_id, "aihub_624_sjml_zip", []),
    ]

    serialized = json.dumps(runs, ensure_ascii=False)
    assert "user@example.com" not in serialized
    assert "010-2222-3333" not in serialized
    assert "zip@example.com" not in serialized
    assert all(item["run"]["status"] == "completed" for item in runs)
    assert all(item["run"]["detected_span_count"] >= 1 for item in runs)


def test_raw_retention_policy_is_disabled(tmp_path: Path) -> None:
    client = _real_client(tmp_path)
    dataset_id = _upload_csv(client, "memo\n010-1234-5678\n")

    response = client.post(
        "/api/dataset-runs",
        json={
            "dataset_id": dataset_id,
            "parser_preset": "generic_csv",
            "text_columns": ["memo"],
            "retention_policy": "encrypted_retention",
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"]["code"] == "DATASET_RUN_ERROR"


def _upload_file(client: TestClient, filename: str, data: bytes, content_type: str) -> str:
    response = client.post(
        "/api/datasets/upload",
        files={"file": (filename, data, content_type)},
    )
    assert response.status_code == 200, response.text
    return response.json()["dataset_id"]


def _create_and_wait(
    client: TestClient,
    dataset_id: str,
    parser_preset: str,
    text_columns: list[str],
) -> dict:
    response = client.post(
        "/api/dataset-runs",
        json={
            "dataset_id": dataset_id,
            "parser_preset": parser_preset,
            "text_columns": text_columns,
            "row_limit": 3,
        },
    )
    assert response.status_code == 200, response.text
    run = _wait_run(client, response.json()["run_id"])
    records = client.get(f"/api/dataset-runs/{run['run_id']}/records").json()["records"]
    return {"run": run, "records": records}


def test_dataset_tables_exist_without_raw_rows_after_invalid_request(tmp_path: Path) -> None:
    client = _mock_client(tmp_path)
    response = client.post("/api/datasets/register-local", json={"path": str(tmp_path / "missing.csv")})
    assert response.status_code == 404

    with sqlite3.connect(tmp_path / "audit.sqlite3") as conn:
        count = conn.execute("SELECT COUNT(*) FROM dataset_runs").fetchone()[0]
    assert count == 0
