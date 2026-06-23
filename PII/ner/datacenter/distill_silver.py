"""LLM 증류 — weak 문서를 강한 teacher 로 재라벨해 silver gold 생성.

검증 권고 + 사용자 결정(2026-06-05): "수집 그만, weak 데이터 살려라."
weak_examples(실제 한국어 챗 도메인) → teacher(gpt-4o-mini) NER 재라벨 → silver gold.
regex weak 라벨보다 질이 압도적이고, 타겟 도메인(챗 PII) 그대로라 학습 신호로 직행 가능.

핵심 설계:
  - LLM 은 char offset 못 센다 → **엔티티 텍스트만 추출**시키고 우리가 문장에서 위치 검색.
  - 할루시네이션 가드: 추출 text 가 문장에 실재해야 채택 (없으면 버림).
  - silver 는 gold 와 별 license("silver-distilled-...") → 미혼합, ablation/누설게이트로 검증.
  - 누설(KLUE test) 제거 + dedup + 이미 적재된 ner_examples 문장 재증류 안 함.
  - DB content_hash UNIQUE = 자동 resume (재실행 시 미처리분만).

⚠️ silver ≠ 사람 gold. teacher 오류 있음. CC-BY-SA export 기본 제외(license 다름).
   학습 투입 전 source_ablation 으로 KLUE val 영향 검증 필수(v2 교훈).

사용 (PowerShell, C:/My-AI-Security-Project/PII/ner):
  python datacenter/distill_silver.py --dry-run --n 50          # 후보+비용 미리보기(API 0)
  python datacenter/distill_silver.py --n 50000 --concurrency 8 # 본 증류
  python datacenter/distill_silver.py --n 50000 --resume        # 끊기면 이어서
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sqlite3
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))

import db  # noqa: E402
from schema import LABEL2ID, content_hash, count_entities, validate_example  # noqa: E402
from leakage_gate import _eval_hashes  # noqa: E402

# in-domain = 챗/대화/상담/리뷰 (일반인 PII). 나무위키/위키/뉴스는 제외:
#   백과·뉴스 인명은 대부분 공인(라벨가이드 제외 대상)이라 증류 수율 낮고 도메인 불일치.
DEFAULT_SOURCES = [
    "dialogue_weak", "safe_conv_weak", "review_weak", "privacy_weak",
    "medical_qa_weak", "ducut91_weak", "financial_weak",
]
_SENT_SPLIT = re.compile(r"(?<=[.!?。…])\s+|\n+|'\s*,\s*'|\"\s*,\s*\"")
_VALID = {"NAME", "ADDRESS", "ORG"}

# 압축본 — 매 요청 전송되므로 TPM 절감 위해 짧게(규칙은 유지).
_SYSTEM_PROMPT = (
    "한국어 문장에서 PII만 JSON 추출.\n"
    "NAME=일반인 실명(공인·역사인물·직책·호칭 제외). "
    "ADDRESS=주소 전체 span(일반지명·비식별 제외). "
    "ORG=회사/학교/병원/기관(부서단독·일반명사 제외).\n"
    "조사·호칭 빼라(\"홍길동이\"→\"홍길동\"). 문장에 실재하는 부분문자열만. 모호하면 제외.\n"
    "출력만: {\"entities\":[{\"type\":\"NAME\",\"text\":\"...\"}]} (없으면 빈 배열)"
)


# ── 프로바이더 프리셋 (전부 OpenAI 호환 엔드포인트) ───────────────
PROVIDERS = {
    "openai":     {"base_url": None,                                          "key_env": "OPENAI_API_KEY",     "model": "gpt-4o-mini"},
    "openrouter": {"base_url": "https://openrouter.ai/api/v1",                "key_env": "OPENROUTER_API_KEY", "model": "deepseek/deepseek-chat"},
    "deepseek":   {"base_url": "https://api.deepseek.com",                    "key_env": "DEEPSEEK_API_KEY",   "model": "deepseek-chat"},
    "gemini":     {"base_url": "https://generativelanguage.googleapis.com/v1beta/openai/", "key_env": "GEMINI_API_KEY", "model": "gemini-2.0-flash"},
}


# ── API 키 로드 (env → C:\litellm\.env 폴백) ─────────────────────
def _load_key(env_name: str) -> str:
    key = os.environ.get(env_name)
    if key:
        return key
    for envf in (Path(r"C:\litellm\.env"), _HERE.parents[2] / ".env"):
        if envf.exists():
            for line in envf.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith(env_name):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise SystemExit(f"{env_name} 없음 — env 또는 C:\\litellm\\.env 에 추가하세요 (채팅에 붙이지 말 것).")


# ── 후보 문장 추출 (소스별 균형 — 큰 소스가 다 먹지 않게) ────────
def _first_good_sentence(raw: str, min_len: int, max_len: int) -> str | None:
    for sent in _SENT_SPLIT.split(raw or ""):
        sent = sent.strip().strip("[]'\"")
        if min_len <= len(sent) <= max_len:
            return sent
    return None


def candidate_sentences(conn: sqlite3.Connection, sources: list[str], n: int,
                        *, min_len: int, max_len: int, seed: int) -> list[str]:
    import random
    rng = random.Random(seed)
    leak = _eval_hashes() if (_HERE.parent / "data" / "pii_ner_v4_full.json").exists() else set()
    done = {h for (h,) in conn.execute("SELECT content_hash FROM ner_examples")}  # 이미 gold/silver
    per_source = max(1, n // len(sources))
    out: list[str] = []
    surplus: list[str] = []
    seen: set[str] = set()
    for src in sources:
        rows = conn.execute("SELECT sentence FROM weak_examples WHERE source=?", (src,)).fetchall()
        rng.shuffle(rows)
        got = 0
        for (sentence,) in rows:
            sent = _first_good_sentence(sentence, min_len, max_len)
            if sent is None:
                continue
            h = content_hash(sent)
            if h in seen or h in done or h in leak:
                continue
            seen.add(h)
            if got < per_source:
                out.append(sent); got += 1
            else:
                surplus.append(sent)  # 균형분 초과분은 부족분 top-up 풀로
    # 작은 소스가 per_source 못 채우면 surplus 로 n 까지 보충
    rng.shuffle(surplus)
    for sent in surplus:
        if len(out) >= n:
            break
        out.append(sent)
    rng.shuffle(out)
    return out[:n]


# ── teacher 호출 ─────────────────────────────────────────────────
def call_teacher(client, model: str, sentence: str) -> tuple[list[dict], dict]:
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": _SYSTEM_PROMPT},
                  {"role": "user", "content": sentence}],
        response_format={"type": "json_object"},
        temperature=0,
        max_tokens=400,
    )
    content = resp.choices[0].message.content or "{}"
    ents: list = []
    try:
        data = json.loads(content)
        if isinstance(data, list):              # 모델이 {"entities":..} 대신 [..] 반환
            ents = data
        elif isinstance(data, dict):
            ents = data.get("entities") or data.get("results") or data.get("pii") or []
    except (json.JSONDecodeError, AttributeError):
        ents = []
    ents = [e for e in ents if isinstance(e, dict)]  # dict 아닌 항목 제거
    usage = {"in": resp.usage.prompt_tokens, "out": resp.usage.completion_tokens}
    return ents, usage


# ── 엔티티 → BIO example (할루시네이션 가드 포함) ─────────────────
def to_example(sentence: str, entities: list[dict]) -> dict | None:
    spans: list[tuple[int, int, str]] = []
    for ent in entities:
        et = (ent.get("type") or "").upper()
        tx = (ent.get("text") or "").strip()
        if et not in _VALID or len(tx) < 1 or tx not in sentence:  # 가드: 문장에 실재해야
            continue
        start = 0
        while True:  # 모든 비중첩 출현 라벨
            i = sentence.find(tx, start)
            if i < 0:
                break
            spans.append((i, i + len(tx), et))
            start = i + len(tx)
    chars = list(sentence)
    n = len(chars)
    label_names = ["O"] * n
    for s, e, et in sorted(spans, key=lambda x: x[1] - x[0], reverse=True):  # 긴 것 우선
        if s < 0 or e > n or any(label_names[i] != "O" for i in range(s, e)):
            continue
        label_names[s] = f"B-{et}"
        for i in range(s + 1, e):
            label_names[i] = f"I-{et}"
    ex = {
        "tokens": chars,
        "labels": [LABEL2ID[l] for l in label_names],
        "label_names": label_names,
        "sentence": sentence,
        "source": "distill_silver",
    }
    ok, _ = validate_example(ex)
    return ex if ok else None


# ── 오케스트레이션 ───────────────────────────────────────────────
# gpt-4o-mini 단가 (2026 기준, $/1M tokens)
_PRICE_IN, _PRICE_OUT = 0.15, 0.60


def distill(n: int, *, sources: list[str], model: str, concurrency: int,
            min_len: int, max_len: int, seed: int, max_cost: float,
            base_url: str | None = None, key_env: str = "OPENAI_API_KEY",
            commit_every: int = 200) -> dict:
    from openai import OpenAI
    # fail-fast: 느린/과부하 provider 에 worker 가 물리지 않게 timeout 짧게 + 재시도 제한.
    # 실패분은 DB 미적재 → resume 시 재시도되므로 손실 없음.
    client = OpenAI(api_key=_load_key(key_env), base_url=base_url, max_retries=3, timeout=25)
    conn = db.connect()

    sents = candidate_sentences(conn, sources, n, min_len=min_len, max_len=max_len, seed=seed)
    print(f"[증류] teacher={model} ({base_url or 'openai'}) 후보 {len(sents):,} 문장 (concurrency={concurrency})")

    lock = threading.Lock()
    stat = {"done": 0, "inserted": 0, "entities": 0, "errors": 0, "tok_in": 0, "tok_out": 0}
    pending: list[dict] = []

    def _work(sent: str):
        ents, usage = call_teacher(client, model, sent)
        return sent, ents, usage

    t0 = time.time()
    with ThreadPoolExecutor(max_workers=concurrency) as ex:
        futures = {ex.submit(_work, s): s for s in sents}
        for fut in as_completed(futures):
            try:
                sent, ents, usage = fut.result()
            except Exception as exc:  # noqa: BLE001 — teacher 에러 한 건이 전체 막지 않게
                with lock:
                    stat["errors"] += 1
                if stat["errors"] <= 3:
                    print(f"  ! teacher 에러: {str(exc)[:80]}")
                continue
            example = to_example(sent, ents)
            with lock:
                stat["done"] += 1
                stat["tok_in"] += usage["in"]; stat["tok_out"] += usage["out"]
                if example is not None:
                    pending.append(example)
                    stat["entities"] += count_entities(example["label_names"])
                if len(pending) >= commit_every:
                    res = db.insert_examples(conn, "distill_silver",
                                             f"silver-distilled-{model} (teacher relabel)",
                                             pending, split_hint="train")
                    stat["inserted"] += res["n_inserted"]
                    pending.clear()
                cost = stat["tok_in"] / 1e6 * _PRICE_IN + stat["tok_out"] / 1e6 * _PRICE_OUT
                if stat["done"] % 200 == 0:
                    rate = stat["done"] / max(time.time() - t0, 1e-9)
                    print(f"  {stat['done']:>6,}/{len(sents):,}  ins={stat['inserted']:>6,}  "
                          f"ent={stat['entities']:>6,}  ${cost:.2f}  {rate:.1f}/s")
                if max_cost and cost >= max_cost:
                    print(f"  ⚠️ 비용 상한 ${max_cost} 도달 — 남은 작업 취소")
                    for f in futures:
                        f.cancel()
                    break
    # 잔여 flush
    if pending:
        res = db.insert_examples(conn, "distill_silver",
                                 f"silver-distilled-{model} (teacher relabel)",
                                 pending, split_hint="train")
        stat["inserted"] += res["n_inserted"]
    conn.commit()
    stat["cost"] = stat["tok_in"] / 1e6 * _PRICE_IN + stat["tok_out"] / 1e6 * _PRICE_OUT
    conn.close()
    return stat


def dry_run(n: int, *, sources: list[str], min_len: int, max_len: int, seed: int) -> None:
    conn = db.connect()
    sents = candidate_sentences(conn, sources, n, min_len=min_len, max_len=max_len, seed=seed)
    conn.close()
    # 비용 추정 (문장 ~ 입력 80tok + 시스템프롬프트 분할상환 + 출력 ~60tok)
    est_in = len(sents) * (len(_SYSTEM_PROMPT) // 2 + 60)
    est_out = len(sents) * 60
    cost = est_in / 1e6 * _PRICE_IN + est_out / 1e6 * _PRICE_OUT
    print(f"=== DRY-RUN (API 0) ===")
    print(f"  후보 문장: {len(sents):,}  (소스 {sources})")
    print(f"  예상 비용 (gpt-4o-mini): ~${cost:.2f}")
    print(f"  샘플 5:")
    for s in sents[:5]:
        print(f"    · {s[:70]}")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50000, help="증류할 문장 수 (silver 목표)")
    ap.add_argument("--sources", default=",".join(DEFAULT_SOURCES))
    ap.add_argument("--provider", default="openai", help=f"teacher 프로바이더 {list(PROVIDERS)}")
    ap.add_argument("--model", default=None, help="프리셋 모델 override (예: deepseek/deepseek-chat)")
    ap.add_argument("--base-url", default=None, help="프리셋 base_url override")
    ap.add_argument("--concurrency", type=int, default=6)
    ap.add_argument("--min-len", type=int, default=15)
    ap.add_argument("--max-len", type=int, default=160)
    ap.add_argument("--seed", type=int, default=20260605)
    ap.add_argument("--max-cost", type=float, default=15.0, help="USD 상한(안전망, OpenAI 단가 기준 추정)")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--resume", action="store_true", help="(자동) DB content_hash 로 이미 resume됨")
    args = ap.parse_args()
    sources = [s.strip() for s in args.sources.split(",") if s.strip()]

    if args.dry_run:
        dry_run(args.n, sources=sources, min_len=args.min_len, max_len=args.max_len, seed=args.seed)
        return

    prov = PROVIDERS.get(args.provider)
    if prov is None:
        raise SystemExit(f"알 수 없는 provider: {args.provider} (선택: {list(PROVIDERS)})")
    base_url = args.base_url or prov["base_url"]
    key_env = prov["key_env"]
    model = args.model or prov["model"]

    stat = distill(args.n, sources=sources, model=model, concurrency=args.concurrency,
                   min_len=args.min_len, max_len=args.max_len, seed=args.seed, max_cost=args.max_cost,
                   base_url=base_url, key_env=key_env)
    print(f"\n=== 증류 완료 ===")
    print(f"  처리: {stat['done']:,}  적재(silver): {stat['inserted']:,}  엔티티: {stat['entities']:,}")
    print(f"  에러: {stat['errors']}  토큰 in/out: {stat['tok_in']:,}/{stat['tok_out']:,}")
    print(f"  💰 비용: ${stat['cost']:.2f}")
    print(f"\n  다음: source_ablation.py 로 silver 의 KLUE val 영향 검증 후 train_v4 투입.")


if __name__ == "__main__":
    main()
