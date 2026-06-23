"""약한 라벨러 — 사전 + regex 로 본문에 자동 BIO 태깅 (Phase B).

⚠️ 약한(pseudo) 라벨이다. 정확하지 않다. weak_examples 트랙에만 저장되고
   gold ner_examples 와 안 섞인다. 검수 후에만 학습 후보로 승격.

알고리즘: 사전/regex 매칭 → 후보 span 수집 → 긴 것 우선 비중첩 배치 → char BIO.
char-level 토큰(=list(text))으로 corpus4everyone 포맷과 동일.
"""
from __future__ import annotations

import re


def _bad_ascii_boundary(text: str, s: int, e: int) -> bool:
    """ASCII 약어가 더 긴 단어의 부분일 때(예: 'ESG' 안의 'SG') 오탐 차단.

    한글 term 은 조사 인접("네이버는")이 정상이라 검사 안 함. ASCII term 만.
    """
    term = text[s:e]
    if not term.isascii() or not any(c.isalnum() for c in term):
        return False
    before = text[s - 1] if s > 0 else ""
    after = text[e] if e < len(text) else ""
    return before.isalnum() or after.isalnum()


def _is_hangul(c: str) -> bool:
    return "가" <= c <= "힣"  # 가~힣


# 인명 뒤에 자연스럽게 붙는 단음절 조사/호칭/서술격(첫 글자 기준).
# 이게 아닌 한글이 인명에 바로 이어지면 합성어(예: '정민수학원')로 보고 거부.
# '입'(입니다/입니까) '인'(인데/인가) 은 서술격조사 — 대화체 인명 recall 보존.
_NAME_FOLLOW_OK = set("은는이가을를의도에와과로만께야아랑님씨입인")


def _bad_korean_name_boundary(text: str, s: int, e: int) -> bool:
    """한글 인명 가제티어가 더 긴 한글 단어의 일부일 때 오탐 차단.

    검증 지적(2026-06-04): '정민수' 가 '정민수학원'(ORG) 안에서 NAME 으로 오탐.
    규칙: ① 앞 글자가 한글이면 거부(인명은 어절 시작). ② 뒤 글자가 한글인데
    조사/호칭(_NAME_FOLLOW_OK)이 아니면 합성어로 보고 거부('학'→거부, '가'→허용).
    공백·문장부호·ASCII 가 경계면 정상. 약한 라벨이라 precision 우선.
    """
    before = text[s - 1] if s > 0 else ""
    after = text[e] if e < len(text) else ""
    if before and _is_hangul(before):
        return True
    if after and _is_hangul(after) and after not in _NAME_FOLLOW_OK:
        return True
    return False


# Aho-Corasick 자동자 캐시 — 대량 weak-labeling 핵심(O(text), 패턴 수 무관).
# 수만 term gazetteer(NAME 2만+) 매칭이 통합 regex 대비 수십배 빠름.
try:
    import ahocorasick
    _HAS_AC = True
except ImportError:
    _HAS_AC = False

_AC_CACHE: dict[int, "object"] = {}


def _automaton(terms: set[str]):
    key = id(terms)
    if key in _AC_CACHE:
        return _AC_CACHE[key]
    A = ahocorasick.Automaton()
    for t in terms:
        t = t.strip()
        if len(t) >= 2:
            A.add_word(t, t)
    A.make_automaton() if len(A) else None
    auto = A if len(A) else None
    _AC_CACHE[key] = auto
    return auto


def _dict_spans(text: str, dictionaries: list[tuple[str, set[str]]]) -> list[tuple[int, int, str]]:
    spans: list[tuple[int, int, str]] = []
    for etype, terms in dictionaries:
        # NAME 은 한글 단어경계 가드 추가(합성어 오탐 차단). ORG/ADDRESS 는
        # 접미("은행"/"시") 인접이 정상이라 ASCII 가드만 유지.
        is_name = etype == "NAME"
        if _HAS_AC:
            auto = _automaton(terms)
            if auto is None:
                continue
            for end_idx, term in auto.iter(text):
                s = end_idx - len(term) + 1
                e = end_idx + 1
                if _bad_ascii_boundary(text, s, e):
                    continue
                if is_name and _bad_korean_name_boundary(text, s, e):
                    continue
                spans.append((s, e, etype))
        else:  # 폴백: term별 regex
            for term in terms:
                term = term.strip()
                if len(term) < 2:
                    continue
                for m in re.finditer(re.escape(term), text):
                    s, e = m.start(), m.end()
                    if _bad_ascii_boundary(text, s, e):
                        continue
                    if is_name and _bad_korean_name_boundary(text, s, e):
                        continue
                    spans.append((s, e, etype))
    return spans


def _regex_spans(text: str, regexes: list[tuple[str, re.Pattern]]) -> list[tuple[int, int, str]]:
    spans = []
    for etype, pattern in regexes:
        for m in pattern.finditer(text):
            spans.append((m.start(), m.end(), etype))
    return spans


def weak_label(
    text: str,
    dictionaries: list[tuple[str, set[str]]],
    regexes: list[tuple[str, re.Pattern]] | None = None,
) -> dict:
    """text → {tokens, label_names}. 비중첩 longest-first BIO."""
    chars = list(text)
    n = len(chars)
    label_names = ["O"] * n
    candidates = _dict_spans(text, dictionaries)
    if regexes:
        candidates += _regex_spans(text, regexes)
    # 긴 span 우선 (구체 entity 보호), first-wins 로 충돌 회피
    for s, e, etype in sorted(candidates, key=lambda x: (x[1] - x[0]), reverse=True):
        if s < 0 or e > n or s >= e:
            continue
        if any(label_names[i] != "O" for i in range(s, e)):
            continue
        label_names[s] = f"B-{etype}"
        for i in range(s + 1, e):
            label_names[i] = f"I-{etype}"
    return {"tokens": chars, "label_names": label_names}


# 공용 구조형 PII regex (익명화 텍스트엔 드물지만 포함)
STRUCTURED_REGEXES = [
    ("PHONE", re.compile(r"01[016789][-\s]?\d{3,4}[-\s]?\d{4}")),
    ("EMAIL", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")),
    ("RRN", re.compile(r"\d{6}[-\s]?[1-4]\d{6}")),
]
