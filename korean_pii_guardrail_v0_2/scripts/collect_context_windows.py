#!/usr/bin/env python3
"""Collect raw-PII-free context windows from curated URLs."""

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

from pii_guardrail.context_window_safety import (  # noqa: E402
    SOURCE_TYPES,
    build_context_corpus_safety_report,
    build_context_term_distribution,
    context_windows_jsonl,
    extract_context_windows_from_html,
    url_hash,
)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Collect safe context-window coverage evidence from curated URLs."
    )
    parser.add_argument("--project-root", type=Path, default=PROJECT_ROOT)
    parser.add_argument(
        "--url",
        action="append",
        default=[],
        metavar="SOURCE_TYPE=URL",
        help="Curated source URL. SOURCE_TYPE must be one of the schema source types.",
    )
    parser.add_argument("--max-windows-per-url", type=int, default=20)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data" / "context_corpus" / "context_windows_v1.jsonl",
    )
    parser.add_argument(
        "--term-distribution-output",
        type=Path,
        default=PROJECT_ROOT / "reports" / "context_term_distribution_v1.json",
    )
    parser.add_argument(
        "--safety-output",
        type=Path,
        default=PROJECT_ROOT / "reports" / "context_corpus_safety_v1.json",
    )
    args = parser.parse_args()
    if not args.url:
        parser.error("At least one --url SOURCE_TYPE=URL is required")
    if args.max_windows_per_url <= 0:
        parser.error("--max-windows-per-url must be positive")

    curated_sources = [_parse_source(value) for value in args.url]
    rows = []
    failed_sources = []
    for source_type, source_url in curated_sources:
        try:
            html_text = _fetch_text(source_url)
        except OSError as exc:
            failed_sources.append(
                {
                    "source_type": source_type,
                    "url_hash": url_hash(source_url),
                    "error_type": exc.__class__.__name__,
                }
            )
            continue
        rows.extend(
            extract_context_windows_from_html(
                html_text=html_text,
                source_type=source_type,
                url=source_url,
                project_root=args.project_root,
                max_windows=args.max_windows_per_url,
            )
        )

    windows_text = context_windows_jsonl(rows)
    term_distribution = build_context_term_distribution(rows)
    term_distribution["failed_source_count"] = len(failed_sources)
    term_distribution["failed_sources"] = failed_sources
    term_text = json.dumps(term_distribution, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    safety_report = build_context_corpus_safety_report(
        rows=rows,
        report_payloads=[windows_text, term_text],
        source_urls=[source_url for _, source_url in curated_sources],
    )
    safety_text = json.dumps(safety_report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    safety_report = build_context_corpus_safety_report(
        rows=rows,
        report_payloads=[windows_text, term_text, safety_text],
        source_urls=[source_url for _, source_url in curated_sources],
    )
    safety_text = json.dumps(safety_report, ensure_ascii=False, indent=2, sort_keys=True) + "\n"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.term_distribution_output.parent.mkdir(parents=True, exist_ok=True)
    args.safety_output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(windows_text, encoding="utf-8")
    args.term_distribution_output.write_text(term_text, encoding="utf-8")
    args.safety_output.write_text(safety_text, encoding="utf-8")

    print(f"Wrote context windows: {args.output}")
    print(f"Wrote term distribution: {args.term_distribution_output}")
    print(f"Wrote corpus safety: {args.safety_output}")
    print(
        "context_corpus_safety_status="
        f"{safety_report['status']} "
        f"rows={len(rows)} "
        f"raw_pii_leak_count={safety_report['raw_pii_leak_count']} "
        f"raw_url_logged_count={safety_report['raw_url_logged_count']}"
    )
    if safety_report["status"] != "pass":
        raise SystemExit(2)


def _parse_source(value: str) -> tuple[str, str]:
    source_type, separator, source_url = value.partition("=")
    if not separator or not source_type or not source_url:
        raise SystemExit("--url must use SOURCE_TYPE=URL")
    if source_type not in SOURCE_TYPES:
        raise SystemExit(f"Unsupported source type: {source_type}")
    return source_type, source_url


def _fetch_text(source_url: str) -> str:
    request = urllib.request.Request(
        source_url,
        headers={"User-Agent": "KoreanPIIGuardrailContextCoverage/0.2"},
    )
    with urllib.request.urlopen(request, timeout=20) as response:
        charset = response.headers.get_content_charset() or "utf-8"
        return response.read().decode(charset, errors="replace")


if __name__ == "__main__":
    main()
