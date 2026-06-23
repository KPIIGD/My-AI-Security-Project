# -*- coding: utf-8 -*-
"""Playground 시연용 최종 샘플 — 모든 PII 가 깔끔하게 마스킹되는지 확인."""
import json
import httpx

GATEWAY = "http://localhost:4000"
HEAD = {"Authorization": "Bearer sk-1234", "Content-Type": "application/json"}

SAMPLE = "안녕하세요, 김민수입니다. 주민번호는 020814-3233139, 전화 010-2345-6789, 서울시 강남구 테헤란로 152에 살고, 이메일은 minsu.kim@gmail.com 입니다."

r = httpx.post(
    f"{GATEWAY}/guardrails/apply_guardrail",
    headers=HEAD,
    json={"guardrail_name": "korean-pii", "text": SAMPLE},
    timeout=30,
)
out = r.json().get("response_text")
print("INPUT :", SAMPLE)
print("OUTPUT:", out)

# raw PII 잔존 검사
RAW = ["김민수", "020814-3233139", "010-2345-6789", "테헤란로 152", "minsu.kim@gmail.com"]
leaks = [t for t in RAW if t in out]
print("\n원문 PII 잔존:", leaks if leaks else "없음 (전부 마스킹됨)")
