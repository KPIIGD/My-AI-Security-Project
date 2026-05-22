#!/usr/bin/env python3
"""Build evaluation JSONL from marker-authored synthetic cases.

Marker input keeps gold spans human-reviewable without hand-counting offsets.
Example:

{"id":"case-1","marked_text":"고객명 <PERSON_NAME risk=\"P1\">하늘</PERSON_NAME>"}

Output:

{"id":"case-1","text":"고객명 하늘","labels":[{"start":4,"end":6,...}]}
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pii_guardrail.enums import EntityType, RiskLevel
from pii_guardrail.evaluation_harness import load_jsonl_cases


MARKER_RE = re.compile(
    r"<(?P<entity>[A-Z_]+)(?P<attrs>(?:\s+[a-z_]+=\"[^\"]*\")*)>"
    r"(?P<value>.*?)"
    r"</(?P=entity)>",
    re.DOTALL,
)
ATTR_RE = re.compile(r"\s+([a-z_]+)=\"([^\"]*)\"")
ALLOWED_EXTRA_FIELDS = {
    "bucket",
    "negative_reason",
    "risk_focus",
    "notes",
}


class MarkerDatasetError(ValueError):
    """Raised when marker input cannot be compiled safely."""


def parse_marked_text(marked_text: str, *, case_id: str) -> tuple[str, list[dict[str, Any]]]:
    """Convert one marker-authored text into clean text and gold labels."""

    clean_parts: list[str] = []
    labels: list[dict[str, Any]] = []
    cursor = 0

    for match in MARKER_RE.finditer(marked_text):
        prefix = marked_text[cursor:match.start()]
        _reject_unconsumed_marker(prefix, case_id=case_id)
        clean_parts.append(prefix)

        entity_type = _parse_entity_type(match.group("entity"), case_id=case_id)
        attrs = _parse_attrs(match.group("attrs"), case_id=case_id)
        risk_level = _parse_risk_level(attrs, case_id=case_id)
        value = match.group("value")
        if not value:
            raise MarkerDatasetError(f"case_id={case_id} marker value is empty")
        _reject_unconsumed_marker(value, case_id=case_id)

        start = sum(len(part) for part in clean_parts)
        clean_parts.append(value)
        end = start + len(value)
        suffix = attrs.get("suffix")
        labels.append(
            {
                "start": start,
                "end": end,
                "entity_type": entity_type.value,
                "risk_level": risk_level.value,
                "suffix": suffix if suffix != "" else None,
            }
        )
        cursor = match.end()

    tail = marked_text[cursor:]
    _reject_unconsumed_marker(tail, case_id=case_id)
    clean_parts.append(tail)
    return "".join(clean_parts), labels


def compile_record(raw: dict[str, Any], *, line_number: int) -> dict[str, Any]:
    """Compile one input JSON object into the evaluation JSONL schema."""

    case_id = str(raw.get("id", "")).strip()
    if not case_id:
        raise MarkerDatasetError(f"line={line_number} missing required id")
    if "marked_text" not in raw:
        raise MarkerDatasetError(f"case_id={case_id} missing required marked_text")
    marked_text = str(raw["marked_text"])
    text, labels = parse_marked_text(marked_text, case_id=case_id)

    compiled: dict[str, Any] = {
        "id": case_id,
        "text": text,
        "labels": labels,
        "tags": list(raw.get("tags", [])),
    }
    if "expected_masked_text" in raw:
        compiled["expected_masked_text"] = raw["expected_masked_text"]
    for field in ALLOWED_EXTRA_FIELDS:
        if field in raw:
            compiled[field] = raw[field]
    return compiled


def compile_jsonl(input_path: Path) -> list[dict[str, Any]]:
    """Compile all marker cases from a JSONL file."""

    records: list[dict[str, Any]] = []
    seen_ids: set[str] = set()
    for line_number, line in enumerate(input_path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = line.strip()
        if not stripped:
            continue
        raw = json.loads(stripped)
        if not isinstance(raw, dict):
            raise MarkerDatasetError(f"line={line_number} must be a JSON object")
        compiled = compile_record(raw, line_number=line_number)
        case_id = compiled["id"]
        if case_id in seen_ids:
            raise MarkerDatasetError(f"case_id={case_id} is duplicated")
        seen_ids.add(case_id)
        records.append(compiled)
    return records


def write_jsonl(records: list[dict[str, Any]], output_path: Path) -> None:
    """Write compiled evaluation cases as UTF-8 JSONL."""

    output_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        json.dumps(record, ensure_ascii=False, separators=(",", ":"))
        for record in records
    ]
    output_path.write_text("\n".join(lines) + ("\n" if lines else ""), encoding="utf-8")


def _parse_attrs(raw_attrs: str, *, case_id: str) -> dict[str, str]:
    attrs: dict[str, str] = {}
    consumed = ""
    for match in ATTR_RE.finditer(raw_attrs):
        key, value = match.groups()
        if key in attrs:
            raise MarkerDatasetError(f"case_id={case_id} duplicate marker attr {key}")
        attrs[key] = value
        consumed += match.group(0)
    if consumed != raw_attrs:
        raise MarkerDatasetError(f"case_id={case_id} has malformed marker attrs")
    unknown = set(attrs) - {"risk", "suffix"}
    if unknown:
        joined = ", ".join(sorted(unknown))
        raise MarkerDatasetError(f"case_id={case_id} has unsupported marker attrs: {joined}")
    return attrs


def _parse_entity_type(value: str, *, case_id: str) -> EntityType:
    try:
        return EntityType(value)
    except ValueError as exc:
        raise MarkerDatasetError(f"case_id={case_id} unknown entity_type={value}") from exc


def _parse_risk_level(attrs: dict[str, str], *, case_id: str) -> RiskLevel:
    if "risk" not in attrs:
        raise MarkerDatasetError(f"case_id={case_id} marker missing risk attr")
    try:
        return RiskLevel(attrs["risk"])
    except ValueError as exc:
        raise MarkerDatasetError(f"case_id={case_id} unknown risk={attrs['risk']}") from exc


def _reject_unconsumed_marker(text: str, *, case_id: str) -> None:
    if "<" in text or ">" in text:
        raise MarkerDatasetError(f"case_id={case_id} has malformed or nested marker")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Compile marker-authored synthetic evaluation cases to JSONL."
    )
    parser.add_argument("--input", required=True, help="Marker JSONL input path")
    parser.add_argument("--output", required=True, help="Evaluation JSONL output path")
    parser.add_argument(
        "--validate",
        action="store_true",
        help="Load the generated JSONL through the evaluation loader after writing.",
    )
    args = parser.parse_args()

    records = compile_jsonl(Path(args.input))
    write_jsonl(records, Path(args.output))
    if args.validate:
        load_jsonl_cases(Path(args.output))
    print(f"compiled_cases={len(records)} output={args.output}")


if __name__ == "__main__":
    main()
