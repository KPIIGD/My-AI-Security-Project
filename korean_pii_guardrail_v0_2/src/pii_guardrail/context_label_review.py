"""Phase 6 draft label review packet and label quality gate."""

from __future__ import annotations

import datetime
import hashlib
import json
import math
from collections import Counter, defaultdict, deque
from pathlib import Path
from typing import Any, Iterable

from .context_anchor_collector import (
    annotate_context_anchor_rows,
    load_context_anchor_windows_jsonl,
)
from .context_source_inventory import ENTITY_TO_GROUP
from .context_window_safety import scan_context_window_outputs


PROJECT_ROOT = Path(__file__).resolve().parents[2]
REPORT_VERSION = "v0.2-single-turn"
DRAFT_SCHEMA_VERSION = "context_anchor_draft_labels_v1"
REVIEW_PACKET_SCHEMA_VERSION = "context_label_review_packet_v1"
QUALITY_SCHEMA_VERSION = "context_label_quality_v1"
SAFETY_SCHEMA_VERSION = "context_label_review_safety_v1"
EVIDENCE_ROLE = "draft_label_review_not_score_tuning"
VALID_REVIEW_LABELS = ("true_pii", "non_pii", "unknown")
REVIEWER_APPROVED_LABEL_PATH = (
    Path("data") / "context_corpus" / "context_anchor_reviewer_approved_labels_v1.jsonl"
)


def build_context_anchor_draft_labels(
    anchor_rows: Iterable[dict[str, Any]],
) -> list[dict[str, Any]]:
    rows = annotate_context_anchor_rows(anchor_rows)
    return [_draft_label_row(row, index=index) for index, row in enumerate(rows, start=1)]


def build_context_label_review_packet_rows(
    draft_rows: Iterable[dict[str, Any]],
    *,
    sample_size: int | None = None,
) -> list[dict[str, Any]]:
    drafts = list(draft_rows)
    required = sample_size if sample_size is not None else required_reviewer_sample_size(len(drafts))
    selected = _stratified_sample(drafts, sample_size=required)
    packet_rows: list[dict[str, Any]] = []
    for index, row in enumerate(selected, start=1):
        packet_rows.append(
            {
                "schema_version": REVIEW_PACKET_SCHEMA_VERSION,
                "review_packet_id": f"review-packet-row-{_alpha_index(index)}",
                "draft_label_id": row["draft_label_id"],
                "anchor_entity": row["anchor_entity"],
                "entity_group": row["entity_group"],
                "anchor_shape": row["anchor_shape"],
                "source_domain": row["source_domain"],
                "material_type": row["material_type"],
                "evidence_lane": row["evidence_lane"],
                "draft_label": row["draft_label"],
                "draft_label_source": row["draft_label_source"],
                "draft_label_status": row["draft_label_status"],
                "review_status": "pending_reviewer",
                "reviewer_label": None,
                "reviewer_approved": False,
                "score_tuning_eligible": False,
                "raw_value_logged": False,
                "raw_url_logged": False,
                "page_body_stored": False,
                "candidate_value_stored": False,
                "evidence_role": EVIDENCE_ROLE,
            }
        )
    return packet_rows


