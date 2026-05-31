from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import jsonschema

from pii_guardrail.context_anchor_manifest import build_context_anchor_manifest
from pii_guardrail.context_synthetic_insertion import (
    build_context_synthetic_insertion_safety_report,
    build_synthetic_true_pii_anchor_rows,
    merge_synthetic_anchor_rows,
)
from pii_guardrail.context_template_inventory import build_context_template_inventory


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _anchor_schema() -> dict:
    return json.loads(
        (PROJECT_ROOT / "schemas" / "context_anchor_window.schema.json").read_text(
            encoding="utf-8"
        )
    )


def test_synthetic_insertion_generates_true_pii_rows_for_person_and_address() -> None:
    rows = build_synthetic_true_pii_anchor_rows(
        template_rows=build_context_template_inventory(),
        existing_anchor_rows=[],
        include_domain_balance_rows=False,
    )
    schema = _anchor_schema()

    assert rows
    for row in rows:
        jsonschema.validate(row, schema)
        assert row["label"] == "true_pii"
        assert row["evidence_lane"] == "safe_synthetic_insertion"
        assert row["label_source"] == "safe_synthetic_generator"
        assert row["label_status"] == "review_needed"
        assert row["source_domain"] != "sample_forms"
        assert row["raw_value_logged"] is False
        assert row["candidate_value_stored"] is False

    assert any(row["anchor_entity"] == "PERSON_NAME" for row in rows)
    assert any(row["anchor_entity"] in {"ADDRESS_FULL", "ADDRESS_UNIT"} for row in rows)


def test_synthetic_insertion_closes_targeted_gaps_and_keeps_data_quality_measured() -> None:
    existing_rows = _diverse_existing_rows()
    synthetic_rows = build_synthetic_true_pii_anchor_rows(
        template_rows=build_context_template_inventory(),
        existing_anchor_rows=existing_rows,
        include_domain_balance_rows=True,
    )
    final_rows = merge_synthetic_anchor_rows(
        existing_rows=existing_rows,
        synthetic_rows=synthetic_rows,
    )
    manifest = build_context_anchor_manifest(
        anchor_input_path=PROJECT_ROOT
        / "data"
        / "context_corpus"
        / "context_anchor_windows_v1.jsonl",
        rows=final_rows,
    )
    anchor_safety = {"status": "pass"}
    safety = build_context_synthetic_insertion_safety_report(
        synthetic_rows=synthetic_rows,
        final_anchor_rows=final_rows,
        anchor_safety_report=anchor_safety,
        manifest=manifest,
    )

    assert safety["phase_exit_gate"]["status"] == "pass"
    assert safety["targeted_true_pii_counts"]["PERSON_NAME"] > 0
    assert safety["targeted_true_pii_counts"]["ADDRESS"] > 0
    assert safety["final_by_label"]["true_pii"] > 0
    assert safety["raw_pii_leak_count"] == 0
    assert safety["synthetic_value_materialized"] is False
    assert safety["score_tuning_allowed_by_this_phase"] is False


