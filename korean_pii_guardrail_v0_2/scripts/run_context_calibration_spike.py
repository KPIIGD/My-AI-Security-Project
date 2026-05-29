#!/usr/bin/env python3
"""Run the Phase 7 research-only context logistic calibration spike."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pii_guardrail.context_phase7 import write_phase7_report  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate the raw-text-free Phase 7 calibration spike report."
    )
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args()

    payload, report_path = write_phase7_report(args.project_root)
    print(f"Wrote calibration spike report: {report_path}")
    print(
        "phase7_status="
        f"{payload['status']} "
        f"promotion_decision={payload['promotion_decision']} "
        f"locked_test_ece_improved={payload['locked_test_ece_improved']} "
        f"recall_regressed={payload['actionable_high_risk_recall_regressed']}"
    )
    if payload["status"] != "pass":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
