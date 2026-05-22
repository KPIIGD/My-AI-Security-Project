"""YAML configuration loaders for dictionary detection and context scoring.

The loaders parse a deliberately small subset of YAML to avoid adding a PyYAML
dependency, matching the style used by ``regex_detectors._load_simple_yaml_mapping``.

Supported shapes:

- Top-level block lists (``surnames:`` followed by ``- value``).
- Top-level indented mappings of float values (``regex_base_scores:``).
- Section-scoped flow lists (``field_labels:`` then ``  name_label: [성명, 이름]``).
- ``single_turn_composite.upgrades`` two-level mapping.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable


DEFAULT_CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs"


def load_dictionary_lists(path: Path | None = None) -> dict[str, tuple[str, ...]]:
    config_path = path or DEFAULT_CONFIG_DIR / "dictionaries.yaml"
    return _read_block_list_yaml(config_path)


def load_dictionary_base_scores(path: Path | None = None) -> dict[str, float]:
    config_path = path or DEFAULT_CONFIG_DIR / "scoring.yaml"
    return _read_indented_mapping(config_path, "dictionary_base_scores", float)


def load_context_boosts(path: Path | None = None) -> dict[str, float]:
    config_path = path or DEFAULT_CONFIG_DIR / "scoring.yaml"
    return _read_indented_mapping(config_path, "context_boosts", float)


def load_context_penalties(path: Path | None = None) -> dict[str, float]:
    config_path = path or DEFAULT_CONFIG_DIR / "scoring.yaml"
    return _read_indented_mapping(config_path, "context_penalties", float)


def load_score_bands(path: Path | None = None) -> dict[str, float]:
    config_path = path or DEFAULT_CONFIG_DIR / "scoring.yaml"
    return _read_indented_mapping(config_path, "score_bands", float)


def load_field_label_terms(path: Path | None = None) -> dict[str, tuple[str, ...]]:
    config_path = path or DEFAULT_CONFIG_DIR / "context_rules.yaml"
    return _read_flow_list_section(config_path, "field_labels")


def load_negative_context_terms(path: Path | None = None) -> dict[str, tuple[str, ...]]:
    config_path = path or DEFAULT_CONFIG_DIR / "context_rules.yaml"
    return _read_flow_list_section(config_path, "negative_contexts")


def load_honorific_terms(path: Path | None = None) -> dict[str, tuple[str, ...]]:
    config_path = path or DEFAULT_CONFIG_DIR / "context_rules.yaml"
    return _read_flow_list_section(config_path, "honorifics_and_titles")


def load_structured_context_terms(
    path: Path | None = None,
) -> dict[str, tuple[str, ...]]:
    config_path = path or DEFAULT_CONFIG_DIR / "context_rules.yaml"
    return _read_flow_list_section(config_path, "structured_identifier_contexts")


def load_entity_priority(path: Path | None = None) -> tuple[str, ...]:
    """Load ``priority_order`` block list from ``configs/entities.yaml``.

    Returns entity name strings in priority order (most important first).
    The caller is responsible for wrapping each name in ``EntityType``.
    """

    config_path = path or DEFAULT_CONFIG_DIR / "entities.yaml"
    lists = _read_block_list_yaml(config_path)
    return lists.get("priority_order", ())


def load_composite_upgrades(path: Path | None = None) -> dict[frozenset[str], str]:
    """Parse ``single_turn_composite.upgrades`` from scoring.yaml.

    The keys ``PERSON_NAME+PHONE_MOBILE`` become ``frozenset({...})`` so that
    entity-pair lookup is order-independent.
    """

    config_path = path or DEFAULT_CONFIG_DIR / "scoring.yaml"
    upgrades: dict[frozenset[str], str] = {}
    in_section = False
    in_upgrades = False
    for line in config_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not line.startswith(" "):
            in_section = line.rstrip(":") == "single_turn_composite"
            in_upgrades = False
            continue
        if not in_section:
            continue
        if line.startswith("  ") and not line.startswith("    "):
            in_upgrades = stripped == "upgrades:"
            continue
        if not in_upgrades or not line.startswith("    "):
            continue
        key, sep, value = stripped.partition(":")
        if not sep:
            continue
        entities = frozenset(part.strip() for part in key.split("+") if part.strip())
        if entities:
            upgrades[entities] = value.strip()
    return upgrades


# --------------------------------------------------------------------------- #
# low-level parsers                                                           #
# --------------------------------------------------------------------------- #


def _read_block_list_yaml(path: Path) -> dict[str, tuple[str, ...]]:
    result: dict[str, list[str]] = {}
    current_key: str | None = None
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not line[:1].isspace():
            if stripped.endswith(":"):
                current_key = stripped[:-1]
                result[current_key] = []
            else:
                current_key = None
            continue
        if current_key is None:
            continue
        if stripped.startswith("-"):
            value = stripped[1:].strip()
            value = value.strip("\"'")
            if value:
                result[current_key].append(value)
    return {key: tuple(values) for key, values in result.items() if values}


def _read_indented_mapping(
    path: Path, section: str, value_parser: Callable[[str], float]
) -> dict[str, float]:
    values: dict[str, float] = {}
    in_section = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" "):
            in_section = line.rstrip(":") == section
            continue
        if not in_section:
            continue
        if not line.startswith("  ") or line.startswith("    "):
            continue
        stripped = line.strip()
        key, sep, value = stripped.partition(":")
        if not sep:
            continue
        try:
            values[key.strip()] = value_parser(value.strip())
        except ValueError:
            continue
    if not values:
        raise ValueError(f"Missing or empty config section: {section}")
    return values


def _read_flow_list_section(path: Path, section: str) -> dict[str, tuple[str, ...]]:
    result: dict[str, list[str]] = {}
    in_section = False
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if not line.startswith(" "):
            in_section = line.rstrip(":") == section
            continue
        if not in_section:
            continue
        if not line.startswith("  ") or line.startswith("    "):
            continue
        stripped = line.strip()
        key, sep, value = stripped.partition(":")
        if not sep:
            continue
        value = value.strip()
        if not (value.startswith("[") and value.endswith("]")):
            continue
        items = [item.strip().strip("\"'") for item in value[1:-1].split(",")]
        result[key.strip()] = [item for item in items if item]
    return {key: tuple(values) for key, values in result.items() if values}
