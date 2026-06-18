#!/usr/bin/env python3
"""Slack 대화를 날짜별 Markdown으로 저장하는 유틸리티.

토큰만 발급하면 MCP 없이도 바로 대화 로그를 `슬랙/<날짜>.md` 로 떨어뜨립니다.
출력 포맷은 `슬랙/_템플릿.md` 와 동일합니다.

사용법:
    # 1) 토큰을 환경변수로 (절대 코드/깃에 넣지 마세요)
    #    PowerShell:  $env:SLACK_BOT_TOKEN = "xoxb-..."
    #    bash:        export SLACK_BOT_TOKEN=xoxb-...
    # 2) 실행
    python scripts/fetch_slack_logs.py --channel general --date 2026-06-18
    python scripts/fetch_slack_logs.py --channel general,random --date 2026-06-18 --tz 9
    python scripts/fetch_slack_logs.py --channel general            # --date 생략 시 오늘(KST)

필요한 Slack 토큰 scope:
    channels:history, channels:read, users:read
    (비공개 채널이면 groups:history, groups:read 추가)

비고:
    - 출력 파일 `슬랙/<날짜>.md` 는 .gitignore 처리되어 공개 레포에 커밋되지 않습니다.
    - 같은 날짜 파일이 있으면 해당 채널 섹션을 이어붙입니다(재실행 시 중복 주의).
    - 요약(📌) 섹션은 사람/LLM이 나중에 채웁니다.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone

API = "https://slack.com/api/"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO_ROOT, "슬랙")
CHANNEL_ID_RE = re.compile(r"^[CGD][A-Z0-9]{7,}$")


def call(method: str, token: str, **params) -> dict:
    """Slack Web API GET 호출 (429 시 Retry-After 만큼 대기 후 재시도)."""
    url = API + method + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req) as resp:
                data = json.load(resp)
            break
        except urllib.error.HTTPError as e:
            if e.code == 429 and attempt < 4:
                wait = int(e.headers.get("Retry-After", "2"))
                print(f"  rate limited, {wait}s 대기...", file=sys.stderr)
                time.sleep(wait)
                continue
            raise
    if not data.get("ok"):
        raise RuntimeError(f"Slack API {method} 실패: {data.get('error')}")
    return data


def paginate(method: str, token: str, key: str, **params):
    """cursor 기반 페이지네이션을 자동 처리해 항목을 순회."""
    cursor = ""
    while True:
        p = dict(params, limit=200)
        if cursor:
            p["cursor"] = cursor
        data = call(method, token, **p)
        for item in data.get(key, []):
            yield item
        cursor = data.get("response_metadata", {}).get("next_cursor", "")
        if not cursor:
            break


def build_user_map(token: str) -> dict:
    users = {}
    for u in paginate("users.list", token, "members"):
        prof = u.get("profile", {}) or {}
        users[u["id"]] = (
            prof.get("display_name")
            or prof.get("real_name")
            or u.get("name")
            or u["id"]
        )
    return users


def resolve_channel_id(token: str, channel: str) -> str:
    if CHANNEL_ID_RE.match(channel):
        return channel
    name = channel.lstrip("#")
    for c in paginate(
        "conversations.list", token, "channels",
        types="public_channel,private_channel",
    ):
        if c.get("name") == name:
            return c["id"]
    raise RuntimeError(f"채널 '{channel}' 을(를) 찾지 못했습니다 (scope/이름 확인).")


def clean_text(text: str, users: dict) -> str:
    if not text:
        return ""
    text = re.sub(r"<@([UW][A-Z0-9]+)>", lambda m: "@" + users.get(m.group(1), m.group(1)), text)
    text = re.sub(r"<#[CG][A-Z0-9]+\|([^>]+)>", lambda m: "#" + m.group(1), text)
    text = re.sub(r"<(https?://[^|>]+)\|([^>]+)>", lambda m: f"{m.group(2)} ({m.group(1)})", text)
    text = re.sub(r"<(https?://[^>]+)>", lambda m: m.group(1), text)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    return text.strip()


def hhmm(ts: str, tz: timezone) -> str:
    return datetime.fromtimestamp(float(ts), tz).strftime("%H:%M")


def fetch_channel_md(token, channel, oldest, latest, tz, users) -> str:
    cid = resolve_channel_id(token, channel)
    name = channel.lstrip("#")
    if CHANNEL_ID_RE.match(channel):
        info = call("conversations.info", token, channel=cid)
        name = info.get("channel", {}).get("name", cid)

    msgs = list(paginate(
        "conversations.history", token, "messages",
        channel=cid, oldest=f"{oldest:.6f}", latest=f"{latest:.6f}", inclusive="true",
    ))
    msgs.sort(key=lambda m: float(m["ts"]))

    lines = [f"## #{name}", ""]
    if not msgs:
        lines.append("_이 날짜에 메시지가 없습니다._")
        lines.append("")
        return "\n".join(lines)

    for m in msgs:
        if m.get("subtype") in {"channel_join", "channel_leave"}:
            continue
        who = users.get(m.get("user", ""), m.get("username", m.get("user", "?")))
        body = clean_text(m.get("text", ""), users)
        lines.append(f"**{hhmm(m['ts'], tz)} {who}**")
        lines.append(body if body else "_(첨부/시스템 메시지)_")
        lines.append("")
        # 스레드 답글
        if m.get("thread_ts") == m.get("ts") and m.get("reply_count", 0) > 0:
            replies = list(paginate(
                "conversations.replies", token, "messages",
                channel=cid, ts=m["ts"],
            ))
            for r in replies:
                if r.get("ts") == m.get("ts"):
                    continue  # 부모 메시지 중복 제외
                rwho = users.get(r.get("user", ""), r.get("username", "?"))
                rbody = clean_text(r.get("text", ""), users)
                lines.append(f"- ↳ **{hhmm(r['ts'], tz)} {rwho}**: {rbody}")
            lines.append("")
    return "\n".join(lines)


def write_day_file(date_str, team, sections, tz_hours):
    os.makedirs(OUT_DIR, exist_ok=True)
    path = os.path.join(OUT_DIR, f"{date_str}.md")
    new = not os.path.exists(path)
    with open(path, "a", encoding="utf-8") as f:
        if new:
            f.write(
                f"# 슬랙 대화 로그 — {date_str}\n\n"
                f"> 워크스페이스: {team}\n"
                f"> 하루치 전체 채널 대화를 시간순으로 정리한 기록 (UTC+{tz_hours} 기준).\n"
                f"> 인덱스: [`목차.md`](목차.md)\n>\n"
                f"> ⚠️ 개인정보 포함 가능 — 이 파일은 `.gitignore` 처리되어 로컬에만 존재합니다.\n\n"
                f"---\n\n"
            )
        for sec in sections:
            f.write(sec)
            f.write("\n---\n\n")
        if new:
            f.write(
                "## 📌 요약 (LLM·사람용)\n\n"
                "- **핵심 결정**:\n"
                "- **액션 아이템**:\n"
                "- **관련 커밋 / 문서 / 이슈**:\n"
                "- **미해결 논점**:\n\n"
                f"---\n\n_수집일: {date_str} · 출처: Slack API (fetch_slack_logs.py)_\n"
            )
    return path, new


def main() -> int:
    ap = argparse.ArgumentParser(description="Slack 대화를 날짜별 Markdown으로 저장")
    ap.add_argument("--channel", required=True, help="채널명 또는 ID, 콤마로 여러 개 (예: general,random)")
    ap.add_argument("--date", help="YYYY-MM-DD (생략 시 오늘)")
    ap.add_argument("--tz", type=int, default=9, help="시간대 UTC offset 시간 (기본 9=KST)")
    args = ap.parse_args()

    token = os.environ.get("SLACK_BOT_TOKEN") or os.environ.get("SLACK_TOKEN")
    if not token:
        print("환경변수 SLACK_BOT_TOKEN 이 없습니다. 토큰을 먼저 설정하세요.", file=sys.stderr)
        return 2

    tz = timezone(timedelta(hours=args.tz))
    date_str = args.date or datetime.now(tz).strftime("%Y-%m-%d")
    start = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=tz)
    oldest, latest = start.timestamp(), (start + timedelta(days=1)).timestamp()

    try:
        team = call("auth.test", token).get("team", "unknown")
        print(f"워크스페이스: {team} · 날짜: {date_str} · 사용자 목록 로딩...", file=sys.stderr)
        users = build_user_map(token)
        sections = []
        for ch in [c.strip() for c in args.channel.split(",") if c.strip()]:
            print(f"  #{ch.lstrip('#')} 수집 중...", file=sys.stderr)
            sections.append(fetch_channel_md(token, ch, oldest, latest, tz, users))
    except (RuntimeError, urllib.error.URLError) as e:
        print(f"오류: {e}", file=sys.stderr)
        return 1

    path, new = write_day_file(date_str, team, sections, args.tz)
    print(f"{'생성' if new else '추가'}: {path}")
    print("→ 요약(📌) 섹션을 채우고, 슬랙/목차.md 인덱스를 갱신하세요.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
