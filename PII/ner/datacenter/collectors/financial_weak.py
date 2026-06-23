"""Collector (Phase B weak): alwaysgood 금융 코퍼스 (BOK/한경) — content.

금융 도메인 텍스트 (한국은행 용어/한경). 도메인 다양성.
"""
from __future__ import annotations
import glob, json
from pathlib import Path
from ._text_weak import weak_label_texts

_DIR = Path(__file__).resolve().parents[2] / "data" / "external" / "huggingface" / "alwaysgood__korean-financial-cpt"
META = {"id": "financial_weak", "kind": "weak_examples", "license": "alwaysgood/HF 금융 (PSEUDO 검수필요)",
        "entities": ["ORG", "ADDRESS", "NAME"], "note": "금융 도메인 텍스트 weak"}
_CAP = 20000

def collect(limit: int = 0) -> dict:
    cap = limit or _CAP
    texts = []
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
                c = obj.get("content") or obj.get("text") or ""
                if c:
                    texts.append(c[:8000])
                if len(texts) >= cap:
                    break
        if len(texts) >= cap:
            break
    return {"kind": "weak_examples", "license": META["license"], "examples": weak_label_texts(texts, min_len=30)}
