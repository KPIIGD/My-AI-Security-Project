#!/usr/bin/env python3
"""Build M4 Phase 6 draft labels and reviewer packet."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pii_guardrail.context_label_review import (  # noqa: E402
    write_context_label_review_artifacts,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build raw-free M4 context label review packet."
    )
    parser.add_argument(
        "--anchor-input",
        type=Path,
        default=PROJECT_ROOT / "data" / "context_corpus" / "context_anchor_windows_v1.jsonl",
    )
    parser.add_argument(
        "--draft-label-output",
        type=Path,
        default=(
            PROJECT_ROOT
            / "data"
            / "context_corpus"
            / "context_anchor_draft_labels_v1.jsonl"
        ),
    )
    parser.add_argument(
        "--review-packet-output",
        type=Path,
        default=(
            PROJECT_ROOT
            / "data"
            / "context_corpus"
            / "context_label_review_packet_v1.jsonl"
        ),
    )
    parser.add_argument(
        "--review-packet-md-output",
        type=Path,
        default=PROJECT_ROOT / "reports" / "context_label_review_packet_v1.md",
    )
    parser.add_argument(
        "--label-quality-output",
        type=Path,
        default=PROJECT_ROOT / "reports" / "context_label_quality_v1.json",
    )
    parser.add_argument(
        "--label-review-safety-output",
        type=Path,
        default=PROJECT_ROOT / "reports" / "context_label_review_safety_v1.json",
    )
    parser.add_argument(
        "--reviewer-approved-input",
        type=Path,
        default=(
            PROJECT_ROOT
            / "data"
            / "context_corpus"
            / "context_anchor_reviewer_approved_labels_v1.jsonl"
        ),
    )
    args = parser.parse_args()

    quality = write_context_label_review_artifacts(
        anchor_input_path=args.anchor_input,
        draft_label_output_path=args.draft_label_output,
        review_packet_output_path=args.review_packet_output,
        review_packet_md_output_path=args.review_packet_md_output,
        label_quality_output_path=args.label_quality_output,
        label_review_safety_output_path=args.label_review_safety_output,
        reviewer_approved_input_path=args.reviewer_approved_input,
    )
    print(f"Wrote draft labels: {args.draft_label_output}")
    print(f"Wrote review packet rows: {args.review_packet_output}")
    print(f"Wrote review packet report: {args.review_packet_md_output}")
    print(f"Wrote label quality report: {args.label_quality_output}")
    print(f"Wrote label review safety: {args.label_review_safety_output}")
    print(
        "context_label_review_status="
        f"{quality['label_quality_gate']['status']} "
        f"draft_rows={quality['draft_label_count']} "
        f"review_packet_rows={quality['reviewer_packet_sample_count']} "
        f"reviewer_approved_rows={quality['reviewer_approved_label_count']} "
        f"raw_pii_leak_count={quality['raw_pii_safety']['raw_pii_leak_count']} "
        f"verdicts={','.join(quality['label_quality_gate']['failure_verdicts'])}"
    )


if __name__ == "__main__":
    main()
