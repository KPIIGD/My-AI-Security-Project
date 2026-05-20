"""M10 evaluation harness for Korean PII Guardrail v0.2.

Implements ``docs/08_EVALUATION_PLAN.md`` for the internal gold sets
(``hard_cases_v0.jsonl`` and synthetic fixtures). External evaluation sets
(KLUE-NER test + KoJailFuzz unseen 6종) are intentionally NOT wired up
here; spec policy reserves them for a single W6 run to prevent test set
contamination during iterative development.

Pipeline:

    EvaluationCase list  ─►  GuardrailPipeline.process()
                              │
                              ▼
                          CaseResult (matches + masked_text)
                              │
                              ▼
                    EvaluationRunner.aggregate()
                              │
                              ▼
                    EvaluationReport (per-entity + overall)
                              │
                              ▼
                    residual_risk_report() ── dict for §9 §10 audit

Span match rules:

- ``exact`` — predicted span has identical ``(start, end, entity_type)``.
- ``partial`` — same ``entity_type`` and overlap ≥ 50% of the longer
  side. Counted as TP for entity recall but not for boundary accuracy.
- ``miss`` — gold span has no same-entity prediction → FN.
- unused predictions, including wrong-type overlaps and surplus overlaps,
  → FP (per predicted entity type).

high_risk_recall is computed over P0 + P1 gold labels only.
"""

from __future__ import annotations

import datetime
import json
import re
import time
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from .enums import Action, EntityType, OutputTarget, RiskLevel, Source
from .preprocess import preprocess_text
from .schema import (
    GuardrailRequest,
    GuardrailResponse,
    InvalidOffsetError,
    PIISpan,
    PublicPIISpan,
    ResponseMetrics,
)


if TYPE_CHECKING:
    from .pipeline import GuardrailPipeline


# ============================================================
# Case + label dataclasses
# ============================================================


@dataclass(frozen=True)
class EvaluationLabel:
    """Gold span label for a single PII occurrence."""

    start: int
    end: int
    entity_type: EntityType
    risk_level: RiskLevel
    suffix: str | None = None

    @property
    def length(self) -> int:
        return self.end - self.start


@dataclass(frozen=True)
class EvaluationCase:
    """A single labeled input from ``hard_cases_v0.jsonl`` or synthetic."""

    id: str
    text: str
    labels: tuple[EvaluationLabel, ...]
    expected_masked_text: str | None = None
    tags: tuple[str, ...] = ()


def load_jsonl_cases(path: Path) -> list[EvaluationCase]:
    """Load a JSONL gold set conforming to docs/08 §4 schema."""
    cases: list[EvaluationCase] = []
    for line_number, line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = line.strip()
        if not line:
            continue
        raw = json.loads(line)
        case_id = str(raw["id"])
        text = str(raw["text"])
        labels: list[EvaluationLabel] = []
        for label_index, label in enumerate(raw.get("labels", [])):
            start = int(label["start"])
            end = int(label["end"])
            _validate_gold_offset(
                case_id=case_id,
                line_number=line_number,
                label_index=label_index,
                start=start,
                end=end,
                text_length=len(text),
            )
            labels.append(
                EvaluationLabel(
                    start=start,
                    end=end,
                    entity_type=EntityType(label["entity_type"]),
                    risk_level=RiskLevel(label["risk_level"]),
                    suffix=label.get("suffix"),
                )
            )
        cases.append(
            EvaluationCase(
                id=case_id,
                text=text,
                labels=tuple(labels),
                expected_masked_text=raw.get("expected_masked_text"),
                tags=tuple(raw.get("tags", [])),
            )
        )
    return cases


def _validate_gold_offset(
    *,
    case_id: str,
    line_number: int,
    label_index: int,
    start: int,
    end: int,
    text_length: int,
) -> None:
    """Reject malformed gold labels without echoing source text."""
    if start < 0 or end > text_length or start >= end:
        raise ValueError(
            "Invalid gold label offset "
            f"case_id={case_id} line={line_number} label_index={label_index} "
            f"start={start} end={end} text_length={text_length}"
        )


# ============================================================
# Per-case match + per-entity aggregation
# ============================================================


@dataclass(frozen=True)
class SpanMatch:
    """One TP/FP/FN row for the aggregator."""

    case_id: str
    expected: EvaluationLabel | None
    actual: PublicPIISpan | None
    match_type: str  # "exact" | "partial" | "miss" | "spurious"


