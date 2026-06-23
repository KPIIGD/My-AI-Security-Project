# -*- coding: utf-8 -*-
"""스크린샷용 데모 요청 — 게이트웨이로 PII 포함 요청을 보내고,
LiteLLM spend log 에 마스킹된 프롬프트가 적재되는지 확인한다.

  docker exec litellm-litellm-1 python /app/config/demo_masking_request.py
"""
import json
import time
import httpx

GATEWAY = "http://localhost:4000"
KEY = "sk-1234"

# 고객센터 상담 요약 시나리오 — 이름/전화/주소/이메일이 섞인 자연스러운 한국어
PROMPT = (
    "다음 고객 상담 내용을 3줄로 요약해줘.\n"
    "상담사: 안녕하세요 무엇을 도와드릴까요?\n"
    "고객: 김민수입니다. 전화번호는 010-2345-6789 이고요, "
    "서울시 강남구 테헤란로 152에 삽니다. 이메일은 minsu.kim@gmail.com 이에요. "
    "주문한 상품이 아직 안 왔어요."
)

print("=" * 64)
print("요청 보내기 (원문 — 화면에는 보여주되 LLM 에는 마스킹되어 전달됨)")
print("=" * 64)
print(PROMPT)

r = httpx.post(
    f"{GATEWAY}/v1/chat/completions",
    headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"},
    json={
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": PROMPT}],
        "max_tokens": 200,
    },
    timeout=90,
)
print("\nstatus:", r.status_code)
body = r.json()
if r.status_code == 200:
    print("assistant:", body["choices"][0]["message"]["content"])
    req_id = body.get("id")
    print("response id:", req_id)
else:
    print("body:", json.dumps(body, ensure_ascii=False)[:600])

# spend log 확인 — 마스킹된 프롬프트가 저장됐는지
print("\n" + "=" * 64)
print("LiteLLM spend log (UI Logs 탭에 표시되는 데이터)")
print("=" * 64)
time.sleep(3)
try:
    lr = httpx.get(
        f"{GATEWAY}/spend/logs",
        headers={"Authorization": f"Bearer {KEY}"},
        timeout=30,
    )
    logs = lr.json()
    if isinstance(logs, list) and logs:
        latest = logs[-1]
        print("messages stored :", json.dumps(latest.get("messages"), ensure_ascii=False)[:500])
        print("response stored :", json.dumps(latest.get("response"), ensure_ascii=False)[:300])
        md = latest.get("metadata") or {}
        kpg = md.get("korean_pii_guardrail") if isinstance(md, dict) else None
        print("guardrail meta  :", json.dumps(kpg, ensure_ascii=False)[:500])
    else:
        print("spend log 비어있음 또는 형식 다름:", json.dumps(logs, ensure_ascii=False)[:300])
except Exception as e:
    print("spend log 조회 예외:", type(e).__name__, str(e)[:200])
