"""Collector: kimmeoungjun/korean_ner (HF, train.json) — 90k, ⚠️단어단위 CoNLL.

PER→NAME / ORG→ORG / LOC→ADDRESS (MISC/DAT→O). 단어단위 BIO → char 변환.

🚨 v2 킬러 패턴(Naver 어절 = 단어단위 char변환 노이즈)과 동형. "이병헌이" 전체가
   NAME 으로 학습되는 조사오염 위험. → 격리 license 로 태깅해 export 기본 제외 +
   source_ablation 에서 경고. **반드시 단독 ablation 통과 후에만 학습 투입.**
   데이터센터=후보 금고 원칙: 모으되 게이트 통과 전엔 안 씀.
"""
from __future__ import annotations

import json
from pathlib import Path

from schema import LABEL2ID, validate_example

_JSON = (Path(__file__).resolve().parents[2] / "data" / "external" / "huggingface"
         / "kimmeoungjun__korean_ner" / "train.json")

TAG_MAP = {"PER": "NAME", "ORG": "ORG", "LOC": "ADDRESS"}  # MISC/DAT → O

META = {
    "id": "kimmeoungjun_ner",
    "kind": "examples",
    "license": "word-level (조사오염 위험·ablation 필수)",  # 격리 — export 기본 제외
    "entities": ["NAME", "ORG", "ADDRESS"],
    "note": "🚨 단어단위=v2 킬러 패턴. 단독 ablation 통과 전 학습 금지",
}


def _word_to_char(words: list[str], tags: list[str]) -> dict | None:
    chars: list[str] = []
    labels: list[str] = []
    for i, (word, tag) in enumerate(zip(words, tags)):
        if i > 0:  # 단어 사이 공백
            chars.append(" ")
            labels.append("O")
        bio, _, base = tag.partition("-")
        etype = TAG_MAP.get(base) if base else None
        for j, ch in enumerate(word):
            chars.append(ch)
            if etype is None:
                labels.append("O")
            elif bio == "B" and j == 0:
                labels.append(f"B-{etype}")
            else:
                labels.append(f"I-{etype}")
    sentence = "".join(chars)
    ex = {
        "tokens": chars,
        "labels": [LABEL2ID[l] for l in labels],
        "label_names": labels,
        "sentence": sentence,
        "source": "kimmeoungjun_ner",
    }
    ok, _ = validate_example(ex)
    return ex if ok else None


def collect(limit: int = 0) -> dict:
    if not _JSON.exists():
        raise FileNotFoundError(f"kimmeoungjun train.json 없음: {_JSON}")
    examples = []
    with open(_JSON, encoding="utf-8") as fp:
        for line in fp:
            line = line.strip()
            if not line:
                continue
            obj = json.loads(line)
            words, tags = obj.get("tokens", []), obj.get("ner_tags", [])
            if not words or len(words) != len(tags):
                continue
            ex = _word_to_char(words, tags)
            if ex is not None:
                examples.append(ex)
            if limit and len(examples) >= limit:
                break
    return {
        "kind": "examples",
        "license": META["license"],
        "split_hint": "train",
        "examples": examples,
    }
