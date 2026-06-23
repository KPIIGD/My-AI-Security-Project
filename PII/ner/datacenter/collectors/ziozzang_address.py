"""Collector: ziozzang/korean_address_en-ko (HF, gil.json) — ADDRESS 가제티어.

136,539 도로명 ({EN, KO}). KO(한글 도로명)만 ADDRESS 풀로. 현재 합성이
행정구역 hierarchy만 쓰는데 도로명을 추가해 ADDRESS 슬롯 다양화.
라벨 문장 아님 → gazetteers 테이블.
"""
from __future__ import annotations

import json
from pathlib import Path

_GIL = (Path(__file__).resolve().parents[2] / "data" / "external" / "huggingface"
        / "ziozzang__korean_address_en-ko" / "gil.json")

META = {
    "id": "ziozzang_address",
    "kind": "gazetteer",
    "license": "ziozzang/HF (도로명=공공데이터 파생)",
    "entities": ["ADDRESS"],
    "note": "도로명 풀 — 합성 ADDRESS 슬롯 다양화",
}


def collect(limit: int = 0) -> dict:
    if not _GIL.exists():
        raise FileNotFoundError(f"gil.json 없음: {_GIL}")
    rows = json.loads(_GIL.read_text(encoding="utf-8"))
    values = [r.get("KO", "").strip() for r in rows if r.get("KO")]
    if limit:
        values = values[:limit]
    return {
        "kind": "gazetteer",
        "license": META["license"],
        "entity_type": "ADDRESS",
        "values": values,
    }
