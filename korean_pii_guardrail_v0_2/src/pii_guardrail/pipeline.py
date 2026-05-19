"""M9 end-to-end Korean PII Guardrail pipeline.

Wires together every stage of the v0.2 single-turn flow:

    GuardrailRequest
        │
        ▼
    M1 preprocess  ──────►  PreprocessResult (raw + normalized + offset map)
        │
        ▼
    M2 regex detectors + M2.5 dictionary detector + M5 NER (optional)
        │              candidate PIISpan[] (raw-offset contract)
        ▼
    M3 boundary corrector  ──►  trim josa/honorific/ending suffix on each span
        │
        ▼
    M4 context scorer       ──►  boost/penalty + is_composite hints
        │
        ▼
    M6 span resolver        ──►  duplicate merge / overlap winner / address fragments / composite escalation
        │
        ▼
    M7 policy router        ──►  Action + TransformationMethod per span
        │
        ▼
    M7 masker               ──►  masked_text | None (BLOCK)
        │
        ▼
    M8 audit logger         ──►  per-span AuditEvent (optional, fail-closed)
        │
        ▼
    GuardrailResponse

The pipeline accepts an optional ``BaseNERDetector`` (default: ``MockNERDetector``)
so callers can swap in the v3 finetuned model without touching pipeline code.
"""

from __future__ import annotations

import time
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from .audit_logger import AuditLogger, AuditPayloadLeakError
from .context_scorer import ContextScorer
from .detector_config import DetectorPolicy, load_detector_policy
from .dictionary_loader import (
    load_composite_upgrades,
    load_context_boosts,
    load_context_penalties,
    load_dictionary_base_scores,
    load_dictionary_lists,
    load_entity_priority,
    load_field_label_terms,
    load_honorific_terms,
    load_negative_context_terms,
)
from .dictionary_detectors import DictionaryDetector
from .enums import Action, EntityType, RiskLevel
from .korean_boundary import KoreanBoundaryCorrector
from .masker import SuffixPreservingMasker
from .ner import BaseNERDetector, MockNERDetector
from .policy import PolicyRouter, load_policy_config, load_risk_action_thresholds
from .preprocess import preprocess_text
from .regex_detectors import (
    BankAccountCandidateDetector,
    BusinessRegNoDetector,
    CreditCardRegexDetector,
    EmailRegexDetector,
    FRNRegexDetector,
    NetworkIdentifierDetector,
    PhoneRegexDetector,
    RRNRegexDetector,
    SecretRegexDetector,
    deduplicate_spans,
    load_entity_risk_levels,
    load_regex_base_scores,
)
from .schema import (
    AuditEvent,
    GuardrailRequest,
    GuardrailResponse,
    PIISpan,
    PublicPIISpan,
    ResponseMetrics,
)
from .span_resolver import SpanResolver


@dataclass(frozen=True)
class _ConfigPaths:
    root: Path
    dictionaries: Path
    scoring: Path
    policy_profiles: Path
    josa_rules: Path
    entities: Path
    context_rules: Path
    detectors: Path


@dataclass(frozen=True)
class PipelineComponents:
    """Container for swappable pipeline stages.

    Kept as a frozen dataclass so test fixtures and production callers can
    construct a ``GuardrailPipeline`` from a curated set of detectors
    without reaching into private attributes.
    """

    regex_detectors: tuple[object, ...]
    dictionary_detector: DictionaryDetector
    boundary_corrector: KoreanBoundaryCorrector
    context_scorer: ContextScorer
    ner_detector: BaseNERDetector | None
    span_resolver: SpanResolver
    policy_router: PolicyRouter
    masker: SuffixPreservingMasker
    audit_logger: AuditLogger | None
    detector_policy: DetectorPolicy


def _default_regex_detectors(
    *,
    scores: dict[str, float] | None = None,
    risk_levels: dict[EntityType, RiskLevel] | None = None,
    detector_policy: DetectorPolicy | None = None,
) -> tuple[object, ...]:
    kwargs = {"scores": scores, "risk_levels": risk_levels, "detector_policy": detector_policy}
    return (
        RRNRegexDetector(**kwargs),
        FRNRegexDetector(**kwargs),
        PhoneRegexDetector(**kwargs),
        EmailRegexDetector(**kwargs),
        NetworkIdentifierDetector(**kwargs),
        CreditCardRegexDetector(**kwargs),
        BusinessRegNoDetector(**kwargs),
        BankAccountCandidateDetector(**kwargs),
        SecretRegexDetector(**kwargs),
    )


