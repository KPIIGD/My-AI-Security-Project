"""Collector (Phase B weak): 91veMe 지방자치 조례 36k — original (행정 문어체).

행정/법규 도메인. ORG(기관)/ADDRESS(관할) 풍부.
"""
from __future__ import annotations
import glob, csv
from pathlib import Path
from ._text_weak import weak_label_texts

_DIR = Path(__file__).resolve().parents[2] / "data" / "external" / "huggingface" / "91veMe4Plus-Project__korean_local_government_ordinances"
META = {"id": "gov_ordinance_weak", "kind": "weak_examples", "license": "91veMe/HF 조례 (PSEUDO 검수필요)",
        "entities": ["ORG", "ADDRESS"], "note": "행정 조례 문어체 weak"}
_CAP = 20000

def collect(limit: int = 0) -> dict:
    cap = limit or _CAP
    texts = []
    for fp in glob.glob(str(_DIR / "*.csv")):
        with open(fp, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                t = row.get("original") or ""
                if t:
                    texts.append(t)
                if len(texts) >= cap:
                    break
        if len(texts) >= cap:
            break
    return {"kind": "weak_examples", "license": META["license"], "examples": weak_label_texts(texts, min_len=20)}
