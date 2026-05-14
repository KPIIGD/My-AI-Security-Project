# 아키텍처 명세서 — Korean PII Guardrail v0.2

Version: v0.2-single-turn  
Date: 2026-05-09

## 1. 아키텍처 원칙

v0.2는 단일 텍스트를 대상으로 하는 다층 탐지·보정·판정·마스킹 pipeline이다.

핵심 원칙은 다음과 같다.

1. detector는 candidate만 생성한다.
2. 최종 boundary는 pipeline이 보정한다.
3. 최종 action은 resolver, context scorer, policy router가 결정한다.
4. 모든 span은 raw text offset 기준이다.
5. raw PII는 audit log에 저장하지 않는다.
6. RAG와 멀티턴 상태는 pipeline에 포함하지 않는다.

## 2. 전체 흐름

```text
GuardrailRequest
  └─ text
      ↓
L0 Preprocessor
  ├─ normalized text
  ├─ variants
  └─ raw offset map
      ↓
L1/L2/L4 Candidate Detectors
  ├─ Regex detectors
  ├─ Dictionary detectors
  └─ NER detector interface
      ↓
L3 Korean Boundary Corrector
  ├─ suffix split
  ├─ numeric PII trim
  └─ corrected raw span
      ↓
L5 Context Scorer
  ├─ field label boost
  ├─ co-occurrence boost
  ├─ negative context penalty
  └─ deterministic context judge
      ↓
L6 Span Resolver
  ├─ duplicate merge
  ├─ overlap priority
  ├─ address merge
  └─ single-turn composite escalation
      ↓
L7 Policy Router + Masker
  ├─ action selection
  ├─ placeholder assignment
  ├─ label mask / hash / block
  └─ Korean suffix-preserving reconstruction
      ↓
GuardrailResponse
  ├─ masked_text
  ├─ public spans
  └─ audit events without raw PII
```

## 3. Layer 명세

### L0. Preprocessor

#### 책임

- 기존 Layer 0에서 확인된 한국어 변형 공격 대응 전략을 v0.2 offset contract에 맞게 재구현한다.
- 입력 텍스트를 탐지 가능한 normalized text와 variant로 변환한다.
- 각 variant의 위치를 raw text offset으로 복원할 수 있게 한다.
- detector가 normalized text에서 탐지하더라도 raw offset으로 결과를 반환할 수 있게 한다.
- 원문을 영구 저장하거나 public response/audit event에 노출하지 않는다.

#### 입력

```python
raw_text: str
```

#### 출력

```python
PreprocessResult(
    raw_text: str,
    normalized_text: str,
    variants: list[TextVariant],
    raw_to_norm: list[int | None],
    norm_to_raw: list[int | None],
    sentences: list[SentenceSpan],
    eojeols: list[TokenSpan]
)
```

#### 설계 결정

`normalized_text`는 보수적 정규화 결과다. 전각 숫자, zero-width 문자, dash, 수학/원문자 숫자처럼 offset 복원이 비교적 안정적인 변환을 포함한다.

L0-derived 고급 복원은 기본 본문을 대체하지 않고 탐지용 `variants`로 생성한다. 예를 들어 `ㅈㅁㅂㅎ`, `jumin`, `즈민뜽록`, `공일공` 같은 입력은 별도 variant에서 복원하고, 탐지 결과는 raw text span으로 되돌린다.

#### TextVariant mapping

고급 변형은 입력과 출력의 길이가 달라질 수 있다. 따라서 variant mapping은 단순히 "variant 문자 index → raw 문자 index"만 가정하지 않는다.

권장 표현:

```python
TextVariant(
    name: str,
    text: str,
    variant_to_raw: tuple[int | None, ...],
    variant_to_raw_span: tuple[tuple[int, int] | None, ...],
)
```

`variant_to_raw`는 1:1 또는 제거 문자 중심 변환에 사용한다. `variant_to_raw_span`은 `jumin` → `주민`, `ㅈㅁㅂㅎ` → `주민번호`처럼 여러 raw 문자가 하나 이상의 variant 문자로 대응되는 경우 사용한다.

#### 필수 기능

