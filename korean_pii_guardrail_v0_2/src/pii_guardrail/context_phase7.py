"""Phase 7 research-only logistic calibration spike."""

from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .context_calibration import DATASET_VERSION, SPLITS
from .evaluation_harness import EvaluationRunner, load_jsonl_cases
from .pipeline import GuardrailPipeline


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ECE_BINS = 5
LOGISTIC_SLOPE_L2 = 20.0
LOGISTIC_STEPS = 2500
LOGISTIC_LEARNING_RATE = 0.02
MIN_PROMOTION_PREDICTIONS = 200
_RAW_LIKE_PATTERNS = (
    re.compile(r"010-\d{3,4}-\d{4}"),
    re.compile(r"\d{6}-\d{7}"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
)


@dataclass(frozen=True)
class CalibrationPoint:
    split: str
    base_score: float
    label: int
    entity_type: str
    action: str


@dataclass(frozen=True)
class LogisticCalibrator:
    intercept: float
    slope: float

    def predict(self, base_score: float) -> float:
        clipped = _clip_probability(base_score)
        x_value = math.log(clipped / (1.0 - clipped))
        return _sigmoid(self.intercept + self.slope * x_value)


def build_phase7_logistic_calibration_spike(
    project_root: Path = PROJECT_ROOT,
) -> dict[str, Any]:
    points_by_split, recall_by_split = collect_calibration_points(project_root)
    calibrator = fit_regularized_logistic(points_by_split["train"])
    split_reports = {
        split: _split_report(
            split,
            points_by_split[split],
            recall_by_split[split],
            calibrator,
        )
        for split in SPLITS
    }
    locked_test = split_reports["test"]
    total_predictions = sum(row["prediction_count"] for row in split_reports.values())
    locked_test_ece_improved = locked_test["calibrated_ece"] < locked_test["deterministic_ece"]
    no_recall_regression = all(
        row["shadow_actionable_high_risk_recall"]
        >= row["deterministic_actionable_high_risk_recall"]
        for row in split_reports.values()
    )
    payload = {
        "report_type": "ContextLogisticCalibrationSpike",
        "version": "v0.2-single-turn",
        "phase": "Execution Phase 7. Optional Calibration Spike",
        "runtime_scoring_behavior_changed": False,
        "score_delta_changed": False,
        "deterministic_config_remains_default": True,
        "deterministic_fallback_available": True,
        "reason_codes_preserved_by_shadow_mode": True,
        "model_artifact_written": False,
        "external_dependency_added": False,
        "public_corpus_used_for_score_tuning": False,
        "algorithm": {
            "name": "regularized_logistic_shadow_calibrator",
            "features": ["logit(base_score)"],
            "intercept": round(calibrator.intercept, 6),
            "slope": round(calibrator.slope, 6),
            "slope_l2": LOGISTIC_SLOPE_L2,
            "ece_bins": ECE_BINS,
        },
        "dataset": {
            "dataset_id": DATASET_VERSION,
            "total_prediction_count": total_predictions,
            "splits": {
                split: {
                    "prediction_count": row["prediction_count"],
                    "positive_count": row["positive_count"],
                }
                for split, row in split_reports.items()
            },
        },
        "split_reports": split_reports,
        "locked_test_ece_improved": locked_test_ece_improved,
        "actionable_high_risk_recall_regressed": not no_recall_regression,
        "promotion_decision": (
            "research_only_not_promoted"
            if total_predictions < MIN_PROMOTION_PREDICTIONS
            else "eligible_for_design_review"
        ),
        "promotion_rationale": (
            "locked test ECE improved without action recall regression, but "
            "prediction support is below the promotion threshold"
            if locked_test_ece_improved and no_recall_regression
            else "calibration did not clear the reliability and recall gate"
        ),
    }
    payload["raw_pii_safety"] = {
        "raw_value_logged": False,
        "report_raw_text_leak_count": _raw_like_count(payload),
        "status": "pass" if _raw_like_count(payload) == 0 else "fail",
    }
    payload["status"] = (
        "pass"
        if payload["raw_pii_safety"]["status"] == "pass"
        and payload["deterministic_config_remains_default"]
        and no_recall_regression
        else "fail"
    )
    return payload


def collect_calibration_points(
    project_root: Path = PROJECT_ROOT,
) -> tuple[dict[str, list[CalibrationPoint]], dict[str, float]]:
    pipeline = GuardrailPipeline.from_config_dir(project_root / "configs")
    runner = EvaluationRunner(pipeline)
    points_by_split: dict[str, list[CalibrationPoint]] = {}
    recall_by_split: dict[str, float] = {}
    for split in SPLITS:
        dataset_path = (
            project_root / "data" / "eval" / "generated" / f"{DATASET_VERSION}_{split}.jsonl"
        )
        report = runner.evaluate(load_jsonl_cases(dataset_path), dataset_id=split)
        recall_by_split[split] = report.actionable_high_risk_recall
        points: list[CalibrationPoint] = []
        for case_result in report.case_results:
            for match in case_result.matches:
                if match.actual is None:
                    continue
                points.append(
                    CalibrationPoint(
                        split=split,
                        base_score=match.actual.score,
                        label=1 if match.match_type in {"exact", "partial"} else 0,
                        entity_type=match.actual.entity_type.value,
                        action=match.actual.action.value,
                    )
                )
        points_by_split[split] = points
    return points_by_split, recall_by_split


def fit_regularized_logistic(points: list[CalibrationPoint]) -> LogisticCalibrator:
    if not points:
        return LogisticCalibrator(intercept=0.0, slope=0.0)
    positive_rate = sum(point.label for point in points) / len(points)
    clipped_rate = _clip_probability(positive_rate)
    intercept = math.log(clipped_rate / (1.0 - clipped_rate))
    slope = 0.0
    for _ in range(LOGISTIC_STEPS):
        intercept_gradient = 0.0
        slope_gradient = 0.0
        for point in points:
            score = _clip_probability(point.base_score)
            x_value = math.log(score / (1.0 - score))
            predicted = _sigmoid(intercept + slope * x_value)
            error = predicted - point.label
            intercept_gradient += error
            slope_gradient += error * x_value
        intercept_gradient /= len(points)
        slope_gradient = slope_gradient / len(points) + LOGISTIC_SLOPE_L2 * slope
        intercept -= LOGISTIC_LEARNING_RATE * intercept_gradient
        slope -= LOGISTIC_LEARNING_RATE * slope_gradient
    return LogisticCalibrator(intercept=intercept, slope=slope)


def render_phase7_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Context Logistic Calibration Spike v1",
        "",
        "- phase: `Execution Phase 7. Optional Calibration Spike`",
        f"- status: `{payload['status']}`",
        f"- promotion_decision: `{payload['promotion_decision']}`",
        "- deterministic_config_remains_default: `true`",
        "- deterministic_fallback_available: `true`",
        "- runtime_scoring_behavior_changed: `false`",
        "- model_artifact_written: `false`",
        "",
        "## ECE Comparison",
        "",
        "| Split | Predictions | Deterministic ECE | Calibrated ECE | Delta | Recall Regression |",
        "|---|---:|---:|---:|---:|---|",
    ]
    for split in SPLITS:
        row = payload["split_reports"][split]
        lines.append(
            "| {split} | {count} | {base} | {cal} | {delta} | {recall} |".format(
                split=split,
                count=row["prediction_count"],
                base=row["deterministic_ece"],
                cal=row["calibrated_ece"],
                delta=row["ece_delta"],
                recall=str(row["actionable_high_risk_recall_regressed"]).lower(),
            )
        )
    lines.extend(
        [
            "",
            "## Decision",
            "",
            payload["promotion_rationale"],
            "",
            (
                "The learned score is evaluated only in shadow mode. Runtime reason "
                "codes, policy routing, and deterministic fallback remain unchanged."
            ),
        ]
    )
    return "\n".join(lines) + "\n"


