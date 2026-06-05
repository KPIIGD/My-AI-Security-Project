from __future__ import annotations

import json
import sqlite3
from pathlib import Path

from fastapi.testclient import TestClient

from api_service.app import create_app


def _client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(db_path=tmp_path / "audit.sqlite3"))


def test_health_reports_safe_console_state(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.get("/api/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["version"] == "v0.2-single-turn"
    assert payload["raw_value_logged"] is False
    assert payload["ner_mode"]


def test_apply_persists_safe_log_without_raw_pii(tmp_path: Path) -> None:
    client = _client(tmp_path)
    raw = "고객명 홍길동, 연락처 010-1234-5678."

    response = client.post("/api/pii/apply", json={"text": raw})

    assert response.status_code == 200
    payload = response.json()
    assert payload["masked_text"] is not None
    assert "010-1234-5678" not in payload["masked_text"]
    assert payload["raw_value_logged"] is False
    request_id = payload["request_id"]

    detail = client.get(f"/api/logs/{request_id}").json()
    serialized = json.dumps(detail, ensure_ascii=False)
    assert "홍길동" not in serialized
    assert "010-1234-5678" not in serialized
    assert detail["raw_value_logged"] is False
    assert detail["spans"]

    db_bytes = (tmp_path / "audit.sqlite3").read_bytes()
    assert "홍길동".encode("utf-8") not in db_bytes
    assert b"010-1234-5678" not in db_bytes


def test_apply_can_store_encrypted_raw_and_decrypt_with_operator_key(tmp_path: Path) -> None:
    client = _client(tmp_path)
    raw = "고객명 홍길동, 연락처 010-1234-5678."
    operator_key = "professor-demo-key"

    response = client.post(
        "/api/pii/apply",
        json={
            "text": raw,
            "encrypted_raw_logging_key": operator_key,
            "encrypted_raw_key_hint": "교수님 데모 키",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    request_id = payload["request_id"]
    assert payload["encrypted_raw_available"] is True
    assert payload["summary"]["encrypted_raw_available"] is True
    assert payload["raw_value_logged"] is False

    detail = client.get(f"/api/logs/{request_id}").json()
    serialized_detail = json.dumps(detail, ensure_ascii=False)
    assert detail["encrypted_raw_available"] is True
    assert detail["encrypted_raw_key_hint"] == "교수님 데모 키"
    assert "홍길동" not in serialized_detail
    assert "010-1234-5678" not in serialized_detail
    assert "ciphertext" not in serialized_detail

    wrong_key = client.post(
        f"/api/logs/{request_id}/decrypt",
        json={"decrypt_key": "wrong-demo-key"},
    )
    assert wrong_key.status_code == 403

    decrypted = client.post(
        f"/api/logs/{request_id}/decrypt",
        json={"decrypt_key": operator_key},
    )
    assert decrypted.status_code == 200
    decrypted_payload = decrypted.json()
    assert decrypted_payload["decrypted_text"] == raw
    assert decrypted_payload["raw_value_logged"] is False

    db_bytes = (tmp_path / "audit.sqlite3").read_bytes()
    assert "홍길동".encode("utf-8") not in db_bytes
    assert b"010-1234-5678" not in db_bytes
    assert operator_key.encode("utf-8") not in db_bytes


def test_decrypt_rejects_raw_free_log(tmp_path: Path) -> None:
    client = _client(tmp_path)
    response = client.post("/api/pii/apply", json={"text": "연락처 010-1234-5678 입니다."})
    request_id = response.json()["request_id"]

    decrypted = client.post(
        f"/api/logs/{request_id}/decrypt",
        json={"decrypt_key": "professor-demo-key"},
    )

    assert decrypted.status_code == 400
    assert decrypted.json()["detail"] == "암호화 원문 로그가 없습니다."


def test_trace_endpoint_returns_safe_stage_payload(tmp_path: Path) -> None:
    client = _client(tmp_path)
    raw = "홍길동이 010-1234-5678로 연락했습니다."

    response = client.post("/api/pii/trace", json={"text": raw, "reveal_raw": True})

    assert response.status_code == 200
    payload = response.json()
    serialized = json.dumps(payload, ensure_ascii=False)
    assert payload["reveal_raw"] is False
    assert "홍길동" not in serialized
    assert "010-1234-5678" not in serialized
    assert payload["stages"]


def test_batch_logs_each_record_and_returns_aggregate(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.post(
        "/api/pii/batch",
        json={
            "lines": "\n".join(
                [
                    "연락처 010-1234-5678 입니다.",
                    "메일은 test@example.com 입니다.",
                    "오늘 날씨가 좋습니다.",
                ]
            )
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["n"] == 3
    assert payload["aggregate"]["total_requests"] == 3
    assert payload["aggregate"]["detected_span_count"] >= 2
    assert all("text" not in row for row in payload["records"])

    logs = client.get("/api/logs").json()["records"]
    assert len(logs) == 3


def test_metrics_accumulate_from_sqlite_logs(tmp_path: Path) -> None:
    client = _client(tmp_path)
    client.post("/api/pii/apply", json={"text": "연락처 010-1234-5678 입니다."})
    client.post("/api/pii/apply", json={"text": "메일 test@example.com 입니다."})

    response = client.get("/api/metrics")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_requests"] == 2
    assert payload["detected_span_count"] >= 2
    assert payload["raw_value_logged"] is False


def test_invalid_requests_are_rejected_without_db_row(tmp_path: Path) -> None:
    client = _client(tmp_path)

    response = client.post("/api/pii/apply", json={"text": "   "})

    assert response.status_code == 400
    with sqlite3.connect(tmp_path / "audit.sqlite3") as conn:
        count = conn.execute("SELECT COUNT(*) FROM guardrail_requests").fetchone()[0]
    assert count == 0
