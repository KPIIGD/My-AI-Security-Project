# Masking Policy Selection 명세서

Version: v0.2-single-turn  
Date: 2026-05-09  
MVP scope note: 2026-05-14, LLM Gateway policy simplification

## 1. 목적

본 문서는 Korean PII Guardrail v0.2의 M7 단계에서 최종 PII span에 적용할 보호 조치의 선택 기준을 정의한다.

v0.2 MVP는 LLM Gateway에 붙는 deterministic guardrail이다. 따라서 M7은 범용 개인정보 정책 플랫폼이 아니라, 다음 세 경로를 안전하게 처리하는 얇은 policy router와 masker로 제한한다.

1. LLM에 보내기 전 입력 보호
2. 사용자 또는 외부 API로 나가기 전 출력 보호
3. raw PII 없는 감사 로그 추적

## 2. M7 MVP 범위

### 2.1 포함 target

| Output target | 의미 | 기본 transformation |
|---|---|---|
| `llm_input` | LLM에 전달하기 전 텍스트 | `label_mask` |
| `external_output` | 사용자 또는 외부 API 응답 | `label_mask` 또는 `block` |
| `audit_log` | 감사/추적 로그 | `hmac_hash` |

### 2.2 기본 policy profile

MVP 기본 profile은 `strict` 하나로 본다.

`strict`는 LLM Gateway 안전 우선 정책이다. PII 과소마스킹을 피하고, P0 secret 또는 API key처럼 위험도가 높은 값은 마스킹보다 차단을 우선한다.

MVP 계약 파일은 `strict`, `llm_input`, `external_output`, `audit_log`만 지원 값으로 노출한다. future extension 값은 지원 enum에서 제외하고, 필요한 경우 별도 PR에서 다시 추가한다.

## 3. 보호 조치 종류

MVP action은 다음 네 가지로 제한한다.

| Action | 설명 | 예시 |
|---|---|---|
| `pass` | 원문 유지 | PII로 보기 어려운 단독 일반어 |
| `mask` | label mask 또는 full redact로 치환 | `[PERSON_1]`, `[REDACTED]` |
| `hash` | HMAC digest로 변환 | `hmac-sha256:key-v1:...` |
| `block` | 출력 전체 또는 해당 요청 차단 | API key 포함 응답 차단 |

`pseudonymize`, `review`, 내부 UI용 partial masking, 분석용 generalization은 v0.2 LLM Gateway MVP의 1차 구현 범위가 아니다. 필요한 제품 범위가 생기면 future extension으로 별도 설계한다.

## 4. Transformation methods

| Method | Reversible | MVP 사용처 | 예시 |
|---|---:|---|---|
| `label_mask` | No | `llm_input`, `external_output` | `[PERSON_1]` |
| `hmac_hash` | No | `audit_log` duplicate tracking | `hmac-sha256:key-v1:...` |
| `full_redact` | No | P0 secret fallback | `[REDACTED]` |
| `block` | N/A | high-risk secret | response blocked |

복원형 tokenization은 v0.2 기본 범위가 아니다. 요청 간 복원 가능한 token mapping도 M7 MVP에 포함하지 않는다.

## 5. Policy selection matrix

| Risk | Entity 예시 | `llm_input` | `external_output` | `audit_log` |
|---|---|---|---|---|
| P0 | RRN, FRN, API key, credential secret | label mask 또는 full redact | API key/secret은 block, 그 외 full redact 가능 | hash only |
| P1 | PHONE, EMAIL, ADDRESS_FULL, BANK_ACCOUNT | label_mask | label_mask | hash only |
| P2 | SCHOOL, ORG, DOB, ADDRESS_UNIT | context/composite 기반 mask 또는 pass | context/composite 기반 mask 또는 pass | hash only |
| P3 | AGE, GENDER 단독 | pass unless composite | pass unless composite | hash only |

## 6. Entity별 기본 정책

| Entity | Risk | MVP 기본 처리 |
|---|---|---|
| API_KEY_SECRET | P0 | `block` |
| RRN, FRN, PASSPORT, DRIVER_LICENSE | P0 | `mask` 또는 `full_redact`; 외부 출력 strict 조건에서는 `block` 가능 |
| CREDIT_CARD | P0/P1 | `mask` |
| BANK_ACCOUNT | P1 | context가 있으면 `mask` |
| PHONE_MOBILE, PHONE_LANDLINE | P1 | 개인 연락처이면 `mask` |
| EMAIL | P1 | `mask` |
| PERSON_NAME | P1/P2 | context 또는 composite가 있으면 `mask` |
| ADDRESS_FULL | P1 | `mask` |
| ADDRESS_UNIT, ORGANIZATION, SCHOOL, HOSPITAL | P2 | context 또는 composite가 있으면 `mask`, 아니면 `pass` 가능 |
| DOB, AGE, GENDER, FAMILY_RELATION | P2/P3 | composite가 있으면 `mask`, 단독이면 `pass` 가능 |
| CUSTOMER_ID, EMPLOYEE_ID, STUDENT_ID, MEDICAL_RECORD_NO | P1/P2 | context가 있으면 `mask` |
| HEALTH_INFO | P1/P2 | domain policy가 정해질 때까지 strict에서는 안전 우선 `mask` |