| 기능 | 설명 |
|---|---|
| NFKC | 전각 숫자/문자 정규화, raw offset map 유지 |
| dash normalization | `‐`, `‑`, `–`, `—`, `−` 등을 `-`로 통합 |
| zero-width handling | zero-width char 제거, 제거 위치 mapping 유지 |
| mathematical/circled digit normalization | `𝟘`, `①` 등 숫자형 동형문자 정규화 |
| digit compact | 전화번호/계좌번호 후보 탐지용 compact variant |
| digit-space compact | 숫자 사이 공백 제거 variant |
| Korean keyword spacing compact | PII keyword 띄어쓰기 변형 대응 |
| jamo composition variant | `ㅈㅜㅁㅣㄴ` 등 자모 분해 입력 복원 |
| choseong restoration variant | `ㅈㅁㅂㅎ` 등 초성 축약 입력 복원 |
| yaminjeongeum restoration variant | `즈민뜽록` 등 야민정음 입력 복원 |
| romanized Korean restoration variant | `jumin`, `jeonhwa` 등 로마자 한국어 입력 복원 |
| Korean digit variant | `공일공` 등 연락처 문맥 숫자화 |
| sentence split | context window boundary |
| eojeol split | context window 단위 |

#### Kiwi 활용 원칙

Kiwi/kiwipiepy는 문장 분리, 형태소/조사/어미 분석, 어절 경계 품질 비교를 위한 optional reference 또는 benchmark로 사용할 수 있다.

단, Kiwi의 `space()`처럼 원문 문자열을 재작성하는 기능은 기본 `normalized_text`로 직접 사용하지 않는다. 사용할 경우 offset-aware 탐지용 variant로만 사용하고 raw span 복원 실패 시 해당 candidate를 reject한다.

### L1. Regex Detectors

#### 책임

구조형 개인정보와 보안비밀을 탐지한다.

#### Detector 목록

| Detector | Entity |
|---|---|
| `RRNRegexDetector` | RRN |
| `FRNRegexDetector` | FRN |
| `PhoneRegexDetector` | PHONE_MOBILE, PHONE_LANDLINE |
| `EmailRegexDetector` | EMAIL |
| `CreditCardRegexDetector` | CREDIT_CARD |
| `BusinessRegNoDetector` | BUSINESS_REG_NO |
| `BankAccountCandidateDetector` | BANK_ACCOUNT |
| `NetworkIdentifierDetector` | IP_ADDRESS, MAC_ADDRESS |
| `SecretRegexDetector` | API_KEY_SECRET |

#### 출력 계약

```python
list[PIISpan]
```

각 `PIISpan`은 `source="regex"`, `action="candidate"`로 반환한다.

### L2. Dictionary Detectors

#### 책임

사전 기반 후보 또는 context evidence를 생성한다.

사전 match는 최종 마스킹 판정자가 아니다. 단독으로 high confidence를 주지 않는다.

#### Dictionary 종류

| Dictionary | 용도 |
|---|---|
| surnames | 성씨 후보 |
| given_name_candidates | 이름 후보 |
| address_terms | 주소 후보 및 context |
| road_terms | 도로명/지번 후보 |
| banks | 계좌 context |
| titles | 호칭/직함 context |
| relation_terms | 가족관계 context |
| organization_suffixes | 조직 후보 |
| negative_context_terms | 오탐 억제 |

### L3. Korean Boundary Corrector

#### 책임

후보 span에 붙은 조사·호칭·어미를 분리하고 PII 본체 offset을 수정한다.

#### 처리 원칙

- 전처리 단계에서 전역적으로 suffix를 제거하지 않는다.
- detector가 생성한 candidate에만 후처리로 적용한다.
- suffix는 마스킹에서 보존한다.
- raw text 밖의 문자를 변경하지 않는다.

#### Entity별 적용

| Entity | 처리 |
|---|---|
| PERSON_NAME | 조사/호칭/호격 분리 |
| ADDRESS_FULL | 조사/위치격 분리 |
| ORGANIZATION | 조사/호칭 분리 |
| SCHOOL/HOSPITAL | 조사 분리 |
| PHONE/EMAIL/RRN | 후행 조사/종결어미 trim |
| API_KEY_SECRET | suffix 분리보다 block 우선 |

### L4. NER Detector Interface

#### 책임

비정형 개인정보 후보를 공급한다.

#### 주의

- real NER fine-tuning은 v0.2 pipeline 개발의 선행조건이 아니다.
- mock NER로 pipeline을 먼저 완성한다.
- NER output은 final span이 아니다.
- NER score는 calibrated confidence여야 한다.

### L5. Context Scorer

#### 책임

단일 입력 텍스트 내부 문맥으로 score를 보정한다.

#### Window 정의