def test_synthetic_insertion_cli_writes_raw_free_artifacts(tmp_path: Path) -> None:
    anchor_input = tmp_path / "context_anchor_windows_v1.jsonl"
    template_input = tmp_path / "context_template_inventory_v1.jsonl"
    synthetic_output = tmp_path / "context_synthetic_true_pii_anchor_windows_v1.jsonl"
    anchor_output = tmp_path / "augmented_context_anchor_windows_v1.jsonl"
    term_output = tmp_path / "korean_context_terms_v1.jsonl"
    manifest_output = tmp_path / "context_anchor_windows_manifest_v1.yaml"
    anchor_safety_output = tmp_path / "context_anchor_corpus_safety_v1.json"
    term_safety_output = tmp_path / "korean_context_terms_safety_v1.json"
    synthetic_safety_output = tmp_path / "context_synthetic_insertion_safety_v1.json"
    synthetic_report_output = tmp_path / "context_synthetic_insertion_v1.md"

    anchor_input.write_text("", encoding="utf-8")
    template_input.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in build_context_template_inventory()
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "build_context_synthetic_true_pii_anchors.py"),
            "--anchor-input",
            str(anchor_input),
            "--template-input",
            str(template_input),
            "--synthetic-output",
            str(synthetic_output),
            "--anchor-output",
            str(anchor_output),
            "--term-output",
            str(term_output),
            "--manifest-output",
            str(manifest_output),
            "--anchor-safety-output",
            str(anchor_safety_output),
            "--term-safety-output",
            str(term_safety_output),
            "--synthetic-safety-output",
            str(synthetic_safety_output),
            "--synthetic-report-output",
            str(synthetic_report_output),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    synthetic_rows = [
        json.loads(line)
        for line in synthetic_output.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    safety = json.loads(synthetic_safety_output.read_text(encoding="utf-8"))
    combined = (
        synthetic_output.read_text(encoding="utf-8")
        + anchor_output.read_text(encoding="utf-8")
        + term_output.read_text(encoding="utf-8")
        + synthetic_safety_output.read_text(encoding="utf-8")
        + synthetic_report_output.read_text(encoding="utf-8")
        + result.stdout
    )
    assert synthetic_rows
    assert safety["phase_exit_gate"]["status"] == "pass"
    assert "context_synthetic_insertion_status=pass" in result.stdout
    assert "홍길동" not in combined
    assert "서울특별시" not in combined
    assert "010-" not in combined
    assert "http://" not in combined
    assert "https://" not in combined
    assert "@" not in combined


def _diverse_existing_rows() -> list[dict]:
    rows: list[dict] = []
    for entity, shape in (
        ("PHONE_MOBILE", "mobile_phone_shape"),
        ("EMAIL", "email_shape"),
        ("BANK_ACCOUNT", "bank_account_shape"),
        ("RRN", "rrn_shape"),
    ):
        for domain in ("customer_support", "ecommerce", "healthcare", "finance", "education"):
            rows.append(_anchor_row(entity=entity, shape=shape, domain=domain))
    return rows


def _anchor_row(*, entity: str, shape: str, domain: str) -> dict:
    return {
        "schema_version": "context_anchor_windows_v1",
        "anchor_entity": entity,
        "anchor_shape": shape,
        "anchor_source": "synthetic_template",
        "label": "non_pii",
        "source_domain": domain,
        "material_class": "realistic_input_like",
        "material_type": "realistic_input_like",
        "evidence_lane": "public_web_context",
        "label_source": "codex_draft",
        "label_status": "review_needed",
        "mvp_target": {"true_pii": 1000, "non_pii": 1000},
        "current_count": {"true_pii": 0, "non_pii": 1, "unknown": 0},
        "gap_reason": ["reviewer_approved_labels_absent"],
        "gap_verdict": ["needs_reviewer_labels"],
        "distance_bucket": "within_2_tokens",
        "left_ngrams": _ngram_windows(f"{domain}-left"),
        "right_ngrams": _ngram_windows(f"{domain}-right"),
        "contains_raw_pii": False,
        "raw_value_logged": False,
        "raw_url_logged": False,
        "page_body_stored": False,
        "candidate_value_stored": False,
        "evidence_role": "anchor_context_only_not_score_tuning",
    }


def _ngram_windows(token: str) -> dict:
    return {
        "within_1_token": {"unigrams": [token], "bigrams": [], "trigrams": []},
        "within_2_tokens": {
            "unigrams": [token, "context"],
            "bigrams": [f"{token} context"],
            "trigrams": [],
        },
        "within_5_tokens": {
            "unigrams": [token, "context", "field"],
            "bigrams": [f"{token} context", "context field"],
            "trigrams": [f"{token} context field"],
        },
    }
