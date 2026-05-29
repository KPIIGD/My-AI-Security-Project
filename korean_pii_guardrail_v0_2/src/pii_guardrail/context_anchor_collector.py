"""Raw-free anchor context collection for M4 context recalibration.

The collector may inspect candidate values in memory, but persisted artifacts
store only anchor shape, source metadata, labels, and surrounding n-grams.
"""

from __future__ import annotations

import datetime
import hashlib
import html
import json
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .context_source_inventory import (
    MATERIAL_CLASSES,
    SOURCE_DOMAIN_TAXONOMY,
    SOURCE_TYPE_INVENTORY,
)
from .context_window_safety import detect_raw_pii_like_values, scan_context_window_outputs


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCHEMA_VERSION = "context_anchor_windows_v1"
TERM_SCHEMA_VERSION = "korean_context_terms_v1"
EVIDENCE_ROLE = "anchor_context_only_not_score_tuning"
TERM_EVIDENCE_ROLE = "context_ngram_frequency_not_score_tuning"
BUCKET_SIZES = {
    "within_1_token": 1,
    "within_2_tokens": 2,
    "within_5_tokens": 5,
}
NGRAM_FIELDS = {
    1: "unigrams",
    2: "bigrams",
    3: "trigrams",
}
VALID_LABELS = ("true_pii", "non_pii", "unknown")
VALID_ANCHOR_SOURCES = (
    "regex",
    "dictionary",
    "ner",
    "dictionary_or_ner",
    "heuristic_shape",
    "synthetic_template",
)
VALID_ANCHOR_ENTITIES = (
    "PERSON_NAME",
    "PHONE_MOBILE",
    "PHONE_LANDLINE",
    "EMAIL",
    "ADDRESS_FULL",
    "ADDRESS_UNIT",
    "BANK_ACCOUNT",
    "RRN",
    "FRN",
    "PASSPORT",
    "DRIVER_LICENSE",
    "BUSINESS_REG_NO",
    "CORPORATE_REG_NO",
)
VALID_ANCHOR_SHAPES = (
    "korean_name_2_syllable",
    "korean_name_3_syllable",
    "korean_name_4_syllable",
    "korean_name_like_2_syllable",
    "korean_name_like_3_syllable",
    "korean_name_like_4_syllable",
    "mobile_phone_shape",
    "landline_phone_shape",
    "email_shape",
    "road_address_shape",
    "lot_address_shape",
    "address_unit_shape",
    "bank_account_shape",
    "rrn_shape",
    "frn_shape",
    "passport_shape",
    "driver_license_shape",
    "business_registration_shape",
    "corporate_registration_shape",
)

SOURCE_TYPE_TO_DOMAIN = {
    row["source_type"]: row["source_domain"] for row in SOURCE_TYPE_INVENTORY
}
DOMAIN_TO_MATERIAL = {
    row["source_domain"]: row["material_class"] for row in SOURCE_DOMAIN_TAXONOMY
}

