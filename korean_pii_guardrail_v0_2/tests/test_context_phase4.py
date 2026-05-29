from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from pii_guardrail.context_phase4 import (
    _select_conservative_candidate,
    _rewrite_context_delta,
    build_context_delta_sweep_v1,
    build_context_rule_evidence_v1,
    build_phase4_reports,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_phase4_rule_evidence_has_lr_bands_and_raw_safety() -> None:
    payload = build_context_rule_evidence_v1(PROJECT_ROOT)
    by_rule = {row["rule_id"]: row for row in payload["rules"]}

    assert payload["report_type"] == "ContextRuleEvidence"
    assert payload["runtime_scoring_behavior_changed"] is False
    assert payload["score_delta_changed"] is False
    assert payload["raw_pii_safety"]["status"] == "pass"
    phone_metrics = by_rule["context.boost.field_label_phone"]["candidate_metrics"]
    assert phone_metrics["likelihood_ratio"] is not None
    assert phone_metrics["precision_lift"] is not None
    assert (
        phone_metrics["target_baseline_precision"]
        is not None
    )
    assert by_rule["context.boost.field_label_phone"]["direction_band"] != "insufficient_support"
    assert "domain_breakdown" in by_rule["context.boost.field_label_phone"]


def test_phase4_delta_sweep_does_not_modify_runtime_config() -> None:
    before = (PROJECT_ROOT / "configs" / "scoring.yaml").read_text(encoding="utf-8")
    evidence = build_context_rule_evidence_v1(PROJECT_ROOT)
    sweep = build_context_delta_sweep_v1(PROJECT_ROOT, evidence)
    after = (PROJECT_ROOT / "configs" / "scoring.yaml").read_text(encoding="utf-8")

    assert before == after
    assert sweep["runtime_scoring_behavior_changed"] is False
    assert sweep["score_delta_changed"] is False
    assert sweep["public_corpus_used_for_score_tuning"] is False
    for row in sweep["rules"]:
        evidence_row = next(
            item for item in evidence["rules"] if item["rule_id"] == row["rule_id"]
        )
        assert evidence_row["verdict"] == "tune_magnitude"
        assert "candidate_results" in row
        assert row["selected_delta"] in row["candidate_grid"]
        for candidate in row["candidate_results"]:
            assert "impact_deltas_by_split" in candidate
            assert "candidate_level" in candidate["impact_deltas_by_split"]["dev"]
            assert "action_level" in candidate["impact_deltas_by_split"]["dev"]
            assert (
                "actionable_high_risk_recall_delta"
                in candidate["impact_deltas_by_split"]["dev"]["action_level"]
            )


def test_phase4_policy_only_rules_are_not_swept() -> None:
    evidence = build_context_rule_evidence_v1(PROJECT_ROOT)
    sweep = build_context_delta_sweep_v1(PROJECT_ROOT, evidence)
    swept = {row["rule_id"] for row in sweep["rules"]}
    unchanged = {row["rule_id"]: row["reason"] for row in sweep["unchanged_rule_reasons"]}

    assert "context.composite.PERSON_NAME" not in swept
    assert unchanged["context.composite.PERSON_NAME"] == "policy_only_rule"
    assert "context.boost.bank_cooccur" not in swept
    assert (
        unchanged["context.boost.bank_cooccur"]
        == "insufficient_support_or_direction_review"
    )


def test_phase4_conservative_selector_is_noop_not_optimization() -> None:
    candidate_rows = [
        {"candidate_delta": 0.10, "passes_release_constraints": True},
        {"candidate_delta": 0.25, "passes_release_constraints": True},
        {"candidate_delta": 0.30, "passes_release_constraints": True},
    ]

    selected = _select_conservative_candidate(
        current_delta=0.25,
        candidate_rows=candidate_rows,
    )

    assert selected == 0.25


def test_phase4_reports_are_raw_text_free() -> None:
    result = build_phase4_reports(PROJECT_ROOT)
    serialized = (
        json.dumps(result.rule_evidence, ensure_ascii=False)
        + json.dumps(result.delta_sweep, ensure_ascii=False)
        + result.tuning_markdown
        + result.policy_markdown
    )
    blocked_fragments = (
        "010-" + "4567-" + "8901",
        "920303-" + "3456780",
        "member03" + "@example.test",
    )

    for fragment in blocked_fragments:
        assert fragment not in serialized
    assert result.rule_evidence["raw_pii_safety"]["status"] == "pass"


def test_phase4_cli_writes_expected_reports(tmp_path: Path) -> None:
    # The script writes to the project reports directory by design. This test
    # exercises the CLI and then checks the expected raw-safe report shapes.
    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "analyze_context_rule_metrics.py"),
            "--project-root",
            str(PROJECT_ROOT),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    assert "phase4_status=pass" in result.stdout
    for path in (
        PROJECT_ROOT / "reports" / "context_rule_evidence_v1.json",
        PROJECT_ROOT / "reports" / "context_delta_sweep_v1.json",
        PROJECT_ROOT / "reports" / "context_score_tuning_v1.md",
        PROJECT_ROOT / "reports" / "context_policy_interaction_v1.md",
    ):
        assert path.exists()
    tuning = (
        PROJECT_ROOT / "reports" / "context_score_tuning_v1.md"
    ).read_text(encoding="utf-8")
    assert "Delta Sweep Summary" in tuning
    assert "Precision Lift" in tuning


def test_rewrite_context_delta_updates_only_target_rule(tmp_path: Path) -> None:
    scoring = tmp_path / "scoring.yaml"
    scoring.write_text(
        "context_boosts:\n  field_label_phone: 0.15\n  field_label_name: 0.25\n",
        encoding="utf-8",
    )

    _rewrite_context_delta(
        scoring,
        section="context_boosts",
        rule_name="field_label_phone",
        new_delta=0.2,
    )

    assert scoring.read_text(encoding="utf-8") == (
        "context_boosts:\n  field_label_phone: 0.20\n  field_label_name: 0.25\n"
    )
