# -*- coding: utf-8 -*-
"""자동 적대검증 루프 (Auto-Verify Loop) — NER 어댑테이션.

2026-05-28 도입. finance/scripts/auto_verify_loop.py (5/24, NER Owner = 김민우)
를 PII NER 프로젝트로 이식. State machine 그대로, 프롬프트만 NER 특화.

state machine: init → attack rounds → (PASS) → final (N병렬, N/N PASS 요구).
가드: 사이코판트(raw 강제+PASS_CONFIRMATION 검증) / 작성자불신(프롬프트) /
     골대이동(같은 verification_request 재사용) / 수렴가짜(N/N + focus 다양화) /
     무한루프(MAX_ATTACK_ITER + 동일이슈/진전없음 2신호) / 위조감사(raw 필수) /
     진행강제(REVISE 후 --fixes 필수) / 자기참조 함정(메타 자아성찰 시 line cite ≥3).

스크립트는 LLM 호출 안 함. 외부 Claude 가 Agent 도구로 띄우고 record 로 기록.

NER 특화 변경:
  - ATTACK_PROMPT 5번: NER CLAUDE.md 하드원 교훈 참조 (v2 실패)
  - ATTACK_PROMPT meta_mode_hint: ARTIFACT = 본 스크립트 자체일 때 분기
  - FOCUS_ANGLES 3개: stat / data / ops (NER 카테고리)
  - PASS_CONFIRMATION focus 키워드 그룹: NER 어휘 + 단어 경계 매치 (R1-i04)
  - cmd_record raw 가드 8: 메타 자아성찰 시 line cite ≥3 (R1-i01)
  - _decide_termination + cmd_record: final 부분 PASS 시 attack_rounds_used 증가 (R1-i09)
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

ROOT = Path(__file__).resolve().parent.parent

# finance _win_encoding 의존 제거 (NER 프로젝트는 별도)
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass


MAX_ATTACK_ITER = 5
FINAL_AGENTS = 3
CONVERGENCE_REPEAT = 2
NO_PROGRESS_WINDOW = 3
PASS_CONFIRM_HEADER = "PASS_CONFIRMATION:"
ISSUES_JSON_HEADER = "ISSUES_JSON:"
SCRAP_REASON_HEADER = "SCRAP_REASON:"
MAX_ITER = MAX_ATTACK_ITER


META_HINT_NORMAL = "ARTIFACT 가 NER 데이터/모델/평가 산출물이면 위 dedup/leakage/F1 검증 적용."
META_HINT_SELF = (
    "ARTIFACT 가 auto_verify_loop.py 자체 (메타 자아성찰) → 위 NER 데이터 검증 항목 무시. "
    "대신 (a) state machine 엣지 케이스 (b) 가드 7개 무력화 시나리오 (c) finance 원본과 본질 diff "
    "(d) 자기참조 함정 (가드가 자기 자신 검증 시 trivially 통과) 를 dry-run 하라."
)
META_EXTRA_RULE_SELF = (
    "\n메타 자아성찰 추가 룰: raw 본문에 ARTIFACT line 번호 cite 최소 3 개 필수 "
    "(예: 'auto_verify_loop.py:412'). 자기참조 함정 차단 가드 추가됨."
)

ATTACK_PROMPT = """당신은 깨끗한 컨텍스트의 적대적 검증자입니다 (PII NER 자아성찰 트랙).

ARTIFACT: {artifact}
VERIFICATION REQUEST: {request}

원칙:
1. 작성자 요약 믿지 마라. 디스크에서 파일/평가 raw JSON 직접 읽어라.
2. ARTIFACT 전체 끝까지 읽어라.
3. PASS 남발 = 실패. SCRAP/REVISE 환영.
4. 반례 하나라도 만들 수 있으면 REVISE.
5. C:/My-AI-Security-Project/PII/ner/CLAUDE.md 하드원 교훈과 모순되는 곳 우선
   (v2 실패: Naver 81%/어절→char 노이즈/다중 변수 동시 변경 = KLUE -10%p).