@dataclass(frozen=True)
class CaseResult:
    """Per-case detection + masking outcome."""

    case_id: str
    matches: tuple[SpanMatch, ...]
    masked_text: str | None
    expected_masked_text: str | None
    blocked: bool
    audit_event_count: int
    prediction_count: int = 0
    raw_pii_logging_count: int = 0
    latency_ms: float = 0.0
    tags: tuple[str, ...] = ()

    @property
    def masked_text_exact_match(self) -> bool:
        if self.expected_masked_text is None:
            return False
        return self.masked_text == self.expected_masked_text


@dataclass(frozen=True)
class EntityMetrics:
    """Precision / recall / F1 for one entity type."""

    entity_type: str
    tp_exact: int
    tp_partial: int
    fp: int
    fn: int

    @property
    def tp(self) -> int:
        return self.tp_exact + self.tp_partial

    @property
    def precision(self) -> float:
        denom = self.tp + self.fp
        return self.tp / denom if denom else 0.0

    @property
    def recall(self) -> float:
        denom = self.tp + self.fn
        return self.tp / denom if denom else 0.0

    @property
    def f1(self) -> float:
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) else 0.0

    @property
    def boundary_accuracy(self) -> float:
        """Fraction of true positives where boundary matched exactly."""
        if self.tp == 0:
            return 0.0
        return self.tp_exact / self.tp

    def to_dict(self) -> dict[str, object]:
        return {
            "entity_type": self.entity_type,
            "tp_exact": self.tp_exact,
            "tp_partial": self.tp_partial,
            "fp": self.fp,
            "fn": self.fn,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1": round(self.f1, 4),
            "boundary_accuracy": round(self.boundary_accuracy, 4),
        }


@dataclass(frozen=True)
class EvaluationReport:
    """Aggregated metrics across a dataset run."""

    dataset_id: str
    records_processed: int
    blocked_count: int
    spans_detected: int
    spans_masked: int
    per_entity: tuple[EntityMetrics, ...]
    masked_text_exact_match_rate: float
    high_risk_recall: float
    masked_text_evaluable_count: int = 0
    raw_pii_logging_count: int = 0
    invalid_offset_count: int = 0
    deterministic_latency_ms: dict[str, float] = field(default_factory=dict)
    generated_at: str = field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat()
    )
    case_results: tuple[CaseResult, ...] = ()

    @property
    def overall_metrics(self) -> EntityMetrics:
        tp_exact = sum(m.tp_exact for m in self.per_entity)
        tp_partial = sum(m.tp_partial for m in self.per_entity)
        fp = sum(m.fp for m in self.per_entity)
        fn = sum(m.fn for m in self.per_entity)
        return EntityMetrics(
            entity_type="__overall__",
            tp_exact=tp_exact,
            tp_partial=tp_partial,
            fp=fp,
            fn=fn,
        )

    def residual_risk_report(
        self,
        *,
        purpose_id: str,
        policy_profile: str = "strict",
        version: str = "v0.2-single-turn",
    ) -> dict[str, object]:
        """Render the spec §9 PseudonymizationResultReport shape.

        ``residual_risk_notes`` aggregates miss-type rows by entity type so
        the operator can see which PII families still slip through. The
        underlying ``case_results`` are not embedded — that would dump
        raw text into the report and violate §5.1.
        """
        overall = self.overall_metrics
        miss_summary: dict[str, int] = {}
        spurious_summary: dict[str, int] = {}
        for case in self.case_results:
            for match in case.matches:
                if match.match_type == "miss" and match.expected is not None:
                    miss_summary[match.expected.entity_type.value] = (
                        miss_summary.get(match.expected.entity_type.value, 0) + 1
                    )
                elif match.match_type == "spurious" and match.actual is not None:
                    spurious_summary[match.actual.entity_type.value] = (
                        spurious_summary.get(match.actual.entity_type.value, 0) + 1
                    )

        return {
            "report_type": "PseudonymizationResultReport",
            "version": version,
            "purpose_id": purpose_id,
            "policy_profile": policy_profile,
            "dataset_id": self.dataset_id,
            "records_processed": self.records_processed,
            "blocked_count": self.blocked_count,
            "spans_detected": self.spans_detected,
            "spans_masked": self.spans_masked,
            "high_risk_recall": round(self.high_risk_recall, 4),
            "boundary_accuracy": round(overall.boundary_accuracy, 4),
            "overall_precision": round(overall.precision, 4),
            "overall_recall": round(overall.recall, 4),
            "overall_f1": round(overall.f1, 4),
            "masked_text_exact_match_rate": round(self.masked_text_exact_match_rate, 4),
            "masked_text_evaluable_count": self.masked_text_evaluable_count,
            "raw_pii_logging_count": self.raw_pii_logging_count,
            "invalid_offset_count": self.invalid_offset_count,
            "deterministic_latency_ms": {
                key: round(value, 4)
                for key, value in sorted(self.deterministic_latency_ms.items())
            },
            "real_ner_latency_ms": {
                "status": "skipped",
                "reason_code": "gate.real_ner_latency.unavailable",
            },
            "residual_risk_notes": [
                {"entity_type": et, "miss_count": count}
                for et, count in sorted(miss_summary.items())
            ],
            "spurious_detections": [
                {"entity_type": et, "fp_count": count}
                for et, count in sorted(spurious_summary.items())
            ],
            "generated_at": self.generated_at,
        }

    def to_safe_dict(
        self,
        *,
        purpose_id: str,
        policy_profile: str = "strict",
        version: str = "v0.2-single-turn",
    ) -> dict[str, object]:
        """Render a raw-text-free JSON payload for CLI reports."""
        payload = self.residual_risk_report(
            purpose_id=purpose_id,
            policy_profile=policy_profile,
            version=version,
        )
        payload["per_entity"] = [metrics.to_dict() for metrics in self.per_entity]
        payload["overall"] = self.overall_metrics.to_dict()
        payload["release_gate"] = build_release_gate_report(self).to_dict()
        return payload


