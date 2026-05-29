"""Phase 6 domain evidence and customer aggregate templates."""

from __future__ import annotations

import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .context_evidence import dumps_json


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DOMAIN_MINIMUM_SUPPORT = 50
CUSTOMER_AGGREGATE_SMALL_COUNT_THRESHOLD = 10
INITIAL_DOMAINS = (
    "generic",
    "ecommerce",
    "healthcare",
    "finance",
    "education",
    "enterprise_internal",
    "developer_docs",
)
_RAW_LIKE_PATTERNS = (
    re.compile(r"010-\d{3,4}-\d{4}"),
    re.compile(r"\d{6}-\d{7}"),
    re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
)


@dataclass(frozen=True)
class Phase6BuildResult:
    domain_evidence: dict[str, Any]
    domain_notes: str
    customer_template: dict[str, Any]
    customer_runbook: str


def build_phase6_reports(project_root: Path = PROJECT_ROOT) -> Phase6BuildResult:
    rule_evidence = json.loads(
        (project_root / "reports" / "context_rule_evidence_v1.json").read_text(
            encoding="utf-8",
        )
    )
    domain_evidence = build_context_domain_evidence(rule_evidence)
    customer_template = build_customer_aggregate_template()
    return Phase6BuildResult(
        domain_evidence=domain_evidence,
        domain_notes=render_domain_profile_notes(domain_evidence),
        customer_template=customer_template,
        customer_runbook=render_customer_side_runbook(customer_template),
    )


def build_context_domain_evidence(rule_evidence: dict[str, Any]) -> dict[str, Any]:
    domain_rows: dict[str, dict[str, Counter[str]]] = defaultdict(
        lambda: defaultdict(Counter)
    )
    domain_buckets: dict[tuple[str, str], set[str]] = defaultdict(set)
    for rule in rule_evidence["rules"]:
        for row in rule.get("domain_breakdown", []):
            domain = row["domain"]
            counter = domain_rows[domain][rule["rule_id"]]
            counter["fired_count"] += row["fired_count"]
            counter["tp_fired"] += row["tp_fired"]
            counter["fp_fired"] += row["fp_fired"]
            domain_buckets[(domain, rule["rule_id"])].add(row["bucket"])

    rows = []
    for domain in INITIAL_DOMAINS:
        for rule_id, counts in sorted(domain_rows.get(domain, {}).items()):
            fired_count = counts["fired_count"]
            rows.append(
                {
                    "domain": domain,
                    "rule_id": rule_id,
                    "buckets": sorted(domain_buckets[(domain, rule_id)]),
                    "fired_count": fired_count,
                    "tp_fired": counts["tp_fired"],
                    "fp_fired": counts["fp_fired"],
                    "precision_when_fired": _precision(
                        counts["tp_fired"],
                        counts["fp_fired"],
                    ),
                    "support_status": (
                        "sufficient"
                        if fired_count >= DOMAIN_MINIMUM_SUPPORT
                        else "insufficient_support"
                    ),
                    "recommendation": (
                        "report_only_collect_more_evidence"
                        if fired_count < DOMAIN_MINIMUM_SUPPORT
                        else "review_before_domain_profile"
                    ),
                }
            )

    low_support_count = sum(
        1 for row in rows if row["support_status"] == "insufficient_support"
    )
    payload = {
        "report_type": "ContextDomainEvidence",
        "version": "v0.2-single-turn",
        "phase": "Execution Phase 6. Domain and Aggregate Follow-Up",
        "runtime_scoring_behavior_changed": False,
        "score_delta_changed": False,
        "domain_specific_profile_created": False,
        "default_profile_decision": "keep_global_default",
        "minimum_domain_support": DOMAIN_MINIMUM_SUPPORT,
        "public_corpus_used_for_score_tuning": False,
        "domain_rows": rows,
        "domain_summary": _domain_summary(rows),
        "domains_without_evidence": [
            domain for domain in INITIAL_DOMAINS if domain not in domain_rows
        ],
        "low_support_domain_row_count": low_support_count,
        "raw_pii_safety": {
            "raw_value_logged": False,
            "report_raw_text_leak_count": _raw_like_count(rows),
            "status": "pass" if _raw_like_count(rows) == 0 else "fail",
        },
    }
    payload["status"] = (
        "pass"
        if payload["raw_pii_safety"]["status"] == "pass"
        and payload["domain_specific_profile_created"] is False
        else "fail"
    )
    return payload


