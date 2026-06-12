# Korean PII Guardrail Capstone — Claude Code Onboarding

> **읽는 순서:** 이 문서 전체를 먼저 읽고, 그다음 `/mnt/user-data/outputs/` 대신 `C:\litellm\` 경로에서 작업 시작.

---

## 1. 프로젝트 한 줄 요약

**LiteLLM Gateway 한국어 PII 가드레일 평가 + 방어 캡스톤.** 4계층(Presidio→Bedrock→Lakera→GPT-4o Judge)에 한국어 특화 Layer 0(정규화+탐지)을 추가해서 한국어 텍스트형 PII 우회 문제를 해결하는 연구.

- **담당자:** 민우 (정보보안학과 학부생, CCIT 융합전공)
- **지도교수:** 임정묵
- **언어:** Windows PC (PowerShell), Python 3.12, Docker
- **작업 경로:** `C:\litellm\`

---

## 2. 현재 상태 (2026-04-18 기준)

### ✅ 완료
- Docker Compose로 LiteLLM + PostgreSQL + Presidio Analyzer/Anonymizer 구축 완료
- Layer 1 Presidio, Layer 2 Bedrock, Layer 3 Lakera, Layer 4 GPT-4o Judge 구현 완료
- 8,400건 퍼저 데이터로 평가 완료 (`eval_l1l3.json`, `eval_full.json`)
- 엑셀 전체 데이터 export (`eval_complete_data.xlsx`, 10 시트)
- **Layer 0 독립 실행 완료:**
  - `korean_normalizer.py` (13단계 정규화 파이프라인)
  - `korean_pii_detector.py` (33종 PII 탐지: 정규식 17 + 키워드 사전 16)
  - `korean_layer0_guardrail.py` (LiteLLM CustomGuardrail 래퍼)
- **A/B 테스트 결과:** Layer 0 추가 시 **1,193건 중 310건 복구 (26.0%p 개선)**
  - L2 Encoding 62.8% 복구 (최대 효과)
  - L3 Format 46.5% 복구
  - L5 Context / 텍스트형 PII는 여전히 0% (Layer 0로 해결 불가)
- **LiteLLM 통합 99% 완료:**
  - `CustomGuardrail` 상속, `async_pre_call_hook` / `async apply_guardrail` 구현
  - config.yaml에 `korean-layer0` 등록
  - 컨테이너 정상 기동, `/health/liveness` OK

### ⚠️ 진행 중 (바로 다음 할 일)
**문제:** `/guardrails/apply_guardrail` API가 커스텀 `apply_guardrail` 메서드를 호출하지 않음. 모든 요청이 200 OK로 통과되고 PII가 BLOCK되지 않음 (PASS 상태로 반환).

**증거:**
```powershell
# 이걸 넣었는데도 PASS로 나옴:
python -c "import httpx; r=httpx.post('http://localhost:4000/guardrails/apply_guardrail', headers={'Authorization':'Bearer sk-1234','Content-Type':'application/json'}, json={'guardrail_name':'korean-layer0','text':'최영희 연봉 7409만원'}); print(r.status_code, r.text[:200])"
# 결과: 200 {"response_text":"최영희 연봉 7409만원"}  ← 원본 그대로 반환
```

**다음 조사 포인트:**
1. `/app/litellm/proxy/guardrails/guardrail_endpoints.py` 읽어서 `/guardrails/apply_guardrail` 엔드포인트가 커스텀 클래스의 어떤 메서드를 호출하는지 확인
2. 참고 샘플: `presidio.py`, `bedrock_guardrails.py`, `generic_guardrail_api.py` 의 `apply_guardrail` 구현 패턴
3. 가능성: LiteLLM이 `async_pre_call_hook`은 실제 LLM 호출 때만 작동하고, `/apply_guardrail` 엔드포인트는 별도 로직일 수 있음

---

## 3. 환경 세팅

### Docker 컨테이너 구성
```
litellm_default 네트워크
  ├── litellm-litellm-1  (포트 4000, LiteLLM Proxy v1.82)
  ├── litellm-db-1       (PostgreSQL 16, 포트 5432 내부)
  ├── presidio-analyzer  (포트 5001→3000)
  └── presidio-anonymizer (포트 5002→3000)
```

### 실행 명령어 모음
```powershell
cd C:\litellm

# 전체 기동
docker compose up -d
docker start presidio-analyzer presidio-anonymizer

# 상태 확인
docker ps --format "table {{.Names}}\t{{.Status}}"
curl.exe http://localhost:4000/health/liveness

# 로그 확인
docker logs --tail 30 litellm-litellm-1