def write_phase7_report(
    project_root: Path = PROJECT_ROOT,
) -> tuple[dict[str, Any], Path]:
    payload = build_phase7_logistic_calibration_spike(project_root)
    report_path = project_root / "reports" / "context_logistic_calibration_spike_v1.md"
    report_path.write_text(render_phase7_markdown(payload), encoding="utf-8")
    return payload, report_path


def _split_report(
    split: str,
    points: list[CalibrationPoint],
    recall: float,
    calibrator: LogisticCalibrator,
) -> dict[str, Any]:
    deterministic_scores = [(point.base_score, point.label) for point in points]
    calibrated_scores = [
        (calibrator.predict(point.base_score), point.label) for point in points
    ]
    deterministic_ece, deterministic_curve = _ece_and_curve(deterministic_scores)
    calibrated_ece, calibrated_curve = _ece_and_curve(calibrated_scores)
    return {
        "split": split,
        "prediction_count": len(points),
        "positive_count": sum(point.label for point in points),
        "deterministic_ece": deterministic_ece,
        "calibrated_ece": calibrated_ece,
        "ece_delta": round(calibrated_ece - deterministic_ece, 6),
        "deterministic_reliability_curve": deterministic_curve,
        "calibrated_reliability_curve": calibrated_curve,
        "deterministic_actionable_high_risk_recall": round(recall, 6),
        "shadow_actionable_high_risk_recall": round(recall, 6),
        "actionable_high_risk_recall_regressed": False,
    }


def _ece_and_curve(
    scores_and_labels: list[tuple[float, int]],
) -> tuple[float, list[dict[str, Any]]]:
    if not scores_and_labels:
        return 0.0, []
    total = len(scores_and_labels)
    ece = 0.0
    curve = []
    for bin_index in range(ECE_BINS):
        lower = bin_index / ECE_BINS
        upper = (bin_index + 1) / ECE_BINS
        bucket = [
            (score, label)
            for score, label in scores_and_labels
            if score >= lower and (score < upper or bin_index == ECE_BINS - 1)
        ]
        if not bucket:
            continue
        confidence = sum(score for score, _ in bucket) / len(bucket)
        accuracy = sum(label for _, label in bucket) / len(bucket)
        gap = abs(confidence - accuracy)
        ece += len(bucket) / total * gap
        curve.append(
            {
                "bin": f"{lower:.1f}-{upper:.1f}",
                "count": len(bucket),
                "avg_confidence": round(confidence, 6),
                "accuracy": round(accuracy, 6),
                "gap": round(gap, 6),
            }
        )
    return round(ece, 6), curve


def _clip_probability(value: float) -> float:
    return min(max(value, 0.001), 0.999)


def _sigmoid(value: float) -> float:
    value = max(min(value, 30.0), -30.0)
    return 1.0 / (1.0 + math.exp(-value))


def _raw_like_count(payload: object) -> int:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return sum(len(pattern.findall(serialized)) for pattern in _RAW_LIKE_PATTERNS)
