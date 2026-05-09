# Korean PII Guardrail GitHub 운영 규칙 및 증빙 관리 가이드

Version: v0.2-single-turn  
Target project: `korean_pii_guardrail_v0_2`

## 문서 목적

이 문서는 Korean PII Guardrail v0.2 팀이 GitHub에서 작업할 때 지켜야 할 운영 규칙과 개발 증빙 관리 기준을 정리한다.

목표는 다음과 같다.

1. 브랜치 혼선과 Git 충돌을 줄인다.
2. AI가 생성한 코드를 검증 없이 반영하는 위험을 줄인다.
3. 누가 무엇을 왜 수정했는지 PR과 commit 기록으로 남긴다.
4. 평가, 보고서, 발표, 논문 작성에 필요한 증빙을 개발 중부터 관리한다.
5. raw PII가 로그, 보고서, 증빙 자료에 남지 않도록 한다.

## 1. 기본 원칙

### 1-1. 작업은 작은 단위로 나눈다

AI에게 한 번에 큰 기능 전체를 맡기지 않는다. 구현은 `docs/07_IMPLEMENTATION_ROADMAP.md`의 milestone 단위 또는 그보다 작은 단위로 나눈다.

좋은 작업 단위 예시:

- `preprocess.py`의 zero-width removal variant만 구현
- `validators.py`의 Luhn checksum만 구현
- `korean_boundary.py`의 josa suffix split만 구현
- `masker.py`의 label mask만 구현
- `audit_logger.py`의 raw PII blocklist 테스트만 구현

피해야 할 작업 단위:

- 전체 pipeline 한 번에 구현
- detector, resolver, masker, audit logger를 한 PR에 모두 구현
- 문서, config, API, 테스트, 대규모 refactor를 한 commit에 섞기

### 1-2. 설명할 수 없는 코드는 commit하지 않는다

AI가 생성한 코드라도 작업자는 아래를 설명할 수 있어야 한다.

- 이 함수 또는 클래스의 역할
- 입력과 출력
- raw text offset을 보존하는 방식
- 기존 dataclass, protocol, schema와의 연결
- raw PII가 public response나 log로 새지 않는 이유

### 1-3. 프로젝트 범위를 섞지 않는다

이 문서는 `korean_pii_guardrail_v0_2`에만 적용한다.

기존 루트의 `PII/` 디렉터리는 별도 연구/평가 스택이다. 사용자가 명시적으로 통합을 요청하지 않는 한, 새 패키지 구현에서 `PII/` 코드를 import하거나 수정하지 않는다.

### 1-4. 모듈 경계를 지킨다

작업은 아래 영역을 기준으로 나눈다.

```text
src/pii_guardrail/schema.py
src/pii_guardrail/interfaces.py
src/pii_guardrail/preprocess.py
src/pii_guardrail/regex_detectors.py
src/pii_guardrail/validators.py
src/pii_guardrail/korean_boundary.py
src/pii_guardrail/dictionary_loader.py
src/pii_guardrail/dictionary_detectors.py
src/pii_guardrail/context_scorer.py
src/pii_guardrail/span_resolver.py
src/pii_guardrail/policy.py
src/pii_guardrail/masker.py
src/pii_guardrail/audit_logger.py
src/pii_guardrail/pipeline.py
src/pii_guardrail/evaluation.py
```

원칙:

- 한 PR은 가능하면 한 milestone 또는 한 모듈 중심으로 작성한다.
- 여러 명이 같은 파일을 동시에 수정하지 않는다.
- `schemas/`, `configs/`, `api/openapi.yaml` 같은 계약 파일을 수정할 때는 팀에 먼저 공유한다.
- 모듈 경계를 넘는 수정은 PR 본문에 이유를 적는다.

## 2. AI 생성 코드 검증 원칙

AI가 생성한 코드는 그대로 commit하지 않는다. 최소한 아래 4단계를 거친다.

### 2-1. 코드 직접 읽기

확인 항목:

- 이상한 import가 없는가
- 기존 interface와 schema를 깨지 않는가
- hard-coded score, policy, entity rule이 들어가지 않았는가
- raw PII가 exception, log, metric, report에 포함될 가능성이 없는가
- detector가 final action을 결정하지 않는가
- raw offset 대신 normalized offset을 반환하지 않는가

### 2-2. 실행 확인

최소 확인:

```bash
python -m pytest
```

작업 중에는 관련 테스트만 먼저 실행해도 된다.

예:

```bash
python -m pytest tests/test_contract_smoke.py
python -m pytest tests/test_preprocess.py
python -m pytest tests/test_korean_boundary.py
```

### 2-3. 기존 기능 영향 확인

확인 항목:

