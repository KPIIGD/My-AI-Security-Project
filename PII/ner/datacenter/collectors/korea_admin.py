"""Collector: korea_admin.json (cosmosfarm 행정구역) — ADDRESS 가제티어.

{data:[{시도:[구/군...]}]} → 시도 + 구/군 + "시도 구/군" 조합을 ADDRESS 풀로.
합성 ADDRESS 슬롯의 행정구역 hierarchy 다양화.
"""
from __future__ import annotations

import json
from pathlib import Path

_JSON = Path(__file__).resolve().parents[2] / "data" / "korea_admin.json"

META = {
    "id": "korea_admin",
    "kind": "gazetteer",
    "license": "public (cosmosfarm 행정구역)",
    "entities": ["ADDRESS"],
    "note": "행정구역 시도/구군 + 조합",
}


def collect(limit: int = 0) -> dict:
    if not _JSON.exists():
        raise FileNotFoundError(f"korea_admin.json 없음: {_JSON}")
    obj = json.loads(_JSON.read_text(encoding="utf-8"))
    values: set[str] = set()
    for entry in obj.get("data", []):
        for sido, guguns in entry.items():
            values.add(sido)
            for gugun in guguns:
                values.add(gugun)
                values.add(f"{sido} {gugun}")
    out = sorted(values)
    if limit:
        out = out[:limit]
    return {
        "kind": "gazetteer",
        "license": META["license"],
        "entity_type": "ADDRESS",
        "values": out,
    }
