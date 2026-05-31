#!/usr/bin/env python3
"""Build M4 Phase 4 safe synthetic true-PII anchor windows."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pii_guardrail.context_synthetic_insertion import (  # noqa: E402
    write_synthetic_true_pii_anchor_artifacts,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build safe synthetic true-PII context anchor windows."
    )
    parser.add_argument(
        "--anchor-input",
        type=Path,
        default=PROJECT_ROOT / "data" / "context_corpus" / "context_anchor_windows_v1.jsonl",
    )
    parser.add_argument(
        "--template-input",
        type=Path,
        default=PROJECT_ROOT / "data" / "context_corpus" / "context_template_inventory_v1.jsonl",
    )
    parser.add_argument(
        "--synthetic-output",
        type=Path,
        default=(
            PROJECT_ROOT
            / "data"
            / "context_corpus"
            / "context_synthetic_true_pii_anchor_windows_v1.jsonl"
        ),
    )
    parser.add_argument(
        "--anchor-output",
        type=Path,
        default=PROJECT_ROOT / "data" / "context_corpus" / "context_anchor_windows_v1.jsonl",
    )
    parser.add_argument(
        "--term-output",
        type=Path,
        default=PROJECT_ROOT / "data" / "context_corpus" / "korean_context_terms_v1.jsonl",
    )
    parser.add_argument(
        "--manifest-output",
        type=Path,
        default=(
            PROJECT_ROOT
            / "data"
            / "context_corpus"
            / "context_anchor_windows_manifest_v1.yaml"
        ),
    )
    parser.add_argument(
        "--anchor-safety-output",
        type=Path,
        default=PROJECT_ROOT / "reports" / "context_anchor_corpus_safety_v1.json",
    )
    parser.add_argument(
        "--term-safety-output",
        type=Path,
        default=PROJECT_ROOT / "reports" / "korean_context_terms_safety_v1.json",
    )
    parser.add_argument(
        "--synthetic-safety-output",
        type=Path,
        default=PROJECT_ROOT / "reports" / "context_synthetic_insertion_safety_v1.json",
    )
    parser.add_argument(
        "--synthetic-report-output",
        type=Path,
        default=PROJECT_ROOT / "reports" / "context_synthetic_insertion_v1.md",
    )
    args = parser.parse_args()

    safety_report = write_synthetic_true_pii_anchor_artifacts(
        anchor_input_path=args.anchor_input,
        template_input_path=args.template_input,
        synthetic_output_path=args.synthetic_output,
        anchor_output_path=args.anchor_output,
        term_output_path=args.term_output,
        manifest_output_path=args.manifest_output,
        anchor_safety_output_path=args.anchor_safety_output,
        term_safety_output_path=args.term_safety_output,
        synthetic_safety_output_path=args.synthetic_safety_output,
        synthetic_report_output_path=args.synthetic_report_output,
    )
    print(f"Wrote synthetic true-PII anchors: {args.synthetic_output}")
    print(f"Wrote augmented context anchors: {args.anchor_output}")
    print(f"Wrote Korean context terms: {args.term_output}")
    print(f"Wrote context anchor manifest: {args.manifest_output}")
    print(f"Wrote synthetic insertion safety: {args.synthetic_safety_output}")
    print(f"Wrote synthetic insertion report: {args.synthetic_report_output}")
    print(
        "context_synthetic_insertion_status="
        f"{safety_report['phase_exit_gate']['status']} "
        f"synthetic_rows={safety_report['synthetic_anchor_window_count']} "
        f"final_rows={safety_report['final_anchor_window_count']} "
        f"raw_pii_leak_count={safety_report['raw_pii_leak_count']} "
        f"data_quality_gate={safety_report['final_data_quality_gate_status']} "
        f"verdicts={','.join(safety_report['phase_exit_gate']['failure_verdicts'])}"
    )
    if safety_report["phase_exit_gate"]["status"] != "pass":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