def build_context_label_quality_report(
    *,
    draft_rows: Iterable[dict[str, Any]],
    review_packet_rows: Iterable[dict[str, Any]],
    reviewer_approved_rows: Iterable[dict[str, Any]] = (),
    reviewer_approved_artifact_exists: bool = False,
    safety_report: dict[str, Any] | None = None,
) -> dict[str, Any]:
    drafts = list(draft_rows)
    packet = list(review_packet_rows)
    approved = list(reviewer_approved_rows)
    total = len(drafts)
    label_counts = Counter(str(row["draft_label"]) for row in drafts)
    source_counts = Counter(str(row["draft_label_source"]) for row in drafts)
    status_counts = Counter(str(row["draft_label_status"]) for row in drafts)
    required_sample = required_reviewer_sample_size(total)
    draft_ids = {str(row["draft_label_id"]) for row in drafts}
    valid_approved = _valid_reviewer_approved_rows(
        approved,
        draft_ids=draft_ids,
    )
    approved_ids = [str(row["draft_label_id"]) for row in valid_approved]
    unique_approved_count = len(set(approved_ids))
    duplicate_approved_count = len(approved_ids) - unique_approved_count
    approved_count = len(valid_approved)
    approved_unknown_ratio = _ratio(
        sum(1 for row in valid_approved if row.get("reviewer_label") == "unknown"),
        approved_count,
    )
    agreement_score = _agreement_score(valid_approved)
    disagreement_ratio = _disagreement_ratio(valid_approved)
    unknown_ratio = _ratio(label_counts.get("unknown", 0), total)
    checks = {
        "draft_labels_created": total > 0,
        "review_packet_stratified": _packet_is_stratified(packet),
        "reviewer_packet_sample_size_met": len(packet) >= required_sample,
        "reviewer_approved_label_artifact_present": reviewer_approved_artifact_exists,
        "reviewer_approved_labels_present": approved_count > 0,
        "reviewer_approved_sample_size_met": unique_approved_count >= required_sample,
        "reviewer_approved_rows_valid": (
            approved_count == len(approved) and duplicate_approved_count == 0
        ),
        "final_probability_uses_reviewer_approved_only": (
            unique_approved_count >= required_sample
            and approved_count == len(approved)
            and duplicate_approved_count == 0
        ),
        "agreement_target_met": agreement_score is not None and agreement_score >= 0.85,
        "disagreement_ratio_target_met": (
            disagreement_ratio is not None and disagreement_ratio <= 0.10
        ),
        "unknown_ratio_target_met": approved_unknown_ratio <= 0.15,
        "disagreements_isolated_or_adjudicated": _disagreements_isolated_or_adjudicated(
            valid_approved
        ),
        "unknown_labels_excluded_from_score_tuning": True,
        "codex_draft_labels_not_gold": True,
        "raw_pii_safety_pass": (
            safety_report is None or safety_report.get("status") == "pass"
        ),
    }
    status = "pass" if all(checks.values()) else "fail"
    return {
        "report_type": "ContextLabelQuality",
        "schema_version": QUALITY_SCHEMA_VERSION,
        "version": REPORT_VERSION,
        "phase": "Phase 6. Label Review Packet",
        "evidence_role": EVIDENCE_ROLE,
        "status": status,
        "label_quality_gate": {
            "status": status,
            "checks": checks,
            "failure_verdicts": ["label_quality_gate_pass"]
            if status == "pass"
            else _label_quality_failure_verdicts(checks),
        },
        "draft_label_count": total,
        "draft_label_counts": {
            "true_pii": label_counts.get("true_pii", 0),
            "non_pii": label_counts.get("non_pii", 0),
            "unknown": label_counts.get("unknown", 0),
        },
        "draft_label_source_counts": dict(sorted(source_counts.items())),
        "draft_label_status_counts": dict(sorted(status_counts.items())),
        "reviewer_approved_label_count": approved_count,
        "reviewer_approved_label_artifact_present": reviewer_approved_artifact_exists,
        "reviewer_approved_label_artifact_path": str(REVIEWER_APPROVED_LABEL_PATH),
        "unique_reviewer_approved_label_count": unique_approved_count,
        "duplicate_reviewer_approved_label_count": duplicate_approved_count,
        "valid_reviewer_approved_label_count": approved_count,
        "final_probability_input_label_source": "reviewer_approved"
        if status == "pass"
        else "none_missing_reviewer_approved_labels",
        "reviewer_sample_required": required_sample,
        "reviewer_packet_sample_count": len(packet),
        "reviewer_sample_size_rule": "max_5_percent_or_1000_when_enough_rows",
        "agreement_score": agreement_score,
        "disagreement_ratio": disagreement_ratio,
        "unknown_ratio": unknown_ratio,
        "approved_unknown_ratio": approved_unknown_ratio,
        "disagreement_handling": "not_applicable_no_reviewer_labels"
        if approved_count == 0
        else "unresolved_disagreements_must_be_isolated_or_adjudicated",
        "unknown_labels_used_for_final_score_tuning": False,
        "codex_draft_labels_used_as_gold": False,
        "public_corpus_used_for_score_tuning": False,
        "score_tuning_allowed_by_this_phase": False,
        "runtime_scoring_behavior_changed": False,
        "score_delta_changed": False,
        "context_rule_changed": False,
        "raw_pii_safety": safety_report or {},
        "generated_at": _now(),
    }


