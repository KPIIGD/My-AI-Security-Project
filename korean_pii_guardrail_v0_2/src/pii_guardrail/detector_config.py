"""Configuration surface for detector and validator routing."""

from __future__ import annotations

import warnings
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from .enums import EntityType


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "detectors.yaml"
SUPPORTED_CHECKSUM_MODES = frozenset({"strict", "warn", "off"})
SUPPORTED_REGEX_DETECTORS = frozenset(
    {
        "regex.rrn",
        "regex.frn",
        "regex.phone",
        "regex.email",
        "regex.network",
        "regex.credit_card",
        "regex.business_reg_no",
        "regex.passport",
        "regex.driver_license",
        "regex.corporate_reg_no",
        "regex.labeled_identifier",
        "regex.bank_account",
        "regex.secret",
    }
)
SUPPORTED_CHECKSUM_VALIDATORS = frozenset({"RRN", "FRN", "CREDIT_CARD", "BUSINESS_REG_NO"})
HIGH_RISK_DISABLE_ENTITIES = frozenset(
    {
        EntityType.API_KEY_SECRET,
        EntityType.RRN,
        EntityType.FRN,
        EntityType.PASSPORT,
        EntityType.DRIVER_LICENSE,
        EntityType.CREDIT_CARD,
        EntityType.BANK_ACCOUNT,
        EntityType.BUSINESS_REG_NO,
        EntityType.CORPORATE_REG_NO,
        EntityType.MEDICAL_RECORD_NO,
        EntityType.VEHICLE_REG_NO,
        EntityType.PHONE_MOBILE,
        EntityType.PHONE_LANDLINE,
        EntityType.EMAIL,
    }
)
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
            checksum_modes[str(name)] = _normalize_checksum_mode(mode, context=str(name))

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

    regex_detectors = _parse_enabled_mapping(
        config_path,
        "regex_detectors",
        supported_keys=SUPPORTED_REGEX_DETECTORS,
    )
    raw_entities = _parse_enabled_mapping(
        config_path,
        "entities",
        supported_keys={entity.value for entity in EntityType},
    )
    entities = {EntityType(name): enabled for name, enabled in raw_entities.items()}
    _warn_for_high_risk_entity_disables(config_path, entities)
    checksum_modes = _parse_checksum_modes(config_path)
    return DetectorPolicy(
        regex_detectors_enabled=regex_detectors,
        entities_enabled=entities,
        checksum_modes=checksum_modes,
    )


def _parse_enabled_mapping(
    path: Path,
    section: str,
    *,
    supported_keys: frozenset[str] | set[str] | None = None,
) -> dict[str, bool]:
    values: dict[str, bool] = {}
    current_section: str | None = None
    current_key: str | None = None

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.split("#", 1)[0].rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if "\t" in line[: len(line) - len(line.lstrip())]:
            _warn_config(path, line_number, f"Tab indentation is not supported in {section}")
            current_key = None
            continue

        if not line.startswith(" "):
            current_section = stripped[:-1] if stripped.endswith(":") else None
            current_key = None
            continue

        if current_section != section:
            continue

        if line.startswith("  ") and not line.startswith("    "):
            if not stripped.endswith(":"):
                _warn_config(path, line_number, f"Malformed entry in {section}: expected '<key>:'")
                current_key = None
                continue
            candidate_key = stripped[:-1]
            if supported_keys is not None and candidate_key not in supported_keys:
                _warn_config(path, line_number, f"Unknown {section} key ignored: {candidate_key}")
                current_key = None
                continue
            current_key = candidate_key
            continue

        if current_key and line.startswith("    "):
            key, separator, value = stripped.partition(":")
            if separator and key == "enabled":
                values[current_key] = _parse_bool(value.strip(), path=path, key=current_key)
                continue
            _warn_config(path, line_number, f"Unknown setting ignored for {section}.{current_key}: {key or stripped}")
            continue

        _warn_config(path, line_number, f"Malformed indentation in {section}: {stripped}")

    return values


def _parse_checksum_modes(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    current_section: str | None = None
    current_key: str | None = None

    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        line = raw_line.split("#", 1)[0].rstrip()
        stripped = line.strip()
        if not stripped:
            continue
        if "\t" in line[: len(line) - len(line.lstrip())]:
            _warn_config(path, line_number, "Tab indentation is not supported in validators")
            current_key = None
            continue

        if not line.startswith(" "):
            current_section = stripped[:-1] if stripped.endswith(":") else None
            current_key = None
            continue

        if current_section != "validators":
            continue

        if line.startswith("  ") and not line.startswith("    "):
            if not stripped.endswith(":"):
                _warn_config(path, line_number, "Malformed entry in validators: expected '<ENTITY>:'")
                current_key = None
                continue
            candidate_key = stripped[:-1]
            if candidate_key not in SUPPORTED_CHECKSUM_VALIDATORS:
                _warn_config(path, line_number, f"Unknown checksum validator ignored: {candidate_key}")
                current_key = None
                continue
            current_key = candidate_key
            continue

        if current_key and line.startswith("    "):
            key, separator, value = stripped.partition(":")
            if separator and key == "checksum":
                values[current_key] = _normalize_checksum_mode(
                    value.strip(),
                    context=f"{current_key}.checksum",
                )
                continue
            _warn_config(path, line_number, f"Unknown setting ignored for validators.{current_key}: {key or stripped}")
            continue

        _warn_config(path, line_number, f"Malformed indentation in validators: {stripped}")

    return values


def _parse_bool(value: str, *, path: Path, key: str) -> bool:
    normalized = value.lower()
    if normalized == "true":
        return True
    if normalized == "false":
        return False
    raise ValueError(f"Invalid enabled value in {path.name} for {key}")


def _normalize_checksum_mode(mode: str, *, context: str | None = None) -> str:
    normalized = mode.strip().lower()
    if normalized not in SUPPORTED_CHECKSUM_MODES:
        scope = f" for {context}" if context else ""
        supported = ", ".join(sorted(SUPPORTED_CHECKSUM_MODES))
        raise ValueError(f"Unsupported checksum mode{scope}: {mode!r}. Supported modes: {supported}")
    return normalized


def _warn_for_high_risk_entity_disables(path: Path, entities: Mapping[EntityType, bool]) -> None:
    for entity, enabled in entities.items():
        if not enabled and entity in HIGH_RISK_DISABLE_ENTITIES:
            _warn_config(
                path,
                None,
                f"Disabling high-risk entity {entity.value} can violate P0/P1 release gates",
            )


def _warn_config(path: Path, line_number: int | None, message: str) -> None:
    location = f"{path.name}:{line_number}" if line_number is not None else path.name
    warnings.warn(f"{location}: {message}", RuntimeWarning, stacklevel=3)


__all__ = [
    "DetectorPolicy",
    "load_detector_policy",
]
