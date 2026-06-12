"""
Multi-AI debate runner — Claude + GPT + Gemini.

Usage:
  python debate.py "주제 한 줄"                       # 병렬 모드 (기본, 1라운드)
  python debate.py --mode debate "주제"               # 토론 모드 (2라운드)
  python debate.py --models claude,gpt "주제"         # 일부 모델만
  python debate.py --context paper/capstone_main_v1.md "주제"  # 컨텍스트 파일 첨부

결과: 콘솔 출력 + debate_history/ 폴더에 markdown 자동 저장
"""
import argparse
import asyncio
import datetime
import json
import os
import sys
from pathlib import Path

import httpx

# Load .env
ROOT = Path(__file__).parent
env_file = ROOT / ".env"
if env_file.exists():
    for line in env_file.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

ANTHROPIC_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
OPENAI_KEY = os.environ.get("OPENAI_API_KEY", "")
GEMINI_KEY = os.environ.get("GEMINI_API_KEY", "")

# 모델 (필요 시 수정)
CLAUDE_MODEL = "claude-opus-4-7"
GPT_MODEL = "gpt-5.5"  # 2026-04-23 최신. pro 변형은 Responses API 전용이라 chat completions 미지원
# 503/오류·빈응답 시 자동 fallback. 2.5-pro를 메인으로 (3.1-preview는 reliability 낮음)
GEMINI_MODELS = [
    "gemini-2.5-pro",  # 안정적 + thinking budget 잘 동작
    "gemini-3-pro-preview",
    "gemini-3.1-pro-preview",
    "gemini-2.5-flash",
]
GEMINI_MODEL = GEMINI_MODELS[0]
GEMINI_MAX_OUTPUT_TOKENS = 24000  # thinking + 응답 둘 다 여유
GEMINI_THINKING_BUDGET = 2000  # thinking이 24000을 다 잡아먹는 거 방지

SYSTEM_PROMPT = """너는 한국어 PII 가드레일 캡스톤 자문 AI다.

프로젝트 컨텍스트:
- 연구자: 정보보안학과 학부생, 지도교수 임정묵
- 스택: LiteLLM Gateway + Presidio + AWS Bedrock + Lakera + GPT-4o judge + 자체 Korean Layer 0
- Layer 0: 13단계 한국어 정규화 + 42개 정규식 + 22개 키워드 사전 (결정론적, LLM 미사용)
- 결과: KR_semantic 49.6% → 96.4% (vs LLM judge 87.4%, p<1e-28), $0.08 vs $1.35/10k requests
- 정직한 포지션: "보강 계층 (Complementary Layer)" — 단독 31% overall / 80.65% KR_semantic

[필수 규칙 — 위반 시 답변 무효]
1. 동의·hedging 금지. "적절합니다", "유리합니다", "좋은 선택입니다" 류 추상어 사용 시 답변 무효.
2. 모든 주장에 숫자, 모델명, 또는 인용을 동반. "왜 그런가"가 한 줄로 적히지 않으면 무효.
3. trade-off 명시. "X가 좋다"가 아니라 "X는 A·B에는 좋고 C·D에는 나쁘다, 너 상황에선 A가 더 큰 비중".
4. 다른 AI 답변 검토 후 "전적으로 동의"·"동의합니다"만 적는 것 금지. 다른 점 최소 1개 찾아 명시.
5. 입장 수정 시 "왜 처음 틀렸나" 1줄 필수.
6. 만장일치는 group think 의심. 합의보다 솔직한 반박 우선.
7. 답변 전 자가검정: "이 줄이 추상어인가, 동의 회피인가" 체크 후 출력.
8. 한국어 답변. 보안·NLP 전문용어 사용 OK."""


async def ask_claude(client, prompt, system=SYSTEM_PROMPT):
    if not ANTHROPIC_KEY:
        return "[ANTHROPIC_API_KEY missing]"
    r = await client.post(
        "https://api.anthropic.com/v1/messages",
        headers={
            "x-api-key": ANTHROPIC_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": CLAUDE_MODEL,
            "max_tokens": 1500,
            "system": system,
            "messages": [{"role": "user", "content": prompt}],
        },
        timeout=120,
    )
    if r.status_code != 200:
        return f"[Claude error {r.status_code}: {r.text[:300]}]"
    return r.json()["content"][0]["text"]


