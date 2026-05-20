#!/usr/bin/env python3
"""Run the v0.2 final-pipeline evaluation core.

This is intentionally narrower than the full M10 ablation/release-gate
surface. It runs the integrated GuardrailPipeline against one JSONL gold
set and writes a raw-text-free JSON summary report.
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

from pii_guardrail.evaluation_harness import EvaluationRunner, load_jsonl_cases
from pii_guardrail.pipeline import GuardrailPipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a raw-text-free v0.2 evaluation summary."
    )
    parser.add_argument("--config-dir", required=True, help="Path to configs directory")
    parser.add_argument("--dataset", required=True, help="JSONL gold dataset path")
    parser.add_argument("--output", required=True, help="Output JSON report path")
    parser.add_argument(
        "--purpose-id",
        default="ko_pii_guardrail_v0_2_eval",
        help="Safe purpose identifier to include in the report",
    )
    parser.add_argument(
        "--policy-profile",
        default="strict",
        help="Policy profile label to include in the report",
    )
    args = parser.parse_args()

    dataset_path = Path(args.dataset)
    output_path = Path(args.output)
    cases = load_jsonl_cases(dataset_path)
    pipeline = GuardrailPipeline.from_config_dir(args.config_dir)
    report = EvaluationRunner(pipeline).evaluate(
        cases,
        dataset_id=dataset_path.stem,
    )
    payload = report.to_safe_dict(
        purpose_id=args.purpose_id,
        policy_profile=args.policy_profile,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote evaluation report: {output_path}")


if __name__ == "__main__":
    main()