## 7. Policy selection 의사코드

```python
def select_policy(span, request_context):
    if request_context.output_target == "audit_log":
        return Action.HASH, Method.HMAC_HASH

    if span.entity_type == "API_KEY_SECRET":
        return Action.BLOCK, Method.BLOCK

    if span.risk_level == "P0":
        if request_context.output_target == "external_output":
            return Action.BLOCK, Method.BLOCK
        return Action.MASK, Method.FULL_REDACT

    if span.is_composite:
        return Action.MASK, Method.LABEL_MASK

    if span.risk_level in {"P1"}:
        return Action.MASK, Method.LABEL_MASK

    if span.risk_level in {"P2", "P3"} and has_strong_context(span):
        return Action.MASK, Method.LABEL_MASK

    return Action.PASS, None
```

## 8. Composite policy upgrade

단일 입력 텍스트 내부에서 composite가 확인되면 policy를 강화한다.

| 기존 | Composite 후 |
|---|---|
| P3 pass | P2 mask 가능 |
| P2 pass | P1 수준 mask 가능 |
| P1 mask | P1 mask 유지 |
| P0 | P0 유지 |

예:

```text
성별: 남, 나이: 42세, 학교: OO고, 거주지: 강남구
```

- 각 항목 단독은 P2/P3일 수 있다.
- 같은 입력 안에서 조합되면 준식별 위험이 커진다.
- v0.2에서는 같은 입력 텍스트 내부 조합만 고려한다.

## 9. 한국어 suffix 보존

마스킹은 반드시 PII 본체만 치환하고 suffix를 보존한다.

| 원문 | 잘못된 결과 | 올바른 결과 |
|---|---|---|
| `홍길동이` | `[PERSON_1]` | `[PERSON_1]이` |
| `김민수에게` | `[PERSON_1]` | `[PERSON_1]에게` |
| `010-1234-5678로` | `[PHONE_1]` | `[PHONE_1]로` |
| `test@example.com입니다` | `[EMAIL_1]` | `[EMAIL_1]입니다` |

## 10. Placeholder indexing

### 10.1 요청 내부 안정성

동일 raw value는 같은 요청 내에서 같은 placeholder를 받아야 한다.

```text
홍길동이 왔고 홍길동에게 전화했다.
→ [PERSON_1]이 왔고 [PERSON_1]에게 전화했다.
```

### 10.2 Entity별 index

```text
[PERSON_1], [PERSON_2], [PHONE_1], [ADDRESS_1]
```

### 10.3 Cross-request stability

v0.2 LLM Gateway MVP는 요청 내부 안정성만 제공한다. 요청 간 안정적인 pseudonym 또는 복원형 token mapping은 후속 범위다.

## 11. Audit log policy

감사 로그 target은 transformation method를 `hmac_hash`로 고정한다.

허용 예:

```json
{
  "event_type": "pii_detection",
  "entity_type": "PHONE_MOBILE",
  "score": 0.94,
  "action": "hash",
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

## 12. Future extensions

다음 기능은 현재 LLM Gateway MVP에 포함하지 않는다.

- `internal_ui` target과 partial masking
- `analytics` 또는 `analytics_ai_training` target
- `balanced`, `analytics`, `audit_log` 전용 profile 분리
- `pseudonymize` action과 요청 간 stable pseudonym
- `review` action, human review queue, 운영 콘솔 workflow
- domain-specific policy profile

## 13. Contract alignment status

M7 MVP 계약 정리는 다음 파일에 반영되어야 한다.

- `configs/policy_profiles.yaml`: supported profile/target은 `strict`, `llm_input`, `external_output`, `audit_log`만 둔다.
- `api/openapi.yaml`: request contract enum은 MVP profile/target/action만 허용한다.
- `schemas/guardrail_request.schema.json`: JSON Schema enum은 MVP profile/target만 허용한다.
- `schemas/pii_span.schema.json`: public span action enum은 `candidate`, `pass`, `mask`, `hash`, `block`만 허용한다.
- `src/pii_guardrail/enums.py`: `OutputTarget`과 `Action` enum도 같은 범위로 유지한다.

## 14. 구현 위치

| 항목 | 파일 |
|---|---|
| policy config | `configs/policy_profiles.yaml` |
| entity risk | `configs/entities.yaml` |
| schema fields | `schemas/pii_span.schema.json` |
| policy router | `src/pii_guardrail/policy.py` 예정 |
| masking engine | `src/pii_guardrail/masker.py` 예정 |
| audit logger | `src/pii_guardrail/audit_logger.py` 예정 |
