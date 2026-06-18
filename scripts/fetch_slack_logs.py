#!/usr/bin/env python3
"""Slack 대화를 날짜별 Markdown으로 저장하는 유틸리티 (자동/반복 수집용).

토큰만 있으면 MCP 없이도 대화 로그를 `슬랙/<날짜>.md` 로 떨어뜨립니다.
**멱등(idempotent)** 하게 동작합니다 — 같은 날짜를 몇 번을 다시 돌려도 그날 파일을
새로 갱신할 뿐 중복되지 않으며, 사람/LLM이 채운 `## 📌 요약` 블록은 보존합니다.
그래서 스케줄러로 N분마다 반복 실행해 "사실상 실시간" 수집이 가능합니다.

사용법:
    # 토큰 설정 (절대 코드/깃에 넣지 마세요)
    #   PowerShell:  $env:SLACK_BOT_TOKEN = "xoxp-..."
    #   bash:        export SLACK_BOT_TOKEN=xoxp-...

    python scripts/fetch_slack_logs.py                  # 오늘(KST), 접근 가능한 모든 공개 채널
    python scripts/fetch_slack_logs.py --days 2         # 오늘+어제 (스케줄러 권장: 자정 롤오버 대비)
    python scripts/fetch_slack_logs.py --date 2026-06-18
    python scripts/fetch_slack_logs.py --channel general,random --date 2026-06-18

옵션:
    --channel  채널명/ID, 콤마로 여러 개. 생략하면 접근 가능한 공개 채널 전체 자동 탐지.
    --date     기준 날짜 YYYY-MM-DD (생략 시 오늘).
    --days N   기준 날짜부터 과거로 N일치 수집 (기본 1).
    --tz H     시간대 UTC offset 시간 (기본 9=KST).

필요한 Slack 토큰 scope: channels:history, channels:read, users:read
    (비공개 채널이면 groups:history, groups:read 추가)

비고:
    - 출력 `슬랙/<날짜>.md` 는 .gitignore 처리되어 공개 레포에 커밋되지 않습니다.
    - 한 채널에서 오류(not_in_channel 등)가 나도 나머지 채널/날짜는 계속 수집합니다.
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

# Windows 콘솔(cp949)에서 한글·이모지 출력 시 UnicodeEncodeError 방지
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8")
    except (AttributeError, ValueError):
        pass

API = "https://slack.com/api/"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO_ROOT, "슬랙")
CHANNEL_ID_RE = re.compile(r"^[CGD][A-Z0-9]{7,}$")
SUMMARY_HEADING = "## 📌 요약 (LLM·사람용)"
DEFAULT_SUMMARY = (
    f"{SUMMARY_HEADING}\n\n"
    "- **핵심 결정**:\n"
    "- **액션 아이템**:\n"
    "- **관련 커밋 / 문서 / 이슈**:\n"
    "- **미해결 논점**:"
)


def call(method: str, token: str, **params) -> dict:
    """Slack Web API GET 호출 (429 시 Retry-After 만큼 대기 후 재시도)."""
    url = API + method + "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    data = {}
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


def list_channels(token: str) -> list:
    """접근 가능한 채널 목록 [{id, name, is_member}]. 비공개는 scope 없으면 자동 생략."""
    chans, seen = [], set()
    for kind in ("public_channel", "private_channel"):
        try:
            for c in paginate(
                "conversations.list", token, "channels",
                types=kind, exclude_archived="true",
            ):
                if c["id"] not in seen:
                    seen.add(c["id"])
                    chans.append({"id": c["id"], "name": c.get("name", c["id"]),
                                  "is_member": c.get("is_member", False)})
        except RuntimeError as e:
            if "missing_scope" in str(e):
                print(f"  ({kind} 생략 — scope 없음)", file=sys.stderr)
            else:
                raise
    return chans


def resolve_targets(token: str, channel_arg: str | None) -> list:
    """--channel 인자를 [{id, name}] 로 변환. 생략 시 접근 가능한 공개 채널 전체."""
    catalog = list_channels(token)
    by_id = {c["id"]: c for c in catalog}
    by_name = {c["name"]: c for c in catalog}
    if not channel_arg:
        # 자동 모드: 공개 채널 전체 (비공개는 멤버인 것만)
        return [{"id": c["id"], "name": c["name"]} for c in catalog]
    targets = []
    for raw in [c.strip() for c in channel_arg.split(",") if c.strip()]:
        key = raw.lstrip("#")
        hit = by_id.get(raw) or by_name.get(key)
        if hit:
            targets.append({"id": hit["id"], "name": hit["name"]})
        elif CHANNEL_ID_RE.match(raw):
            info = call("conversations.info", token, channel=raw).get("channel", {})
            targets.append({"id": raw, "name": info.get("name", raw)})
        else:
            print(f"  경고: 채널 '{raw}' 을(를) 찾지 못해 건너뜁니다.", file=sys.stderr)
    return targets


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


def fetch_channel_md(token, cid, name, oldest, latest, tz, users):
    """채널 하루치를 마크다운 섹션 문자열로. 실제 메시지 없으면 None."""
    msgs = list(paginate(
        "conversations.history", token, "messages",
        channel=cid, oldest=f"{oldest:.6f}", latest=f"{latest:.6f}", inclusive="true",
    ))
    msgs.sort(key=lambda m: float(m["ts"]))

    body_lines = []
    for m in msgs:
        if m.get("subtype") in {"channel_join", "channel_leave"}:
            continue
        who = users.get(m.get("user", ""), m.get("username", m.get("user", "?")))
        body = clean_text(m.get("text", ""), users)
        body_lines.append(f"**{hhmm(m['ts'], tz)} {who}**")
        body_lines.append(body if body else "_(첨부/시스템 메시지)_")
        body_lines.append("")
        if m.get("thread_ts") == m.get("ts") and m.get("reply_count", 0) > 0:
            for r in paginate("conversations.replies", token, "messages", channel=cid, ts=m["ts"]):
                if r.get("ts") == m.get("ts"):
                    continue  # 부모 메시지 중복 제외
                rwho = users.get(r.get("user", ""), r.get("username", "?"))
                rbody = clean_text(r.get("text", ""), users)
                body_lines.append(f"- ↳ **{hhmm(r['ts'], tz)} {rwho}**: {rbody}")
            body_lines.append("")

    if not body_lines:
        return None
    return "\n".join([f"## #{name}", ""] + body_lines)


def extract_existing_summary(path: str):
    """기존 파일에서 사람/LLM이 채운 📌 요약 블록을 추출 (없으면 None)."""
    if not os.path.exists(path):
        return None
    text = open(path, encoding="utf-8").read()
    if SUMMARY_HEADING not in text:
        return None
    after = text.split(SUMMARY_HEADING, 1)[1]
    block = after.split("\n---\n", 1)[0]
    return (SUMMARY_HEADING + block).rstrip()


def write_day_file(date_str, team, sections, tz_hours):
    """그날 파일을 통째로 다시 쓰되(멱등) 기존 📌 요약은 보존."""
    sections = [s for s in sections if s]
    path = os.path.join(OUT_DIR, f"{date_str}.md")
    if not sections:
        # 메시지 없음: 기존 파일 있으면 보존, 없으면 생성 안 함
        return (path if os.path.exists(path) else None), False, False
    existed = os.path.exists(path)
    summary = extract_existing_summary(path) or DEFAULT_SUMMARY
    os.makedirs(OUT_DIR, exist_ok=True)

    content = (
        f"# 슬랙 대화 로그 — {date_str}\n\n"
        f"> 워크스페이스: {team}\n"
        f"> 하루치 전체 채널 대화를 시간순으로 정리한 기록 (UTC+{tz_hours} 기준).\n"
        f"> 인덱스: [`목차.md`](목차.md)\n>\n"
        f"> ⚠️ 개인정보 포함 가능 — 이 파일은 `.gitignore` 처리되어 로컬에만 존재합니다.\n\n"
        f"---\n\n"
    )
    for sec in sections:
        content += sec + "\n---\n\n"
    content += (
        summary + "\n\n---\n\n"
        f"_수집일: {date_str} · 출처: Slack API (fetch_slack_logs.py)_\n"
    )
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return path, not existed, True


def main() -> int:
    ap = argparse.ArgumentParser(description="Slack 대화를 날짜별 Markdown으로 저장 (자동/반복 수집)")
    ap.add_argument("--channel", help="채널명/ID 콤마 구분 (생략 시 공개 채널 전체 자동 탐지)")
    ap.add_argument("--date", help="기준 날짜 YYYY-MM-DD (생략 시 오늘)")
    ap.add_argument("--days", type=int, default=1, help="기준 날짜부터 과거로 N일치 (기본 1)")
    ap.add_argument("--tz", type=int, default=9, help="시간대 UTC offset 시간 (기본 9=KST)")
    args = ap.parse_args()

    token = os.environ.get("SLACK_BOT_TOKEN") or os.environ.get("SLACK_TOKEN")
    if not token:
        print("환경변수 SLACK_BOT_TOKEN 이 없습니다. 토큰을 먼저 설정하세요.", file=sys.stderr)
        return 2

    tz = timezone(timedelta(hours=args.tz))
    base = (datetime.strptime(args.date, "%Y-%m-%d") if args.date
            else datetime.now(tz)).replace(tzinfo=tz)
    dates = [(base - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(max(1, args.days))]

    try:
        team = call("auth.test", token).get("team", "unknown")
        targets = resolve_targets(token, args.channel)
        if not targets:
            print("수집할 채널이 없습니다 (scope/채널명 확인).", file=sys.stderr)
            return 1
        print(f"워크스페이스: {team} · 채널 {len(targets)}개 · 날짜 {dates[-1]}~{dates[0]} · 사용자 로딩...",
              file=sys.stderr)
        users = build_user_map(token)
    except (RuntimeError, urllib.error.URLError) as e:
        print(f"오류(초기화): {e}", file=sys.stderr)
        return 1

    wrote = 0
    for date_str in dates:
        start = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=tz)
        oldest, latest = start.timestamp(), (start + timedelta(days=1)).timestamp()
        sections = []
        for ch in targets:
            try:
                sec = fetch_channel_md(token, ch["id"], ch["name"], oldest, latest, tz, users)
                if sec:
                    sections.append(sec)
            except (RuntimeError, urllib.error.URLError) as e:
                print(f"  #{ch['name']} 건너뜀: {e}", file=sys.stderr)
        path, new, written = write_day_file(date_str, team, sections, args.tz)
        if written:
            wrote += 1
            print(f"{'생성' if new else '갱신'}: {path}")
        else:
            print(f"{date_str}: 메시지 없음 — 파일 변경 없음.", file=sys.stderr)

    print(f"완료: {wrote}개 날짜 파일 갱신.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
