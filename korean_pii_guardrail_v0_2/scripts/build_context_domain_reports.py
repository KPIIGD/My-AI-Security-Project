#!/usr/bin/env python3
"""Generate Phase 6 domain evidence and customer aggregate templates."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pii_guardrail.context_phase6 import write_phase6_reports  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate raw-text-free Phase 6 domain and aggregate evidence."
    )
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    args = parser.parse_args()

    result, paths = write_phase6_reports(args.project_root)
    for name, path in paths.items():
        print(f"Wrote {name}: {path}")
    print(
        "phase6_status="
        f"{result.domain_evidence['status']} "
        f"domain_rows={len(result.domain_evidence['domain_rows'])} "
        f"low_support_domain_rows={result.domain_evidence['low_support_domain_row_count']} "
        f"customer_template_status={result.customer_template['status']}"
    )
    if (
        result.domain_evidence["status"] != "pass"
        or result.customer_template["status"] != "pass"
    ):
        raise SystemExit(2)


if __name__ == "__main__":
    main()
