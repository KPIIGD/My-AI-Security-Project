"""Source and domain inventory for M4 context recalibration.

The inventory is planning evidence only. It stores source categories, source
types, entity coverage plans, and aggregate counts from any existing safe
context windows. It does not store raw URLs, page bodies, candidate values, or
raw span text.
"""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_VERSION = "v0.2-single-turn"

CORE_ENTITY_GROUPS = (
    "PERSON_NAME",
    "PHONE",
    "EMAIL",
    "ADDRESS",
    "BANK_ACCOUNT",
    "REGISTRATION_IDENTIFIER",
)

MATERIAL_CLASSES = (
    "realistic_input_like",
    "general_web_or_explanatory",
    "example_or_sample",
)

SOURCE_DOMAIN_TAXONOMY: tuple[dict[str, Any], ...] = (
    {
        "source_domain": "customer_support",
        "material_class": "realistic_input_like",
        "description": "support, contact, inquiry, and issue-resolution guidance",
    },
    {
        "source_domain": "ecommerce",
        "material_class": "realistic_input_like",
        "description": "ordering, delivery, refund, account, and checkout flows",
    },
    {
        "source_domain": "healthcare",
        "material_class": "realistic_input_like",
        "description": "appointment, reception, patient, and medical-record guidance",
    },
    {
        "source_domain": "finance",
        "material_class": "realistic_input_like",
        "description": "deposit, transfer, refund, account, and identity guidance",
    },
    {
        "source_domain": "education",
        "material_class": "realistic_input_like",
        "description": "school, application, student, and registration guidance",
    },
    {
        "source_domain": "public_services",
        "material_class": "realistic_input_like",
        "description": "public institution application and civil-service guidance",
    },
    {
        "source_domain": "enterprise_internal",
        "material_class": "realistic_input_like",
        "description": "employee, HR, internal request, and organization workflows",
    },
    {
        "source_domain": "developer_docs",
        "material_class": "general_web_or_explanatory",
        "description": "technical examples, logs, schemas, and API documentation",
    },
    {
        "source_domain": "general_web",
        "material_class": "general_web_or_explanatory",
        "description": "general explanatory or policy-like text",
    },
    {
        "source_domain": "sample_forms",
        "material_class": "example_or_sample",
        "description": "safe sample forms and synthetic templates",
    },
)

SOURCE_TYPE_INVENTORY: tuple[dict[str, Any], ...] = (
    {
        "source_type": "customer_support_help",
        "source_domain": "customer_support",
        "collector_supported_currently": False,
    },
    {
        "source_type": "ecommerce_help",
        "source_domain": "ecommerce",
        "collector_supported_currently": True,
    },
    {
        "source_type": "healthcare_guide",
        "source_domain": "healthcare",
        "collector_supported_currently": True,
    },
    {
        "source_type": "finance_guide",
        "source_domain": "finance",
        "collector_supported_currently": False,
    },
    {
        "source_type": "education_application",
        "source_domain": "education",
        "collector_supported_currently": True,
    },
    {
        "source_type": "institution_application",
        "source_domain": "public_services",
        "collector_supported_currently": True,
    },
    {
        "source_type": "enterprise_internal",
        "source_domain": "enterprise_internal",
        "collector_supported_currently": True,
    },
    {
        "source_type": "developer_docs",
        "source_domain": "developer_docs",
        "collector_supported_currently": True,
    },
    {
        "source_type": "privacy_policy",
        "source_domain": "general_web",
        "collector_supported_currently": True,
    },
    {
        "source_type": "synthetic_safe_template",
        "source_domain": "sample_forms",
        "collector_supported_currently": True,
    },
)

CORE_ENTITY_DOMAIN_PLAN: dict[str, tuple[str, ...]] = {
    "PERSON_NAME": (
        "customer_support",
        "ecommerce",
        "healthcare",
        "education",
        "enterprise_internal",
        "public_services",
    ),
    "PHONE": (
        "customer_support",
        "ecommerce",
        "healthcare",
        "finance",
        "public_services",
        "developer_docs",
    ),
    "EMAIL": (
        "customer_support",
        "ecommerce",
        "education",
        "enterprise_internal",
        "developer_docs",
        "general_web",
    ),
    "ADDRESS": (
        "ecommerce",
        "healthcare",
        "finance",
        "education",
        "public_services",
        "sample_forms",
    ),
    "BANK_ACCOUNT": (
        "customer_support",
        "ecommerce",
        "finance",
        "public_services",
        "enterprise_internal",
        "sample_forms",
    ),
    "REGISTRATION_IDENTIFIER": (
        "healthcare",
        "finance",
        "education",
        "public_services",
        "enterprise_internal",
        "sample_forms",
    ),
}

