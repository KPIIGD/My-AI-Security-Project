"""Configuration surface for detector and validator routing."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from .enums import EntityType


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "detectors.yaml"
SUPPORTED_CHECKSUM_MODES = frozenset({"strict", "warn", "off"})
DEFAULT_CHECKSUM_MODES = {
    "BUSINESS_REG_NO": "warn",
}


@dataclass(frozen=True)
class DetectorPolicy:
    """Runtime detector policy loaded from ``configs/detectors.yaml``.

    The policy is intentionally coarse-grained for v0.2:
    regex detector IDs can be disabled, entity types can be filtered after
    candidate generation, and selected validators can choose checksum mode.
    Request-time regex injection is not supported.
    """

    regex_detectors_enabled: Mapping[str, bool] = field(default_factory=dict)
    entities_enabled: Mapping[EntityType | str, bool] = field(default_factory=dict)
    checksum_modes: Mapping[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        regex_detectors = {
            str(detector_id): bool(enabled)
            for detector_id, enabled in self.regex_detectors_enabled.items()
        }
        entities: dict[EntityType, bool] = {}
        for entity, enabled in self.entities_enabled.items():
            entity_type = entity if isinstance(entity, EntityType) else EntityType(str(entity))
            entities[entity_type] = bool(enabled)

        checksum_modes = dict(DEFAULT_CHECKSUM_MODES)
        for name, mode in self.checksum_modes.items():
            checksum_modes[str(name)] = _normalize_checksum_mode(mode)

        object.__setattr__(self, "regex_detectors_enabled", regex_detectors)
        object.__setattr__(self, "entities_enabled", entities)
        object.__setattr__(self, "checksum_modes", checksum_modes)

    def regex_detector_enabled(self, detector_id: str) -> bool:
        return self.regex_detectors_enabled.get(detector_id, True)

    def entity_enabled(self, entity_type: EntityType) -> bool:
        return self.entities_enabled.get(entity_type, True)

    def checksum_mode(self, name: str | EntityType) -> str:
        key = name.value if isinstance(name, EntityType) else str(name)
        return self.checksum_modes.get(key, "strict")


def load_detector_policy(path: Path | None = None) -> DetectorPolicy:
    config_path = path or DEFAULT_CONFIG_PATH
    if not config_path.is_file():
        return DetectorPolicy()

    regex_detectors = _parse_enabled_mapping(config_path, "regex_detectors")
    raw_entities = _parse_enabled_mapping(config_path, "entities")
    entities = {EntityType(name): enabled for name, enabled in raw_entities.items()}
    checksum_modes = _parse_checksum_modes(config_path)
    return DetectorPolicy(
        regex_detectors_enabled=regex_detectors,
        entities_enabled=entities,
        checksum_modes=checksum_modes,
    )


def _parse_enabled_mapping(path: Path, section: str) -> dict[str, bool]:
    values: dict[str, bool] = {}
    current_section: str | None = None
    current_key: str | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        stripped = line.strip()
        if not stripped:
            continue

        if not line.startswith(" "):
            current_section = stripped[:-1] if stripped.endswith(":") else None
            current_key = None
            continue

        if current_section != section:
            continue

        if line.startswith("  ") and not line.startswith("    ") and stripped.endswith(":"):
            current_key = stripped[:-1]
            continue

        if current_key and line.startswith("    "):
            key, separator, value = stripped.partition(":")
            if separator and key == "enabled":
                values[current_key] = _parse_bool(value.strip(), path=path, key=current_key)

    return values


def _parse_checksum_modes(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    current_section: str | None = None
    current_key: str | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        stripped = line.strip()
        if not stripped:
            continue

        if not line.startswith(" "):
            current_section = stripped[:-1] if stripped.endswith(":") else None
            current_key = None
            continue

        if current_section != "validators":
            continue

        if line.startswith("  ") and not line.startswith("    ") and stripped.endswith(":"):
            current_key = stripped[:-1]
            continue

        if current_key and line.startswith("    "):
            key, separator, value = stripped.partition(":")
            if separator and key == "checksum":
                values[current_key] = _normalize_checksum_mode(value.strip())

    return values


def _parse_bool(value: str, *, path: Path, key: str) -> bool:
    normalized = value.lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ValueError(f"Invalid enabled value in {path.name} for {key}")


def _normalize_checksum_mode(mode: str) -> str:
    normalized = mode.strip().lower()
    if normalized not in SUPPORTED_CHECKSUM_MODES:
        raise ValueError("Unsupported checksum mode")
    return normalized


__all__ = [
    "DetectorPolicy",
    "load_detector_policy",
]
