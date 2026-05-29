#!/usr/bin/env python3
"""Generate Phase 5 reviewed context scoring release-gate comparison reports."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pii_guardrail.context_phase5 import write_phase5_reviewed_config_reports  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate raw-text-free Phase 5 config/release-gate evidence."
    )
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument(
        "--phase4-delta-path",
        type=Path,
        default=PROJECT_ROOT / "reports" / "context_delta_sweep_v1.json",
    )
    parser.add_argument(
        "--before-release-gate-path",
        type=Path,
        default=PROJECT_ROOT / "reports" / "release_gate_v0_2.json",
    )
    parser.add_argument(
        "--after-release-gate-path",
        type=Path,
        default=PROJECT_ROOT / "reports" / "release_gate_m4_phase5_after_v1.json",
    )
    parser.add_argument(
        "--after-audit-safety-path",
        type=Path,
        default=PROJECT_ROOT
        / "reports"
        / "audit_safety_release_gate_m4_phase5_after_v1.json",
    )
    args = parser.parse_args()

    result, paths = write_phase5_reviewed_config_reports(
        project_root=args.project_root,
        phase4_delta_path=args.phase4_delta_path,
        before_release_gate_path=args.before_release_gate_path,
        after_release_gate_path=args.after_release_gate_path,
        after_audit_safety_path=args.after_audit_safety_path,
    )
    for name, path in paths.items():
        print(f"Wrote {name}: {path}")
    print(
        "phase5_status="
        f"{result.comparison['status']} "
        f"approved_delta_count={result.comparison['approved_delta_count']} "
        f"config_update_applied={result.comparison['config_update_applied']} "
        f"after_release_gate_status={result.comparison['release_gate_summary']['after_status']}"
    )
    if result.comparison["status"] != "pass":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
