# My AI Security Project

> 한국어 AI Gateway에서 PII(개인정보)를 실시간으로 감지·마스킹하는 가드레일 시스템.
> 정규식 → 사전 → NER → 컨텍스트 스코어 → 정책 → 마스킹의 M1~M9 파이프라인으로 구성.
> Python 패키지명: `pii_guardrail` | 서비스 포트: 8000 | 데모 포트: 7860

---

## ⚠️ 먼저 읽어야 할 주의사항

- **span은 직접 정렬하지 말 것** — `span_resolver.py`가 중복/겹침을 처리. 직접 sort하면 복합 엔티티가 깨짐
- **`configs/`를 수정하면 반드시 pytest 재실행** — YAML 변경이 감지 로직에 즉시 반영됨
- **`ner/mock_ner.py`는 테스트 전용** — 실제 추론은 `ner/owner_wrapper.py` (KLUE-RoBERTa-Large-v3)
- **`src/pii_guardrail/generated/`는 건드리지 말 것** — 자동 생성 파일
- **M1~M9 순서는 변경 불가** — 각 단계가 이전 단계 출력에 의존
- **`[Unreleased]` 섹션은 `CHANGELOG.md`에서 관리** — 폴더 `히스토리.md`에 버전 이력 쓰지 말 것

---

## 기술 스택

| 계층 | 기술 | 버전 |
|------|------|------|
| 언어 | Python | 3.11+ |
| 패키지 관리 | pyproject.toml (uv/pip) | — |
| 코어 라이브러리 | `pii_guardrail` (src layout) | v0.2 |
| NER 모델 | KLUE-RoBERTa-Large-v3 | HuggingFace |
| API 서버 | FastAPI + Uvicorn | 최신 |
| 데모 UI | Gradio | 3탭 |
| 콘솔 UI | React + Vite + Tailwind | TypeScript |
| 설정 | YAML (configs/) | — |
| 테스트 | pytest | — |
| CI | GitHub Actions | — |

---

## 실행 명령어

```bash
# 패키지 설치 (korean_pii_guardrail_v0_2/ 에서)
pip install -e .

# 전체 테스트 실행
pytest tests/

# 단일 테스트 파일 (반복 작업 시)
pytest tests/test_pipeline.py -v

# 타입 체크
mypy src/

# 린트
ruff check src/

# 평가 파이프라인
python scripts/run_eval.py

# 릴리즈 게이트 판정
python scripts/run_release_gate.py

# Gradio 데모 실행 (포트 7860)
cd demo && python app.py

# FastAPI 서버 (포트 8000)
cd api_service && uvicorn app:app --reload

# React 콘솔 UI (포트 5173)
cd web && npm install && npm run dev
```

---

## 아키텍처 (M1~M9 파이프라인)

```
입력 텍스트
    │
    ▼
[M1] preprocess.py        유니코드 정규화, 공백 정리, 한글 NFC 변환
    │
    ▼
[M2] regex_detectors.py   정규식 감지 — RRN, 전화번호, 이메일, 카드번호 등
    │
    ▼
[M3] korean_boundary.py   형태소 경계 보정 — 조사(은/는/이/가) 분리
    │
    ▼
[M4] dictionary_detectors.py + context_scorer.py
                          사전 감지 + 컨텍스트 신뢰도 스코어링
    │
    ▼
[M5] ner/owner_wrapper.py KLUE-RoBERTa-Large-v3 NER 추론
    │
    ▼
[M6] span_resolver.py     중복·겹침 span 병합, 복합 엔티티 처리
    │
    ▼
[M7] policy.py + masker.py 정책 결정(BLOCK/MASK/ALLOW) + 마스킹 실행
    │
    ▼
[M8] audit_logger.py      HMAC-SHA256 서명 감사 로그 (JSONL sink)
    │
    ▼
[M9] pipeline.py          GuardrailPipeline — M1~M8 통합 진입점
    │
    ▼
DetectionResult { masked_text, spans[], policy_action, audit_hash }
```

---

## 디렉토리 → 역할 맵

| 경로 | 역할 | 수정 시 주의 |
|------|------|------------|
| `src/pii_guardrail/` | 핵심 라이브러리 | 변경 후 pytest 필수 |
| `configs/` | 감지·정책 YAML 설정 | 변경 즉시 적용 (재시작 불필요) |
| `tests/` | pytest 스위트 | 커버리지 유지 필수 |
| `scripts/` | 평가·릴리즈 게이트 | 결과는 `reports/`에 자동 저장 |
| `reports/` | 평가 결과 JSON | 직접 편집 금지 (자동 생성) |
| `api_service/` | FastAPI REST 서버 | `schemas/`와 계약 동기화 필수 |
| `demo/` | Gradio 데모 | raw PII 클라이언트 전송 금지 |
| `web/` | React 콘솔 UI | `npm run typecheck` 후 PR |
| `schemas/` | JSON Schema 계약 | `api_service/models.py`와 동기화 |
| `docs/` | 설계 명세 00~18 | 추가 시 번호 순서 유지 |

---

## 컨벤션

```
엔티티 타입:   SCREAMING_SNAKE_CASE    예) PERSON_NAME, BANK_ACCOUNT
파이썬 파일:   snake_case.py
클래스:        PascalCase
함수/변수:     snake_case
TypeScript:    PascalCase (컴포넌트), camelCase (함수/변수)
커밋 메시지:   Conventional Commits — feat:, fix:, chore:, docs:, refactor:, test:
브랜치:        feature/<이름>, fix/<이름>, chore/<이름>
```

