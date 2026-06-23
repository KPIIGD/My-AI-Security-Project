# -*- coding: utf-8 -*-
"""저장된 spend log 전체 JSON 에 원문 PII 가 남아있는지 전수 검사 (no-raw-PII 경계)."""
import json
import httpx

GATEWAY = "http://localhost:4000"
HEAD = {"Authorization": "Bearer sk-1234"}

# demo_check_log.py 가 보내는 원문에 들어있는 raw PII 토큰들
RAW_PII = ["김민수", "010-2345-6789", "01023456789", "minsu.kim@gmail.com",
           "테헤란로 152", "강남구"]

lr = httpx.get(f"{GATEWAY}/spend/logs", headers=HEAD, timeout=30)
logs = lr.json()
if not (isinstance(logs, list) and logs):
    print("no logs"); raise SystemExit

latest = sorted(logs, key=lambda x: x.get("startTime", ""))[-1]
blob = json.dumps(latest, ensure_ascii=False)

print("request_id:", latest.get("request_id"))
print("=" * 60)
leaks = [tok for tok in RAW_PII if tok in blob]
if leaks:
    print("RAW PII LEAK 발견:", leaks)
else:
    print("OK — 저장된 spend log 전체에 원문 PII 0건 (전부 마스킹됨)")
print("=" * 60)
# 마스킹 토큰이 실제로 들어있는지 (역검증)
masks = [m for m in ["[PERSON_1]", "[PHONE_1]", "[ADDRESS_1]", "[EMAIL_1]"] if m in blob]
print("로그에 존재하는 마스킹 토큰:", masks)
