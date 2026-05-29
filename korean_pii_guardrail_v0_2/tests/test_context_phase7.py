from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from pii_guardrail.context_phase7 import (
    CalibrationPoint,
    build_phase7_logistic_calibration_spike,
    fit_regularized_logistic,
    render_phase7_markdown,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_phase7_regularized_logistic_learns_shadow_score() -> None:
    points = [
        CalibrationPoint("train", 0.15, 0, "PERSON_NAME", "pass"),
        CalibrationPoint("train", 0.40, 0, "PERSON_NAME", "pass"),
        CalibrationPoint("train", 0.90, 1, "PHONE_MOBILE", "mask"),
        CalibrationPoint("train", 0.95, 1, "PHONE_MOBILE", "mask"),
    ]

    calibrator = fit_regularized_logistic(points)

    assert calibrator.predict(0.95) > calibrator.predict(0.15)
    assert 0.0 < calibrator.predict(0.40) < 1.0


def test_phase7_project_report_is_shadow_only_and_raw_safe() -> None:
    payload = build_phase7_logistic_calibration_spike(PROJECT_ROOT)

    assert payload["status"] == "pass"
    assert payload["runtime_scoring_behavior_changed"] is False
    assert payload["score_delta_changed"] is False
    assert payload["deterministic_config_remains_default"] is True
    assert payload["deterministic_fallback_available"] is True
    assert payload["reason_codes_preserved_by_shadow_mode"] is True
    assert payload["raw_pii_safety"]["status"] == "pass"
    assert payload["split_reports"]["test"]["calibrated_ece"] < payload["split_reports"]["test"][
        "deterministic_ece"
    ]
    assert payload["actionable_high_risk_recall_regressed"] is False


def test_phase7_markdown_records_research_only_decision() -> None:
    payload = build_phase7_logistic_calibration_spike(PROJECT_ROOT)
    markdown = render_phase7_markdown(payload)

    assert "promotion_decision: `research_only_not_promoted`" in markdown
    assert "Runtime reason codes" in markdown
    assert "010-" not in markdown


def test_phase7_cli_writes_expected_report() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "run_context_calibration_spike.py"),
            "--project-root",
            str(PROJECT_ROOT),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "phase7_status=pass" in result.stdout
    report_path = PROJECT_ROOT / "reports" / "context_logistic_calibration_spike_v1.md"
    assert report_path.exists()
    assert "research_only_not_promoted" in report_path.read_text(encoding="utf-8")
