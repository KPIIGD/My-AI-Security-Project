"""Collector (Phase B weak): hcw0329 medical-korean-alpaca — 의료 Q&A 15k.

instruction/input/output 의 의료 답변 텍스트 → weak label (병명/시술/약물).
"""
from __future__ import annotations

from pathlib import Path

from ._text_weak import weak_label_texts

_PARQUET = (Path(__file__).resolve().parents[2] / "data" / "external" / "huggingface"
            / "hcw0329__medical-korean-alpaca" / "data" / "train-00000-of-00001.parquet")

META = {"id": "medical_qa_weak", "kind": "weak_examples",
        "license": "hcw0329/HF medical-alpaca (PSEUDO 검수필요)",
        "entities": ["DISEASE", "MEDICAL_PROC", "MEDICATION"],
        "note": "의료 Q&A 본문 weak"}


def collect(limit: int = 0) -> dict:
    import pyarrow.parquet as pq

    if not _PARQUET.exists():
        raise FileNotFoundError(f"없음: {_PARQUET}")
    table = pq.read_table(str(_PARQUET))
    cols = table.column_names
    texts: list[str] = []
    instr = table.column("instruction").to_pylist() if "instruction" in cols else []
    outp = table.column("output").to_pylist() if "output" in cols else []
    for i in range(table.num_rows):
        parts = [p for p in ((instr[i] if i < len(instr) else ""),
                             (outp[i] if i < len(outp) else "")) if p]
        if parts:
            texts.append(" ".join(parts))
        if limit and len(texts) >= limit:
            break
    return {"kind": "weak_examples", "license": META["license"],
            "examples": weak_label_texts(texts, min_len=20)}
