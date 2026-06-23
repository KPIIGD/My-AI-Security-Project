"""Collector: 대화체 NAME 합성 gold — 가제티어 이름 × 대화 템플릿 → 완벽 BIO.

검증세션이 짚은 #1·#2 갭(대화체/구어체 NAME) 직격. 합성이라 라벨 100% 정확
(내가 이름 위치를 알고 박음) + 프라이버시 무관 + 한국 이름 분포 통제.
→ ner_examples(GOLD)에 들어감. license='synthetic-conv-name'로 태깅(ablation 권장).

받침 맞춘 조사(이/가, 은/는, 을/를, 와/과, 아/야)로 자연스러운 한국어.
"""
from __future__ import annotations

import random
import sqlite3
from pathlib import Path

from schema import LABEL2ID

_DB = Path(__file__).resolve().parents[1] / "ner_datacenter.db"
_SEED = 20260604  # 재현성(난수 고정)

# 성씨(이름 품질 필터 — 가제티어 잡음 제거: 성씨로 시작하는 3~4자만)
_SURNAMES = set("김이박최정강조윤장임한오서신권황안송류전홍고문양손배백허유남심노하곽성차주우구원탁민")

# 대화/구어 템플릿. {N}=이름. {조사}=받침 맞춤. 호칭형은 조사 불필요.
_TEMPLATES = [
    "안녕하세요 저 {N}입니다", "안녕하세요 {N}이라고 합니다", "저는 {N}인데요",
    "{N}예요", "제 이름은 {N}이에요", "{N}{이가} 누구예요?",
    "{N}{아야} 어디야?", "{N}{아야} 밥 먹었어?", "{N}{아야} 이것 좀 봐",
    "{N} 선배님 안녕하세요", "{N}씨 연락 부탁드려요", "{N}님 오셨어요?",
    "어제 {N}{이가} 그러는데", "{N}한테 전화왔어", "{N}{을를} 만났어",
    "{N} 형 어디 계세요", "{N} 누나가 도와줬어", "내 친구 {N} 소개할게",
    "{N} 부장님 회의 들어가셨어요", "팀장 {N}입니다", "{N} 고객님 맞으신가요?",
    "이번에 {N}씨가 입사했어요", "{N}쌤 수업 언제예요", "{N}{와과} 같이 갈게",
    "{N} 어머니께 안부 전해줘", "{N} 기자입니다", "담당자 {N}입니다",
    "{N}{이가} 추천한 식당이야", "{N} 사장님 통화 가능하세요?", "@{N} 카톡 확인해",
]


def _batchim(ch: str) -> bool:
    return "가" <= ch <= "힣" and (ord(ch) - 0xAC00) % 28 != 0


def _josa(name: str, with_b: str, without_b: str) -> str:
    return with_b if _batchim(name[-1]) else without_b


def _fill(template: str, name: str) -> str:
    s = template.replace("{이가}", _josa(name, "이", "가"))
    s = s.replace("{은는}", _josa(name, "은", "는"))
    s = s.replace("{을를}", _josa(name, "을", "를"))
    s = s.replace("{와과}", _josa(name, "과", "와"))
    s = s.replace("{아야}", _josa(name, "아", "야"))
    return s.replace("{N}", name)


def _to_example(template: str, name: str) -> dict | None:
    sentence = _fill(template, name)
    idx = sentence.find(name)
    if idx < 0:
        return None
    chars = list(sentence)
    labels = ["O"] * len(chars)
    labels[idx] = "B-NAME"
    for i in range(idx + 1, idx + len(name)):
        labels[i] = "I-NAME"
    return {
        "tokens": chars,
        "labels": [LABEL2ID[l] for l in labels],
        "label_names": labels,
        "sentence": sentence,
        "source": "synth_conv_name",
    }


META = {
    "id": "synth_conv_name",
    "kind": "examples",  # GOLD (라벨 정확)
    "license": "synthetic-conv-name (gold, ablation 권장)",
    "entities": ["NAME"],
    "note": "대화체 NAME 합성 — 검증세션 갭#1 직격",
}

_CAP = 40000


def _quality_names() -> list[str]:
    if not _DB.exists():
        return []
    conn = sqlite3.connect(str(_DB))
    rows = conn.execute(
        "SELECT value FROM gazetteers WHERE entity_type='NAME'").fetchall()
    conn.close()
    # 성씨로 시작하는 3~4자 = 현실적 한국 이름 (가제티어 잡음 필터)
    return [v for (v,) in rows if 3 <= len(v) <= 4 and v[0] in _SURNAMES]


def collect(limit: int = 0) -> dict:
    cap = limit or _CAP
    names = _quality_names()
    if not names:
        return {"kind": "examples", "license": META["license"], "split_hint": "train", "examples": []}
    rng = random.Random(_SEED)
    examples = []
    seen = set()
    attempts = 0
    while len(examples) < cap and attempts < cap * 4:
        attempts += 1
        name = rng.choice(names)
        tmpl = rng.choice(_TEMPLATES)
        ex = _to_example(tmpl, name)
        if ex is None or ex["sentence"] in seen:
            continue
        seen.add(ex["sentence"])
        examples.append(ex)
    return {"kind": "examples", "license": META["license"], "split_hint": "train", "examples": examples}