# ============================================================
# M10-3 release gate core
# ============================================================


_STRUCTURED_HIGH_RISK_ENTITIES = frozenset(
    {
        EntityType.RRN,
        EntityType.FRN,
        EntityType.PASSPORT,
        EntityType.DRIVER_LICENSE,
        EntityType.PHONE_MOBILE,
        EntityType.PHONE_LANDLINE,
        EntityType.EMAIL,
        EntityType.CREDIT_CARD,
        EntityType.BANK_ACCOUNT,
        EntityType.BUSINESS_REG_NO,
        EntityType.CUSTOMER_ID,
        EntityType.EMPLOYEE_ID,
        EntityType.STUDENT_ID,
        EntityType.MEDICAL_RECORD_NO,
        EntityType.API_KEY_SECRET,
    }
)
_PHONE_EMAIL_ENTITIES = frozenset(
    {EntityType.PHONE_MOBILE, EntityType.PHONE_LANDLINE, EntityType.EMAIL}
)
_AMBIGUITY_TAGS = frozenset({"hard_negative", "ambiguous_name", "weather_context"})


@dataclass(frozen=True)
class ReleaseGateCheck:
    """One raw-text-free release gate row."""

    name: str
    actual_value: float | int | str | None
    threshold: float | int | str | None
    status: str
    reason_code: str

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "actual_value": self.actual_value,
            "threshold": self.threshold,
            "status": self.status,
            "reason_code": self.reason_code,
        }


@dataclass(frozen=True)
class ReleaseGateReport:
    """Minimal M10-3 release gate result."""

    overall_status: str
    checks: tuple[ReleaseGateCheck, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "report_type": "ReleaseGateReport",
            "version": "v0.2-single-turn",
            "scope": "M10-3 core release gate",
            "overall_status": self.overall_status,
            "checks": [check.to_dict() for check in self.checks],
        }


def build_release_gate_report(report: EvaluationReport) -> ReleaseGateReport:
    """Build the currently computable release gate checks.

    The output contains only metrics and reason codes. It never embeds case
    text, span text, or reversible mappings.
    """
    checks = (
        _threshold_check(
            "high_risk_structured_recall",
            _recall_for_expected(
                report,
                lambda label: label.risk_level in {RiskLevel.P0, RiskLevel.P1}
                and label.entity_type in _STRUCTURED_HIGH_RISK_ENTITIES,
            ),
            0.99,
            ">=",
            "gate.high_risk_structured_recall",
        ),
        _threshold_check(
            "phone_email_recall",
            _recall_for_expected(
                report,
                lambda label: label.entity_type in _PHONE_EMAIL_ENTITIES,
            ),
            0.98,
            ">=",
            "gate.phone_email_recall",
        ),
        _threshold_check(
            "josa_boundary_accuracy",
            _josa_boundary_accuracy(report),
            0.95,
            ">=",
            "gate.josa_boundary_accuracy",
        ),
        ReleaseGateCheck(
            name="exact_span_match_rate",
            actual_value=_exact_span_match_rate(report),
            threshold="baseline_improvement_required",
            status="skipped",
            reason_code="gate.exact_span.baseline_unavailable",
        ),
        _threshold_check(
            "name_ambiguity_fp_rate",
            _name_ambiguity_fp_rate(report),
            0.0,
            "<=",
            "gate.name_ambiguity_fp_rate",
        ),
        _threshold_check(
            "raw_pii_logging_count",
            report.raw_pii_logging_count,
            0,
            "==",
            "gate.raw_pii_logging_count",
        ),
        _threshold_check(
            "invalid_offset_count",
            report.invalid_offset_count,
            0,
            "==",
            "gate.invalid_offset_count",
        ),
        _threshold_check(
            "deterministic_latency_p95_ms",
            report.deterministic_latency_ms.get("p95"),
            100.0,
            "<=",
            "gate.deterministic_latency_p95_ms",
        ),
        ReleaseGateCheck(
            name="real_ner_latency_ms",
            actual_value=None,
            threshold="measured_separately_when_real_ner_available",
            status="skipped",
            reason_code="gate.real_ner_latency.unavailable",
        ),
    )
    failing = any(check.status == "fail" for check in checks)
    overall_status = "fail" if failing else "pass"
    return ReleaseGateReport(overall_status=overall_status, checks=checks)


