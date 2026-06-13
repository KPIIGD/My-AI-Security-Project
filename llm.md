# LLM 컨텍스트 가이드

> **이 파일은 AI 어시스턴트(LLM)가 빠르게 프로젝트를 이해하도록 설계된 가이드입니다.**
> 사람이 읽는 소개는 `README.md`, 탐색 목차는 `목차.md`를 참조하세요.

---

## 프로젝트 정체성

**프로젝트명:** My AI Security Project  
**핵심 산출물:** `korean_pii_guardrail_v0_2` — 한국어 AI Gateway PII 가드레일 v0.2  
**언어:** Python (백엔드), TypeScript/React (프론트엔드)  
**패키지 구조:** `src/` 레이아웃 (`pyproject.toml` 기반)  

---

## 시스템 아키텍처 (M1~M9 파이프라인)

```
입력 텍스트
    │
    ▼
[M1] preprocess.py       — 한국어 정규화, 공백·유니코드 정리
    │
    ▼
[M2] regex_detectors.py  — 정규식 기반 PII 감지 (주민번호, 전화번호, 이메일 등)
    │
    ▼
[M3] korean_boundary.py  — 한국어 형태소 경계 보정 (조사 분리)
    │
    ▼
[M4] dictionary_detectors.py — 사전 기반 감지 (병원명, 기관명 등)
    │
    ▼
[M5] ner/owner_wrapper.py — NER 모델 (klue-roberta-large-v3) 기반 감지
    │
    ▼
[M6] span_resolver.py    — 중복/겹침 span 병합·해소
    │
    ▼
[M7] policy.py + masker.py — 정책 결정 + PII 마스킹 적용
    │
    ▼
[M8] audit_logger.py     — HMAC 서명 감사 로그 (JSONL)
    │
    ▼
[M9] pipeline.py         — GuardrailPipeline 통합 진입점
    │
    ▼
출력 (마스킹된 텍스트 + DetectionResult)
```

모든 모듈 경로: `korean_pii_guardrail_v0_2/src/pii_guardrail/`

---

## 핵심 클래스 / 함수 위치

| 클래스/함수 | 파일 | 역할 |
|------------|------|------|
| `GuardrailPipeline` | `pipeline.py` | M1→M9 통합 실행 |
| `KoreanPIIDetector` | `PII/layer_0/korean_pii_detector.py` | Layer 0 원형 |
| `KoreanNormalizer` | `PII/layer_0/korean_normalizer.py` | 정규화 원형 |
| `RegexDetector` | `regex_detectors.py` | 정규식 감지 |
| `DictionaryDetector` | `dictionary_detectors.py` | 사전 감지 |
| `NEROwnerWrapper` | `ner/owner_wrapper.py` | NER 래퍼 |
| `SpanResolver` | `span_resolver.py` | span 충돌 해소 |
| `PolicyRouter` | `policy.py` | 마스킹 정책 라우팅 |
| `Masker` | `masker.py` | 마스킹 실행 |
| `AuditLogger` | `audit_logger.py` | HMAC 감사 로그 |
| `ContextScorer` | `context_scorer.py` | 컨텍스트 신뢰도 스코어 |

---

## 감지 가능한 PII 엔티티 타입

`configs/entities.yaml` 참조. 주요 엔티티:

| 카테고리 | 엔티티 |
|----------|--------|
| 신원 | PERSON_NAME, RRN (주민등록번호) |
| 연락처 | PHONE, EMAIL, ADDRESS |
| 금융 | BANK_ACCOUNT, CARD_NUMBER |
| 의료 | MEDICAL_RECORD, PRESCRIPTION |
| 기관 | CORPORATE_NAME, ORGANIZATION |
| 식별자 | EMPLOYEE_ID, PASSPORT_NO, DRIVER_LICENSE |

---

## 설정 파일 구조

```
configs/
├── entities.yaml        — 엔티티 타입 정의
├── detectors.yaml       — 각 감지기 활성화·임계값
├── scoring.yaml         — 신뢰도 스코어 가중치
├── policy_profiles.yaml — 정책 프로파일 (strict / balanced / permissive)
├── context_rules.yaml   — 컨텍스트 규칙 (조사·단어 문맥 기반)
├── dictionaries.yaml    — 사전 경로 설정
└── josa_rules.yaml      — 한국어 조사 규칙
```