# 파일 배포 → 재시작 사이클
docker cp korean_layer0_guardrail.py litellm-litellm-1:/app/korean_layer0_guardrail.py
docker cp config.yaml litellm-litellm-1:/app/config.yaml
docker compose restart litellm  # 서비스 이름은 "litellm"이지 "litellm-litellm-1" 아님
Start-Sleep 15
curl.exe http://localhost:4000/health/liveness
```

### ⚠️ 중요: 인코딩 주의사항
- PowerShell에서 `curl.exe`로 한국어 JSON 보내면 **한글 깨짐** → Python `httpx` 사용할 것
- PowerShell `-replace`로 config.yaml 편집하면 **UTF-8 한글 주석 깨짐** → 파일 새로 작성
- config.yaml 한글 주석은 `-- Layer 0 --` 같은 영어로 쓸 것

---

## 4. LiteLLM API 구조 (조사 결과)

### ✅ 발견된 것
- LiteLLM 버전: 현재 컨테이너 내부 (v1.82)
- `CustomGuardrail` 위치: `litellm.integrations.custom_guardrail` (proxy.guardrails.guardrail_hooks 아님!)
- `GuardrailEventHooks` 위치: `litellm.types.guardrails` → 값: `pre_call`, `during_call`, `post_call`, `logging_only`, `pre_mcp_call`, `during_mcp_call`, `realtime_input_transcription`
- `GenericGuardrailAPIInputs` 위치: `litellm.integrations.custom_guardrail` (types.guardrails 아님!)
  - 필드: `texts: List[str]`, `images`, `tools`, `tool_calls`, `structured_messages`, `model: Optional[str]`
- `apply_guardrail` 시그니처:
  ```python
  async def apply_guardrail(
      self,
      inputs: GenericGuardrailAPIInputs,
      request_data: dict,
      input_type: Literal["request", "response"],
      logging_obj: Optional["LiteLLMLoggingObj"] = None,
  ) -> GenericGuardrailAPIInputs:
      return inputs
  ```

### ❌ 존재하지 않는 것
- `litellm.proxy.guardrails.guardrail_hooks.GuardrailCallback` (과거 버전)
- `litellm.__version__` (속성 없음)

### 현재 Layer 0 클래스 구조
```python
# korean_layer0_guardrail.py
from litellm.integrations.custom_guardrail import CustomGuardrail
from litellm.types.guardrails import GuardrailEventHooks

class KoreanLayer0Guard(CustomGuardrail):
    def __init__(self, **kwargs):
        self.layer0 = KoreanLayer0(mode="block", threshold=1)
        self.event_hook = GuardrailEventHooks.pre_call
        super().__init__(**kwargs)

    async def async_pre_call_hook(self, data, user_api_key_dict, call_type):
        # LLM 호출 직전에 input messages 검사 - 잘 동작함 (로컬 데모 OK)

    async def apply_guardrail(self, inputs, request_data, input_type, logging_obj=None):
        # /guardrails/apply_guardrail API용 - 현재 호출되지 않는 듯
```

---

## 5. 핵심 파일 목록 (`C:\litellm\`)

### Python 모듈
| 파일 | 용도 |
|------|------|
| `korean_normalizer.py` | 13단계 정규화 파이프라인 (jamo, NFKC, zwsp 제거 등) |
| `korean_pii_detector.py` | 33종 PII 탐지 (regex 17 + 키워드 사전 16) |
| `korean_layer0_guardrail.py` | LiteLLM CustomGuardrail 래퍼 |
| `custom_guardrail.py` | Layer 4 GPT-4o Judge |
| `guardrail_evaluator.py` | 퍼저 데이터 → 평가 결과 JSON |
| `cascade_evaluator.py` | Layer 4 Cascade 평가 (L1-L3 우회 케이스만 L4 투입) |
| `analyze_true_detection.py` | TRUE/FALSE/BYPASS 질적 분류기 |
| `layer0_ab_test.py` | Layer 0 on/off A/B 비교 |

### 설정/데이터
| 파일 | 용도 |
|------|------|
| `config.yaml` | LiteLLM 가드레일 설정 (Layer 0~4) |
| `docker-compose.yml` | Docker 구성 |
| `eval_l1l3.json` | 3계층 평가 원본 (8,400건, 12MB) |
| `eval_full.json` | Layer 4 Cascade 추가 결과 |
| `eval_complete_data.xlsx` | 엑셀 10시트 종합 (1.3MB) |
| `dashboard.html` | Brutalist 스타일 시각화 |

---

## 6. 데이터 핵심 수치 (논문용)

### 전체 탐지율
- 총 8,400 케이스 (95종 PII × 36 변이 × L0-L5 레벨)
- Before Layer 4: 한국어 우회율 32.5%, 전체 TRUE 78.5%
- After Layer 4 Cascade: 한국어 우회율 21.3%, 전체 TRUE 85.8%
- Real Bypass (FALSE + BYPASS): 14.2%

### 한국어 vs 영어 (숫자형 PII만)
- KR 숫자형: 89.2% TRUE / 10.8% 우회
- EN 숫자형: 99.2% TRUE / 0.8% 우회
- **L2 Encoding 격차 12.7배** (KR 34.2% vs EN 2.7%)

### 텍스트형 PII (한국어 전용, 32종)
- 전체 68.1% 우회 — 가드레일이 거의 탐지 못함
- 이게 Layer 0 키워드 사전의 핵심 타겟

### Layer 0 효과 (A/B 테스트, 1,193건)
| 구간 | 복구율 |
|------|--------|
| L0 Original | 0% |
| L1 Character | 20.6% |
| **L2 Encoding** | **62.8%** ← 최대 |
| L3 Format | 46.5% |
| L4 Linguistic | 16.5% |
| L5 Context | 0% ← 문맥 공격은 해결 불가 |
| **전체** | **26.0%p 개선** |

---

## 7. 논문 스토리라인 (3막 구조)

- **Act 1 — 공격**: 한국어 퍼저로 8,400건 변이 생성, 프로덕션 가드레일 우회 입증
- **Act 2 — 분석**: Root cause 파헤침. "한국어 우회"보다 "텍스트형 PII 우회"가 본질
  - 숫자 PII는 한국어도 89% 탐지
  - 텍스트형 PII (allergy, surgery, salary 등)는 68% 우회 — 영어 중심 가드레일의 근본 한계
- **Act 3 — 방어**: Layer 0 (정규화 + 한국어 PII 키워드 사전) 제안
  - L2 Encoding 62.8% 복구, 전체 26%p 개선
  - 한계: L5 Context 공격과 RAG 삽입은 여전히 해결 불가 → 향후 과제

**Working thesis:** "We demonstrate that production PII guardrails are significantly vulnerable to Korean-language adversarial mutations, and propose a morphological normalization + keyword detection layer that recovers detection rates by 26.0%p."

---

## 8. 병행 프로젝트 (민우 다른 작업)

- **AI 모델 공급망 보안 캡스톤**: HuggingFace 화이트리스트 파이프라인
- **KoJailFuzz**: 독자 개발한 한국어 LLM 탈옥 퍼징 프레임워크
- **MCP 에이전트 침투 캡스톤**: Claude Code, Cursor, Windsurf 대상 악성 MCP
- **주식/코인 자동매매**: `C:\finence\` 별도 프로젝트

이 캡스톤은 `C:\litellm\`만 건드리면 됨. `C:\finence`와 혼동 금지.

---

## 9. 당장 다음 할 일 (우선순위 순)

### 🔴 최우선
**`/guardrails/apply_guardrail` API가 커스텀 메서드를 호출하지 않는 문제 해결**

조사 명령어:
```powershell
# 엔드포인트 구현 읽기
docker exec litellm-litellm-1 cat /app/litellm/proxy/guardrails/guardrail_endpoints.py | Select-String "apply_guardrail" -Context 5