def _threshold_check(
    name: str,
    actual: float | int | None,
    threshold: float | int,
    comparator: str,
    reason_prefix: str,
) -> ReleaseGateCheck:
    if actual is None:
        return ReleaseGateCheck(
            name=name,
            actual_value=None,
            threshold=f"{comparator} {threshold}",
            status="skipped",
            reason_code=f"{reason_prefix}.not_evaluable",
        )
    if comparator == ">=":
        passed = actual >= threshold
    elif comparator == "<=":
        passed = actual <= threshold
    elif comparator == "==":
        passed = actual == threshold
    else:
        raise ValueError("Unsupported release gate comparator")
    return ReleaseGateCheck(
        name=name,
        actual_value=round(actual, 4) if isinstance(actual, float) else actual,
        threshold=f"{comparator} {threshold}",
        status="pass" if passed else "fail",
        reason_code=f"{reason_prefix}.{'pass' if passed else 'fail'}",
    )


def _recall_for_expected(
    report: EvaluationReport,
    predicate,
) -> float | None:
    total = 0
    matched = 0
    for result in report.case_results:
        for match in result.matches:
            if match.expected is None or not predicate(match.expected):
                continue
            total += 1
            if match.match_type in {"exact", "partial"}:
                matched += 1
    if total == 0:
        return None
    return matched / total


def _josa_boundary_accuracy(report: EvaluationReport) -> float | None:
    total = 0
    exact = 0
    for result in report.case_results:
        for match in result.matches:
            if match.expected is None or not match.expected.suffix:
                continue
            total += 1
            if match.match_type == "exact":
                exact += 1
    if total == 0:
        return None
    return exact / total


def _exact_span_match_rate(report: EvaluationReport) -> float | None:
    total = 0
    exact = 0
    for result in report.case_results:
        for match in result.matches:
            if match.expected is None:
                continue
            total += 1
            if match.match_type == "exact":
                exact += 1
    if total == 0:
        return None
    return exact / total


def _name_ambiguity_fp_rate(report: EvaluationReport) -> float | None:
    eligible_cases = [
        result for result in report.case_results if set(result.tags) & _AMBIGUITY_TAGS
    ]
    if not eligible_cases:
        return None
    fp_count = 0
    for result in eligible_cases:
        for match in result.matches:
            if (
                match.match_type == "spurious"
                and match.actual is not None
                and match.actual.entity_type is EntityType.PERSON_NAME
            ):
                fp_count += 1
    return fp_count / len(eligible_cases)


def _latency_percentiles(values: Iterable[float]) -> dict[str, float]:
    sorted_values = sorted(value for value in values if value >= 0.0)
    if not sorted_values:
        return {"p50": 0.0, "p95": 0.0, "p99": 0.0}
    return {
        "p50": _percentile(sorted_values, 0.50),
        "p95": _percentile(sorted_values, 0.95),
        "p99": _percentile(sorted_values, 0.99),
    }


def _percentile(sorted_values: list[float], percentile: float) -> float:
    if len(sorted_values) == 1:
        return sorted_values[0]
    rank = percentile * (len(sorted_values) - 1)
    lower = int(rank)
    upper = min(lower + 1, len(sorted_values) - 1)
    weight = rank - lower
    return sorted_values[lower] * (1.0 - weight) + sorted_values[upper] * weight


# ============================================================
# M10-2 cumulative ablation stages
# ============================================================


@dataclass(frozen=True)
class AblationStageSpec:
    """One cumulative M10-2 ablation stage."""

    name: str
    components: tuple[str, ...]
    include_regex_patterns: bool = False
    include_validated_regex: bool = False
    include_dictionary: bool = False
    include_boundary: bool = False
    include_mock_ner: bool = False
    include_context: bool = False
    status: str = "supported"
    skip_reason: str | None = None


