"""Collector: daje/korean-address-voice-v2 (HF parquet) — ADDRESS 가제티어.

3,400 실제 전체주소(도로명+건물명+동/호). text 컬럼만(audio 무시).
v3 ADDRESS F1 0.692(중간) 보강 — 합성에 건물/동호 단위 실주소 다양화.
"""
from __future__ import annotations

from pathlib import Path

_DATA = (Path(__file__).resolve().parents[2] / "data" / "external" / "huggingface"
         / "daje__korean-address-voice-v2" / "data")

META = {
    "id": "daje_address",
    "kind": "gazetteer",
    "license": "daje/HF (음성주소 코퍼스)",
    "entities": ["ADDRESS"],
    "note": "실제 전체주소(도로명+건물+동/호) 3.4k",
}


def collect(limit: int = 0) -> dict:
    import pyarrow.parquet as pq

    values: list[str] = []
    for split in ("train", "test"):
        fpath = _DATA / f"{split}-00000-of-00001.parquet"
        if not fpath.exists():
            continue
        table = pq.read_table(str(fpath), columns=["text"])
        values.extend(t for t in table.column("text").to_pylist() if t)
    if limit:
        values = values[:limit]
    return {
        "kind": "gazetteer",
        "license": META["license"],
        "entity_type": "ADDRESS",
        "values": values,
    }
