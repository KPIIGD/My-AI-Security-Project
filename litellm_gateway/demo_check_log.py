# -*- coding: utf-8 -*-
"""데모 요청 후 해당 spend log 가 마스킹된 본문을 담는지 검증.
  docker exec litellm-litellm-1 python /app/config/demo_check_log.py
"""
import json
import time
import httpx

GATEWAY = "http://localhost:4000"
KEY = "sk-1234"
HEAD = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}

PROMPT = (
    "다음 고객 상담 내용을 3줄로 요약해줘.\n"
    "상담사: 안녕하세요 무엇을 도와드릴까요?\n"
    "고객: 김민수입니다. 전화번호는 010-2345-6789 이고요, "
    "서울시 강남구 테헤란로 152에 삽니다. 이메일은 minsu.kim@gmail.com 이에요. "
    "주문한 상품이 아직 안 왔어요."
)

r = httpx.post(
    f"{GATEWAY}/v1/chat/completions",
    headers=HEAD,
    json={"model": "gpt-4o", "messages": [{"role": "user", "content": PROMPT}], "max_tokens": 200},
    timeout=90,
)
body = r.json()
req_id = body.get("id")
print("status:", r.status_code, "| response id:", req_id)
print("assistant:", body["choices"][0]["message"]["content"][:300])

# spend log 적재 대기 (배치 flush)
print("\nspend log flush 대기...")
found = None
for attempt in range(12):
    time.sleep(5)
    try:
        lr = httpx.get(f"{GATEWAY}/spend/logs", headers=HEAD, params={"request_id": req_id}, timeout=30)
        logs = lr.json()
        if isinstance(logs, list) and logs:
            found = logs[0]
            break
        # request_id 필터 미지원 시 전체에서 검색
        lr2 = httpx.get(f"{GATEWAY}/spend/logs", headers=HEAD, timeout=30)
        alllogs = lr2.json()
        if isinstance(alllogs, list):
            for lg in alllogs:
                if lg.get("request_id") == req_id:
                    found = lg
                    break
        if found:
            break
    except Exception as e:
        print(f"  [{attempt}] 조회 예외:", type(e).__name__, str(e)[:120])
    print(f"  [{attempt}] 아직 없음...")

print("\n" + "=" * 64)
if found:
    print("SPEND LOG 발견 — UI Logs 탭에 표시될 데이터")
    print("=" * 64)
    print("request_id :", found.get("request_id"))
    print("model      :", found.get("model"))
    print("messages   :", json.dumps(found.get("messages"), ensure_ascii=False)[:600])
    print("response   :", json.dumps(found.get("response"), ensure_ascii=False)[:400])
else:
    print("해당 request_id 의 spend log 를 못 찾음 (flush 지연 가능)")
