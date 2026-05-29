#!/usr/bin/env python3
"""Write the Phase 1 raw-text-free context rule inventory report."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pii_guardrail.context_evidence import (  # noqa: E402
    build_context_rule_inventory,
    dumps_json,
    render_inventory_markdown,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate a raw-text-free M4 context rule inventory."
    )
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "reports" / "context_rule_inventory_v1.json",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=PROJECT_ROOT / "reports" / "context_rule_inventory_v1.md",
    )
    args = parser.parse_args()

    payload = build_context_rule_inventory(args.project_root)
    json_text = dumps_json(payload)
    markdown_text = render_inventory_markdown(payload)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json_text, encoding="utf-8")
    args.markdown_output.write_text(markdown_text, encoding="utf-8")

    print(f"Wrote context rule inventory JSON: {args.output}")
    print(f"Wrote context rule inventory Markdown: {args.markdown_output}")
    print(f"rule_count={payload['rule_count']} raw_value_logged=false")


if __name__ == "__main__":
    main()
