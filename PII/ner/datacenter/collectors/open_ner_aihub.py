"""Collector: datasciathlete/open-ner-english-aihub-korean (HF, 로컬 parquet).

119k. 포맷 = {text, entities:[{entity_type, spans:[[s,e)...]}]}. span=char offset.
person→NAME / organization→ORG 만 매핑(나머지 product/work_of_art=O).
→ ORG/NAME recall 보강 (v4 ORG 약점 타겟).

⚠️ AIHub 파생 → GitHub 공개 시 재배포 라이선스 확인 필요. license 태그로 분리해
   export 기본(CC-BY-SA만)에서 제외되게 함 (공개 안전).

🛠 정제 (검증 지적 2026-06-04, 실측 후 강화):
   이 데이터셋은 영어가 31% 섞인 'english-aihub-korean'. 실측 결과
   - location/address span 의 ~100% 가 영어 지명("United States","New York")
     또는 영어 주소("2039 GULF OF MEXICO DR")+쓰레기("value"). → ADDRESS 매핑 폐기.
   - person span 의 54% 가 비한글: placeholder("AAA"/"AAA1" 6500+), 보통명사
     ("patients"/"user"/"children"), 영어 인명. org span 의 51% 가 비한글.
   → 한국어 PII NER gold 이므로 NAME/ORG 는 **한글 포함 span 만** 채택.
     영어 인명/약어/placeholder 손실은 감수(precision 우선, v2 오염 방어).
     정제 후 aihub 기여 ≈ NAME 62k / ORG 94k (깨끗한 한국어).
"""
from __future__ import annotations

from pathlib import Path

from schema import LABEL2ID

_DATA = (Path(__file__).resolve().parents[2] / "data" / "external" / "huggingface"
         / "datasciathlete__open-ner-english-aihub-korean" / "data")

# AIHub entity_type → 우리 7-way BIO. 나머지(product/work of art/location/address 등)는 O.
# location/address 는 영어 지명·주소·쓰레기뿐이라 매핑 폐기(위 docstring 참조).
ENTITY_MAP = {
    "person": "NAME",
    "organization": "ORG",
}


def _keep_span(etype: str, span_text: str) -> bool:
    """한글 포함 span 만 채택 — 영어/placeholder(AAA·patients) 오염 차단.

    NAME/ORG 모두 한국어 PII gold 대상이라 한글 1자 이상 필수.
    """
    return any("가" <= c <= "힣" for c in span_text)

META = {
    "id": "open_ner_aihub",
    "kind": "examples",
    "license": "AIHub-derived (재배포 확인필요)",  # 공개 export 기본 제외
    "entities": ["NAME", "ORG"],
    "note": "AIHub 파생 — 라이선스 확인 전 공개 금지. ORG/NAME 보강용(한글 span만)",
}


def _to_example(text: str, entities: list[dict]) -> dict | None:
    chars = list(text)
    n = len(chars)
    if n == 0:
        return None
    label_names = ["O"] * n
    # 긴 span 먼저 (겹칠 때 큰 entity 우선). first-wins 로 충돌 회피.
    flat = []
    for ent in entities:
        etype = ENTITY_MAP.get(ent.get("entity_type", ""))
        if not etype:
            continue
        for span in ent.get("spans", []):
            if len(span) != 2:
                continue
            s, e = int(span[0]), int(span[1])
            if 0 <= s < e <= n and _keep_span(etype, "".join(chars[s:e])):
                flat.append((s, e, etype))
    for s, e, etype in sorted(flat, key=lambda x: (x[1] - x[0]), reverse=True):
        if any(label_names[i] != "O" for i in range(s, e)):
            continue  # 이미 라벨된 구간과 충돌 → 스킵 (first/longest wins)
        label_names[s] = f"B-{etype}"
        for i in range(s + 1, e):
            label_names[i] = f"I-{etype}"
    return {
        "tokens": chars,
        "labels": [LABEL2ID[l] for l in label_names],
        "label_names": label_names,
        "sentence": text,
        "source": "open_ner_aihub",
    }


def collect(limit: int = 0) -> dict:
    import pyarrow.parquet as pq

    fpath = _DATA / "train-00000-of-00001.parquet"
    if not fpath.exists():
        raise FileNotFoundError(f"open_ner_aihub 파일 없음: {fpath}")
    table = pq.read_table(str(fpath))
    texts = table.column("text").to_pylist()
    ents = table.column("entities").to_pylist()
    if limit:
        texts, ents = texts[:limit], ents[:limit]

    examples = []
    for text, entlist in zip(texts, ents):
        ex = _to_example(text or "", entlist or [])
        if ex is not None:
            examples.append(ex)
    return {
        "kind": "examples",
        "license": META["license"],
        "split_hint": "train",
        "examples": examples,
    }