@dataclass(frozen=True)
class AblationStageResult:
    """Raw-text-free summary for one ablation stage."""

    stage_name: str
    components: tuple[str, ...]
    status: str
    report: EvaluationReport | None = None
    invalid_offset_count: int = 0
    skip_reason: str | None = None

    def to_safe_dict(self) -> dict[str, object]:
        empty_overall = EntityMetrics(
            entity_type="__overall__",
            tp_exact=0,
            tp_partial=0,
            fp=0,
            fn=0,
        )
        per_entity = [m.to_dict() for m in self.report.per_entity] if self.report else []
        overall = self.report.overall_metrics if self.report else empty_overall
        payload: dict[str, object] = {
            "stage_name": self.stage_name,
            "components": list(self.components),
            "status": self.status,
            "invalid_offset_count": self.invalid_offset_count,
            "records_processed": self.report.records_processed if self.report else 0,
            "spans_detected": self.report.spans_detected if self.report else 0,
            "raw_pii_logging_count": self.report.raw_pii_logging_count if self.report else 0,
            "per_entity": per_entity,
            "overall": overall.to_dict(),
        }
        if self.skip_reason is not None:
            payload["skip_reason"] = self.skip_reason
        return payload


@dataclass(frozen=True)
class AblationReport:
    """Raw-text-free report for cumulative M10-2 stages."""

    dataset_id: str
    stages: tuple[AblationStageResult, ...]
    generated_at: str = field(
        default_factory=lambda: datetime.datetime.now(datetime.UTC).isoformat()
    )

    def to_safe_dict(self) -> dict[str, object]:
        return {
            "report_type": "AblationEvaluationReport",
            "version": "v0.2-single-turn",
            "scope": "M10-2 cumulative stage evaluation",
            "dataset_id": self.dataset_id,
            "generated_at": self.generated_at,
            "stages": [stage.to_safe_dict() for stage in self.stages],
        }


def m10_2_ablation_stage_specs() -> tuple[AblationStageSpec, ...]:
    """Return the small M10-2 cumulative stage set.

    E2 is included as a skipped marker only. Real NER activation and latency
    evaluation remain outside this PR's scope.
    """
    return (
        AblationStageSpec(
            name="A",
            components=("regex_patterns",),
            include_regex_patterns=True,
        ),
        AblationStageSpec(
            name="B",
            components=("regex_patterns", "validators"),
            include_validated_regex=True,
        ),
        AblationStageSpec(
            name="C",
            components=("regex_patterns", "validators", "dictionary"),
            include_validated_regex=True,
            include_dictionary=True,
        ),
        AblationStageSpec(
            name="D",
            components=("regex_patterns", "validators", "dictionary", "korean_boundary"),
            include_validated_regex=True,
            include_dictionary=True,
            include_boundary=True,
        ),
        AblationStageSpec(
            name="E1",
            components=(
                "regex_patterns",
                "validators",
                "dictionary",
                "korean_boundary",
                "mock_ner",
            ),
            include_validated_regex=True,
            include_dictionary=True,
            include_boundary=True,
            include_mock_ner=True,
        ),
        AblationStageSpec(
            name="E2",
            components=(
                "regex_patterns",
                "validators",
                "dictionary",
                "korean_boundary",
                "real_v3_ner",
            ),
            status="skipped",
            skip_reason="real NER v3 is not connected in M10-2",
        ),
        AblationStageSpec(
            name="F",
            components=(
                "regex_patterns",
                "validators",
                "dictionary",
                "korean_boundary",
                "mock_ner",
                "context_scorer",
            ),
            include_validated_regex=True,
            include_dictionary=True,
            include_boundary=True,
            include_mock_ner=True,
            include_context=True,
        ),
    )


class AblationRunner:
    """Run cumulative M10-2 stages without invoking full release gates."""

    def __init__(
        self,
        pipeline: "GuardrailPipeline",
        *,
        partial_overlap_min: float = 0.5,
    ) -> None:
        self._pipeline = pipeline
        self._partial_overlap_min = partial_overlap_min

    def evaluate(
        self,
        cases: Iterable[EvaluationCase],
        *,
        dataset_id: str = "hard_cases_v0",
    ) -> AblationReport:
        case_list = list(cases)
        results: list[AblationStageResult] = []
        for spec in m10_2_ablation_stage_specs():
            if spec.status == "skipped":
                results.append(
                    AblationStageResult(
                        stage_name=spec.name,
                        components=spec.components,
                        status="skipped",
                        skip_reason=spec.skip_reason,
                    )
                )
                continue

            stage_pipeline = _AblationStagePipeline(self._pipeline.components, spec)
            report = EvaluationRunner(
                stage_pipeline,
                partial_overlap_min=self._partial_overlap_min,
            ).evaluate(case_list, dataset_id=f"{dataset_id}_{spec.name}")
            results.append(
                AblationStageResult(
                    stage_name=spec.name,
                    components=spec.components,
                    status="ok",
                    report=report,
                    invalid_offset_count=stage_pipeline.invalid_offset_count,
                )
            )
        return AblationReport(dataset_id=dataset_id, stages=tuple(results))


