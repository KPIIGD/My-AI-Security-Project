# -*- coding: utf-8 -*-
"""전체 spend log 중 원문 PII 가 남은 (수정 전) 항목 수 집계 + UI 접근성 확인."""
import json
import httpx

GATEWAY = "http://localhost:4000"
HEAD = {"Authorization": "Bearer sk-1234"}
RAW_PII = ["김민수", "010-2345-6789", "minsu.kim@gmail.com", "테헤란로 152"]

lr = httpx.get(f"{GATEWAY}/spend/logs", headers=HEAD, timeout=30)
logs = lr.json()
logs = logs if isinstance(logs, list) else []
leak_ids, clean_ids = [], []
for lg in logs:
    blob = json.dumps(lg, ensure_ascii=False)
    if any(tok in blob for tok in RAW_PII):
        leak_ids.append(lg.get("request_id"))
    elif "[PERSON_1]" in blob or "[PHONE_1]" in blob:
        clean_ids.append(lg.get("request_id"))

print(f"총 spend log: {len(logs)}")
print(f"원문 PII 남은(수정 전) 항목: {len(leak_ids)}")
print(f"마스킹된(수정 후) 항목     : {len(clean_ids)}")
print("leak ids:", leak_ids)

# UI 접근성
try:
    u = httpx.get(f"{GATEWAY}/ui/", timeout=10, follow_redirects=True)
    print("UI status:", u.status_code, "| len:", len(u.text))
except Exception as e:
    print("UI err:", type(e).__name__, str(e)[:120])
