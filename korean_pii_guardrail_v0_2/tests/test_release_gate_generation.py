import importlib.util
import sys
from pathlib import Path

from pii_guardrail.enums import EntityType


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def _load_release_gate_script():
    path = PROJECT_ROOT / "scripts" / "run_release_gate.py"
    spec = importlib.util.spec_from_file_location("run_release_gate_for_test", path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _cases_by_id(cases):
    return {case.id: case for case in cases}


def _label_types(case):
    return tuple(label.entity_type for label in case.labels)


def test_release_gate_name_address_templates_label_every_embedded_pii() -> None:
    run_release_gate = _load_release_gate_script()
    cases = _cases_by_id(run_release_gate.generate_release_gate_cases(8))

    assert _label_types(cases["name_address_affiliation-0001"]) == (
        EntityType.PERSON_NAME,
        EntityType.ADDRESS_FULL,
    )
    assert _label_types(cases["name_address_affiliation-0003"]) == (
        EntityType.PERSON_NAME,
        EntityType.ORGANIZATION,
    )
    assert _label_types(cases["name_address_affiliation-0006"]) == (
        EntityType.FAMILY_RELATION,
        EntityType.PHONE_MOBILE,
    )
    assert _label_types(cases["name_address_affiliation-0007"]) == (
        EntityType.PERSON_NAME,
        EntityType.ADDRESS_FULL,
    )


def test_release_gate_adversarial_person_contact_template_labels_contact() -> None:
    run_release_gate = _load_release_gate_script()
    cases = _cases_by_id(run_release_gate.generate_release_gate_cases(1))

    assert _label_types(cases["adversarial_boundary-0000"]) == (
        EntityType.PERSON_NAME,
        EntityType.PHONE_MOBILE,
    )
