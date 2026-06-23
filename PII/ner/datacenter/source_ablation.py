"""소스 pre-flight 게이트 — GPU 쓰기 전 "이 소스가 뭘 더해주나" 로컬 리포트.

왜 (철학 뒤집기의 실행 도구):
  NER 은 "전부 다" 가 독(v2). 새 소스는 비싼 KLUE val ablation(GPU ~$0.17/회) 으로
  검증해야 하는데, 그 전에 **로컬에서 공짜로** "GPU 돌릴 가치 있나" 를 거른다.

각 소스별 리포트:
  - n_examples (dedup 후 실제 기여)
  - entity 분포 (NAME/ADDRESS/ORG) — ⭐ ORG 기여가 v4 목표
  - 누설 (KLUE test 와 겹침) — 있으면 학습 투입 전 제거 필요
  - license — 공개 가능 여부

사용:
  python datacenter/source_ablation.py
"""
from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from db import DB_PATH  # noqa: E402
from leakage_gate import _eval_hashes  # noqa: E402


def _entity_counts(label_names: list[str]) -> dict:
    out = {"NAME": 0, "ADDRESS": 0, "ORG": 0}
    for label in label_names:
        if label.startswith("B-"):
            etype = label[2:]
            if etype in out:
                out[etype] += 1
    return out


def run() -> None:
    eval_hashes = _eval_hashes()
    conn = sqlite3.connect(str(DB_PATH))
    sources = [r[0] for r in conn.execute(
        "SELECT DISTINCT source FROM ner_examples ORDER BY source").fetchall()]

    print(f"=== 소스 pre-flight 게이트 (KLUE test {len(eval_hashes):,} 대비) ===\n")
    print(f"{'source':22}{'문장':>8}{'NAME':>8}{'ADDR':>8}{'ORG':>8}{'누설':>7}  license")
    print("-" * 90)
    for src in sources:
        rows = conn.execute(
            "SELECT content_hash, label_names_json, license FROM ner_examples WHERE source=?",
            (src,)).fetchall()
        totals = {"NAME": 0, "ADDRESS": 0, "ORG": 0}
        leaks = 0
        license = ""
        for chash, labs_json, lic in rows:
            license = lic
            for k, v in _entity_counts(json.loads(labs_json)).items():
                totals[k] += v
            if chash in eval_hashes:
                leaks += 1
        flag = " ⚠️" if leaks else ""
        print(f"{src:22}{len(rows):>8,}{totals['NAME']:>8,}{totals['ADDRESS']:>8,}"
              f"{totals['ORG']:>8,}{leaks:>7,}{flag}  {license}")

    print("\n판단 가이드:")
    print("  · ORG 기여 큰 소스 = v4 ORG 보강 1순위 (단, 누설 0 + 라이선스 확인)")
    print("  · 누설>0 = 학습 투입 전 제거 (KLUE 평가 정직성)")
    print("  · 다음: 소스 1개만 base 에 추가 → 고정 KLUE val ablation (train_v4 + KlueAbortCallback)")
    conn.close()


if __name__ == "__main__":
    run()
