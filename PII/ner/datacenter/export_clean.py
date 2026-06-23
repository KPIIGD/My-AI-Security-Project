"""누설-안전 학습 후보셋 export.

ner_examples 에서:
  1. 라이선스 필터 (기본 CC-BY-SA-4.0 만 = 졸업 공개 안전)
  2. 누설 문장 제거 (KLUE test 와 겹치는 content_hash 제외 — 평가 정직성)
→ data/datacenter_clean_candidate.json (data_prep 포맷, 학습 직접 투입 가능)

⚠️ 이건 "후보셋" — 학습 투입 전 소스 1개씩 고정 KLUE val ablation 필요 (v2 교훈).

사용:
  python datacenter/export_clean.py
  python datacenter/export_clean.py --licenses CC-BY-SA-4.0 "AIHub-derived (재배포 확인필요)"
"""
from __future__ import annotations

import argparse
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import db  # noqa: E402
from leakage_gate import _eval_hashes  # noqa: E402

OUT = Path(__file__).resolve().parent.parent / "data" / "datacenter_clean_candidate.json"


def _leaked_hashes(conn: sqlite3.Connection) -> set[str]:
    eval_hashes = _eval_hashes()
    rows = conn.execute("SELECT content_hash FROM ner_examples").fetchall()
    return {h for (h,) in rows if h in eval_hashes}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--licenses", nargs="*", default=["CC-BY-SA-4.0"],
                    help="포함할 라이선스 (기본 CC-BY-SA-4.0 만 = 공개 안전)")
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    conn = db.connect()
    leaked = _leaked_hashes(conn)
    out_path = Path(args.out)
    n = db.export_training_json(conn, out_path, licenses=args.licenses, exclude_hashes=leaked)

    total = conn.execute("SELECT COUNT(*) FROM ner_examples").fetchone()[0]
    print(f"=== 누설-안전 export ===")
    print(f"  전체 적재:        {total:,}")
    print(f"  라이선스 필터:     {args.licenses}")
    print(f"  누설 제외:        {len(leaked)}")
    print(f"  → 깨끗한 후보셋:   {n:,}  →  {out_path}")
    print(f"\n  ⚠️ 학습 투입 전 소스 1개씩 고정 KLUE val ablation 필수 (v2 교훈).")


if __name__ == "__main__":
    main()
