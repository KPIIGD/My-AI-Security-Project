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
8. M1 구현 시 기존 L0 코드는 reference로만 사용하고 v0.2 package에서 직접 import하지 않는다.
9. L0-derived 변형 복원 결과는 raw span으로 되돌릴 수 있어야 하며, 복원 실패 candidate는 reject한다.

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
[ ] preprocess/L0-derived variants
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

### L0-derived variant

```text
ㅈㅜㅁㅣㄴ번호 900101-1234567
ㅈㅁㅂㅎ는 900101-1234567
즈민뜽록볜훟 900101-1234567
jumin beonho 900101-1234567
연락처는 공일공 일이삼사 오육칠팔입니다.
```

위 케이스는 탐지용 variant로 복원할 수 있어야 한다. 단, 최종 span은 항상 원문 raw offset 기준이어야 한다.

## 6. M1 L0 활용 규칙

- `PII/layer_0/korean_normalizer.py`는 변형 유형, 정규화 순서, 테스트 아이디어를 확인하는 reference로 사용한다.
- `PII/layer_0/korean_pii_detector.py`는 M2 이후 detector 패턴 후보를 검토하는 reference로 사용한다.
- v0.2 package는 `PII/layer_0` 모듈을 import하지 않는다.
- L0의 block/mask 결정 로직은 v0.2 M1에 포함하지 않는다.
- `original`, `normalized`, `value` 같은 raw PII 포함 가능 필드는 public response, audit event, evidence에 남기지 않는다.
- Kiwi/kiwipiepy는 optional reference로 설치 가능성, token/sentence offset, latency를 검증할 수 있다. Kiwi 소스, 모델, 사전은 v0.2 package에 복사하지 않는다.

## 7. Config change protocol

- entity 추가: `configs/entities.yaml`, `src/pii_guardrail/enums.py`, JSON Schema 동시 수정
- score 변경: `configs/scoring.yaml`, `docs/03_SCORING_POLICY_SPEC.md` 동시 수정
- policy 변경: `configs/policy_profiles.yaml`, `docs/05_MASKING_POLICY_SPEC.md` 동시 수정
- context 변경: `configs/context_rules.yaml`, `docs/04_CONTEXT_POLICY_SPEC.md` 동시 수정

## 8. PR review checklist

| Check | Required |
|---|---:|
| raw offset 검증 | Yes |
| raw PII log 없음 | Yes |
| public response raw text 없음 | Yes |
| unit test 추가 | Yes |
| config/doc 동기화 | Yes |
| RAG/multiturn 코드 없음 | Yes |
| deterministic output | Yes |

## 9. Known open items

| Item | Owner | Status |
|---|---|---|
| business registration checksum 정확 구현 | Pipeline | Open |
| Korean digit normalization 범위 | Pipeline | Open |
| NER temperature scaling dataset | NER | Open |
| evaluation gold set 구축 | Eval | Open |
| HMAC key provider 실제 구현 | Security | Open |
| domain-specific policy profile | Compliance | Open |

## 10. Do not implement yet

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