def _resolve_config_dir(config_dir: str | Path) -> _ConfigPaths:
    root = Path(config_dir).expanduser()
    if not root.is_dir():
        package_relative = Path(__file__).resolve().parents[2] / root
        if package_relative.is_dir():
            root = package_relative
    if not root.is_dir():
        raise ValueError(f"config_dir does not exist: {config_dir}")

    paths = _ConfigPaths(
        root=root.resolve(),
        dictionaries=root / "dictionaries.yaml",
        scoring=root / "scoring.yaml",
        policy_profiles=root / "policy_profiles.yaml",
        josa_rules=root / "josa_rules.yaml",
        entities=root / "entities.yaml",
        context_rules=root / "context_rules.yaml",
        detectors=root / "detectors.yaml",
    )
    missing = [
        path.name
        for path in (
            paths.dictionaries,
            paths.scoring,
            paths.policy_profiles,
            paths.josa_rules,
            paths.entities,
            paths.context_rules,
        )
        if not path.is_file()
    ]
    if missing:
        raise ValueError(
            "config_dir is missing required config files: " + ", ".join(missing)
        )
    return paths


def default_components(
    *,
    config_dir: str | Path | None = None,
    ner_detector: BaseNERDetector | None = None,
    audit_logger: AuditLogger | None = None,
) -> PipelineComponents:
    """Build a stock set of v0.2 pipeline components.

    ``ner_detector`` defaults to ``MockNERDetector`` so the pipeline is
    self-contained without the v3 finetuned model. Pass an instance of
    ``FinetunedKoreanNERDetector`` to enable real NER at the M5 stage.
    """
    if config_dir is None:
        policy_router = PolicyRouter()
        dictionary_detector = DictionaryDetector()
        boundary_corrector = KoreanBoundaryCorrector()
        context_scorer = ContextScorer()
        span_resolver = SpanResolver()
        detector_policy = load_detector_policy()
        regex_detectors = _default_regex_detectors(detector_policy=detector_policy)
    else:
        paths = _resolve_config_dir(config_dir)
        detector_policy = load_detector_policy(paths.detectors)
        risk_levels = load_entity_risk_levels(paths.entities)
        dictionaries = load_dictionary_lists(paths.dictionaries)
        composite_upgrades = load_composite_upgrades(paths.scoring)
        policy_router = PolicyRouter(
            policy_config=load_policy_config(paths.policy_profiles),
            thresholds=load_risk_action_thresholds(paths.scoring),
        )
        dictionary_detector = DictionaryDetector(
            dictionaries=dictionaries,
            scores=load_dictionary_base_scores(paths.scoring),
            risk_levels=risk_levels,
        )
        boundary_corrector = KoreanBoundaryCorrector(config_path=paths.josa_rules)
        context_scorer = ContextScorer(
            boosts=load_context_boosts(paths.scoring),
            penalties=load_context_penalties(paths.scoring),
            field_label_terms=load_field_label_terms(paths.context_rules),
            negative_terms=load_negative_context_terms(paths.context_rules),
            honorifics=load_honorific_terms(paths.context_rules),
            bank_names=dictionaries.get("bank_names", ()),
            composite_upgrades=composite_upgrades,
        )
        span_resolver = SpanResolver(
            priority_order=tuple(
                EntityType(name) for name in load_entity_priority(paths.entities)
            ),
            composite_upgrades=composite_upgrades,
            risk_levels=risk_levels,
        )
        regex_detectors = _default_regex_detectors(
            scores=load_regex_base_scores(paths.scoring),
            risk_levels=risk_levels,
            detector_policy=detector_policy,
        )

    masker = SuffixPreservingMasker(
        policy_router=policy_router,
        hash_provider=audit_logger,
    )
    return PipelineComponents(
        regex_detectors=regex_detectors,
        dictionary_detector=dictionary_detector,
        boundary_corrector=boundary_corrector,
        context_scorer=context_scorer,
        ner_detector=ner_detector if ner_detector is not None else MockNERDetector(),
        span_resolver=span_resolver,
        policy_router=policy_router,
        masker=masker,
        audit_logger=audit_logger,
        detector_policy=detector_policy,
    )