def build_context_label_review_safety_report(
    *,
    draft_label_text: str,
    review_packet_text: str,
    label_quality_payload: dict[str, Any] | None = None,
    review_packet_markdown: str = "",
) -> dict[str, Any]:
    scan = scan_context_window_outputs(
        rows=[],
        report_payloads=[
            draft_label_text,
            review_packet_text,
            label_quality_payload or {},
            review_packet_markdown,
        ],
        source_urls=[],
    )
    return {
        "report_type": "ContextLabelReviewSafety",
        "schema_version": SAFETY_SCHEMA_VERSION,
        "version": REPORT_VERSION,
        "phase": "Phase 6. Label Review Packet",
        "evidence_role": EVIDENCE_ROLE,
        "status": scan["status"],
        "contains_raw_pii_true_count": scan["contains_raw_pii_true_count"],
        "raw_pii_leak_count": scan["raw_pii_leak_count"],
        "raw_url_logged_count": scan["raw_url_logged_count"],
        "raw_value_logged_count": scan["raw_value_logged_count"],
        "page_body_stored": False,
        "candidate_value_stored": False,
        "public_corpus_used_for_score_tuning": False,
        "reason_codes": scan["reason_codes"],
        "generated_at": _now(),
    }


def render_context_label_review_packet_markdown(
    *,
    draft_rows: Iterable[dict[str, Any]],
    review_packet_rows: Iterable[dict[str, Any]],
    label_quality: dict[str, Any],
) -> str:
    drafts = list(draft_rows)
    packet = list(review_packet_rows)
    strata = _strata_counts(drafts)
    lines = [
        "# M4 Phase 6 Label Review Packet",
        "",
        "This packet separates Codex draft labels from reviewer-approved gold labels. It stores only raw-free anchor metadata and reviewer workflow fields.",
        "",
        f"- phase_exit_status: {label_quality['label_quality_gate']['status']}",
        f"- draft_label_count: {label_quality['draft_label_count']}",
        f"- reviewer_packet_sample_count: {label_quality['reviewer_packet_sample_count']}",
        f"- reviewer_sample_required: {label_quality['reviewer_sample_required']}",
        f"- reviewer_approved_label_count: {label_quality['reviewer_approved_label_count']}",
        f"- final_probability_input_label_source: {label_quality['final_probability_input_label_source']}",
        f"- unknown_ratio: {label_quality['unknown_ratio']}",
        f"- score_tuning_allowed_by_this_phase: {str(label_quality['score_tuning_allowed_by_this_phase']).lower()}",
        "",
        "## Label Source Counts",
        "",
        "| source | count |",
        "| --- | ---: |",
    ]
    for source, count in label_quality["draft_label_source_counts"].items():
        lines.append(f"| {source} | {count} |")
    lines.extend(
        [
            "",
            "## Draft Label Counts",
            "",
            "| label | count |",
            "| --- | ---: |",
        ]
    )
    for label, count in label_quality["draft_label_counts"].items():
        lines.append(f"| {label} | {count} |")
    lines.extend(
        [
            "",
            "## Stratification Summary",
            "",
            "| entity_group | source_domain | draft_label | draft_rows | packet_rows |",
            "| --- | --- | --- | ---: | ---: |",
        ]
    )
    packet_strata = _strata_counts(packet, label_key="draft_label")
    for key, count in sorted(strata.items()):
        packet_count = packet_strata.get(key, 0)
        lines.append(f"| {key[0]} | {key[1]} | {key[2]} | {count} | {packet_count} |")
    lines.extend(
        [
            "",
            "## Gate Verdict",
            "",
            f"- label_quality_gate_status: {label_quality['label_quality_gate']['status']}",
            "- failure_verdicts: "
            + ", ".join(label_quality["label_quality_gate"]["failure_verdicts"]),
            "",
            "Codex draft labels remain draft-only. Probability/logLR estimation and score tuning remain blocked until a valid reviewer-approved label artifact exists.",
            "",
        ]
    )
    return "\n".join(lines)


def draft_labels_jsonl(rows: Iterable[dict[str, Any]]) -> str:
    return "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
    )


def review_packet_jsonl(rows: Iterable[dict[str, Any]]) -> str:
    return "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
    )


