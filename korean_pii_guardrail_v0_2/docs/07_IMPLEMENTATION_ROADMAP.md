# 구현 로드맵 — Korean PII Guardrail v0.2

Version: v0.2-single-turn  
Date: 2026-05-09

## 1. 구현 전략

v0.2는 NER fine-tuning을 기다리지 않고 deterministic core를 먼저 구현한다. NER는 mock interface로 연결하고, pipeline의 raw offset, boundary correction, resolver, masking, audit, evaluation이 안정화된 뒤 실제 모델로 교체한다.

## 2. Milestones

### M0. Repository skeleton and schema

#### 구현 파일

- `src/pii_guardrail/enums.py`
- `src/pii_guardrail/schema.py`
- `src/pii_guardrail/interfaces.py`
- `schemas/*.schema.json`
- `tests/test_contract_smoke.py`

#### 작업

- enum 정의
- dataclass 정의
- JSON serialization/deserialization
- offset validation
- public span 변환

#### Acceptance criteria

- `pytest tests/test_contract_smoke.py` 통과
- invalid offset 검출
- public response에 raw text 미포함

### M1. Preprocessor

#### 구현 예정 파일

- `src/pii_guardrail/preprocess.py`
- `tests/test_preprocess.py`

#### 작업

- NFKC normalization
- dash normalization
- zero-width removal
- digit compact variant
- raw/norm offset map
- sentence/eojeol split

#### Acceptance criteria

- `010\u200b-1234\u200b-5678` 탐지 가능한 variant 생성
- normalized span을 raw span으로 복원 가능
- emoji와 전각 숫자가 offset 오류를 만들지 않음

### M2. Regex detectors and validators

#### 구현 예정 파일

- `src/pii_guardrail/regex_detectors.py`
- `src/pii_guardrail/validators.py`
- `tests/test_regex_detectors.py`
- `tests/test_validators.py`

#### 작업

- RRN/FRN
- PHONE
- EMAIL
- CREDIT_CARD + Luhn
- BUSINESS_REG_NO
- BANK_ACCOUNT candidate
- IP/MAC
- API_KEY_SECRET

#### Acceptance criteria

- 구조형 hard cases 통과
- 계좌번호는 context 없으면 낮은 score
- email 내부 substring 중복 탐지 시 resolver에서 EMAIL 우선 가능

### M3. Korean boundary corrector

#### 구현 예정 파일

- `src/pii_guardrail/korean_boundary.py`
- `tests/test_korean_boundary.py`

#### 작업

- 조사 suffix table
- 호칭 suffix table
- 종결어미 trim
- numeric PII suffix trim
- offset-safe suffix split

#### Acceptance criteria

- `홍길동이` → span text `홍길동`, suffix `이`
- `김민수에게` → suffix `에게`
- `010-1234-5678로` → suffix `로`
- `test@example.com입니다` → suffix `입니다`

### M4. Dictionary and context scorer

#### 구현 예정 파일

- `src/pii_guardrail/dictionary_loader.py`
- `src/pii_guardrail/dictionary_detectors.py`
- `src/pii_guardrail/context_scorer.py`
- `tests/test_dictionary_detectors.py`
- `tests/test_context_scorer.py`

#### 작업

- config 기반 dictionary load
- field label recognition
- co-occurrence detection
- negative context
- deterministic context judge

#### Acceptance criteria

- `오늘 하늘이 맑네요` pass
- `고객명 하늘, 연락처 010-1111-2222` mask
- `신한은행 계좌 110-123-456789` BANK_ACCOUNT mask

### M5. NER interface

#### 구현 파일

- `src/pii_guardrail/ner/base.py`
- `src/pii_guardrail/ner/mock_ner.py`
- `src/pii_guardrail/ner/finetuned_wrapper.py`
- `tests/test_ner_interface.py`

#### 작업

- Protocol 정의
- mock output
- label mapping
- calibration metadata field

#### Acceptance criteria

- real NER 없이 pipeline end-to-end 실행 가능
- NER output offset validation 통과
- NER output이 boundary/context/resolver를 통과

### M6. Span resolver

#### 구현 예정 파일

- `src/pii_guardrail/span_resolver.py`
- `tests/test_span_resolver.py`

#### 작업

- duplicate merge
- max score merge
- source list preservation
- overlap priority
- ADDRESS_FULL merge
- single-turn composite escalation

#### Acceptance criteria

- EMAIL > PERSON substring
- ADDRESS fragments merge
- PERSON + PHONE same sentence composite
- source/reason_codes 보존

### M7. Policy router and masker

#### 구현 예정 파일

- `src/pii_guardrail/policy.py`
- `src/pii_guardrail/masker.py`
- `tests/test_policy.py`
- `tests/test_masker.py`

