from __future__ import annotations

import copy
import json
from pathlib import Path

import jsonschema
import pytest

from pii_guardrail.context_source_inventory import (
    MATERIAL_CLASSES,
    SOURCE_DOMAIN_TAXONOMY,
    SOURCE_TYPE_INVENTORY,
)


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _schema() -> dict:
    return json.loads(
        (PROJECT_ROOT / "schemas" / "context_anchor_window.schema.json").read_text(
            encoding="utf-8"
        )
    )


def _ngram_windows() -> dict:
    return {
        "within_1_token": {
            "unigrams": ["applicant"],
            "bigrams": ["applicant label"],
            "trigrams": [],
        },
        "within_2_tokens": {
            "unigrams": ["contact"],
            "bigrams": ["contact field"],
            "trigrams": ["contact field label"],
        },
        "within_5_tokens": {
            "unigrams": ["confirm"],
            "bigrams": ["identity confirm"],
            "trigrams": [],
        },
    }


def _valid_row() -> dict:
    return {
        "schema_version": "context_anchor_windows_v1",
        "anchor_entity": "PERSON_NAME",
        "anchor_shape": "korean_name_3_syllable",
        "anchor_source": "ner",
        "label": "true_pii",
        "source_domain": "customer_support",
        "source_type": "customer_support_help",
        "material_class": "realistic_input_like",
        "source_id_hash": "sha256:" + ("a" * 64),
        "distance_bucket": "within_5_tokens",
        "left_ngrams": _ngram_windows(),
        "right_ngrams": _ngram_windows(),
        "contains_raw_pii": False,
        "raw_value_logged": False,
        "raw_url_logged": False,
        "page_body_stored": False,
        "candidate_value_stored": False,
        "evidence_role": "anchor_context_only_not_score_tuning",
    }


def test_anchor_window_schema_accepts_raw_free_context_row() -> None:
    schema = _schema()

    jsonschema.Draft202012Validator.check_schema(schema)
    jsonschema.validate(_valid_row(), schema)


def test_anchor_window_schema_forbids_raw_value_and_text_fields() -> None:
    schema = _schema()
    forbidden_fields = (
        "anchor_value",
        "candidate_value",
        "raw_value",
        "text",
        "raw_text",
        "span_text",
        "page_body",
        "document_text",
        "html",
        "html_text",
        "url",
        "raw_url",
    )

    for field in forbidden_fields:
        unsafe = _valid_row() | {field: "not_allowed"}
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(unsafe, schema)


def test_anchor_window_schema_requires_false_raw_storage_flags() -> None:
    schema = _schema()

    for field in (
        "contains_raw_pii",
        "raw_value_logged",
        "raw_url_logged",
        "page_body_stored",
        "candidate_value_stored",
    ):
        unsafe = _valid_row() | {field: True}
        with pytest.raises(jsonschema.ValidationError):
            jsonschema.validate(unsafe, schema)


def test_anchor_window_schema_requires_distance_and_ngram_buckets() -> None:
    schema = _schema()

    missing_distance = copy.deepcopy(_valid_row())
    del missing_distance["left_ngrams"]["within_2_tokens"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(missing_distance, schema)

    missing_ngram_size = copy.deepcopy(_valid_row())
    del missing_ngram_size["right_ngrams"]["within_5_tokens"]["trigrams"]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(missing_ngram_size, schema)


def test_anchor_window_schema_rejects_raw_like_shapes_and_ngrams() -> None:
    schema = _schema()

    raw_like_phone = "010" + "-" + "1234" + "-" + "5678"
    unsafe_shape = _valid_row() | {"anchor_shape": raw_like_phone}
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(unsafe_shape, schema)

    unsafe_ngram = copy.deepcopy(_valid_row())
    unsafe_ngram["left_ngrams"]["within_1_token"]["unigrams"] = [raw_like_phone]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(unsafe_ngram, schema)

    unsafe_email_ngram = copy.deepcopy(_valid_row())
    unsafe_email_ngram["right_ngrams"]["within_1_token"]["unigrams"] = [
        "person" + "@" + "example" + "." + "test"
    ]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(unsafe_email_ngram, schema)

    unsafe_url_ngram = copy.deepcopy(_valid_row())
    unsafe_url_ngram["right_ngrams"]["within_2_tokens"]["bigrams"] = [
        "https" + "://" + "example.test/path"
    ]
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(unsafe_url_ngram, schema)


def test_anchor_window_schema_aligns_with_source_inventory_taxonomy() -> None:
    schema = _schema()

    assert set(schema["properties"]["source_domain"]["enum"]) == {
        row["source_domain"] for row in SOURCE_DOMAIN_TAXONOMY
    }
    assert set(schema["properties"]["source_type"]["enum"]) == {
        row["source_type"] for row in SOURCE_TYPE_INVENTORY
    }
    assert set(schema["properties"]["material_class"]["enum"]) == set(MATERIAL_CLASSES)
