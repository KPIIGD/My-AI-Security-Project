"""Collector (라이브 스크래핑, PSEUDO): 한국어 뉴스 RSS → 본문 전체 → weak label.

⭐ "본문 전체" 룰: RSS엔 제목/요약만 → 기사 URL 직접 들어가 본문 전체 fetch.
약한 라벨 = ORG 가제티어(KRX) + 행정구역 ADDRESS + 구조형 regex(phone/email/RRN).
weak_examples 트랙(PSEUDO). 검수 후 학습 승격.

정중함: 피드당 기사 수 cap + 요청 간 sleep. 대량 스크래핑 아님(인프라 증명+소량 수집).
"""
from __future__ import annotations

import re
import sqlite3
from pathlib import Path

from ._fetch import extract_body, fetch_html, polite, rss_links
from ._weak_label import STRUCTURED_REGEXES, weak_label

_DB = Path(__file__).resolve().parents[1] / "ner_datacenter.db"

# 동작 확인된 피드(2026-06). 뉴스 사이트는 기사 직접 fetch 를 자주 막으므로
# (성공률 ~20%) 한 번에 대량보다 incremental 누적(cron 반복)이 정석. dedup 이 중복 차단.
FEEDS = [
    "https://www.yna.co.kr/rss/news.xml",          # 연합 종합
    "https://www.yna.co.kr/rss/society.xml",       # 연합 사회(PII 풍부)
    "https://www.yna.co.kr/rss/politics.xml",      # 연합 정치
    "https://www.yna.co.kr/rss/economy.xml",       # 연합 경제
    "https://www.yna.co.kr/rss/local.xml",         # 연합 지역(주소 풍부)
    "https://rss.donga.com/total.xml",             # 동아
    "https://www.khan.co.kr/rss/rssdata/total_news.xml",  # 경향
    "https://www.hankyung.com/feed/all-news",      # 한경
    "https://www.mk.co.kr/rss/30000001/",          # 매경 경제
    "https://fs.jtbc.co.kr/RSS/newsflash.xml",     # JTBC
]
_DEFAULT_CAP = 300  # 1회 상한. 사이트 차단으로 실제 수집은 더 적음 → 반복 실행 누적

META = {
    "id": "news_rss",
    "kind": "weak_examples",
    "license": "PSEUDO-weak scraped (검수필요)",
    "entities": ["ORG", "ADDRESS", "PHONE", "EMAIL", "RRN"],
    "note": "뉴스 본문전체 약한라벨 — 라이브 스크래핑, 검수 후 학습",
}


def _load_gazetteers() -> list[tuple[str, set]]:
    if not _DB.exists():
        return []
    conn = sqlite3.connect(str(_DB))
    org = {v for (v,) in conn.execute(
        "SELECT value FROM gazetteers WHERE entity_type='ORG'").fetchall() if len(v) >= 2}
    # ADDRESS 는 행정구역(451)만 — 도로명 136k 는 매칭 너무 느림
    addr = {v for (v,) in conn.execute(
        "SELECT value FROM gazetteers WHERE entity_type='ADDRESS' AND source='korea_admin'").fetchall()
        if len(v) >= 2}
    conn.close()
    return [("ORG", org), ("ADDRESS", addr)]


def collect(limit: int = 0) -> dict:
    cap = limit if limit else _DEFAULT_CAP
    dictionaries = _load_gazetteers()
    examples = []
    per_feed = max(1, cap // len(FEEDS))

    for feed in FEEDS:
        xml = fetch_html(feed)
        if not xml:
            continue
        for url in rss_links(xml, limit=per_feed):
            html = fetch_html(url, referer=feed)
            body = extract_body(html)
            polite(0.8)
            if not body or len(body) < 100:
                continue
            labeled = weak_label(body, dictionaries, STRUCTURED_REGEXES)
            labeled["sentence"] = body
            examples.append(labeled)
            if len(examples) >= cap:
                break
        if len(examples) >= cap:
            break

    return {
        "kind": "weak_examples",
        "license": META["license"],
        "examples": examples,
    }
