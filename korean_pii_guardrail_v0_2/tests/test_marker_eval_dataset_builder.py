"""Tests for marker-authored evaluation dataset compilation."""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SCRIPT_PATH = PROJECT_ROOT / "scripts" / "build_marker_eval_dataset.py"
GENERATOR_PATH = PROJECT_ROOT / "scripts" / "generate_stage1_person_name_markers.py"
CONTACT_GENERATOR_PATH = PROJECT_ROOT / "scripts" / "generate_stage2_contact_markers.py"
ADDRESS_GENERATOR_PATH = PROJECT_ROOT / "scripts" / "generate_stage3_address_markers.py"
CORPORATE_RRN_GENERATOR_PATH = PROJECT_ROOT / "scripts" / "generate_stage4_corporate_rrn_markers.py"
NUMERIC_IDENTIFIER_GENERATOR_PATH = PROJECT_ROOT / "scripts" / "generate_stage5_numeric_identifier_markers.py"
SUMMARY_PATH = PROJECT_ROOT / "scripts" / "summarize_person_name_actions.py"


def _load_builder_module():
    spec = importlib.util.spec_from_file_location("build_marker_eval_dataset", SCRIPT_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_generator_module():
    spec = importlib.util.spec_from_file_location("generate_stage1_person_name_markers", GENERATOR_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_contact_generator_module():
    spec = importlib.util.spec_from_file_location("generate_stage2_contact_markers", CONTACT_GENERATOR_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_address_generator_module():
    spec = importlib.util.spec_from_file_location("generate_stage3_address_markers", ADDRESS_GENERATOR_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_corporate_rrn_generator_module():
    spec = importlib.util.spec_from_file_location(
        "generate_stage4_corporate_rrn_markers",
        CORPORATE_RRN_GENERATOR_PATH,
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_numeric_identifier_generator_module():
    spec = importlib.util.spec_from_file_location(
        "generate_stage5_numeric_identifier_markers",
        NUMERIC_IDENTIFIER_GENERATOR_PATH,
    )
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_summary_module():
    spec = importlib.util.spec_from_file_location("summarize_person_name_actions", SUMMARY_PATH)
    assert spec is not None
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_parse_marked_text_computes_offsets_and_suffix() -> None:
    builder = _load_builder_module()

    text, labels = builder.parse_marked_text(
        "고객명 <PERSON_NAME risk=\"P1\">하늘</PERSON_NAME>, 연락처 "
        "<PHONE_MOBILE risk=\"P1\" suffix=\"입니다\">010-1111-2222</PHONE_MOBILE>입니다.",
        case_id="stage1-test",
    )

    assert text == "고객명 하늘, 연락처 010-1111-2222입니다."
    assert labels == [
        {
            "start": 4,
            "end": 6,
            "entity_type": "PERSON_NAME",
            "risk_level": "P1",
            "suffix": None,
        },
        {
            "start": 12,
            "end": 25,
            "entity_type": "PHONE_MOBILE",
            "risk_level": "P1",
            "suffix": "입니다",
        },
    ]


def test_marker_builder_cli_writes_loadable_eval_jsonl(tmp_path: Path) -> None:
    source = tmp_path / "markers.jsonl"
    output = tmp_path / "compiled.jsonl"
    source.write_text(
        json.dumps(
            {
                "id": "stage1-name-pos-0001",
                "marked_text": "고객명 <PERSON_NAME risk=\"P1\">하늘</PERSON_NAME>입니다.",
                "expected_masked_text": "고객명 [PERSON_1]입니다.",
                "tags": ["stage1", "person_context_positive"],
                "bucket": "person_context_positive",
            },
            ensure_ascii=False,
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT_PATH),
            "--input",
            str(source),
            "--output",
            str(output),
            "--validate",
        ],
        cwd=PROJECT_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    assert "compiled_cases=1" in result.stdout
    [record] = [json.loads(line) for line in output.read_text(encoding="utf-8").splitlines()]
    assert record["text"] == "고객명 하늘입니다."
    assert record["labels"][0]["start"] == 4
    assert record["labels"][0]["end"] == 6
    assert record["bucket"] == "person_context_positive"


def test_stage1_person_name_generator_has_expected_bucket_counts() -> None:
    generator = _load_generator_module()

    cases = generator.build_cases()

    assert len(cases) == 800
    assert sum(1 for case in cases if case.bucket == "hard_negative_name") == 500
    assert sum(1 for case in cases if case.bucket == "person_context_positive") == 300
    assert len({case.id for case in cases}) == 800
    assert all("PERSON_NAME" not in case.marked_text for case in cases[:500])
    assert all("<PERSON_NAME risk=\"P1\">" in case.marked_text for case in cases[500:])


def test_person_name_action_metrics_separates_candidate_and_actionable() -> None:
    summary = _load_summary_module()

    metrics = summary.PersonNameActionMetrics(tp_exact=3, fn=1, fp=2)

    assert metrics.to_dict() == {
        "tp_exact": 3,
        "fn": 1,
        "fp": 2,
        "precision": 0.6,
        "recall": 0.75,
        "f1": 0.6667,
    }


def test_stage2_contact_generator_has_expected_bucket_counts() -> None:
    generator = _load_contact_generator_module()

    cases = generator.build_cases()
    counts: dict[str, int] = {}
    for case in cases:
        counts[case.bucket] = counts.get(case.bucket, 0) + 1

    assert len(cases) == 1200
    assert counts == {
        "email_positive": 200,
        "hard_negative_email": 300,
        "hard_negative_phone": 400,
        "phone_positive": 300,
    }
    assert len({case.id for case in cases}) == 1200
    assert any("<PHONE_MOBILE" in case.marked_text for case in cases)
    assert any("<EMAIL" in case.marked_text for case in cases)


def test_stage3_address_generator_has_expected_bucket_counts() -> None:
    generator = _load_address_generator_module()

    cases = generator.build_cases()
    counts: dict[str, int] = {}
    for case in cases:
        counts[case.bucket] = counts.get(case.bucket, 0) + 1

    assert len(cases) == 600
    assert counts == {
        "address_full_positive": 200,
        "address_unit_positive": 200,
        "hard_negative_address": 200,
    }
    assert len({case.id for case in cases}) == 600
    assert any("<ADDRESS_FULL" in case.marked_text for case in cases)
    assert any("<ADDRESS_UNIT" in case.marked_text for case in cases)


def test_stage4_corporate_rrn_generator_has_expected_bucket_counts() -> None:
    generator = _load_corporate_rrn_generator_module()

    cases = generator.build_cases()
    counts: dict[str, int] = {}
    for case in cases:
        counts[case.bucket] = counts.get(case.bucket, 0) + 1

    assert len(cases) == 400
    assert counts == {
        "corporate_context_positive": 200,
        "rrn_context_positive": 200,
    }
    assert len({case.id for case in cases}) == 400
    assert any("<CORPORATE_REG_NO" in case.marked_text for case in cases)
    assert any("<RRN" in case.marked_text for case in cases)
    assert any("also passes RRN checksum" in (case.notes or "") for case in cases)


def test_stage5_numeric_identifier_generator_has_expected_bucket_counts() -> None:
    generator = _load_numeric_identifier_generator_module()

    cases = generator.build_cases()
    counts: dict[str, int] = {}
    for case in cases:
        counts[case.bucket] = counts.get(case.bucket, 0) + 1

    assert len(cases) == 900
    assert counts == {
        "bank_account_positive": 200,
        "business_context_positive": 200,
        "hard_negative_numeric_identifier": 300,
        "phone_positive": 200,
    }
    assert len({case.id for case in cases}) == 900
    assert any("<BUSINESS_REG_NO" in case.marked_text for case in cases)
    assert any("<BANK_ACCOUNT" in case.marked_text for case in cases)
    assert any("<PHONE_MOBILE" in case.marked_text for case in cases)
    assert sum(1 for case in cases if case.negative_reason is not None) == 300
