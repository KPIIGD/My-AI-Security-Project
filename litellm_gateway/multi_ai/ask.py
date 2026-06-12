"""Multi-AI 호출 도구 — litellm PII 캡스톤. 무료모델 우선(OpenRouter/Groq/GitHub).

finence multi_ai/ask.py 이식 → PII 가드레일/한국어 보안 연구 도메인 맞춤.

사용법:
  python multi_ai/ask.py gpt "질문"
  python multi_ai/ask.py openrouter_glm "질문"      # 무료 모델 단일
  python multi_ai/ask.py both "질문"                 # 두 모델
  python multi_ai/ask.py debate "질문"               # 3-라운드 토론(무료 3혈통, Devil's Advocate)
  python multi_ai/ask.py debate --diverse "질문"     # 다양성 사고(DMAD ICLR 2025)

옵션:
  --system "시스템 프롬프트" / --no-log / --models a,b,c / --rounds N / --diverse
"""
import argparse
import datetime
import json
import os
import sys
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

# .env 로드 — multi_ai/.env(무료키) 우선, 없으면 루트 c:/litellm/.env(OPENROUTER/GEMINI) 폴백.
for _env in [Path(__file__).parent / ".env", Path(__file__).parent.parent / ".env"]:
    if _env.exists():
        for line in _env.read_text(encoding="utf-8", errors="ignore").splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

import litellm

litellm.suppress_debug_info = True

# litellm github provider 는 GITHUB_API_KEY 를 읽음 — 우리 .env 는 GITHUB_MODELS_TOKEN
if os.environ.get("GITHUB_MODELS_TOKEN") and not os.environ.get("GITHUB_API_KEY"):
    os.environ["GITHUB_API_KEY"] = os.environ["GITHUB_MODELS_TOKEN"]

MODELS = {
    "gpt": "gpt-5-pro",
    "gpt_fast": "gpt-5",
    "gpt_o3": "o3",
    "gemini": "gemini/gemini-pro-latest",
    "gemini_flash": "gemini/gemini-flash-latest",
    "claude": "anthropic/claude-opus-4-7",
    "claude_sonnet": "anthropic/claude-sonnet-4-6",
    # ── 무료 모델 (크레딧 0 research) ──
    "groq_llama": "groq/llama-3.3-70b-versatile",
    "groq_gptoss": "groq/openai/gpt-oss-120b",
    "cerebras_glm": "cerebras/zai-glm-4.7",
    "cerebras_gptoss": "cerebras/gpt-oss-120b",
    "openrouter_llama": "openrouter/meta-llama/llama-3.3-70b-instruct:free",
    "openrouter_glm": "openrouter/nex-agi/nex-n2-pro:free",
    "openrouter_nemotron": "openrouter/nvidia/nemotron-3-super-120b-a12b:free",
    "openrouter_kimi": "openrouter/moonshotai/kimi-k2.6:free",
    "github_4omini": "github/gpt-4o-mini",
}
GEMINI_FALLBACK = "gemini/gemini-flash-latest"
LABEL = {
    "gpt": "GPT-5 Pro", "gpt_fast": "GPT-5", "gpt_o3": "GPT o3 (reasoning)",
    "gemini": "Gemini Pro", "gemini_flash": "Gemini Flash",
    "claude": "Claude Opus 4.7", "claude_sonnet": "Claude Sonnet 4.6",
    "groq_llama": "Llama-3.3-70B (Groq)", "groq_gptoss": "gpt-oss-120B (Groq)",
    "cerebras_glm": "GLM-4.7 (Cerebras)", "cerebras_gptoss": "gpt-oss-120B (Cerebras)",
    "openrouter_llama": "Llama-3.3-70B (OpenRouter)",
    "openrouter_glm": "Nex-N2-Pro (OpenRouter)", "openrouter_nemotron": "Nemotron-120B (OpenRouter)",
    "openrouter_kimi": "Kimi-K2.6 (OpenRouter)", "github_4omini": "GPT-4o-mini (GitHub)",
}

