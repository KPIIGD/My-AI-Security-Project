#!/usr/bin/env python3
"""Generate Phase 4 context rule metrics, delta sweep, and policy reports."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pii_guardrail.context_phase4 import write_phase4_reports  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate raw-text-free Phase 4 context scoring evidence reports."
    )
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args()

    result, paths = write_phase4_reports(args.project_root)
    for name, path in paths.items():
        print(f"Wrote {name}: {path}")
    print(
        "phase4_status=pass "
        f"rule_evidence_safety={result.rule_evidence['raw_pii_safety']['status']} "
        f"eligible_rules={result.delta_sweep['eligible_rule_count']} "
        f"config_changes_proposed={len(result.delta_sweep['config_changes_proposed'])}"
    )
    if result.rule_evidence["raw_pii_safety"]["status"] != "pass":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
