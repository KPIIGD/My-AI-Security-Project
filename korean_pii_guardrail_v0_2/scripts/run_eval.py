#!/usr/bin/env python3
"""Run the v0.2 final-pipeline evaluation core.

This is intentionally narrower than the full M10 ablation/release-gate
surface. It runs the integrated GuardrailPipeline against one JSONL gold
set and writes a raw-text-free JSON summary report. Real NER v3 is enabled
by default; use ``--mock-ner`` only for lightweight contract tests.
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

from pii_guardrail.evaluation_harness import (
    EvaluationRunner,
    build_audit_safety_report,
    count_report_raw_text_leaks,
    failure_analysis_jsonl,
    load_jsonl_cases,
)
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
    """Build the evaluation pipeline with real NER v3 by default."""

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
        description="Run a raw-text-free v0.2 evaluation summary."
    )
    parser.add_argument("--config-dir", required=True, help="Path to configs directory")
    parser.add_argument("--dataset", required=True, help="JSONL gold dataset path")
    parser.add_argument("--output", required=True, help="Output JSON report path")
    parser.add_argument(
        "--failure-output",
        help="Optional JSONL failure analysis report path",
    )
    parser.add_argument(
        "--audit-safety-output",
        help="Optional JSON audit safety report path",
    )
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
    parser.add_argument(
        "--mock-ner",
        action="store_true",
        help="Use the lightweight MockNERDetector instead of real NER v3.",
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
    failure_output_path = Path(args.failure_output) if args.failure_output else None
    audit_safety_output_path = (
        Path(args.audit_safety_output) if args.audit_safety_output else None
    )
    cases = load_jsonl_cases(dataset_path)
    pipeline = build_pipeline(
        config_dir=args.config_dir,
        use_real_ner=not args.mock_ner,
        ner_model_path=args.ner_model_path,
        ner_calibration_path=args.ner_calibration_path,
    )
    try:
        report = EvaluationRunner(pipeline).evaluate(
            cases,
            dataset_id=dataset_path.stem,
        )
    except NERDependencyError as exc:
        raise SystemExit(f"Real NER evaluation failed: {exc}") from exc
    payload = report.to_safe_dict(
        purpose_id=args.purpose_id,
        policy_profile=args.policy_profile,
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    evaluation_report_text = (
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n"
    )
    output_path.write_text(evaluation_report_text, encoding="utf-8")
    print(f"Wrote evaluation report: {output_path}")

    generated_report_texts: list[str] = [evaluation_report_text]
    if failure_output_path is not None:
        failure_report_text = failure_analysis_jsonl(report)
        failure_output_path.parent.mkdir(parents=True, exist_ok=True)
        failure_output_path.write_text(failure_report_text, encoding="utf-8")
        generated_report_texts.append(failure_report_text)
        print(f"Wrote failure analysis report: {failure_output_path}")

    if audit_safety_output_path is not None:
        leak_count = count_report_raw_text_leaks(generated_report_texts, cases)
        audit_safety_report = build_audit_safety_report(
            report,
            report_raw_text_leak_count=leak_count,
            safe_report_generated=True,
        )
        audit_safety_output_path.parent.mkdir(parents=True, exist_ok=True)
        audit_safety_output_path.write_text(
            json.dumps(
                audit_safety_report.to_dict(),
                ensure_ascii=False,
                indent=2,
                sort_keys=True,
            )
            + "\n",
            encoding="utf-8",
        )
        print(f"Wrote audit safety report: {audit_safety_output_path}")


if __name__ == "__main__":
    main()
