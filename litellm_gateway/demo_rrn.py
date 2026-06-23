# -*- coding: utf-8 -*-
"""RRN 마스킹 동작 확인 — 어떤 포맷이 마스킹되나."""
import json
import httpx

GATEWAY = "http://localhost:4000"
HEAD = {"Authorization": "Bearer sk-1234", "Content-Type": "application/json"}

TESTS = [
    "주민번호 0208143233139",          # memory 에서 마스킹됐던 값(체크섬 유효, 하이픈X)
    "주민번호 020814-3233139",          # 위 값에 하이픈
    "주민번호 900101-2345678",          # 위 데모에서 안 잡힌 값
    "주민번호 880812-1234567",          # 임의
    "운전면허 11-12-345678-90 여권 M12345678",  # 기타 신분증
]

for text in TESTS:
    r = httpx.post(
        f"{GATEWAY}/guardrails/apply_guardrail",
        headers=HEAD,
        json={"guardrail_name": "korean-pii", "text": text},
        timeout=30,
    )
    out = r.json().get("response_text", r.text[:120])
    masked = out != text
    print(f"[{'MASK' if masked else ' -- '}] {text}")
    print(f"        -> {out}")
