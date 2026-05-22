from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

from pii_guardrail.detector_config import DetectorPolicy
from pii_guardrail.enums import EntityType
from pii_guardrail.pipeline import GuardrailPipeline, default_components
from pii_guardrail.schema import GuardrailRequest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = PROJECT_ROOT / "configs"
DEMO_DIR = PROJECT_ROOT / "demo"
if str(DEMO_DIR) not in sys.path:
    sys.path.insert(0, str(DEMO_DIR))

from pipeline_trace import assert_matches_pipeline, trace_pipeline  # noqa: E402


def test_trace_applies_detector_policy_entity_filter_like_pipeline() -> None:
    components = default_components(config_dir=CONFIG_DIR)
    components = replace(
        components,
        detector_policy=DetectorPolicy(
            entities_enabled={EntityType.PERSON_NAME: False}
        ),
    )
    pipeline = GuardrailPipeline(components)
    request = GuardrailRequest(
        text=(
            "\uace0\uac1d\uba85 \uae40\ubbfc\uc218 "
            "\uc5f0\ub77d\ucc98 010-1234-5678"
        )
    )

    assert_matches_pipeline(pipeline, request)
    trace = trace_pipeline(pipeline, request, reveal_raw=False)
    m2 = next(stage for stage in trace.stages if stage.module == "M2")

    assert m2.detail["detector_policy_filtered"] >= 1
    assert m2.detail["raw_candidate_count"] > m2.span_count
    assert all(span["type"] != EntityType.PERSON_NAME.value for span in m2.spans)
    assert trace.masked_text is not None
    assert "[PERSON_1]" not in trace.masked_text
    assert "[PHONE_1]" in trace.masked_text
