from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from pii_guardrail.context_label_review import (
    build_context_anchor_draft_labels,
    build_context_label_quality_report,
    build_context_label_review_packet_rows,
    build_context_label_review_safety_report,
    draft_labels_jsonl,
    required_reviewer_sample_size,
    review_packet_jsonl,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_phase6_draft_labels_are_raw_free_and_not_gold() -> None:
    draft_rows = build_context_anchor_draft_labels(_anchor_rows())

    assert draft_rows
    for row in draft_rows:
        assert row["schema_version"] == "context_anchor_draft_labels_v1"
        assert row["reviewer_approved"] is False
        assert row["score_tuning_eligible"] is False
        assert row["codex_draft_label_is_gold"] is False
        assert row["raw_value_logged"] is False
        assert row["candidate_value_stored"] is False


def test_phase6_label_quality_gate_stops_without_reviewer_labels() -> None:
    draft_rows = build_context_anchor_draft_labels(_anchor_rows())
    packet_rows = build_context_label_review_packet_rows(draft_rows, sample_size=4)
    draft_text = draft_labels_jsonl(draft_rows)
    packet_text = review_packet_jsonl(packet_rows)
    safety = build_context_label_review_safety_report(
        draft_label_text=draft_text,
        review_packet_text=packet_text,
    )
    quality = build_context_label_quality_report(
        draft_rows=draft_rows,
        review_packet_rows=packet_rows,
        reviewer_approved_rows=[],
        reviewer_approved_artifact_exists=False,
        safety_report=safety,
    )

    assert quality["label_quality_gate"]["status"] == "fail"
    assert "needs_reviewer_labels" in quality["label_quality_gate"]["failure_verdicts"]
    assert quality["final_probability_input_label_source"] == (
        "none_missing_reviewer_approved_labels"
    )
    assert quality["codex_draft_labels_used_as_gold"] is False
    assert quality["unknown_labels_used_for_final_score_tuning"] is False
    assert quality["raw_pii_safety"]["status"] == "pass"


def test_phase6_required_sample_size_uses_1000_when_enough_rows() -> None:
    assert required_reviewer_sample_size(1307) == 1000
    assert required_reviewer_sample_size(100) == 100
    assert required_reviewer_sample_size(0) == 0


def test_phase6_one_reviewer_approved_row_cannot_pass_label_quality_gate() -> None:
    draft_rows = build_context_anchor_draft_labels(_anchor_rows())
    packet_rows = build_context_label_review_packet_rows(draft_rows, sample_size=4)
    approved_row = {
        "draft_label_id": draft_rows[0]["draft_label_id"],
        "draft_label": draft_rows[0]["draft_label"],
        "reviewer_label": draft_rows[0]["draft_label"],
        "reviewer_approved": True,
        "label_status": "reviewer_approved",
    }

    quality = build_context_label_quality_report(
        draft_rows=draft_rows,
        review_packet_rows=packet_rows,
        reviewer_approved_rows=[approved_row],
        reviewer_approved_artifact_exists=True,
        safety_report={"status": "pass"},
    )

    assert quality["label_quality_gate"]["status"] == "fail"
    assert quality["reviewer_approved_label_count"] == 1
    assert quality["valid_reviewer_approved_label_count"] == 1
    assert quality["final_probability_input_label_source"] == (
        "none_missing_reviewer_approved_labels"
    )
    assert "needs_more_labels" in quality["label_quality_gate"]["failure_verdicts"]


def test_phase6_duplicate_reviewer_approved_rows_cannot_satisfy_sample_size() -> None:
    draft_rows = build_context_anchor_draft_labels(_anchor_rows())
    packet_rows = build_context_label_review_packet_rows(draft_rows, sample_size=4)
    approved_row = {
        "draft_label_id": draft_rows[0]["draft_label_id"],
        "draft_label": draft_rows[0]["draft_label"],
        "reviewer_label": draft_rows[0]["draft_label"],
        "reviewer_approved": True,
        "label_status": "reviewer_approved",
    }

    quality = build_context_label_quality_report(
        draft_rows=draft_rows,
        review_packet_rows=packet_rows,
        reviewer_approved_rows=[dict(approved_row) for _ in range(100)],
        reviewer_approved_artifact_exists=True,
        safety_report={"status": "pass"},
    )

    assert quality["label_quality_gate"]["status"] == "fail"
    assert quality["unique_reviewer_approved_label_count"] == 1
    assert quality["duplicate_reviewer_approved_label_count"] == 99
    assert quality["label_quality_gate"]["checks"]["reviewer_approved_rows_valid"] is False
    assert "invalid_reviewer_labels" in quality["label_quality_gate"]["failure_verdicts"]
    assert "needs_more_labels" in quality["label_quality_gate"]["failure_verdicts"]


def test_phase6_cli_writes_expected_raw_free_stop_reports(tmp_path: Path) -> None:
    anchor_input = tmp_path / "context_anchor_windows_v1.jsonl"
    draft_output = tmp_path / "context_anchor_draft_labels_v1.jsonl"
    packet_output = tmp_path / "context_label_review_packet_v1.jsonl"
    packet_md_output = tmp_path / "context_label_review_packet_v1.md"
    quality_output = tmp_path / "context_label_quality_v1.json"
    safety_output = tmp_path / "context_label_review_safety_v1.json"
    approved_input = tmp_path / "missing_reviewer_approved.jsonl"
    anchor_input.write_text(
        "".join(
            json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n"
            for row in _anchor_rows()
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "build_context_label_review_packet.py"),
            "--anchor-input",
            str(anchor_input),
            "--draft-label-output",
            str(draft_output),
            "--review-packet-output",
            str(packet_output),
            "--review-packet-md-output",
            str(packet_md_output),
            "--label-quality-output",
            str(quality_output),
            "--label-review-safety-output",
            str(safety_output),
            "--reviewer-approved-input",
            str(approved_input),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    quality = json.loads(quality_output.read_text(encoding="utf-8"))
    safety = json.loads(safety_output.read_text(encoding="utf-8"))
    combined = (
        draft_output.read_text(encoding="utf-8")
        + packet_output.read_text(encoding="utf-8")
        + packet_md_output.read_text(encoding="utf-8")
        + quality_output.read_text(encoding="utf-8")
        + safety_output.read_text(encoding="utf-8")
        + result.stdout
    )
    assert "context_label_review_status=fail" in result.stdout
    assert "needs_reviewer_labels" in quality["label_quality_gate"]["failure_verdicts"]
    assert quality["reviewer_approved_label_count"] == 0
    assert safety["status"] == "pass"
    assert "010-" not in combined
    assert "http://" not in combined
    assert "https://" not in combined
    assert "@" not in combined


def _anchor_rows() -> list[dict]:
    rows: list[dict] = []
    for index, (entity, group, shape, label) in enumerate(
        (
            ("PERSON_NAME", "PERSON_NAME", "korean_name_like_3_syllable", "non_pii"),
            ("PERSON_NAME", "PERSON_NAME", "korean_name_3_syllable", "true_pii"),
            ("PHONE_MOBILE", "PHONE", "mobile_phone_shape", "non_pii"),
            ("EMAIL", "EMAIL", "email_shape", "true_pii"),
            ("ADDRESS_FULL", "ADDRESS", "road_address_shape", "non_pii"),
            ("BANK_ACCOUNT", "BANK_ACCOUNT", "bank_account_shape", "true_pii"),
            (
                "BUSINESS_REG_NO",
                "REGISTRATION_IDENTIFIER",
                "business_registration_shape",
                "non_pii",
            ),
        ),
        start=1,
    ):
        rows.append(
            _anchor_row(
                entity=entity,
                group=group,
                shape=shape,
                label=label,
                source_domain=("customer_support", "ecommerce", "finance")[index % 3],
                unique=f"row{index}",
            )
        )
    return rows


def _anchor_row(
    *,
    entity: str,
    group: str,
    shape: str,
    label: str,
    source_domain: str,
    unique: str,
) -> dict:
    del group
    return {
        "schema_version": "context_anchor_windows_v1",
        "anchor_entity": entity,
        "anchor_shape": shape,
        "anchor_source": "heuristic_shape",
        "label": label,
        "source_domain": source_domain,
        "material_class": "realistic_input_like",
        "material_type": "realistic_input_like",
        "evidence_lane": "hard_negative_corpus"
        if label == "non_pii"
        else "safe_synthetic_insertion",
        "label_source": "codex_draft"
        if label == "non_pii"
        else "safe_synthetic_generator",
        "label_status": "review_needed",
        "mvp_target": {"true_pii": 1000, "non_pii": 1000},
        "current_count": {"true_pii": 1 if label == "true_pii" else 0, "non_pii": 1 if label == "non_pii" else 0, "unknown": 0},
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
            "unigrams": [token, "review"],
            "bigrams": [f"{token} review"],
            "trigrams": [],
        },
        "within_5_tokens": {
            "unigrams": [token, "review", "field"],
            "bigrams": [f"{token} review", "review field"],
            "trigrams": [f"{token} review field"],
        },
    }
