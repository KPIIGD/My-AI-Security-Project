"""텍스트 코퍼스 → 약한 라벨 공유 헬퍼 (Phase B).

raw 텍스트 리스트를 받아 gazetteer(ORG/행정구역) + 의료사전(병명/시술/약물) +
구조형 regex(phone/email/RRN) 로 약한 BIO 라벨링. weak_examples 트랙(PSEUDO).

여러 텍스트 collector(뉴스/개인정보/의료Q&A/대화)가 공유. 사전은 한 번만 로드.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path

from ._weak_label import STRUCTURED_REGEXES, weak_label
from .ducut91_weak import DISEASE_SEED, MEDICAL_PROC_SEED, MEDICATION_SEED

_DB = Path(__file__).resolve().parents[1] / "ner_datacenter.db"


def _load_dictionaries() -> list[tuple[str, set]]:
    dicts: list[tuple[str, set]] = [
        ("DISEASE", DISEASE_SEED),
        ("MEDICAL_PROC", MEDICAL_PROC_SEED),
        ("MEDICATION", MEDICATION_SEED),
    ]
    if _DB.exists():
        conn = sqlite3.connect(str(_DB))
        org = {v for (v,) in conn.execute(
            "SELECT value FROM gazetteers WHERE entity_type='ORG'").fetchall() if len(v) >= 2}
        addr = {v for (v,) in conn.execute(
            "SELECT value FROM gazetteers WHERE entity_type='ADDRESS' AND source='korea_admin'"
        ).fetchall() if len(v) >= 2}
        # NAME 가제티어 (gold 추출) — 3자 이상만(2자 인명은 흔한 단어와 충돌 많아 제외)
        name = {v for (v,) in conn.execute(
            "SELECT value FROM gazetteers WHERE entity_type='NAME'").fetchall() if len(v) >= 3}
        conn.close()
        dicts = [("NAME", name), ("ORG", org), ("ADDRESS", addr)] + dicts
    return dicts


def weak_label_texts(texts: list[str], *, min_len: int = 20) -> list[dict]:
    """텍스트 리스트 → weak example 리스트 ({tokens,label_names,sentence})."""
    dictionaries = _load_dictionaries()
    out = []
    for text in texts:
        text = (text or "").strip()
        if len(text) < min_len:
            continue
        ex = weak_label(text, dictionaries, STRUCTURED_REGEXES)
        ex["sentence"] = text
        out.append(ex)
    return out
