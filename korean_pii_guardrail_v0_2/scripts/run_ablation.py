#!/usr/bin/env python3
"""Run the small M10-2 cumulative ablation report.

This intentionally stops at A-F and leaves full release gates / external
datasets to later M10 work. Real NER v3 is enabled by default for E2/F;
use ``--mock-ner`` only for lightweight contract tests.
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
from pii_guardrail.ner import FinetunedNERDetector, NERDependencyError
from pii_guardrail.pipeline import GuardrailPipeline


DEFAULT_REAL_NER_MODEL_PATH = "vmaca123/korean-pii-ner-v3"


def build_pipeline(
    *,
    config_dir: str,
    use_real_ner: bool = True,
    ner_model_path: str | None = None,
    ner_calibration_path: str | None = None,
) -> GuardrailPipeline:
    """Build the ablation pipeline with real NER v3 by default."""

    ner_detector = None
    if use_real_ner:
        ner_detector = FinetunedNERDetector(
            model_path=ner_model_path or DEFAULT_REAL_NER_MODEL_PATH,
            calibration_path=ner_calibration_path,
        )
    return GuardrailPipeline.from_config_dir(
        config_dir,
        ner_detector=ner_detector,
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run a raw-text-free v0.2 cumulative ablation summary."
    )
    parser.add_argument("--config-dir", required=True, help="Path to configs directory")
    parser.add_argument("--dataset", required=True, help="JSONL gold dataset path")
    parser.add_argument("--output", required=True, help="Output JSON report path")
    parser.add_argument(
        "--mock-ner",
        action="store_true",
        help="Use MockNERDetector and keep E2 skipped.",
    )
    parser.add_argument(
        "--ner-model-path",
        default=DEFAULT_REAL_NER_MODEL_PATH,
        help=(
            "Local model directory or HuggingFace model id for real NER v3. "
            f"Default: {DEFAULT_REAL_NER_MODEL_PATH}"
        ),
    )
    parser.add_argument(
        "--ner-calibration-path",
        help="Optional calibration JSON path for real NER v3 thresholds.",
    )
    args = parser.parse_args()
    if args.mock_ner and args.ner_calibration_path:
        parser.error("--ner-calibration-path cannot be used with --mock-ner")

    dataset_path = Path(args.dataset)
    output_path = Path(args.output)
    cases = load_jsonl_cases(dataset_path)
    pipeline = build_pipeline(
        config_dir=args.config_dir,
        use_real_ner=not args.mock_ner,
        ner_model_path=args.ner_model_path,
        ner_calibration_path=args.ner_calibration_path,
    )
    try:
        report = AblationRunner(pipeline).evaluate(
            cases,
            dataset_id=dataset_path.stem,
        )
    except NERDependencyError as exc:
        raise SystemExit(f"Real NER ablation failed: {exc}") from exc
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(report.to_safe_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote ablation report: {output_path}")


if __name__ == "__main__":
    main()
