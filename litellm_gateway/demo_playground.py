# -*- coding: utf-8 -*-
"""UI Guardrail Testing Playground 가 호출하는 엔드포인트 확인.
Playground 의 'Test 1 guardrail' 버튼 = POST /guardrails/apply_guardrail
"""
import json
import httpx

GATEWAY = "http://localhost:4000"
HEAD = {"Authorization": "Bearer sk-1234", "Content-Type": "application/json"}

SAMPLES = [
    "김민수 주민등록번호 900101-2345678, 전화 010-2345-6789, 서울시 강남구 테헤란로 152, 이메일 minsu.kim@gmail.com",
    "최영희 연봉 7409만원, 전화는 010-1234-5678, 삼성전자 다님",
]

for text in SAMPLES:
    r = httpx.post(
        f"{GATEWAY}/guardrails/apply_guardrail",
        headers=HEAD,
        json={"guardrail_name": "korean-pii", "text": text},
        timeout=30,
    )
    print("=" * 70)
    print("INPUT :", text)
    print("status:", r.status_code)
    try:
        body = r.json()
        print("OUTPUT:", json.dumps(body, ensure_ascii=False))
    except Exception:
        print("raw   :", r.text[:300])
