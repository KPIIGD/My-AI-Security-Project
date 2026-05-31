#!/usr/bin/env python3
"""Build the M4 Phase 3 raw-free template inventory."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pii_guardrail.context_template_inventory import (  # noqa: E402
    write_context_template_inventory_artifacts,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build context_template_inventory_v1 artifacts."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data" / "context_corpus" / "context_template_inventory_v1.jsonl",
    )
    parser.add_argument(
        "--safety-output",
        type=Path,
        default=PROJECT_ROOT / "reports" / "context_template_inventory_safety_v1.json",
    )
    parser.add_argument(
        "--report-output",
        type=Path,
        default=PROJECT_ROOT / "reports" / "context_template_inventory_v1.md",
    )
    args = parser.parse_args()

    safety_report = write_context_template_inventory_artifacts(
        output_path=args.output,
        safety_output_path=args.safety_output,
        report_output_path=args.report_output,
    )
    gate = safety_report["phase_exit_gate"]
    print(f"Wrote context template inventory: {args.output}")
    print(f"Wrote context template inventory safety: {args.safety_output}")
    print(f"Wrote context template inventory report: {args.report_output}")
    print(
        "context_template_inventory_status="
        f"{gate['status']} "
        f"templates={safety_report['template_count']} "
        f"raw_pii_leak_count={safety_report['raw_pii_leak_count']} "
        f"verdicts={','.join(gate['failure_verdicts'])}"
    )
    if gate["status"] != "pass":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
