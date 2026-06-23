# -*- coding: utf-8 -*-
"""최근 spend log 1건의 전체 필드를 덤프 — 입력 프롬프트가 어느 키에 저장되는지 확인."""
import json
import httpx

GATEWAY = "http://localhost:4000"
HEAD = {"Authorization": "Bearer sk-1234"}

lr = httpx.get(f"{GATEWAY}/spend/logs", headers=HEAD, timeout=30)
logs = lr.json()
if not (isinstance(logs, list) and logs):
    print("no logs:", json.dumps(logs, ensure_ascii=False)[:300])
    raise SystemExit

latest = sorted(logs, key=lambda x: x.get("startTime", ""))[-1]
print("=== 최근 spend log 전체 키 ===")
for k in sorted(latest.keys()):
    v = latest[k]
    sval = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
    print(f"  {k:28} = {sval[:160]}")
