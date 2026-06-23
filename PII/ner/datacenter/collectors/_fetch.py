"""본문 전체 fetch 헬퍼 (finance datacenter/_fetch.py 패턴 이식).

사용자 영구룰 "데이터 수집은 본문 전체" — 목록/RSS엔 요약만 오므로 기사 URL에
직접 들어가 본문 전체를 가져온다.
- fetch_html(url): 진짜 크롬 UA(봇차단 회피) + 인코딩 자동(utf-8→euc-kr).
- extract_body(html): <article> → 최대 텍스트 div → strip. bs4 있으면 정밀.
- polite(): 요청 간 대기(차단 회피).
"""
from __future__ import annotations

import re
import time
import urllib.request

_UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
       "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36")
_HEADERS = {
    "User-Agent": _UA,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.7",
    "Connection": "keep-alive",
}

try:
    from bs4 import BeautifulSoup
    _HAS_BS4 = True
except ImportError:
    _HAS_BS4 = False

_SCRIPT_RE = re.compile(r"<(script|style|noscript)[^>]*>.*?</\1>", re.S | re.I)
_TAG_RE = re.compile(r"<[^>]+>")
_WS_RE = re.compile(r"[ \t\r\f\v]+")
_NL_RE = re.compile(r"\n{3,}")


def fetch_html(url: str, timeout: int = 12, referer: str | None = None) -> str | None:
    headers = dict(_HEADERS)
    if referer:
        headers["Referer"] = referer
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout) as r:
            raw = r.read()
    except Exception:
        return None
    for enc in ("utf-8", "euc-kr", "cp949"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", "ignore")


# 한국어 뉴스 본문 컨테이너 selector (정확 추출 — 네비/목록 오긁힘 방지)
_BODY_SELECTORS = [
    "[itemprop=articleBody]", "#articleBody", "#article-body", ".article-body",
    "#newsct_article", "#articleBodyContents", "#article_body", ".article_body",
    ".article_txt", ".art_text", "#article-view-content-div", ".news_body",
    "#dic_area", ".story-news", "#CmAdContent", ".view_con", "#news_body_area",
]


def _finalize(text: str, max_chars: int) -> str | None:
    text = _WS_RE.sub(" ", text)
    text = _NL_RE.sub("\n\n", text)
    text = "\n".join(line.strip() for line in text.splitlines() if line.strip())
    return text[:max_chars].strip() or None


def extract_body(html: str, max_chars: int = 100000) -> str | None:
    """HTML → 기사 본문 텍스트. 뉴스 본문 selector 우선 → <article> → 최대 div.

    max_chars 기본 100k = 사실상 "본문 전체"(아주 긴 페이지만 안전 상한).
    """
    if not html:
        return None
    if _HAS_BS4:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "aside"]):
            tag.decompose()
        node = None
        for sel in _BODY_SELECTORS:
            node = soup.select_one(sel)
            if node and len(node.get_text(strip=True)) > 80:
                break
            node = None
        if node is None:
            node = soup.find("article")
        if node is None:
            # robust: <p> 단락 텍스트가 가장 많은 컨테이너 = 기사 본문
            # (네비/목록은 <p> 가 적음 → 자동 배제)
            def _p_text_len(el) -> int:
                return sum(len(p.get_text(strip=True)) for p in el.find_all("p", recursive=False)) \
                    or sum(len(p.get_text(strip=True)) for p in el.find_all("p"))
            cands = soup.find_all(["div", "section", "article"])
            node = max(cands, key=_p_text_len, default=None)
            if node is not None and _p_text_len(node) > 80:
                # 본문은 <p> 들만 모아 깔끔하게
                ps = node.find_all("p")
                if ps:
                    text = "\n".join(p.get_text(" ", strip=True) for p in ps)
                    return _finalize(text, max_chars)
        text = (node.get_text("\n") if node else soup.get_text("\n"))
    else:
        text = _TAG_RE.sub(" ", _SCRIPT_RE.sub(" ", html))
    return _finalize(text, max_chars)


def rss_links(xml: str, limit: int = 15) -> list[str]:
    """RSS/Atom 에서 기사 링크 추출."""
    links = re.findall(r"<link>\s*(https?://[^<\s]+)\s*</link>", xml)
    links += re.findall(r'<link[^>]+href="(https?://[^"]+)"', xml)
    out, seen = [], set()
    for u in links:
        if u not in seen and "rss" not in u.lower():
            seen.add(u)
            out.append(u)
        if len(out) >= limit:
            break
    return out


def polite(seconds: float = 0.8) -> None:
    time.sleep(seconds)
