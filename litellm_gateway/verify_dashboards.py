# -*- coding: utf-8 -*-
"""양 대시보드 로그 적재 검증 (컨테이너 내부 실행)."""
import base64
import json
import httpx

# 1) LiteLLM spend logs (내장 UI 가 보여주는 DB 로그)
print("=" * 60)
print("LiteLLM /spend/logs (내장 UI 데이터 소스)")
print("=" * 60)
try:
    r = httpx.get(
        "http://localhost:4000/spend/logs",
        headers={"Authorization": "Bearer sk-1234"},
        timeout=20,
    )
    logs = r.json()
    print("status:", r.status_code, "| log 건수:", len(logs))
    # gpt-4o 완료 요청만 추려서 최신순으로
    gpt = [l for l in logs if (l.get("model") or "").startswith("gpt")]
    gpt.sort(key=lambda l: l.get("startTime") or l.get("endTime") or "", reverse=True)
    print("gpt 요청 행 수:", len(gpt))
    if gpt:
        last = gpt[0]
        print("model       :", last.get("model"))
        print("messages    :", json.dumps(last.get("messages"), ensure_ascii=False)[:300])
        print("response    :", json.dumps(last.get("response"), ensure_ascii=False)[:200])
        meta = last.get("metadata") or {}
        kpg = meta.get("korean_pii_guardrail")
        print("guardrail md:", json.dumps(kpg, ensure_ascii=False)[:400] if kpg else "(없음)")
except Exception as e:
    print("예외:", type(e).__name__, str(e)[:200])

# 2) Langfuse traces
print("\n" + "=" * 60)
print("Langfuse /api/public/traces")
print("=" * 60)
try:
    auth = base64.b64encode(b"pk-lf-capstone-pub-1234567890:sk-lf-capstone-secret-abcdefghij").decode()
    r = httpx.get(
        "http://langfuse:3000/api/public/traces?limit=3",
        headers={"Authorization": f"Basic {auth}"},
        timeout=20,
    )
    print("status:", r.status_code)
    body = r.json()
    items = body.get("data", body if isinstance(body, list) else [])
    print("trace 건수:", len(items))
    for t in items[:3]:
        print(f"  - id={t.get('id','?')[:18]} name={t.get('name')} "
              f"time={t.get('timestamp')}")
except Exception as e:
    print("예외:", type(e).__name__, str(e)[:200])
