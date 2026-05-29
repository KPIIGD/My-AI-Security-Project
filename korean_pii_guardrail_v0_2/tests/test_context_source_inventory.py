from __future__ import annotations

import json
from pathlib import Path

from pii_guardrail.context_source_inventory import (
    CORE_ENTITY_GROUPS,
    build_context_source_inventory,
    render_context_source_inventory_markdown,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_source_inventory_defines_five_domain_plan_for_core_entities() -> None:
    payload = build_context_source_inventory(PROJECT_ROOT)
    by_entity = {
        row["entity_group"]: row for row in payload["core_entity_domain_plan"]
    }

    assert set(by_entity) == set(CORE_ENTITY_GROUPS)
    for row in by_entity.values():
        assert row["planned_domain_count"] >= 5
        assert row["meets_minimum_domain_plan"] is True
        assert row["current_score_tuning_status"] == "insufficient_current_data"


def test_source_inventory_is_raw_free_and_not_score_tuning() -> None:
    payload = build_context_source_inventory(PROJECT_ROOT)
    rendered = json.dumps(payload, ensure_ascii=False) + render_context_source_inventory_markdown(payload)

    assert payload["runtime_scoring_behavior_changed"] is False
    assert payload["score_delta_changed"] is False
    assert payload["context_rule_changed"] is False
    assert payload["public_corpus_used_for_score_tuning"] is False
    assert payload["raw_value_logged"] is False
    assert payload["raw_url_logged"] is False
    assert ("http" + "://") not in rendered
    assert ("https" + "://") not in rendered
    assert "@" not in rendered


def test_source_inventory_data_quality_gate_draft_is_measurable() -> None:
    payload = build_context_source_inventory(PROJECT_ROOT)
    gate = payload["data_quality_gate_draft"]
    criteria = gate["pass_criteria"]

    assert gate["status"] == "draft_ready"
    assert gate["score_tuning_allowed_by_this_phase"] is False
    assert criteria["raw_pii_leak_count"] == 0
    assert criteria["invalid_offset_count"] == 0
    assert criteria["min_domain_count_by_core_entity"] == 5
    assert criteria["max_single_domain_ratio"] == 0.35
    assert criteria["min_realistic_input_like_ratio"] == 0.7
