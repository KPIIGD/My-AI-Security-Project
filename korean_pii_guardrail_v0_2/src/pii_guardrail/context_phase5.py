"""Phase 5 reviewed context scoring config release-gate comparison."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .context_evidence import dumps_json


PROJECT_ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class Phase5BuildResult:
    comparison: dict[str, Any]
    markdown: str
    previous_config_snapshot: str


def build_phase5_reviewed_config_report(
    *,
    project_root: Path = PROJECT_ROOT,
    phase4_delta_path: Path | None = None,
    before_release_gate_path: Path | None = None,
    after_release_gate_path: Path | None = None,
    after_audit_safety_path: Path | None = None,
) -> Phase5BuildResult:
    phase4_delta_path = phase4_delta_path or (
        project_root / "reports" / "context_delta_sweep_v1.json"
    )
    before_release_gate_path = before_release_gate_path or (
        project_root / "reports" / "release_gate_v0_2.json"
    )
    after_release_gate_path = after_release_gate_path or (
        project_root / "reports" / "release_gate_m4_phase5_after_v1.json"
    )
    after_audit_safety_path = after_audit_safety_path or (
        project_root / "reports" / "audit_safety_release_gate_m4_phase5_after_v1.json"
    )

    scoring_path = project_root / "configs" / "scoring.yaml"
    scoring_text = scoring_path.read_text(encoding="utf-8")
    phase4_delta = _read_json(phase4_delta_path)
    before = _read_json(before_release_gate_path)
    after = _read_json(after_release_gate_path)
    after_audit = _read_json(after_audit_safety_path)

    approved_changes = phase4_delta.get("config_changes_proposed", [])
    config_update_applied = False
    config_hash = _sha256(scoring_text)
    comparison = {
        "report_type": "ContextReviewedConfigReleaseGateComparison",
        "version": "v0.2-single-turn",
        "phase": "Execution Phase 5. Reviewed Config Change",
        "runtime_scoring_behavior_changed": False,
        "score_delta_changed": False,
        "public_corpus_used_for_score_tuning": False,
        "approved_delta_count": len(approved_changes),
        "approved_deltas": approved_changes,
        "config_update_applied": config_update_applied,
        "config_change_decision": (
            "no_op_no_approved_deltas"
            if not approved_changes
            else "not_applied_requires_manual_review"
        ),
        "paired_docs_update_required": bool(approved_changes),
        "paired_docs_update_reason": (
            "no approved scoring deltas; scoring/context docs remain unchanged"
            if not approved_changes
            else "approved scoring deltas require paired scoring/context docs"
        ),
        "config_snapshot": {
            "path": "configs/scoring.yaml",
            "previous_snapshot_path": (
                "reports/context_scoring_previous_config_phase5_v1.yaml"
            ),
            "previous_sha256": config_hash,
            "current_sha256": config_hash,
            "unchanged": True,
        },
        "release_gate_inputs": {
            "before_report": _relpath(before_release_gate_path, project_root),
            "after_report": _relpath(after_release_gate_path, project_root),
            "after_audit_safety_report": _relpath(after_audit_safety_path, project_root),
        },
        "release_gate_summary": {
            "before_status": before["release_gate"]["overall_status"],
            "after_status": after["release_gate"]["overall_status"],
            "records_processed_before": before["records_processed"],
            "records_processed_after": after["records_processed"],
        },
        "checks": _release_gate_checks(before, after, after_audit),
    }
    comparison["status"] = (
        "pass"
        if comparison["config_update_applied"] is False
        and all(check["status"] == "pass" for check in comparison["checks"])
        else "fail"
    )
    return Phase5BuildResult(
        comparison=comparison,
        markdown=render_phase5_markdown(comparison),
        previous_config_snapshot=scoring_text,
    )


def write_phase5_reviewed_config_reports(
    *,
    project_root: Path = PROJECT_ROOT,
    phase4_delta_path: Path | None = None,
    before_release_gate_path: Path | None = None,
    after_release_gate_path: Path | None = None,
    after_audit_safety_path: Path | None = None,
) -> tuple[Phase5BuildResult, dict[str, Path]]:
    result = build_phase5_reviewed_config_report(
        project_root=project_root,
        phase4_delta_path=phase4_delta_path,
        before_release_gate_path=before_release_gate_path,
        after_release_gate_path=after_release_gate_path,
        after_audit_safety_path=after_audit_safety_path,
    )
    paths = {
        "comparison_json": (
            project_root / "reports" / "context_scoring_release_gate_comparison_v1.json"
        ),
        "comparison_md": (
            project_root / "reports" / "context_scoring_release_gate_comparison_v1.md"
        ),
        "previous_config_snapshot": (
            project_root / "reports" / "context_scoring_previous_config_phase5_v1.yaml"
        ),
    }
    paths["comparison_json"].write_text(dumps_json(result.comparison), encoding="utf-8")
    paths["comparison_md"].write_text(result.markdown, encoding="utf-8")
    paths["previous_config_snapshot"].write_text(
        result.previous_config_snapshot,
        encoding="utf-8",
    )
    return result, paths


def render_phase5_markdown(comparison: dict[str, Any]) -> str:
    lines = [
        "# Context Reviewed Config Release Gate Comparison v1",
        "",
        f"- phase: `{comparison['phase']}`",
        f"- status: `{comparison['status']}`",
        f"- approved_delta_count: `{comparison['approved_delta_count']}`",
        f"- config_update_applied: `{str(comparison['config_update_applied']).lower()}`",
        "- runtime_scoring_behavior_changed: `false`",
        "- public_corpus_used_for_score_tuning: `false`",
        f"- config_change_decision: `{comparison['config_change_decision']}`",
        "",
        "## Release Gate Checks",
        "",
        "| Check | Before | After | Delta | Status |",
        "|---|---:|---:|---:|---|",
    ]
    for check in comparison["checks"]:
        lines.append(
            "| {name} | {before} | {after} | {delta} | {status} |".format(
                name=check["name"],
                before=_display(check["before"]),
                after=_display(check["after"]),
                delta=_display(check["delta"]),
                status=check["status"],
            )
        )
    return "\n".join(lines) + "\n"


def _release_gate_checks(
    before: dict[str, Any],
    after: dict[str, Any],
    after_audit: dict[str, Any],
) -> list[dict[str, Any]]:
    return [
        _zero_check("raw_pii_logging_count", before, after),
        _zero_check("invalid_offset_count", before, after),
        _no_regression_check("high_risk_recall", before, after),
        _no_regression_check("actionable_high_risk_recall", before, after),
        _no_regression_value_check(
            "phone_email_actionable_recall",
            _min_entity_recall(before, ("EMAIL", "PHONE_LANDLINE", "PHONE_MOBILE")),
            _min_entity_recall(after, ("EMAIL", "PHONE_LANDLINE", "PHONE_MOBILE")),
        ),
        _no_regression_value_check(
            "bank_account_actionable_recall",
            _entity_recall(before, "BANK_ACCOUNT"),
            _entity_recall(after, "BANK_ACCOUNT"),
        ),
        _no_increase_value_check(
            "person_name_hard_negative_candidate_fp",
            _hard_negative_entity_fp(before, "PERSON_NAME"),
            _hard_negative_entity_fp(after, "PERSON_NAME"),
        ),
        _no_increase_value_check(
            "hard_negative_actionable_fp_total",
            _hard_negative_actionable_count(before),
            _hard_negative_actionable_count(after),
        ),
        _no_regression_check("actionable_overall_precision", before, after),
        _no_increase_value_check(
            "deterministic_latency_p95_ms",
            before["deterministic_latency_ms"]["p95"],
            after["deterministic_latency_ms"]["p95"],
        ),
        {
            "name": "report_raw_text_leak_count",
            "before": 0,
            "after": after_audit["report_raw_text_leak_count"],
            "delta": after_audit["report_raw_text_leak_count"],
            "status": (
                "pass" if after_audit["report_raw_text_leak_count"] == 0 else "fail"
            ),
        },
        {
            "name": "after_audit_safety_status",
            "before": "pass",
            "after": after_audit["status"],
            "delta": "n/a",
            "status": "pass" if after_audit["status"] == "pass" else "fail",
        },
        {
            "name": "release_gate_overall_status",
            "before": before["release_gate"]["overall_status"],
            "after": after["release_gate"]["overall_status"],
            "delta": "n/a",
            "status": (
                "pass" if after["release_gate"]["overall_status"] == "pass" else "fail"
            ),
        },
    ]


def _zero_check(
    metric_name: str,
    before: dict[str, Any],
    after: dict[str, Any],
) -> dict[str, Any]:
    before_value = before[metric_name]
    after_value = after[metric_name]
    return {
        "name": metric_name,
        "before": before_value,
        "after": after_value,
        "delta": after_value - before_value,
        "status": "pass" if after_value == 0 else "fail",
    }


def _no_regression_check(
    metric_name: str,
    before: dict[str, Any],
    after: dict[str, Any],
) -> dict[str, Any]:
    return _no_regression_value_check(metric_name, before[metric_name], after[metric_name])


def _no_regression_value_check(
    metric_name: str,
    before_value: float | int,
    after_value: float | int,
) -> dict[str, Any]:
    delta = after_value - before_value
    return {
        "name": metric_name,
        "before": before_value,
        "after": after_value,
        "delta": round(delta, 6) if isinstance(delta, float) else delta,
        "status": "pass" if after_value >= before_value else "fail",
    }


def _no_increase_value_check(
    metric_name: str,
    before_value: float | int,
    after_value: float | int,
) -> dict[str, Any]:
    delta = after_value - before_value
    return {
        "name": metric_name,
        "before": before_value,
        "after": after_value,
        "delta": round(delta, 6) if isinstance(delta, float) else delta,
        "status": "pass" if after_value <= before_value else "fail",
    }


def _entity_recall(payload: dict[str, Any], entity_type: str) -> float:
    for row in payload["actionable_per_entity"]:
        if row["entity_type"] == entity_type:
            return row["recall"]
    return 0.0


def _min_entity_recall(payload: dict[str, Any], entity_types: tuple[str, ...]) -> float:
    return min(_entity_recall(payload, entity_type) for entity_type in entity_types)


def _hard_negative_entity_fp(payload: dict[str, Any], entity_type: str) -> int:
    hard_negative = payload["per_bucket"].get("hard_negative", {})
    for row in hard_negative.get("per_entity", []):
        if row["entity_type"] == entity_type:
            return row["fp"]
    return 0


def _hard_negative_actionable_count(payload: dict[str, Any]) -> int:
    action_counts = payload["per_bucket"].get("hard_negative", {}).get(
        "action_counts",
        {},
    )
    return sum(
        int(count)
        for action, count in action_counts.items()
        if action in {"block", "hash", "mask"}
    )


def _read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _relpath(path: Path, project_root: Path) -> str:
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return str(path)


def _sha256(text: str) -> str:
    return "sha256:" + hashlib.sha256(text.encode("utf-8")).hexdigest()


def _display(value: Any) -> str:
    if value is None:
        return "n/a"
    return str(value)