6. 가능하면 코드 실행/dry-run — Python 으로 dedup 실제 카운트, train ∩ eval leakage 실측, F1 산식 검증.
   ※ {meta_mode_hint}

이전 라운드 (참고하되 무비판적 추종 금지):
{prior_rounds}

응답 마지막에:
VERDICT: PASS | REVISE | SCRAP
- REVISE: 다음 줄 헤더 ISSUES_JSON: + JSON array. 각 항목 = {{"id":"r{round_num}-i01","severity":"high|med|low","category":"stat|data|ops","description":"...","file_refs":["path:line"]}}
- SCRAP: 헤더 SCRAP_REASON: + 근본 결함
- PASS: 헤더 PASS_CONFIRMATION: + (a) 읽은 파일 (b) 체크리스트 처리 결과 (c) minor 무시 사항
{meta_mode_extra_rule}
"""

FINAL_PROMPT = """당신은 {n}명의 독립 검증자 중 한 명 (PII NER 자아성찰 final 라운드). 나머지 {other_n}명도 같은 산출물을 *지금* 별도로 검토 중.

PASS 가 되려면 {n}/{n} 전원 동의. 당신 역할 = PASS *못* 시킬 이유 찾기.

당신의 특정 공격 각도: **{focus}**

ARTIFACT: {artifact}
VERIFICATION REQUEST: {request}

ATTACK 모든 원칙 적용. final 추가 원칙:
- PASS 보낼 경우 PASS_CONFIRMATION 에 *자기 focus 밖* 카테고리도 최소 1개 다뤘다 명시.
  자기 focus 만 다루면 가짜 PASS 로 거부됨.

이전 라운드:
{prior_rounds}

