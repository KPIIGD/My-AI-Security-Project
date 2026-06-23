"""v4 학습셋 조립 — 기존 v4 split + silver/synth/aihub 증강 (ablation용).

원칙(v2 방어):
  - 검증된 기존 split(val/test/klue_test) **그대로 고정** → 평가 비교 가능.
  - train 에만 새 소스 추가. 추가분이 eval split 과 겹치면 제외(누설 차단).
  - silver 는 negative(무엔티티) 과다라 서브샘플링(positive 다 + neg 일부).
  - --include 로 소스 on/off → ablation 변형(baseline/+silver/+synth/+all) 생성.

소스(ner_datacenter.db ner_examples, license 기준):
  silver = 'silver-distilled-%'  / synth = 'synthetic-conv-name%' / aihub = 'AIHub-derived%'

사용:
  python datacenter/assemble_trainset.py --include silver,synth          # 기본
  python datacenter/assemble_trainset.py --include ""                    # baseline(증강 0)
  python datacenter/assemble_trainset.py --include silver --out data/pii_ner_v4_1_silver.json
"""
from __future__ import annotations

import argparse
import json
import random
import sqlite3
import sys
from pathlib import Path

_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE))
from schema import content_hash  # noqa: E402

_DB = _HERE / "ner_datacenter.db"
_BASE = _HERE.parent / "data" / "pii_ner_v4_full.json"

LICENSE_LIKE = {
    "silver": "silver-distilled-%",
    "synth": "synthetic-conv-name%",
    "aihub": "AIHub-derived%",
}


def _examples_by_license(conn: sqlite3.Connection, like: str) -> list[dict]:
    rows = conn.execute(
        "SELECT tokens_json, labels_json, label_names_json, sentence, source "
        "FROM ner_examples WHERE license LIKE ?", (like,)).fetchall()
    out = []
    for tj, lj, lnj, sent, src in rows:
        out.append({
            "tokens": json.loads(tj), "labels": json.loads(lj),
            "label_names": json.loads(lnj), "sentence": sent, "source": src,
        })
    return out


def _n_entities(ex: dict) -> int:
    return sum(1 for l in ex["label_names"] if l.startswith("B-"))


def assemble(include: list[str], *, neg_per_pos: float, seed: int) -> dict:
    rng = random.Random(seed)
    base = json.loads(_BASE.read_text(encoding="utf-8"))

    # eval split 해시 = 누설 차단 + 기존 train 해시 = 중복 차단
    blocked = set()
    for split in ("val", "test", "klue_test"):
        for ex in base.get(split, []):
            blocked.add(content_hash(ex["sentence"]))
    train = list(base["train"])
    train_hashes = {content_hash(ex["sentence"]) for ex in train}

    conn = sqlite3.connect(str(_DB))
    added_stats: dict[str, dict] = {}
    for key in include:
        like = LICENSE_LIKE.get(key)
        if not like:
            print(f"  ⚠️ 알 수 없는 소스 '{key}' (선택: {list(LICENSE_LIKE)})")
            continue
        exs = _examples_by_license(conn, like)
        # silver: negative 서브샘플링 (positive 전부 + neg 일부)
        if key == "silver":
            pos = [e for e in exs if _n_entities(e) > 0]
            neg = [e for e in exs if _n_entities(e) == 0]
            rng.shuffle(neg)
            keep_neg = int(len(pos) * neg_per_pos)
            exs = pos + neg[:keep_neg]
            rng.shuffle(exs)
        # 누설/중복 제거
        kept = 0
        seen_ent = {"NAME": 0, "ADDRESS": 0, "ORG": 0}
        for ex in exs:
            h = content_hash(ex["sentence"])
            if h in blocked or h in train_hashes:
                continue
            train_hashes.add(h)
            train.append(ex)
            kept += 1
            for l in ex["label_names"]:
                if l.startswith("B-"):
                    seen_ent[l[2:]] = seen_ent.get(l[2:], 0) + 1
        added_stats[key] = {"문장": kept, **seen_ent}
    conn.close()

    rng.shuffle(train)
    out = dict(base)
    out["train"] = train
    out["meta"] = {**base.get("meta", {}), "augmented": include,
                   "base_train": len(base["train"]), "new_train": len(train)}
    return out, added_stats


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--include", default="silver,synth", help="쉼표구분 (silver,synth,aihub / 빈값=baseline)")
    ap.add_argument("--neg-per-pos", type=float, default=1.5, help="silver negative:positive 비율 상한")
    ap.add_argument("--seed", type=int, default=20260605)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()
    include = [s.strip() for s in args.include.split(",") if s.strip()]

    out, stats = assemble(include, neg_per_pos=args.neg_per_pos, seed=args.seed)
    tag = "_".join(include) if include else "baseline"
    out_path = Path(args.out) if args.out else (_HERE.parent / "data" / f"pii_ner_v4_1_{tag}.json")
    out_path.write_text(json.dumps(out, ensure_ascii=False), encoding="utf-8")

    print(f"=== v4 학습셋 조립 ({tag}) → {out_path.name} ===")
    print(f"  기존 train: {out['meta']['base_train']:,}  →  증강 train: {out['meta']['new_train']:,}")
    for key, s in stats.items():
        print(f"  + {key:8} 문장 {s['문장']:>6,}  (NAME {s.get('NAME',0):,} / ADDRESS {s.get('ADDRESS',0):,} / ORG {s.get('ORG',0):,})")
    print(f"  val/test/klue_test 고정: {len(out['val']):,}/{len(out['test']):,}/{len(out['klue_test']):,} (누설 차단됨)")
    print(f"\n  GPU ablation: baseline vs 이 셋으로 train_v4 → KLUE val 비교 (vast key 후).")


if __name__ == "__main__":
    main()
