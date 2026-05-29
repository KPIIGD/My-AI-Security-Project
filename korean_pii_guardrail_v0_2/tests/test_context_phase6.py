from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from pii_guardrail.context_phase6 import (
    build_context_domain_evidence,
    build_customer_aggregate_template,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_phase6_domain_rows_are_report_only_for_low_support() -> None:
    rule_evidence = {
        "rules": [
            {
                "rule_id": "context.boost.field_label_phone",
                "domain_breakdown": [
                    {
                        "domain": "ecommerce",
                        "bucket": "positive_person_phone",
                        "fired_count": 3,
                        "tp_fired": 3,
                        "fp_fired": 0,
                    }
                ],
            }
        ]
    }

    payload = build_context_domain_evidence(rule_evidence)

    assert payload["status"] == "pass"
    assert payload["domain_specific_profile_created"] is False
    assert payload["default_profile_decision"] == "keep_global_default"
    assert payload["domain_rows"][0]["support_status"] == "insufficient_support"
    assert payload["domain_rows"][0]["recommendation"] == "report_only_collect_more_evidence"


def test_phase6_customer_template_is_aggregate_only_and_raw_safe() -> None:
    template = build_customer_aggregate_template()
    serialized = json.dumps(template, ensure_ascii=False)

    assert template["status"] == "pass"
    assert template["raw_text_allowed"] is False
    assert template["raw_url_allowed"] is False
    assert template["raw_candidate_value_allowed"] is False
    assert template["example_row"]["raw_value_logged"] is False
    assert "raw_text" in template["disallowed_fields"]
    assert "010-" not in serialized
    assert "@example" not in serialized


def test_phase6_cli_writes_expected_reports() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "build_context_domain_reports.py"),
            "--project-root",
            str(PROJECT_ROOT),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "phase6_status=pass" in result.stdout
    for path in (
        PROJECT_ROOT / "reports" / "context_domain_evidence_v1.json",
        PROJECT_ROOT / "docs" / "context_domain_profile_notes_v1.md",
        PROJECT_ROOT / "reports" / "customer_aggregate_context_evidence_template_v1.json",
        PROJECT_ROOT / "docs" / "customer_side_context_calibration_runbook_v1.md",
    ):
        assert path.exists()


def test_phase6_generated_reports_keep_global_default() -> None:
    subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "build_context_domain_reports.py"),
            "--project-root",
            str(PROJECT_ROOT),
        ],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    domain = json.loads(
        (PROJECT_ROOT / "reports" / "context_domain_evidence_v1.json").read_text(
            encoding="utf-8",
        )
    )
    template = json.loads(
        (
            PROJECT_ROOT
            / "reports"
            / "customer_aggregate_context_evidence_template_v1.json"
        ).read_text(encoding="utf-8")
    )

    assert domain["domain_specific_profile_created"] is False
    assert domain["runtime_scoring_behavior_changed"] is False
    assert domain["low_support_domain_row_count"] == len(domain["domain_rows"])
    assert "education" in domain["domains_without_evidence"]
    notes = (
        PROJECT_ROOT / "docs" / "context_domain_profile_notes_v1.md"
    ).read_text(encoding="utf-8")
    assert "Requests without domain metadata continue to use the global default profile." in notes
    assert template["small_count_suppression_threshold"] == 10