---

## API 계약

**요청 스키마:** `schemas/guardrail_request.schema.json`
**응답 스키마:** `schemas/guardrail_response.schema.json`
**OpenAPI 명세:** `api/openapi.yaml`
**FastAPI 서버:** `api_service/app.py` (기본 포트: 8000)

---

## 데이터 흐름 다이어그램

```
[사용자 입력]
     │
     ├──▶ [api_service/app.py]  (REST API 경로)
     │           │
     │           ▼
     └──▶ [demo/app.py]         (Gradio UI 경로)
                 │
                 ▼
         [pipeline.py:GuardrailPipeline.run()]
                 │
         ┌───────┴──────────────────────┐
         │    M1~M8 순차 실행           │
         └───────┬──────────────────────┘
                 │
         ┌───────▼───────┐
         │  DetectionResult│
         │  - spans[]     │  ← 감지된 PII 위치·타입·신뢰도
         │  - masked_text │  ← 마스킹 완료 텍스트
         │  - policy_action│ ← BLOCK / MASK / ALLOW
         │  - audit_hash  │  ← HMAC 서명
         └───────────────┘
```

---

## 테스트 전략

```
tests/
├── test_pipeline.py          — end-to-end 파이프라인 통합 테스트
├── test_regex_detectors.py   — M2 정규식 감지 단위 테스트
├── test_dictionary_detectors.py — M4 사전 감지 단위 테스트
├── test_span_resolver.py     — M6 span 병합 단위 테스트
├── test_masker.py            — M7 마스킹 단위 테스트
├── test_audit_logger.py      — M8 감사 로그 단위 테스트
├── test_context_scorer.py    — 컨텍스트 스코어 단위 테스트
├── test_contract_smoke.py    — API 계약 스모크 테스트
└── test_release_gate_generation.py — 릴리즈 게이트 생성 테스트
```

**실행:** `cd korean_pii_guardrail_v0_2 && pytest tests/`

---

## 평가 시스템

```
scripts/run_eval.py           — 단계별 평가 실행
scripts/run_release_gate.py   — 릴리즈 게이트 판정
reports/eval_v0_2.json        — 최신 평가 결과
reports/release_gate_v0_2.json — 릴리즈 게이트 결과
```

**릴리즈 기준 (`audit_safety_release_gate_v0_2.json`):**
- F1 ≥ 0.90 per entity stage
- False Positive Rate ≤ 10%

---

## 연구 실험 (PII/)

초기 4-way 비교: Layer 0 (Regex) vs Layer 1 (Claude API) vs Layer 2 (LiteLLM) vs Layer 4 (Custom)

- 측정 지표: F1, Precision, Recall, Latency (ms)
- 결과: `PII/results/` (phase 1~6)
- 퍼저: `PII/fuzzer/korean_pii_fuzzer_v4.py` (10K+ 합성 PII 데이터 생성)

---

## CI/CD

```
.github/workflows/
├── layer_0_tests.yml    — Layer 0 pytest (PR마다 실행)
├── claude-review.yml    — Claude AI 코드 리뷰
└── security-review.yml  — 보안 리뷰
```

---

## 코드 검색 힌트

- **PII 감지 로직 수정** → `src/pii_guardrail/regex_detectors.py` 또는 `dictionary_detectors.py`
- **새 엔티티 추가** → `configs/entities.yaml` + `configs/detectors.yaml`
- **마스킹 규칙 변경** → `configs/policy_profiles.yaml` + `src/pii_guardrail/masker.py`
- **API 엔드포인트** → `api_service/app.py`
- **데모 UI** → `demo/app.py` (Gradio) 또는 `web/src/` (React)
- **평가 결과 조회** → `reports/` 폴더 JSON 파일들
- **Layer 0 원형 코드** → `PII/layer_0/korean_pii_detector.py`

---

_생성: 2026-06-14_
