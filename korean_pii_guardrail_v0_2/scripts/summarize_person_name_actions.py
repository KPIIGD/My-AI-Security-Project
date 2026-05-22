#!/usr/bin/env python3
"""Build action-aware PERSON_NAME metrics for stage-1 datasets.

The main M10 evaluator treats public spans as predictions regardless of final
action. This helper separates candidate-level behavior from actionable
MASK/HASH/BLOCK behavior so PERSON_NAME fixes can target the right layer.

The output is raw-text-free: it records ids, tags, actions, lengths, scores,
and reason-code ids, never matched values.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pii_guardrail.enums import Action, EntityType
from pii_guardrail.evaluation_harness import EvaluationCase, EvaluationLabel, load_jsonl_cases
from pii_guardrail.ner import MockNERDetector
from pii_guardrail.pipeline import GuardrailPipeline
from pii_guardrail.schema import GuardrailRequest, PublicPIISpan


ACTIONABLE_ACTIONS = {Action.MASK, Action.HASH, Action.BLOCK}


@dataclass(frozen=True)
class PersonNameActionMetrics:
    tp_exact: int = 0
    fn: int = 0
    fp: int = 0

    @property
    def precision(self) -> float:
        denominator = self.tp_exact + self.fp
        return self.tp_exact / denominator if denominator else 0.0

    @property
    def recall(self) -> float:
        denominator = self.tp_exact + self.fn
        return self.tp_exact / denominator if denominator else 0.0

    @property
    def f1(self) -> float:
        precision = self.precision
        recall = self.recall
        return 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    def to_dict(self) -> dict[str, float | int]:
        return {
            "tp_exact": self.tp_exact,
            "fn": self.fn,
            "fp": self.fp,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
        }


def build_summary(
    cases: Iterable[EvaluationCase],
    pipeline: GuardrailPipeline,
) -> dict[str, object]:
    case_list = list(cases)
    candidate_tp = candidate_fn = candidate_fp = 0
    actionable_tp = actionable_fn = actionable_fp = 0

    action_counts: Counter[str] = Counter()
    action_counts_by_bucket: dict[str, Counter[str]] = defaultdict(Counter)
    failure_tags: Counter[str] = Counter()
    failure_rows: list[dict[str, object]] = []
    reason_code_counts: Counter[str] = Counter()
    person_span_count = 0
    gold_count = 0

    for case in case_list:
        bucket = _bucket(case)
        response = pipeline.process(GuardrailRequest(text=case.text))
        labels = tuple(
            label for label in case.labels if label.entity_type is EntityType.PERSON_NAME
        )
        predictions = tuple(
            span for span in response.spans if span.entity_type is EntityType.PERSON_NAME
        )
        actionable_predictions = tuple(
            span for span in predictions if span.action in ACTIONABLE_ACTIONS
        )
        gold_count += len(labels)
        person_span_count += len(predictions)
        for span in predictions:
            action_counts[span.action.value] += 1
            action_counts_by_bucket[bucket][span.action.value] += 1

        c_tp, c_fn, c_fp, c_rows = _match_case(
            case=case,
            labels=labels,
            predictions=predictions,
            scope="candidate",
            bucket=bucket,
        )
        a_tp, a_fn, a_fp, a_rows = _match_case(
            case=case,
            labels=labels,
            predictions=actionable_predictions,
            scope="actionable",
            bucket=bucket,
        )
        candidate_tp += c_tp
        candidate_fn += c_fn
        candidate_fp += c_fp
        actionable_tp += a_tp
        actionable_fn += a_fn
        actionable_fp += a_fp
        for row in (*c_rows, *a_rows):
            failure_rows.append(row)
            for tag in row["tags"]:
                if tag not in {"stage1", "stage1_expanded"}:
                    failure_tags[str(tag)] += 1
            for code in row.get("reason_codes", ()):
                reason_code_counts[str(code)] += 1

    return {
        "report_type": "PersonNameActionSummary",
        "dataset_id": _dataset_id(case_list),
        "records_processed": len(case_list),
        "gold_person_name_count": gold_count,
        "person_name_public_span_count": person_span_count,
        "action_counts": dict(sorted(action_counts.items())),
        "action_counts_by_bucket": {
            bucket: dict(sorted(counter.items()))
            for bucket, counter in sorted(action_counts_by_bucket.items())
        },
        "candidate_metrics": PersonNameActionMetrics(
            candidate_tp, candidate_fn, candidate_fp
        ).to_dict(),
        "actionable_metrics": PersonNameActionMetrics(
            actionable_tp, actionable_fn, actionable_fp
        ).to_dict(),
        "failure_tag_counts": dict(failure_tags.most_common()),
        "reason_code_counts": dict(reason_code_counts.most_common(40)),
        "failure_rows": failure_rows,
        "raw_value_logged": False,
    }


def _match_case(
    *,
    case: EvaluationCase,
    labels: tuple[EvaluationLabel, ...],
    predictions: tuple[PublicPIISpan, ...],
    scope: str,
    bucket: str,
) -> tuple[int, int, int, list[dict[str, object]]]:
    tp = fn = fp = 0
    rows: list[dict[str, object]] = []
    used: set[int] = set()
    for label in labels:
        match_idx = None
        for idx, prediction in enumerate(predictions):
            if idx in used:
                continue
            if label.start == prediction.start and label.end == prediction.end:
                match_idx = idx
                break
        if match_idx is None:
            fn += 1
            rows.append(
                {
                    "case_id": case.id,
                    "bucket": bucket,
                    "scope": scope,
                    "error_type": "FN",
                    "tags": list(case.tags),
                    "span_length": label.end - label.start,
                }
            )
        else:
            used.add(match_idx)
            tp += 1

    for idx, prediction in enumerate(predictions):
        if idx in used:
            continue
        fp += 1
        rows.append(
            {
                "case_id": case.id,
                "bucket": bucket,
                "scope": scope,
                "error_type": "FP",
                "tags": list(case.tags),
                "action": prediction.action.value,
                "span_length": prediction.end - prediction.start,
                "score": round(prediction.score, 4),
                "reason_codes": list(prediction.reason_codes),
            }
        )
    return tp, fn, fp, rows


def _bucket(case: EvaluationCase) -> str:
    for tag in case.tags:
        if tag in {"hard_negative_name", "person_context_positive"}:
            return tag
    return "unknown"


def _dataset_id(cases: list[EvaluationCase]) -> str:
    if not cases:
        return "empty"
    first = cases[0].id
    if first.startswith("stage1-name-"):
        return "stage1_person_name_expanded" if "expanded" in cases[0].tags else "stage1_person_name_seed"
    return "custom"


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Summarize candidate vs actionable PERSON_NAME behavior."
    )
    parser.add_argument("--config-dir", required=True, help="Path to configs directory")
    parser.add_argument("--dataset", required=True, help="Evaluation JSONL path")
    parser.add_argument("--output", required=True, help="Summary JSON output path")
    args = parser.parse_args()

    cases = load_jsonl_cases(Path(args.dataset))
    pipeline = GuardrailPipeline.from_config_dir(
        args.config_dir,
        ner_detector=MockNERDetector(),
    )
    summary = build_summary(cases, pipeline)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(f"wrote_summary={args.output} records={summary['records_processed']}")


if __name__ == "__main__":
    main()
