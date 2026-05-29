from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from pii_guardrail.context_anchor_collector import context_anchor_windows_jsonl
from pii_guardrail.context_anchor_manifest import (
    build_context_anchor_manifest,
    render_manifest_yaml,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]
CORE_ENTITY_TO_ANCHOR = {
    "PERSON_NAME": ("PERSON_NAME", "korean_name_3_syllable"),
    "PHONE": ("PHONE_MOBILE", "mobile_phone_shape"),
    "EMAIL": ("EMAIL", "email_shape"),
    "ADDRESS": ("ADDRESS_FULL", "road_address_shape"),
    "BANK_ACCOUNT": ("BANK_ACCOUNT", "bank_account_shape"),
    "REGISTRATION_IDENTIFIER": ("RRN", "rrn_shape"),
}
REALISTIC_DOMAINS = (
    "customer_support",
    "ecommerce",
    "healthcare",
    "finance",
    "education",
    "public_services",
)


def test_context_anchor_manifest_passes_diverse_raw_free_fixture() -> None:
    rows = _diverse_rows()
    manifest = build_context_anchor_manifest(
        anchor_input_path=PROJECT_ROOT
        / "data"
        / "context_corpus"
        / "context_anchor_windows_v1.jsonl",
        rows=rows,
    )

    assert manifest["data_quality_gate"]["status"] == "pass"
    assert manifest["score_tuning_allowed_by_this_manifest"] is False
    assert manifest["raw_free_scan"]["raw_pii_leak_count"] == 0
    assert manifest["measurements"]["duplicate_anchor_window_ratio"] == 0.0
    assert manifest["measurements"]["material_ratios"]["realistic_input_like"] == 1.0
    assert all(
        count >= 5
        for count in manifest["measurements"][
            "domain_count_by_core_entity"
        ].values()
    )
    assert all(
        ratio <= 0.35
        for ratio in manifest["measurements"][
            "max_single_domain_ratio_by_core_entity"
        ].values()
    )


def test_context_anchor_manifest_fails_missing_or_single_domain_data() -> None:
    missing_manifest = build_context_anchor_manifest(
        anchor_input_path=PROJECT_ROOT
        / "data"
        / "context_corpus"
        / "missing_context_anchor_windows_v1.jsonl"
    )
    assert missing_manifest["data_quality_gate"]["status"] == "fail"
    assert "needs_anchor_corpus" in missing_manifest["data_quality_gate"][
        "failure_verdicts"
    ]

    row = _anchor_row(
        core_entity="PERSON_NAME",
        domain="customer_support",
        label="true_pii",
        unique="single-domain",
    )
    single_domain_manifest = build_context_anchor_manifest(
        anchor_input_path=PROJECT_ROOT
        / "data"
        / "context_corpus"
        / "context_anchor_windows_v1.jsonl",
        rows=[row],
    )
    assert single_domain_manifest["data_quality_gate"]["status"] == "fail"
    assert "needs_more_data" in single_domain_manifest["data_quality_gate"][
        "failure_verdicts"
    ]
    assert "needs_domain_split" in single_domain_manifest["data_quality_gate"][
        "failure_verdicts"
    ]


def test_context_anchor_manifest_detects_duplicates_and_unknown_ratio() -> None:
    rows = _diverse_rows()
    for row in rows[:10]:
        row["label"] = "unknown"
    rows.extend(dict(rows[0]) for _ in range(3))

    manifest = build_context_anchor_manifest(
        anchor_input_path=PROJECT_ROOT
        / "data"
        / "context_corpus"
        / "context_anchor_windows_v1.jsonl",
        rows=rows,
    )

    assert manifest["data_quality_gate"]["status"] == "fail"
    assert "needs_deduplication" in manifest["data_quality_gate"]["failure_verdicts"]
    assert "needs_labels" in manifest["data_quality_gate"]["failure_verdicts"]


def test_context_anchor_manifest_render_is_raw_free_json_compatible_yaml() -> None:
    rows = _diverse_rows()
    rendered = render_manifest_yaml(
        build_context_anchor_manifest(
            anchor_input_path=PROJECT_ROOT
            / "data"
            / "context_corpus"
            / "context_anchor_windows_v1.jsonl",
            rows=rows,
        )
    )

    parsed = json.loads(rendered)
    assert parsed["manifest_type"] == "ContextAnchorWindowsManifest"
    assert ("http" + "://") not in rendered
    assert ("https" + "://") not in rendered
    assert "@" not in rendered


def test_context_anchor_manifest_cli_writes_pass_manifest(tmp_path: Path) -> None:
    anchor_input = tmp_path / "context_anchor_windows_v1.jsonl"
    output = tmp_path / "context_anchor_windows_manifest_v1.yaml"
    anchor_input.write_text(
        context_anchor_windows_jsonl(_diverse_rows()),
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(PROJECT_ROOT / "scripts" / "build_context_anchor_manifest.py"),
            "--anchor-input",
            str(anchor_input),
            "--output",
            str(output),
        ],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=True,
    )

    payload = json.loads(output.read_text(encoding="utf-8"))
    assert payload["data_quality_gate"]["status"] == "pass"
    assert "context_anchor_manifest_status=pass" in result.stdout


def _diverse_rows() -> list[dict]:
    rows: list[dict] = []
    for core_entity in CORE_ENTITY_TO_ANCHOR:
        for index, domain in enumerate(REALISTIC_DOMAINS):
            rows.append(
                _anchor_row(
                    core_entity=core_entity,
                    domain=domain,
                    label="true_pii" if index % 2 == 0 else "non_pii",
                    unique=f"{core_entity.lower()}-{domain}",
                )
            )
    return rows


def _anchor_row(
    *,
    core_entity: str,
    domain: str,
    label: str,
    unique: str,
) -> dict:
    anchor_entity, anchor_shape = CORE_ENTITY_TO_ANCHOR[core_entity]
    return {
        "schema_version": "context_anchor_windows_v1",
        "anchor_entity": anchor_entity,
        "anchor_shape": anchor_shape,
        "anchor_source": "regex",
        "label": label,
        "source_domain": domain,
        "material_class": "realistic_input_like",
        "distance_bucket": "within_2_tokens",
        "left_ngrams": _ngram_windows(f"left-{unique}"),
        "right_ngrams": _ngram_windows(f"right-{unique}"),
        "contains_raw_pii": False,
        "raw_value_logged": False,
        "raw_url_logged": False,
        "page_body_stored": False,
        "candidate_value_stored": False,
        "evidence_role": "anchor_context_only_not_score_tuning",
    }


def _ngram_windows(token: str) -> dict:
    return {
        "within_1_token": {
            "unigrams": [token],
            "bigrams": [],
            "trigrams": [],
        },
        "within_2_tokens": {
            "unigrams": [token, "context"],
            "bigrams": [f"{token} context"],
            "trigrams": [],
        },
        "within_5_tokens": {
            "unigrams": [token, "context", "field"],
            "bigrams": [f"{token} context", "context field"],
            "trigrams": [f"{token} context field"],
        },
    }
