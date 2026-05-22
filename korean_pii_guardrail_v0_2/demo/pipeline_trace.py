"""파이프라인 해부(observability) — M1→M8 단계별 trace.

`GuardrailPipeline.process()` 는 최종 `GuardrailResponse` 만 반환하므로 각 모듈이
중간에 무엇을 했는지 보이지 않는다. 이 모듈은 `pipeline.py`(M9, Pipeline Owner
영역)를 **수정하지 않고**, 공개된 `pipeline.components` 를 그대로 재생(replay)
하면서 각 스테이지의 span 스냅샷과 "이 모듈이 무엇을·어떻게·무슨 결과로" 를 기록한다.

재생 순서는 `GuardrailPipeline.process()` 와 1:1 로 맞춘다. 어긋나면 최종 출력이
달라지므로, `assert_matches_pipeline()` 로 동일성을 검증할 수 있다(drift guard).

raw-PII 경계: 단일 로컬 분석에서는 원문을 보이되(reveal_raw=True), 저장/공개 시에는
reveal_raw=False 로 길이/placeholder/요약만 남긴다.
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from typing import Any

from pii_guardrail.enums import Action
from pii_guardrail.preprocess import preprocess_text
from pii_guardrail.regex_detectors import deduplicate_spans
from pii_guardrail.schema import GuardrailRequest, PIISpan


# ───────────────────────── 데이터 구조 ─────────────────────────
@dataclass
class StageView:
    """한 스테이지(M1, M2 …)의 스냅샷.

    spans: 이 스테이지를 마친 시점의 span 리스트(직렬화된 dict).
    summary: 개수 in→out 등 한 줄 요약.
    what_it_did: 이 모듈이 한 일(가시성의 핵심) — 사람이 읽는 bullet 리스트.
    detail: 스테이지별 부가 데이터(예: detector별 기여 수).
    """

    module: str            # "M2"
    title: str             # "탐지 (regex + 사전 + NER)"
    span_count: int
    summary: str
    what_it_did: list[str] = field(default_factory=list)
    spans: list[dict] = field(default_factory=list)
    detail: dict[str, Any] = field(default_factory=dict)


@dataclass
class PipelineTrace:
    request_id: str
    reveal_raw: bool
    raw_len: int
    normalized_text: str | None      # reveal_raw=False 면 None
    normalized_changed: bool
    variants: list[dict]
    stages: list[StageView]
    masked_text: str | None          # reveal_raw=False 면 원문 filler 없이 요약
    blocked: bool
    audit_event_count: int
    total_latency_ms: float

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "raw_len": self.raw_len,
            "normalized_changed": self.normalized_changed,
            "blocked": self.blocked,
            "audit_event_count": self.audit_event_count,
            "total_latency_ms": round(self.total_latency_ms, 2),
            "stages": [
                {
                    "module": s.module,
                    "title": s.title,
                    "span_count": s.span_count,
                    "summary": s.summary,
                    "what_it_did": s.what_it_did,
                    "spans": s.spans,
                    "detail": s.detail,
                }
                for s in self.stages
            ],
        }


# ───────────────────────── span 직렬화 ─────────────────────────
def _span_dict(span: PIISpan, reveal_raw: bool) -> dict[str, Any]:
    return {
        "type": span.entity_type.value,
        "value": span.text if reveal_raw else f"🔒 {span.end - span.start}자",
        "start": span.start,
        "end": span.end,
        "score": round(span.score, 3),
        "risk": span.risk_level.value,
        "action": span.action.value,
        "suffix": span.suffix or "",
        "is_composite": span.is_composite,
        "sources": list(span.sources),
        "detector_ids": list(span.detector_ids),
        "reason_codes": list(span.reason_codes),
    }


def _detect_one(detector, preprocessed, request) -> list[PIISpan]:
    """regex/dict 검출기 호출 (공통 시그니처)."""
    return list(detector.detect(preprocessed, request))


def _detector_label(detector) -> str:
    return (
        getattr(detector, "detector_id", None)
        or getattr(detector, "source", None)
        or type(detector).__name__
    )


# preprocess 가 만드는 변이형(표기 변이 복원형) 한글 설명 — 검출기는 이 변이형들도 함께 스캔한다.
_VARIANT_GLOSS = {
    "normalized": "기본 정규화 (NFKC · 대시/전각숫자 통일 · zero-width 제거)",
    "digit_compact": "숫자 사이 구분자(-, 공백 등) 제거",
    "digit_space_compact": "숫자 사이 공백 제거",
    "korean_keyword_spacing_compact": "띄어쓴 한글 키워드 붙이기 (주 민 번 호 → 주민번호)",
    "jamo_composed": "분해된 자모 결합 (ㅈㅜㅁㅣㄴ → 주민)",
    "choseong_restored": "초성 축약 복원 (ㅈㅁㅂㅎ → 주민번호)",
    "yamin_restored": "야민정음 복원 (댸 → 대 등)",
    "romanized_restored": "로마자 표기 복원 (jumin → 주민)",
    "korean_digit_restored": "한글 숫자 → 아라비아 숫자 (구공공 → 900)",
}


_SAFE_PLACEHOLDER_RE = re.compile(r"\[(?:[A-Z][A-Z0-9]*_\d+|REDACTED)\]")


def _safe_masked_view(masked_text: str | None, *, reveal_raw: bool) -> str:
    """Render final output without echoing raw filler in public/share mode."""
    if masked_text is None:
        return "🚫 BLOCKED (고위험 다수)"
    if reveal_raw:
        return masked_text
    placeholders = _SAFE_PLACEHOLDER_RE.findall(masked_text)
    if placeholders:
        return (
            f"🔒 출력 {len(masked_text)}자 (원문 숨김) · "
            f"placeholder: {' '.join(placeholders)}"
        )
    return f"🔒 출력 {len(masked_text)}자 (원문 숨김 · 탐지 placeholder 없음)"


def _val(span: PIISpan, reveal_raw: bool) -> str:
    """span 원문값 (share 모드면 길이만)."""
    return f"「{span.text}」" if reveal_raw else f"「🔒{span.end - span.start}자」"


def _reasons(span: PIISpan, prefix: str) -> str:
    """span.reason_codes 중 특정 prefix 만 사람이 읽게 묶음 (왜 그랬는지)."""
    rs = [rc for rc in span.reason_codes if rc.startswith(prefix)]
    return ", ".join(rs)


# ───────────────────────── 핵심: trace ─────────────────────────
def trace_pipeline(pipe, request: GuardrailRequest, *, reveal_raw: bool = True) -> PipelineTrace:
    """`pipe.components` 를 재생하며 단계별 스냅샷을 만든다.

    재생 순서는 `GuardrailPipeline.process()` 와 동일하다.
    """
    c = pipe.components
    t0 = time.perf_counter()
    stages: list[StageView] = []

    # ── M1 정규화 ──────────────────────────────────────────────
    pre = preprocess_text(request.text)
    norm_changed = pre.normalized_text != pre.raw_text
    # 변이형은 normalized 위에 추가 변환을 적용한 것. normalized 와 다르면 "뭔가 복원함".
    changed_vars = [v for v in pre.variants
                    if v.name != "normalized" and v.text != pre.normalized_text]

    did1: list[str] = []
    # (1) 기본 정규화 before → after
    if norm_changed:
        if reveal_raw:
            did1.append(f"원문:   「{pre.raw_text}」")
            did1.append(f"정규화: 「{pre.normalized_text}」  ← NFKC · 대시/전각숫자 통일 · zero-width 제거")
        else:
            did1.append(f"기본 정규화로 원문 변경됨 (원문 숨김, {len(pre.normalized_text)}자)")
    else:
        did1.append("기본 정규화: 변화 없음 (NFKC · zero-width 등 해당 사항 없음)")
    # (2) 표기 변이 복원형 — 실제로 무엇을 만들었는지
    if changed_vars:
        did1.append(f"표기 변이 복원형 {len(changed_vars)}개 생성 — 검출기가 이 형태들도 함께 스캔:")
        for v in changed_vars:
            gloss = _VARIANT_GLOSS.get(v.name, v.name)
            if reveal_raw:
                did1.append(f"   ↳ {gloss}  →  「{v.text}」")
            else:
                did1.append(f"   ↳ {gloss} (적용됨)")
    else:
        did1.append("표기 변이 없음 (자모분해 · 띄어쓰기 · 로마자 · 초성 등 미감지)")
    # (3) 구조 분해
    did1.append(f"문장 {len(pre.sentences)}개 · 어절 {len(pre.eojeols)}개로 분해")

    var_summary = (f"변이 복원형 {len(changed_vars)}개" if changed_vars else "변이 없음")
    stages.append(StageView(
        module="M1",
        title="정규화 (preprocess)",
        span_count=0,
        summary=f"원문 {len(pre.raw_text)}자 → 정규화 {'변경됨' if norm_changed else '변화 없음'} · {var_summary}",
        what_it_did=did1,
        detail={
            "normalized_changed": norm_changed,
            "variants": [
                {"name": v.name, "changed": v.text != pre.normalized_text}
                for v in pre.variants if v.name != "normalized"
            ],
        },
    ))

    # ── M2 탐지 (regex + 사전 + NER) — detector별 기여 분해 ──────
    candidates: list[PIISpan] = []
    contrib: list[dict] = []
    for det in c.regex_detectors:
        got = _detect_one(det, pre, request)
        candidates.extend(got)
        if got:
            contrib.append({"detector": _detector_label(det), "kind": "regex", "count": len(got),
                            "types": sorted({s.entity_type.value for s in got})})
    dict_got = _detect_one(c.dictionary_detector, pre, request)
    candidates.extend(dict_got)
    if dict_got:
        contrib.append({"detector": _detector_label(c.dictionary_detector), "kind": "dict",
                        "count": len(dict_got), "types": sorted({s.entity_type.value for s in dict_got})})
    ner_got: list[PIISpan] = []
    if c.ner_detector is not None:
        ner_got = list(c.ner_detector.detect(raw_text=request.text, preprocessed=pre, request=request))
        candidates.extend(ner_got)
        if ner_got:
            contrib.append({"detector": _detector_label(c.ner_detector), "kind": "ner",
                            "count": len(ner_got), "types": sorted({s.entity_type.value for s in ner_got})})
    did = [f"검출기 {len(contrib)}종 가동 → " + " · ".join(
        f"{ct['detector'].split('.')[-1]}({ct['kind']}) {ct['count']}" for ct in contrib)] if contrib else []
    # 후보별 "어느 검출기가 무슨 값을 어떤 신뢰도로 잡았나"
    for s in sorted(candidates, key=lambda x: x.start):
        det = (s.detector_ids[0] if s.detector_ids else (s.sources[0] if s.sources else "?"))
        did.append(f"   ↳ {det}: {s.entity_type.value} {_val(s, reveal_raw)} (score {s.score:.2f})")
    if not did:
        did = ["어떤 검출기도 후보를 내지 않음 (탐지 0)"]
    stages.append(StageView(
        module="M2", title="탐지 (정규식 + 사전 + NER)",
        span_count=len(candidates),
        summary=f"검출기 {len(contrib)}종이 후보 {len(candidates)}건 생성",
        what_it_did=did,
        spans=[_span_dict(s, reveal_raw) for s in candidates],
        detail={"contributions": contrib, "regex": sum(1 for x in contrib if x['kind']=='regex'),
                "dict": len(dict_got), "ner": len(ner_got)},
    ))

    # ── M3 경계 보정 (조사/호칭/어미 분리) ──────────────────────
    corrected = [c.boundary_corrector.correct(s, pre) for s in candidates]
    # before(candidates) → after(corrected) 는 index 1:1 대응 (correct 는 per-span)
    did3 = []
    for before, after in zip(candidates, corrected):
        if after.suffix or before.text != after.text:
            did3.append(
                f"{after.entity_type.value}: {_val(before, reveal_raw)} → "
                f"{_val(after, reveal_raw)}  (조사/호칭/어미 '{after.suffix}' 분리)"
            )
    trimmed_n = len(did3)
    if not did3:
        did3 = ["분리할 조사/호칭/어미 없음 (span 경계 그대로)"]
    stages.append(StageView(
        module="M3", title="경계 보정 (boundary corrector)",
        span_count=len(corrected),
        summary=f"{trimmed_n}건에서 조사/호칭/어미 분리",
        what_it_did=did3,
        spans=[_span_dict(s, reveal_raw) for s in corrected],
        detail={"trimmed_count": trimmed_n},
    ))

    # ── dedup (동일 start/end/type 중복 제거) ───────────────────
    pre_dedup = corrected
    before_dedup = len(pre_dedup)
    # 중복 그룹: 같은 (start,end,type) 을 낸 검출기들
    groups: dict[tuple, list[PIISpan]] = {}
    for s in pre_dedup:
        groups.setdefault((s.start, s.end, s.entity_type.value), []).append(s)
    corrected = deduplicate_spans(corrected)
    removed = before_dedup - len(corrected)
    did_d = []
    for (st, en, typ), grp in groups.items():
        if len(grp) > 1:
            dets = " + ".join(sorted({(g.detector_ids[0] if g.detector_ids else
                              (g.sources[0] if g.sources else "?")) for g in grp}))
            did_d.append(f"{typ} {_val(grp[0], reveal_raw)}: {dets} → 1개로 통합 ({len(grp)}건 중복)")
    if not did_d:
        did_d = ["중복 없음 (검출기 간 동일 span 없음)"]
    stages.append(StageView(
        module="dedup", title="중복 제거 (deduplicate)",
        span_count=len(corrected),
        summary=f"동일 (start,end,type) 중복 {removed}건 제거",
        what_it_did=did_d,
        spans=[_span_dict(s, reveal_raw) for s in corrected],
        detail={"removed": removed},
    ))

    # ── M4 문맥 점수 (boost/penalty + composite) ────────────────
    scored = c.context_scorer.score(corrected, pre)
    by_key = {(s.start, s.end, s.entity_type.value): s for s in corrected}
    did4 = []
    n_delta = 0
    for s in scored:
        prev = by_key.get((s.start, s.end, s.entity_type.value))
        if prev is not None and abs(s.score - prev.score) > 1e-9:
            n_delta += 1
            why = _reasons(s, "context.") or "문맥 규칙"
            arrow = "▲" if s.score >= prev.score else "▼"
            did4.append(
                f"{arrow} {s.entity_type.value} {_val(s, reveal_raw)}: "
                f"{prev.score:.2f} → {s.score:.2f}  (왜: {why})"
            )
    composites = [s for s in scored if s.is_composite]
    if composites:
        did4.append(f"composite 후보 표시 ({len(composites)}건): "
                    + ", ".join(sorted({s.entity_type.value for s in composites}))
                    + " — 함께 등장해 위험도 상향 후보")
    if not did4:
        did4 = ["점수 변화 없음 (문맥 boost/penalty 미적용)"]
    stages.append(StageView(
        module="M4", title="문맥 점수 (context scorer)",
        span_count=len(scored),
        summary=f"{n_delta}건 점수 조정 · composite {len(set(s.entity_type.value for s in composites))}종",
        what_it_did=did4,
        spans=[_span_dict(s, reveal_raw) for s in scored],
        detail={"score_changes": n_delta,
                "composite_types": sorted({s.entity_type.value for s in composites})},
    ))

    # ── M6 span 해소 (병합/overlap/주소조각/composite 승급) ──────
    before_resolve = len(scored)
    risk_before = {(s.start, s.end, s.entity_type.value): s.risk_level.value for s in scored}
    resolved = c.span_resolver.resolve(scored, pre, request)
    delta_n = before_resolve - len(resolved)
    did6 = []
    if delta_n > 0:
        did6.append(f"중복/overlap 정리로 {delta_n}건 감소 (우선순위 승자 선택·병합)")
    elif delta_n < 0:
        did6.append(f"주소 조각 분할 등으로 {-delta_n}건 증가")
    else:
        did6.append("span 수 변화 없음 (병합/분할 없음)")
    # 위험도 승급 (composite 등) per span
    upgrades = []
    for s in resolved:
        prev_risk = risk_before.get((s.start, s.end, s.entity_type.value))
        if prev_risk and prev_risk != s.risk_level.value:
            why = _reasons(s, "resolver.") or _reasons(s, "composite") or "composite 상향"
            did6.append(f"▲ {s.entity_type.value} {_val(s, reveal_raw)}: "
                        f"위험도 {prev_risk} → {s.risk_level.value}  (왜: {why})")
            upgrades.append(s.entity_type.value)
    stages.append(StageView(
        module="M6", title="span 해소 (resolver)",
        span_count=len(resolved),
        summary=f"{before_resolve}건 → {len(resolved)}건 · 위험도 승급 {len(upgrades)}건",
        what_it_did=did6,
        spans=[_span_dict(s, reveal_raw) for s in resolved],
        detail={"delta": delta_n, "upgrades": sorted(set(upgrades))},
    ))

    # ── M7 정책 라우팅 (Action + method) ────────────────────────
    routed = c.policy_router.route(resolved, request)
    from collections import Counter
    action_dist = Counter(s.action.value for s in routed)
    did7 = []
    for s in routed:
        why = _reasons(s, "policy.") or "기본 정책"
        did7.append(f"{s.entity_type.value} {_val(s, reveal_raw)} → "
                    f"{s.action.value.upper()} ({s.risk_level.value}, 왜: {why})")
    if not did7:
        did7 = ["라우팅할 span 없음"]
    stages.append(StageView(
        module="M7", title="정책 라우팅 (policy router)",
        span_count=len(routed),
        summary=f"조치 분포: {dict(action_dist)}",
        what_it_did=did7,
        spans=[_span_dict(s, reveal_raw) for s in routed],
        detail={"action_distribution": dict(action_dist)},
    ))

    # ── M7 마스킹 (텍스트 재구성) ───────────────────────────────
    masked_text = c.masker.apply(request.text, routed, request)
    blocked = masked_text is None
    masked_view = _safe_masked_view(masked_text, reveal_raw=reveal_raw)
    stages.append(StageView(
        module="M7", title="마스킹 (masker)",
        span_count=len(routed),
        summary="BLOCK (마스킹 텍스트 없음)" if blocked else "placeholder 치환 완료",
        what_it_did=[f"결과: {masked_view}"],
        detail={"blocked": blocked},
    ))

    # ── M8 감사 대상 산정 (trace는 파일 쓰기 부작용 없이 대상만 계산) ─────────────
    actionable_spans = [s for s in routed if s.action in {Action.MASK, Action.HASH, Action.BLOCK}]
    audit_n = len(actionable_spans) if c.audit_logger is not None else 0
    if c.audit_logger is not None:
        did8 = ["감사 로그에는 원문이 아니라 hash+offset+type 만 기록 (raw-PII 경계):"]
        for s in actionable_spans:
            # value_hash 는 원문이 아닌 HMAC — 노출돼도 안전. share/local 무관.
            try:
                h = c.audit_logger.digest(s.text)
            except Exception:
                h = "hmac-sha256:…"
            short = h if len(h) <= 40 else h[:40] + "…"
            did8.append(f"   ↳ {s.entity_type.value} [{s.start}:{s.end}] len{s.end - s.start} "
                        f"{s.action.value} → {short}")
        did8.append("trace 뷰는 관측용이라 실제 audit log 파일 쓰기는 하지 않음")
    else:
        did8 = ["감사 로거가 주입되지 않음 — 이벤트 없음 (기본 데모는 로거 비활성)"]
    stages.append(StageView(
        module="M8", title="감사 대상 산정 (audit logger)",
        span_count=audit_n,
        summary=(f"actionable {len(actionable_spans)}건 → 감사 이벤트 대상 (hash only)"
                 if c.audit_logger is not None else "감사 로거 비활성 (이벤트 0)"),
        what_it_did=did8,
        detail={"audit_event_targets": audit_n, "actionable": len(actionable_spans), "emitted": False},
    ))

    total_ms = (time.perf_counter() - t0) * 1000.0
    return PipelineTrace(
        request_id=request.effective_request_id,
        reveal_raw=reveal_raw,
        raw_len=len(request.text),
        normalized_text=(pre.normalized_text if reveal_raw else None),
        normalized_changed=norm_changed,
        variants=[{"name": v.name, "changed": v.text != pre.normalized_text}
                  for v in pre.variants if v.name != "normalized"],
        stages=stages,
        masked_text=masked_view,
        blocked=blocked,
        audit_event_count=audit_n,
        total_latency_ms=total_ms,
    )


@dataclass
class BatchTraceResult:
    n: int
    aggregate: dict[str, Any]
    records: list[dict]      # 레코드별 요약 (drill-down 표용)


def _percentile(values: list[float], q: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    idx = min(len(s) - 1, int(round(q * (len(s) - 1))))
    return s[idx]


def batch_trace(pipe, texts: list[str], *, reveal_raw: bool = False) -> BatchTraceResult:
    """N개 입력을 단계별로 흘려보내며 집계 + 레코드별 요약을 만든다.

    각 레코드 full trace 는 보관하지 않고(메모리 bound), drill-down 시
    `trace_pipeline(pipe, request)` 로 재계산한다. 따라서 10k 도 처리 가능.
    """
    from collections import Counter

    n = len(texts)
    records: list[dict] = []
    detector_contrib: Counter = Counter()   # detector_id → 기여 span 수
    action_dist: Counter = Counter()
    entity_dist: Counter = Counter()
    stage_counts: dict[str, list[int]] = {}
    latencies: list[float] = []
    n_normalized_changed = 0
    n_blocked = 0
    n_zero_detection = 0

    for i, txt in enumerate(texts):
        txt = (txt or "").strip()
        if not txt:
            continue
        tr = trace_pipeline(pipe, GuardrailRequest(text=txt), reveal_raw=reveal_raw)
        latencies.append(tr.total_latency_ms)
        if tr.normalized_changed:
            n_normalized_changed += 1
        if tr.blocked:
            n_blocked += 1

        # 스테이지별 span 수
        for st in tr.stages:
            stage_counts.setdefault(st.module, []).append(st.span_count)

        # M2 detector별 기여
        m2 = next((s for s in tr.stages if s.module == "M2"), None)
        if m2:
            for ct in m2.detail.get("contributions", []):
                detector_contrib[ct["detector"]] += ct["count"]

        # 최종(M7 정책) 기준 action/entity 분포
        m7 = next((s for s in tr.stages if s.module == "M7" and "정책" in s.title), None)
        final_spans = m7.spans if m7 else []
        for sp in final_spans:
            action_dist[sp["action"]] += 1
            entity_dist[sp["type"]] += 1
        if not final_spans:
            n_zero_detection += 1

        records.append({
            "idx": i,
            "len": len(txt),
            "norm_changed": tr.normalized_changed,
            "candidates": (m2.span_count if m2 else 0),
            "final": len(final_spans),
            "blocked": tr.blocked,
            "types": sorted({sp["type"] for sp in final_spans}),
            "latency_ms": round(tr.total_latency_ms, 2),
        })

    valid = len(records)
    detected = valid - n_zero_detection
    aggregate = {
        "n": valid,
        "detection_rate": (detected / valid) if valid else 0.0,
        "zero_detection": n_zero_detection,
        "block_rate": (n_blocked / valid) if valid else 0.0,
        "normalized_changed": n_normalized_changed,
        "detector_contrib": dict(detector_contrib.most_common()),
        "action_dist": dict(action_dist.most_common()),
        "entity_dist": dict(entity_dist.most_common()),
        "stage_avg": {k: (sum(v) / len(v) if v else 0) for k, v in stage_counts.items()},
        "latency_p50": _percentile(latencies, 0.5),
        "latency_p95": _percentile(latencies, 0.95),
        "latency_mean": (sum(latencies) / len(latencies)) if latencies else 0.0,
    }
    return BatchTraceResult(n=valid, aggregate=aggregate, records=records)


_MODULE_COLOR = {
    "M1": "#4263eb", "M2": "#0ca678", "M3": "#7048e8", "dedup": "#868e96",
    "M4": "#f59f00", "M6": "#e8590c", "M7": "#e64980", "M8": "#1098ad",
}


def _esc(s: str) -> str:
    return (str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;"))


def render_trace_html(trace: PipelineTrace) -> str:
    """PipelineTrace → 단계별 타임라인 HTML (최대 가시성)."""
    head = (
        f'<div style="font-size:13px;opacity:.8;margin-bottom:8px">'
        f'원문 {trace.raw_len}자 · 정규화 {"변경됨 ✨" if trace.normalized_changed else "변화 없음"} · '
        f'{"🚫 BLOCKED" if trace.blocked else "🟢 통과/마스킹"} · ⏱ {trace.total_latency_ms:.1f}ms</div>'
        f'<div style="background:#1118;border-radius:8px;padding:10px 12px;margin-bottom:14px;'
        f'font-family:monospace;font-size:14px">최종 출력 → {_esc(trace.masked_text)}</div>'
    )
    blocks = [head]
    for st in trace.stages:
        color = _MODULE_COLOR.get(st.module, "#868e96")
        bullets = "".join(f"<li>{_esc(b)}</li>" for b in st.what_it_did)
        # span 미니 테이블 (있을 때만)
        table = ""
        if st.spans:
            rows = "".join(
                f"<tr><td>{_esc(sp['type'])}</td><td style='font-family:monospace'>{_esc(sp['value'])}</td>"
                f"<td>{sp['score']}</td><td>{_esc(sp['risk'])}</td><td>{_esc(sp['action'])}</td>"
                f"<td style='font-size:11px;opacity:.7'>{_esc(', '.join(sp['detector_ids']) or '-')}</td></tr>"
                for sp in st.spans
            )
            table = (
                "<table style='width:100%;border-collapse:collapse;margin-top:8px;font-size:12px'>"
                "<tr style='opacity:.6;text-align:left'><th>type</th><th>value</th><th>score</th>"
                "<th>risk</th><th>action</th><th>detector</th></tr>" + rows + "</table>"
            )
        blocks.append(
            f'<div style="border-left:4px solid {color};background:{color}10;'
            f'border-radius:0 10px 10px 0;padding:12px 16px;margin:10px 0">'
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:4px">'
            f'<span style="background:{color};color:#fff;font-weight:800;border-radius:6px;'
            f'padding:2px 9px;font-size:13px">{st.module}</span>'
            f'<span style="font-weight:700;font-size:15px">{_esc(st.title)}</span>'
            f'<span style="margin-left:auto;font-size:12px;opacity:.65">span {st.span_count}</span></div>'
            f'<div style="font-size:13px;opacity:.85;margin-bottom:4px">{_esc(st.summary)}</div>'
            f'<ul style="margin:4px 0 0;padding-left:18px;font-size:13px">{bullets}</ul>'
            f'{table}</div>'
        )
    return "<div>" + "".join(blocks) + "</div>"


def _bar(label: str, value: float, maxv: float, color: str, suffix: str = "") -> str:
    pct = (value / maxv * 100) if maxv else 0
    return (
        f'<div style="display:flex;align-items:center;gap:8px;margin:3px 0;font-size:12px">'
        f'<span style="width:160px;text-align:right;opacity:.8">{_esc(label)}</span>'
        f'<div style="flex:1;background:#8881;border-radius:4px;height:16px">'
        f'<div style="width:{pct:.0f}%;background:{color};height:16px;border-radius:4px"></div></div>'
        f'<span style="width:70px">{value:.0f}{suffix}</span></div>'
    )


def render_batch_html(result: BatchTraceResult) -> str:
    a = result.aggregate
    n = a["n"]
    cards = [
        (f"{n:,}", "분석 건수", "#4263eb"),
        (f"{a['detection_rate']*100:.1f}%", f"탐지율 (≥1 PII) · 미탐 {a['zero_detection']}", "#37b24d"),
        (f"{a['block_rate']*100:.1f}%", "차단율 (BLOCK)", "#e64980"),
        (f"{a['latency_p50']:.1f}ms", f"latency p50 (p95 {a['latency_p95']:.0f})", "#f59f00"),
    ]
    card_html = '<div style="display:flex;gap:12px;flex-wrap:wrap;margin:8px 0 16px">'
    for big, sub, color in cards:
        card_html += (
            f'<div style="flex:1;min-width:150px;background:{color}1a;border:1px solid {color}55;'
            f'border-radius:12px;padding:14px;text-align:center">'
            f'<div style="font-size:26px;font-weight:800;color:{color}">{big}</div>'
            f'<div style="font-size:12px;opacity:.75;margin-top:4px">{_esc(sub)}</div></div>'
        )
    card_html += "</div>"

    # detector별 기여
    dc = a["detector_contrib"]
    maxd = max(dc.values()) if dc else 1
    det_bars = "".join(_bar(k, v, maxd, "#0ca678", "건") for k, v in dc.items()) \
        or "<div style='opacity:.6'>기여 검출기 없음</div>"

    # 단계별 평균 span 수 (어디서 늘고 주는지)
    order = ["M2", "M3", "dedup", "M4", "M6", "M7"]
    sa = a["stage_avg"]
    maxs = max((sa.get(k, 0) for k in order), default=1) or 1
    stage_bars = "".join(_bar(k, sa.get(k, 0), maxs, "#7048e8", "") for k in order if k in sa)

    # entity / action 분포
    ed = a["entity_dist"]; maxe = max(ed.values()) if ed else 1
    ent_bars = "".join(_bar(k, v, maxe, "#e8590c", "") for k, v in list(ed.items())[:12]) \
        or "<div style='opacity:.6'>탐지된 entity 없음</div>"
    act = a["action_dist"]
    act_html = " · ".join(f"<b>{_esc(k)}</b> {v}" for k, v in act.items()) or "—"

    def sect(title, body):
        return (f'<div style="margin:14px 0"><div style="font-weight:700;font-size:14px;'
                f'margin-bottom:6px">{title}</div>{body}</div>')

    body = (
        card_html
        + sect("🔎 검출기별 기여 (M2 후보 수)", det_bars)
        + sect("📉 단계별 평균 span 수 (어디서 늘고/주는지)", stage_bars)
        + sect("🏷 최종 entity 분포 (상위 12)", ent_bars)
        + sect("⚙️ 조치 분포", f'<div style="font-size:13px">{act_html}</div>')
        + f'<div style="font-size:12px;opacity:.7;margin-top:8px">표기 변이 감지(정규화 변경): '
          f'{a["normalized_changed"]}건 · 0건 탐지(잠재 미탐): {a["zero_detection"]}건</div>'
    )
    return "<div>" + body + "</div>"


def load_texts(path: str, limit: int | None = None) -> list[str]:
    """파일에서 입력 텍스트 로드. .json(list[str] 또는 list[{text:..}]) / .txt(줄 단위)."""
    import json
    from pathlib import Path as _P

    p = _P(path).expanduser()
    raw = p.read_text(encoding="utf-8")
    texts: list[str] = []
    if p.suffix.lower() == ".json":
        data = json.loads(raw)
        for item in data:
            if isinstance(item, str):
                texts.append(item)
            elif isinstance(item, dict):
                v = item.get("text") or item.get("payload") or item.get("input")
                if v:
                    texts.append(str(v))
    else:
        texts = [ln for ln in raw.splitlines() if ln.strip()]
    if limit:
        texts = texts[:limit]
    return texts


def assert_matches_pipeline(pipe, request: GuardrailRequest) -> None:
    """drift guard: trace 재생 결과가 pipeline.process() 와 동일한지 검증.

    재생 순서가 어긋나면 최종 masked_text / blocked / 탐지 수가 달라진다.
    """
    tr = trace_pipeline(pipe, request, reveal_raw=True)
    resp = pipe.process(request)
    policy_stage = next(s for s in tr.stages if s.module == "M7" and "정책" in s.title)
    final_routed = policy_stage.span_count
    assert tr.blocked == resp.blocked, ("blocked mismatch", tr.blocked, resp.blocked)
    expected_masked = None if resp.blocked else resp.masked_text
    got_masked = None if tr.blocked else tr.masked_text
    assert got_masked == expected_masked, ("masked_text mismatch", got_masked, expected_masked)
    assert final_routed == resp.metrics.detected_span_count, (
        "span count mismatch", final_routed, resp.metrics.detected_span_count)