# 참고 샘플 읽기
docker exec litellm-litellm-1 cat /app/litellm/proxy/guardrails/guardrail_hooks/presidio.py | Select-String "apply_guardrail" -Context 3
docker exec litellm-litellm-1 cat /app/litellm/proxy/guardrails/guardrail_hooks/generic_guardrail_api/generic_guardrail_api.py
```

가설:
1. 엔드포인트가 `run_guardrail` 같은 다른 메서드를 호출할 수도 있음
2. `event_hook` 값에 따라 분기될 수도 있음
3. 그냥 `default_on: true`를 config에 추가해야 할 수도 있음

### 🟡 그다음
1. Layer 0 실제 LLM 요청 경로로 통합 테스트 (`/v1/chat/completions` 호출)
2. Layer 0 추가한 상태로 전체 8,400건 재평가
3. 대시보드(`dashboard.html`)에 Layer 0 섹션 추가

### 🟢 논문 작업
1. 방법론 섹션: 퍼저 설계 + Layer 0 아키텍처
2. 실험 결과: Before/After 비교 표, 히트맵
3. 한계 및 향후 과제: L5 Context, ctx_json 공격

---

## 10. 디버깅 히스토리 (삽질 방지용)

- ❌ `from litellm.proxy.guardrails.guardrail_hooks import GuardrailCallback` → 구 버전 경로. 실제로는 `CustomGuardrail`이 `litellm.integrations.custom_guardrail`에 있음
- ❌ config.yaml에 Layer 0 등록하고 import 실패 시 컨테이너가 즉시 죽음 → 복구 시 Layer 0 먼저 주석처리 후 alive 확인 → 재등록
- ❌ PowerShell `-replace`로 yaml 편집 시 한글 주석 깨짐 + 다른 `mode: "pre_call"`도 같이 주석처리됨 → 파일 새로 작성
- ❌ `apply_guardrail`을 sync로 만들면 "object dict can't be used in 'await' expression" 500 에러 → 반드시 `async def`
- ❌ `apply_guardrail(self, **kwargs)` 시그니처로 만들면 호출은 되지만 빈 응답 → 실제는 `(self, inputs, request_data, input_type, logging_obj)` 시그니처
- ❌ `docker compose restart litellm-litellm-1` → "no such service". 서비스 이름은 `litellm` (컨테이너 이름이 `litellm-litellm-1`인 것과 다름)
- ❌ Docker 재시작 후 즉시 `curl`하면 "Empty reply" → `Start-Sleep 15` 필요

---

## 11. 새 채팅에서 Claude Code에게 해줄 말 (템플릿)

```
한국어 PII 가드레일 캡스톤 프로젝트 작업 중이야. C:\litellm 폴더에
CLAUDE.md 읽어보면 전체 맥락 있어. 그거 먼저 읽고 시작하자.

지금 내가 하려는 건: [여기에 구체적 작업 적기]
```
