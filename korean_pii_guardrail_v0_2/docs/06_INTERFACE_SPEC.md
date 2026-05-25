# 인터페이스 명세서 — Korean PII Guardrail v0.2

Version: v0.2-single-turn  
Date: 2026-05-09

## 1. 목적

본 문서는 Korean PII Guardrail v0.2의 Python package interface, detector interface, NER interface, HTTP API contract, request/response schema를 정의한다.

## 2. Interface design principles

1. 모든 detector는 raw offset 기준 `PIISpan`을 반환한다.
2. detector는 최종 action을 결정하지 않는다. 기본 action은 `candidate`이다.
3. policy router가 최종 action과 transformation method를 결정한다.
4. 외부 응답과 로그에는 raw span text를 포함하지 않는다.
5. `session_id`는 v0.2에서 사용하지 않는다.
6. `rag_context` 또는 retrieval document field는 v0.2에서 사용하지 않는다.

## 3. Python public API

### 3.1 GuardrailPipeline

```python
from pii_guardrail import GuardrailPipeline, GuardrailRequest

pipeline = GuardrailPipeline.from_config_dir("configs")

response = pipeline.apply(
    GuardrailRequest(
        text="홍길동이 010-1234-5678로 연락했습니다.",
        scan_stage="input",
        output_target="llm_input",
        policy_profile="strict",
    )
)

print(response.masked_text)
# [PERSON_1]이 [PHONE_1]로 연락했습니다.
```

### 3.2 GuardrailPipeline methods

```python
class GuardrailPipeline:
    @classmethod
    def from_config_dir(cls, config_dir: str) -> "GuardrailPipeline": ...

    def scan(self, request: GuardrailRequest) -> DetectionResult: ...

    def mask(self, request: GuardrailRequest, detection: DetectionResult) -> MaskingResult: ...

    def apply(self, request: GuardrailRequest) -> GuardrailResponse: ...
```

## 4. Detector interface

```python
from typing import Protocol

class Detector(Protocol):
    detector_id: str
    source: str

    def detect(
        self,
        preprocessed: PreprocessResult,
        context: ProcessingContext,
    ) -> list[PIISpan]:
        ...
```

### 4.1 Detector output requirements

- `span.start`와 `span.end`는 raw text offset이어야 한다.
- `span.text == raw_text[span.start:span.end]`여야 한다.
- `span.entity_type`은 `EntityType` enum에 정의되어 있어야 한다.
- `span.score`는 `[0.0, 1.0]` 범위여야 한다.
- `span.action`은 detector 단계에서 `candidate`여야 한다.
- `span.reason_codes`는 최소 1개 이상이어야 한다.

## 5. NER interface

```python
class BaseNERDetector(Protocol):
    detector_id: str = "ner.base"

    def detect(
        self,
        raw_text: str,
        preprocessed: PreprocessResult,
        context: ProcessingContext,
    ) -> list[PIISpan]:
        ...
```

### 5.1 NER label mapping

v0.2의 실제 fine-tuned NER v3 모델은 `NAME`, `ADDRESS`, `ORG` 3개 entity만 BIO token classification으로 출력한다. NER 모델 고유 label은 다음 pipeline label로만 매핑한다.

| NER v3 label | Pipeline entity | 후속 처리 책임 |
|---|---|---|
| `NAME` | PERSON_NAME | boundary/context/resolver |
| `ADDRESS` | ADDRESS_FULL | ADDRESS_UNIT 분기는 dictionary/resolver 후속 처리 |
| `ORG` | ORGANIZATION | SCHOOL/HOSPITAL 세분화는 dictionary/resolver 후속 처리 |

NER v3는 `SCHOOL`, `HOSPITAL`, `ADDRESS_UNIT`, `CUSTOMER_ID`, `MEDICAL_RECORD_NO`를 직접 emit하지 않는다. `SCHOOL`/`HOSPITAL`/`ADDRESS_UNIT`/`MEDICAL_RECORD_NO`는 dictionary, regex, context scorer, resolver의 책임으로 처리한다. `CUSTOMER_ID`/`EMPLOYEE_ID`/`STUDENT_ID`는 production 기본 detector가 추정 생성하지 않으며, 조직별 custom identifier profile이 활성화될 때만 생성 대상이다.

NER label이 위 매핑에 없으면 detector는 해당 span을 반환하지 않는다. v3 통합에서는 `allow_experimental_entities=True`여도 NER 단독으로 새 entity type을 만들지 않는다.

## 6. Dataclass contracts

### 6.1 GuardrailRequest

```python
@dataclass(frozen=True)
class GuardrailRequest:
    text: str
    scan_stage: ScanStage = ScanStage.INPUT
    output_target: OutputTarget = OutputTarget.LLM_INPUT
    policy_profile: str = "strict"
    request_id: str | None = None
    document_id: str | None = None
    purpose_id: str | None = None
    domain: str | None = None
    locale: str = "ko-KR"
    options: GuardrailOptions = field(default_factory=GuardrailOptions)
```

### 6.2 GuardrailOptions

