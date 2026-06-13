"""in-domain 평가셋 후보 추출 — 사람 라벨링 대상 문장 모으기.

검증 지적(2026-06-04): "평가셋 도메인 불일치(KLUE 뉴스 vs 챗 PII)".
→ KLUE 뉴스 대신 **챗/대화 도메인** 문장을 모아 사람이 정답 라벨을 단다.

소스 (in-domain = 챗 PII):
  1. weak_examples 챗 도메인 (dialogue/safe_conv/review/privacy/medical_qa) 샘플
  2. 구조형 PII 합성 (synth_structured.py) — 여권/면허/카드/계좌 등
  (소설 등 공개문헌은 현실성용 소량만, 옵션)

게이트:
  - KLUE test 누설 제거 (leakage_gate 와 동일 content_hash 검사)
  - content_hash dedup
  - 길이 필터 (사람이 한 화면에 라벨 가능한 단위)

출력: candidates.jsonl — {id, sentence, source, draft_spans?(초벌), needs_human_label}
  draft_spans 는 weak 라벨러의 *초벌*(편의용). 사람이 반드시 검토/수정.

⚠️ 라벨 자체는 자동화 불가 — 사람(민우+양유상) 2인 독립 라벨 → reconcile.py.

사용:
  python eval_indomain/build_candidates.py --n-chat 400 --n-struct 150
"""
from __future__ import annotations

import argparse
import json
import random
import re
import sqlite3
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
_DC = _HERE.parent / "datacenter"
sys.path.insert(0, str(_DC))
sys.path.insert(0, str(_DC / "collectors"))

from schema import content_hash  # noqa: E402  (datacenter/schema.py)

import synth_structured  # noqa: E402  (eval_indomain/)

_DB = _DC / "ner_datacenter.db"
_EVAL_JSON = _HERE.parent / "data" / "pii_ner_v4_full.json"  # KLUE test 누설 검사용

# in-domain = 챗/대화/상담 도메인 (뉴스/위키 제외)
_CHAT_SOURCES = ["dialogue_weak", "safe_conv_weak", "review_weak", "privacy_weak", "medical_qa_weak"]

# 문장 분리: 문장부호 + 줄바꿈 + 파이썬 list-repr 경계('foo', 'bar')
_SENT_SPLIT = re.compile(r"(?<=[.!?。…])\s+|\n+|'\s*,\s*'|\"\s*,\s*\"")


def _klue_leak_hashes() -> set[str]:
    if not _EVAL_JSON.exists():
        print(f"  ⚠️ KLUE 평가셋 없음({_EVAL_JSON}) — 누설필터 생략", file=sys.stderr)
        return set()
    data = json.loads(_EVAL_JSON.read_text(encoding="utf-8"))
    return {content_hash(r["sentence"]) for r in data.get("klue_test", []) if r.get("sentence")}


def _sentences_from_weak(rng: random.Random, n: int, *, min_len: int, max_len: int) -> list[dict]:
    """챗 도메인 weak_examples 에서 문장 단위로 샘플 (긴 본문은 문장 분리)."""
    if not _DB.exists():
        print(f"  ⚠️ DB 없음({_DB}) — 챗 후보 생략", file=sys.stderr)
        return []
    conn = sqlite3.connect(str(_DB))
    placeholders = ",".join("?" * len(_CHAT_SOURCES))
    # 넉넉히 뽑아 문장 분리 후 길이필터 (각 소스 균형)
    rows = conn.execute(
        f"SELECT source, sentence FROM weak_examples WHERE source IN ({placeholders})",
        _CHAT_SOURCES,
    ).fetchall()
    conn.close()
    rng.shuffle(rows)
    out: list[dict] = []
    seen: set[str] = set()
    for source, sentence in rows:
        for sent in _SENT_SPLIT.split(sentence or ""):
            sent = sent.strip().strip("[]'\"")
            if not (min_len <= len(sent) <= max_len):
                continue
            h = content_hash(sent)
            if h in seen:
                continue
            seen.add(h)
            out.append({"sentence": sent, "source": source})
            break  # 문서당 1문장 (도메인 다양성)
        if len(out) >= n:
            break
    return out


def build(n_chat: int, n_struct: int, *, seed: int = 20260604,
          min_len: int = 15, max_len: int = 160) -> list[dict]:
    rng = random.Random(seed)
    leak = _klue_leak_hashes()

    chat = _sentences_from_weak(rng, n_chat, min_len=min_len, max_len=max_len)
    struct = synth_structured.generate(n_struct, seed=seed)

    candidates: list[dict] = []
    seen: set[str] = set()
    cid = 0

    def _add(sentence: str, source: str, draft_spans):
        nonlocal cid
        h = content_hash(sentence)
        if h in leak or h in seen:
            return
        seen.add(h)
        cid += 1
        candidates.append({
            "id": f"eval-{cid:04d}",
            "sentence": sentence,
            "source": source,
            "draft_spans": draft_spans,  # 초벌(검토 필수) 또는 [] / 합성은 정답
            "needs_human_label": source != "synth_structured",
        })

    for c in chat:
        _add(c["sentence"], c["source"], draft_spans=[])  # 챗은 사람이 라벨
    for s in struct:
        # 구조형 합성은 span 이 이미 정답 (사람 불필요) — NER 7-way 밖이라 별 트랙
        _add(s["sentence"], "synth_structured",
             draft_spans=[{**sp, "gold": True} for sp in s["spans"]])

    rng.shuffle(candidates)
    return candidates


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n-chat", type=int, default=400, help="챗 도메인 후보 문장 수")
    ap.add_argument("--n-struct", type=int, default=150, help="구조형 PII 합성 수")
    ap.add_argument("--seed", type=int, default=20260604)
    ap.add_argument("--out", default=str(_HERE / "candidates.jsonl"))
    args = ap.parse_args()

    cands = build(args.n_chat, args.n_struct, seed=args.seed)
    out_path = Path(args.out)
    with out_path.open("w", encoding="utf-8") as f:
        for c in cands:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")

    n_human = sum(1 for c in cands if c["needs_human_label"])
    by_src: dict[str, int] = {}
    for c in cands:
        by_src[c["source"]] = by_src.get(c["source"], 0) + 1
    print(f"=== in-domain 후보 {len(cands)} 건 → {out_path} ===")
    print(f"  사람 라벨 필요(챗): {n_human}  /  합성 정답(구조형): {len(cands) - n_human}")
    print(f"  소스별: {by_src}")
    print(f"\n  다음: make_annotation_sheets.py 로 2인 독립 라벨 시트 생성")


if __name__ == "__main__":
    main()