---

## 흔한 작업 패턴

### 새 PII 엔티티 타입 추가
```
1. configs/entities.yaml      → 엔티티 타입 정의 추가
2. configs/detectors.yaml     → 해당 감지기 활성화·임계값 설정
3. src/.../regex_detectors.py 또는 dictionary_detectors.py → 감지 로직 구현
4. tests/test_regex_detectors.py 또는 test_dictionary_detectors.py → 단위 테스트 추가
5. pytest tests/ && python scripts/run_eval.py → 검증
```

### 정책 변경 (마스킹 강도 조정)
```
1. configs/policy_profiles.yaml → 프로파일 수정 (strict/balanced/permissive)
2. pytest tests/test_policy.py  → 정책 테스트 확인
3. python scripts/run_release_gate.py → 릴리즈 게이트 통과 확인
```

### 새 API 엔드포인트 추가
```
1. api_service/app.py     → 라우터 추가
2. api_service/service.py → 비즈니스 로직
3. api_service/models.py  → Pydantic 모델
4. schemas/               → JSON Schema 업데이트
5. api/openapi.yaml       → OpenAPI 명세 동기화
6. tests/test_console_api.py → API 테스트 추가
```

---

## 용어집 (도메인 특수 용어)

| 용어 | 의미 |
|------|------|
| **span** | (start, end, label, confidence) 튜플 — 텍스트 내 PII 위치 |
| **guardrail** | 입력/출력 검사 레이어 전체 시스템 |
| **release gate** | 릴리즈 전 자동 품질 판정 (F1 ≥ 0.90, FPR ≤ 10%) |
| **Layer 0~4** | `PII/` 폴더의 초기 실험 레이어 (v0.2 제품과 별개) |
| **M1~M9** | 파이프라인 처리 단계 번호 |
| **RRN** | Resident Registration Number (주민등록번호) |
| **FP / FN** | False Positive / False Negative |
| **ablation** | 특정 컴포넌트 제거 후 성능 변화 측정 실험 |
| **marker eval** | 마커 기반 평가 — 감지 위치의 정확성 측정 |
| **audit hash** | HMAC-SHA256 서명 — 감사 로그 위변조 방지 |
| **조사** | 한국어 문법 조사 (은/는/이/가 등) — 경계 보정 대상 |

---

## 절대 하지 말 것

- `reports/` JSON 파일 직접 수정 — 자동 생성 파일이므로 스크립트로만 갱신
- `mock_ner.py`를 프로덕션 경로에 사용 — 테스트 전용
- span을 `span_resolver.py` 외부에서 직접 정렬/병합 — 복합 엔티티 손상 위험
- `configs/` 변경 후 pytest 생략 — YAML 오타가 런타임 오류로 이어짐
- `demo/app.py`에서 raw PII를 클라이언트 응답에 포함 — 보안 정책 위반
- `--no-verify` 커밋 — pre-commit hook은 필수 (린트·타입 체크 포함)
- `ANY` TypeScript 타입 사용 — `unknown`으로 대체 후 타입 가드 작성

---

## 핵심 파일 링크

- [파이프라인 진입점](korean_pii_guardrail_v0_2/src/pii_guardrail/pipeline.py): GuardrailPipeline.run() — M1→M9 통합 실행
- [엔티티 타입 정의](korean_pii_guardrail_v0_2/configs/entities.yaml): 감지 가능한 모든 PII 타입 목록
- [감지기 설정](korean_pii_guardrail_v0_2/configs/detectors.yaml): 각 감지기 활성화·임계값
- [정책 프로파일](korean_pii_guardrail_v0_2/configs/policy_profiles.yaml): strict/balanced/permissive 정책 정의
- [아키텍처 명세](korean_pii_guardrail_v0_2/docs/02_ARCHITECTURE_SPEC.md): 상세 설계 문서
- [API 서버](korean_pii_guardrail_v0_2/api_service/app.py): FastAPI 라우터 진입점
- [릴리즈 게이트 결과](korean_pii_guardrail_v0_2/reports/release_gate_v0_2.json): 최신 품질 판정 결과
- [Layer 0 원형](PII/layer_0/korean_pii_detector.py): 정규식 감지기 초기 구현체
- [퍼저](PII/fuzzer/korean_pii_fuzzer_v4.py): 합성 한국어 PII 데이터 생성기

---

## Optional

- [OpenAPI 명세](korean_pii_guardrail_v0_2/api/openapi.yaml): REST API 전체 계약
- [스코어링 정책](korean_pii_guardrail_v0_2/docs/03_SCORING_POLICY_SPEC.md): 신뢰도 계산 상세
- [FP 분석](korean_pii_guardrail_v0_2/docs/15_FALSE_POSITIVE_ANALYSIS_AND_TEST_EXPANSION_PLAN.md): 오탐 분석 및 테스트 확장 계획
- [논문 본문](paper/capstone_main_v1.md): 캡스톤 학술 논문 전체

---

_포맷: [llms.txt](https://llmstxt.org) + [AGENTS.md](https://agents.md) 표준 참고 | 업데이트: 2026-06-14_
