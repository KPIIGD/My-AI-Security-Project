# Compliance and Audit 명세서

Version: v0.2-single-turn  
Date: 2026-05-09

## 1. 목적

본 문서는 Korean PII Guardrail v0.2가 가명정보 처리 및 안전한 관리 원칙에 맞게 동작하기 위한 policy, audit, logging, report 요구사항을 정의한다.

## 2. 적용 원칙

v0.2 guardrail은 단순 탐지기가 아니라 LLM Gateway에서 masked/hash-safe output을 생성하는 시스템이다. 따라서 다음을 분리해 관리한다.

1. 개인정보 탐지
2. 비식별화/마스킹
3. HMAC/hash 기반 추적
4. 적정성 검토 및 평가 리포트
5. 안전한 로그 관리

분석용 가명처리와 복원형 tokenization은 v0.2 LLM Gateway MVP의 1차 범위가 아니며, 필요한 경우 후속 확장으로 별도 설계한다.

## 3. 가명처리 lifecycle mapping

| 단계 | Guardrail artifact | 산출물 |
|---|---|---|
| 사전 준비 | 목적/대상/정책 profile 정의 | `purpose_id`, data use note |
| 위험성 검토 | risk level, entity taxonomy | risk decision, reason codes |
| 마스킹/해시 처리 | masker/hash provider | masked text, public spans, value hash |
| 적정성 검토 | evaluation harness | metrics, residual risk report |
| 안전한 관리 | audit logger, key management | no raw PII logs, HMAC event |

## 4. Processing context

요청 또는 batch job은 다음 context를 기록할 수 있다.

```yaml
processing_context:
  purpose_id: "ko_pii_guardrail_v0_2_eval"
  purpose_description: "Korean PII detection and masking evaluation"
  data_controller: "internal"
  recipient_type: "internal"
  environment_control: "high"
  data_modality: "text"
  contains_sensitive_domain: false
  retention_ttl_days: 90
  raw_pii_logging_allowed: false
  human_review_required: false
```

Implementation note (M8): `retention_ttl_days: 90` remains the target
retention requirement. The current cleanup script only handles exact
`RotatingFileHandler` backup files by file mtime; event-level TTL enforcement
for individual audit events requires a separate follow-up design. The active
audit log is not removed by the script, and `backupCount` can evict rotated
backups before 90 days under high log volume.

## 5. Raw PII 금지 원칙

### 5.1 금지 위치

다음 위치에는 raw PII가 저장되어서는 안 된다.

- application log
- audit log
- telemetry
- metrics label
- evaluation report
- failure report
- exception message
- tracing span attribute
- model prompt log
- public API response span text

### 5.2 예외

pipeline 내부 메모리에서는 마스킹 처리를 위해 raw text를 일시적으로 사용할 수 있다. 단, 저장·로그·외부 응답에는 포함하지 않는다.

## 6. AuditEvent schema

```json
{
  "event_type": "pii_detection",
  "timestamp": "2026-05-09T00:00:00Z",
  "request_id": "req-001",
  "policy_profile": "strict",
  "output_target": "llm_input",
  "entity_type": "PHONE_MOBILE",
  "source": ["regex"],
  "detector_ids": ["regex.phone.kr"],
  "score": 0.94,
  "risk_level": "P1",
  "action": "mask",
  "value_hash": "hmac-sha256:key-v1:...",
  "span_length": 13,
  "reason_codes": ["regex.phone.kr", "suffix.josa.ro"],
  "raw_value_logged": false
}
```

## 7. HMAC/hash policy

| 항목 | 기준 |
|---|---|
| Algorithm | HMAC-SHA256 이상 |
| Key id | event에 `key_id` 또는 hash prefix로 기록 |
| Key storage | application config와 분리 |
| Raw value | 저장 금지 |
| Duplicate tracking | HMAC hash로만 수행 |
| Rotation | key version 관리 |

## 8. 추가정보 관리

가명처리 또는 복원형 tokenization에서 특정 개인을 복원할 수 있는 정보는 추가정보로 본다.

v0.2 기본 정책은 복원형 tokenization을 사용하지 않는 것이다. 다만 향후 복원형 tokenization이 필요하면 다음을 지켜야 한다.

- token mapping은 main application DB와 분리
- 복원 권한은 별도 role로 분리
- 복원 event는 별도 access log 작성
- mapping TTL 및 파기 정책 명시
- API response에 mapping 포함 금지

## 9. Gateway masking result report

Batch 또는 evaluation 수행 후 다음 JSON report를 생성할 수 있어야 한다.

```json
{
  "report_type": "GatewayMaskingResultReport",
  "version": "v0.2-single-turn",
  "purpose_id": "ko_pii_guardrail_v0_2_eval",
  "policy_profile": "strict",
  "dataset_id": "hard_cases_v0",
  "records_processed": 1400,
  "spans_detected": 0,
  "spans_masked": 0,
  "high_risk_recall": null,
  "boundary_accuracy": null,
  "raw_pii_logging_count": 0,
  "residual_risk_notes": [],
  "generated_at": "2026-05-09T00:00:00Z"
}
```

## 10. 안전 검증 checklist

| Check | Required |
|---|---:|
| raw PII audit log 없음 | Yes |
| public response raw text 없음 | Yes |
| HMAC key 분리 | Yes |
| policy profile 명시 | Yes |
| purpose_id 기록 | Recommended |
| evaluation report raw text 제거 | Yes |
| exception message raw text 제거 | Yes |
| test fixture는 synthetic | Yes |
| production PII를 unit test에 사용하지 않음 | Yes |

## 11. Incident handling

마스킹 또는 해시 처리 후 특정 개인 식별 가능성이 발견되면 다음 순서로 처리한다.

1. 해당 output 또는 dataset 사용 중지
2. 원인 span/entity/reason code를 raw 없이 hash 기반으로 식별
3. detector/context/policy rule 보완
4. 재평가 수행
5. residual risk report 갱신
6. 필요한 경우 파기 또는 추가 마스킹 수행

## 12. v0.2 문서화 산출물

| 문서 | 담당 |
|---|---|
| Data Use Note | Compliance Owner |
| Risk Review Note | Compliance Owner + Tech Lead |
| Gateway Masking Policy Plan | Pipeline Owner |
| Gateway Masking Result Report | Evaluation Owner |
| Audit Safety Report | Pipeline Owner |
| Residual Risk Register | Evaluation Owner |