ENTITY_TO_GROUP = {
    "PERSON_NAME": "PERSON_NAME",
    "PHONE_MOBILE": "PHONE",
    "PHONE_LANDLINE": "PHONE",
    "EMAIL": "EMAIL",
    "ADDRESS_FULL": "ADDRESS",
    "ADDRESS_UNIT": "ADDRESS",
    "BANK_ACCOUNT": "BANK_ACCOUNT",
    "RRN": "REGISTRATION_IDENTIFIER",
    "FRN": "REGISTRATION_IDENTIFIER",
    "PASSPORT": "REGISTRATION_IDENTIFIER",
    "DRIVER_LICENSE": "REGISTRATION_IDENTIFIER",
    "BUSINESS_REG_NO": "REGISTRATION_IDENTIFIER",
    "CORPORATE_REG_NO": "REGISTRATION_IDENTIFIER",
}


def build_context_source_inventory(project_root: Path = PROJECT_ROOT) -> dict[str, Any]:
    rows = _load_existing_context_window_rows(
        project_root / "data" / "context_corpus" / "context_windows_v1.jsonl"
    )
    source_type_to_domain = {
        row["source_type"]: row["source_domain"] for row in SOURCE_TYPE_INVENTORY
    }
    domain_to_material = {
        row["source_domain"]: row["material_class"] for row in SOURCE_DOMAIN_TAXONOMY
    }

    by_source_type = Counter(str(row.get("source_type", "unknown")) for row in rows)
    by_domain = Counter(
        source_type_to_domain.get(source_type, "unknown")
        for source_type in by_source_type
        for _ in range(by_source_type[source_type])
    )
    by_material_class = Counter(
        domain_to_material.get(domain, "unknown")
        for domain in by_domain
        for _ in range(by_domain[domain])
    )
    unique_url_hashes_by_domain: dict[str, set[str]] = defaultdict(set)
    domains_by_entity_group: dict[str, set[str]] = defaultdict(set)
    for row in rows:
        source_type = str(row.get("source_type", "unknown"))
        domain = source_type_to_domain.get(source_type, "unknown")
        url_hash = row.get("url_hash")
        if isinstance(url_hash, str):
            unique_url_hashes_by_domain[domain].add(url_hash)
        for entity in row.get("entity_hints", []):
            group = ENTITY_TO_GROUP.get(str(entity))
            if group:
                domains_by_entity_group[group].add(domain)

    domain_plan = [
        {
            "entity_group": entity_group,
            "planned_source_domains": list(domains),
            "planned_domain_count": len(domains),
            "meets_minimum_domain_plan": len(domains) >= 5,
            "current_observed_domains": sorted(domains_by_entity_group[entity_group]),
            "current_observed_domain_count": len(domains_by_entity_group[entity_group]),
            "current_score_tuning_status": "insufficient_current_data",
        }
        for entity_group, domains in sorted(CORE_ENTITY_DOMAIN_PLAN.items())
    ]
    return {
        "report_type": "ContextSourceInventory",
        "version": REPORT_VERSION,
        "stage": "1.1 source inventory",
        "runtime_scoring_behavior_changed": False,
        "score_delta_changed": False,
        "context_rule_changed": False,
        "public_corpus_used_for_score_tuning": False,
        "raw_value_logged": False,
        "raw_url_logged": False,
        "page_body_stored": False,
        "source_domain_taxonomy": list(SOURCE_DOMAIN_TAXONOMY),
        "source_type_inventory": list(SOURCE_TYPE_INVENTORY),
        "core_entity_domain_plan": domain_plan,
        "current_safe_context_window_summary": {
            "row_count": len(rows),
            "by_source_type": dict(sorted(by_source_type.items())),
            "by_source_domain": dict(sorted(by_domain.items())),
            "by_material_class": dict(sorted(by_material_class.items())),
            "unique_url_hash_count_by_domain": {
                domain: len(hashes)
                for domain, hashes in sorted(unique_url_hashes_by_domain.items())
            },
            "current_data_quality_status": "insufficient_for_score_tuning",
        },
        "data_quality_gate_draft": _data_quality_gate_draft(),
        "stage_1_1_exit_gate": {
            "source_domain_taxonomy_defined": True,
            "core_entities_have_five_domain_plan": all(
                len(domains) >= 5 for domains in CORE_ENTITY_DOMAIN_PLAN.values()
            ),
            "realistic_input_like_ratio_measurable": True,
            "single_domain_over_35_percent_not_allowed_for_score_tuning": True,
            "score_tuning_approved": False,
        },
    }


