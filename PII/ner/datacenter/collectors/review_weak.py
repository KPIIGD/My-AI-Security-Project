"""Collector (Phase B weak): jwengr DACON 리뷰 — sentence (구어체).

리뷰 구어체 문장. 스타일 다양성(문어체 위주 코퍼스 보완). noisy 쌍은 정규화용.
"""
from __future__ import annotations
import glob
from pathlib import Path
from ._text_weak import weak_label_texts

_DIR = Path(__file__).resolve().parents[2] / "data" / "external" / "huggingface" / "jwengr__DACON-Korean-Review-Obfuscation" / "data"
META = {"id": "review_weak", "kind": "weak_examples", "license": "jwengr/HF 리뷰 (PSEUDO 검수필요)",
        "entities": ["ORG", "NAME"], "note": "리뷰 구어체 weak — 스타일 다양성"}

def collect(limit: int = 0) -> dict:
    import pyarrow.parquet as pq
    texts = []
    for fp in sorted(glob.glob(str(_DIR / "*.parquet"))):
        t = pq.read_table(fp)
        col = "sentence" if "sentence" in t.column_names else t.column_names[0]
        for v in t.column(col).to_pylist():
            if v:
                texts.append(str(v))
            if limit and len(texts) >= limit:
                break
    return {"kind": "weak_examples", "license": META["license"], "examples": weak_label_texts(texts, min_len=15)}