- 기존 dataclass field 의미가 바뀌지 않았는가
- `PublicPIISpan` 또는 audit event에 raw text가 들어가지 않는가
- `scan_stage`가 `input`, `output` 범위를 벗어나지 않는가
- RAG, multi-turn, session 관련 field가 새로 들어가지 않았는가
- JSON Schema와 Python dataclass가 어긋나지 않는가

### 2-4. 정리 후 commit

commit 전 정리:

- 불필요한 주석과 debug print 제거
- 중복 코드 제거
- 테스트 fixture 정리
- 실패하던 임시 파일 제거
- 문서와 config 동기화 확인

## 3. 브랜치 운영 규칙

### 3-1. 브랜치 구조

권장 구조:

```text
main          통합 및 최종 안정 브랜치
feature/*     기능 작업 브랜치, main으로 PR
docs/*        문서 작업 브랜치, main으로 PR
fix/*         버그 수정 브랜치, main으로 PR
```

원칙:

- `main`에 직접 push하지 않는다.
- 작업은 feature/docs/fix 브랜치에서 진행한다.
- 작업 결과는 PR로 `main`에 합친다.

### 3-2. 권장 브랜치 이름

로드맵 milestone을 반영한다.

```text
feature/schema-contract
feature/preprocess-offset-map
feature/regex-detectors
feature/korean-boundary
feature/context-scorer
feature/span-resolver
feature/masker-policy
feature/audit-logger
feature/eval-harness
docs/github-operations-guide
fix/raw-offset-validation
```

## 4. 실제 작업 절차

### 4-1. 작업 시작 전

```bash
git checkout main
git pull origin main
git checkout -b feature/preprocess-offset-map
```

항상 최신 `main`에서 작업 브랜치를 만든다. `main` 직접 수정과 직접 push는 금지한다.

### 4-2. 작업 후

```bash
python -m pytest
git status
git add <changed-files>
git commit -m "[feat] preprocess: raw offset map skeleton 추가"
git push origin feature/preprocess-offset-map
```

그 다음 GitHub에서 PR을 생성한다.

## 5. 커밋 메시지 규칙

형식:

```text
[타입] 영역: 무엇을 했는지
```

타입:

- `[feat]` 기능 추가
- `[fix]` 버그 수정
- `[refactor]` 동작 변화 없는 구조 개선
- `[docs]` 문서 수정
- `[test]` 테스트 추가/수정
- `[chore]` 설정, 정리, 기타 작업

예시:

```text
[feat] preprocess: NFKC normalization variant 추가
[fix] schema: PublicPIISpan raw text 노출 방지 검증 수정
[test] boundary: 조사 suffix split 테스트 추가
[docs] operations: GitHub 운영 규칙 추가
[refactor] interfaces: Detector protocol 입력 타입 정리
```

나쁜 예시:

```text
수정
업데이트
테스트
AI 코드 추가
```

## 6. PR 규칙

### 6-1. PR 생성 전 체크

PR 생성 전 확인:

1. 현재 브랜치가 작업 브랜치인지 확인
2. 변경 파일이 작업 범위를 벗어나지 않는지 확인
3. 관련 테스트를 실행했는지 확인
4. raw PII가 log, report, exception, audit event, public response에 들어가지 않는지 확인
5. config/schema/doc 동기화가 필요한 변경인지 확인
6. `main`과 충돌이 없는지 확인

충돌 확인 예시:

```bash
git checkout main
git pull origin main
git checkout feature/preprocess-offset-map
git merge main
```

### 6-2. PR 대상

기본 규칙:

```text
base: main
compare: feature/작업명
```

즉, 작업 브랜치를 `main`에 합치는 PR을 만든다. `main`에 직접 push하지 않는다.

### 6-3. PR 제목

형식:

```text
[타입] 작업 요약
```

핵심 계약 변경은 `[CORE]`를 붙인다.

예:

```text
[feat] preprocess raw offset map 구현
[CORE][fix] PIISpan validation 계약 수정
[docs] GitHub 운영 및 증빙 관리 가이드 추가
```

### 6-4. PR 본문 템플릿

```text
1. 작업 내용
-

2. 수정 이유
-

3. 테스트 결과
-

4. 영향 범위
-

5. 리뷰 요청 사항
-
```

테스트 결과에는 실제 실행 명령을 적는다.

예:

```text
3. 테스트 결과
- python -m pytest tests/test_contract_smoke.py
- 3 passed
```

### 6-5. 승인 후 merge

원칙:

- 승인 없이 merge하지 않는다.
- 자기 PR을 자기 혼자 바로 merge하지 않는다.
- `schema`, `config`, `policy`, `audit`, `pipeline` 변경은 리뷰를 더 엄격히 한다.
- `main`에는 리뷰와 테스트를 통과한 변경만 반영한다.

