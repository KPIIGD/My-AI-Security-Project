"""Collector (Phase B weak): nayohan 141_korean_multi_session_dialogue — 페르소나 대화 76k.

session1/session2 대화 텍스트 → weak label. 페르소나 대화라 인명/지역/소속 문맥 포함.
"""
from __future__ import annotations

from pathlib import Path

from ._text_weak import weak_label_texts

_PARQUET = (Path(__file__).resolve().parents[2] / "data" / "external" / "huggingface"
            / "nayohan__141_korean_multi_session_dialogue" / "data" / "train-00000-of-00001.parquet")

META = {"id": "dialogue_weak", "kind": "weak_examples",
        "license": "nayohan/HF dialogue (PSEUDO 검수필요)",
        "entities": ["ORG", "ADDRESS", "DISEASE", "MEDICAL_PROC"],
        "note": "페르소나 대화 본문 weak"}

_CAP = 5000


def _flatten(val) -> str:
    if val is None:
        return ""
    if isinstance(val, (list, tuple)):
        return " ".join(_flatten(x) for x in val)
    if isinstance(val, dict):
        return " ".join(_flatten(v) for v in val.values())
    return str(val)


def collect(limit: int = 0) -> dict:
    import pyarrow.parquet as pq

    if not _PARQUET.exists():
        raise FileNotFoundError(f"없음: {_PARQUET}")
    cap = limit or _CAP
    table = pq.read_table(str(_PARQUET))
    cols = [c for c in ("session1", "session2") if c in table.column_names]
    data = {c: table.column(c).to_pylist() for c in cols}
    texts: list[str] = []
    for i in range(table.num_rows):
        merged = " ".join(_flatten(data[c][i]) for c in cols).strip()
        if merged:
            texts.append(merged)
        if len(texts) >= cap:
            break
    return {"kind": "weak_examples", "license": META["license"],
            "examples": weak_label_texts(texts, min_len=20)}