#### 작업

- output target별 policy selection
- placeholder index
- label mask
- partial mask
- pseudonym skeleton
- HMAC hash provider
- block response

#### Acceptance criteria

- suffix-preserving masking 통과
- `audit_log` target은 hash only
- API key는 block
- 동일 값은 요청 내 동일 placeholder

### M8. Audit logger

#### 구현 예정 파일

- `src/pii_guardrail/audit_logger.py`
- `tests/test_audit_logger.py`

#### 작업

- audit event schema
- raw PII field blocklist
- HMAC hashing
- key id metadata
- safe JSON export

#### Acceptance criteria

- audit event에 raw span text 없음
- unsafe payload reject
- raw PII logging zero 테스트 통과

### M9. Pipeline integration

#### 구현 예정 파일

- `src/pii_guardrail/pipeline.py`
- `tests/test_pipeline.py`

#### 작업

- preprocess → detector → boundary → context → resolver → policy/mask 순서 구현
- config loading
- request/response generation
- error handling

#### Acceptance criteria

- hard cases end-to-end 통과
- blocked response 처리
- public response raw text 미포함

### M10. Evaluation harness

#### 구현 예정 파일

- `scripts/run_eval.py`
- `scripts/run_ablation.py`
- `src/pii_guardrail/evaluation.py`
- `tests/test_evaluation.py`

#### 작업

- JSONL loading
- prediction/gold matching
- exact/partial span F1
- entity F1
- boundary accuracy
- high-risk recall
- latency metric
- ablation config

#### Acceptance criteria

- ablation A~F 실행 가능
- entity별 FP/FN report 생성
- release gate 자동 체크

## 3. Work Breakdown Structure

| ID | 작업 | 담당 | 선행 |
|---|---|---|---|
| W-001 | enum/schema 작성 | Pipeline | - |
| W-002 | JSON Schema 작성 | Pipeline | W-001 |
| W-003 | preprocess 구현 | Pipeline | W-001 |
| W-004 | regex detector 구현 | Pipeline | W-003 |
| W-005 | validators 구현 | Pipeline | W-004 |
| W-006 | boundary corrector 구현 | Pipeline | W-003 |
| W-007 | dictionary loader 구현 | Pipeline | W-001 |
| W-008 | context scorer 구현 | Pipeline | W-006,W-007 |
| W-009 | mock NER 구현 | NER | W-001 |
| W-010 | span resolver 구현 | Pipeline | W-004,W-008,W-009 |
| W-011 | policy router 구현 | Pipeline | W-010 |
| W-012 | masker 구현 | Pipeline | W-011 |
| W-013 | audit logger 구현 | Pipeline | W-012 |
| W-014 | pipeline integration | Pipeline | W-003~W-013 |
| W-015 | eval harness | Eval | W-014 |
| W-016 | ablation report | Eval | W-015 |
| W-017 | NER wrapper 교체 | NER | W-009,W-014 |

## 4. Stop conditions

다음이 완료되기 전에는 real NER fine-tuning integration 또는 v1 기능으로 넘어가지 않는다.

- raw offset mapping 안정화
- 구조형 regex detector 테스트 통과
- boundary correction 테스트 통과
- span resolver overlap policy 통과
- masker suffix preservation 통과
- audit logger raw PII zero 검증
- evaluation harness ablation 실행 가능

## 5. Definition of Done

각 모듈의 DoD는 다음을 모두 포함한다.

1. unit test 작성
2. config-driven behavior 확인
3. error case 테스트
4. public response에 raw PII 없음
5. docs와 config 변경 사항 반영
6. 최소 1개 hard case fixture 추가

## 6. Suggested branch strategy

```text
main
  ├─ feature/schema-contract
  ├─ feature/preprocess-offset-map
  ├─ feature/regex-detectors
  ├─ feature/korean-boundary
  ├─ feature/context-scorer
  ├─ feature/span-resolver
  ├─ feature/masker-policy
  ├─ feature/audit-logger
  └─ feature/eval-harness
```

## 7. Initial Codex prompt

```text
Implement a Python package named pii_guardrail for a Korean PII guardrail prototype.
Use the v0.2 single-turn scope only. Do not implement RAG scanning, session monitoring, fragment ledger, subject tracker, or multi-turn logic.
Start with deterministic core: schema, preprocessing with raw offset map, structured regex detectors, validators, Korean josa/suffix boundary correction, dictionary/context scorer, span resolver, policy router, masker, audit logger, and evaluation harness.
All detector outputs must return raw text character offsets.
Raw PII must never be written to logs or public response spans.
Create a mock NER interface but do not fine-tune a real NER model yet.
Include pytest cases for Korean particles, hard negatives, structured PII, and raw-log safety.
```
