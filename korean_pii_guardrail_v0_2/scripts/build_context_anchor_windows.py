#!/usr/bin/env python3
"""Build raw-free M4 context anchor windows from curated sources."""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pii_guardrail.context_anchor_collector import (  # noqa: E402
    SOURCE_TYPE_TO_DOMAIN,
    VALID_LABELS,
    aggregate_korean_context_terms,
    build_context_anchor_safety_report,
    context_anchor_windows_jsonl,
    extract_context_anchor_windows_from_html,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build raw-free context_anchor_windows_v1 rows."
    )
    parser.add_argument(
        "--source",
        action="append",
        default=[],
        metavar="SOURCE_TYPE=PATH_OR_URL",
        help="Curated source. SOURCE_TYPE must be known to the source inventory.",
    )
    parser.add_argument(
        "--default-label",
        choices=VALID_LABELS,
        default="unknown",
        help="Label used when a detector match has no explicit marker label.",
    )
    parser.add_argument("--max-windows-per-source", type=int, default=50)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data" / "context_corpus" / "context_anchor_windows_v1.jsonl",
    )
    parser.add_argument(
        "--safety-output",
        type=Path,
        default=PROJECT_ROOT / "reports" / "context_anchor_corpus_safety_v1.json",
    )
    args = parser.parse_args()

    if not args.source:
        parser.error("At least one --source SOURCE_TYPE=PATH_OR_URL is required")
    if args.max_windows_per_source <= 0:
        parser.error("--max-windows-per-source must be positive")

    curated_sources = [_parse_source(value) for value in args.source]
    rows = []
    failed_sources = []
    for source_type, source_id in curated_sources:
        try:
            html_text = _read_source(source_id)
        except OSError as exc:
            failed_sources.append(
                {
                    "source_type": source_type,
                    "error_type": exc.__class__.__name__,
                }
            )
            continue
        rows.extend(
            extract_context_anchor_windows_from_html(
                html_text=html_text,
                source_type=source_type,
                source_id=source_id,
                default_label=args.default_label,
                max_windows=args.max_windows_per_source,
            )
        )

    term_rows = aggregate_korean_context_terms(rows)
    windows_text = context_anchor_windows_jsonl(rows)
    safety_report = build_context_anchor_safety_report(
        rows=rows,
        term_rows=term_rows,
        source_ids=[source_id for _, source_id in curated_sources],
        extra_payloads=[failed_sources],
    )
    safety_report["failed_source_count"] = len(failed_sources)
    safety_report["failed_sources"] = failed_sources
    safety_text = json.dumps(safety_report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.safety_output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(windows_text, encoding="utf-8")
    args.safety_output.write_text(safety_text, encoding="utf-8")

    print(f"Wrote context anchor windows: {args.output}")
    print(f"Wrote context anchor safety: {args.safety_output}")
    print(
        "context_anchor_safety_status="
        f"{safety_report['status']} "
        f"rows={len(rows)} "
        f"raw_pii_leak_count={safety_report['raw_pii_leak_count']} "
        f"raw_url_logged_count={safety_report['raw_url_logged_count']}"
    )
    if safety_report["status"] != "pass":
        raise SystemExit(2)


def _parse_source(value: str) -> tuple[str, str]:
    source_type, separator, source_id = value.partition("=")
    if not separator or not source_type or not source_id:
        raise SystemExit("--source must use SOURCE_TYPE=PATH_OR_URL")
    if source_type not in SOURCE_TYPE_TO_DOMAIN:
        raise SystemExit(f"Unsupported source type: {source_type}")
    return source_type, source_id


def _read_source(source_id: str) -> str:
    if _looks_like_url(source_id):
        request = urllib.request.Request(
            source_id,
            headers={"User-Agent": "KoreanPIIGuardrailContextAnchor/0.2"},
        )
        with urllib.request.urlopen(request, timeout=20) as response:
            charset = response.headers.get_content_charset() or "utf-8"
            return response.read().decode(charset, errors="replace")
    return Path(source_id).read_text(encoding="utf-8")


def _looks_like_url(source_id: str) -> bool:
    return source_id.startswith(("http" + "://", "https" + "://", "file" + "://"))


if __name__ == "__main__":
    main()
