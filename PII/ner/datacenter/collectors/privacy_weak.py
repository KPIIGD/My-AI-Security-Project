"""Collector (Phase B weak): scvcoder korean-privacy-law-corpus — 개인정보 상담/질의응답.

jsonl 의 body 필드(개인정보 처리 상담 본문 전체) → weak label. 개인정보 도메인이라
PII 문맥 풍부 (의료/금융/영상정보 등 텍스트형 PII 타겟).
"""
from __future__ import annotations

import glob
import json
from pathlib import Path

from ._text_weak import weak_label_texts

_DIR = (Path(__file__).resolve().parents[2] / "data" / "external" / "huggingface"
        / "scvcoder__korean-privacy-law-corpus")

META = {"id": "privacy_weak", "kind": "weak_examples",
        "license": "scvcoder/HF 개인정보 (PSEUDO 검수필요)",
        "entities": ["ORG", "ADDRESS", "DISEASE", "MEDICAL_PROC", "MEDICATION"],
        "note": "개인정보 상담/질의응답 본문전체 weak"}


def collect(limit: int = 0) -> dict:
    texts: list[str] = []
    for fp in glob.glob(str(_DIR / "*.jsonl")):
        with open(fp, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                body = obj.get("body") or obj.get("text") or ""
                if body:
                    texts.append(body)
                if limit and len(texts) >= limit:
                    break
        if limit and len(texts) >= limit:
            break
    return {"kind": "weak_examples", "license": META["license"],
            "examples": weak_label_texts(texts, min_len=20)}