```python
@dataclass(frozen=True)
class GuardrailOptions:
    return_spans: bool = True
    include_audit_events: bool = True
    allow_experimental_entities: bool = False
```

`fail_on_invalid_offset` and `mask_suffix_preserving` are not request options
in v0.2. Invalid raw offsets fail closed, and Korean suffix-preserving masking
is a fixed safety contract. Detector and validator tunables such as regex
selection or checksum strictness belong in configuration profiles, not this
per-request response shaping object.

### 6.3 GuardrailResponse

```python
@dataclass(frozen=True)
class GuardrailResponse:
    request_id: str
    blocked: bool
    masked_text: str | None
    spans: tuple[PublicPIISpan, ...]
    audit_events: tuple[AuditEvent, ...]
    metrics: ResponseMetrics
    policy_profile: str
    output_target: OutputTarget
```

## 7. HTTP API

### 7.1 POST /v1/pii/apply

입력 텍스트를 스캔하고 마스킹 결과를 반환한다.

#### Request

```json
{
  "text": "홍길동이 010-1234-5678로 연락했습니다.",
  "scan_stage": "input",
  "output_target": "llm_input",
  "policy_profile": "strict",
  "request_id": "req-001",
  "document_id": "doc-001",
  "purpose_id": "guardrail_eval_v0",
  "domain": "general",
  "options": {
    "return_spans": true,
    "include_audit_events": true,
    "allow_experimental_entities": false
  }
}
```

#### Response

```json
{
  "request_id": "req-001",
  "blocked": false,
  "masked_text": "[PERSON_1]이 [PHONE_1]로 연락했습니다.",
  "spans": [
    {
      "start": 0,
      "end": 3,
      "span_length": 3,
      "entity_type": "PERSON_NAME",
      "score": 0.91,
      "risk_level": "P1",
      "action": "mask",
      "suffix": "이",
      "is_composite": true,
      "sources": ["ner", "context"],
      "detector_ids": ["mock_ner.person", "context.single_turn"],
      "reason_codes": ["ner.person", "suffix.josa", "context.phone_cooccur"],
      "value_hash": "hmac-sha256:key-v1:..."
    },
    {
      "start": 5,
      "end": 18,
      "span_length": 13,
      "entity_type": "PHONE_MOBILE",
      "score": 0.94,
      "risk_level": "P1",
      "action": "mask",
      "suffix": "로",
      "is_composite": true,
      "sources": ["regex"],
      "detector_ids": ["regex.phone.kr"],
      "reason_codes": ["regex.phone.kr", "suffix.josa.ro"],
      "value_hash": "hmac-sha256:key-v1:..."
    }
  ],
  "audit_events": [
    {
      "event_type": "pii_detection",
      "entity_type": "PERSON_NAME",
      "score": 0.91,
      "risk_level": "P1",
      "action": "mask",
      "span_length": 3,
      "raw_value_logged": false,
      "reason_codes": ["ner.person", "suffix.josa", "context.phone_cooccur"]
    }
  ],
  "metrics": {
    "latency_ms": 12.4,
    "detected_span_count": 2,
    "masked_span_count": 2
  },
  "policy_profile": "strict",
  "output_target": "llm_input"
}
```

### 7.2 POST /v1/pii/scan

탐지만 수행하고 마스킹된 텍스트는 반환하지 않는다.

사용처:

- evaluation
- UI preview
- detector debugging

주의:

- response span에도 raw text는 포함하지 않는다.

### 7.3 POST /v1/pii/mask

호출자가 이미 보유한 span list를 기준으로 마스킹한다.

사용처:

- offline evaluation
- detector A/B test

### 7.4 GET /v1/health

서비스 상태를 반환한다.

```json
{
  "status": "ok",
  "version": "v0.2-single-turn",
  "loaded_profiles": ["strict"],
  "ner_enabled": false
}
```

## 8. API validation rules

| Rule | 처리 |
|---|---|
| `text` empty | 400 Bad Request |
| `text` too long | 413 Payload Too Large 또는 chunking 미지원 |
| invalid `scan_stage` | 400 |
| `scan_stage=retrieval` | 400, v0.2 unsupported |
| `session_id` field present | ignore 또는 400. 기본 권장: 400 with unsupported field |
| unknown `policy_profile` | 400 |
| raw span text requested | 403 |

## 9. Public response safety

Public response는 다음을 포함하면 안 된다.

- `span.text`
- `raw_text`
- `normalized_text` 중 PII 원문 포함 가능 값
- reversible token mapping

Debug 모드에서도 raw PII는 API response에 포함하지 않는다. 필요 시 개발자는 로컬 테스트 fixture에서만 확인한다.

## 10. OpenAPI

OpenAPI 초안은 다음 파일에 있다.

```text
api/openapi.yaml
```

## 11. JSON Schema

| Schema | 파일 |
|---|---|
| PIISpan public schema | `schemas/pii_span.schema.json` |
| DetectionResult | `schemas/detection_result.schema.json` |
| GuardrailRequest | `schemas/guardrail_request.schema.json` |
| GuardrailResponse | `schemas/guardrail_response.schema.json` |
