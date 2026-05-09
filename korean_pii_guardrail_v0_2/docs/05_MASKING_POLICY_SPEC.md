# Masking Policy Selection 명세서

Version: v0.2-single-turn  
Date: 2026-05-09

## 1. 목적

본 문서는 Korean PII Guardrail v0.2에서 최종 PII span에 적용할 보호 조치의 선택 기준을 정의한다.

초기 자료에서 누락되었던 다음 의사결정 변수를 명시한다.

- entity 위험도
- output target
- policy profile
- composite 여부
- domain/sensitive context
- audit log 목적

## 2. 보호 조치 종류

| Action | 설명 | 예시 |
|---|---|---|
| `pass` | 원문 유지 | `서울` 단독 |
| `mask` | label 또는 partial로 치환 | `[PERSON_1]` |
| `pseudonymize` | 분석용 가명값으로 치환 | `사람A` |
| `hash` | HMAC 등 digest로 변환 | `hmac-sha256:...` |
| `review` | 호출자에게 검토 필요 표시 | response flag |
| `block` | 출력 전체 또는 해당 요청 차단 | API key |

## 3. Transformation methods

| Method | Reversible | 사용처 | 예시 |
|---|---:|---|---|
| label_mask | No | LLM input, external output | `[PERSON_1]` |
| partial_mask | No | internal UI | `010-****-5678` |
| pseudonym | No by default | analytics | `사람A`, `기관A` |
| hmac_hash | No | audit/log duplicate tracking | `hmac-sha256:...` |
| full_redact | No | secret/P0 | `[REDACTED]` |
| block | N/A | high-risk secret | response blocked |

복원형 tokenization은 v0.2 기본 범위가 아니다. 필요한 경우 `TokenizationProvider` interface를 별도 추가한다.

## 4. Output target

| Output target | 의미 | 기본 transformation |
|---|---|---|
| `llm_input` | LLM에 전달하기 전 텍스트 | label_mask |
| `external_output` | 사용자 또는 외부 API 응답 | label_mask/block |
| `internal_ui` | 내부 상담/운영 화면 | partial_mask |
| `analytics` | 분석/통계/품질평가용 데이터 | pseudonym/generalization |
| `audit_log` | 감사/추적 로그 | hmac_hash |

## 5. Policy profile

| Profile | 목적 | 기본 성향 |
|---|---|---|
| `strict` | 외부 출력/고위험 도메인 | recall 우선, 과소마스킹 방지 |
| `balanced` | 일반 내부 사용 | recall/precision 균형 |
| `analytics` | 분석용 데이터 | 유틸리티 보존 + 가명화 |
| `analytics_ai_training` | AI 평가/학습용 가명 데이터 | 엄격 필터링 + 샘플 검수 |
| `audit_log` | 로깅 | HMAC만 허용 |

## 6. Policy selection matrix

| Risk | Entity 예시 | llm_input | external_output | internal_ui | analytics | audit_log |
|---|---|---|---|---|---|---|
| P0 | RRN, FRN, API key | mask/block | block 또는 full mask | full mask | 제거/비포함 | hash only |
| P1 | PHONE, EMAIL, ADDRESS_FULL, BANK_ACCOUNT | label_mask | label_mask | partial_mask | pseudonym/generalize | hash only |
| P2 | SCHOOL, ORG, DOB, ADDRESS_UNIT | context 기반 mask | context 기반 mask | partial/pass | generalize | hash only |
| P3 | AGE, GENDER 단독 | pass/review | pass/review | pass | aggregate/generalize | hash only |

## 7. Entity별 기본 정책

| Entity | Risk | Default action | Default method |
|---|---|---|---|
| API_KEY_SECRET | P0 | block | block |
| RRN | P0 | mask/block | label_mask/full_redact |
| FRN | P0 | mask/block | label_mask/full_redact |
| CREDIT_CARD | P0/P1 | mask | label_mask/partial_mask |
| BANK_ACCOUNT | P1 | mask if context | label_mask/partial_mask |
| PHONE_MOBILE | P1 | mask | label_mask/partial_mask |
| PHONE_LANDLINE | P1/P2 | mask if personal, pass if public representative | label_mask/partial_mask |
| EMAIL | P1 | mask | label_mask |
| PERSON_NAME | P1/P2 | context mask | label_mask/pseudonym |
| ADDRESS_FULL | P1 | mask | label_mask/generalize |
| ADDRESS_UNIT | P2/P3 | context mask/review | generalize |
| ORGANIZATION | P2 | context mask/review | pseudonym/pass |
| SCHOOL | P2 | context mask/review | pseudonym/generalize |
| HOSPITAL | P2/P1 | context mask | pseudonym/generalize |
| MEDICAL_RECORD_NO | P1 | mask | label_mask/hash |
| CUSTOMER_ID | P1/P2 | context mask | label_mask/hash |
| EMPLOYEE_ID | P1/P2 | context mask | label_mask/hash |
| STUDENT_ID | P1/P2 | context mask | label_mask/hash |
| DOB | P2 | composite mask | generalize |
| AGE | P3 | pass unless composite | generalize |
| GENDER | P3 | pass unless composite | aggregate |
| HEALTH_INFO | P1/P2 | domain policy | redact/generalize |

