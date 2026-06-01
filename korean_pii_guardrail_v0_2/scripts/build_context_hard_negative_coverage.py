#!/usr/bin/env python3
"""Build M4 Phase 5 hard-negative coverage artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pii_guardrail.context_hard_negative_coverage import (  # noqa: E402
    write_context_hard_negative_coverage_artifacts,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build raw-free hard-negative coverage artifacts."
    )
    parser.add_argument(
        "--anchor-input",
        type=Path,
        default=PROJECT_ROOT / "data" / "context_corpus" / "context_anchor_windows_v1.jsonl",
    )
    parser.add_argument(
        "--hard-negative-output",
        type=Path,
        default=(
            PROJECT_ROOT
            / "data"
            / "context_corpus"
            / "context_hard_negative_anchor_windows_v1.jsonl"
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
        "--report-json-output",
        type=Path,
        default=PROJECT_ROOT / "reports" / "context_hard_negative_coverage_v1.json",
    )
    parser.add_argument(
        "--report-md-output",
        type=Path,
        default=PROJECT_ROOT / "reports" / "context_hard_negative_coverage_v1.md",
    )
    args = parser.parse_args()

    report = write_context_hard_negative_coverage_artifacts(
        anchor_input_path=args.anchor_input,
        hard_negative_output_path=args.hard_negative_output,
        anchor_output_path=args.anchor_output,
        term_output_path=args.term_output,
        manifest_output_path=args.manifest_output,
        anchor_safety_output_path=args.anchor_safety_output,
        report_json_output_path=args.report_json_output,
        report_md_output_path=args.report_md_output,
    )
    print(f"Wrote hard-negative anchors: {args.hard_negative_output}")
    print(f"Wrote augmented context anchors: {args.anchor_output}")
    print(f"Wrote Korean context terms: {args.term_output}")
    print(f"Wrote context anchor manifest: {args.manifest_output}")
    print(f"Wrote hard-negative coverage report: {args.report_md_output}")
    print(
        "context_hard_negative_coverage_status="
        f"{report['hard_negative_gate']['status']} "
        f"generated_rows={report['generated_hard_negative_anchor_count']} "
        f"final_rows={report['final_anchor_window_count']} "
        f"raw_pii_leak_count={report['raw_pii_safety']['raw_pii_leak_count']} "
        f"verdicts={','.join(report['hard_negative_gate']['failure_verdicts'])}"
    )
    if report["hard_negative_gate"]["status"] != "pass":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
