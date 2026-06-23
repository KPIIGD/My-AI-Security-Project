# -*- coding: utf-8 -*-
"""UI 상세 엔드포인트 /spend/logs/ui/{request_id} 응답 확인 — 클릭 시 화면에 뜨는 데이터."""
import json
import httpx

GATEWAY = "http://localhost:4000"
HEAD = {"Authorization": "Bearer sk-1234"}
RID = "chatcmpl-DtqddVPb4ZdqjMUi2KqgOekycPUJp"  # 마스킹된 최신 요청

r = httpx.get(f"{GATEWAY}/spend/logs/ui/{RID}", headers=HEAD,
              params={"start_date": "2026-06-23 00:00:00", "end_date": "2026-06-24 00:00:00"},
              timeout=20)
print("status:", r.status_code)
d = r.json()
print("keys:", sorted(d.keys()) if isinstance(d, dict) else type(d))
for f in ["messages", "response", "proxy_server_request"]:
    v = d.get(f) if isinstance(d, dict) else None
    s = json.dumps(v, ensure_ascii=False) if not isinstance(v, str) else v
    print(f"\n--- {f} ---")
    print(s[:500] if s else repr(v))