## 7. 리뷰 기준

리뷰어는 아래를 확인한다.

### 코드 측면

- raw offset 계약을 지키는가
- detector가 candidate만 반환하는가
- public response와 audit event에 raw PII가 없는가
- config-driven 원칙을 지키는가
- v0.2 범위를 벗어난 RAG/multi-turn 코드가 없는가
- 기존 schema/API contract를 깨지 않는가
- 테스트가 작업 범위를 충분히 덮는가

### 운영 측면

- 브랜치와 commit 메시지가 규칙에 맞는가
- PR 본문이 작성되어 있는가
- 테스트 결과가 실제 명령과 함께 적혀 있는가
- 문서/config/schema 동기화가 필요한 경우 함께 수정했는가
- 증빙 자료가 필요한 작업이면 evidence에 남겼는가

## 8. 증빙 자료 관리

개발 종료 후 한 번에 모으지 말고, 개발 중부터 증빙을 남긴다.

### 8-1. 권장 폴더 구조

```text
evidence/
  worklog/          작업 단계별 스크린샷, 로그 요약, 데모 캡처
  meetings/         회의록, 결정 사항
  tests/            pytest 결과, 수동 테스트 표, 회귀 테스트 로그
  demo/             데모 입력, 실행 명령, 출력 캡처
  perf/             latency, throughput, 비교 표
  audit_safety/     no-raw-PII 검증 결과
  reports/          평가 리포트, release gate 결과
```

### 8-2. raw PII 증빙 금지

증빙 자료에도 raw PII를 남기지 않는다.

금지:

- 실제 개인정보
- raw span text
- 원문 전체 입력을 그대로 담은 실패 로그
- 복원 가능한 token mapping
- secret, API key, credential

허용:

- synthetic fixture ID
- case ID
- entity type
- span length
- score, risk level, action
- HMAC/hash
- raw value가 제거된 summary

예:

```json
{
  "case_id": "case-0019",
  "error_type": "FP",
  "entity_type": "PERSON_NAME",
  "layer_suspected": "span_resolver",
  "raw_value_logged": false
}
```

### 8-3. 매주 남길 자료

- 이번 주 작업 요약
- 결정 사항
- 변경된 architecture 또는 contract
- 테스트 결과
- 실패 사례와 수정 내역
- known limitations
- 다음 주 작업 계획

## 9. 인계 패키지

구현 안정화 단계에는 아래 산출물이 준비되어야 한다.

```text
README.md
docs/00_PROJECT_PLAN.md
docs/07_IMPLEMENTATION_ROADMAP.md
docs/08_EVALUATION_PLAN.md
docs/09_COMPLIANCE_AND_AUDIT_SPEC.md
reports/entity_metrics_v0_2.json
reports/boundary_metrics_v0_2.json
reports/ablation_v0_2.md
reports/release_gate_v0_2.json
evidence/README.md 또는 evidence index
```

## 10. 팀원이 지킬 최소 행동 규칙

1. 작업 전 최신 `main` 브랜치를 pull한다.
2. feature/docs/fix 브랜치에서 작업한다.
3. AI 코드 바로 commit 금지.
4. 직접 읽고, 실행하고, 영향 확인 후 commit한다.
5. commit 메시지는 규칙대로 작성한다.
6. PR 본문에 작업 내용, 이유, 테스트 결과, 영향 범위를 적는다.
7. raw PII가 어디에도 남지 않았는지 확인한다.
8. 계약 변경은 config/schema/doc을 함께 맞춘다.
9. 리뷰 승인 후 merge한다.
10. 평가와 보고서에 필요한 증빙을 개발 중부터 정리한다.

## 11. 회의록 및 AI 사용 기록 템플릿

### 회의록

```text
회의 일시:
참석자:
회의 안건:

결정 사항:
-

할 일:
- 담당자 / 작업 / 마감일

비고:
-
```

### AI 사용 기록

```text
날짜:
작업자:
작업 브랜치:
작업 내용:
사용한 AI 도구:
입력 요약:
출력 요약:
실제 반영 여부:
사람이 검토/수정한 내용:
실행한 테스트:
비고:
```

## 12. 최종 정리

이 문서의 핵심은 다음이다.

- 작은 단위로 작업한다.
- feature 브랜치에서 작업하고 PR로 합친다.
- AI 코드는 직접 검증한 뒤 commit한다.
- raw offset과 raw PII 안전 규칙을 깨지 않는다.
- config, schema, docs를 함께 관리한다.
- 개발 중부터 평가와 보고서용 증빙을 남긴다.
