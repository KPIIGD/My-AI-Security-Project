# Development Handoff — Korean PII Guardrail v0.2

Version: v0.2-single-turn  
Date: 2026-05-09

## 1. 시작 전에 읽을 파일

개발자는 아래 순서대로 읽는다.

1. `README.md`
2. `docs/12_SCOPE_CHANGE_NOTE.md`
3. `docs/01_REQUIREMENTS_SPEC.md`
4. `docs/02_ARCHITECTURE_SPEC.md`
5. `docs/03_SCORING_POLICY_SPEC.md`
6. `docs/06_INTERFACE_SPEC.md`
7. `configs/entities.yaml`
8. `schemas/pii_span.schema.json`

## 2. 절대 규칙

1. raw offset 기준을 깨지 않는다.
2. detector는 final action을 결정하지 않는다.
3. NER output은 candidate일 뿐이다.
4. raw PII를 log, exception, metric, report에 넣지 않는다.
5. RAG와 멀티턴 코드를 v0.2에 넣지 않는다.
6. score rule을 코드에 하드코딩하지 않고 config로 둔다.
7. dictionary match 단독으로 PERSON을 high confidence 처리하지 않는다.

## 3. 첫 PR 목표

첫 PR은 schema와 skeleton만 포함한다.

포함 파일:

- `src/pii_guardrail/enums.py`
- `src/pii_guardrail/schema.py`
- `src/pii_guardrail/interfaces.py`
- `src/pii_guardrail/ner/base.py`
- `src/pii_guardrail/ner/mock_ner.py`
- `tests/test_contract_smoke.py`

첫 PR acceptance:

```bash
pip install -e .[dev]
pytest
```

- import 성공
- PIISpan offset 검증 성공/실패 케이스 통과
- public span에 raw text 미포함

## 4. 구현 순서 체크리스트

```text
[ ] schema/enums
[ ] preprocess/offset map
[ ] regex detectors
[ ] validators
[ ] korean_boundary
[ ] dictionary loader
[ ] context scorer
[ ] mock NER
[ ] span resolver
[ ] policy router
[ ] masker
[ ] audit logger
[ ] pipeline integration
[ ] evaluation runner
[ ] ablation runner
```

## 5. Test case minimum

각 모듈은 최소 다음 fixture를 포함한다.

### Boundary

```text
홍길동이 신청했습니다.
김민수에게 연락하세요.
010-1234-5678로 전화 주세요.
test@example.com입니다.
서울시 강남구에 거주합니다.
```

### Hard negative

```text
오늘 하늘이 맑네요.
사랑은 중요한 가치입니다.
예시 전화번호는 010-0000-0000입니다.
```

### Context

```text
고객명 하늘, 연락처 010-1111-2222.
신한은행 계좌 110-123-456789로 입금해 주세요.
```

### Overlap

```text
test@example.com입니다.
```

EMAIL이 내부 username 후보보다 우선해야 한다.

## 6. Config change protocol

- entity 추가: `configs/entities.yaml`, `src/pii_guardrail/enums.py`, JSON Schema 동시 수정
- score 변경: `configs/scoring.yaml`, `docs/03_SCORING_POLICY_SPEC.md` 동시 수정
- policy 변경: `configs/policy_profiles.yaml`, `docs/05_MASKING_POLICY_SPEC.md` 동시 수정
- context 변경: `configs/context_rules.yaml`, `docs/04_CONTEXT_POLICY_SPEC.md` 동시 수정

## 7. PR review checklist

| Check | Required |
|---|---:|
| raw offset 검증 | Yes |
| raw PII log 없음 | Yes |
| public response raw text 없음 | Yes |
| unit test 추가 | Yes |
| config/doc 동기화 | Yes |
| RAG/multiturn 코드 없음 | Yes |
| deterministic output | Yes |

## 8. Known open items

| Item | Owner | Status |
|---|---|---|
| business registration checksum 정확 구현 | Pipeline | Open |
| Korean digit normalization 범위 | Pipeline | Open |
| NER temperature scaling dataset | NER | Open |
| evaluation gold set 구축 | Eval | Open |
| HMAC key provider 실제 구현 | Security | Open |
| domain-specific policy profile | Compliance | Open |

## 9. Do not implement yet

아래 항목은 구현 PR에 포함하지 않는다.

- session monitor
- fragment ledger
- subject tracker
- Redis TTL store
- RAG context scanner
- retrieval document sanitizer
- LLM judge
- human review dashboard
- production key management system
