"""평가셋(val/test/klue_test)을 독립 gold 파일로 export.

다른 세션/PC/가드레일 벤치마크용 — pii_ner_v4_full.json 의존 없이 이 폴더만 들고 가면 됨.
출력: eval_gold.jsonl  (각 줄: {id, split, sentence, spans:[{start,end,type}]})
  type = NAME/ADDRESS/ORG, start/end = char offset (sentence[start:end] == 개체).

사용: python export_eval_gold.py
"""
from __future__ import annotations

import json
from pathlib import Path

SRC = Path(r"C:\My-AI-Security-Project\PII\ner\data\pii_ner_v4_full.json")
OUT = Path(__file__).resolve().parent / "eval_gold.jsonl"
SPLITS = ("val", "test", "klue_test")


def _spans(ex: dict) -> list[dict]:
    """label_names(char-level BIO) → [{start,end,type}]. 토큰=list(sentence)라 idx=char offset."""
    labs = ex["label_names"]
    out, s, t = [], None, None
    for i, l in enumerate(labs):
        if l.startswith("B-"):
            if s is not None:
                out.append({"start": s, "end": i, "type": t})
            s, t = i, l[2:]
        elif l.startswith("I-") and s is not None and l[2:] == t:
            continue
        else:
            if s is not None:
                out.append({"start": s, "end": i, "type": t}); s = t = None
    if s is not None:
        out.append({"start": s, "end": len(labs), "type": t})
    return out


def main() -> None:
    if not SRC.exists():
        raise SystemExit(f"원본 없음: {SRC}")
    data = json.loads(SRC.read_text(encoding="utf-8"))
    n, n_pii = 0, 0
    with OUT.open("w", encoding="utf-8") as f:
        for split in SPLITS:
            for j, ex in enumerate(data.get(split, [])):
                sp = _spans(ex)
                f.write(json.dumps({"id": f"{split}-{j:05d}", "split": split,
                                    "sentence": ex["sentence"], "spans": sp},
                                   ensure_ascii=False) + "\n")
                n += 1
                n_pii += 1 if sp else 0
    print(f"=== eval gold export ===")
    print(f"  {n:,} 문장 (PII 있는 것 {n_pii:,}) → {OUT}")
    print(f"  splits: {', '.join(SPLITS)}")
    print(f"  → 이제 benchmark.py 가 이 파일을 읽음 (원본 의존 끊김).")


if __name__ == "__main__":
    main()
