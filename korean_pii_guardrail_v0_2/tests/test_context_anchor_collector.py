from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import jsonschema

from pii_guardrail.context_anchor_collector import (
    aggregate_korean_context_terms,
    build_context_anchor_safety_report,
    context_anchor_windows_jsonl,
    extract_context_anchor_windows_from_text,
    korean_context_terms_jsonl,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _schema() -> dict:
    return json.loads(
        (PROJECT_ROOT / "schemas" / "context_anchor_window.schema.json").read_text(
            encoding="utf-8"
        )
    )


def test_anchor_collector_extracts_shape_and_context_without_candidate_value() -> None:
    raw_phone = "010" + "-" + "1234" + "-" + "5678"
    rows = extract_context_anchor_windows_from_text(
        text=f"support request applicant contact phone {raw_phone} confirm delivery",
        source_type="customer_support_help",
        source_id="fixture://support-one",
    )

    assert len(rows) == 1
    payload = rows[0].to_dict()
    jsonschema.validate(payload, _schema())
    serialized = json.dumps(payload, ensure_ascii=False)
    assert payload["anchor_entity"] == "PHONE_MOBILE"
    assert payload["anchor_shape"] == "mobile_phone_shape"
    assert payload["label"] == "unknown"
    assert payload["evidence_lane"] == "public_web_context"
    assert payload["label_source"] == "unlabeled"
    assert payload["label_status"] == "unknown"
    assert payload["material_type"] == payload["material_class"]
    assert payload["mvp_target"] == {"true_pii": 1500, "non_pii": 1500}
    assert payload["current_count"] == {"true_pii": 0, "non_pii": 0, "unknown": 1}
    assert "needs_reviewer_labels" in payload["gap_verdict"]
    assert payload["left_ngrams"]["within_2_tokens"]["bigrams"] == ["contact phone"]
    assert payload["right_ngrams"]["within_2_tokens"]["bigrams"] == [
        "confirm delivery"
    ]
    assert raw_phone not in serialized
    assert "anchor_value" not in payload
    assert payload["raw_value_logged"] is False
    assert payload["candidate_value_stored"] is False


def test_anchor_collector_supports_raw_free_marker_labels_for_name_like_values() -> None:
    rows = extract_context_anchor_windows_from_text(
        text=(
            "product model "
            "[[ANCHOR:PERSON_NAME:korean_name_like_3_syllable:non_pii:dictionary_or_ner]] "
            "release note"
        ),
        source_type="developer_docs",
        source_id="fixture://developer-doc",
    )

    assert len(rows) == 1
    payload = rows[0].to_dict()
    jsonschema.validate(payload, _schema())
    assert payload["anchor_entity"] == "PERSON_NAME"
    assert payload["anchor_shape"] == "korean_name_like_3_syllable"
    assert payload["anchor_source"] == "dictionary_or_ner"
    assert payload["label"] == "non_pii"
    assert payload["label_source"] == "codex_draft"
    assert payload["label_status"] == "review_needed"
    assert payload["source_domain"] == "developer_docs"
    assert payload["material_class"] == "general_web_or_explanatory"


def test_context_term_aggregation_keeps_discovered_ngrams_raw_free() -> None:
    raw_email = "person" + "@" + "example" + "." + "test"
    rows = extract_context_anchor_windows_from_text(
        text=f"account recovery contact email {raw_email} verify request",
        source_type="customer_support_help",
        source_id="fixture://support-two",
    )

    terms = aggregate_korean_context_terms(rows)
    rendered = korean_context_terms_jsonl(terms)
    assert any(
        row["ngram"] == "contact email"
        and row["entity_hint"] == "EMAIL"
        and row["ngram_size"] == 2
        and row["relative_position"] == "left_within_2_tokens"
        for row in terms
    )
    assert any(row["ngram"] == "verify request" and row["frequency"] == 1 for row in terms)
    assert all(row["term_class"] is None for row in terms)
    assert all(
        row["term_class_status"] == "unclassified_discovered_term" for row in terms
    )
    assert raw_email not in rendered


def test_anchor_collector_outputs_schema_valid_unique_bounded_ngrams() -> None:
    long_context = "x" * 70
    rows = extract_context_anchor_windows_from_text(
        text=(
            f"repeat repeat repeat {long_context} "
            "[[ANCHOR:PERSON_NAME:korean_name_3_syllable:true_pii:ner]] "
            f"repeat repeat {long_context}"
        ),
        source_type="synthetic_safe_template",
        source_id="fixture://duplicate-context",
    )

    assert len(rows) == 1
    payload = rows[0].to_dict()
    jsonschema.validate(payload, _schema())
    for side in ("left_ngrams", "right_ngrams"):
        for bucket in payload[side].values():
            for values in bucket.values():
                assert len(values) == len(set(values))
                assert all(len(value) <= 64 for value in values)
                assert long_context not in values


def test_context_anchor_safety_report_flags_raw_free_collector_outputs() -> None:
    raw_phone = "010" + "-" + "1111" + "-" + "2222"
    source_id = "fixture://support-three"
    rows = extract_context_anchor_windows_from_text(
        text=f"customer contact phone {raw_phone} check status",
        source_type="customer_support_help",
        source_id=source_id,
    )
    terms = aggregate_korean_context_terms(rows)
    report = build_context_anchor_safety_report(
        rows=rows,
        term_rows=terms,
        source_ids=[source_id],
        extra_payloads=[context_anchor_windows_jsonl(rows), korean_context_terms_jsonl(terms)],
    )

    assert report["status"] == "pass"
    assert report["raw_pii_leak_count"] == 0
    assert report["raw_url_logged_count"] == 0
    assert report["raw_value_logged_count"] == 0
    assert report["runtime_scoring_behavior_changed"] is False
    assert report["score_delta_changed"] is False
    assert report["context_rule_changed"] is False


def test_context_anchor_cli_writes_anchor_and_term_artifacts(tmp_path: Path) -> None:
    raw_phone = "010" + "-" + "3333" + "-" + "4444"
    html_path = tmp_path / "source.html"
    html_path.write_text(
        f"""
        <html><body>
        <p>support request applicant contact phone {raw_phone} confirm delivery.</p>
        <p>product model [[ANCHOR:PERSON_NAME:korean_name_like_3_syllable:non_pii:dictionary_or_ner]] release note.</p>
        </body></html>
        """,
        encoding="utf-8",
    )
    anchor_output = tmp_path / "context_anchor_windows_v1.jsonl"
    anchor_safety = tmp_path / "context_anchor_corpus_safety_v1.json"
    term_output = tmp_path / "korean_context_terms_v1.jsonl"
    term_safety = tmp_path / "korean_context_terms_safety_v1.json"
    source_id = html_path.as_uri()

    build_result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "build_context_anchor_windows.py"),
            "--source",
            f"customer_support_help={source_id}",
            "--output",
            str(anchor_output),
            "--safety-output",
            str(anchor_safety),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )
    collect_result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "collect_korean_context_terms.py"),
            "--anchor-input",
            str(anchor_output),
            "--output",
            str(term_output),
            "--safety-output",
            str(term_safety),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    combined = (
        anchor_output.read_text(encoding="utf-8")
        + anchor_safety.read_text(encoding="utf-8")
        + term_output.read_text(encoding="utf-8")
        + term_safety.read_text(encoding="utf-8")
        + build_result.stdout
        + collect_result.stdout
    )
    anchor_payloads = [
        json.loads(line)
        for line in anchor_output.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    term_payloads = [
        json.loads(line)
        for line in term_output.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert {row["anchor_entity"] for row in anchor_payloads} == {
        "PHONE_MOBILE",
        "PERSON_NAME",
    }
    assert all("evidence_lane" in row for row in anchor_payloads)
    assert all(row["label_status"] in {"unknown", "review_needed"} for row in anchor_payloads)
    assert term_payloads
    assert all("evidence_lane" in row for row in term_payloads)
    assert json.loads(anchor_safety.read_text(encoding="utf-8"))["status"] == "pass"
    assert json.loads(term_safety.read_text(encoding="utf-8"))["status"] == "pass"
    assert raw_phone not in combined
    assert source_id not in combined
