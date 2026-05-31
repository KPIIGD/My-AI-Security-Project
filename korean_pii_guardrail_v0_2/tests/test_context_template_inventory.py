from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import jsonschema

from pii_guardrail.context_template_inventory import (
    build_context_template_inventory,
    build_context_template_inventory_safety_report,
    context_template_inventory_jsonl,
    render_context_template_inventory_markdown,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _schema() -> dict:
    return json.loads(
        (PROJECT_ROOT / "schemas" / "context_template_inventory.schema.json").read_text(
            encoding="utf-8"
        )
    )


def test_context_template_inventory_schema_and_entity_mapping() -> None:
    rows = build_context_template_inventory()
    schema = _schema()

    assert rows
    for row in rows:
        jsonschema.validate(row, schema)
        assert row["slot_mappings"][0]["anchor_entity"] == row["anchor_entity"]
        assert row["slot_mappings"][0]["anchor_shape"] == row["anchor_shape"]

    by_group = {group: 0 for group in ("PERSON_NAME", "ADDRESS")}
    domains_by_group = {group: set() for group in by_group}
    for row in rows:
        by_group[row["entity_group"]] += 1
        domains_by_group[row["entity_group"]].add(row["source_domain"])

    assert by_group["PERSON_NAME"] > 0
    assert by_group["ADDRESS"] > 0
    assert len(domains_by_group["PERSON_NAME"]) >= 5
    assert len(domains_by_group["ADDRESS"]) >= 5
    assert {row["evidence_lane"] for row in rows} == {"template_extraction"}
    assert {row["label_status"] for row in rows} == {"review_needed"}


def test_context_template_inventory_is_raw_free_and_score_neutral() -> None:
    rows = build_context_template_inventory()
    safety = build_context_template_inventory_safety_report(rows)
    rendered = (
        context_template_inventory_jsonl(rows)
        + json.dumps(safety, ensure_ascii=False, sort_keys=True)
        + render_context_template_inventory_markdown(rows, safety)
    )

    assert safety["status"] == "pass"
    assert safety["phase_exit_gate"]["status"] == "pass"
    assert safety["raw_pii_leak_count"] == 0
    assert safety["raw_url_logged_count"] == 0
    assert safety["raw_value_logged_count"] == 0
    assert safety["raw_sentence_logged_count"] == 0
    assert safety["slot_value_materialized"] is False
    assert safety["score_tuning_allowed_by_this_phase"] is False
    assert safety["runtime_scoring_behavior_changed"] is False
    assert safety["score_delta_changed"] is False
    assert safety["context_rule_changed"] is False
    forbidden_terms = (
        "홍길동",
        "김철수",
        "서울특별시",
        "부산광역시",
        "010-",
        "http://",
        "https://",
        "@",
    )
    assert not any(term in rendered for term in forbidden_terms)
    forbidden_keys = (
        '"raw_name"',
        '"raw_address"',
        '"raw_sentence"',
        '"raw_url"',
        '"template_text"',
        '"template_sentence"',
        '"value"',
    )
    assert not any(key in rendered for key in forbidden_keys)


def test_context_template_inventory_cli_writes_artifacts(tmp_path: Path) -> None:
    output = tmp_path / "context_template_inventory_v1.jsonl"
    safety_output = tmp_path / "context_template_inventory_safety_v1.json"
    report_output = tmp_path / "context_template_inventory_v1.md"

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "build_context_template_inventory.py"),
            "--output",
            str(output),
            "--safety-output",
            str(safety_output),
            "--report-output",
            str(report_output),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    rows = [
        json.loads(line)
        for line in output.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    safety = json.loads(safety_output.read_text(encoding="utf-8"))
    combined = (
        output.read_text(encoding="utf-8")
        + safety_output.read_text(encoding="utf-8")
        + report_output.read_text(encoding="utf-8")
        + result.stdout
    )
    assert rows
    assert safety["status"] == "pass"
    assert "context_template_inventory_status=pass" in result.stdout
    assert "홍길동" not in combined
    assert "서울특별시" not in combined
