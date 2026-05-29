#!/usr/bin/env python3
"""Write the Phase 1 raw-text-free existing-data context evidence report."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pii_guardrail.context_evidence import (  # noqa: E402
    DEFAULT_MINIMUM_SUPPORT,
    DatasetSpec,
    build_existing_context_rule_evidence,
    dumps_json,
    render_existing_evidence_markdown,
    update_evidence_payload_safety,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate raw-text-free M4 context rule evidence from existing eval datasets."
    )
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument(
        "--dataset",
        action="append",
        default=[],
        metavar="DATASET_ID=PATH",
        help="Optional dataset override. May be repeated.",
    )
    parser.add_argument("--minimum-support", type=int, default=DEFAULT_MINIMUM_SUPPORT)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "reports" / "context_rule_evidence_existing_v1.json",
    )
    parser.add_argument(
        "--markdown-output",
        type=Path,
        default=PROJECT_ROOT / "reports" / "context_rule_evidence_existing_v1.md",
    )
    args = parser.parse_args()
    if args.minimum_support < 1:
        parser.error("--minimum-support must be positive")

    dataset_specs = tuple(_parse_dataset_arg(value) for value in args.dataset) or None
    result = build_existing_context_rule_evidence(
        args.project_root,
        dataset_specs=dataset_specs,
        minimum_support=args.minimum_support,
    )
    markdown_text = render_existing_evidence_markdown(result.payload)
    json_text = dumps_json(result.payload)
    update_evidence_payload_safety(
        result.payload,
        result.cases,
        [json_text, markdown_text],
    )
    markdown_text = render_existing_evidence_markdown(result.payload)
    json_text = dumps_json(result.payload)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.markdown_output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json_text, encoding="utf-8")
    args.markdown_output.write_text(markdown_text, encoding="utf-8")

    safety = result.payload["raw_pii_safety"]
    print(f"Wrote context rule evidence JSON: {args.output}")
    print(f"Wrote context rule evidence Markdown: {args.markdown_output}")
    print(
        "raw_pii_safety_status="
        f"{safety['status']} "
        f"raw_pii_logging_count={safety['raw_pii_logging_count']} "
        f"report_raw_text_leak_count={safety['report_raw_text_leak_count']}"
    )
    if safety["status"] != "pass":
        raise SystemExit(2)


def _parse_dataset_arg(value: str) -> DatasetSpec:
    dataset_id, separator, path = value.partition("=")
    if not separator or not dataset_id or not path:
        raise SystemExit("--dataset must use DATASET_ID=PATH")
    return DatasetSpec(dataset_id=dataset_id, path=Path(path))


if __name__ == "__main__":
    main()