class GuardrailPipeline:
    """Stateless single-turn Korean PII guardrail.

    Stateless = no per-request mutation of components. A single
    ``GuardrailPipeline`` instance can be shared across concurrent
    requests as long as the underlying detectors are themselves
    stateless (the v0.2 detectors are).
    """

    def __init__(self, components: PipelineComponents | None = None) -> None:
        self._components = components or default_components()

    @classmethod
    def from_config_dir(
        cls,
        config_dir: str | Path,
        *,
        ner_detector: BaseNERDetector | None = None,
        audit_logger: AuditLogger | None = None,
    ) -> "GuardrailPipeline":
        """Build a pipeline from the documented v0.2 config directory."""

        return cls(
            default_components(
                config_dir=config_dir,
                ner_detector=ner_detector,
                audit_logger=audit_logger,
            )
        )

    @property
    def components(self) -> PipelineComponents:
        return self._components

    def apply(self, request: GuardrailRequest) -> GuardrailResponse:
        """Public API alias for running the full guardrail flow."""

        return self.process(request)

    def process(self, request: GuardrailRequest) -> GuardrailResponse:
        """Run the full M1→M8 flow and return a GuardrailResponse.

        Always builds a valid response — even if the policy router
        marks the request as ``BLOCK``, the response shape stays
        consistent (``blocked=True``, ``masked_text=None``,
        ``spans`` carries the routed candidates).
        """
        t0 = time.perf_counter()
        preprocessed = preprocess_text(request.text)

        # --- Detect (M2 regex + M2.5 dictionary + M5 NER) ---
        candidates: list[PIISpan] = []
        for detector in self._components.regex_detectors:
            candidates.extend(detector.detect(preprocessed, request))
        candidates.extend(self._components.dictionary_detector.detect(preprocessed, request))
        if self._components.ner_detector is not None:
            candidates.extend(
                self._components.ner_detector.detect(
                    raw_text=request.text,
                    preprocessed=preprocessed,
                    request=request,
                )
            )
        candidates = [
            span
            for span in candidates
            if self._components.detector_policy.entity_enabled(span.entity_type)
        ]

        # --- M3 boundary correction (per-span) ---
        corrected = [
            self._components.boundary_corrector.correct(span, preprocessed)
            for span in candidates
        ]

        # --- Dedup before context scoring so identical (start,end,type)
        # spans don't double-count for is_composite peer-detection ---
        corrected = deduplicate_spans(corrected)

        # --- M4 context scoring ---
        scored = self._components.context_scorer.score(corrected, preprocessed)

        # --- M6 span resolver (duplicate merge / overlap / address / composite) ---
        resolved = self._components.span_resolver.resolve(scored, preprocessed, request)

        # --- M7 policy routing (per-span Action + method) ---
        routed = self._components.policy_router.route(resolved, request)

        # --- M7 masker (text reconstruction) ---
        # If any span resolved to BLOCK, masked_text is None.
        masked_text = self._components.masker.apply(request.text, routed, request)
        blocked = masked_text is None

        # --- M8 audit (per-span, fail-closed) ---
        audit_events = self._emit_audit_events(routed, request)

        # --- Build public response ---
        # value_hash is populated only for actionable spans (MASK/HASH/BLOCK)
        # so callers can correlate a public span with the matching audit
        # event without exposing raw text. PASS spans intentionally omit the
        # hash to keep the public payload small.
        public_spans_all = tuple(
            span.to_public(value_hash=self._public_value_hash(span))
            for span in routed
        )
        public_spans = public_spans_all if request.options.return_spans else ()
        response_audit_events = (
            audit_events if request.options.include_audit_events else ()
        )
        masked_count = sum(
            1
            for span in routed
            if span.action in {Action.MASK, Action.HASH}
        )
        latency_ms = (time.perf_counter() - t0) * 1000.0

        return GuardrailResponse(
            request_id=request.effective_request_id,
            blocked=blocked,
            masked_text=masked_text,
            spans=public_spans,
            audit_events=response_audit_events,
            metrics=ResponseMetrics(
                latency_ms=latency_ms,
                detected_span_count=len(routed),
                masked_span_count=masked_count,
            ),
            policy_profile=request.policy_profile,
            output_target=request.output_target,
            raw_value_logged=False,
        )

    def _public_value_hash(self, span: PIISpan) -> str | None:
        """Return the HMAC value_hash for actionable spans, else None.

        Actionable = the policy router decided to MASK, HASH, or BLOCK the
        span. PASS / CANDIDATE spans get ``None`` because exposing a hash
        for content that flows through unchanged offers no audit benefit
        and just enlarges the response.
        """
        if span.action not in {Action.MASK, Action.HASH, Action.BLOCK}:
            return None
        if self._components.audit_logger is not None:
            return self._components.audit_logger.digest(span.text)
        return self._components.masker.hash_provider.digest(span.text)

    def _emit_audit_events(
        self, spans: Sequence[PIISpan], request: GuardrailRequest
    ) -> tuple[AuditEvent, ...]:
        """Emit audit events for actionable spans only.

        ``Action.PASS`` and ``Action.CANDIDATE`` spans are skipped so the
        audit log stays focused on policy-driven actions. A leak in a
        single event is logged as ``AuditPayloadLeakError`` and dropped
        (fail-closed); the pipeline continues so the caller still
        receives a usable masked response.
        """
        if self._components.audit_logger is None:
            return ()
        events: list[AuditEvent] = []
        for span in spans:
            if span.action not in {Action.MASK, Action.HASH, Action.BLOCK}:
                continue
            try:
                events.append(
                    self._components.audit_logger.emit(span=span, request=request)
                )
            except AuditPayloadLeakError:
                # Fail-closed: drop this event but keep going.
                continue
        return tuple(events)


__all__ = [
    "GuardrailPipeline",
    "PipelineComponents",
    "default_components",
]
