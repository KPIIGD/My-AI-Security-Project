from __future__ import annotations

import json
from pathlib import Path

from pii_guardrail.context_evidence import (
    DatasetSpec,
    build_context_rule_inventory,
    build_existing_context_rule_evidence,
    dumps_json,
    render_existing_evidence_markdown,
    render_inventory_markdown,
    update_evidence_payload_safety,
)
from pii_guardrail.dictionary_loader import (
    load_composite_upgrades,
    load_context_boosts,
    load_context_penalties,
)
from pii_guardrail.evaluation_harness import count_report_raw_text_leaks


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_context_rule_inventory_lists_every_configured_context_reason_code() -> None:
    payload = build_context_rule_inventory(PROJECT_ROOT)
    rule_ids = {row["rule_id"] for row in payload["rules"]}

    for rule_name in load_context_boosts(PROJECT_ROOT / "configs" / "scoring.yaml"):
        assert f"context.boost.{rule_name}" in rule_ids
    for rule_name in load_context_penalties(PROJECT_ROOT / "configs" / "scoring.yaml"):
        assert f"context.penalty.{rule_name}" in rule_ids
    for key in load_composite_upgrades(PROJECT_ROOT / "configs" / "scoring.yaml"):
        for entity in key:
            assert f"context.composite.{entity}" in rule_ids

    assert payload["runtime_scoring_behavior_changed"] is False
    assert payload["raw_value_logged"] is False
    assert "candidate_level" in payload["rules"][0]["metric_scopes"]
    assert "actionable_level" in payload["rules"][0]["metric_scopes"]


def test_context_rule_inventory_markdown_is_raw_text_free_shape() -> None:
    payload = build_context_rule_inventory(PROJECT_ROOT)
    markdown = render_inventory_markdown(payload)

    assert "Context Rule Inventory" in markdown
    assert "context.boost.field_label_name" in markdown
    assert "raw span text" in markdown


def test_existing_context_rule_evidence_is_raw_text_free(tmp_path: Path) -> None:
    raw_text = "고객명 하늘, 연락처 010-1111-2222."
    raw_phone = "010-1111-2222"
    dataset = tmp_path / "phase1_context.jsonl"
    dataset.write_text(
        json.dumps(
            {
                "id": "case-phase1-context",
                "text": raw_text,
                "labels": [
                    {
                        "start": 4,
                        "end": 6,
                        "entity_type": "PERSON_NAME",
                        "risk_level": "P1",
                    },
                    {
                        "start": 12,
                        "end": 25,
                        "entity_type": "PHONE_MOBILE",
                        "risk_level": "P1",
                    },
                ],
                "tags": ["context", "single_turn_composite"],
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    result = build_existing_context_rule_evidence(
        PROJECT_ROOT,
        dataset_specs=(DatasetSpec("phase1_context", dataset),),
        minimum_support=1,
    )
    markdown = render_existing_evidence_markdown(result.payload)
    json_text = dumps_json(result.payload)
    update_evidence_payload_safety(result.payload, result.cases, [json_text, markdown])
    serialized = dumps_json(result.payload)

    assert result.payload["raw_pii_safety"]["status"] == "pass"
    assert result.payload["raw_pii_safety"]["report_raw_text_leak_count"] == 0
    assert raw_text not in serialized
    assert raw_phone not in serialized
    assert raw_text not in markdown
    assert raw_phone not in markdown
    assert count_report_raw_text_leaks([serialized, markdown], result.cases) == 0


def test_existing_context_rule_evidence_distinguishes_evidence_levels(tmp_path: Path) -> None:
    dataset = tmp_path / "phase1_context.jsonl"
    dataset.write_text(
        json.dumps(
            {
                "id": "case-phase1-context",
                "text": "고객명 하늘, 연락처 010-1111-2222.",
                "labels": [
                    {
                        "start": 4,
                        "end": 6,
                        "entity_type": "PERSON_NAME",
                        "risk_level": "P1",
                    },
                    {
                        "start": 12,
                        "end": 25,
                        "entity_type": "PHONE_MOBILE",
                        "risk_level": "P1",
                    },
                ],
                "tags": ["context", "single_turn_composite"],
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    result = build_existing_context_rule_evidence(
        PROJECT_ROOT,
        dataset_specs=(DatasetSpec("phase1_context", dataset),),
        minimum_support=1,
    )
    by_rule = {row["rule_id"]: row for row in result.payload["rules"]}
    name_rule = by_rule["context.boost.field_label_name"]
    composite_rule = by_rule["context.composite.PHONE_MOBILE"]

    assert name_rule["fired_count"] >= 1
    assert "candidate_metrics" in name_rule
    assert "actionable_metrics" in name_rule
    assert name_rule["evidence_levels"]["magnitude_evidence"] == "not_evaluated_phase_1"
    assert name_rule["suggested_delta"] is None
    assert composite_rule["verdict"] == "policy_only_rule"
    assert result.payload["score_delta_changed"] is False
