"""Collector (Phase B weak): 91veMe korean_news_corpus — 뉴스문어체 281,932.

original 컬럼(깨끗한 뉴스문장) → weak label. (obfuscated 쌍은 정규화 강건성용 별도)
본문 전체 = 문장 통째.
"""
from __future__ import annotations

import csv
import glob
from pathlib import Path

from ._text_weak import weak_label_texts

_DIR = (Path(__file__).resolve().parents[2] / "data" / "external" / "huggingface"
        / "91veMe4Plus-Project__korean_news_corpus")

META = {"id": "news91_weak", "kind": "weak_examples",
        "license": "91veMe/HF 뉴스코퍼스 (PSEUDO 검수필요)",
        "entities": ["ORG", "ADDRESS", "DISEASE", "MEDICAL_PROC"],
        "note": "뉴스문어체 281k weak — 본문전체"}

_CAP = 8000  # limit 0 시 상한 (전체 281k 는 과다 — 샘플)


def collect(limit: int = 0) -> dict:
    cap = limit or _CAP
    files = glob.glob(str(_DIR / "*.csv"))
    texts: list[str] = []
    for fp in files:
        with open(fp, encoding="utf-8") as f:
            for row in csv.DictReader(f):
                t = row.get("original") or ""
                if t:
                    texts.append(t)
                if len(texts) >= cap:
                    break
        if len(texts) >= cap:
            break
    return {"kind": "weak_examples", "license": META["license"],
            "examples": weak_label_texts(texts, min_len=15)}
