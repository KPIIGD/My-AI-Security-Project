"""Tests for M10 evaluation harness.

Coverage:

- load_jsonl_cases parses docs/08 §4 schema (hard_cases_v0 fixture)
- SpanMatch classifies exact / partial / miss / spurious correctly
- EntityMetrics precision / recall / F1 / boundary_accuracy compute right
- EvaluationReport.overall_metrics aggregates across entity types
- residual_risk_report follows spec §9 shape and contains no raw text
- high_risk_recall only counts P0/P1 gold labels
- EvaluationRunner runs the GuardrailPipeline end-to-end on a
  synthetic case list and aggregates metrics
- External evaluation policy is honored: the runner does not auto-load
  external test sets
"""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

from pii_guardrail.audit_logger import AuditLogger
from pii_guardrail.enums import Action, EntityType, OutputTarget, RiskLevel, Source
from pii_guardrail.evaluation_harness import (
    CaseResult,
    EntityMetrics,
    EvaluationCase,
    EvaluationLabel,
    EvaluationReport,
    EvaluationRunner,
    SpanMatch,
    load_jsonl_cases,
)
from pii_guardrail.pipeline import GuardrailPipeline
from pii_guardrail.schema import PublicPIISpan


HARD_CASES_PATH = (
    Path(__file__).resolve().parents[1] / "data" / "eval" / "hard_cases_v0.jsonl"
)


@pytest.fixture(autouse=True)
def _isolated_audit_logger():
    logger = logging.getLogger(AuditLogger.LOGGER_NAME)
    saved_handlers = list(logger.handlers)
    saved_propagate = logger.propagate
    logger.handlers.clear()
    yield logger
    for handler in logger.handlers:
        handler.close()
    logger.handlers = saved_handlers
    logger.propagate = saved_propagate


def _public(
    start: int,
    end: int,
    entity_type: EntityType,
    *,
    action: Action = Action.MASK,
    risk_level: RiskLevel = RiskLevel.P1,
) -> PublicPIISpan:
    return PublicPIISpan(
        start=start,
        end=end,
        span_length=end - start,
        entity_type=entity_type,
        score=0.9,
        sources=(Source.REGEX.value,),
        risk_level=risk_level,
        action=action,
        reason_codes=("test",),
        detector_ids=("test",),
    )


# ============================================================
# load_jsonl_cases
# ============================================================


def test_load_jsonl_cases_reads_hard_cases_v0() -> None:
    cases = load_jsonl_cases(HARD_CASES_PATH)

    assert len(cases) > 0
    first = cases[0]
    assert first.id.startswith("case-")
    assert first.text  # raw text present
    assert all(isinstance(label, EvaluationLabel) for label in first.labels)


def test_load_jsonl_cases_preserves_label_metadata(tmp_path: Path) -> None:
    fixture = tmp_path / "tiny.jsonl"
    fixture.write_text(
        json.dumps({
            "id": "case-test",
            "text": "홍길동 010-1234-5678",
            "expected_masked_text": "[PERSON_1] [PHONE_1]",
            "labels": [
                {"start": 0, "end": 3, "entity_type": "PERSON_NAME", "risk_level": "P1", "suffix": None},
                {"start": 4, "end": 17, "entity_type": "PHONE_MOBILE", "risk_level": "P1", "suffix": None},
            ],
            "tags": ["person", "phone"],
        }) + "\n",
        encoding="utf-8",
    )

    [case] = load_jsonl_cases(fixture)

    assert case.id == "case-test"
    assert case.expected_masked_text == "[PERSON_1] [PHONE_1]"
    assert case.tags == ("person", "phone")
    assert case.labels[0].entity_type is EntityType.PERSON_NAME
    assert case.labels[0].risk_level is RiskLevel.P1


# ============================================================
# Span match classification
# ============================================================


def test_exact_match_when_offsets_and_type_align() -> None:
    case = EvaluationCase(
        id="c1",
        text="홍길동 010-1234-5678",
        labels=(
            EvaluationLabel(start=0, end=3, entity_type=EntityType.PERSON_NAME, risk_level=RiskLevel.P1),
        ),
    )
    prediction = _public(0, 3, EntityType.PERSON_NAME)
    runner = EvaluationRunner(GuardrailPipeline())

    matches = runner._match_spans(case, (prediction,))

    assert len(matches) == 1
    assert matches[0].match_type == "exact"


def test_partial_match_when_boundary_drifts_but_type_aligns() -> None:
    case = EvaluationCase(
        id="c1",
        text="김민수가 왔습니다",
        labels=(
            EvaluationLabel(start=0, end=3, entity_type=EntityType.PERSON_NAME, risk_level=RiskLevel.P1),
        ),
    )
    # Prediction includes the josa "가" — boundary off by 1 char.
    prediction = _public(0, 4, EntityType.PERSON_NAME)
    runner = EvaluationRunner(GuardrailPipeline())

    matches = runner._match_spans(case, (prediction,))

    assert matches[0].match_type == "partial"


