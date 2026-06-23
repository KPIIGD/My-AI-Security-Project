"""Collector (Phase B weak): lcw99 위키피디아 한국어 — 기사 본문 전체.

7 parquet 샤드, text=기사 본문. 인명/기관/지명 폭발 = 엔티티 다양성 최고 소스.
NAME/ORG/ADDRESS 가제티어로 weak label.
"""
from __future__ import annotations
import glob
from pathlib import Path
from ._text_weak import weak_label_texts

_DIR = Path(__file__).resolve().parents[2] / "data" / "external" / "huggingface" / "lcw99__wikipedia-korean-20240501" / "data"
META = {"id": "wiki_weak", "kind": "weak_examples", "license": "위키피디아 CC-BY-SA (PSEUDO 검수필요)",
        "entities": ["NAME", "ORG", "ADDRESS", "DISEASE"], "note": "위키 본문전체 weak — 엔티티 다양성"}
_CAP = 600000

def collect(limit: int = 0) -> dict:
    import pyarrow.parquet as pq
    cap = limit or _CAP
    texts = []
    for fp in sorted(glob.glob(str(_DIR / "*.parquet"))):
        t = pq.read_table(fp, columns=["text"])
        for v in t.column("text").to_pylist():
            s = v if isinstance(v, str) else (" ".join(v) if isinstance(v, list) else str(v))
            if s:
                texts.append(s[:8000])
            if len(texts) >= cap:
                break
        if len(texts) >= cap:
            break
    return {"kind": "weak_examples", "license": META["license"], "examples": weak_label_texts(texts, min_len=40)}
