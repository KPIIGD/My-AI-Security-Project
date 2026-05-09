"""Generate scalable normal Korean non-PII text datasets."""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_SEED = 20260501


CATEGORIES: dict[str, dict[str, list[str]]] = {
    "daily": {
        "topics": [
            "날씨 변화",
            "주말 계획",
            "독서 습관",
            "운동 루틴",
            "식사 준비",
            "집안 정리",
            "취미 활동",
            "산책 코스",
            "영화 감상",
            "음악 추천",
            "카페 분위기",
            "여행 준비",
            "생활 패턴",
            "수면 습관",
            "반려식물 관리",
        ],
        "objects": [
            "준비 과정",
            "진행 방식",
            "선택 기준",
            "느낀 점",
            "개선 방향",
            "다음 계획",
            "사용 경험",
            "만족도",
            "변화 흐름",
            "주의할 점",
        ],
    },
    "business": {
        "topics": [
            "회의 일정",
            "업무 프로세스",
            "보고서 검토",
            "자료 정리",
            "일정 조율",
            "품질 점검",
            "운영 정책",
            "교육 안내",
            "공지 사항",
            "협업 방식",
            "성과 공유",
            "검토 의견",
            "리스크 관리",
            "업무 분장",
            "개선 과제",
        ],
        "objects": [
            "핵심 내용을",
            "진행 상황을",
            "우선순위를",
            "검토 결과를",
            "변경 사항을",
            "세부 기준을",
            "관련 자료를",
            "완료 조건을",
            "후속 작업을",
            "논의 범위를",
        ],
    },
    "technical": {
        "topics": [
            "배포 절차",
            "서버 설정",
            "캐시 정책",
            "로그 수집",
            "모니터링 지표",
            "테스트 자동화",
            "API 설계",
            "데이터 처리",
            "권한 관리",
            "성능 개선",
            "오류 분석",
            "문서화 방식",
            "버전 관리",
            "알림 규칙",
            "백업 전략",
        ],
        "objects": [
            "처리 흐름을",
            "구성 방식을",
            "검증 기준을",
            "운영 절차를",
            "예외 상황을",
            "응답 시간을",
            "사용 패턴을",
            "변경 이력을",
            "설정 값을",
            "테스트 범위를",
        ],
    },
    "news": {
        "topics": [
            "경제 전망",
            "교육 정책",
            "환경 보호",
            "문화 행사",
            "교통 개선",
            "산업 동향",
            "지역 축제",
            "공공 서비스",
            "소비 흐름",
            "기술 혁신",
            "관광 활성화",
            "스포츠 경기",
            "연구 성과",
            "시장 변화",
            "에너지 절감",
        ],
        "objects": [
            "주요 쟁점을",
            "변화 요인을",
            "향후 전망을",
            "참여 방식을",
            "정책 방향을",
            "현장 반응을",
            "기대 효과를",
            "운영 계획을",
            "분석 결과를",
            "개선 방안을",
        ],
    },
    "academic": {
        "topics": [
            "연구 방법",
            "실험 설계",
            "분석 절차",
            "이론적 배경",
            "문헌 검토",
            "평가 지표",
            "모형 비교",
            "가설 설정",
            "결과 해석",
            "한계 논의",
            "후속 연구",
            "자료 수집",
            "검증 방식",
            "표본 구성",
            "관찰 결과",
        ],
        "objects": [
            "주요 변수를",
            "측정 기준을",
            "분석 단계를",
            "비교 대상을",
            "연구 범위를",
            "검증 결과를",
            "해석 관점을",
            "자료 특성을",
            "논의 구조를",
            "실험 조건을",
        ],
    },
    "customer_support": {
        "topics": [
            "문의 흐름",
            "안내 문구",
            "접수 절차",
            "처리 상태",
            "대기 시간",
            "서비스 품질",
            "상담 기준",
            "응답 방식",
            "사용자 경험",
            "만족도 조사",
            "FAQ 구성",
            "피드백 정리",
            "공지 전달",
            "문제 해결",
            "개선 요청",
        ],
        "objects": [
            "안내 내용을",
            "처리 절차를",
            "응답 품질을",
            "접수 기준을",
            "검토 의견을",
            "개선 사항을",
            "진행 상태를",
            "대응 방식을",
            "사용 흐름을",
            "확인 항목을",
        ],
    },
    "product": {
        "topics": [
            "제품 기획",
            "사용성 평가",
            "화면 구성",
            "기능 개선",
            "디자인 검토",
            "출시 준비",
            "고객 반응",
            "운영 지표",
            "품질 기준",
            "가격 정책",
            "시장 조사",
            "설문 결과",
            "기능 우선순위",
            "사용 흐름",
            "개선 실험",
        ],
        "objects": [
            "기획 의도를",
            "사용 흐름을",
            "개선 범위를",
            "검토 기준을",
            "실험 결과를",
            "운영 지표를",
            "출시 조건을",
            "반응 추이를",
            "비교 항목을",
            "적용 방안을",
        ],
    },
    "policy": {
        "topics": [
            "운영 원칙",
            "검토 기준",
            "내부 절차",
            "문서 보관",
            "교육 과정",
            "품질 관리",
            "변경 승인",
            "위험 평가",
            "점검 항목",
            "보고 체계",
            "감사 준비",
            "업무 기준",
            "역할 정의",
            "승인 절차",
            "개선 조치",
        ],
        "objects": [
            "적용 범위를",
            "검토 절차를",
            "승인 기준을",
            "관리 방식을",
            "점검 결과를",
            "개선 계획을",
            "운영 원칙을",
            "보고 흐름을",
            "책임 범위를",
            "변경 내역을",
        ],
    },
}


