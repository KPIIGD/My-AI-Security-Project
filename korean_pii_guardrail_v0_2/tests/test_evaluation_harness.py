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
import subprocess
import sys
from pathlib import Path

import pytest

from pii_guardrail.audit_logger import AuditLogger
from pii_guardrail.enums import Action, EntityType, OutputTarget, RiskLevel, Source
from pii_guardrail.evaluation_harness import (
    AblationRunner,
    CaseResult,
    EntityMetrics,
    EvaluationCase,
    EvaluationLabel,
    EvaluationReport,
    EvaluationRunner,
    SpanMatch,
    build_audit_safety_report,
    build_failure_analysis_rows,
    build_release_gate_report,
    count_report_raw_text_leaks,
    failure_analysis_jsonl,
    load_jsonl_cases,
)
from pii_guardrail.pipeline import GuardrailPipeline
from pii_guardrail.schema import (
    AuditEvent,
    GuardrailResponse,
    PublicPIISpan,
    ResponseMetrics,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
HARD_CASES_PATH = (
    PROJECT_ROOT / "data" / "eval" / "hard_cases_v0.jsonl"
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
    raw_value_logged: bool = False,
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
        raw_value_logged=raw_value_logged,
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


def test_load_jsonl_cases_rejects_invalid_gold_offsets_without_raw_text(tmp_path: Path) -> None:
    fixture = tmp_path / "bad-offset.jsonl"
    raw_text = "홍길동"
    fixture.write_text(
        json.dumps({
            "id": "case-bad-offset",
            "text": raw_text,
            "expected_masked_text": "[PERSON_1]",
            "labels": [
                {"start": 0, "end": 99, "entity_type": "PERSON_NAME", "risk_level": "P1"},
            ],
            "tags": [],
        }) + "\n",
        encoding="utf-8",
    )

    with pytest.raises(ValueError) as exc_info:
        load_jsonl_cases(fixture)

    message = str(exc_info.value)
    assert "case-bad-offset" in message
    assert "start=0" in message
    assert "end=99" in message
    assert raw_text not in message


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


def test_type_mismatch_with_overlap_counts_miss_and_spurious() -> None:
    case = EvaluationCase(
        id="c1",
        text="홍길동",
        labels=(
            EvaluationLabel(start=0, end=3, entity_type=EntityType.PERSON_NAME, risk_level=RiskLevel.P1),
        ),
    )
    # Same span but wrong entity_type: PERSON_NAME is missed and the
    # ORGANIZATION prediction must still count as a false positive.
    prediction = _public(0, 3, EntityType.ORGANIZATION)
    runner = EvaluationRunner(GuardrailPipeline())

    matches = runner._match_spans(case, (prediction,))

    types = {(m.match_type, m.actual.entity_type if m.actual else None) for m in matches}
    assert ("miss", None) in types
    assert ("spurious", EntityType.ORGANIZATION) in types


def test_surplus_overlapping_prediction_counts_as_spurious() -> None:
    case = EvaluationCase(
        id="c1",
        text="김민수가 왔습니다",
        labels=(
            EvaluationLabel(start=0, end=3, entity_type=EntityType.PERSON_NAME, risk_level=RiskLevel.P1),
        ),
    )
    exact = _public(0, 3, EntityType.PERSON_NAME)
    duplicate_overlap = _public(0, 4, EntityType.PERSON_NAME)
    runner = EvaluationRunner(GuardrailPipeline())

    matches = runner._match_spans(case, (exact, duplicate_overlap))

    assert [(m.match_type, m.actual.start if m.actual else None, m.actual.end if m.actual else None) for m in matches] == [
        ("exact", 0, 3),
        ("spurious", 0, 4),
    ]


def test_spans_detected_uses_actual_prediction_count_for_surplus_overlap() -> None:
    case = EvaluationCase(
        id="c1",
        text="김민수가 왔습니다",
        labels=(
            EvaluationLabel(start=0, end=3, entity_type=EntityType.PERSON_NAME, risk_level=RiskLevel.P1),
        ),
    )
    runner = EvaluationRunner(GuardrailPipeline())
    matches = runner._match_spans(
        case,
        (
            _public(0, 3, EntityType.PERSON_NAME),
            _public(0, 4, EntityType.PERSON_NAME),
        ),
    )
    report = runner._aggregate(
        "synthetic",
        [case],
        [
            CaseResult(
                case_id="c1",
                matches=tuple(matches),
                masked_text="[PERSON_1] 왔습니다",
                expected_masked_text="[PERSON_1] 왔습니다",
                blocked=False,
                audit_event_count=0,
                prediction_count=2,
            )
        ],
    )

    person = next(row for row in report.per_entity if row.entity_type == "PERSON_NAME")
    assert report.spans_detected == 2
    assert person.tp_exact == 1
    assert person.fp == 1


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


def test_actionable_metrics_ignore_pass_predictions() -> None:
    label = EvaluationLabel(
        start=0,
        end=2,
        entity_type=EntityType.PERSON_NAME,
        risk_level=RiskLevel.P1,
    )
    pass_prediction = _public(0, 2, EntityType.PERSON_NAME, action=Action.PASS)
    report = EvaluationReport(
        dataset_id="synthetic",
        records_processed=1,
        blocked_count=0,
        spans_detected=1,
        spans_masked=0,
        per_entity=(EntityMetrics("PERSON_NAME", 1, 0, 0, 0),),
        masked_text_exact_match_rate=0.0,
        high_risk_recall=1.0,
        case_results=(
            CaseResult(
                case_id="case-pass",
                matches=(
                    SpanMatch(
                        case_id="case-pass",
                        expected=label,
                        actual=pass_prediction,
                        match_type="exact",
                    ),
                ),
                masked_text="하늘",
                expected_masked_text="[PERSON_1]",
                blocked=False,
                audit_event_count=0,
                prediction_count=1,
            ),
        ),
    )

    actionable = report.actionable_overall_metrics

    assert report.overall_metrics.tp_exact == 1
    assert actionable.tp_exact == 0
    assert actionable.fn == 1
    assert actionable.fp == 0
    assert report.actionable_high_risk_recall == 0.0


def test_actionable_metrics_count_only_actionable_spurious_predictions() -> None:
    label = EvaluationLabel(
        start=0,
        end=2,
        entity_type=EntityType.PERSON_NAME,
        risk_level=RiskLevel.P1,
    )
    masked_match = _public(0, 2, EntityType.PERSON_NAME, action=Action.MASK)
    pass_spurious = _public(3, 5, EntityType.PERSON_NAME, action=Action.PASS)
    masked_spurious = _public(6, 8, EntityType.PERSON_NAME, action=Action.MASK)
    report = EvaluationReport(
        dataset_id="synthetic",
        records_processed=1,
        blocked_count=0,
        spans_detected=3,
        spans_masked=2,
        per_entity=(EntityMetrics("PERSON_NAME", 1, 0, 2, 0),),
        masked_text_exact_match_rate=1.0,
        high_risk_recall=1.0,
        case_results=(
            CaseResult(
                case_id="case-actionable",
                matches=(
                    SpanMatch(
                        case_id="case-actionable",
                        expected=label,
                        actual=masked_match,
                        match_type="exact",
                    ),
                    SpanMatch(
                        case_id="case-actionable",
                        expected=None,
                        actual=pass_spurious,
                        match_type="spurious",
                    ),
                    SpanMatch(
                        case_id="case-actionable",
                        expected=None,
                        actual=masked_spurious,
                        match_type="spurious",
                    ),
                ),
                masked_text="[PERSON_1]",
                expected_masked_text="[PERSON_1]",
                blocked=False,
                audit_event_count=0,
                prediction_count=3,
            ),
        ),
    )

    actionable = report.actionable_overall_metrics
    payload = report.to_safe_dict(purpose_id="test")

    assert actionable.tp_exact == 1
    assert actionable.fp == 1
    assert actionable.precision == pytest.approx(0.5)
    assert actionable.recall == pytest.approx(1.0)
    assert payload["actionable_overall"]["precision"] == 0.5
    assert payload["actionable_per_entity"][0]["entity_type"] == "PERSON_NAME"


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
    assert payload["masked_text_evaluable_count"] == 0
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


def test_raw_pii_logging_count_is_aggregated_from_response_flags() -> None:
    class FakePipeline:
        def process(self, request):
            span = _public(0, 3, EntityType.PERSON_NAME, raw_value_logged=True)
            event = AuditEvent(
                event_type="pii_action",
                entity_type=EntityType.PERSON_NAME,
                score=0.9,
                risk_level=RiskLevel.P1,
                action=Action.MASK,
                raw_value_logged=True,
            )
            return GuardrailResponse(
                request_id=request.effective_request_id,
                blocked=False,
                masked_text="[PERSON_1]",
                spans=(span,),
                audit_events=(event,),
                metrics=ResponseMetrics(latency_ms=1.0, detected_span_count=1, masked_span_count=1),
                policy_profile="strict",
                output_target=OutputTarget.LLM_INPUT,
                raw_value_logged=True,
            )

    runner = EvaluationRunner(FakePipeline())
    case = EvaluationCase(
        id="c1",
        text="홍길동",
        expected_masked_text="[PERSON_1]",
        labels=(
            EvaluationLabel(start=0, end=3, entity_type=EntityType.PERSON_NAME, risk_level=RiskLevel.P1),
        ),
    )

    report = runner.evaluate([case], dataset_id="synthetic")

    assert report.raw_pii_logging_count == 3
    assert report.response_raw_value_logged_count == 1
    assert report.public_span_raw_value_logged_count == 1
    assert report.audit_event_raw_value_logged_count == 1
    payload = report.to_safe_dict(purpose_id="ko_pii_guardrail_v0_2_eval")
    assert payload["raw_pii_logging_count"] == 3
    assert payload["response_raw_value_logged_count"] == 1
    assert payload["public_span_raw_value_logged_count"] == 1
    assert payload["audit_event_raw_value_logged_count"] == 1


def test_masked_text_accuracy_ignores_cases_without_expected_masked_text() -> None:
    runner = EvaluationRunner(GuardrailPipeline())
    expected_case = EvaluationCase(
        id="with-expected",
        text="홍길동",
        labels=(),
        expected_masked_text="[PERSON_1]",
    )
    missing_expected_case = EvaluationCase(
        id="without-expected",
        text="plain text",
        labels=(),
        expected_masked_text=None,
    )
    report = runner._aggregate(
        "synthetic",
        [expected_case, missing_expected_case],
        [
            CaseResult(
                case_id="with-expected",
                matches=(),
                masked_text="[PERSON_1]",
                expected_masked_text="[PERSON_1]",
                blocked=False,
                audit_event_count=0,
            ),
            CaseResult(
                case_id="without-expected",
                matches=(),
                masked_text="different output",
                expected_masked_text=None,
                blocked=False,
                audit_event_count=0,
            ),
        ],
    )

    assert report.masked_text_evaluable_count == 1
    assert report.masked_text_exact_match_rate == 1.0


# ============================================================
# M10-3 release gate core
# ============================================================


def _release_gate_report(
    *,
    raw_pii_logging_count: int = 0,
    invalid_offset_count: int = 0,
    latency_p95: float = 50.0,
    match_type: str = "exact",
    actual_action: Action = Action.MASK,
    ner_mode: str = "disabled",
) -> EvaluationReport:
    label = EvaluationLabel(
        start=4,
        end=17,
        entity_type=EntityType.PHONE_MOBILE,
        risk_level=RiskLevel.P1,
        suffix="로",
    )
    actual = (
        _public(4, 17, EntityType.PHONE_MOBILE, action=actual_action)
        if match_type != "miss"
        else None
    )
    case_result = CaseResult(
        case_id="case-release",
        matches=(
            SpanMatch(
                case_id="case-release",
                expected=label,
                actual=actual,
                match_type=match_type,
            ),
        ),
        masked_text="[PHONE_1]로",
        expected_masked_text="[PHONE_1]로",
        blocked=False,
        audit_event_count=0,
        prediction_count=1 if actual is not None else 0,
        raw_pii_logging_count=raw_pii_logging_count,
        latency_ms=latency_p95,
    )
    return EvaluationReport(
        dataset_id="release-synthetic",
        records_processed=1,
        blocked_count=0,
        spans_detected=case_result.prediction_count,
        spans_masked=0,
        per_entity=(
            EntityMetrics(
                entity_type="PHONE_MOBILE",
                tp_exact=1 if match_type == "exact" else 0,
                tp_partial=1 if match_type == "partial" else 0,
                fp=0,
                fn=1 if match_type == "miss" else 0,
            ),
        ),
        masked_text_exact_match_rate=1.0,
        high_risk_recall=0.0,
        masked_text_evaluable_count=1,
        raw_pii_logging_count=raw_pii_logging_count,
        invalid_offset_count=invalid_offset_count,
        deterministic_latency_ms={"p50": latency_p95, "p95": latency_p95, "p99": latency_p95},
        ner_mode=ner_mode,
        case_results=(case_result,),
    )


def test_release_gate_core_pass_and_skipped_real_ner() -> None:
    payload = build_release_gate_report(_release_gate_report()).to_dict()
    checks = {check["name"]: check for check in payload["checks"]}

    assert payload["overall_status"] == "pass"
    assert checks["high_risk_structured_recall"]["status"] == "pass"
    assert checks["phone_email_recall"]["status"] == "pass"
    assert checks["josa_boundary_accuracy"]["status"] == "pass"
    assert checks["deterministic_latency_p95_ms"]["status"] == "pass"
    assert checks["real_ner_latency_ms"]["status"] == "skipped"


def test_release_gate_recall_requires_actionable_prediction() -> None:
    payload = build_release_gate_report(
        _release_gate_report(actual_action=Action.PASS)
    ).to_dict()
    checks = {check["name"]: check for check in payload["checks"]}

    assert payload["overall_status"] == "fail"
    assert checks["high_risk_structured_recall"]["status"] == "fail"
    assert checks["high_risk_structured_recall"]["actual_value"] == 0.0
    assert checks["phone_email_recall"]["status"] == "fail"
    assert checks["phone_email_recall"]["actual_value"] == 0.0


def test_release_gate_fails_when_raw_pii_logging_count_is_nonzero() -> None:
    payload = build_release_gate_report(
        _release_gate_report(raw_pii_logging_count=1)
    ).to_dict()
    checks = {check["name"]: check for check in payload["checks"]}

    assert payload["overall_status"] == "fail"
    assert checks["raw_pii_logging_count"]["status"] == "fail"
    assert checks["raw_pii_logging_count"]["actual_value"] == 1


def test_release_gate_fails_when_invalid_offset_count_is_nonzero() -> None:
    payload = build_release_gate_report(
        _release_gate_report(invalid_offset_count=1)
    ).to_dict()
    checks = {check["name"]: check for check in payload["checks"]}

    assert payload["overall_status"] == "fail"
    assert checks["invalid_offset_count"]["status"] == "fail"
    assert checks["invalid_offset_count"]["actual_value"] == 1


def test_release_gate_fails_when_latency_exceeds_threshold() -> None:
    payload = build_release_gate_report(
        _release_gate_report(latency_p95=101.0)
    ).to_dict()
    checks = {check["name"]: check for check in payload["checks"]}

    assert payload["overall_status"] == "fail"
    assert checks["deterministic_latency_p95_ms"]["status"] == "fail"


def test_release_gate_skips_deterministic_latency_when_real_ner_path_is_included() -> None:
    payload = build_release_gate_report(
        _release_gate_report(latency_p95=250.0, ner_mode="real")
    ).to_dict()
    checks = {check["name"]: check for check in payload["checks"]}

    assert payload["overall_status"] == "pass"
    assert checks["deterministic_latency_p95_ms"]["status"] == "skipped"
    assert checks["deterministic_latency_p95_ms"]["reason_code"] == (
        "gate.deterministic_latency.real_ner_path_included"
    )


def test_name_ambiguity_fp_rate_counts_only_actionable_person_predictions() -> None:
    pass_person = _public(0, 2, EntityType.PERSON_NAME, action=Action.PASS)
    masked_person = _public(3, 5, EntityType.PERSON_NAME, action=Action.MASK)
    report = EvaluationReport(
        dataset_id="hard-negative",
        records_processed=2,
        blocked_count=0,
        spans_detected=2,
        spans_masked=1,
        per_entity=(),
        masked_text_exact_match_rate=0.0,
        high_risk_recall=0.0,
        deterministic_latency_ms={"p50": 1.0, "p95": 1.0, "p99": 1.0},
        case_results=(
            CaseResult(
                case_id="hn-pass",
                matches=(
                    SpanMatch(
                        case_id="hn-pass",
                        expected=None,
                        actual=pass_person,
                        match_type="spurious",
                    ),
                ),
                masked_text="safe",
                expected_masked_text=None,
                blocked=False,
                audit_event_count=0,
                prediction_count=1,
                tags=("hard_negative",),
            ),
            CaseResult(
                case_id="hn-mask",
                matches=(
                    SpanMatch(
                        case_id="hn-mask",
                        expected=None,
                        actual=masked_person,
                        match_type="spurious",
                    ),
                ),
                masked_text="[PERSON_1]",
                expected_masked_text=None,
                blocked=False,
                audit_event_count=0,
                prediction_count=1,
                tags=("hard_negative",),
            ),
        ),
    )
    payload = build_release_gate_report(report).to_dict()
    checks = {check["name"]: check for check in payload["checks"]}

    assert checks["name_ambiguity_fp_rate"]["actual_value"] == 0.5
    assert checks["name_ambiguity_fp_rate"]["status"] == "fail"


# ============================================================
# M10-4 failure analysis + audit safety reports
# ============================================================


def test_failure_analysis_rows_classify_errors_without_raw_text() -> None:
    runner = EvaluationRunner(GuardrailPipeline())
    raw_value = "ABCD1234"
    raw_text = f"token {raw_value} tail"
    label = EvaluationLabel(
        start=6,
        end=14,
        entity_type=EntityType.PERSON_NAME,
        risk_level=RiskLevel.P1,
    )
    type_case = EvaluationCase(id="case-type", text=raw_text, labels=(label,))
    type_matches = runner._match_spans(
        type_case,
        (_public(6, 14, EntityType.ORGANIZATION),),
    )
    fp_case = EvaluationCase(id="case-fp", text="plain text", labels=())
    fp_matches = runner._match_spans(
        fp_case,
        (_public(0, 5, EntityType.EMAIL),),
    )
    duplicate_case = EvaluationCase(id="case-duplicate", text=raw_text, labels=(label,))
    duplicate_matches = runner._match_spans(
        duplicate_case,
        (
            _public(6, 14, EntityType.PERSON_NAME),
            _public(6, 15, EntityType.PERSON_NAME),
        ),
    )
    report = EvaluationReport(
        dataset_id="failure-synthetic",
        records_processed=3,
        blocked_count=0,
        spans_detected=4,
        spans_masked=0,
        per_entity=(),
        masked_text_exact_match_rate=0.0,
        high_risk_recall=0.0,
        case_results=(
            CaseResult(
                case_id="case-type",
                matches=tuple(type_matches),
                masked_text=None,
                expected_masked_text=None,
                blocked=False,
                audit_event_count=0,
                prediction_count=1,
            ),
            CaseResult(
                case_id="case-fp",
                matches=tuple(fp_matches),
                masked_text=None,
                expected_masked_text=None,
                blocked=False,
                audit_event_count=0,
                prediction_count=1,
            ),
            CaseResult(
                case_id="case-duplicate",
                matches=tuple(duplicate_matches),
                masked_text=None,
                expected_masked_text=None,
                blocked=False,
                audit_event_count=0,
                prediction_count=2,
            ),
        ),
    )

    rows = build_failure_analysis_rows(report)
    row_keys = {
        (row.case_id, row.error_type, row.entity_type, row.match_type)
        for row in rows
    }
    assert ("case-type", "FN", "PERSON_NAME", "miss") in row_keys
    assert ("case-type", "TYPE_CONFUSION", "ORGANIZATION", "spurious") in row_keys
    assert ("case-fp", "FP", "EMAIL", "spurious") in row_keys
    assert ("case-duplicate", "OVERDETECTION", "PERSON_NAME", "spurious") in row_keys

    serialized = failure_analysis_jsonl(report)
    assert raw_value not in serialized
    assert raw_text not in serialized
    for line in serialized.splitlines():
        payload = json.loads(line)
        assert set(payload) == {
            "case_id",
            "error_type",
            "entity_type",
            "span_length",
            "match_type",
            "suspected_layer",
            "reason_code",
            "raw_value_logged",
        }
        assert payload["raw_value_logged"] is False


def test_audit_safety_report_passes_and_fails_without_raw_values() -> None:
    pass_payload = build_audit_safety_report(
        _release_gate_report(),
        report_raw_text_leak_count=0,
    ).to_dict()
    assert pass_payload["status"] == "pass"
    assert pass_payload["raw_pii_logging_count"] == 0
    assert pass_payload["public_span_raw_value_logged_count"] == 0
    assert pass_payload["audit_event_raw_value_logged_count"] == 0
    assert pass_payload["report_raw_text_leak_count"] == 0

    fail_payload = build_audit_safety_report(
        _release_gate_report(raw_pii_logging_count=1),
        report_raw_text_leak_count=0,
    ).to_dict()
    assert fail_payload["status"] == "fail"
    assert fail_payload["raw_pii_logging_count"] == 1
    assert "audit_safety.raw_pii_logging_count.fail" in fail_payload["reason_codes"]


def test_report_raw_text_leak_counter_returns_count_only() -> None:
    raw_value = "WXYZ9876"
    case = EvaluationCase(
        id="case-leak-check",
        text=f"prefix {raw_value} suffix",
        labels=(
            EvaluationLabel(
                start=7,
                end=15,
                entity_type=EntityType.PHONE_MOBILE,
                risk_level=RiskLevel.P1,
            ),
        ),
    )

    assert count_report_raw_text_leaks([{"note": "safe summary"}], [case]) == 0
    assert count_report_raw_text_leaks([{"note": f"unsafe {raw_value}"}], [case]) == 1


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


def test_run_eval_writes_safe_json_report(tmp_path: Path) -> None:
    # real-NER integration test: run_eval 가 mode="real" 로 실제 NER 모델
    # (torch + `[ner]` extra)을 로드한다. torch 없는 가벼운 CI 에서는 skip.
    pytest.importorskip("torch")
    raw_phone = "010-1234-5678"
    raw_text = f"연락처 {raw_phone}"
    dataset = tmp_path / "tiny_eval.jsonl"
    dataset.write_text(
        json.dumps({
            "id": "case-cli",
            "text": raw_text,
            "expected_masked_text": "연락처 [PHONE_1]",
            "labels": [
                {"start": 4, "end": 17, "entity_type": "PHONE_MOBILE", "risk_level": "P1"},
            ],
            "tags": ["phone"],
        }) + "\n",
        encoding="utf-8",
    )
    output = tmp_path / "reports" / "eval.json"
    failure_output = tmp_path / "reports" / "failure.jsonl"
    audit_output = tmp_path / "reports" / "audit_safety.json"

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "run_eval.py"),
            "--config-dir",
            str(PROJECT_ROOT / "configs"),
            "--dataset",
            str(dataset),
            "--output",
            str(output),
            "--failure-output",
            str(failure_output),
            "--audit-safety-output",
            str(audit_output),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    assert output.exists()
    assert failure_output.exists()
    assert audit_output.exists()
    serialized = output.read_text(encoding="utf-8")
    failure_serialized = failure_output.read_text(encoding="utf-8")
    audit_serialized = audit_output.read_text(encoding="utf-8")
    payload = json.loads(serialized)
    audit_payload = json.loads(audit_serialized)
    assert payload["dataset_id"] == "tiny_eval"
    assert payload["records_processed"] == 1
    assert "per_entity" in payload
    assert "deterministic_latency_ms" in payload
    assert payload["ner_detector"] == {
        "mode": "real",
        "detector_id": "ner.finetuned.klue-roberta-large-v3",
    }
    assert payload["real_ner_latency_ms"]["reason_code"] == (
        "gate.real_ner_latency.separate_instrumentation_unavailable"
    )
    assert "release_gate" in payload
    assert payload["release_gate"]["report_type"] == "ReleaseGateReport"
    assert audit_payload["report_type"] == "AuditSafetyReport"
    assert audit_payload["status"] == "pass"
    assert audit_payload["report_raw_text_leak_count"] == 0
    assert raw_phone not in serialized
    assert raw_text not in serialized
    assert raw_phone not in failure_serialized
    assert raw_text not in failure_serialized
    assert raw_phone not in audit_serialized
    assert raw_text not in audit_serialized
    assert raw_phone not in result.stdout
    assert raw_text not in result.stdout


# ============================================================
# M10-2 cumulative ablation
# ============================================================


def _tiny_ablation_dataset(tmp_path: Path) -> tuple[Path, str, str]:
    raw_phone = "010-1234-5678"
    raw_text = f"연락처 {raw_phone}"
    dataset = tmp_path / "tiny_ablation.jsonl"
    dataset.write_text(
        json.dumps({
            "id": "case-ablation",
            "text": raw_text,
            "expected_masked_text": "연락처 [PHONE_1]",
            "labels": [
                {"start": 4, "end": 17, "entity_type": "PHONE_MOBILE", "risk_level": "P1"},
            ],
            "tags": ["phone"],
        }) + "\n",
        encoding="utf-8",
    )
    return dataset, raw_text, raw_phone


def test_ablation_runner_executes_a_to_f_and_skips_e2(tmp_path: Path) -> None:
    dataset, _, _ = _tiny_ablation_dataset(tmp_path)
    cases = load_jsonl_cases(dataset)
    pipeline = GuardrailPipeline.from_config_dir(PROJECT_ROOT / "configs")

    report = AblationRunner(pipeline).evaluate(cases, dataset_id="tiny_ablation")
    payload = report.to_safe_dict()

    stage_names = [stage["stage_name"] for stage in payload["stages"]]
    assert stage_names == ["A", "B", "C", "D", "E1", "E2", "F"]
    by_name = {stage["stage_name"]: stage for stage in payload["stages"]}
    for name in ("A", "B", "C", "D", "E1", "F"):
        assert by_name[name]["status"] == "ok"
        assert by_name[name]["records_processed"] == 1
        assert "components" in by_name[name]
        assert "per_entity" in by_name[name]
        assert "overall" in by_name[name]
        assert by_name[name]["raw_pii_logging_count"] == 0
        assert by_name[name]["invalid_offset_count"] == 0

    assert by_name["E2"]["status"] == "skipped"
    assert "real NER" in by_name["E2"]["skip_reason"]


def test_ablation_report_does_not_contain_raw_text(tmp_path: Path) -> None:
    dataset, raw_text, raw_phone = _tiny_ablation_dataset(tmp_path)
    cases = load_jsonl_cases(dataset)
    pipeline = GuardrailPipeline.from_config_dir(PROJECT_ROOT / "configs")

    report = AblationRunner(pipeline).evaluate(cases, dataset_id="tiny_ablation")
    serialized = json.dumps(report.to_safe_dict(), ensure_ascii=False)

    assert raw_text not in serialized
    assert raw_phone not in serialized


def test_run_ablation_writes_safe_json_report(tmp_path: Path) -> None:
    # real-NER integration test (test_run_eval 와 동일 이유): torch 없으면 skip.
    pytest.importorskip("torch")
    dataset, raw_text, raw_phone = _tiny_ablation_dataset(tmp_path)
    output = tmp_path / "reports" / "ablation.json"

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "run_ablation.py"),
            "--config-dir",
            str(PROJECT_ROOT / "configs"),
            "--dataset",
            str(dataset),
            "--output",
            str(output),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    assert output.exists()
    serialized = output.read_text(encoding="utf-8")
    payload = json.loads(serialized)
    assert payload["report_type"] == "AblationEvaluationReport"
    assert payload["dataset_id"] == "tiny_ablation"
    assert [stage["stage_name"] for stage in payload["stages"]] == ["A", "B", "C", "D", "E1", "E2", "F"]
    by_name = {stage["stage_name"]: stage for stage in payload["stages"]}
    assert by_name["E2"]["status"] == "ok"
    assert "real_v3_ner" in by_name["E2"]["components"]
    assert "real_v3_ner" in by_name["F"]["components"]
    assert raw_text not in serialized
    assert raw_phone not in serialized
    assert raw_text not in result.stdout
    assert raw_phone not in result.stdout
