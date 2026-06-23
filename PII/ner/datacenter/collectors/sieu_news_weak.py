"""Collector (Phase B weak): sieu-n korean-newstext-dump — 뉴스 본문 대량.

txt(318M, 243만줄)를 스트리밍 — '제목:' 줄로 기사 구분. 기사 단위로 제목+내용+
단락 전체를 합쳐 본문 전체로 weak label. 대용량이라 cap(기본 10k 기사).
"""
from __future__ import annotations

from pathlib import Path

from ._text_weak import weak_label_texts

_TXT = (Path(__file__).resolve().parents[2] / "data" / "external" / "huggingface"
        / "sieu-n__korean-newstext-dump" / "train" / "new_format_data.txt")

META = {"id": "sieu_news_weak", "kind": "weak_examples",
        "license": "sieu-n/HF newstext-dump (PSEUDO 검수필요)",
        "entities": ["ORG", "ADDRESS", "DISEASE", "MEDICAL_PROC"],
        "note": "뉴스덤프 본문전체 weak (스트리밍, cap)"}

_CAP = 300000


def _articles(cap: int):
    """txt 스트리밍 → 기사 본문 전체 yield ('제목:' 으로 구분)."""
    buf: list[str] = []
    n = 0
    with open(_TXT, encoding="utf-8") as f:
        for line in f:
            s = line.strip()
            if s.startswith("제목:"):
                if buf:
                    yield "\n".join(buf)
                    n += 1
                    if n >= cap:
                        return
                buf = [s[3:].strip()]
            elif s.startswith("내용:"):
                buf.append(s[3:].strip())
            elif s:
                buf.append(s)
    if buf and n < cap:
        yield "\n".join(buf)


def collect(limit: int = 0) -> dict:
    if not _TXT.exists():
        raise FileNotFoundError(f"없음: {_TXT}")
    cap = limit or _CAP
    texts = [a for a in _articles(cap)]
    return {"kind": "weak_examples", "license": META["license"],
            "examples": weak_label_texts(texts, min_len=40)}