# 다양성 사고 (Diversity of Thought, DMAD ICLR 2025) — 각 모델에 다른 추론 방식 강제.
REASONING_METHODS = {
    "gpt": ("🔍 추론 방식 강제 (Chain of Thought): 단계별 사슬로 추론. 각 결론마다 직전 단계 명시 + 단계별 검증 1줄."),
    "gpt_fast": ("🔍 추론 방식 강제 (Chain of Thought): 단계별 사슬. 각 결론마다 이전 단계 명시 + 검증 1줄."),
    "gpt_o3": ("🔍 추론 방식 강제 (Chain of Thought + Self-Verification): 단계별 + 자가 검증 의무."),
    "claude": ("🌱 추론 방식 강제 (First Principles): 기본 원리부터. 깔린 가정 모두 명시 → 가정 하나 무너지면 결론도 무너지는 부분 명시."),
    "claude_sonnet": ("🌱 추론 방식 강제 (First Principles): 기본 원리 + 가정 명시 의무."),
    "gemini": ("🔗 추론 방식 강제 (Analogical Reasoning): 다른 도메인(생물/물리/역사/일상) 유사 사례 1-2개로 비교 후 본 문제에 적용."),
    "gemini_flash": ("🔗 추론 방식 강제 (Analogical Reasoning): 다른 도메인 비유 1개 의무."),
    "groq_llama": ("🌱 추론 방식 강제 (First Principles): 가정 명시 의무."),
    "groq_gptoss": ("🔍 추론 방식 강제 (Chain of Thought): 단계별 + 검증 1줄."),
    "openrouter_glm": ("🔗 추론 방식 강제 (Analogical Reasoning): 다른 도메인 비유 1개."),
}

NO_TEMPERATURE_MODELS = {
    "anthropic/claude-opus-4-7", "gpt-5", "gpt-5-pro", "gpt-5-codex", "o3", "o1", "o1-pro", "o3-mini", "o3-pro",
}
LONG_TIMEOUT_MODELS = {"gpt-5-pro", "o1-pro", "o3-pro", "o3", "o1"}


def _ask(model_key: str, prompt: str, system: str | None = None) -> str:
    msgs = []
    if system:
        msgs.append({"role": "system", "content": system})
    msgs.append({"role": "user", "content": prompt})

    targets = [MODELS[model_key]]
    if model_key == "gemini":
        targets.append(GEMINI_FALLBACK)

    last_err = None
    for m in targets:
        try:
            kwargs = {"model": m, "messages": msgs}
            if m not in NO_TEMPERATURE_MODELS:
                kwargs["temperature"] = 0.7
            if m in LONG_TIMEOUT_MODELS:
                kwargs["timeout"] = 240
            elif m.startswith("gemini/"):
                kwargs["timeout"] = 60 if "flash" not in m else 30
            r = litellm.completion(**kwargs)
            return (r.choices[0].message.content or "").strip()
        except Exception as e:
            last_err = e
            err = str(e).lower()
            if not any(x in err for x in ("503", "unavailable", "overload", "timeout", "timed out")):
                raise
    raise last_err if last_err else RuntimeError("all targets failed")


def _log(payload: dict) -> Path:
    log_dir = Path(__file__).parent / "logs"
    log_dir.mkdir(exist_ok=True)
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    f = log_dir / f"{ts}_{payload['mode']}.json"
    f.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return f


def cmd_single(model_key: str, prompt: str, system: str | None, log: bool):
    ans = _ask(model_key, prompt, system)
    print(ans)
    if log:
        _log({"mode": model_key, "ts": datetime.datetime.now().isoformat(),
              "system": system, "prompt": prompt, "answer": ans})


def cmd_both(prompt: str, system: str | None, log: bool):
    out = {}
    for k in ("openrouter_glm", "groq_llama"):
        print(f"\n===== {LABEL[k]} =====")
        try:
            out[k] = _ask(k, prompt, system)
        except Exception as e:
            out[k] = f"[ERROR] {e}"
        print(out[k])
    if log:
        _log({"mode": "both", "ts": datetime.datetime.now().isoformat(),
              "system": system, "prompt": prompt, "answers": out})