## 8. Policy selection 의사코드

```python
def select_policy(span, request_context):
    if span.entity_type == "API_KEY_SECRET":
        return Action.BLOCK, Method.BLOCK

    if request_context.output_target == "audit_log":
        return Action.HASH, Method.HMAC_HASH

    if span.risk_level == "P0":
        if request_context.policy_profile == "strict":
            return Action.BLOCK, Method.BLOCK
        return Action.MASK, Method.FULL_REDACT

    if span.is_composite:
        span = upgrade_policy(span)

    if request_context.output_target == "llm_input":
        return Action.MASK, Method.LABEL_MASK

    if request_context.output_target == "external_output":
        return Action.MASK, Method.LABEL_MASK

    if request_context.output_target == "internal_ui":
        return Action.MASK, Method.PARTIAL_MASK

    if request_context.output_target == "analytics":
        return Action.PSEUDONYMIZE, Method.PSEUDONYM

    return Action.MASK, Method.LABEL_MASK
```

## 9. Composite policy upgrade

단일 입력 텍스트 내부에서 composite가 확인되면 policy를 강화한다.

| 기존 | Composite 후 |
|---|---|
| P3 pass | P2 review 또는 mask |
| P2 review | P1 mask |
| P1 mask | P1 mask 유지, method 강화 가능 |
| P0 | P0 유지 |

예:

```text
성별: 남, 나이: 42세, 학교: OO고, 거주지: 강남구
```

- 각 항목 단독은 P2/P3일 수 있음
- 조합되면 준식별 위험이 커짐
- v0.2에서는 같은 입력 텍스트 내부 조합만 고려

## 10. 한국어 suffix 보존

마스킹은 반드시 PII 본체만 치환하고 suffix를 보존한다.

| 원문 | 잘못된 결과 | 올바른 결과 |
|---|---|---|
| `홍길동이` | `[PERSON_1]` | `[PERSON_1]이` |
| `김민수에게` | `[PERSON_1]` | `[PERSON_1]에게` |
| `010-1234-5678로` | `[PHONE_1]` | `[PHONE_1]로` |
| `test@example.com입니다` | `[EMAIL_1]` | `[EMAIL_1]입니다` |

## 11. Placeholder indexing

### 11.1 문서 내부 안정성

동일 raw value는 같은 요청 내에서 같은 placeholder를 받아야 한다.

```text
홍길동이 왔고 홍길동에게 전화했다.
→ [PERSON_1]이 왔고 [PERSON_1]에게 전화했다.
```

### 11.2 Entity별 index

```text
[PERSON_1], [PERSON_2], [PHONE_1], [ADDRESS_1]
```

### 11.3 Cross-request stability

v0.2 기본값은 요청 내부 안정성만 제공한다. cross-request stable pseudonym은 HMAC 기반 별도 profile에서만 허용한다.

## 12. Audit log policy

감사 로그는 transformation method를 `hmac_hash`로 고정한다.

허용 예:

```json
{
  "event_type": "pii_detection",
  "entity_type": "PHONE_MOBILE",
  "score": 0.94,
  "action": "mask",
  "value_hash": "hmac-sha256:key-v1:...",
  "span_length": 13,
  "reason_codes": ["regex.phone.kr", "suffix.josa.ro"],
  "raw_value_logged": false
}
```

금지 예:

```json
{
  "entity_type": "PHONE_MOBILE",
  "raw_value": "010-1234-5678"
}
```

## 13. 구현 위치

| 항목 | 파일 |
|---|---|
| policy config | `configs/policy_profiles.yaml` |
| entity risk | `configs/entities.yaml` |
| schema fields | `schemas/pii_span.schema.json` |
| masking engine | `src/pii_guardrail/masker.py` 예정 |
| audit logger | `src/pii_guardrail/audit_logger.py` 예정 |