@dataclass(frozen=True)
class _RegexPatternRule:
    entity_type: EntityType
    pattern: re.Pattern[str]
    score_key: str
    detector_id: str


_REGEX_PATTERN_ONLY_RULES = (
    _RegexPatternRule(EntityType.RRN, re.compile(r"(?<!\d)\d{6}\s*-?\s*\d{7}(?!\d)"), "RRN", "eval.regex_only.rrn"),
    _RegexPatternRule(EntityType.FRN, re.compile(r"(?<!\d)\d{6}\s*-?\s*\d{7}(?!\d)"), "FRN", "eval.regex_only.frn"),
    _RegexPatternRule(EntityType.PHONE_MOBILE, re.compile(r"(?<!\d)0\d{1,2}[\s-]?\d{3,4}[\s-]?\d{4}(?!\d)"), "PHONE_MOBILE", "eval.regex_only.phone"),
    _RegexPatternRule(EntityType.EMAIL, re.compile(r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9.!#$%&'*+/=?^_`{|}~-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), "EMAIL", "eval.regex_only.email"),
    _RegexPatternRule(EntityType.IP_ADDRESS, re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])"), "IP_ADDRESS_PUBLIC", "eval.regex_only.ipv4"),
    _RegexPatternRule(EntityType.MAC_ADDRESS, re.compile(r"(?<![0-9A-Fa-f])(?:[0-9A-Fa-f]{2}[:-]){5}[0-9A-Fa-f]{2}(?![0-9A-Fa-f])"), "MAC_ADDRESS", "eval.regex_only.mac"),
    _RegexPatternRule(EntityType.CREDIT_CARD, re.compile(r"(?<!\d)(?:\d[\s-]?){13,19}(?!\d)"), "CREDIT_CARD_PATTERN_ONLY", "eval.regex_only.credit_card"),
    _RegexPatternRule(EntityType.BUSINESS_REG_NO, re.compile(r"(?<!\d)\d{3}-?\d{2}-?\d{5}(?!\d)"), "BUSINESS_REG_NO_PATTERN_ONLY", "eval.regex_only.business_reg_no"),
    _RegexPatternRule(EntityType.BANK_ACCOUNT, re.compile(r"(?<!\d)\d{2,6}(?:[- ]\d{2,6}){1,4}(?!\d)"), "BANK_ACCOUNT_PATTERN_ONLY", "eval.regex_only.bank_account"),
    _RegexPatternRule(EntityType.API_KEY_SECRET, re.compile(r"(?<![A-Za-z0-9_=-])(?:sk-[A-Za-z0-9_=-]{16,}|gh[po]_[A-Za-z0-9]{16,}|xox[bp]-[A-Za-z0-9-]{16,}|AKIA[0-9A-Z]{16})(?![A-Za-z0-9_=-])"), "API_KEY_SECRET", "eval.regex_only.secret"),
)


class _AblationStagePipeline:
    """Small process-compatible pipeline for one cumulative stage."""

    def __init__(self, components, spec: AblationStageSpec) -> None:
        self._components = components
        self._spec = spec
        first_detector = components.regex_detectors[0]
        self._scores = getattr(first_detector, "scores", {})
        self._risk_levels = getattr(first_detector, "risk_levels", {})
        self.invalid_offset_count = 0

    def process(self, request: GuardrailRequest) -> GuardrailResponse:
        t0 = time.perf_counter()
        preprocessed = preprocess_text(request.text)
        spans: list[PIISpan] = []

        if self._spec.include_regex_patterns:
            spans.extend(self._detect_regex_patterns(request.text))
        if self._spec.include_validated_regex:
            for detector in self._components.regex_detectors:
                spans.extend(detector.detect(preprocessed, request))
        if self._spec.include_dictionary:
            spans.extend(self._components.dictionary_detector.detect(preprocessed, request))
        if self._spec.include_mock_ner and self._components.ner_detector is not None:
            spans.extend(
                self._components.ner_detector.detect(
                    raw_text=request.text,
                    preprocessed=preprocessed,
                    request=request,
                )
            )
        if self._spec.include_boundary:
            spans = [
                self._components.boundary_corrector.correct(span, preprocessed)
                for span in spans
            ]
        if self._spec.include_context:
            spans = self._components.context_scorer.score(spans, preprocessed)

        spans = self._drop_invalid_offsets(spans, request.text)
        public_spans = tuple(span.to_public() for span in spans)
        latency_ms = (time.perf_counter() - t0) * 1000.0
        return GuardrailResponse(
            request_id=request.effective_request_id,
            blocked=False,
            masked_text=None,
            spans=public_spans,
            audit_events=(),
            metrics=ResponseMetrics(
                latency_ms=latency_ms,
                detected_span_count=len(public_spans),
                masked_span_count=0,
            ),
            policy_profile=request.policy_profile,
            output_target=OutputTarget(request.output_target),
            raw_value_logged=False,
        )

    def _detect_regex_patterns(self, raw_text: str) -> list[PIISpan]:
        spans: list[PIISpan] = []
        for rule in _REGEX_PATTERN_ONLY_RULES:
            for match in rule.pattern.finditer(raw_text):
                text = raw_text[match.start() : match.end()]
                spans.append(
                    PIISpan(
                        start=match.start(),
                        end=match.end(),
                        text=text,
                        entity_type=rule.entity_type,
                        score=float(self._scores.get(rule.score_key, 0.5)),
                        sources=(Source.REGEX.value,),
                        risk_level=self._risk_levels.get(rule.entity_type, RiskLevel.P1),
                        action=Action.CANDIDATE,
                        reason_codes=("eval.regex_pattern_only",),
                        detector_ids=(rule.detector_id,),
                    )
                )
        return spans

    def _drop_invalid_offsets(self, spans: list[PIISpan], raw_text: str) -> list[PIISpan]:
        valid: list[PIISpan] = []
        for span in spans:
            try:
                span.validate_against(raw_text)
            except InvalidOffsetError:
                self.invalid_offset_count += 1
                continue
            valid.append(span)
        return valid


# ============================================================
# EvaluationRunner — orchestrate pipeline + match + aggregate
# ============================================================


class EvaluationRunner:
    """Run a pipeline over labeled cases and compute metrics.

    External evaluation policy:
        This class is *not* wired to external test sets (KLUE-NER test,
        KoJailFuzz unseen 6종). Spec §X reserves those for a single W6
        run; passing them through this runner before W6 contaminates the
        held-out signal. Callers running W6 should load those sets
        explicitly and acknowledge single-use in their commit message.
    """

    def __init__(
        self,
        pipeline: "GuardrailPipeline",
        *,
        partial_overlap_min: float = 0.5,
    ) -> None:
        if not 0.0 < partial_overlap_min <= 1.0:
            raise ValueError("partial_overlap_min must be in (0, 1]")
        self._pipeline = pipeline
        self._partial_threshold = partial_overlap_min

    def evaluate(
        self,
        cases: Iterable[EvaluationCase],
        *,
        dataset_id: str = "hard_cases_v0",
    ) -> EvaluationReport:
        case_list = list(cases)
        case_results: list[CaseResult] = []
        for case in case_list:
            request = GuardrailRequest(text=case.text, request_id=f"eval-{case.id}")
            response = self._pipeline.process(request)
            case_results.append(self._build_case_result(case, response))
        return self._aggregate(dataset_id, case_list, case_results)

    # ----- private -----

    def _build_case_result(
        self, case: EvaluationCase, response: GuardrailResponse
    ) -> CaseResult:
        matches = self._match_spans(case, response.spans)
        return CaseResult(
            case_id=case.id,
            matches=tuple(matches),
            masked_text=response.masked_text,
            expected_masked_text=case.expected_masked_text,
            blocked=response.blocked,
            audit_event_count=len(response.audit_events),
            prediction_count=len(response.spans),
            raw_pii_logging_count=self._raw_pii_logging_count(response),
            latency_ms=response.metrics.latency_ms,
            tags=case.tags,
        )

    def _match_spans(
        self,
        case: EvaluationCase,
        predictions: tuple[PublicPIISpan, ...],
    ) -> list[SpanMatch]:
        matches: list[SpanMatch] = []
        used_predictions: set[int] = set()

        for expected in case.labels:
            best_idx: int | None = None
            best_match_type: str = "miss"
            for idx, prediction in enumerate(predictions):
                if idx in used_predictions:
                    continue
                if prediction.entity_type is not expected.entity_type:
                    continue
                if expected.start == prediction.start and expected.end == prediction.end:
                    best_idx = idx
                    best_match_type = "exact"
                    break
                if self._overlap_ratio(expected, prediction) >= self._partial_threshold:
                    if best_match_type != "exact":
                        best_idx = idx
                        best_match_type = "partial"

            if best_idx is None:
                matches.append(
                    SpanMatch(
                        case_id=case.id,
                        expected=expected,
                        actual=None,
                        match_type="miss",
                    )
                )
            else:
                used_predictions.add(best_idx)
                matches.append(
                    SpanMatch(
                        case_id=case.id,
                        expected=expected,
                        actual=predictions[best_idx],
                        match_type=best_match_type,
                    )
                )

        for idx, prediction in enumerate(predictions):
            if idx in used_predictions:
                continue
            matches.append(
                SpanMatch(
                    case_id=case.id,
                    expected=None,
                    actual=prediction,
                    match_type="spurious",
                )
            )
        return matches

    @staticmethod
    def _overlap_ratio(expected: EvaluationLabel, prediction: PublicPIISpan) -> float:
        overlap = max(0, min(expected.end, prediction.end) - max(expected.start, prediction.start))
        if overlap == 0:
            return 0.0
        longest = max(expected.length, prediction.end - prediction.start)
        return overlap / longest if longest else 0.0

    def _aggregate(
        self,
        dataset_id: str,
        cases: list[EvaluationCase],
        case_results: list[CaseResult],
    ) -> EvaluationReport:
        counts: dict[str, dict[str, int]] = {}
        for case in case_results:
            for match in case.matches:
                entity_type = (
                    match.expected.entity_type.value
                    if match.expected is not None
                    else match.actual.entity_type.value  # type: ignore[union-attr]
                )
                row = counts.setdefault(
                    entity_type,
                    {"tp_exact": 0, "tp_partial": 0, "fp": 0, "fn": 0},
                )
                if match.match_type == "exact":
                    row["tp_exact"] += 1
                elif match.match_type == "partial":
                    row["tp_partial"] += 1
                elif match.match_type == "miss":
                    row["fn"] += 1
                elif match.match_type == "spurious":
                    row["fp"] += 1

        per_entity = tuple(
            EntityMetrics(
                entity_type=et,
                tp_exact=row["tp_exact"],
                tp_partial=row["tp_partial"],
                fp=row["fp"],
                fn=row["fn"],
            )
            for et, row in sorted(counts.items())
        )

        high_risk_tp = 0
        high_risk_fn = 0
        for case in case_results:
            for match in case.matches:
                if match.expected is None:
                    continue
                if match.expected.risk_level not in {RiskLevel.P0, RiskLevel.P1}:
                    continue
                if match.match_type == "miss":
                    high_risk_fn += 1
                else:
                    high_risk_tp += 1
        high_risk_recall = (
            high_risk_tp / (high_risk_tp + high_risk_fn)
            if (high_risk_tp + high_risk_fn)
            else 0.0
        )

        spans_detected = sum(case.prediction_count for case in case_results)
        spans_masked = sum(
            len(
                [
                    m
                    for m in case.matches
                    if m.actual is not None
                    and m.actual.action.value in {"mask", "hash", "block"}
                ]
            )
            for case in case_results
        )
        masked_evaluable = [
            case for case in case_results if case.expected_masked_text is not None
        ]
        masked_exact = sum(1 for case in masked_evaluable if case.masked_text_exact_match)
        masked_match_rate = (
            masked_exact / len(masked_evaluable) if masked_evaluable else 0.0
        )
        blocked = sum(1 for case in case_results if case.blocked)
        raw_pii_logging_count = sum(case.raw_pii_logging_count for case in case_results)
        deterministic_latency_ms = _latency_percentiles(
            case.latency_ms for case in case_results
        )

        return EvaluationReport(
            dataset_id=dataset_id,
            records_processed=len(cases),
            blocked_count=blocked,
            spans_detected=spans_detected,
            spans_masked=spans_masked,
            per_entity=per_entity,
            masked_text_exact_match_rate=masked_match_rate,
            high_risk_recall=high_risk_recall,
            masked_text_evaluable_count=len(masked_evaluable),
            raw_pii_logging_count=raw_pii_logging_count,
            invalid_offset_count=0,
            deterministic_latency_ms=deterministic_latency_ms,
            case_results=tuple(case_results),
        )

    @staticmethod
    def _raw_pii_logging_count(response: GuardrailResponse) -> int:
        """Count raw-value leak flags without reading or serializing raw values."""
        count = 1 if response.raw_value_logged else 0
        count += sum(1 for span in response.spans if span.raw_value_logged)
        count += sum(1 for event in response.audit_events if event.raw_value_logged)
        return count


__all__ = [
    "AblationReport",
    "AblationRunner",
    "AblationStageResult",
    "AblationStageSpec",
    "CaseResult",
    "EntityMetrics",
    "EvaluationCase",
    "EvaluationLabel",
    "EvaluationReport",
    "EvaluationRunner",
    "SpanMatch",
    "load_jsonl_cases",
    "m10_2_ablation_stage_specs",
]