async def ask_gpt(client, prompt, system=SYSTEM_PROMPT):
    if not OPENAI_KEY:
        return "[OPENAI_API_KEY missing]"
    body = {
        "model": GPT_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": prompt},
        ],
    }
    # gpt-5.x는 max_completion_tokens, 4o 계열은 max_tokens
    if "gpt-5" in GPT_MODEL or GPT_MODEL.startswith("o"):
        body["max_completion_tokens"] = 4000
        # 5.x / o-series는 temperature 기본값(1)만 지원
    else:
        body["max_tokens"] = 1500
        body["temperature"] = 0.7
    r = await client.post(
        "https://api.openai.com/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENAI_KEY}",
            "Content-Type": "application/json",
        },
        json=body,
        timeout=180,
    )
    if r.status_code != 200:
        return f"[GPT error {r.status_code}: {r.text[:300]}]"
    return r.json()["choices"][0]["message"]["content"]


async def ask_gemini(client, prompt, system=SYSTEM_PROMPT):
    if not GEMINI_KEY:
        return "[GEMINI_API_KEY missing]"
    full = f"{system}\n\n---\n\n{prompt}"
    last_err = ""
    for model in GEMINI_MODELS:
        is_pro_thinking = "pro" in model and ("3" in model or "2.5" in model)
        gen_cfg = {
            "maxOutputTokens": GEMINI_MAX_OUTPUT_TOKENS if is_pro_thinking else 4000,
            "temperature": 0.7,
        }
        if is_pro_thinking:
            # thinking이 응답 토큰을 다 먹는 걸 방지
            gen_cfg["thinkingConfig"] = {"thinkingBudget": GEMINI_THINKING_BUDGET}
        r = await client.post(
            f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
            params={"key": GEMINI_KEY},
            json={
                "contents": [{"parts": [{"text": full}]}],
                "generationConfig": gen_cfg,
            },
            timeout=180,
        )
        if r.status_code == 200:
            data = r.json()
            try:
                cand = data["candidates"][0]
                content = cand.get("content", {})
                parts = content.get("parts", [])
                text = parts[0].get("text", "") if parts else ""
                if not text.strip():
                    finish = cand.get("finishReason", "?")
                    last_err = f"empty content model={model} finish={finish} (thinking burned tokens?)"
                    continue
                used = "" if model == GEMINI_MODELS[0] else f"\n\n*(fallback: {model})*"
                return text + used
            except (KeyError, IndexError) as e:
                last_err = f"parse error model={model}: {e} | {json.dumps(data)[:200]}"
                continue
        last_err = f"{r.status_code} model={model}: {r.text[:200]}"
        if r.status_code in (503, 429):
            continue
        return f"[Gemini error {last_err}]"
    return f"[Gemini all models failed. Last: {last_err}]"


ASK_FN = {"claude": ask_claude, "gpt": ask_gpt, "gemini": ask_gemini}


DEVILS_ADVOCATE_PROMPT = """⚠️ 너는 이번 토론의 Devil's Advocate (반대 옹호자) 다.
다른 AI가 동의할 만한 의견이라도 반박/회의적 입장 우선.
낙관 시나리오 X, 비관/리스크 시나리오 강조.
단 무리한 반대 X — 데이터 기반의 합리적 회의."""


async def round1(topic, models, da_model=None):
    async with httpx.AsyncClient() as client:
        tasks = []
        for m in models:
            prompt = topic
            if m == da_model:
                prompt = f"{topic}\n\n---\n{DEVILS_ADVOCATE_PROMPT}"
            tasks.append(ASK_FN[m](client, prompt))
        results = await asyncio.gather(*tasks, return_exceptions=True)
    return dict(zip(models, [str(r) if isinstance(r, Exception) else r for r in results]))