| 항목 | v0.2 정의 |
|---|---|
| 단위 | 어절 |
| 크기 | 후보 기준 ±5 어절 |
| 문장 제한 | 같은 문장 내부로 제한 |
| field label | 같은 문장 내 전체 위치 허용 |
| co-occurrence | 같은 문장 내 PII만 인정 |
| form/table | v0.2 범위 외 |
| 이전 턴 | v0.2 범위 외 |

#### Feature

- field label: `성명`, `고객명`, `연락처`, `배송지`, `계좌`, `환자번호`
- honorific/title: `님`, `씨`, `과장`, `팀장`, `교수`, `변호사`
- co-occurrence: `PERSON + PHONE`, `PERSON + ADDRESS`, `BANK + ACCOUNT`
- negative context: `예시`, `테스트`, `샘플`, `날씨`, `대표번호`

### L6. Span Resolver

#### 책임

여러 detector가 반환한 후보를 최종 span set으로 정리한다.

#### 주요 정책

1. 동일 span은 merge한다.
2. 점수는 max score를 채택한다.
3. source list는 보존한다.
4. 겹침 span은 priority table로 결정한다.
5. address fragment는 가능한 경우 `ADDRESS_FULL`로 병합한다.
6. single-turn composite 승격을 최종 결정한다.

### L7. Policy Router + Masker

#### 책임

최종 span에 action과 transformation method를 적용한다.

#### Transformation

| Method | 예시 |
|---|---|
| label_mask | `[PERSON_1]` |
| hmac_hash | `hmac-sha256:...` |
| block | 응답 차단 |
| pass | 원문 유지 |

v0.2 LLM Gateway MVP에서 L7은 `llm_input`, `external_output`, `audit_log` target을 우선 지원한다. 내부 UI partial masking, 분석용 pseudonymization, review workflow는 future extension이다.

## 4. 데이터 객체

### 4.1 Internal PIISpan

`PIISpan`은 pipeline 내부에서는 raw `text`를 보유할 수 있다. 단, log/public response 변환 시 raw `text`는 제거해야 한다.

```python
@dataclass(frozen=True)
class PIISpan:
    start: int
    end: int
    text: str
    entity_type: EntityType
    score: float
    sources: tuple[str, ...]
    risk_level: RiskLevel
    action: Action = Action.CANDIDATE
    normalized: str | None = None
    suffix: str | None = None
    reason_codes: tuple[str, ...] = ()
    detector_ids: tuple[str, ...] = ()
    is_composite: bool = False
    policy_profile: str | None = None
    output_target: OutputTarget | None = None
```

### 4.2 Public span

외부 응답이나 audit에는 raw `text`를 포함하지 않는다.

```json
{
  "start": 0,
  "end": 3,
  "span_length": 3,
  "entity_type": "PERSON_NAME",
  "score": 0.91,
  "risk_level": "P1",
  "action": "mask",
  "suffix": "이",
  "value_hash": "hmac-sha256:...",
  "sources": ["ner", "context"],
  "reason_codes": ["ner.person", "suffix.josa", "context.phone_cooccur"]
}
```

## 5. Error Handling

| Error | 조건 | 처리 |
|---|---|---|
| `InvalidOffsetError` | `text != raw[start:end]` | detector output reject |
| `UnknownEntityTypeError` | config에 없는 entity | reject 또는 experimental flag 필요 |
| `PolicyConfigError` | policy profile 없음 | default strict 사용 또는 실패 |
| `UnsafeAuditPayloadError` | audit event에 raw text 포함 | event reject, test fail |
| `NormalizationMapError` | offset 복원 실패 | 해당 candidate reject |

## 6. 확장 포인트

v0.2에서 구현하지 않지만, 구조상 확장 가능한 포인트는 다음이다.

| 확장 | 현재 상태 |
|---|---|
| Real NER | `BaseNERDetector` interface 뒤에 연결 |
| Reversible tokenization | `TokenizationProvider` 별도 interface 필요 |
| RAG scan | v1에서 `scan_stage=retrieval` 재설계 필요 |
| Multi-turn | v1에서 `SessionMonitor` 독립 module로 설계 필요 |
| LLM judge | v1에서 context judge fallback으로 제한적 도입 |

## 7. 금지 설계

다음 설계는 v0.2에서 금지한다.

- detector가 normalized offset만 반환
- NER 결과를 바로 마스킹
- dictionary match를 단독 high-confidence PERSON으로 처리
- raw PII를 log/metric/report에 저장
- `session_id`를 필수 입력으로 요구
- RAG context용 field를 API 필수값으로 추가
- 모든 모호한 case를 LLM judge로 전송
