"""Collector: KRX 상장사 ORG 풀 (resource/gazetteer).

org_krx.txt 2,765 상장사 → gazetteers(ORG). 합성 슬롯 다양화용
(v3 org_pool 24 → 2,795 확장의 데이터센터화). 라벨 문장이 아니라
ORG 이름 풀이므로 gazetteer 테이블에 들어간다.

기존 scripts/data_prep_v4.load_org_pool_v4 재사용.
"""
from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

META = {
    "id": "org_krx",
    "kind": "gazetteer",
    "license": "public (KRX 공시)",
    "entities": ["ORG"],
    "note": "상장사 ORG 풀 — 합성 슬롯 다양화",
}


def collect(limit: int = 0) -> dict:
    import data_prep_v4 as dp

    values = dp.load_org_pool_v4()
    if limit:
        values = values[:limit]
    return {
        "kind": "gazetteer",
        "license": META["license"],
        "entity_type": "ORG",
        "values": values,
    }
