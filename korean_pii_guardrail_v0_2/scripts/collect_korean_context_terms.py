#!/usr/bin/env python3
"""Aggregate raw-free Korean context n-grams from anchor windows."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pii_guardrail.context_anchor_collector import (  # noqa: E402
    aggregate_korean_context_terms,
    build_context_anchor_safety_report,
    korean_context_terms_jsonl,
    load_context_anchor_windows_jsonl,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Aggregate korean_context_terms_v1 from raw-free anchor windows."
    )
    parser.add_argument(
        "--anchor-input",
        type=Path,
        default=PROJECT_ROOT / "data" / "context_corpus" / "context_anchor_windows_v1.jsonl",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data" / "context_corpus" / "korean_context_terms_v1.jsonl",
    )
    parser.add_argument(
        "--safety-output",
        type=Path,
        default=PROJECT_ROOT / "reports" / "korean_context_terms_safety_v1.json",
    )
    args = parser.parse_args()

    anchor_rows = load_context_anchor_windows_jsonl(args.anchor_input)
    term_rows = aggregate_korean_context_terms(anchor_rows)
    terms_text = korean_context_terms_jsonl(term_rows)
    safety_report = build_context_anchor_safety_report(
        rows=anchor_rows,
        term_rows=term_rows,
        source_ids=[],
        extra_payloads=[terms_text],
    )
    safety_text = json.dumps(safety_report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.safety_output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(terms_text, encoding="utf-8")
    args.safety_output.write_text(safety_text, encoding="utf-8")

    print(f"Wrote Korean context terms: {args.output}")
    print(f"Wrote context term safety: {args.safety_output}")
    print(
        "korean_context_terms_safety_status="
        f"{safety_report['status']} "
        f"terms={len(term_rows)} "
        f"raw_pii_leak_count={safety_report['raw_pii_leak_count']}"
    )
    if safety_report["status"] != "pass":
        raise SystemExit(2)


if __name__ == "__main__":
    main()
