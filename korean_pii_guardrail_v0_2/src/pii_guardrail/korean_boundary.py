"""Korean suffix boundary correction for candidate PII spans."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path

from .enums import EntityType
from .interfaces import PreprocessResult
from .schema import PIISpan


DEFAULT_CONFIG_PATH = Path(__file__).resolve().parents[2] / "configs" / "josa_rules.yaml"
_UNSET = object()


@dataclass(frozen=True)
class SuffixRule:
    suffix: str
    group: str


class KoreanBoundaryCorrector:
    """Split Korean particles/endings from PII bodies without changing final policy."""

    def __init__(
        self,
        *,
        config_path: Path | None = None,
        rules: Mapping[EntityType, tuple[SuffixRule, ...]] | None = None,
    ) -> None:
        loaded_rules = rules if rules is not None else load_suffix_rules(config_path)
        self._rules = {entity: _sort_rules(entity_rules) for entity, entity_rules in loaded_rules.items()}

    def correct(self, span: PIISpan, preprocessed: PreprocessResult) -> PIISpan:
        if span.suffix:
            return span

        rules = self._rules.get(span.entity_type)
        if not rules:
            return span

        raw_text = preprocessed.raw_text
        corrected = self._trim_internal_suffix(span, raw_text, rules)
        if corrected is not None:
            return corrected

        corrected = self._capture_lookahead_suffix(span, raw_text, rules)
        if corrected is not None:
            return corrected

        return span

    def _trim_internal_suffix(self, span: PIISpan, raw_text: str, rules: tuple[SuffixRule, ...]) -> PIISpan | None:
        for rule in rules:
            if not span.text.endswith(rule.suffix) or len(span.text) <= len(rule.suffix):
                continue
            corrected = _copy_span(
                span,
                end=span.end - len(rule.suffix),
                text=span.text[: -len(rule.suffix)],
                suffix=rule.suffix,
                normalized=None,
                reason_codes=_append_reason_codes(
                    span.reason_codes,
                    "boundary.suffix_trim",
                    f"suffix.{rule.group}",
                ),
            )
            corrected.validate_against(raw_text)
            return corrected
        return None

    def _capture_lookahead_suffix(self, span: PIISpan, raw_text: str, rules: tuple[SuffixRule, ...]) -> PIISpan | None:
        for rule in rules:
            if not raw_text.startswith(rule.suffix, span.end):
                continue
            corrected = _copy_span(
                span,
                suffix=rule.suffix,
                reason_codes=_append_reason_codes(
                    span.reason_codes,
                    "boundary.suffix_lookahead",
                    f"suffix.{rule.group}",
                ),
            )
            corrected.validate_against(raw_text)
            return corrected
        return None


def load_suffix_rules(path: Path | None = None) -> dict[EntityType, tuple[SuffixRule, ...]]:
    config_path = path or DEFAULT_CONFIG_PATH
    suffix_groups, entity_application = _parse_josa_rules(config_path)

    rules: dict[EntityType, tuple[SuffixRule, ...]] = {}
    for entity_name, group_names in entity_application.items():
        entity_type = EntityType(entity_name)
        entity_rules: list[SuffixRule] = []
        for group_name in group_names:
            try:
                suffixes = suffix_groups[group_name]
            except KeyError as exc:
                raise ValueError(f"Unknown suffix group for {entity_name}: {group_name}") from exc
            entity_rules.extend(SuffixRule(suffix=suffix, group=group_name) for suffix in suffixes)
        rules[entity_type] = _sort_rules(tuple(entity_rules))

    if not rules:
        raise ValueError("No boundary suffix rules loaded")
    return rules


def _parse_josa_rules(path: Path) -> tuple[dict[str, tuple[str, ...]], dict[str, tuple[str, ...]]]:
    suffix_groups: dict[str, list[str]] = {}
    entity_application: dict[str, tuple[str, ...]] = {}
    section: str | None = None
    current_group: str | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        stripped = line.strip()
        if not stripped:
            continue

        if not line.startswith(" ") and stripped.endswith(":"):
            section = stripped[:-1]
            current_group = None
            continue

        if section == "suffix_groups":
            if line.startswith("  ") and not line.startswith("    ") and stripped.endswith(":"):
                current_group = stripped[:-1]
                suffix_groups[current_group] = []
                continue
            if current_group and stripped.startswith("- "):
                suffix = stripped[2:].strip()
                if suffix:
                    suffix_groups[current_group].append(suffix)
                continue

        if section == "entity_application" and line.startswith("  "):
            entity_name, separator, value = stripped.partition(":")
            if not separator:
                continue
            entity_application[entity_name] = _parse_inline_list(value.strip())

    if not suffix_groups:
        raise ValueError(f"Missing suffix_groups in {path}")
    if not entity_application:
        raise ValueError(f"Missing entity_application in {path}")

    return {name: tuple(values) for name, values in suffix_groups.items()}, entity_application


def _parse_inline_list(value: str) -> tuple[str, ...]:
    if not (value.startswith("[") and value.endswith("]")):
        raise ValueError(f"Expected inline list in josa_rules.yaml, got: {value}")
    inner = value[1:-1].strip()
    if not inner:
        return ()
    return tuple(item.strip() for item in inner.split(",") if item.strip())


def _sort_rules(rules: tuple[SuffixRule, ...]) -> tuple[SuffixRule, ...]:
    indexed_rules = tuple(enumerate(rules))
    return tuple(rule for _, rule in sorted(indexed_rules, key=lambda item: (-len(item[1].suffix), item[0])))


def _append_reason_codes(existing: tuple[str, ...], *new_codes: str) -> tuple[str, ...]:
    result = list(existing)
    for code in new_codes:
        if code not in result:
            result.append(code)
    return tuple(result)


def _copy_span(
    span: PIISpan,
    *,
    start: int | None = None,
    end: int | None = None,
    text: str | None = None,
    normalized: str | None | object = _UNSET,
    suffix: str | None = None,
    reason_codes: tuple[str, ...] | None = None,
) -> PIISpan:
    return PIISpan(
        start=span.start if start is None else start,
        end=span.end if end is None else end,
        text=span.text if text is None else text,
        entity_type=span.entity_type,
        score=span.score,
        sources=span.sources,
        risk_level=span.risk_level,
        action=span.action,
        normalized=span.normalized if normalized is _UNSET else normalized,
        suffix=span.suffix if suffix is None else suffix,
        reason_codes=span.reason_codes if reason_codes is None else reason_codes,
        detector_ids=span.detector_ids,
        is_composite=span.is_composite,
        policy_profile=span.policy_profile,
        output_target=span.output_target,
    )
