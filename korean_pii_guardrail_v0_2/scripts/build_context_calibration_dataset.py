#!/usr/bin/env python3
"""Build Phase 3 synthetic context calibration train/dev/test datasets."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pii_guardrail.context_calibration import (  # noqa: E402
    build_dataset_card,
    build_dataset_safety_report,
    validate_context_calibration_records,
    write_context_calibration_datasets,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build raw-offset-validated synthetic context calibration datasets."
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=PROJECT_ROOT / "data" / "eval" / "generated",
    )
    parser.add_argument(
        "--dataset-card-output",
        type=Path,
        default=PROJECT_ROOT / "reports" / "context_calibration_dataset_card_v1.md",
    )
    parser.add_argument(
        "--safety-output",
        type=Path,
        default=PROJECT_ROOT / "reports" / "context_calibration_safety_v1.json",
    )
    args = parser.parse_args()

    records_by_split, paths = write_context_calibration_datasets(args.output_dir)
    validation = validate_context_calibration_records(records_by_split)
    card_text = build_dataset_card(records_by_split, validation)
    safety_report = build_dataset_safety_report(validation)

    args.dataset_card_output.parent.mkdir(parents=True, exist_ok=True)
    args.safety_output.parent.mkdir(parents=True, exist_ok=True)
    args.dataset_card_output.write_text(card_text, encoding="utf-8")
    args.safety_output.write_text(
        json.dumps(safety_report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )

    print("Wrote context calibration datasets:")
    for path in paths:
        print(f"- {path}")
    print(f"Wrote dataset card: {args.dataset_card_output}")
    print(f"Wrote safety report: {args.safety_output}")
    print(
        "context_calibration_status="
        f"{safety_report['status']} "
        f"offset_errors={safety_report['offset_validation_error_count']} "
        f"suffix_errors={safety_report['suffix_validation_error_count']} "
        f"raw_value_logged_count={safety_report['raw_value_logged_count']}"
    )
    if safety_report["status"] != "pass":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
