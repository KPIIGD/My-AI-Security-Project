# 요구사항 명세서 — Korean PII Guardrail v0.2

Version: v0.2-single-turn  
Date: 2026-05-09

## 1. 시스템 정의

Korean PII Guardrail v0.2는 단일 한국어 텍스트를 입력받아 개인정보 및 보안비밀 후보를 탐지하고, 한국어 문법을 보존하면서 정책에 맞게 비식별화된 텍스트와 탐지 결과를 반환하는 소프트웨어 모듈이다.

## 2. 사용자 및 이해관계자

| 이해관계자 | 관심사 |
|---|---|
| Pipeline 개발자 | 안정적인 offset, detector 통합, resolver, masker |
| NER 개발자 | 공통 PIISpan 계약, label mapping, calibration |
| 평가 담당자 | gold set, metric, ablation, release gate |
| 운영 담당자 | latency, error handling, audit event |
| 개인정보/보안 담당자 | raw PII logging 금지, 가명처리 정책, HMAC/key 관리 |

## 3. Functional Requirements

### FR-001. 단일 텍스트 스캔

시스템은 하나의 문자열 `text`를 입력받아 개인정보 후보 span 목록을 생성해야 한다.

- 입력은 UTF-8 문자열이다.
- 입력은 user input 또는 model output일 수 있다.
- RAG/retrieval context 타입은 v0.2에서 지원하지 않는다.
- 이전 턴 또는 세션 상태는 입력으로 받지 않는다.

### FR-002. Raw offset 보존

모든 detector output은 원문 raw text 기준 character offset을 반환해야 한다.

- `start`: inclusive
- `end`: exclusive
- `text == raw_text[start:end]` 조건을 만족해야 한다.
- normalized text 기준 offset만 반환하는 detector는 실패 처리한다.

### FR-003. L0 기반 offset-aware 텍스트 전처리

시스템은 기존 Layer 0에서 검증된 한국어 변형 공격 대응 전략을 v0.2의 raw offset contract에 맞게 재구현해야 한다.

전처리는 원문을 대체하는 기능이 아니라 탐지 가능한 표현을 늘리는 기능이다. 모든 기본 정규화 결과와 탐지용 variant는 원문 offset으로 복원 가능해야 한다.

#### FR-003-1. 보수적 정규화

| 정규화 | 설명 |
|---|---|
| NFKC | 전각 숫자/문자 정규화 |
| Dash normalization | hyphen, en dash, minus 등 통합 |
| Zero-width removal | zero-width space/joiner 제거 |
| Mathematical/circled digit normalization | 수학 숫자·원문자 숫자를 일반 숫자로 정규화 |

이 결과는 `normalized_text`가 될 수 있다. 단, `norm_to_raw`, `raw_to_norm` 또는 동등한 mapping을 포함해야 한다.

#### FR-003-2. 구조 보존형 탐지 variant

시스템은 다음 탐지용 variant를 생성해야 한다.

| Variant | 설명 |
|---|---|
| Digit compact | `010 1234 5678`, `010-1234-5678`, `01012345678` 대응 |
| Digit-space compact | `9 0 0 1 0 1 - 1 2 3 4 5 6 7` 대응 |
| Korean keyword spacing compact | `주 민 번 호`, `계 좌 번 호` 등 PII keyword 띄어쓰기 변형 대응 |

이 variant들은 기본 본문을 대체하지 않는다. detector가 variant에서 후보를 찾으면 pipeline은 해당 후보를 raw text span으로 복원해야 한다.

#### FR-003-3. L0-derived 고급 한국어 변형 variant

시스템은 한국어 특화 변형 공격 대응을 위해 다음 고급 variant를 지원해야 한다.

| Variant | 예시 | 처리 원칙 |
|---|---|---|
| Jamo composition | `ㅈㅜㅁㅣㄴ` → `주민` | 원문 자모 범위를 raw span으로 보존 |
| Choseong restoration | `ㅈㅁㅂㅎ` → `주민번호` | 탐지용 variant로만 사용 |
| Yaminjeongeum restoration | `즈민뜽록` → `주민등록` | 탐지용 variant로만 사용 |
| Romanized Korean restoration | `jumin` → `주민` | 탐지용 variant로만 사용 |
| Korean digit restoration | `공일공` → `010` | 숫자 context 또는 명시적 rule 필요 |

고급 variant는 길이와 의미가 크게 바뀔 수 있으므로, 문자 하나당 raw index 하나만으로 표현할 수 없는 경우 raw start/end span mapping을 사용해야 한다.

#### FR-003-4. L0 활용 범위

`PII/layer_0/korean_normalizer.py`는 변형 공격 유형과 정규화 전략을 확인하기 위한 reference로 사용한다. v0.2 package는 해당 모듈을 직접 import하지 않는다.

