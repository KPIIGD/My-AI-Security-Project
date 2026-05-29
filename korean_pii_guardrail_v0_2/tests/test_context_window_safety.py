from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import jsonschema

from pii_guardrail.context_window_safety import (
    build_context_corpus_safety_report,
    build_context_term_distribution,
    build_context_window_row,
    context_windows_jsonl,
    extract_context_windows_from_html,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_context_window_schema_accepts_safe_row_and_forbids_raw_fields() -> None:
    schema = json.loads(
        (PROJECT_ROOT / "schemas" / "context_window.schema.json").read_text(
            encoding="utf-8"
        )
    )
    row = build_context_window_row(
        source_type="ecommerce_help",
        url="https://example.test/help",
        sentence_text="배송지 정보에는 수령인, 연락처, 주소를 입력합니다.",
        project_root=PROJECT_ROOT,
    )

    assert row is not None
    jsonschema.validate(row.to_dict(), schema)

    unsafe = row.to_dict() | {"raw_text": "배송지 정보에는 수령인 연락처 주소를 입력합니다."}
    try:
        jsonschema.validate(unsafe, schema)
    except jsonschema.ValidationError:
        return
    raise AssertionError("context_window schema must reject raw_text")


def test_context_window_row_redacts_raw_pii_before_safe_output() -> None:
    raw_phone = "010-1234-5678"
    row = build_context_window_row(
        source_type="education_application",
        url="https://example.test/apply",
        sentence_text=f"신청자 연락처 {raw_phone} 및 주소를 입력합니다.",
        project_root=PROJECT_ROOT,
    )

    assert row is not None
    payload = row.to_dict()
    serialized = json.dumps(payload, ensure_ascii=False)
    assert payload["contains_raw_pii"] is False
    assert payload["raw_value_logged"] is False
    assert payload["redaction_applied"] is True
    assert raw_phone not in serialized
    assert "field:phone_label" in payload["anchor_terms"]
    assert "field:address_label" in payload["anchor_terms"]


def test_context_corpus_reports_are_coverage_only_and_raw_url_free() -> None:
    source_url = "https://example.test/help?raw-url-must-not-appear=1"
    raw_phone = "010-0000-0000"
    rows = extract_context_windows_from_html(
        html_text=f"""
        <html><body>
        <p>배송지 정보에는 수령인, 연락처, 주소를 입력합니다.</p>
        <p>예시 전화번호 {raw_phone}는 저장하지 않습니다.</p>
        </body></html>
        """,
        source_type="ecommerce_help",
        url=source_url,
        project_root=PROJECT_ROOT,
    )

    windows_text = context_windows_jsonl(rows)
    distribution = build_context_term_distribution(rows)
    safety = build_context_corpus_safety_report(
        rows=rows,
        report_payloads=[windows_text, distribution],
        source_urls=[source_url],
    )
    combined = windows_text + json.dumps(distribution, ensure_ascii=False) + json.dumps(
        safety,
        ensure_ascii=False,
    )

    assert rows
    assert distribution["evidence_role"] == "coverage_only_not_score_tuning"
    assert distribution["public_corpus_used_for_score_tuning"] is False
    assert safety["status"] == "pass"
    assert safety["raw_pii_leak_count"] == 0
    assert safety["raw_url_logged_count"] == 0
    assert source_url not in combined
    assert raw_phone not in combined


def test_collect_context_windows_cli_writes_safe_artifacts(tmp_path: Path) -> None:
    html_path = tmp_path / "safe_context.html"
    raw_phone = "010-1234-5678"
    html_path.write_text(
        f"""
        <html><body>
        <p>배송지 정보에는 수령인, 연락처, 주소를 입력합니다.</p>
        <p>환자번호와 진료기록은 병원 안내 화면에서 확인합니다.</p>
        <p>예시 전화번호 {raw_phone}는 저장하지 않습니다.</p>
        </body></html>
        """,
        encoding="utf-8",
    )
    output = tmp_path / "context_windows.jsonl"
    distribution = tmp_path / "term_distribution.json"
    safety = tmp_path / "corpus_safety.json"
    source_url = html_path.as_uri()

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "collect_context_windows.py"),
            "--url",
            f"ecommerce_help={source_url}",
            "--output",
            str(output),
            "--term-distribution-output",
            str(distribution),
            "--safety-output",
            str(safety),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    combined = (
        output.read_text(encoding="utf-8")
        + distribution.read_text(encoding="utf-8")
        + safety.read_text(encoding="utf-8")
        + result.stdout
    )
    safety_payload = json.loads(safety.read_text(encoding="utf-8"))
    assert safety_payload["status"] == "pass"
    assert safety_payload["raw_pii_leak_count"] == 0
    assert safety_payload["raw_url_logged_count"] == 0
    assert source_url not in combined
    assert raw_phone not in combined


def test_context_window_safety_ignores_opaque_hash_false_positive() -> None:
    row = build_context_window_row(
        source_type="ecommerce_help",
        url="https://example.test/source",
        sentence_text="배송지 연락처와 주소를 입력합니다.",
        project_root=PROJECT_ROOT,
    )
    assert row is not None
    hash_payload = ("010" + "1234" + "5678") * 5 + "010" + "123" + "456"
    payload = {
        "url_hash": f"sha256:{hash_payload}",
        "anchor_terms": ["field:phone_label"],
    }

    safety = build_context_corpus_safety_report(
        rows=[row],
        report_payloads=[payload],
        source_urls=["https://example.test/source"],
    )

    assert safety["status"] == "pass"
    assert safety["raw_pii_leak_count"] == 0


def test_context_window_safety_still_flags_raw_url_with_hash_token() -> None:
    row = build_context_window_row(
        source_type="ecommerce_help",
        url="https://example.test/source",
        sentence_text="배송지 연락처와 주소를 입력합니다.",
        project_root=PROJECT_ROOT,
    )
    assert row is not None
    hash_payload = ("010" + "1234" + "5678") * 5 + "010" + "123" + "456"
    source_url = f"https://example.test/path/sha256:{hash_payload}"

    safety = build_context_corpus_safety_report(
        rows=[row],
        report_payloads=[{"leaked_url": source_url}],
        source_urls=[source_url],
    )

    assert safety["status"] == "fail"
    assert safety["raw_pii_leak_count"] == 0
    assert safety["raw_url_logged_count"] == 1


def test_context_window_safety_scans_iterator_payload_once() -> None:
    row = build_context_window_row(
        source_type="ecommerce_help",
        url="https://example.test/source",
        sentence_text="배송지 연락처와 주소를 입력합니다.",
        project_root=PROJECT_ROOT,
    )
    assert row is not None
    raw_like_value = "010-" + "1234-" + "5678"
    report_payloads = iter(({"leaked_value": raw_like_value},))

    safety = build_context_corpus_safety_report(
        rows=[row],
        report_payloads=report_payloads,
        source_urls=["https://example.test/source"],
    )

    assert safety["status"] == "fail"
    assert safety["raw_pii_leak_count"] >= 1