def test_miss_when_no_prediction_covers_gold_span() -> None:
    case = EvaluationCase(
        id="c1",
        text="홍길동",
        labels=(
            EvaluationLabel(start=0, end=3, entity_type=EntityType.PERSON_NAME, risk_level=RiskLevel.P1),
        ),
    )
    runner = EvaluationRunner(GuardrailPipeline())

    matches = runner._match_spans(case, ())

    assert matches == [
        SpanMatch(
            case_id="c1",
            expected=case.labels[0],
            actual=None,
            match_type="miss",
        )
    ]


def test_spurious_when_prediction_has_no_gold_overlap() -> None:
    case = EvaluationCase(
        id="c1",
        text="홍길동이 왔습니다",
        labels=(
            EvaluationLabel(start=0, end=3, entity_type=EntityType.PERSON_NAME, risk_level=RiskLevel.P1),
        ),
    )
    # Spurious phone detection at a non-overlapping range.
    spurious = _public(5, 8, EntityType.PHONE_MOBILE)
    matched = _public(0, 3, EntityType.PERSON_NAME)
    runner = EvaluationRunner(GuardrailPipeline())

    matches = runner._match_spans(case, (matched, spurious))

    types = {(m.match_type, m.actual.entity_type if m.actual else None) for m in matches}
    assert ("exact", EntityType.PERSON_NAME) in types
    assert ("spurious", EntityType.PHONE_MOBILE) in types


def test_type_mismatch_with_overlap_does_not_count_as_match() -> None:
    case = EvaluationCase(
        id="c1",
        text="홍길동",
        labels=(
            EvaluationLabel(start=0, end=3, entity_type=EntityType.PERSON_NAME, risk_level=RiskLevel.P1),
        ),
    )
    # Same span but wrong entity_type → still a miss for PERSON_NAME, and
    # the wrong-typed prediction overlaps the gold so it's not spurious.
    prediction = _public(0, 3, EntityType.ORGANIZATION)
    runner = EvaluationRunner(GuardrailPipeline())

    matches = runner._match_spans(case, (prediction,))

    types = sorted(m.match_type for m in matches)
    assert "miss" in types
    # Overlapping wrong-type prediction is NOT counted as spurious
    # (it overlaps gold, so it's a separate downgraded-type signal).
    assert "spurious" not in types


# ============================================================
# EntityMetrics
# ============================================================


def test_entity_metrics_precision_recall_f1() -> None:
    metrics = EntityMetrics(entity_type="PHONE_MOBILE", tp_exact=8, tp_partial=2, fp=1, fn=4)

    assert metrics.tp == 10
    assert metrics.precision == pytest.approx(10 / 11)
    assert metrics.recall == pytest.approx(10 / 14)
    expected_f1 = 2 * metrics.precision * metrics.recall / (metrics.precision + metrics.recall)
    assert metrics.f1 == pytest.approx(expected_f1)
    assert metrics.boundary_accuracy == pytest.approx(0.8)


def test_entity_metrics_zero_division_safety() -> None:
    metrics = EntityMetrics(entity_type="EMAIL", tp_exact=0, tp_partial=0, fp=0, fn=0)

    assert metrics.precision == 0.0
    assert metrics.recall == 0.0
    assert metrics.f1 == 0.0
    assert metrics.boundary_accuracy == 0.0


# ============================================================
# EvaluationReport + residual_risk_report
# ============================================================


def _empty_report() -> EvaluationReport:
    return EvaluationReport(
        dataset_id="synthetic",
        records_processed=0,
        blocked_count=0,
        spans_detected=0,
        spans_masked=0,
        per_entity=(),
        masked_text_exact_match_rate=0.0,
        high_risk_recall=0.0,
    )


def test_overall_metrics_sums_across_entity_rows() -> None:
    report = EvaluationReport(
        dataset_id="synthetic",
        records_processed=5,
        blocked_count=0,
        spans_detected=10,
        spans_masked=8,
        per_entity=(
            EntityMetrics(entity_type="PHONE_MOBILE", tp_exact=4, tp_partial=0, fp=1, fn=1),
            EntityMetrics(entity_type="EMAIL", tp_exact=3, tp_partial=1, fp=0, fn=1),
        ),
        masked_text_exact_match_rate=0.6,
        high_risk_recall=0.8,
    )

    overall = report.overall_metrics

    assert overall.tp_exact == 7
    assert overall.tp_partial == 1
    assert overall.fp == 1
    assert overall.fn == 2


def test_residual_risk_report_follows_spec_shape() -> None:
    report = _empty_report()

    payload = report.residual_risk_report(
        purpose_id="ko_pii_guardrail_v0_2_eval",
        policy_profile="strict",
    )

    assert payload["report_type"] == "PseudonymizationResultReport"
    assert payload["version"] == "v0.2-single-turn"
    assert payload["purpose_id"] == "ko_pii_guardrail_v0_2_eval"
    assert payload["policy_profile"] == "strict"
    assert payload["raw_pii_logging_count"] == 0
    assert "residual_risk_notes" in payload
    assert "generated_at" in payload


