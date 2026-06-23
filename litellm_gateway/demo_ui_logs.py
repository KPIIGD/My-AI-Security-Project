# -*- coding: utf-8 -*-
"""UI Logs 탭이 실제 호출하는 엔드포인트 응답을 확인 — 요청 본문이 어느 필드로 오는지."""
import json
import httpx

GATEWAY = "http://localhost:4000"
HEAD = {"Authorization": "Bearer sk-1234"}

# UI 가 쓰는 페이지네이션 엔드포인트
PARAMS = {
    "page": 1,
    "page_size": 5,
    "start_date": "2026-06-23 00:00:00",
    "end_date": "2026-06-24 00:00:00",
}
for path in ["/spend/logs/ui", "/spend/logs/ui/v2"]:
    try:
        r = httpx.get(f"{GATEWAY}{path}", headers=HEAD, params=PARAMS, timeout=20)
        print(f"### {path} -> {r.status_code}")
        if r.status_code != 200:
            print("   ", r.text[:200]); continue
        data = r.json()
        rows = data.get("data") if isinstance(data, dict) else data
        if not rows:
            print("    (no rows)"); continue
        row = rows[0]
        print("    keys:", sorted(row.keys()))
        for f in ["request_id", "messages", "response", "proxy_server_request"]:
            v = row.get(f)
            s = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
            print(f"    {f:22} = {s[:220]}")
        break
    except Exception as e:
        print(f"### {path} ERR:", type(e).__name__, str(e)[:120])
