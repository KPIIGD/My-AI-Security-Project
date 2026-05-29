#!/usr/bin/env python3
"""Generate Stage 1.1 raw-free context source inventory artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pii_guardrail.context_source_inventory import (  # noqa: E402
    write_context_source_inventory_reports,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate raw-free Stage 1.1 context source inventory reports."
    )
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args()

    payload, paths = write_context_source_inventory_reports(args.project_root)
    for name, path in paths.items():
        print(f"Wrote {name}: {path}")
    summary = payload["current_safe_context_window_summary"]
    print(
        "source_inventory_status=pass "
        f"planned_entity_groups={len(payload['core_entity_domain_plan'])} "
        f"current_rows={summary['row_count']} "
        f"current_data_quality_status={summary['current_data_quality_status']}"
    )


if __name__ == "__main__":
    main()