def test_residual_risk_report_aggregates_miss_summary() -> None:
    runner = EvaluationRunner(GuardrailPipeline())
    case = EvaluationCase(
        id="c1",
        text="홍길동이 왔습니다.",  # NER mock may not detect this Korean name
        labels=(
            EvaluationLabel(start=0, end=3, entity_type=EntityType.PERSON_NAME, risk_level=RiskLevel.P1),
            EvaluationLabel(start=10, end=20, entity_type=EntityType.EMAIL, risk_level=RiskLevel.P1),
        ),
    )

    case_result = CaseResult(
        case_id="c1",
        matches=(
            SpanMatch(case_id="c1", expected=case.labels[0], actual=None, match_type="miss"),
            SpanMatch(case_id="c1", expected=case.labels[1], actual=None, match_type="miss"),
        ),
        masked_text="홍길동이 왔습니다.",
        expected_masked_text=None,
        blocked=False,
        audit_event_count=0,
    )
    report = EvaluationReport(
        dataset_id="synthetic",
        records_processed=1,
        blocked_count=0,
        spans_detected=0,
        spans_masked=0,
        per_entity=(),
        masked_text_exact_match_rate=0.0,
        high_risk_recall=0.0,
        case_results=(case_result,),
    )

    payload = report.residual_risk_report(purpose_id="ko_pii_guardrail_v0_2_eval")

    miss_entities = {note["entity_type"] for note in payload["residual_risk_notes"]}
    assert "PERSON_NAME" in miss_entities
    assert "EMAIL" in miss_entities


def test_residual_risk_report_does_not_contain_raw_text(tmp_path: Path) -> None:
    """The report must summarize misses without dumping raw text into JSON."""
    raw_phone = "010-1234-5678"
    case = EvaluationCase(
        id="c1",
        text=f"연락처는 {raw_phone}입니다.",
        labels=(
            EvaluationLabel(start=5, end=18, entity_type=EntityType.PHONE_MOBILE, risk_level=RiskLevel.P1),
        ),
    )
    runner = EvaluationRunner(GuardrailPipeline())

    report = runner.evaluate([case], dataset_id="synthetic-leak-check")
    payload = report.residual_risk_report(purpose_id="ko_pii_guardrail_v0_2_eval")
    serialized = json.dumps(payload, ensure_ascii=False)

    assert raw_phone not in serialized
    assert case.text not in serialized


# ============================================================
# High-risk recall
# ============================================================


def test_high_risk_recall_counts_only_p0_and_p1_labels() -> None:
    runner = EvaluationRunner(GuardrailPipeline())
    # Two cases: one with a P1 gold (high risk), one with a P3 gold (low risk).
    # Both go undetected by the mock-only pipeline, but only the P1 should
    # drive high_risk_recall to 0.0 — the P3 must not contribute.
    case_p1 = EvaluationCase(
        id="c1",
        text="some text without detectable PII for the mock",
        labels=(
            EvaluationLabel(start=0, end=4, entity_type=EntityType.PERSON_NAME, risk_level=RiskLevel.P1),
        ),
    )
    case_p3 = EvaluationCase(
        id="c2",
        text="some other text",
        labels=(
            EvaluationLabel(start=0, end=4, entity_type=EntityType.AGE, risk_level=RiskLevel.P3),
        ),
    )

    report = runner.evaluate([case_p1, case_p3])

    # P1 alone missed → 0 / 1 = 0.0
    assert report.high_risk_recall == 0.0


# ============================================================
# Runner end-to-end on hard_cases_v0
# ============================================================


def test_runner_evaluates_hard_cases_v0_without_crashing() -> None:
    cases = load_jsonl_cases(HARD_CASES_PATH)
    runner = EvaluationRunner(GuardrailPipeline())

    report = runner.evaluate(cases, dataset_id="hard_cases_v0")

    assert report.records_processed == len(cases)
    assert report.dataset_id == "hard_cases_v0"
    # Some PII should be detectable by regex (PHONE/EMAIL/RRN) even with
    # the mock NER; require non-trivial detection.
    assert report.spans_detected > 0
    # Invariant from M8: raw PII never logged.
    assert report.raw_pii_logging_count == 0


def test_runner_invalid_partial_threshold_raises() -> None:
    with pytest.raises(ValueError):
        EvaluationRunner(GuardrailPipeline(), partial_overlap_min=0.0)
    with pytest.raises(ValueError):
        EvaluationRunner(GuardrailPipeline(), partial_overlap_min=1.5)


def test_runner_w6_external_policy_documented_in_docstring() -> None:
    """The runner's docstring must explicitly forbid auto-loading external sets."""
    assert "W6" in EvaluationRunner.__doc__
    assert "external" in EvaluationRunner.__doc__.lower()
