# -*- coding: utf-8 -*-
"""apply_guardrail 경로 검증 (Test Playground 와 동일 엔드포인트)."""
import json
import httpx

TEXT = "김민우 주민번호 0208143233139 전화번호 01087009404"

print("=" * 60)
print("1) SIDECAR 직접 — 이 입력에서 뭐가 마스킹되나")
print("=" * 60)
r = httpx.post("http://pii-guardrail:8080/v1/pii/apply",
               json={"text": TEXT, "policy_profile": "strict"}, timeout=30)
d = r.json()
print("masked_text:", d.get("masked_text"))
for s in d.get("spans", []):
    print(f"  - {s['entity_type']:<14} {s['action']:<7} len={s['span_length']}")

print("\n" + "=" * 60)
print("2) GATEWAY /guardrails/apply_guardrail (Playground 와 동일)")
print("=" * 60)
rg = httpx.post("http://localhost:4000/guardrails/apply_guardrail",
                headers={"Authorization": "Bearer sk-1234"},
                json={"guardrail_name": "korean-pii", "text": TEXT}, timeout=30)
print("status:", rg.status_code)
print("body  :", json.dumps(rg.json(), ensure_ascii=False)[:400])
