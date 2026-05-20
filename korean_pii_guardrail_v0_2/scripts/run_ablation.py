#!/usr/bin/env python3
"""Run the small M10-2 cumulative ablation report.

This intentionally stops at A-F plus an E2 skipped marker. Full release
gates, external datasets, and real NER activation remain later M10 work.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pii_guardrail.evaluation_harness import AblationRunner, load_jsonl_cases
from pii_guardrail.pipeline import GuardrailPipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a raw-text-free v0.2 cumulative ablation summary."
    )
    parser.add_argument("--config-dir", required=True, help="Path to configs directory")
    parser.add_argument("--dataset", required=True, help="JSONL gold dataset path")
    parser.add_argument("--output", required=True, help="Output JSON report path")
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    output_path = Path(args.output)
    cases = load_jsonl_cases(dataset_path)
    pipeline = GuardrailPipeline.from_config_dir(args.config_dir)
    report = AblationRunner(pipeline).evaluate(
        cases,
        dataset_id=dataset_path.stem,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report.to_safe_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote ablation report: {output_path}")


if __name__ == "__main__":
    main()