_MARKER_PATTERN = re.compile(
    r"\[\[ANCHOR:"
    r"(?P<entity>[A-Z0-9_]+):"
    r"(?P<shape>[a-z0-9_]+)"
    r"(?::(?P<label>true_pii|non_pii|unknown))?"
    r"(?::(?P<source>regex|dictionary|ner|dictionary_or_ner|heuristic_shape|synthetic_template))?"
    r"\]\]"
)
_URL_PATTERN = re.compile(r"\b(?:http[s]?|ftp)://\S+")
_SAFE_HASH_PATTERN = re.compile(r"sha256:[0-9a-f]{64}")
_TOKEN_PATTERN = re.compile(r"[^\s,.;:!?()\[\]{}<>\"']+")
_CANDIDATE_PATTERNS: tuple[tuple[str, str, str, re.Pattern[str]], ...] = (
    (
        "EMAIL",
        "email_shape",
        "regex",
        re.compile(r"(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    ),
    (
        "PHONE_MOBILE",
        "mobile_phone_shape",
        "regex",
        re.compile(r"(?<![0-9])01[016789][- ]?[0-9]{3,4}[- ]?[0-9]{4}(?![0-9])"),
    ),
    (
        "PHONE_LANDLINE",
        "landline_phone_shape",
        "regex",
        re.compile(r"(?<![0-9])0(?:2|[3-6][1-5])[- ]?[0-9]{3,4}[- ]?[0-9]{4}(?![0-9])"),
    ),
    (
        "RRN",
        "rrn_shape",
        "regex",
        re.compile(r"(?<![0-9])[0-9]{6}[- ]?[1-4][0-9]{6}(?![0-9])"),
    ),
    (
        "FRN",
        "frn_shape",
        "regex",
        re.compile(r"(?<![0-9])[0-9]{6}[- ]?[5-8][0-9]{6}(?![0-9])"),
    ),
    (
        "BUSINESS_REG_NO",
        "business_registration_shape",
        "regex",
        re.compile(r"(?<![0-9])[0-9]{3}[- ]?[0-9]{2}[- ]?[0-9]{5}(?![0-9])"),
    ),
    (
        "BANK_ACCOUNT",
        "bank_account_shape",
        "regex",
        re.compile(r"(?<![0-9])[0-9]{2,6}(?:[- ][0-9]{2,6}){2,4}(?![0-9])"),
    ),
)


@dataclass(frozen=True)
class AnchorCandidate:
    anchor_entity: str
    anchor_shape: str
    anchor_source: str
    label: str
    start: int
    end: int


@dataclass(frozen=True)
class ContextAnchorWindowRow:
    anchor_entity: str
    anchor_shape: str
    anchor_source: str
    label: str
    source_domain: str
    material_class: str
    distance_bucket: str
    left_ngrams: dict[str, dict[str, list[str]]]
    right_ngrams: dict[str, dict[str, list[str]]]
    source_type: str | None = None
    source_id_hash: str | None = None
    contains_raw_pii: bool = False
    raw_value_logged: bool = False
    raw_url_logged: bool = False
    page_body_stored: bool = False
    candidate_value_stored: bool = False
    evidence_role: str = EVIDENCE_ROLE

    def to_dict(self) -> dict[str, Any]:
        row = {
            "schema_version": SCHEMA_VERSION,
            "anchor_entity": self.anchor_entity,
            "anchor_shape": self.anchor_shape,
            "anchor_source": self.anchor_source,
            "label": self.label,
            "source_domain": self.source_domain,
            "material_class": self.material_class,
            "distance_bucket": self.distance_bucket,
            "left_ngrams": self.left_ngrams,
            "right_ngrams": self.right_ngrams,
            "contains_raw_pii": False,
            "raw_value_logged": False,
            "raw_url_logged": False,
            "page_body_stored": False,
            "candidate_value_stored": False,
            "evidence_role": self.evidence_role,
        }
        if self.source_type is not None:
            row["source_type"] = self.source_type
        if self.source_id_hash is not None:
            row["source_id_hash"] = self.source_id_hash
        return row


def source_id_hash(source_id: str) -> str:
    return "sha256:" + hashlib.sha256(source_id.encode("utf-8")).hexdigest()


def extract_context_anchor_windows_from_html(
    *,
    html_text: str,
    source_type: str,
    source_id: str,
    default_label: str = "unknown",
    max_windows: int = 50,
) -> tuple[ContextAnchorWindowRow, ...]:
    return extract_context_anchor_windows_from_text(
        text=_strip_html(html_text),
        source_type=source_type,
        source_id=source_id,
        default_label=default_label,
        max_windows=max_windows,
    )


def extract_context_anchor_windows_from_text(
    *,
    text: str,
    source_type: str,
    source_id: str,
    default_label: str = "unknown",
    max_windows: int = 50,
) -> tuple[ContextAnchorWindowRow, ...]:
    if source_type not in SOURCE_TYPE_TO_DOMAIN:
        raise ValueError("Unsupported source_type")
    if default_label not in VALID_LABELS:
        raise ValueError("Unsupported default_label")
    if max_windows <= 0:
        raise ValueError("max_windows must be positive")

    rows: list[ContextAnchorWindowRow] = []
    seen: set[str] = set()
    domain = SOURCE_TYPE_TO_DOMAIN[source_type]
    material_class = DOMAIN_TO_MATERIAL[domain]
    for sentence in _sentence_candidates(text):
        for candidate in _candidate_spans(sentence, default_label):
            left_text = sentence[: candidate.start]
            right_text = sentence[candidate.end :]
            left_ngrams = _ngram_windows(_tokens(left_text), side="left")
            right_ngrams = _ngram_windows(_tokens(right_text), side="right")
            if not _has_any_ngram(left_ngrams) and not _has_any_ngram(right_ngrams):
                continue
            row = ContextAnchorWindowRow(
                anchor_entity=candidate.anchor_entity,
                anchor_shape=candidate.anchor_shape,
                anchor_source=candidate.anchor_source,
                label=candidate.label,
                source_domain=domain,
                source_type=source_type,
                material_class=material_class,
                source_id_hash=source_id_hash(source_id),
                distance_bucket=_largest_non_empty_bucket(left_ngrams, right_ngrams),
                left_ngrams=left_ngrams,
                right_ngrams=right_ngrams,
            )
            payload = json.dumps(row.to_dict(), ensure_ascii=False, sort_keys=True)
            scan_payload = _SAFE_HASH_PATTERN.sub("sha256:SAFE_HASH", payload)
            if detect_raw_pii_like_values(scan_payload) or _URL_PATTERN.search(scan_payload):
                continue
            key = hashlib.sha256(payload.encode("utf-8")).hexdigest()
            if key in seen:
                continue
            seen.add(key)
            rows.append(row)
            if len(rows) >= max_windows:
                return tuple(rows)
    return tuple(rows)


def context_anchor_windows_jsonl(rows: Iterable[ContextAnchorWindowRow | dict[str, Any]]) -> str:
    return "".join(
        json.dumps(_row_dict(row), ensure_ascii=False, sort_keys=True) + "\n"
        for row in rows
    )


def aggregate_korean_context_terms(
    rows: Iterable[ContextAnchorWindowRow | dict[str, Any]]
) -> list[dict[str, Any]]:
    counter: Counter[tuple[str, str, str, int, str, str]] = Counter()
    for row in rows:
        payload = _row_dict(row)
        entity = str(payload["anchor_entity"])
        domain = str(payload["source_domain"])
        label = str(payload["label"])
        for side in ("left", "right"):
            windows = payload[f"{side}_ngrams"]
            for bucket, ngram_groups in windows.items():
                relative_position = f"{side}_{bucket}"
                for ngram_size, field_name in NGRAM_FIELDS.items():
                    for ngram in ngram_groups[field_name]:
                        if _is_safe_ngram(str(ngram)):
                            counter[
                                (
                                    entity,
                                    domain,
                                    str(ngram),
                                    ngram_size,
                                    relative_position,
                                    label,
                                )
                            ] += 1
    return [
        {
            "schema_version": TERM_SCHEMA_VERSION,
            "entity_hint": entity,
            "source_domain": domain,
            "ngram": ngram,
            "ngram_size": ngram_size,
            "relative_position": relative_position,
            "frequency": frequency,
            "label": label,
            "term_class": None,
            "term_class_status": "unclassified_discovered_term",
            "raw_value_logged": False,
            "raw_url_logged": False,
            "page_body_stored": False,
            "evidence_role": TERM_EVIDENCE_ROLE,
        }
        for (
            entity,
            domain,
            ngram,
            ngram_size,
            relative_position,
            label,
        ), frequency in sorted(counter.items())
    ]


def korean_context_terms_jsonl(rows: Iterable[dict[str, Any]]) -> str:
    return "".join(
        json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n" for row in rows
    )


def build_context_anchor_safety_report(
    *,
    rows: Iterable[ContextAnchorWindowRow | dict[str, Any]],
    term_rows: Iterable[dict[str, Any]],
    source_ids: Iterable[str],
    extra_payloads: Iterable[object] = (),
) -> dict[str, Any]:
    row_list = list(rows)
    term_list = list(term_rows)
    scan = scan_context_window_outputs(
        rows=[_SafetyRow(_row_dict(row)) for row in row_list],
        report_payloads=[
            context_anchor_windows_jsonl(row_list),
            korean_context_terms_jsonl(term_list),
            *extra_payloads,
        ],
        source_urls=source_ids,
    )
    return {
        "report_type": "ContextAnchorCorpusSafetyReport",
        "schema_version": SCHEMA_VERSION,
        "stage": "1.3 collector MVP",
        "evidence_role": EVIDENCE_ROLE,
        "anchor_window_count": len(row_list),
        "context_term_count": len(term_list),
        "contains_raw_pii_true_count": scan["contains_raw_pii_true_count"],
        "raw_pii_leak_count": scan["raw_pii_leak_count"],
        "raw_url_logged_count": scan["raw_url_logged_count"],
        "raw_value_logged_count": scan["raw_value_logged_count"],
        "page_body_stored": False,
        "candidate_value_stored": False,
        "public_corpus_used_for_score_tuning": False,
        "runtime_scoring_behavior_changed": False,
        "score_delta_changed": False,
        "context_rule_changed": False,
        "status": scan["status"],
        "reason_codes": scan["reason_codes"],
        "generated_at": _now(),
    }


def load_context_anchor_windows_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        if isinstance(payload, dict):
            rows.append(payload)
    return rows


def _candidate_spans(text: str, default_label: str) -> tuple[AnchorCandidate, ...]:
    candidates: list[AnchorCandidate] = []
    for match in _MARKER_PATTERN.finditer(text):
        entity = match.group("entity")
        shape = match.group("shape")
        label = match.group("label") or default_label
        source = match.group("source") or "synthetic_template"
        if (
            entity in VALID_ANCHOR_ENTITIES
            and shape in VALID_ANCHOR_SHAPES
            and label in VALID_LABELS
            and source in VALID_ANCHOR_SOURCES
        ):
            candidates.append(
                AnchorCandidate(
                    anchor_entity=entity,
                    anchor_shape=shape,
                    anchor_source=source,
                    label=label,
                    start=match.start(),
                    end=match.end(),
                )
            )
    for entity, shape, source, pattern in _CANDIDATE_PATTERNS:
        for match in pattern.finditer(text):
            candidate = AnchorCandidate(
                anchor_entity=entity,
                anchor_shape=shape,
                anchor_source=source,
                label=default_label,
                start=match.start(),
                end=match.end(),
            )
            if not any(_overlaps(candidate, existing) for existing in candidates):
                candidates.append(candidate)
    return tuple(sorted(candidates, key=lambda candidate: (candidate.start, candidate.end)))


def _ngram_windows(tokens: list[str], *, side: str) -> dict[str, dict[str, list[str]]]:
    return {
        bucket: {
            field_name: _ngrams(_bucket_tokens(tokens, bucket, side=side), ngram_size)
            for ngram_size, field_name in NGRAM_FIELDS.items()
        }
        for bucket in BUCKET_SIZES
    }


def _bucket_tokens(tokens: list[str], bucket: str, *, side: str) -> list[str]:
    size = BUCKET_SIZES[bucket]
    if side == "left":
        return tokens[-size:]
    if side == "right":
        return tokens[:size]
    raise ValueError("side must be left or right")


def _ngrams(tokens: list[str], ngram_size: int) -> list[str]:
    values: list[str] = []
    seen: set[str] = set()
    for index in range(0, len(tokens) - ngram_size + 1):
        ngram = " ".join(tokens[index : index + ngram_size])
        if _is_safe_ngram(ngram) and ngram not in seen:
            seen.add(ngram)
            values.append(ngram)
    return values


def _tokens(text: str) -> list[str]:
    return [token for token in _TOKEN_PATTERN.findall(text) if _is_safe_token(token)]


def _is_safe_token(token: str) -> bool:
    return bool(token) and _is_safe_ngram(token)


def _is_safe_ngram(ngram: str) -> bool:
    return (
        bool(ngram.strip())
        and len(ngram) <= 64
        and "\n" not in ngram
        and "\r" not in ngram
        and "\t" not in ngram
        and "@" not in ngram
        and not _URL_PATTERN.search(ngram)
        and not detect_raw_pii_like_values(ngram)
    )


def _largest_non_empty_bucket(
    left_ngrams: dict[str, dict[str, list[str]]],
    right_ngrams: dict[str, dict[str, list[str]]],
) -> str:
    for bucket in ("within_5_tokens", "within_2_tokens", "within_1_token"):
        if _has_any_ngram({bucket: left_ngrams[bucket]}) or _has_any_ngram(
            {bucket: right_ngrams[bucket]}
        ):
            return bucket
    return "within_1_token"


def _has_any_ngram(windows: dict[str, dict[str, list[str]]]) -> bool:
    return any(
        bool(values)
        for ngram_groups in windows.values()
        for values in ngram_groups.values()
    )


def _overlaps(left: AnchorCandidate, right: AnchorCandidate) -> bool:
    return left.start < right.end and right.start < left.end


def _strip_html(html_text: str) -> str:
    without_scripts = re.sub(
        r"(?is)<(script|style|noscript).*?</\1>",
        " ",
        html_text,
    )
    without_tags = re.sub(r"(?s)<[^>]+>", " ", without_scripts)
    unescaped = html.unescape(without_tags)
    return re.sub(r"\s+", " ", unescaped).strip()


def _sentence_candidates(text: str) -> tuple[str, ...]:
    parts = re.split(r"(?<=[.!?])\s+|[\r\n]+", text)
    return tuple(part.strip() for part in parts if len(part.strip()) >= 4)


def _row_dict(row: ContextAnchorWindowRow | dict[str, Any]) -> dict[str, Any]:
    return row.to_dict() if isinstance(row, ContextAnchorWindowRow) else dict(row)


def _now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat()


@dataclass(frozen=True)
class _SafetyRow:
    payload: dict[str, Any]

    @property
    def contains_raw_pii(self) -> bool:
        return bool(self.payload.get("contains_raw_pii", False))

    @property
    def raw_value_logged(self) -> bool:
        return bool(self.payload.get("raw_value_logged", False))