def cmd_debate(prompt: str, system: str | None, log: bool,
               models: list | None = None, num_rounds: int = 3, diverse: bool = False):
    """N-라운드 토론. 기본 = 3라운드, 무료 3혈통. Round1 독립 → 반박/수정 → 최종 결론.

    [메타 토론 룰]
    1. 표본 n<30 → '추측' 태그 강제, 확신도 % 금지
    2. 입장 수정 시 '왜 처음 틀렸나' 1줄 명시 필수
    3. Devil's Advocate 1명 강제(rotate)
    4. 만장일치 = group think 의심 → 마지막 라운드 반대 검증
    diverse=True 시 각 모델 다른 추론 방식(DMAD ICLR 2025).
    """
    sys_default = (
        "너는 한국어 PII 가드레일/AI 보안 연구 자문 AI 다. 한국어로 짧고 구체적으로 답하라. "
        "탐지율·우회율·복구율 등 측정/통계/위협모델 관점 우선. 추측은 반드시 '추측' 태그.\n"
        "[필수 룰]\n"
        "1. 평가 표본 n<30 시 → 모든 의견에 '추측' 태그 강제, 확신도 % 표기 금지\n"
        "2. 이전 라운드 입장 수정 시 → '왜 처음 틀렸나' 1줄 명시 필수\n"
        "3. 만장일치 = group think 의심. 합의보다 솔직한 반박 우선\n"
        "4. 가드레일은 fail-CLOSED 가 기본. '아마 막힌다' 추측 금지 — 실측 우선\n"
        "5. '실행 안 되는 목록 5개' = 아첨. 실행 1개 > 목록 5개"
    )
    sys_msg = system or sys_default

    if models is None:
        # 2026-06-12 생존조사: groq_llama·groq_gptoss 확인 작동. openrouter 무료슬러그/gemini 死.
        # 기본 = 작동 확인된 Groq 2혈통(Llama/GPT-oss) + OpenRouter Llama(폴백, 실패해도 [ERROR] 태그로 계속).
        models = ["groq_llama", "groq_gptoss", "openrouter_llama"]

    if num_rounds < 2:
        num_rounds = 2

    da_index = datetime.datetime.now().minute % len(models)
    da_model = models[da_index]
    print(f"\n🎭 이번 토론 Devil's Advocate: {LABEL[da_model]}")
    if diverse:
        print("🎨 다양성 사고 ON — 각 모델 다른 추론 방식 (DMAD ICLR 2025)")

    rounds = {f"r{i}": {} for i in range(1, num_rounds + 1)}

    # Round 1: 독립 의견
    print(f"\n========== Round 1/{num_rounds}: 독립 의견 ==========")
    for k in models:
        da_tag = " (Devil's Advocate)" if k == da_model else ""
        method_tag = " [다양성]" if diverse and k in REASONING_METHODS else ""
        print(f"\n----- {LABEL[k]}{da_tag}{method_tag} -----")
        method_prefix = (REASONING_METHODS[k] + "\n\n") if (diverse and k in REASONING_METHODS) else ""
        if k == da_model:
            da_prompt = (
                f"{method_prefix}{prompt}\n\n"
                f"⚠️ 너는 이번 토론의 Devil's Advocate (반대 옹호자) 다.\n"
                f"다른 AI 가 동의할 만한 의견이라도 반박/회의적 입장 우선. 비관/리스크/우회 시나리오 강조.\n"
                f"단 무리한 반대 X — 데이터·위협모델 기반의 합리적 회의."
            )
        else:
            da_prompt = f"{method_prefix}{prompt}"
        try:
            rounds["r1"][k] = _ask(k, da_prompt, sys_msg)
        except Exception as e:
            rounds["r1"][k] = f"[ERROR] {e}"
        print(rounds["r1"][k])

    # Round 2 ~ N-1: 상호 반박/수정
    for r_idx in range(2, num_rounds):
        prev_r, cur_r = f"r{r_idx - 1}", f"r{r_idx}"
        print(f"\n========== Round {r_idx}/{num_rounds}: 반박/수정 ==========")
        for k in models:
            others = "\n\n".join(
                f"### {LABEL[o]}{' (DA)' if o == da_model else ''}\n{rounds[prev_r][o]}"
                for o in models if o != k)
            r_prompt = (
                f"원 질문:\n{prompt}\n\n너의 직전 답변:\n{rounds[prev_r][k]}\n\n"
                f"다른 AI들의 직전 답변:\n{others}\n\n"
                f"동의/반박할 점 + 수정안을 250자 내외로. "
                f"⚠️ 입장 수정 시 '왜 직전이 틀렸나' 1줄 필수. ⚠️ 만장일치면 group think 의심하고 반박 1개 시도.")
            print(f"\n----- {LABEL[k]}{' (DA)' if k == da_model else ''} -----")
            try:
                rounds[cur_r][k] = _ask(k, r_prompt, sys_msg)
            except Exception as e:
                rounds[cur_r][k] = f"[ERROR] {e}"
            print(rounds[cur_r][k])

    # Round N: 최종 결론
    last_r = f"r{num_rounds}"
    print(f"\n========== Round {num_rounds}/{num_rounds}: 최종 결론 ==========")
    for k in models:
        history = "\n".join(
            "\n".join(f"[R{i} {LABEL[o]}] {rounds[f'r{i}'].get(o, '')[:300]}" for o in models)
            for i in range(1, num_rounds))
        r_prompt = (
            f"원 질문:\n{prompt}\n\n전체 토론 기록(요약):\n{history}\n\n"
            f"최종 결론 + 권장 액션을 5줄 이내로. "
            f"⚠️ 표본 n<30 시 확신도 % 금지, '추측' 태그 의무. ⚠️ 실행 1개 > 목록 5개. ⚠️ 만장일치도 자가 점검.")
        print(f"\n----- {LABEL[k]}{' (DA)' if k == da_model else ''} -----")
        try:
            rounds[last_r][k] = _ask(k, r_prompt, sys_msg)
        except Exception as e:
            rounds[last_r][k] = f"[ERROR] {e}"
        print(rounds[last_r][k])

    if log:
        path = _log({
            "mode": "debate", "ts": datetime.datetime.now().isoformat(),
            "system": sys_msg, "prompt": prompt, "models": models, "num_rounds": num_rounds,
            "devils_advocate": da_model, "diverse": diverse,
            "reasoning_methods_applied": ({k: REASONING_METHODS[k] for k in models if k in REASONING_METHODS} if diverse else None),
            "rounds": rounds,
        })
        print(f"\n💾 로그: {path}")


def main():
    p = argparse.ArgumentParser(description="Multi-AI debate tool (litellm PII capstone)")
    p.add_argument("mode", choices=list(MODELS.keys()) + ["both", "debate"])
    p.add_argument("prompt", help="질문 내용")
    p.add_argument("--system", default=None)
    p.add_argument("--no-log", action="store_true")
    p.add_argument("--models", default=None, help="debate 모델 (콤마 구분)")
    p.add_argument("--rounds", type=int, default=3)
    p.add_argument("--diverse", action="store_true", help="다양성 사고(DMAD) — 모델별 다른 추론 방식")
    args = p.parse_args()

    log = not args.no_log
    models = [m.strip() for m in args.models.split(",")] if args.models else None

    if args.mode in MODELS:
        cmd_single(args.mode, args.prompt, args.system, log)
    elif args.mode == "both":
        cmd_both(args.prompt, args.system, log)
    elif args.mode == "debate":
        cmd_debate(args.prompt, args.system, log, models=models, num_rounds=args.rounds, diverse=args.diverse)


if __name__ == "__main__":
    main()
