"""Collector: NAME 가제티어 — gold NER 의 NAME 라벨 span 추출 + 성씨 seed.

상용급 NER 갭 메우기: 지금 ORG/ADDRESS 가제티어만 있고 NAME 풀이 없어
weak-labeling 이 인명을 못 잡음. 이미 흡수한 gold(corpus4ev/aihub/kimmeoungjun)의
B-NAME..I-NAME span 을 복원 → 실제 한국어 인명 사전. + 한국 성씨 seed.
"""
from __future__ import annotations

import json
import sqlite3
from pathlib import Path

_DB = Path(__file__).resolve().parents[1] / "ner_datacenter.db"

# 한국 주요 성씨 (weak-labeling 성씨 단서)
SURNAME_SEED = {
    "김", "이", "박", "최", "정", "강", "조", "윤", "장", "임", "한", "오", "서", "신",
    "권", "황", "안", "송", "류", "전", "홍", "고", "문", "양", "손", "배", "백", "허",
    "유", "남", "심", "노", "하", "곽", "성", "차", "주", "우", "구", "원", "탁", "민",
}

META = {
    "id": "name_gazetteer",
    "kind": "gazetteer",
    "license": "derived from gold NER (NAME span)",
    "entities": ["NAME"],
    "note": "gold NAME span 추출 + 성씨 seed — 상용급 NAME 풀",
}


# 흔한 조사 — 단어단위 소스 오염 보정(끝 조사 제거)
_JOSA = ("으로서", "으로써", "이라고", "라고", "에서", "에게", "께서", "으로", "이라",
         "은", "는", "이", "가", "을", "를", "의", "도", "에", "와", "과", "로", "만",
         "께", "야", "아", "랑", "님")


def _strip_josa(name: str) -> str:
    for j in _JOSA:  # 긴 것부터(정렬됨)
        if len(name) - len(j) >= 2 and name.endswith(j):
            return name[: -len(j)]
    return name


def _extract_names(conn: sqlite3.Connection) -> set[str]:
    names: set[str] = set()
    # ⚠️ kimmeoungjun(단어단위 조사오염) 제외 — char-level 깨끗한 소스만
    cur = conn.execute(
        "SELECT tokens_json, label_names_json FROM ner_examples WHERE source != 'kimmeoungjun_ner'")
    for toks_json, labs_json in cur:
        toks = json.loads(toks_json)
        labs = json.loads(labs_json)
        cur_chars: list[str] = []
        for t, l in zip(toks, labs):
            if l == "B-NAME":
                if cur_chars:
                    names.add("".join(cur_chars))
                cur_chars = [t]
            elif l == "I-NAME" and cur_chars:
                cur_chars.append(t)
            else:
                if cur_chars:
                    names.add("".join(cur_chars))
                    cur_chars = []
        if cur_chars:
            names.add("".join(cur_chars))
    # 조사 제거 + 2~5자 한글만 (잡음 제거)
    cleaned = {_strip_josa(n.strip()) for n in names}
    return {
        n for n in cleaned
        if 2 <= len(n) <= 5 and all("가" <= c <= "힣" for c in n)
    }


def collect(limit: int = 0) -> dict:
    values: set[str] = set(SURNAME_SEED)
    if _DB.exists():
        conn = sqlite3.connect(str(_DB))
        values |= _extract_names(conn)
        conn.close()
    out = sorted(values)
    if limit:
        out = out[:limit]
    return {
        "kind": "gazetteer",
        "license": META["license"],
        "entity_type": "NAME",
        "values": out,
    }