def write_context_label_review_artifacts(
    *,
    anchor_input_path: Path,
    draft_label_output_path: Path,
    review_packet_output_path: Path,
    review_packet_md_output_path: Path,
    label_quality_output_path: Path,
    label_review_safety_output_path: Path,
    reviewer_approved_input_path: Path | None = None,
) -> dict[str, Any]:
    anchor_rows = (
        load_context_anchor_windows_jsonl(anchor_input_path)
        if anchor_input_path.exists()
        else []
    )
    approved_path = reviewer_approved_input_path or (
        PROJECT_ROOT / REVIEWER_APPROVED_LABEL_PATH
    )
    approved_exists = approved_path.exists()
    approved_rows = _load_jsonl(approved_path) if approved_exists else []

    draft_rows = build_context_anchor_draft_labels(anchor_rows)
    packet_rows = build_context_label_review_packet_rows(draft_rows)
    draft_text = draft_labels_jsonl(draft_rows)
    packet_text = review_packet_jsonl(packet_rows)
    initial_safety = build_context_label_review_safety_report(
        draft_label_text=draft_text,
        review_packet_text=packet_text,
    )
    label_quality = build_context_label_quality_report(
        draft_rows=draft_rows,
        review_packet_rows=packet_rows,
        reviewer_approved_rows=approved_rows,
        reviewer_approved_artifact_exists=approved_exists,
        safety_report=initial_safety,
    )
    markdown = render_context_label_review_packet_markdown(
        draft_rows=draft_rows,
        review_packet_rows=packet_rows,
        label_quality=label_quality,
    )
    final_safety = build_context_label_review_safety_report(
        draft_label_text=draft_text,
        review_packet_text=packet_text,
        label_quality_payload=label_quality,
        review_packet_markdown=markdown,
    )
    label_quality["raw_pii_safety"] = final_safety
    label_quality["label_quality_gate"]["checks"]["raw_pii_safety_pass"] = (
        final_safety["status"] == "pass"
    )
    if final_safety["status"] != "pass":
        label_quality["status"] = "fail"
        label_quality["label_quality_gate"]["status"] = "fail"
        label_quality["label_quality_gate"]["failure_verdicts"] = (
            _label_quality_failure_verdicts(label_quality["label_quality_gate"]["checks"])
        )

    _write_text(draft_label_output_path, draft_text)
    _write_text(review_packet_output_path, packet_text)
    _write_text(review_packet_md_output_path, markdown)
    _write_text(
        label_quality_output_path,
        json.dumps(label_quality, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )
    _write_text(
        label_review_safety_output_path,
        json.dumps(final_safety, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
    )

    if final_safety["status"] != "pass":
        raise ValueError("raw PII safety failed for label review packet")
    return label_quality


def required_reviewer_sample_size(total_rows: int) -> int:
    if total_rows <= 0:
        return 0
    return min(total_rows, max(math.ceil(total_rows * 0.05), 1000))


def _draft_label_row(row: dict[str, Any], *, index: int) -> dict[str, Any]:
    entity = str(row.get("anchor_entity", "unknown"))
    entity_group = ENTITY_TO_GROUP.get(entity, entity)
    return {
        "schema_version": DRAFT_SCHEMA_VERSION,
        "draft_label_id": _stable_id("draft", row, index),
        "source_row_hash": _stable_id("source-row", row, index),
        "anchor_entity": entity,
        "entity_group": entity_group,
        "anchor_shape": row.get("anchor_shape"),
        "source_domain": row.get("source_domain"),
        "material_type": row.get("material_type", row.get("material_class")),
        "evidence_lane": row.get("evidence_lane"),
        "draft_label": row.get("label", "unknown"),
        "draft_label_source": row.get("label_source", "unlabeled"),
        "draft_label_status": row.get("label_status", "unknown"),
        "reviewer_label": None,
        "reviewer_approved": False,
        "score_tuning_eligible": False,
        "unknown_labels_excluded_from_score_tuning": True,
        "codex_draft_label_is_gold": False,
        "raw_value_logged": False,
        "raw_url_logged": False,
        "page_body_stored": False,
        "candidate_value_stored": False,
        "evidence_role": EVIDENCE_ROLE,
    }


def _stratified_sample(rows: list[dict[str, Any]], *, sample_size: int) -> list[dict[str, Any]]:
    if sample_size <= 0:
        return []
    buckets: dict[tuple[str, str, str], deque[dict[str, Any]]] = defaultdict(deque)
    for row in sorted(rows, key=lambda item: str(item.get("draft_label_id", ""))):
        key = (
            str(row.get("entity_group", "unknown")),
            str(row.get("source_domain", "unknown")),
            str(row.get("draft_label", "unknown")),
        )
        buckets[key].append(row)
    selected: list[dict[str, Any]] = []
    keys = sorted(buckets)
    while len(selected) < sample_size and any(buckets[key] for key in keys):
        for key in keys:
            if buckets[key]:
                selected.append(buckets[key].popleft())
                if len(selected) >= sample_size:
                    break
    return selected


def _packet_is_stratified(packet_rows: list[dict[str, Any]]) -> bool:
    if not packet_rows:
        return False
    return all(
        row.get("entity_group")
        and row.get("source_domain")
        and row.get("draft_label")
        for row in packet_rows
    )


def _strata_counts(
    rows: Iterable[dict[str, Any]],
    *,
    label_key: str = "draft_label",
) -> dict[tuple[str, str, str], int]:
    counts: Counter[tuple[str, str, str]] = Counter()
    for row in rows:
        counts[
            (
                str(row.get("entity_group", "unknown")),
                str(row.get("source_domain", "unknown")),
                str(row.get(label_key, "unknown")),
            )
        ] += 1
    return dict(counts)


def _label_quality_failure_verdicts(checks: dict[str, bool]) -> list[str]:
    verdicts: list[str] = []
    if not checks.get("reviewer_approved_label_artifact_present", False):
        verdicts.append("needs_reviewer_labels")
    if not checks.get("reviewer_approved_labels_present", False) or not checks.get(
        "reviewer_approved_sample_size_met",
        False,
    ):
        verdicts.append("needs_more_labels")
    if not checks.get("reviewer_approved_rows_valid", False):
        verdicts.append("invalid_reviewer_labels")
    if not checks.get("agreement_target_met", False):
        verdicts.append("label_quality_failed")
    if not checks.get("disagreement_ratio_target_met", False) or not checks.get(
        "disagreements_isolated_or_adjudicated",
        False,
    ):
        verdicts.append("needs_adjudication")
    if not checks.get("unknown_ratio_target_met", False):
        verdicts.append("unknown_ratio_too_high")
    if not checks.get("reviewer_packet_sample_size_met", False):
        verdicts.append("reviewer_sample_too_small")
    if not checks.get("raw_pii_safety_pass", False):
        verdicts.append("raw_pii_safety_failure")
    return sorted(set(verdicts))


def _valid_reviewer_approved_rows(
    approved_rows: list[dict[str, Any]],
    *,
    draft_ids: set[str],
) -> list[dict[str, Any]]:
    valid_rows: list[dict[str, Any]] = []
    for row in approved_rows:
        draft_id = row.get("draft_label_id")
        reviewer_label = row.get("reviewer_label")
        source_ok = (
            row.get("label_source") == "reviewer_approved"
            or row.get("label_status") == "reviewer_approved"
            or row.get("reviewer_approved") is True
        )
        if (
            isinstance(draft_id, str)
            and draft_id in draft_ids
            and reviewer_label in VALID_REVIEW_LABELS
            and row.get("draft_label") in VALID_REVIEW_LABELS
            and source_ok
        ):
            valid_rows.append(row)
    return valid_rows


def _disagreements_isolated_or_adjudicated(approved_rows: list[dict[str, Any]]) -> bool:
    for row in approved_rows:
        if row.get("draft_label") == row.get("reviewer_label"):
            continue
        if row.get("reviewer_label") == "unknown":
            continue
        if row.get("adjudication_status") in {"adjudicated", "isolated_unknown"}:
            continue
        return False
    return bool(approved_rows)


def _agreement_score(approved_rows: list[dict[str, Any]]) -> float | None:
    if not approved_rows:
        return None
    comparable = [
        row
        for row in approved_rows
        if row.get("draft_label") is not None and row.get("reviewer_label") is not None
    ]
    if not comparable:
        return None
    matches = sum(1 for row in comparable if row["draft_label"] == row["reviewer_label"])
    return _ratio(matches, len(comparable))


def _disagreement_ratio(approved_rows: list[dict[str, Any]]) -> float | None:
    agreement = _agreement_score(approved_rows)
    if agreement is None:
        return None
    return round(1.0 - agreement, 6)


def _stable_id(prefix: str, row: dict[str, Any], index: int) -> str:
    payload = json.dumps(row, ensure_ascii=False, sort_keys=True)
    digest = hashlib.sha256(f"{index}:{payload}".encode("utf-8")).hexdigest()
    alpha_digest = "".join(chr(ord("a") + int(char, 16)) for char in digest[:16])
    return f"{prefix}-{alpha_digest}"


def _alpha_index(index: int) -> str:
    if index <= 0:
        return "a"
    chars: list[str] = []
    value = index
    while value:
        value, remainder = divmod(value - 1, 26)
        chars.append(chr(ord("a") + remainder))
    return "".join(reversed(chars))


def _ratio(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(numerator / denominator, 6)


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()