def render_context_source_inventory_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Context Source Inventory v1",
        "",
        "- stage: `1.1 source inventory`",
        "- evidence_role: `source_domain_inventory_only`",
        "- runtime_scoring_behavior_changed: `false`",
        "- score_delta_changed: `false`",
        "- context_rule_changed: `false`",
        "- public_corpus_used_for_score_tuning: `false`",
        "- raw_value_logged: `false`",
        "- raw_url_logged: `false`",
        "",
        "## Source Domains",
        "",
        "| Domain | Material Class | Description |",
        "|---|---|---|",
    ]
    for row in payload["source_domain_taxonomy"]:
        lines.append(
            "| {domain} | {material} | {description} |".format(
                domain=row["source_domain"],
                material=row["material_class"],
                description=row["description"],
            )
        )
    lines.extend(
        [
            "",
            "## Source Types",
            "",
            "| Source Type | Domain | Collector Supported |",
            "|---|---|---:|",
        ]
    )
    for row in payload["source_type_inventory"]:
        lines.append(
            "| {source_type} | {domain} | {supported} |".format(
                source_type=row["source_type"],
                domain=row["source_domain"],
                supported=str(row["collector_supported_currently"]).lower(),
            )
        )
    lines.extend(
        [
            "",
            "## Core Entity Domain Plan",
            "",
            "| Entity Group | Planned Domains | Current Observed Domains | Current Status |",
            "|---|---:|---:|---|",
        ]
    )
    for row in payload["core_entity_domain_plan"]:
        lines.append(
            "| {entity} | {planned} | {observed} | {status} |".format(
                entity=row["entity_group"],
                planned=row["planned_domain_count"],
                observed=row["current_observed_domain_count"],
                status=row["current_score_tuning_status"],
            )
        )
    summary = payload["current_safe_context_window_summary"]
    lines.extend(
        [
            "",
            "## Current Safe Context Window Summary",
            "",
            f"- row_count: `{summary['row_count']}`",
            f"- current_data_quality_status: `{summary['current_data_quality_status']}`",
            "",
            "Current rows remain coverage evidence only. They are not sufficient for score tuning.",
            "",
            "## Data Quality Gate Draft",
            "",
            "| Measurement | Pass Criteria |",
            "|---|---|",
        ]
    )
    for key, value in payload["data_quality_gate_draft"]["pass_criteria"].items():
        lines.append(f"| `{key}` | `{value}` |")
    return "\n".join(lines) + "\n"


def write_context_source_inventory_reports(
    project_root: Path = PROJECT_ROOT,
) -> tuple[dict[str, Any], dict[str, Path]]:
    payload = build_context_source_inventory(project_root)
    markdown = render_context_source_inventory_markdown(payload)
    paths = {
        "json": project_root / "reports" / "context_source_inventory_v1.json",
        "md": project_root / "reports" / "context_source_inventory_v1.md",
    }
    paths["json"].write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    paths["md"].write_text(markdown, encoding="utf-8")
    return payload, paths


def _data_quality_gate_draft() -> dict[str, Any]:
    return {
        "status": "draft_ready",
        "score_tuning_allowed_by_this_phase": False,
        "measurements": [
            "raw_pii_leak_count",
            "invalid_offset_count",
            "domain_count_by_core_entity",
            "max_single_domain_ratio_by_entity",
            "realistic_input_like_ratio",
            "general_web_or_explanatory_ratio",
            "example_or_sample_document_ratio",
            "duplicate_anchor_window_ratio",
            "unknown_label_ratio",
        ],
        "pass_criteria": {
            "raw_pii_leak_count": 0,
            "invalid_offset_count": 0,
            "min_domain_count_by_core_entity": 5,
            "max_single_domain_ratio": 0.35,
            "min_realistic_input_like_ratio": 0.7,
            "max_general_web_or_explanatory_ratio": 0.3,
            "max_example_or_sample_document_ratio": 0.15,
            "max_duplicate_anchor_window_ratio": 0.05,
            "max_unknown_label_ratio_when_labels_present": 0.15,
        },
        "failure_verdicts": [
            "rejected_data_quality_gate",
            "evidence_backlog",
            "needs_more_data",
            "needs_domain_split",
        ],
    }


def _load_existing_context_window_rows(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if isinstance(row, dict):
            rows.append(row)
    return rows
