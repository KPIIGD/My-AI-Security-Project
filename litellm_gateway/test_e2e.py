# -*- coding: utf-8 -*-
"""LiteLLM + Korean PII guardrail E2E 테스트 (컨테이너 내부 실행).

  docker exec litellm-litellm-1 python /app/config/test_e2e.py
"""
import json
import httpx

SIDECAR = "http://pii-guardrail:8080/v1/pii/apply"
GATEWAY = "http://localhost:4000/v1/chat/completions"
SAMPLE = "최영희 연봉 7409만원이고 전화는 010-1234-5678, 서울시 강남구 테헤란로 152에 살아요. 삼성전자 다님."


def show(title):
    print("\n" + "=" * 60)
    print(title)
    print("=" * 60)


# ── 1) 사이드카 직접 ──────────────────────────────────────
show("1) SIDECAR  /v1/pii/apply")
r = httpx.post(SIDECAR, json={"text": SAMPLE, "policy_profile": "strict"}, timeout=30)
data = r.json()
print("status      :", r.status_code)
print("ner_mode    :", data.get("ner_mode"))
print("blocked     :", data.get("blocked"))
print("masked_text :", data.get("masked_text"))
print("metrics     :", json.dumps(data.get("metrics"), ensure_ascii=False))
print("spans (no raw text — type/action/hash):")
for s in data.get("spans", []):
    print(f"  - {s['entity_type']:<14} {s['action']:<7} risk={s['risk_level']} "
          f"len={s['span_length']} hash={str(s.get('value_hash'))[:12]}")


# ── 2) 게이트웨이 전체 경로 ───────────────────────────────
show("2) GATEWAY  /v1/chat/completions  (guardrail pre_call 적용)")
try:
    rg = httpx.post(
        GATEWAY,
        headers={"Authorization": "Bearer sk-1234", "Content-Type": "application/json"},
        json={
            "model": "gpt-4o",
            "messages": [{"role": "user", "content": SAMPLE}],
            "max_tokens": 50,
        },
        timeout=60,
    )
    print("status:", rg.status_code)
    body = rg.json()
    if rg.status_code == 200:
        print("assistant:", body["choices"][0]["message"]["content"][:200])
    else:
        # 차단되었거나 LLM 호출 실패 — 어느 쪽이든 본문 출력
        print("body:", json.dumps(body, ensure_ascii=False)[:500])
except Exception as e:
    print("gateway 호출 예외:", type(e).__name__, str(e)[:200])