STYLES = [
    "plain",
    "notice",
    "memo",
    "report",
    "chat",
    "manual",
    "summary",
    "question",
]


QUALIFIERS = [
    "간단히",
    "차분하게",
    "구체적으로",
    "단계별로",
    "전체적으로",
    "우선적으로",
    "반복해서",
    "객관적으로",
    "실무 관점에서",
    "사용자 관점에서",
    "운영 관점에서",
    "비교 가능한 방식으로",
]


OUTCOMES = [
    "정리합니다",
    "검토합니다",
    "공유합니다",
    "확인합니다",
    "비교합니다",
    "개선합니다",
    "기록합니다",
    "설명합니다",
    "점검합니다",
    "조정합니다",
    "분석합니다",
    "제안합니다",
]


BENIGN_NUMBERS = [
    "첫 번째",
    "두 가지",
    "세 단계",
    "네 가지",
    "5분 정도",
    "10분 안팎",
    "20퍼센트 수준",
    "3개 항목",
    "2단계 절차",
    "1차 검토",
    "버전 2",
    "상위 3개",
]


CONNECTORS = [
    "그리고",
    "다만",
    "또한",
    "이후",
    "따라서",
    "반면",
    "특히",
    "마지막으로",
]


TEMPLATES = [
    "{topic}의 {obj} {qualifier} {outcome}.",
    "{topic}에 대해 {obj} {outcome}는 방식으로 내용을 구성합니다.",
    "{topic} 관련 {obj} 먼저 확인하고 필요한 부분만 보완합니다.",
    "{topic}에서는 {obj} {qualifier} 살펴보는 과정이 중요합니다.",
    "{topic} 문서는 {obj} 중심으로 작성하면 이해하기 쉽습니다.",
    "{topic}에 대한 논의는 {obj} 기준으로 나누어 진행합니다.",
    "{topic} 과정에서 발견된 내용을 {qualifier} {outcome}.",
    "{topic} 관련 자료는 {obj} 빠르게 찾을 수 있도록 정리합니다.",
    "{topic}의 다음 단계는 {obj} 다시 확인하는 것입니다.",
    "{topic}에서는 {benign_number} 정도의 예시를 두고 비교합니다.",
    "{connector} {topic}의 {obj} {qualifier} {outcome}.",
    "{topic} 관련 의견을 모아 {obj} 다음 회의에서 검토합니다.",
    "{topic} 안내문은 짧은 문장으로 작성하고 핵심만 남깁니다.",
    "{topic}에 대한 질문은 범위를 좁혀 순서대로 처리합니다.",
    "{topic} 결과를 표로 정리하면 차이를 쉽게 확인할 수 있습니다.",
    "{topic}에서 중요한 부분은 과도하게 복잡한 설명을 줄이는 것입니다.",
]


STYLE_PREFIXES = {
    "plain": ["", ""],
    "notice": ["안내드립니다. ", "공지 사항입니다. ", "참고 바랍니다. "],
    "memo": ["메모: ", "검토 메모: ", "작업 메모: "],
    "report": ["요약 보고: ", "검토 결과: ", "분석 요약: "],
    "chat": ["좋아요. ", "확인했어요. ", "그 부분은 "],
    "manual": ["절차 안내: ", "사용 방법: ", "운영 가이드: "],
    "summary": ["핵심 요약: ", "간단 요약: ", "정리하면, "],
    "question": ["질문입니다. ", "확인 요청: ", "검토가 필요합니다. "],
}


STYLE_SUFFIXES = {
    "plain": ["", ""],
    "notice": [" 확인 후 반영해 주세요.", " 필요 시 담당 부서에서 이어서 검토합니다."],
    "memo": [" 추가 의견은 별도 문서에 남깁니다.", " 중복된 내용은 제외합니다."],
    "report": [" 세부 내용은 표와 문단으로 나누어 제시합니다.", " 결론은 마지막 문단에 배치합니다."],
    "chat": [" 너무 길지 않게 정리하면 좋겠습니다.", " 지금은 큰 흐름만 보면 됩니다."],
    "manual": [" 순서를 바꾸지 않도록 주의합니다.", " 완료 후 결과를 다시 확인합니다."],
    "summary": [" 불필요한 예시는 줄였습니다.", " 다음 단계만 남겨 두었습니다."],
    "question": [" 어떤 방식이 더 적절한지 검토해 주세요.", " 우선순위 조정이 필요할까요?"],
}


