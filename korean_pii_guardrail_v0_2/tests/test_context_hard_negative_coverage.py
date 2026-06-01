from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import jsonschema

from pii_guardrail.context_hard_negative_coverage import (
    HARD_NEGATIVE_THRESHOLDS,
    build_context_hard_negative_coverage_report,
    build_hard_negative_anchor_rows,
    merge_hard_negative_anchor_rows,
)
from pii_guardrail.context_anchor_collector import build_context_anchor_safety_report
from pii_guardrail.context_anchor_manifest import build_context_anchor_manifest


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _anchor_schema() -> dict:
    return json.loads(
        (PROJECT_ROOT / "schemas" / "context_anchor_window.schema.json").read_text(
            encoding="utf-8"
        )
    )


def test_phase5_generates_raw_free_person_and_address_hard_negatives() -> None:
    generated = build_hard_negative_anchor_rows([])
    schema = _anchor_schema()

    assert generated
    assert any(row["anchor_entity"] == "PERSON_NAME" for row in generated)
    assert any(row["anchor_entity"] in {"ADDRESS_FULL", "ADDRESS_UNIT"} for row in generated)
    for row in generated:
        jsonschema.validate(row, schema)
        assert row["label"] == "non_pii"
        assert row["evidence_lane"] == "hard_negative_corpus"
        assert row["label_status"] == "review_needed"
        assert row["raw_value_logged"] is False
        assert row["candidate_value_stored"] is False


def test_phase5_hard_negative_gate_passes_with_generated_gap_rows() -> None:
    generated = build_hard_negative_anchor_rows([])
    merged = merge_hard_negative_anchor_rows(
        existing_rows=_existing_public_non_pii_rows(),
        hard_negative_rows=generated,
    )
    safety = build_context_anchor_safety_report(
        rows=merged,
        term_rows=[],
        source_ids=[],
        extra_payloads=[],
    )
    manifest = build_context_anchor_manifest(
        anchor_input_path=PROJECT_ROOT
        / "data"
        / "context_corpus"
        / "context_anchor_windows_v1.jsonl",
        rows=merged,
    )

    report = build_context_hard_negative_coverage_report(
        final_anchor_rows=merged,
        generated_hard_negative_rows=generated,
        safety_report=safety,
        manifest=manifest,
    )

    assert report["hard_negative_gate"]["status"] == "pass"
    assert report["score_tuning_allowed_by_this_phase"] is False
    assert report["raw_pii_safety"]["status"] == "pass"
    for entity_group, threshold in HARD_NEGATIVE_THRESHOLDS.items():
        row = report["coverage_by_entity_group"][entity_group]
        assert row["non_pii_anchor_count"] > 0
        assert row["hard_negative_ratio"] >= threshold


def test_phase5_cli_writes_expected_raw_free_reports(tmp_path: Path) -> None:
    anchor_input = tmp_path / "context_anchor_windows_v1.jsonl"
    hard_negative_output = tmp_path / "context_hard_negative_anchor_windows_v1.jsonl"
    anchor_output = tmp_path / "context_anchor_windows_v1.jsonl"
    term_output = tmp_path / "korean_context_terms_v1.jsonl"
    manifest_output = tmp_path / "context_anchor_windows_manifest_v1.yaml"
    safety_output = tmp_path / "context_anchor_corpus_safety_v1.json"
    report_json_output = tmp_path / "context_hard_negative_coverage_v1.json"
    report_md_output = tmp_path / "context_hard_negative_coverage_v1.md"
    anchor_input.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in _existing_public_non_pii_rows()
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "build_context_hard_negative_coverage.py"),
            "--anchor-input",
            str(anchor_input),
            "--hard-negative-output",
            str(hard_negative_output),
            "--anchor-output",
            str(anchor_output),
            "--term-output",
            str(term_output),
            "--manifest-output",
            str(manifest_output),
            "--anchor-safety-output",
            str(safety_output),
            "--report-json-output",
            str(report_json_output),
            "--report-md-output",
            str(report_md_output),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    report = json.loads(report_json_output.read_text(encoding="utf-8"))
    combined = (
        hard_negative_output.read_text(encoding="utf-8")
        + anchor_output.read_text(encoding="utf-8")
        + term_output.read_text(encoding="utf-8")
        + report_json_output.read_text(encoding="utf-8")
        + report_md_output.read_text(encoding="utf-8")
        + result.stdout
    )
    assert report["hard_negative_gate"]["status"] == "pass"
    assert "context_hard_negative_coverage_status=pass" in result.stdout
    assert "010-" not in combined
    assert "http://" not in combined
    assert "https://" not in combined
    assert "@" not in combined


def _existing_public_non_pii_rows() -> list[dict]:
    rows: list[dict] = []
    for entity_group, entity, shape in (
        ("PHONE", "PHONE_MOBILE", "mobile_phone_shape"),
        ("EMAIL", "EMAIL", "email_shape"),
        ("BANK_ACCOUNT", "BANK_ACCOUNT", "bank_account_shape"),
        ("REGISTRATION_IDENTIFIER", "BUSINESS_REG_NO", "business_registration_shape"),
    ):
        for domain in (
            "customer_support",
            "ecommerce",
            "healthcare",
            "finance",
            "education",
            "public_services",
        ):
            rows.append(
                _anchor_row(
                    entity_group=entity_group,
                    entity=entity,
                    shape=shape,
                    domain=domain,
                    unique=f"{entity_group.lower()}-{domain}",
                )
            )
    return rows


def _anchor_row(
    *,
    entity_group: str,
    entity: str,
    shape: str,
    domain: str,
    unique: str,
) -> dict:
    del entity_group
    return {
        "schema_version": "context_anchor_windows_v1",
        "anchor_entity": entity,
        "anchor_shape": shape,
        "anchor_source": "regex",
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
        "left_ngrams": _ngram_windows(f"{unique}-left"),
        "right_ngrams": _ngram_windows(f"{unique}-right"),
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
            "unigrams": [token, "lookalike"],
            "bigrams": [f"{token} lookalike"],
            "trigrams": [],
        },
        "within_5_tokens": {
            "unigrams": [token, "lookalike", "field"],
            "bigrams": [f"{token} lookalike", "lookalike field"],
            "trigrams": [f"{token} lookalike field"],
        },
    }