응답 마지막: VERDICT + ISSUES_JSON / SCRAP_REASON / PASS_CONFIRMATION.
"""

# NER 특화 focus 각도 3개
FOCUS_ANGLES = [
    "통계·평가 건전성 (data leakage train∩eval, KLUE val early-stop + 같은 set 보고 누설, "
    "macro vs micro vs span-exact 산식, per-entity F1 평균 가중치, 재현성 — seed/batch shuffle/dropout/fp16)",
    "데이터 정확성 (char-level 변환 오류, dedup 룰 exact/near-dup/hash, "
    "라벨 매핑 PS→NAME/LC→ADDRESS/OG→ORG 정합, 합성 비중 v2 Naver 81% 함정, BIO 무효 시퀀스)",
    "ML 운영 리스크 (v2 실패 재발 — 데이터+setup 한 PR 동시 변경, plateau 트랩 — internal 멈춤이 외부 약점 가림, "
    "외부 transfer 환상 — KLUE val로 fit한 걸 외부라 부름, HF 모델 swap/rollback, 사이드카 호환성)",
]


# PASS_CONFIRMATION 키워드 그룹 — 단어 경계 매치 (R1-i04 fix: 짧은 키워드 거짓 양성 차단)
FOCUS_KEYWORD_GROUPS = {
    "stat": [
        r"\bleakage\b", r"누설", r"\bmacro[-_ ]?f1\b", r"\bmicro[-_ ]?f1\b",
        r"\bspan[-_ ]?exact\b", r"\bper[-_ ]?entity\b",
        r"\bf1[\s\-_]score\b", r"재현성", r"\bseed\s+(고정|fix|set)",
        r"\breproducibility\b", r"entity[-_ ]level", r"token[-_ ]level",
    ],
    "data": [
        r"\bdedup", r"중복\s*(검사|제거|확인)", r"\bchar[-_ ]?level\b",
        r"어절", r"\bbio\s+(라벨|태그|sequence|시퀀스)",
        r"라벨\s*(매핑|일관|품질)", r"\bconjunctive\b",
        r"합성\s*(데이터|비중|비율)", r"\bsynthetic\b",
    ],
    "ops": [
        r"v2\s*(실패|재발|trap|함정)", r"변수\s*(격리|동시|한.번에)",
        r"\bplateau\b", r"외부\s*transfer", r"\bhf\s*(hub|모델|배포)",
        r"사이드카", r"\bsidecar\b", r"모델\s*(swap|교체|배포|롤백|롤아웃)",
        r"\brollback\b", r"롤백",
    ],
}


@dataclass
class Round:
    iteration: int
    stage: str
    timestamp: str
    verdicts: list
    issues: list = field(default_factory=list)
    fixes_applied: str = ""
    raw_response_paths: list = field(default_factory=list)
    pass_confirmations: list = field(default_factory=list)


@dataclass
class State:
    artifact: str
    request: str
    log_path: str
    max_iter: int = MAX_ATTACK_ITER
    final_agents: int = FINAL_AGENTS
    current_iter: int = 1
    next_stage: str = "attack"
    terminated: Optional[str] = None
    rounds: list = field(default_factory=list)
    attack_rounds_used: int = 0

    def to_json(self) -> dict:
        return asdict(self)

    @classmethod
    def from_json(cls, d: dict) -> "State":
        rounds_data = d.pop("rounds", [])
        s = cls(**d)
        s.rounds = [Round(**r) for r in rounds_data]
        return s


def state_path(log_path: Path) -> Path:
    return log_path.with_suffix(".state.json")


def load_state(log_path: Path) -> State:
    sp = state_path(log_path)
    if not sp.exists():
        raise SystemExit(f"[ERR] state 없음: {sp}. init 먼저.")
    return State.from_json(json.loads(sp.read_text(encoding="utf-8")))


def save_state(state: State) -> None:
    sp = state_path(Path(state.log_path))
    sp.parent.mkdir(parents=True, exist_ok=True)
    sp.write_text(json.dumps(state.to_json(), indent=2, ensure_ascii=False), encoding="utf-8")
    write_markdown_log(state)


def write_markdown_log(state: State) -> None:
    p = Path(state.log_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    lines = [f"# Auto-Verify Log (NER 자아성찰) — {Path(state.artifact).name}", ""]
    lines.append(f"- Artifact: `{state.artifact}`")
    lines.append(f"- Request: `{state.request}`")
    lines.append(f"- Max attack iter: {state.max_iter} | Final agents (N/N PASS): {state.final_agents}")
    lines.append(f"- 현재 round: {state.current_iter} | 다음 stage: `{state.next_stage}` | attack 사용: {state.attack_rounds_used}/{state.max_iter}")
    lines.append(f"- 종료: {state.terminated or '진행 중'}")
    lines.append("")
    for r in state.rounds:
        lines.append(f"## Round {r.iteration} — `{r.stage}` ({r.timestamp})")
        for i, v in enumerate(r.verdicts):
            tag = f"Agent {i+1}/{len(r.verdicts)}" if r.stage == "final" else "Agent"
            lines.append(f"- {tag}: `{v}`")
        if r.issues:
            lines.append(f"- Issues ({len(r.issues)}):")
            for it in r.issues:
                sev = it.get("severity", "?")
                cat = it.get("category", "?")
                desc = it.get("description", "")
                refs = ", ".join(it.get("file_refs", []) or [])
                refs_s = f"  ({refs})" if refs else ""
                lines.append(f"  - [{sev}/{cat}] {desc}{refs_s}")
        if r.fixes_applied:
            lines.append(f"- fixes: {r.fixes_applied}")
        if r.raw_response_paths:
            lines.append(f"- raw 감사 trail: {', '.join(f'`{x}`' for x in r.raw_response_paths)}")
        if r.pass_confirmations and any(c for c in r.pass_confirmations):
            n_ok = sum(1 for c in r.pass_confirmations if c)
            lines.append(f"- PASS_CONFIRMATION 통과: {n_ok}/{len(r.pass_confirmations)}")
        lines.append("")
    if state.terminated:
        lines.append(f"## 최종 결과: **{state.terminated}**")
    p.write_text("\n".join(lines), encoding="utf-8")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _summarize_prior(state: State, max_chars: int = 4000) -> str:
    if not state.rounds:
        return "(이전 라운드 없음 — 이번이 첫 공격입니다.)"
    parts = []
    for r in state.rounds:
        stage_tag = "[ATTACK]" if r.stage == "attack" else "[FINAL/병렬]"
        parts.append(f"Round {r.iteration} {stage_tag}: verdicts={r.verdicts}")
        for it in r.issues[:5]:
            parts.append(f"  - [{it.get('severity','?')}/{it.get('category','?')}] {(it.get('description') or '')[:200]}")
        if r.fixes_applied:
            parts.append(f"  -> {stage_tag} 후 fix: {r.fixes_applied[:300]}")
    text = "\n".join(parts)
    return text[-max_chars:] if len(text) > max_chars else text


def _issue_hash(issues: list) -> str:
    """결함 hash (수렴 가드용).

    R3-i06 fix: description wording 살짝 바꾸면 hash 다름 우회 차단.
    normalization: lowercase + whitespace/punctuation 제거 + file_refs 도 포함.
    """
    if not issues:
        return ""
    parts = []
    for it in issues:
        desc = (it.get("description") or "").strip().lower()
        # whitespace + punctuation 압축 (wording 변형 흡수)
        desc_norm = re.sub(r"[\s\.,;:!\?\-_'\"\(\)\[\]\{\}]+", "", desc)[:300]
        # file_refs basename 만 (line 번호 제외) — 같은 file 의 같은 결함은 동일 hash
        refs = sorted(set(
            Path(r.split(":")[0]).name for r in (it.get("file_refs") or [])
        ))
        parts.append(f"{desc_norm}|{','.join(refs)}")
    parts.sort()
    return hashlib.sha1("\n".join(parts).encode("utf-8")).hexdigest()[:12]


def _check_convergence_stuck(state: State) -> Optional[str]:
    issue_rounds = [r for r in state.rounds if r.issues]
    if len(issue_rounds) >= CONVERGENCE_REPEAT:
        last = issue_rounds[-CONVERGENCE_REPEAT:]
        hashes = [_issue_hash(r.issues) for r in last]
        if hashes[0] and all(h == hashes[0] for h in hashes):
            return "ESCALATE_CONVERGENCE_SAME_ISSUES"
    if len(issue_rounds) >= NO_PROGRESS_WINDOW:
        recent = issue_rounds[-NO_PROGRESS_WINDOW:]
        counts = [len(r.issues) for r in recent]
        if all(c >= counts[0] for c in counts[1:]):
            return "ESCALATE_NO_PROGRESS"
    return None


def _extract_pass_confirmation(raw_text: str) -> str:
    if PASS_CONFIRM_HEADER not in raw_text:
        return ""
    after = raw_text.split(PASS_CONFIRM_HEADER, 1)[1]
    for sentinel in (ISSUES_JSON_HEADER, SCRAP_REASON_HEADER, "\nVERDICT:"):
        if sentinel in after:
            after = after.split(sentinel, 1)[0]
    return after.strip()


def _validate_pass_confirmation(text: str, require_focus_keywords: bool = False) -> tuple:
    if not text:
        return False, "PASS_CONFIRMATION 본문 누락/빈값"
    if len(text) < 80:
        return False, f"PASS_CONFIRMATION 너무 짧음 ({len(text)} chars)"
    has_a = any(t in text for t in ("(a)", "a)", "a.", "a:"))
    has_b = any(t in text for t in ("(b)", "b)", "b.", "b:"))
    if not (has_a and has_b):
        return False, "PASS_CONFIRMATION (a)(b) 표기 누락"
    if require_focus_keywords:
        text_lower = text.lower()
        hit = sum(
            1 for g in FOCUS_KEYWORD_GROUPS.values()
            if any(re.search(p, text_lower, re.IGNORECASE) for p in g)
        )
        if hit < 2:
            return False, (
                f"focus 카테고리 {hit}/3만 다룸 (final 룰: 최소 2). "
                "단어 경계 매치 — 짧은 키워드 거짓 양성 차단."
            )
    return True, "ok"


def _is_meta_self_reflection(artifact_path: str) -> bool:
    """ARTIFACT가 본 스크립트 자체인지 detection.

    R2-i02 + R3-i02 fix: byte-동일 카피 (이름 다름) 와 same-name-different-byte 둘 다 메타로 판정.
    조건 (OR):
      (1) 절대 경로 동일
      (2) sha256 hash 동일 (byte 정확 일치, 이름 무관)
      (3) basename 에 'auto_verify_loop' 포함 + 핵심 함수 시그니처 존재
          (cmd_record + _validate_pass_confirmation + FOCUS_KEYWORD_GROUPS)
          → 1바이트 다른 fork 도 본질적으로 같은 스크립트면 메타
    """
    try:
        a = Path(artifact_path).resolve(strict=False)
        s = Path(__file__).resolve(strict=False)
        if a == s:
            return True
        if not a.exists() or not s.exists():
            return False
        # (2) byte 정확 일치
        ah = hashlib.sha256(a.read_bytes()).hexdigest()
        sh = hashlib.sha256(s.read_bytes()).hexdigest()
        if ah == sh:
            return True
        # (3) basename + 본질 시그니처 매치 (1바이트 다른 fork 도 메타)
        if "auto_verify_loop" not in a.name.lower():
            return False
        try:
            a_src = a.read_text(encoding="utf-8")
            signatures = [
                "def cmd_record",
                "def _validate_pass_confirmation",
                "FOCUS_KEYWORD_GROUPS",
                "def _is_meta_self_reflection",
            ]
            sig_hit = sum(1 for sig in signatures if sig in a_src)
            return sig_hit >= 3
        except Exception:
            return False
    except Exception:
        return False


def cmd_init(args: argparse.Namespace) -> int:
    log = Path(args.log)
    if state_path(log).exists() and not args.force:
        raise SystemExit(f"[ERR] 이미 init: {state_path(log)} (--force 로 덮어쓰기)")
    artifact = Path(args.artifact)
    request = Path(args.request)
    if not artifact.exists():
        raise SystemExit(f"[ERR] artifact 없음: {artifact}")
    if not request.exists():
        raise SystemExit(f"[ERR] request 없음: {request}")
    if args.max_iter < 2:
        raise SystemExit("[ERR] --max-iter 최소 2")
    if args.final_agents < 1:
        raise SystemExit("[ERR] --final-agents 최소 1")
    state = State(
        artifact=str(artifact), request=str(request), log_path=str(log),
        max_iter=args.max_iter, final_agents=args.final_agents,
        current_iter=1, next_stage="attack",
    )
    save_state(state)
    print(f"[INIT] log={log} state={state_path(log)}")
    print(f"  artifact={artifact}")
    print(f"  request={request}")
    print(f"  max_iter={args.max_iter} final_agents={args.final_agents}")
    print(f"\n다음: python scripts/auto_verify_loop.py next-prompts --log {log}")
    return 0


def cmd_next_prompts(args: argparse.Namespace) -> int:
    state = load_state(Path(args.log))
    if state.terminated:
        print(f"[TERMINATED] {state.terminated}")
        return 1
    prior = _summarize_prior(state)
    # R1-i05 fix: 메타 자아성찰 (ARTIFACT = auto_verify_loop.py 자체) 시 별도 힌트
    is_meta = _is_meta_self_reflection(state.artifact)
    meta_hint = META_HINT_SELF if is_meta else META_HINT_NORMAL
    meta_extra = META_EXTRA_RULE_SELF if is_meta else ""
    if state.next_stage == "attack":
        prompt = ATTACK_PROMPT.format(
            artifact=state.artifact, request=state.request,
            prior_rounds=prior, round_num=state.current_iter,
            meta_mode_hint=meta_hint, meta_mode_extra_rule=meta_extra,
        )
        print(f"=== Round {state.current_iter} | attack | Agent 1개 | meta={'YES' if is_meta else 'NO'} ===\n")
        print(prompt)
    else:
        n = state.final_agents
        print(f"=== Round {state.current_iter} | final | Agent {n}개 병렬 | {n}/{n} PASS 요구 ===\n")
        for i in range(n):
            focus = FOCUS_ANGLES[i % len(FOCUS_ANGLES)]
            prompt = FINAL_PROMPT.format(
                n=n, other_n=n - 1, focus=focus,
                artifact=state.artifact, request=state.request, prior_rounds=prior,
            )
            print(f"--- Agent {i+1}/{n} ---")
            print(prompt)
            print()
    return 0


def cmd_record(args: argparse.Namespace) -> int:
    state = load_state(Path(args.log))
    if state.terminated:
        raise SystemExit(f"[ERR] 이미 종료: {state.terminated}")

    verdicts = [v.strip().upper() for v in args.verdict.split(",")]
    expected = state.final_agents if state.next_stage == "final" else 1
    if len(verdicts) != expected:
        raise SystemExit(f"[ERR] verdict 개수: stage={state.next_stage} 는 {expected}개, {len(verdicts)}개 받음")
    for v in verdicts:
        if v not in ("PASS", "REVISE", "SCRAP"):
            raise SystemExit(f"[ERR] verdict: {v} (PASS|REVISE|SCRAP)")

    raw_paths = []
    raw_texts = []
    is_meta = _is_meta_self_reflection(state.artifact)
    if args.raw_files:
        raw_paths = [s.strip() for s in args.raw_files.split(",") if s.strip()]
        if len(raw_paths) != len(verdicts):
            raise SystemExit(f"[ERR] raw-files {len(raw_paths)} != verdicts {len(verdicts)}")
        # R3-i05 fix: resolved 비교 (./a vs a 같은 표기 차이 차단)
        resolved_paths = [str(Path(p).resolve(strict=False)) for p in raw_paths]
        if len(set(resolved_paths)) != len(resolved_paths):
            raise SystemExit("[ERR] raw-files 중복 path (resolved). 각 Agent 마다 별도 파일 필수 (위조 차단).")
        seen_hashes = set()
        for rp in raw_paths:
            pp = Path(rp)
            if not pp.exists():
                raise SystemExit(f"[ERR] raw 없음: {pp}")
            content = pp.read_text(encoding="utf-8")
            h = hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]
            if h in seen_hashes:
                raise SystemExit(f"[ERR] raw-files 내용 중복 (hash {h}). 각 Agent 응답 고유해야 함.")
            seen_hashes.add(h)
            if state.artifact.rsplit("/", 1)[-1] not in content and state.artifact not in content:
                raise SystemExit(f"[ERR] raw {rp} 에 ARTIFACT 경로/파일명 mention 없음 (Agent 가 진짜로 읽었는지 의심).")
            if "VERDICT:" not in content:
                raise SystemExit(f"[ERR] raw {rp} 에 VERDICT: 헤더 없음 (LLM 응답 형식 위반 = 가짜 의심).")
            # R1-i01 + R2-i01 + R3-i01 fix: 메타 자아성찰 시 line cite 가드 강화
            # R3-i01: 풀 경로 prefix 만으로는 ARTIFACT 본문 실제 인용 검증 X →
            #   다음 조건 모두 강제 (방어 측 패배 비대칭 차단):
            #   (a) `<basename>:NNN` 풀 경로 cite + line 번호 [1, N] 범위
            #   (b) 최소 3 개 unique line
            #   (c) 각 cite line 의 ARTIFACT 본문 token (≥10 char unique substring) 이 raw 에 존재
            #       → 적대자가 그 line 의 실제 코드를 읽고 인용했다는 증거
            if is_meta:
                artifact_basename = Path(state.artifact).name
                try:
                    artifact_src_lines = Path(state.artifact).read_text(encoding="utf-8").splitlines()
                    artifact_lines = len(artifact_src_lines)
                except Exception:
                    artifact_src_lines = []
                    artifact_lines = 10000
                cite_pattern = re.compile(
                    rf"(?:[\w/\\.-]*{re.escape(artifact_basename)}):(\d{{1,5}})\b"
                )
                cites = cite_pattern.findall(content)
                unique_valid_in_range = set()
                substantiated = set()  # R3-i01: 본문 substring 매치까지 통과한 cite
                for c in cites:
                    n = int(c)
                    if not (1 <= n <= artifact_lines):
                        continue
                    unique_valid_in_range.add(n)
                    if not artifact_src_lines:
                        continue
                    # ARTIFACT 본문 line N 의 unique substring 이 raw 에 있는지 검증
                    line_src = artifact_src_lines[n - 1].strip()
                    if len(line_src) < 10:
                        # 너무 짧은 line (공백/괄호) 은 substring 검증 면제
                        substantiated.add(n)
                        continue
                    # line 의 10+ char substring 중 raw 에 등장하는 게 있는지
                    # (간단한 trigram-like check: 연속 12 char window slide)
                    found = False
                    for i in range(0, max(1, len(line_src) - 11), 3):
                        chunk = line_src[i:i + 12]
                        if len(chunk) >= 10 and chunk in content:
                            found = True
                            break
                    if found:
                        substantiated.add(n)
                if len(unique_valid_in_range) < 3:
                    raise SystemExit(
                        f"[ERR] raw {rp} 메타 자아성찰 R3-i01 가드. "
                        f"valid cite {len(unique_valid_in_range)} 개 (요구: ≥3 unique, "
                        f"'<{artifact_basename}>:NNN' 풀 경로 + [1, {artifact_lines}] 범위)."
                    )
                if artifact_src_lines and len(substantiated) < 2:
                    raise SystemExit(
                        f"[ERR] raw {rp} 메타 자아성찰 R3-i01 본문 인용 검증 실패. "
                        f"cite 한 {len(unique_valid_in_range)} line 중 ARTIFACT 본문 substring "
                        f"매치 {len(substantiated)} 개 (요구: ≥2). "
                        "적대자가 line 번호만 박고 실제 코드는 안 읽은 증거. "
                        "방어 측 패배 비대칭 차단."
                    )
            raw_texts.append(content)
    elif any(v == "PASS" for v in verdicts):
        raise SystemExit("[ERR] PASS 는 --raw-files 필수 (위조/사이코판트 감사)")

    pass_confirmations = []
    if raw_texts:
        require_focus = state.next_stage == "final"
        for i, (v, raw) in enumerate(zip(verdicts, raw_texts)):
            confirm = _extract_pass_confirmation(raw)
            pass_confirmations.append(confirm)
            if v == "PASS":
                ok, reason = _validate_pass_confirmation(confirm, require_focus_keywords=require_focus)
                if not ok:
                    raise SystemExit(f"[ERR] Agent {i+1} PASS_CONFIRMATION 검증 실패: {reason}")

    issues = []
    if args.issues_file:
        p = Path(args.issues_file)
        if not p.exists():
            raise SystemExit(f"[ERR] issues_file 없음: {p}")
        data = json.loads(p.read_text(encoding="utf-8"))
        if not isinstance(data, list):
            raise SystemExit("[ERR] issues_file 은 JSON array")
        issues = data

    if state.rounds:
        prev = state.rounds[-1]
        if any(v == "REVISE" for v in prev.verdicts) and not (args.fixes or "").strip():
            raise SystemExit("[ERR] 직전 REVISE → 이번 record 는 --fixes 필수")

    round_rec = Round(
        iteration=state.current_iter, stage=state.next_stage, timestamp=_now(),
        verdicts=verdicts, issues=issues, fixes_applied=(args.fixes or "").strip(),
        raw_response_paths=raw_paths, pass_confirmations=pass_confirmations,
    )
    state.rounds.append(round_rec)
    if round_rec.stage == "attack":
        state.attack_rounds_used += 1

    state.terminated = _decide_termination(state, verdicts)

    if state.terminated is None:
        state.current_iter += 1
        conv = _check_convergence_stuck(state)
        if conv:
            state.terminated = conv
        elif state.next_stage == "attack" and all(v == "PASS" for v in verdicts):
            state.next_stage = "final"
        elif state.next_stage == "attack" and state.attack_rounds_used >= state.max_iter:
            state.terminated = "ESCALATE_MAX_ITER"
        elif state.next_stage == "final":
            # R1-i09 + R3-i04 fix: final 부분 PASS 시 attack 복귀.
            # attack_rounds_used 카운트는 다음 record 의 line 497-498 에서 (이중 카운트 차단).
            state.next_stage = "attack"

    save_state(state)
    print(f"[RECORD] round={round_rec.iteration} stage={round_rec.stage} verdicts={verdicts} issues={len(issues)} attack_used={state.attack_rounds_used}/{state.max_iter}")
    if state.terminated:
        print(f"\n>>> 종료: {state.terminated}")
    else:
        print(f"\n다음: round {state.current_iter} stage={state.next_stage}")
    return 0


def _decide_termination(state: State, verdicts: list) -> Optional[str]:
    if "SCRAP" in verdicts:
        return "SCRAP"
    if state.next_stage == "final" and all(v == "PASS" for v in verdicts):
        return "PASS"
    return None


def cmd_status(args: argparse.Namespace) -> int:
    state = load_state(Path(args.log))
    print(f"Artifact: {state.artifact}")
    print(f"Request:  {state.request}")
    print(f"진행: {len(state.rounds)} 라운드 | attack {state.attack_rounds_used}/{state.max_iter}")
    print(f"다음: round={state.current_iter} stage={state.next_stage}")
    print(f"종료: {state.terminated or '진행 중'}")
    print()
    for r in state.rounds:
        print(f"  R{r.iteration}[{r.stage}] verdicts={r.verdicts} issues={len(r.issues)} raw={len(r.raw_response_paths)}")
        if r.fixes_applied:
            print(f"       fixes: {r.fixes_applied[:120]}")
    return 0


def cmd_summary(args: argparse.Namespace) -> int:
    state = load_state(Path(args.log))
    write_markdown_log(state)
    print(f"로그: {state.log_path}")
    print(f"state: {state_path(Path(state.log_path))}")
    print(f"종료: {state.terminated or '진행 중'}")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Auto-Verify Loop (NER 자아성찰)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init")
    p.add_argument("--artifact", required=True)
    p.add_argument("--request", required=True)
    p.add_argument("--log", required=True)
    p.add_argument("--max-iter", type=int, default=MAX_ATTACK_ITER)
    p.add_argument("--final-agents", type=int, default=FINAL_AGENTS)
    p.add_argument("--force", action="store_true")
    p.set_defaults(func=cmd_init)

    p = sub.add_parser("next-prompts")
    p.add_argument("--log", required=True)
    p.set_defaults(func=cmd_next_prompts)

    p = sub.add_parser("record")
    p.add_argument("--log", required=True)
    p.add_argument("--verdict", required=True)
    p.add_argument("--issues-file")
    p.add_argument("--fixes")
    p.add_argument("--raw-files")
    p.set_defaults(func=cmd_record)

    p = sub.add_parser("status")
    p.add_argument("--log", required=True)
    p.set_defaults(func=cmd_status)

    p = sub.add_parser("summary")
    p.add_argument("--log", required=True)
    p.set_defaults(func=cmd_summary)

    args = ap.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
    sys.exit(main())
