# -*- coding: utf-8 -*-
import httpx, json
r = httpx.post(
    "http://localhost:4000/v1/chat/completions",
    headers={"Authorization": "Bearer sk-1234", "Content-Type": "application/json"},
    json={
        "model": "gpt-4o",
        "messages": [{"role": "user", "content": "김민수 전화 010-2345-6789 서울시 강남구 테헤란로 152 minsu.kim@gmail.com"}],
        "max_tokens": 80,
    },
    timeout=60,
)
print("status", r.status_code)
print(json.dumps(r.json(), ensure_ascii=False)[:800])