async def next_round(topic, prev_rounds, models, round_num):
    """Each AI sees previous rounds and continues. round_num >= 2."""
    async with httpx.AsyncClient() as client:
        tasks = []
        for m in models:
            history = ""
            for ridx, results in enumerate(prev_rounds, 1):
                history += f"\n\n=== Round {ridx} ===\n"
                for name, body in results.items():
                    tag = "너의" if name == m else f"{name.upper()}의"
                    history += f"\n[{tag} R{ridx} 답변]\n{body}\n"

            if round_num == 2:
                instruction = """다른 두 AI 답변 보고 너 입장 보강·반박·합의 정리. 새 정보·관점 위주, 1R 반복 금지.

⚠️ 입장 수정 시 "왜 처음 틀렸나" 1줄 명시 필수.
⚠️ 만장일치 보이면 group think 의심하고 반박 1개 시도."""
            else:
                instruction = f"""R{round_num-1}에서 어디까지 좁혀졌는지 보고, 너 최종 입장 정리. 잘못 봤던 점 인정, 옳다 본 점 강화. 인간이 결정해야 할 잔여 쟁점 1~2개 명시.

⚠️ 입장 수정 시 "왜 처음 틀렸나" 1줄 명시 필수.
⚠️ 만장일치도 의심 — 자기 입장이 group think인지 자가 점검."""

            prompt = f"""원래 주제: {topic}
{history}

---
이번은 Round {round_num}.
{instruction}"""
            tasks.append(ASK_FN[m](client, prompt))
        results = await asyncio.gather(*tasks, return_exceptions=True)
    return dict(zip(models, [str(r) if isinstance(r, Exception) else r for r in results]))


def save(topic, mode, rounds, context_file=None):
    ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir = ROOT / "debate_history"
    out_dir.mkdir(exist_ok=True)
    safe = "".join(c if c.isalnum() else "_" for c in topic[:40])
    f = out_dir / f"{ts}_{mode}_{safe}.md"
    with f.open("w", encoding="utf-8") as fp:
        fp.write(f"# Debate: {topic}\n\n")
        fp.write(f"- Date: {datetime.datetime.now().isoformat()}\n")
        fp.write(f"- Mode: {mode}\n")
        if context_file:
            fp.write(f"- Context: {context_file}\n")
        fp.write("\n")
        for round_idx, results in enumerate(rounds, 1):
            fp.write(f"\n## Round {round_idx}\n\n")
            for name, body in results.items():
                fp.write(f"### {name.upper()}\n\n{body}\n\n---\n\n")
    return f


def print_results(round_idx, results):
    print(f"\n{'═'*72}")
    print(f"  ROUND {round_idx}")
    print(f"{'═'*72}")
    for name, body in results.items():
        print(f"\n┌─ {name.upper()} {'─'*(70-len(name)-3)}")
        for line in (body if isinstance(body, str) else str(body)).splitlines():
            print(f"│ {line}")
        print(f"└{'─'*70}\n")


async def main():
    p = argparse.ArgumentParser()
    p.add_argument("topic", nargs="+")
    p.add_argument("--mode", default="parallel", choices=["parallel", "debate"])
    p.add_argument("--rounds", type=int, default=None, help="라운드 수 (2~5). 지정 시 mode=debate 강제")
    p.add_argument("--models", default="claude,gpt,gemini")
    p.add_argument("--context", help="파일 경로 — 컨텐츠를 주제에 첨부")
    args = p.parse_args()

    topic = " ".join(args.topic)
    models = [m.strip() for m in args.models.split(",") if m.strip() in ASK_FN]
    if not models:
        print("[error] no valid models", file=sys.stderr)
        sys.exit(1)

    if args.context:
        ctx_path = Path(args.context)
        if not ctx_path.exists():
            ctx_path = ROOT / args.context
        ctx_content = ctx_path.read_text(encoding="utf-8")[:8000]
        topic = f"{topic}\n\n--- 참고 컨텍스트 ({args.context}) ---\n{ctx_content}"

    print(f"\n🎭 Debate: {' '.join(args.topic)}")
    print(f"   Mode: {args.mode} | Models: {','.join(models)}")

    # Devil's Advocate: 매 토론 시간 분 단위로 rotate
    da_idx = datetime.datetime.now().minute % len(models)
    da_model = models[da_idx]
    print(f"   Devil's Advocate (R1): {da_model.upper()}\n")

    total_rounds = args.rounds if args.rounds else (2 if args.mode == "debate" else 1)
    total_rounds = max(1, min(total_rounds, 5))
    if total_rounds > 1:
        args.mode = "debate"

    r1 = await round1(topic, models, da_model=da_model)
    print_results(1, r1)
    rounds = [r1]

    for ridx in range(2, total_rounds + 1):
        print(f"\n⏳ Round {ridx} 진행 중...")
        r = await next_round(topic, rounds, models, ridx)
        print_results(ridx, r)
        rounds.append(r)

    f = save(" ".join(args.topic), args.mode, rounds, args.context)
    print(f"\n📁 저장됨: {f.relative_to(ROOT)}")


if __name__ == "__main__":
    asyncio.run(main())