정규화 결과는 raw offset map을 반드시 포함해야 하며, 최종 `PIISpan`은 항상 다음 조건을 만족해야 한다.

```python
span.text == raw_text[span.start:span.end]
```

### FR-004. 구조형 개인정보 탐지

시스템은 다음 구조형 entity를 regex/validator로 탐지해야 한다.

| Entity | 필수 여부 | validator |
|---|---:|---|
| RRN | 필수 | 날짜/성별 digit/길이 + checksum |
| FRN | 필수 | 날짜/성별 digit/길이 + checksum |
| PHONE_MOBILE | 필수 | 길이/국번 |
| PHONE_LANDLINE | 필수 | 지역번호/길이 |
| EMAIL | 필수 | domain 구조 |
| CREDIT_CARD | 필수 | Luhn checksum |
| BUSINESS_REG_NO | 필수 | checksum 또는 v0 placeholder validator |
| BANK_ACCOUNT | 필수 | 숫자 패턴 + 금융 context |
| IP_ADDRESS | 권장 | IPv4/IPv6 형식 |
| MAC_ADDRESS | 권장 | MAC 형식 |
| API_KEY_SECRET | 필수 | prefix/entropy/length |

### FR-005. 의미형 개인정보 후보 탐지

시스템은 다음 의미형 entity를 dictionary와 NER interface로 탐지할 수 있어야 한다. Fine-tuned NER v3는 `NAME`, `ADDRESS`, `ORG` 3종만 직접 emit하며, 다른 의미형 entity는 dictionary, regex, context, resolver 후속 처리로 탐지 또는 재분류한다.

| Entity | 기본 detector |
|---|---|
| PERSON_NAME | NER + dictionary + context |
| ALIAS_HANDLE | regex + context |
| ADDRESS_FULL | pattern + dictionary + NER |
| ADDRESS_UNIT | pattern + dictionary + resolver 분기 |
| ORGANIZATION | dictionary + NER |
| SCHOOL | dictionary + resolver reclassify |
| HOSPITAL | dictionary + resolver reclassify |
| FAMILY_RELATION | dictionary + context |
| CUSTOMER_ID | custom identifier profile |
| EMPLOYEE_ID | custom identifier profile |
| STUDENT_ID | custom identifier profile |
| MEDICAL_RECORD_NO | regex + context |

### FR-006. 한국어 boundary correction

시스템은 후보 span의 후행 조사·호칭·어미를 분리해야 한다.

예시:

| Raw candidate | PII 본체 | suffix | 최종 출력 |
|---|---|---|---|
| `홍길동이` | `홍길동` | `이` | `[PERSON_1]이` |
| `김민수에게` | `김민수` | `에게` | `[PERSON_1]에게` |
| `010-1234-5678로` | `010-1234-5678` | `로` | `[PHONE_1]로` |
| `test@example.com입니다` | `test@example.com` | `입니다` | `[EMAIL_1]입니다` |
| `서울시 강남구에` | `서울시 강남구` | `에` | `[ADDRESS_1]에` |

### FR-007. Context scoring

시스템은 단일 입력 텍스트 내부의 문맥으로 candidate score를 조정해야 한다.

- context window 단위: 어절
- 기본 크기: 후보 기준 ±5 어절
- 제한: 같은 문장 안으로 제한
- field label: 같은 문장 내 전체 위치 허용
- co-occurrence: 같은 문장 내 PII만 인정
- 이전 턴 context: 미지원

### FR-008. Score composition

시스템은 detector별 base score와 context adjustment를 결합해 최종 score를 산정해야 한다.

- 동일 span을 여러 detector가 탐지하면 `max(score)`를 사용한다.
- source list와 detector id list는 보존한다.
- Bayesian 결합은 v0.2에서 사용하지 않는다.
- score는 `[0.0, 1.0]` 범위로 clamp한다.

### FR-009. Context judge

`0.55 <= score < 0.75` 구간은 LLM 호출 없이 deterministic context judge로 처리해야 한다.

Context judge는 다음 순서로 판단한다.

1. strong field label 확인
2. entity-specific context 확인
3. negative context 확인
4. single-turn composite 확인
5. P0/P1이면 안전 우선 mask/block, P2/P3이면 context/composite 여부에 따라 mask/pass 정책 적용

### FR-010. Span resolver

시스템은 중복·겹침 span을 결정론적으로 정리해야 한다.

우선순위:

