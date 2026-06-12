import httpx, time, uuid

MARKER = "MWTRACE" + uuid.uuid4().hex[:6].upper()
print(f"[{time.strftime('%H:%M:%S')}] >>> MARKER={MARKER}")
resp = httpx.post(
    "http://localhost:4000/v1/chat/completions",
    headers={
        "Authorization": "Bearer sk-1234",
        "Content-Type": "application/json",
    },
    json={
        "model": "gpt-4o",
        "messages": [
            {"role": "user",
             "content": f"[{MARKER}] 최영희 연봉 7409만원. 부서는 인사팀."}
        ],
    },
    timeout=30,
)
print(f"[{time.strftime('%H:%M:%S')}] <<< {resp.status_code}")
print(f"MARKER={MARKER}")
