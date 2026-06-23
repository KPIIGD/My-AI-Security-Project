"""Collector (Phase B, PSEUDO): ducut91 의료/개인정보 분쟁조정 사례.

⭐ "본문 전체" 룰: 각 사례의 모든 텍스트 컬럼(case_summary/key_issues/
   resolution_method/detailed_outcome 등)을 통째로 concat → 본문 전체에 약한 라벨링.

타겟 = 텍스트형 PII(병명/시술/진료과) = 캡스톤 "68% 우회" 정조준. 단 NER 7-way 가
아니라 확장 태그라서, gold ner_examples 가 아니라 weak_examples 트랙에 PSEUDO 저장.
검수 + 스키마 확장 결정(사용자) 후에만 학습 승격.

사전은 ① 데이터 자체(medical_department 실값) + ② 병명/시술 SEED. SEED 는
출발점일 뿐 — 커버리지 부분적(약한 라벨의 본질). 검수로 보강.
"""
from __future__ import annotations

import csv
from pathlib import Path

from ._weak_label import STRUCTURED_REGEXES, weak_label

_HF = Path(__file__).resolve().parents[2] / "data" / "external" / "huggingface"
_CSVS = [
    _HF / "ducut91__korean-medical-dispute-mediation-cases" / "medical_dispute_mediation_cases.csv",
    _HF / "ducut91__korean-personal-info-dispute-mediation-cases" / "korean_personal_info_dispute_mediation_cases.csv",
]

# 병명 SEED (출발점 — 검수로 보강). 텍스트형 PII = 68% 우회 타겟.
DISEASE_SEED = {
    # 암
    "암", "구강암", "위암", "폐암", "간암", "유방암", "대장암", "갑상선암", "췌장암",
    "전립선암", "자궁경부암", "난소암", "신장암", "방광암", "식도암", "담도암", "혈액암",
    # 만성·대사
    "당뇨", "당뇨병", "고혈압", "저혈압", "고지혈증", "통풍", "골다공증", "갑상선기능항진증",
    "갑상선기능저하증", "신부전", "만성신부전", "간경화", "지방간",
    # 심혈관·뇌
    "뇌출혈", "뇌경색", "뇌졸중", "심근경색", "협심증", "부정맥", "심부전", "동맥경화",
    "정맥류", "혈전증", "대동맥류", "판막증",
    # 호흡기·감염
    "폐렴", "패혈증", "결핵", "폐결핵", "기관지염", "천식", "만성폐쇄성폐질환", "비염",
    "축농증", "중이염", "감염", "대상포진", "봉와직염", "간염",
    # 소화기
    "위염", "위궤양", "십이지장궤양", "역류성식도염", "궤양", "복막염", "충수염", "맹장염",
    "췌장염", "담석", "담낭염", "치질", "치핵", "탈장",
    # 근골격·신경
    "골절", "디스크", "추간판탈출증", "척추협착증", "관절염", "류마티스관절염", "인대파열",
    "반월상연골판파열", "회전근개파열", "치매", "알츠하이머", "파킨슨병", "뇌전증",
    # 정신·기타
    "우울증", "조현병", "공황장애", "불안장애", "불면증",
    "백내장", "녹내장", "치주염", "치은염", "빈혈", "백혈병", "림프종", "종양",
    "자궁근종", "자궁내막증", "난소낭종", "전립선비대증", "방광염", "요로결석", "신장결석",
    "탈모", "건선", "아토피", "두드러기", "황달", "합병증", "염증", "화상",
}
MEDICAL_PROC_SEED = {
    "임플란트", "발치", "사랑니발치", "상악동거상술", "수술", "시술", "마취", "전신마취",
    "국소마취", "수면마취", "내시경", "위내시경", "대장내시경", "기관지내시경", "봉합", "절개",
    "생검", "조직검사", "세포검사", "골수검사", "방사선치료", "항암치료", "항암화학요법",
    "면역치료", "투석", "혈액투석", "복막투석", "수혈", "주사", "처방", "진단", "촬영",
    "초음파", "심장초음파", "엑스레이", "CT", "MRI", "카테터", "스텐트", "스텐트삽입",
    "제왕절개", "자연분만", "분만", "소파술", "발관", "삽관", "기관삽관", "기관절개술",
    "성형", "교정", "보철", "신경치료", "충치치료", "스케일링", "개복술", "복강경수술",
    "관절경", "인공관절치환술", "척추유합술", "디스크수술", "백내장수술", "라식", "라섹",
    "자궁적출술", "갑상선절제술", "위절제술", "대장절제술", "담낭절제술", "충수절제술",
    "탈장수술", "치질수술", "혈관조영술", "물리치료", "재활치료", "도수치료", "신경차단술",
    "인공호흡기", "요추천자", "복수천자",
}
# 약물(처방) SEED — 처방 정보도 텍스트형 PII
MEDICATION_SEED = {
    "항생제", "진통제", "소염제", "소염진통제", "해열제", "스테로이드", "항응고제",
    "항혈소판제", "인슐린", "혈압약", "혈압강하제", "당뇨약", "고지혈증약", "수면제",
    "항우울제", "항불안제", "마취제", "마약성진통제", "항암제", "면역억제제", "이뇨제",
    "제산제", "위장약", "항히스타민제", "기관지확장제", "항바이러스제",
}

META = {
    "id": "ducut91_weak",
    "kind": "weak_examples",
    "license": "PSEUDO-weak (검수필요)",  # gold 에 안 섞임, export 기본 제외
    "entities": ["DISEASE", "MEDICAL_PROC", "MEDICATION", "DEPARTMENT", "PHONE", "EMAIL", "RRN"],
    "note": "Phase B 텍스트형 PII 약한라벨 — 본문전체, 검수+스키마확장 후 학습",
}

_BODY_COLS_SKIP = {"url", "case_id", "﻿case_id", "seq", "id"}


def _full_body(row: dict) -> str:
    """본문 전체 = url/id 제외 모든 텍스트 컬럼 concat."""
    parts = [str(v) for k, v in row.items()
             if k.lower().strip("﻿") not in _BODY_COLS_SKIP and v]
    return "\n".join(parts).strip()


def _departments() -> set[str]:
    deps: set[str] = set()
    medical = _CSVS[0]
    if medical.exists():
        with open(medical, encoding="utf-8") as fp:
            for row in csv.DictReader(fp):
                d = (row.get("medical_department") or "").strip()
                if len(d) >= 2:
                    deps.add(d)
    return deps


def collect(limit: int = 0) -> dict:
    dictionaries = [
        ("DEPARTMENT", _departments()),
        ("DISEASE", DISEASE_SEED),
        ("MEDICAL_PROC", MEDICAL_PROC_SEED),
        ("MEDICATION", MEDICATION_SEED),
    ]
    examples = []
    for csv_path in _CSVS:
        if not csv_path.exists():
            continue
        with open(csv_path, encoding="utf-8") as fp:
            for row in csv.DictReader(fp):
                body = _full_body(row)
                if len(body) < 30:
                    continue
                labeled = weak_label(body, dictionaries, STRUCTURED_REGEXES)
                labeled["sentence"] = body
                examples.append(labeled)
                if limit and len(examples) >= limit:
                    break
        if limit and len(examples) >= limit:
            break
    return {
        "kind": "weak_examples",
        "license": META["license"],
        "examples": examples,
    }