def build_customer_aggregate_template() -> dict[str, Any]:
    template = {
        "report_type": "CustomerAggregateContextEvidenceTemplate",
        "version": "v0.2-single-turn",
        "phase": "Execution Phase 6. Domain and Aggregate Follow-Up",
        "evidence_role": "customer_side_aggregate_only",
        "public_corpus_used_for_score_tuning": False,
        "raw_text_allowed": False,
        "raw_url_allowed": False,
        "raw_candidate_value_allowed": False,
        "small_count_suppression_threshold": CUSTOMER_AGGREGATE_SMALL_COUNT_THRESHOLD,
        "required_fields": [
            "deployment_id_hash",
            "config_version",
            "dataset_window",
            "domain",
            "rule_id",
            "entity_type",
            "fired_count",
            "action_mask_count",
            "action_pass_count",
            "review_tp_count",
            "review_fp_count",
            "raw_value_logged",
        ],
        "suppression_rule": (
            "omit or bucket rows where fired_count, review_tp_count, or "
            "review_fp_count is below the threshold"
        ),
        "example_row": {
            "deployment_id_hash": "sha256:aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa",
            "config_version": "scoring-v0.2.1",
            "dataset_window": "2026-W22",
            "domain": "ecommerce",
            "rule_id": "context.boost.field_label_phone",
            "entity_type": "PHONE_MOBILE",
            "fired_count": 1280,
            "action_mask_count": 1270,
            "action_pass_count": 10,
            "review_tp_count": 120,
            "review_fp_count": 10,
            "raw_value_logged": False,
        },
        "disallowed_fields": [
            "raw_text",
            "raw_url",
            "raw_candidate_value",
            "span_text",
            "case_text",
            "reversible_hash_map",
        ],
    }
    template["raw_pii_safety"] = {
        "raw_value_logged": False,
        "template_raw_like_match_count": _raw_like_count(template),
        "status": "pass" if _raw_like_count(template) == 0 else "fail",
    }
    template["status"] = "pass" if template["raw_pii_safety"]["status"] == "pass" else "fail"
    return template


def render_domain_profile_notes(domain_evidence: dict[str, Any]) -> str:
    lines = [
        "# Context Domain Profile Notes v1",
        "",
        "- phase: `Execution Phase 6. Domain and Aggregate Follow-Up`",
        "- default_profile_decision: `keep_global_default`",
        "- domain_specific_profile_created: `false`",
        "- request_time_domain_required: `false`",
        "- fallback_behavior: global default context profile",
        "",
        "Domain-specific rows are report-only in v0.2. Low-support rows are not tuned.",
        "",
        "| Domain | Rule Rows | Low Support Rows | Recommendation |",
        "|---|---:|---:|---|",
    ]
    for domain, row in domain_evidence["domain_summary"].items():
        lines.append(
            "| {domain} | {rules} | {low} | {rec} |".format(
                domain=domain,
                rules=row["rule_row_count"],
                low=row["low_support_row_count"],
                rec=row["recommendation"],
            )
        )
    missing = ", ".join(domain_evidence["domains_without_evidence"]) or "none"
    lines.extend(
        [
            "",
            "## Fallback",
            "",
            f"Domains without enough evidence: `{missing}`",
            "",
            "Requests without domain metadata continue to use the global default profile.",
        ]
    )
    return "\n".join(lines) + "\n"


def render_customer_side_runbook(template: dict[str, Any]) -> str:
    return "\n".join(
        [
            "# Customer-Side Context Calibration Runbook v1",
            "",
            "Run evidence collection inside the customer environment and export aggregates only.",
            "",
            "Required controls:",
            "",
            "- Use a versioned scoring config id.",
            "- Hash deployment identifiers before export.",
            "- Export counts by domain, rule id, entity type, action, and optional review outcome.",
            "- Suppress small-count rows below the configured threshold.",
            "- Do not export raw text, raw URLs, span text, candidate values, or reversible maps.",
            "- Treat received aggregates as evidence for review, not automatic score changes.",
            "",
            f"Small-count threshold: `{template['small_count_suppression_threshold']}`",
            "",
            "Central analysis may consume only the JSON template fields in the companion report.",
            "",
        ]
    )


def write_phase6_reports(
    project_root: Path = PROJECT_ROOT,
) -> tuple[Phase6BuildResult, dict[str, Path]]:
    result = build_phase6_reports(project_root)
    paths = {
        "domain_evidence_json": project_root / "reports" / "context_domain_evidence_v1.json",
        "domain_notes_md": project_root / "docs" / "context_domain_profile_notes_v1.md",
        "customer_template_json": (
            project_root / "reports" / "customer_aggregate_context_evidence_template_v1.json"
        ),
        "customer_runbook_md": (
            project_root / "docs" / "customer_side_context_calibration_runbook_v1.md"
        ),
    }
    paths["domain_evidence_json"].write_text(
        dumps_json(result.domain_evidence),
        encoding="utf-8",
    )
    paths["domain_notes_md"].write_text(result.domain_notes, encoding="utf-8")
    paths["customer_template_json"].write_text(
        dumps_json(result.customer_template),
        encoding="utf-8",
    )
    paths["customer_runbook_md"].write_text(result.customer_runbook, encoding="utf-8")
    return result, paths


def _domain_summary(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    by_domain: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_domain[row["domain"]].append(row)
    return {
        domain: {
            "rule_row_count": len(domain_rows),
            "total_fired_count": sum(row["fired_count"] for row in domain_rows),
            "low_support_row_count": sum(
                1
                for row in domain_rows
                if row["support_status"] == "insufficient_support"
            ),
            "recommendation": "keep_global_default_collect_more_evidence",
        }
        for domain, domain_rows in sorted(by_domain.items())
    }


def _precision(tp_count: int, fp_count: int) -> float | None:
    denominator = tp_count + fp_count
    if denominator == 0:
        return None
    return round(tp_count / denominator, 6)


def _raw_like_count(payload: object) -> int:
    serialized = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return sum(len(pattern.findall(serialized)) for pattern in _RAW_LIKE_PATTERNS)
