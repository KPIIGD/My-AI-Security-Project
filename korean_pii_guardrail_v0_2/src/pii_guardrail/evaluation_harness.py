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
- ``miss`` — gold span has no overlapping prediction → FN.
- predicted span with no gold overlap → FP (per entity type).

high_risk_recall is computed over P0 + P1 gold labels only.
"""

from __future__ import annotations

import datetime
import json
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from .enums import EntityType, RiskLevel
from .schema import GuardrailRequest, GuardrailResponse, PublicPIISpan


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
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        raw = json.loads(line)
        labels = tuple(
            EvaluationLabel(
                start=int(label["start"]),
                end=int(label["end"]),
                entity_type=EntityType(label["entity_type"]),
                risk_level=RiskLevel(label["risk_level"]),
                suffix=label.get("suffix"),
            )
            for label in raw.get("labels", [])
        )
        cases.append(
            EvaluationCase(
                id=raw["id"],
                text=raw["text"],
                labels=labels,
                expected_masked_text=raw.get("expected_masked_text"),
                tags=tuple(raw.get("tags", [])),
            )
        )
    return cases


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
    raw_pii_logging_count: int = 0  # invariant — pipeline forces this to zero
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
            "raw_pii_logging_count": self.raw_pii_logging_count,
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
            # Surplus predictions with no overlapping gold span are FPs.
            if not self._overlaps_any_expected(prediction, case.labels):
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

    @staticmethod
    def _overlaps_any_expected(
        prediction: PublicPIISpan, labels: tuple[EvaluationLabel, ...]
    ) -> bool:
        for label in labels:
            if not (prediction.end <= label.start or prediction.start >= label.end):
                return True
        return False

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

        spans_detected = sum(
            len([m for m in case.matches if m.actual is not None])
            for case in case_results
        )
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
        masked_exact = sum(1 for case in case_results if case.masked_text_exact_match)
        masked_match_rate = (
            masked_exact / len(case_results) if case_results else 0.0
        )
        blocked = sum(1 for case in case_results if case.blocked)

        return EvaluationReport(
            dataset_id=dataset_id,
            records_processed=len(cases),
            blocked_count=blocked,
            spans_detected=spans_detected,
            spans_masked=spans_masked,
            per_entity=per_entity,
            masked_text_exact_match_rate=masked_match_rate,
            high_risk_recall=high_risk_recall,
            case_results=tuple(case_results),
        )


__all__ = [
    "CaseResult",
    "EntityMetrics",
    "EvaluationCase",
    "EvaluationLabel",
    "EvaluationReport",
    "EvaluationRunner",
    "SpanMatch",
    "load_jsonl_cases",
]
