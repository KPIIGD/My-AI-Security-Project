from __future__ import annotations

import json
import subprocess
import sys
from copy import deepcopy
from pathlib import Path

from pii_guardrail.context_calibration import (
    SPLITS,
    build_context_calibration_records,
    build_dataset_card,
    build_dataset_safety_report,
    load_generated_context_calibration_cases,
    validate_context_calibration_records,
    write_context_calibration_datasets,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_context_calibration_records_validate_offsets_suffixes_and_splits() -> None:
    records_by_split = build_context_calibration_records()
    validation = validate_context_calibration_records(records_by_split)

    assert set(records_by_split) == set(SPLITS)
    assert validation["status"] == "pass"
    assert validation["template_level_split"] == "pass"
    assert validation["offset_validation_error_count"] == 0
    assert validation["suffix_validation_error_count"] == 0
    assert validation["expected_masked_text_error_count"] == 0
    assert validation["raw_pii_safety"]["raw_value_logged_count"] == 0
    assert validation["raw_pii_safety"]["synthetic_fixture_only"] is True
    assert validation["raw_pii_safety"]["production_pii_used"] is False


def test_context_calibration_balances_required_buckets() -> None:
    records_by_split = build_context_calibration_records()
    validation = validate_context_calibration_records(records_by_split)
    buckets = validation["bucket_counts"]
    labels = validation["label_counts"]

    for required in (
        "hard_negative_public_number",
        "hard_negative_placeholder",
        "hard_negative_code_log",
        "hard_negative_business_name",
        "hard_negative_abstract_value",
        "positive_person_phone",
        "positive_address",
        "positive_bank_account",
    ):
        assert buckets[required] >= 1
    for entity in (
        "PERSON_NAME",
        "PHONE_MOBILE",
        "EMAIL",
        "BANK_ACCOUNT",
        "ADDRESS_FULL",
        "ORGANIZATION",
        "MEDICAL_RECORD_NO",
    ):
        assert labels[entity] >= 1


def test_context_calibration_rejects_cross_split_template_reuse() -> None:
    records_by_split = build_context_calibration_records()
    duplicate = deepcopy(records_by_split["train"][0])
    duplicate["id"] = "duplicated-template-in-test"
    duplicate["template_id"] = "duplicated_template_in_test"
    records_by_split["test"].append(duplicate)

    validation = validate_context_calibration_records(records_by_split)

    assert validation["status"] == "fail"
    assert validation["template_level_split"] == "fail"
    assert any(
        error["error_type"] == "template_split_leakage"
        for error in validation["validation_errors"]
    )


def test_context_calibration_counts_missing_suffix_as_suffix_error() -> None:
    records_by_split = build_context_calibration_records()
    tampered = deepcopy(records_by_split)
    for record in tampered["train"]:
        for label in record["labels"]:
            if label.get("suffix"):
                label["suffix"] = None
                validation = validate_context_calibration_records(tampered)
                assert validation["status"] == "fail"
                assert validation["suffix_validation_error_count"] >= 1
                assert any(
                    error["error_type"] == "suffix_missing"
                    for error in validation["validation_errors"]
                )
                return
    raise AssertionError("fixture should include at least one suffixed label")


def test_context_calibration_counts_wrong_suffix_as_suffix_error() -> None:
    records_by_split = build_context_calibration_records()
    tampered = deepcopy(records_by_split)
    for record in tampered["train"]:
        for label in record["labels"]:
            if label.get("suffix"):
                label["suffix"] = "님"
                validation = validate_context_calibration_records(tampered)
                assert validation["status"] == "fail"
                assert validation["suffix_validation_error_count"] >= 1
                assert any(
                    error["error_type"] == "suffix_mismatch"
                    for error in validation["validation_errors"]
                )
                return
    raise AssertionError("fixture should include at least one suffixed label")


def test_context_calibration_dataset_card_and_safety_report_are_raw_safe() -> None:
    records_by_split = build_context_calibration_records()
    validation = validate_context_calibration_records(records_by_split)
    card = build_dataset_card(records_by_split, validation)
    safety = build_dataset_safety_report(validation)
    serialized = card + json.dumps(safety, ensure_ascii=False)

    assert safety["status"] == "pass"
    assert safety["offset_validation_error_count"] == 0
    assert safety["raw_value_logged_count"] == 0
    assert "010-2345-6789" not in serialized
    assert "900101-1234568" not in serialized
    assert "applicant01@example.test" not in serialized


def test_build_context_calibration_dataset_cli_writes_loadable_splits(tmp_path: Path) -> None:
    output_dir = tmp_path / "generated"
    card = tmp_path / "reports" / "dataset_card.md"
    safety = tmp_path / "reports" / "safety.json"

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "build_context_calibration_dataset.py"),
            "--output-dir",
            str(output_dir),
            "--dataset-card-output",
            str(card),
            "--safety-output",
            str(safety),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    cases_by_split = load_generated_context_calibration_cases(output_dir)
    safety_payload = json.loads(safety.read_text(encoding="utf-8"))
    assert {split: len(cases) for split, cases in cases_by_split.items()} == {
        "train": 15,
        "dev": 15,
        "test": 15,
    }
    assert safety_payload["status"] == "pass"
    assert "context_calibration_status=pass" in result.stdout
