"""누설 게이트 — 적재된 example 이 외부 평가셋(KLUE test)과 겹치는지 검사.

왜 NER 전용으로 꼭 필요한가 (CLAUDE.md §4.1):
  corpus4everyone 등은 KLUE 파생이다. train 에 KLUE val/test 문장이 섞이면
  "KLUE 로 평가" 가 누설된 점수가 된다 (외부 transfer 환상). v2 실패의 사촌.

방식: ner_datacenter.db 의 모든 문장 content_hash ∩ KLUE test 문장 content_hash.
  KLUE test 는 이미 로컬에 있는 data/pii_ner_v4_full.json 의 klue_test 사용 (네트워크 X).

사용:
  python datacenter/leakage_gate.py
  → 겹치는 문장 수 + 소스별 분해 출력. 0 이어야 안전.
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from db import DB_PATH  # noqa: E402
from schema import content_hash  # noqa: E402

EVAL_JSON = Path(__file__).resolve().parent.parent / "data" / "pii_ner_v4_full.json"
EVAL_SPLIT = "klue_test"


def _eval_hashes() -> set[str]:
    if not EVAL_JSON.exists():
        raise FileNotFoundError(f"평가셋 없음: {EVAL_JSON} (v4 데이터셋 먼저 생성)")
    data = json.loads(EVAL_JSON.read_text(encoding="utf-8"))
    rows = data.get(EVAL_SPLIT, [])
    return {content_hash(r["sentence"]) for r in rows if r.get("sentence")}


def run() -> dict:
    eval_hashes = _eval_hashes()
    conn = sqlite3.connect(str(DB_PATH))
    rows = conn.execute("SELECT content_hash, source, sentence FROM ner_examples").fetchall()
    conn.close()

    leaks_by_source: dict[str, int] = {}
    examples: list[str] = []
    for chash, source, sentence in rows:
        if chash in eval_hashes:
            leaks_by_source[source] = leaks_by_source.get(source, 0) + 1
            if len(examples) < 5:
                examples.append(f"[{source}] {sentence[:60]}")

    total_leaks = sum(leaks_by_source.values())
    print(f"=== 누설 게이트 ({EVAL_SPLIT} {len(eval_hashes):,} 문장 대비) ===")
    print(f"  적재 문장: {len(rows):,}")
    print(f"  누설(KLUE test 와 겹침): {total_leaks:,}")
    if leaks_by_source:
        for source, n in sorted(leaks_by_source.items(), key=lambda x: -x[1]):
            print(f"    - {source:20} {n:>6,}")
        print("  샘플:")
        for ex in examples:
            print(f"    · {ex}")
        print("\n  ⚠️ 누설 발견 — 이 문장들은 학습 투입 전 제거해야 평가가 정직함.")
    else:
        print("  ✅ 누설 0 — KLUE test 와 겹치는 문장 없음.")

    return {"eval_size": len(eval_hashes), "loaded": len(rows),
            "total_leaks": total_leaks, "by_source": leaks_by_source}


if __name__ == "__main__":
    run()