FORBIDDEN_PATTERNS: dict[str, re.Pattern[str]] = {
    "email": re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"),
    "url": re.compile(r"\b(?:https?://|www\.)\S+", re.IGNORECASE),
    "phone": re.compile(r"\b01[016789][- .]?\d{3,4}[- .]?\d{4}\b"),
    "rrn": re.compile(r"\b\d{6}[- ]?[1-4]\d{6}\b"),
    "card": re.compile(r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b"),
    "account_like": re.compile(r"\b\d{2,6}[- ]\d{2,6}[- ]\d{2,8}\b"),
    "ip": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "token": re.compile(r"\b(?:AKIA|ASIA|eyJ|sk-)[A-Za-z0-9_\-]{10,}\b"),
}


def build_text(rng: random.Random, category: str, style: str) -> str:
    values = CATEGORIES[category]
    template = rng.choice(TEMPLATES)
    text = template.format(
        topic=rng.choice(values["topics"]),
        obj=rng.choice(values["objects"]),
        qualifier=rng.choice(QUALIFIERS),
        outcome=rng.choice(OUTCOMES),
        benign_number=rng.choice(BENIGN_NUMBERS),
        connector=rng.choice(CONNECTORS),
    )

    prefix = rng.choice(STYLE_PREFIXES[style])
    suffix = rng.choice(STYLE_SUFFIXES[style])
    if rng.random() < 0.28:
        second = template.format(
            topic=rng.choice(values["topics"]),
            obj=rng.choice(values["objects"]),
            qualifier=rng.choice(QUALIFIERS),
            outcome=rng.choice(OUTCOMES),
            benign_number=rng.choice(BENIGN_NUMBERS),
            connector=rng.choice(CONNECTORS),
        )
        text = f"{text} {second}"
    return f"{prefix}{text}{suffix}".strip()


def validate_no_pii(text: str) -> list[str]:
    return [name for name, pattern in FORBIDDEN_PATTERNS.items() if pattern.search(text)]


def make_payload(idx: int, text: str, category: str, style: str) -> dict[str, Any]:
    digest = hashlib.sha1(text.encode("utf-8")).hexdigest()[:12]
    return {
        "id": f"NKR-{idx:06d}",
        "text_id": digest,
        "text": text,
        "mutated": text,
        "original": "",
        "pii_type": "NO_PII",
        "label": "NO_PII",
        "lang": "KR",
        "category": category,
        "style": style,
        "synthetic": True,
    }


def generate(count: int, seed: int, max_attempt_multiplier: int = 30) -> list[dict[str, Any]]:
    rng = random.Random(seed)
    categories = list(CATEGORIES)
    seen: set[str] = set()
    payloads: list[dict[str, Any]] = []
    attempts = 0
    max_attempts = max(1000, count * max_attempt_multiplier)

    while len(payloads) < count and attempts < max_attempts:
        attempts += 1
        category = categories[len(payloads) % len(categories)]
        if rng.random() < 0.35:
            category = rng.choice(categories)
        style = STYLES[(len(payloads) + rng.randrange(len(STYLES))) % len(STYLES)]
        text = build_text(rng, category, style)
        if text in seen:
            continue
        if validate_no_pii(text):
            continue
        seen.add(text)
        payloads.append(make_payload(len(payloads), text, category, style))

    if len(payloads) < count:
        raise RuntimeError(
            f"Could only generate {len(payloads)} clean rows after {attempts} attempts"
        )
    return payloads


def summarize(payloads: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "by_category": dict(Counter(p["category"] for p in payloads)),
        "by_style": dict(Counter(p["style"] for p in payloads)),
        "avg_chars": round(sum(len(p["text"]) for p in payloads) / len(payloads), 1)
        if payloads
        else 0,
        "min_chars": min((len(p["text"]) for p in payloads), default=0),
        "max_chars": max((len(p["text"]) for p in payloads), default=0),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate normal Korean non-PII data.")
    parser.add_argument("--count", type=int, default=10000)
    parser.add_argument("--output", required=True)
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED)
    parser.add_argument("--indent", type=int, default=0)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = Path(args.output).expanduser().resolve()
    payloads = generate(args.count, args.seed)
    violations = [
        {"id": p["id"], "patterns": validate_no_pii(p["text"]), "text": p["text"]}
        for p in payloads
        if validate_no_pii(p["text"])
    ]
    if violations:
        raise SystemExit(f"Generated data has forbidden patterns: {violations[:3]}")

    metadata = {
        "dataset": "normal_kr_non_pii",
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "count": len(payloads),
        "seed": args.seed,
        "lang": "KR",
        "label": "NO_PII",
        "generator": str(Path(__file__).as_posix()),
        "forbidden_patterns": sorted(FORBIDDEN_PATTERNS),
        **summarize(payloads),
    }
    output = {"metadata": metadata, "payloads": payloads}
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        if args.indent > 0:
            json.dump(output, f, ensure_ascii=False, indent=args.indent)
        else:
            json.dump(output, f, ensure_ascii=False, separators=(",", ":"))
    print(f"saved {len(payloads)} rows to {output_path}")
    print(json.dumps(summarize(payloads), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
