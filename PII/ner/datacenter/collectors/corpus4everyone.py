"""Collector: datasciathlete/corpus4everyone-korean-NER (HF, 로컬 parquet).

117k char-level token+tag (PS/LC/OG → NAME/ADDRESS/ORG). Phase A 메인 소스.
⚠️ KLUE 파생 → 소스 간 dedup + KLUE val/test 누설 게이트 필수 (leakage_gate.py).

기존 학습 로더(scripts/data_prep_v4.load_corpus4everyone)를 재사용 →
학습 포맷과 100% 동일 보장 (재발명 X).
"""
from __future__ import annotations

import sys
from pathlib import Path

_SCRIPTS = Path(__file__).resolve().parents[2] / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

META = {
    "id": "corpus4everyone",
    "kind": "examples",
    "license": "CC-BY-SA-4.0",  # KLUE 파생 → KLUE 라이선스 상속 (공개 가능)
    "entities": ["NAME", "ADDRESS", "ORG"],
    "note": "KLUE 파생 — dedup/누설 게이트 필수",
}


def collect(limit: int = 0) -> dict:
    import data_prep_v4 as dp

    examples = dp.load_corpus4everyone(split="train", limit=limit)
    return {
        "kind": "examples",
        "license": META["license"],
        "split_hint": "train",
        "examples": examples,
    }
