# n8n 자동화 — 데이터센터 정제 파이프라인

n8n(오케스트레이터)이 cron 으로 **수집→정제→큐레이션→누수게이트→export** 를 자동 실행한다.

## 구조
```
n8n (Docker, :5678)  --HTTP-->  pipeline_api.py (호스트, :8000)  -->  datacenter/*.py
                                  (host.docker.internal:8000)
```
n8n 컨테이너는 호스트 파이썬을 직접 못 돌리므로, 호스트의 FastAPI(`pipeline_api.py`)를
HTTP 로 호출한다.

## 1회 셋업

### (a) 파이프라인 API 띄우기 (호스트)
```powershell
cd C:\My-AI-Security-Project\PII\ner
python datacenter/pipeline_api.py        # http://localhost:8000 (계속 켜둠)
```
확인: http://localhost:8000/health → `{"ok":true}`

### (b) Milvus 띄우기 (큐레이션용)
```powershell
cd C:\My-AI-Security-Project\PII\ner\datacenter\milvus
docker compose up -d
```

### (c) n8n 띄우기 + 계정
```powershell
cd C:\My-AI-Security-Project\PII\ner\datacenter\n8n
docker compose up -d
```
→ http://localhost:5678 접속 → **첫 화면에서 owner 계정 생성**(이메일/비번, 로컬용).

### (d) 워크플로 import
n8n UI → 좌상단 **⋯ → Import from File** → `datacenter/n8n/datacenter_pipeline.workflow.json`
→ 들어오면 노드 5개(Schedule → Stats → Leakage Gate → Curate → Export) 보임.

## 실행
- **수동 테스트**: 워크플로 열고 우상단 **Execute Workflow** → 각 노드가 호스트 API 호출하는지 확인.
- **자동**: 우상단 **Active** 토글 ON → Weekly Schedule(매주 1회)대로 자동 실행.

## 엔드포인트 (pipeline_api.py)
| 메서드 | 경로 | 동작 |
|--------|------|------|
| GET | `/health` | 헬스체크 |
| GET | `/stats` | DB 실 건수(COUNT) |
| POST | `/leakage_gate` | KLUE 누수 검사 |
| POST | `/curate?source=&limit=&threshold=` | Milvus 다양성 큐레이션 |
| POST | `/export` | 깨끗한 학습셋 export |

## 주의
- 워크플로 기본 `curate` 는 `limit=2000`(빠른 데모). 전체는 limit 키우기(임베딩 느림 → GPU 권장).
- n8n 컨테이너→호스트 접근은 `host.docker.internal` (compose 에 `extra_hosts` 로 설정됨).
- 안 쓸 때: `docker compose down` (n8n / milvus 각각).
