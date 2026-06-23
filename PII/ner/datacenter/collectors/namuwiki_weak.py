"""Collector (Phase B weak): heegyu 나무위키 문장 3,801만 — sentence (대량 cap).

iter_batches 로 스트리밍(2.3GB 통째 로드 회피). 대중문화/인물 인명·기관 풍부.
"""
from __future__ import annotations
from pathlib import Path
from ._text_weak import weak_label_texts

_PARQUET = Path(__file__).resolve().parents[2] / "data" / "external" / "huggingface" / "heegyu__namuwiki-sentences" / "namuwiki_20210301_sents.parquet"
META = {"id": "namuwiki_weak", "kind": "weak_examples", "license": "나무위키 CC-BY-NC-SA (PSEUDO 검수필요)",
        "entities": ["NAME", "ORG", "ADDRESS"], "note": "나무위키 문장 weak (스트리밍 cap)"}
_CAP = 800000

def collect(limit: int = 0) -> dict:
    import pyarrow.parquet as pq
    cap = limit or _CAP
    texts = []
    pf = pq.ParquetFile(str(_PARQUET))
    for batch in pf.iter_batches(batch_size=10000, columns=["sentence"]):
        for v in batch.column("sentence").to_pylist():
            if v:
                texts.append(str(v))
            if len(texts) >= cap:
                break
        if len(texts) >= cap:
            break
    return {"kind": "weak_examples", "license": META["license"], "examples": weak_label_texts(texts, min_len=15)}
