from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from pii_guardrail.context_phase5 import (
    build_phase5_reviewed_config_report,
    write_phase5_reviewed_config_reports,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_phase5_noop_config_report_passes_release_gate_checks(tmp_path: Path) -> None:
    paths = _write_phase5_fixture(tmp_path)

    result = build_phase5_reviewed_config_report(
        project_root=tmp_path,
        phase4_delta_path=paths["delta"],
        before_release_gate_path=paths["before"],
        after_release_gate_path=paths["after"],
        after_audit_safety_path=paths["audit"],
    )

    assert result.comparison["status"] == "pass"
    assert result.comparison["approved_delta_count"] == 0
    assert result.comparison["config_update_applied"] is False
    assert result.comparison["config_snapshot"]["unchanged"] is True
    assert all(check["status"] == "pass" for check in result.comparison["checks"])
    assert "config_update_applied: `false`" in result.markdown


def test_phase5_report_fails_on_actionable_recall_regression(tmp_path: Path) -> None:
    paths = _write_phase5_fixture(tmp_path, after_actionable_high_risk_recall=0.8)

    result = build_phase5_reviewed_config_report(
        project_root=tmp_path,
        phase4_delta_path=paths["delta"],
        before_release_gate_path=paths["before"],
        after_release_gate_path=paths["after"],
        after_audit_safety_path=paths["audit"],
    )
    by_name = {check["name"]: check for check in result.comparison["checks"]}

    assert result.comparison["status"] == "fail"
    assert by_name["actionable_high_risk_recall"]["status"] == "fail"


def test_phase5_writer_creates_config_snapshot_and_reports(tmp_path: Path) -> None:
    paths = _write_phase5_fixture(tmp_path)

    result, output_paths = write_phase5_reviewed_config_reports(
        project_root=tmp_path,
        phase4_delta_path=paths["delta"],
        before_release_gate_path=paths["before"],
        after_release_gate_path=paths["after"],
        after_audit_safety_path=paths["audit"],
    )

    assert result.comparison["status"] == "pass"
    assert output_paths["comparison_json"].exists()
    assert output_paths["comparison_md"].exists()
    assert output_paths["previous_config_snapshot"].read_text(
        encoding="utf-8"
    ) == "context_boosts:\n  field_label_name: 0.25\n"


def test_phase5_cli_writes_expected_reports() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "build_context_config_release_report.py"),
            "--project-root",
            str(PROJECT_ROOT),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "phase5_status=pass" in result.stdout
    for path in (
        PROJECT_ROOT / "reports" / "context_scoring_release_gate_comparison_v1.json",
        PROJECT_ROOT / "reports" / "context_scoring_release_gate_comparison_v1.md",
        PROJECT_ROOT / "reports" / "context_scoring_previous_config_phase5_v1.yaml",
    ):
        assert path.exists()


def _write_phase5_fixture(
    root: Path,
    *,
    after_actionable_high_risk_recall: float = 0.9,
) -> dict[str, Path]:
    (root / "configs").mkdir(parents=True)
    (root / "reports").mkdir(parents=True)
    (root / "configs" / "scoring.yaml").write_text(
        "context_boosts:\n  field_label_name: 0.25\n",
        encoding="utf-8",
    )
    paths = {
        "delta": root / "reports" / "context_delta_sweep_v1.json",
        "before": root / "reports" / "release_gate_before.json",
        "after": root / "reports" / "release_gate_after.json",
        "audit": root / "reports" / "audit_safety_after.json",
    }
    paths["delta"].write_text(
        json.dumps({"config_changes_proposed": []}),
        encoding="utf-8",
    )
    paths["before"].write_text(
        json.dumps(_release_gate_payload(actionable_high_risk_recall=0.9)),
        encoding="utf-8",
    )
    paths["after"].write_text(
        json.dumps(
            _release_gate_payload(
                actionable_high_risk_recall=after_actionable_high_risk_recall,
            )
        ),
        encoding="utf-8",
    )
    paths["audit"].write_text(
        json.dumps({"status": "pass", "report_raw_text_leak_count": 0}),
        encoding="utf-8",
    )
    return paths


def _release_gate_payload(*, actionable_high_risk_recall: float) -> dict[str, object]:
    return {
        "release_gate": {"overall_status": "pass"},
        "records_processed": 5000,
        "raw_pii_logging_count": 0,
        "invalid_offset_count": 0,
        "high_risk_recall": 0.9,
        "actionable_high_risk_recall": actionable_high_risk_recall,
        "actionable_overall_precision": 0.99,
        "deterministic_latency_ms": {"p95": 50.0},
        "actionable_per_entity": [
            {"entity_type": "EMAIL", "recall": 1.0},
            {"entity_type": "PHONE_LANDLINE", "recall": 1.0},
            {"entity_type": "PHONE_MOBILE", "recall": 1.0},
            {"entity_type": "BANK_ACCOUNT", "recall": 1.0},
        ],
        "per_bucket": {
            "hard_negative": {
                "action_counts": {"pass": 10},
                "per_entity": [{"entity_type": "PERSON_NAME", "fp": 5}],
            }
        },
    }
