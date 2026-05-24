"""M7 policy routing for Korean PII Guardrail v0.2.

The router consumes already resolved ``PIISpan`` instances and assigns the
final public action plus an internal transformation method. It does not resolve
overlaps and does not emit audit events; those belong to M6 and M8/M9.
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path

from .enums import Action, EntityType, OutputTarget, RiskLevel, Source
from .schema import GuardrailRequest, PIISpan


DEFAULT_CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs"
DEFAULT_POLICY_CONFIG_PATH = DEFAULT_CONFIG_DIR / "policy_profiles.yaml"
DEFAULT_SCORING_CONFIG_PATH = DEFAULT_CONFIG_DIR / "scoring.yaml"
_CONTACT_ENTITIES = frozenset(
    {EntityType.PHONE_MOBILE, EntityType.PHONE_LANDLINE, EntityType.EMAIL}
)
_PHONE_ENTITIES = frozenset({EntityType.PHONE_MOBILE, EntityType.PHONE_LANDLINE})


class PolicyConfigError(ValueError):
    """Raised when M7 policy configuration or request policy is unsupported."""


class TransformationMethod(StrEnum):
    PASS = "pass"
    LABEL_MASK = "label_mask"
    FULL_REDACT = "full_redact"
    HMAC_HASH = "hmac_hash"
    BLOCK = "block"


@dataclass(frozen=True)
class PolicyDecision:
    action: Action
    method: TransformationMethod
    reason_codes: tuple[str, ...]
    policy_profile: str
    output_target: OutputTarget


@dataclass(frozen=True)
class OutputTargetPolicy:
    default_method: TransformationMethod
    block_entities: frozenset[EntityType]


@dataclass(frozen=True)
class PolicyConfig:
    profiles: frozenset[str]
    output_targets: Mapping[OutputTarget, OutputTargetPolicy]
    entity_overrides: Mapping[EntityType, Mapping[str, TransformationMethod]]
    placeholder_format: str
    stable_within_request: bool
    cross_request_stable: bool


@dataclass(frozen=True)
class RiskActionThresholds:
    p0_mask_min_score: float
    p0_structured_like_min_score: float
    p1_mask_min_score: float
    p1_context_judge_min_score: float
    p2_mask_min_score: float
    p2_context_judge_min_score: float
    p3_composite_mask_min_score: float


class PolicyRouter:
    """Select final actions for resolved candidate spans."""

    detector_id = "policy.strict"
    source = Source.POLICY.value

    def __init__(
        self,
        *,
        policy_config: PolicyConfig | None = None,
        thresholds: RiskActionThresholds | None = None,
    ) -> None:
        self.policy_config = policy_config or load_policy_config()
        self.thresholds = thresholds or load_risk_action_thresholds()

    def select(self, span: PIISpan, request: GuardrailRequest) -> PolicyDecision:
        profile = self._validate_profile(request.policy_profile)
        output_target = self._validate_output_target(request.output_target)

        if output_target is OutputTarget.AUDIT_LOG:
            return PolicyDecision(
                action=Action.HASH,
                method=TransformationMethod.HMAC_HASH,
                reason_codes=("policy.target.audit_log", "policy.method.hmac_hash"),
                policy_profile=profile,
                output_target=output_target,
            )

        target_policy = self.policy_config.output_targets[output_target]
        if span.entity_type in target_policy.block_entities:
            return self._decision(
                Action.BLOCK,
                TransformationMethod.BLOCK,
                profile,
                output_target,
                "policy.target.block_entity",
            )

        override = self._entity_override(span.entity_type, profile, output_target)
        if override is TransformationMethod.BLOCK:
            return self._decision(
                Action.BLOCK,
                TransformationMethod.BLOCK,
                profile,
                output_target,
                "policy.override.block",
            )
        if override is TransformationMethod.FULL_REDACT:
            return self._decision(
                Action.MASK,
                TransformationMethod.FULL_REDACT,
                profile,
                output_target,
                "policy.override.full_redact",
            )

        if span.entity_type is EntityType.API_KEY_SECRET:
            return self._decision(
                Action.BLOCK,
                TransformationMethod.BLOCK,
                profile,
                output_target,
                "policy.entity.api_key_secret",
            )

        if self._has_decisive_negative_context(span):
            return self._pass_decision(
                profile,
                output_target,
                "policy.negative_context.pass",
            )

        if span.risk_level is RiskLevel.P0:
            if self._p0_should_mask(span):
                return self._decision(
                    Action.MASK,
                    TransformationMethod.FULL_REDACT,
                    profile,
                    output_target,
                    "policy.risk.p0_full_redact",
                )
            return self._pass_decision(profile, output_target, "policy.risk.p0_below_threshold")

        if span.is_composite:
            return self._decision(
                Action.MASK,
                TransformationMethod.LABEL_MASK,
                profile,
                output_target,
                "policy.composite.mask",
            )

        if span.risk_level is RiskLevel.P1:
            if span.score >= self.thresholds.p1_mask_min_score:
                return self._decision(
                    Action.MASK,
                    TransformationMethod.LABEL_MASK,
                    profile,
                    output_target,
                    "policy.risk.p1_threshold",
                )
            if (
                span.score >= self.thresholds.p1_context_judge_min_score
                and self._has_strong_context(span)
            ):
                return self._decision(
                    Action.MASK,
                    TransformationMethod.LABEL_MASK,
                    profile,
                    output_target,
                    "policy.risk.p1_context",
                )
            return self._pass_decision(profile, output_target, "policy.risk.p1_below_threshold")

        if span.risk_level is RiskLevel.P2:
            if (
                span.score >= self.thresholds.p2_context_judge_min_score
                and self._has_strong_context(span)
            ):
                return self._decision(
                    Action.MASK,
                    TransformationMethod.LABEL_MASK,
                    profile,
                    output_target,
                    "policy.risk.p2_context",
                )
            return self._pass_decision(profile, output_target, "policy.risk.p2_no_context")

        if span.risk_level is RiskLevel.P3:
            if (
                span.score >= self.thresholds.p3_composite_mask_min_score
                and self._has_strong_context(span)
            ):
                return self._decision(
                    Action.MASK,
                    TransformationMethod.LABEL_MASK,
                    profile,
                    output_target,
                    "policy.risk.p3_context",
                )
            return self._pass_decision(profile, output_target, "policy.risk.p3_no_context")

        return self._pass_decision(profile, output_target, "policy.risk.unknown")

    def route(self, spans: list[PIISpan], request: GuardrailRequest) -> list[PIISpan]:
        """Return spans with final M7 action metadata applied."""

        return [self.apply(span, request) for span in spans]

    def apply(self, span: PIISpan, request: GuardrailRequest) -> PIISpan:
        decision = self.select(span, request)
        return replace(
            span,
            action=decision.action,
            sources=_append_unique(span.sources, Source.POLICY.value),
            reason_codes=_ordered_union(span.reason_codes, decision.reason_codes),
            detector_ids=_append_unique(span.detector_ids, self.detector_id),
            policy_profile=decision.policy_profile,
            output_target=decision.output_target,
        )

    def _validate_profile(self, profile: str) -> str:
        if profile not in self.policy_config.profiles:
            raise PolicyConfigError("Unsupported policy profile")
        return profile

    def _validate_output_target(self, output_target: OutputTarget | str) -> OutputTarget:
        try:
            target = OutputTarget(output_target)
        except ValueError as exc:
            raise PolicyConfigError("Unsupported output target") from exc
        if target not in self.policy_config.output_targets:
            raise PolicyConfigError("Unsupported output target")
        return target

    def _entity_override(
        self, entity_type: EntityType, profile: str, output_target: OutputTarget
    ) -> TransformationMethod | None:
        overrides = self.policy_config.entity_overrides.get(entity_type, {})
        target_override = overrides.get(output_target.value)
        if target_override is not None:
            return target_override
        return overrides.get(profile)

    def _p0_should_mask(self, span: PIISpan) -> bool:
        if span.score >= self.thresholds.p0_mask_min_score:
            return True
        if span.score < self.thresholds.p0_structured_like_min_score:
            return False
        return any(source in span.sources for source in (Source.REGEX.value, Source.VALIDATOR.value))

    @staticmethod
    def _has_strong_context(span: PIISpan) -> bool:
        if span.is_composite:
            return True
        return any(
            code.startswith(("context.boost.", "context.composite."))
            for code in span.reason_codes
        )

    @staticmethod
    def _has_context_boost(span: PIISpan) -> bool:
        return any(code.startswith("context.boost.") for code in span.reason_codes)

    @staticmethod
    def _has_decisive_negative_context(span: PIISpan) -> bool:
        has_example_context = any(
            code.startswith(
                (
                    "context.penalty.example_context",
                    "context.penalty.example_keyword_for_person",
                )
            )
            for code in span.reason_codes
        )
        if span.entity_type in _CONTACT_ENTITIES:
            has_direct_boost = PolicyRouter._has_context_boost(span)
            if has_example_context and not has_direct_boost:
                return True
            return span.entity_type in _PHONE_ENTITIES and any(
                code.startswith("context.penalty.public_phone_context")
                for code in span.reason_codes
            )

        if span.entity_type is not EntityType.PERSON_NAME:
            return False
        has_boost = any(
            code.startswith("context.boost.") for code in span.reason_codes
        )
        if has_example_context and not has_boost:
            return True
        if span.is_composite:
            return False
        has_negative = any(
            code.startswith(
                (
                    "context.penalty.weather_context_for_person",
                    "context.penalty.organization_not_person",
                    "context.penalty.example_context",
                    "context.penalty.example_keyword_for_person",
                    "context.penalty.code_or_log_context",
                )
            )
            for code in span.reason_codes
        )
        if not has_negative:
            return False
        return not has_boost

    @staticmethod
    def _decision(
        action: Action,
        method: TransformationMethod,
        profile: str,
        output_target: OutputTarget,
        reason_code: str,
    ) -> PolicyDecision:
        return PolicyDecision(
            action=action,
            method=method,
            reason_codes=(
                f"policy.profile.{profile}",
                f"policy.target.{output_target.value}",
                f"policy.action.{action.value}",
                f"policy.method.{method.value}",
                reason_code,
            ),
            policy_profile=profile,
            output_target=output_target,
        )

    def _pass_decision(
        self, profile: str, output_target: OutputTarget, reason_code: str
    ) -> PolicyDecision:
        return self._decision(
            Action.PASS,
            TransformationMethod.PASS,
            profile,
            output_target,
            reason_code,
        )


def load_policy_config(path: Path | None = None) -> PolicyConfig:
    config_path = path or DEFAULT_POLICY_CONFIG_PATH
    lines = config_path.read_text(encoding="utf-8").splitlines()

    profiles: set[str] = set()
    output_targets: dict[OutputTarget, OutputTargetPolicy] = {}
    target_methods: dict[OutputTarget, TransformationMethod] = {}
    target_block_entities: dict[OutputTarget, set[EntityType]] = {}
    entity_overrides: dict[EntityType, dict[str, TransformationMethod]] = {}
    placeholder_format = "[{entity_family}_{index}]"
    stable_within_request = True
    cross_request_stable = False

    section: str | None = None
    current_target: OutputTarget | None = None
    current_entity: EntityType | None = None

    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not line.startswith(" "):
            section = stripped[:-1] if stripped.endswith(":") else None
            current_target = None
            current_entity = None
            continue

        if section == "profiles":
            if _indent_level(line) == 2 and stripped.endswith(":"):
                profiles.add(stripped[:-1])
            continue

        if section == "output_targets":
            if _indent_level(line) == 2 and stripped.endswith(":"):
                current_target = _parse_output_target(stripped[:-1])
                target_block_entities.setdefault(current_target, set())
                continue
            if current_target is None or _indent_level(line) != 4:
                continue
            key, value = _parse_key_value(stripped)
            if key == "default_method":
                target_methods[current_target] = TransformationMethod(value)
            elif key == "block_entities":
                target_block_entities[current_target].update(
                    EntityType(item) for item in _parse_flow_list(value)
                )
            continue

        if section == "entity_overrides":
            if _indent_level(line) == 2 and stripped.endswith(":"):
                current_entity = EntityType(stripped[:-1])
                entity_overrides.setdefault(current_entity, {})
                continue
            if current_entity is None or _indent_level(line) != 4:
                continue
            key, value = _parse_key_value(stripped)
            entity_overrides[current_entity][key] = TransformationMethod(value)
            continue

        if section == "placeholder" and _indent_level(line) == 2:
            key, value = _parse_key_value(stripped)
            if key == "format":
                placeholder_format = value.strip("\"'")
            elif key == "stable_within_request":
                stable_within_request = _parse_bool(value)
            elif key == "cross_request_stable":
                cross_request_stable = _parse_bool(value)

    if not profiles:
        raise PolicyConfigError("Policy config has no profiles")
    if not target_methods:
        raise PolicyConfigError("Policy config has no output targets")

    for target, method in target_methods.items():
        output_targets[target] = OutputTargetPolicy(
            default_method=method,
            block_entities=frozenset(target_block_entities.get(target, set())),
        )

    return PolicyConfig(
        profiles=frozenset(profiles),
        output_targets=output_targets,
        entity_overrides=entity_overrides,
        placeholder_format=placeholder_format,
        stable_within_request=stable_within_request,
        cross_request_stable=cross_request_stable,
    )


def load_risk_action_thresholds(path: Path | None = None) -> RiskActionThresholds:
    config_path = path or DEFAULT_SCORING_CONFIG_PATH
    values: dict[RiskLevel, dict[str, float]] = {}
    in_section = False
    current_risk: RiskLevel | None = None

    for line in config_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if not line.startswith(" "):
            in_section = stripped == "risk_action_thresholds:"
            current_risk = None
            continue
        if not in_section:
            continue
        if _indent_level(line) == 2 and stripped.endswith(":"):
            current_risk = RiskLevel(stripped[:-1])
            values[current_risk] = {}
            continue
        if current_risk is None or _indent_level(line) != 4:
            continue
        key, value = _parse_key_value(stripped)
        values[current_risk][key] = float(value)

    try:
        return RiskActionThresholds(
            p0_mask_min_score=values[RiskLevel.P0]["mask_min_score"],
            p0_structured_like_min_score=values[RiskLevel.P0]["structured_like_min_score"],
            p1_mask_min_score=values[RiskLevel.P1]["mask_min_score"],
            p1_context_judge_min_score=values[RiskLevel.P1]["context_judge_min_score"],
            p2_mask_min_score=values[RiskLevel.P2]["mask_min_score"],
            p2_context_judge_min_score=values[RiskLevel.P2]["context_judge_min_score"],
            p3_composite_mask_min_score=values[RiskLevel.P3]["composite_mask_min_score"],
        )
    except KeyError as exc:
        raise PolicyConfigError("Missing risk action threshold") from exc


def _parse_output_target(value: str) -> OutputTarget:
    try:
        return OutputTarget(value)
    except ValueError as exc:
        raise PolicyConfigError("Unsupported output target in policy config") from exc


def _parse_key_value(stripped_line: str) -> tuple[str, str]:
    key, separator, value = stripped_line.partition(":")
    if not separator:
        raise PolicyConfigError("Malformed policy config line")
    return key.strip(), value.strip()


def _parse_flow_list(value: str) -> tuple[str, ...]:
    if not (value.startswith("[") and value.endswith("]")):
        raise PolicyConfigError("Expected YAML flow list")
    return tuple(
        item.strip().strip("\"'")
        for item in value[1:-1].split(",")
        if item.strip()
    )


def _parse_bool(value: str) -> bool:
    if value == "true":
        return True
    if value == "false":
        return False
    raise PolicyConfigError("Expected boolean config value")


def _indent_level(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _append_unique(existing: tuple[str, ...], value: str) -> tuple[str, ...]:
    if value in existing:
        return existing
    return (*existing, value)


def _ordered_union(left: tuple[str, ...], right: tuple[str, ...]) -> tuple[str, ...]:
    result: list[str] = []
    for item in (*left, *right):
        if item not in result:
            result.append(item)
    return tuple(result)