```text
API_KEY_SECRET > RRN/FRN/PASSPORT/DRIVER_LICENSE > CREDIT_CARD/BANK_ACCOUNT > PHONE/EMAIL > ADDRESS > MEDICAL_RECORD_NO > custom-profile CUSTOMER_ID/EMPLOYEE_ID/STUDENT_ID > PERSON_NAME > ORGANIZATION/SCHOOL/HOSPITAL > quasi identifiers
```

요구사항:

- EMAIL 내부 username은 PERSON_NAME보다 EMAIL 우선
- ADDRESS fragment는 가능하면 ADDRESS_FULL로 merge
- 같은 span은 하나의 span으로 merge
- composite 승격은 L6 resolver에서 최종 결정

### FR-011. Masking policy

시스템은 LLM Gateway MVP 기준으로 `output_target`과 기본 `strict` profile에 따라 마스킹 방식을 선택해야 한다.

| Output target | 기본 policy |
|---|---|
| `llm_input` | label mask |
| `external_output` | label mask 또는 block |
| `audit_log` | HMAC hash |

`internal_ui`, `analytics`, `analytics_ai_training`, pseudonymization, human review workflow는 v0.2 LLM Gateway MVP의 1차 범위가 아니며 후속 확장으로 다룬다.

### FR-012. 감사 로그

시스템은 개인정보 원문을 audit log에 저장하지 않아야 한다.

허용 필드:

- event_type
- timestamp
- request_id
- policy_profile
- output_target
- entity_type
- source list
- detector id list
- score
- risk_level
- action
- value_hash
- span_length
- reason_codes
- raw_value_logged=false

금지 필드:

- raw text
- raw span text
- normalized raw PII
- reversible token mapping

### FR-013. 평가 하네스

시스템은 다음 metric을 산출해야 한다.

- entity precision/recall/F1
- exact span F1
- partial span F1
- boundary accuracy
- over-masking rate
- under-masking rate
- high-risk recall
- false block rate
- p50/p95/p99 latency
- raw PII logging count
- single-turn composite recall

## 4. Non-Functional Requirements

### NFR-001. 결정론성

동일 input, 동일 config, 동일 model output이면 최종 masked text와 span list는 동일해야 한다.

### NFR-002. Latency

초기 목표:

| 경로 | 목표 |
|---|---:|
| regex + dictionary + boundary + resolver | p95 100ms 이하 |
| mock NER 포함 | p95 120ms 이하 |
| real NER 포함 | 모델 배포 방식에 따라 별도 SLA |

`real NER 포함` latency는 deterministic CPU path 목표와 분리해 측정한다. NER v3의 실제 serving latency는 PyTorch CPU/GPU/ONNX 등 배포 방식별로 별도 report에 기록한다.

### NFR-003. Config driven

entity별 risk, detector routing, score base, context rules, masking policy는 config로 관리해야 한다.

### NFR-004. No raw PII logging

테스트와 운영 모두에서 raw PII 로그가 0건이어야 한다.

### NFR-005. 확장성

RAG와 멀티턴은 v0.2에서 제외하지만, 향후 확장을 위해 pipeline component는 독립 모듈로 설계한다.

단, 현재 인터페이스에 `session_id`를 필수화하지 않는다.

## 5. Data Requirements

### DR-001. Dictionary

초기 dictionary는 다음 파일로 분리한다.

- surnames
- given_name_candidates
- address_terms
- road_terms
- banks
- titles
- relation_terms
- organization_suffixes
- negative_context_terms

### DR-002. Evaluation data

평가 데이터는 synthetic 또는 적법하게 가명처리된 데이터만 사용한다.

- raw production PII 사용 금지
- 평가 리포트에 raw PII 노출 금지
- hard case는 synthetic fixture로 관리

## 6. Acceptance Criteria

| 항목 | 기준 |
|---|---|
| schema | JSON Schema validation 통과 |
| offset | 모든 PIISpan raw offset 검증 통과 |
| detector | 구조형 hard cases 통과 |
| boundary | 핵심 조사/호칭 예시 통과 |
| resolver | overlap priority 테스트 통과 |
| masking | output target별 expected output 통과 |
| audit | raw PII logging zero |
| evaluation | ablation runner 실행 가능 |

## 7. 변경관리

- entity type 추가는 `configs/entities.yaml`, `schemas/pii_span.schema.json`, `src/pii_guardrail/enums.py`를 함께 수정해야 한다.
- score rule 변경은 `configs/scoring.yaml`과 `docs/03_SCORING_POLICY_SPEC.md`를 함께 수정해야 한다.
- context rule 변경은 `configs/context_rules.yaml`과 `docs/04_CONTEXT_POLICY_SPEC.md`를 함께 수정해야 한다.
- masking policy 변경은 `configs/policy_profiles.yaml`과 `docs/05_MASKING_POLICY_SPEC.md`를 함께 수정해야 한다.
