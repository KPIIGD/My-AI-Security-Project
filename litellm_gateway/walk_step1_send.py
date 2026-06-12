"""
Walkthrough Step 1 — 테스트 요청 1건 보내기
실행: python walk_step1_send.py
"""
import httpx, uuid

MARKER = "WALK" + uuid.uuid4().hex[:5].upper()
PROMPT = f"[{MARKER}] 최영희 010-1234-5678 페니실린 알레르기, 연봉 7409만원 인사팀"

print(f">>> 보낼 마커: {MARKER}")
print(f">>> 프롬프트: {PROMPT}\n")

r = httpx.post(
    "http://localhost:4000/v1/chat/completions",
    headers={
        "Authorization": "Bearer sk-1234",
        "Content-Type": "application/json",
    },
    json={
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": PROMPT}],
    },
    timeout=30,
)

print(f"<<< HTTP {r.status_code}")
try:
    out = r.json()["choices"][0]["message"]["content"]
    print(f"<<< 응답: {out[:200]}")
except Exception:
    print(f"<<< raw: {r.text[:200]}")

print(f"\n{'='*60}")
print(f"  이 마커를 외워둬:  MARKER = {MARKER}")
print(f"{'='*60}")
