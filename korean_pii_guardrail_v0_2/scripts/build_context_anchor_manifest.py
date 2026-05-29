#!/usr/bin/env python3
"""Build the Stage 1.4 context anchor diversity manifest."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pii_guardrail.context_anchor_manifest import (  # noqa: E402
    write_context_anchor_manifest,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build context_anchor_windows_manifest_v1.yaml."
    )
    parser.add_argument(
        "--anchor-input",
        type=Path,
        default=PROJECT_ROOT / "data" / "context_corpus" / "context_anchor_windows_v1.jsonl",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=(
            PROJECT_ROOT
            / "data"
            / "context_corpus"
            / "context_anchor_windows_manifest_v1.yaml"
        ),
    )
    args = parser.parse_args()

    payload = write_context_anchor_manifest(
        anchor_input_path=args.anchor_input,
        output_path=args.output,
    )
    gate = payload["data_quality_gate"]
    measurements = payload["measurements"]
    print(f"Wrote context anchor manifest: {args.output}")
    print(
        "context_anchor_manifest_status="
        f"{gate['status']} "
        f"rows={measurements['total_anchor_windows']} "
        f"raw_pii_leak_count={payload['raw_free_scan']['raw_pii_leak_count']} "
        f"duplicate_ratio={measurements['duplicate_anchor_window_ratio']} "
        f"verdicts={','.join(gate['failure_verdicts'])}"
    )
    if gate["status"] != "pass":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
