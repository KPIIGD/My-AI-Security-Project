# Score Composition 명세서

Version: v0.2-single-turn  
Date: 2026-05-09

## 1. 목적

본 문서는 Korean PII Guardrail v0.2에서 detector별 base score, context adjustment, score merge, threshold, risk/action mapping을 정의한다.

초기 슬라이드의 공백이었던 다음 항목을 구현 명세로 고정한다.

- L1 Regex entity별 base score
- L2 Dictionary 사전 종류별 base score
- L4 NER confidence calibration 방식
- 여러 detector가 같은 span을 잡았을 때 점수 결합 방식
- 0.55 / 0.75 / 0.90 threshold의 사용 방식
- context judge 동작 방식

## 2. 기본 원칙

1. 모든 score는 `[0.0, 1.0]` 범위의 calibrated confidence로 해석한다.
2. detector가 같은 span을 잡으면 `max(score)`를 채택한다.
3. detector source와 detector id는 list로 보존한다.
4. Bayesian 결합은 v0.2에서 사용하지 않는다.
5. context adjustment는 max로 병합된 candidate score에 더한다.
6. 최종 score는 clamp한다.
7. threshold는 초기값이며 gold set PR curve로 조정 가능해야 한다.

## 3. Score 계산 공식

### 3.1 Candidate base score

```text
base_score(span) = max(detector_score_1, detector_score_2, ...)
```

### 3.2 Context adjustment

```text
context_delta = sum(boosts) - sum(penalties)
```

### 3.3 Final score

```text
final_score = clamp(base_score + context_delta, 0.0, 1.0)
```

### 3.4 동일 span merge

동일 span 조건:

```text
same start, same end, same entity_type
```

처리:

```text
score = max(scores)
sources = union(sources)
detector_ids = union(detector_ids)
reason_codes = union(reason_codes)
```

### 3.5 overlap span 처리

겹침 span은 L6 Span Resolver에서 priority table을 적용한다. score가 높은 span이 항상 우선하지 않는다.

예:

```text
test@example.com
```

- EMAIL score 0.90
- PERSON_NAME candidate `test` score 0.60
- EMAIL이 priority상 우선한다.

## 4. Regex base score

| Entity | 조건 | Base score | 설명 |
|---|---|---:|---|
| API_KEY_SECRET | prefix + length + entropy 통과 | 0.99 | 보안비밀, block 후보 |
| RRN | 날짜/성별 digit/길이 + checksum 통과 | 0.98 | P0 recall 우선 |
| FRN | 날짜/성별 digit/길이 + checksum 통과 | 0.98 | P0 recall 우선 |
| CREDIT_CARD | Luhn 통과 | 0.96 | 금융 직접식별 |
| CREDIT_CARD | Luhn 미통과 but 카드형 패턴 | 0.45 | candidate만 유지 가능 |
| EMAIL | domain 구조 통과 | 0.92 | suffix trim 필요 |
| PHONE_MOBILE | 국내 모바일 패턴 + 길이 통과 | 0.94 | 한글 숫자 variant 포함 |
| PHONE_LANDLINE | 지역번호/길이 통과 | 0.90 | 대표번호 negative context 가능 |
| BUSINESS_REG_NO | checksum 통과 | 0.92 | checksum 미구현 시 0.75로 시작 |
| CORPORATE_REG_NO | 형식 통과 | 0.90 | v0.2 선택 구현 |
| BANK_ACCOUNT | 숫자 패턴만 | 0.42 | context 없이는 마스킹 금지 |
| BANK_ACCOUNT | 은행명/계좌 label co-occur | 0.78 | context scorer 후 승격 |
| IP_ADDRESS | valid public IP | 0.72 | policy별 처리 |
| IP_ADDRESS | private/local IP | 0.45 | 내부 정책에 따라 pass 가능 |
| MAC_ADDRESS | MAC 형식 | 0.70 | device identifier 후보 |
| CUSTOMER_ID | label + id pattern | 0.72 | label 없으면 낮게 시작 |
| EMPLOYEE_ID | label + id pattern | 0.72 | label 없으면 낮게 시작 |
| STUDENT_ID | label + id pattern | 0.72 | label 없으면 낮게 시작 |
| MEDICAL_RECORD_NO | 의료 label + id pattern | 0.82 | domain high-risk |

## 5. Dictionary base score

Dictionary는 최종 판정자가 아니다. 단독 score는 낮게 시작한다.

| Dictionary | Entity/evidence | Base score | 비고 |
|---|---|---:|---|
| surname | PERSON_NAME candidate | 0.25 | 단독 마스킹 금지 |
| given_name_candidate | PERSON_NAME candidate | 0.35 | 중의성 높음 |
| full_name_pattern | PERSON_NAME candidate | 0.55 | 성+이름 2~4자 |
| title/honorific | context evidence | 0.00 | score 직접 생성보다 boost |
| relation_term | FAMILY_RELATION | 0.40 | 단독 PII 아님 |
| address_si_gu_dong | ADDRESS_UNIT | 0.45 | 단독 위험 낮음 |
| road_name | ADDRESS_FULL candidate | 0.65 | 번지/동호수 있으면 boost |
| apartment_unit | ADDRESS_UNIT | 0.70 | 상세주소 위험 높음 |
| bank_name | context evidence | 0.00 | 계좌 boost용 |
| organization_suffix | ORGANIZATION | 0.50 | NER/context 필요 |
| school_suffix | SCHOOL | 0.55 | 준식별자 |
| hospital_suffix | HOSPITAL | 0.60 | 의료 context 시 상승 |
| negative_context | penalty evidence | 0.00 | penalty 적용 |

## 6. NER score calibration

### 6.1 계약

NER detector는 pipeline에 calibrated confidence를 제공해야 한다.

```text
PIISpan.score = P(candidate span is correct | model raw confidence, entity type)
```

### 6.2 v0.2 target calibration 방식

v0.2 기준 방식은 temperature scaling이다.

```text
calibrated_score = softmax(logits / T)
```

- `T`는 validation set에서 학습한다.
- entity별 calibration을 우선한다.
- entity별 데이터가 부족하면 shared temperature를 사용한다.
- calibration이 불가능한 mock NER는 명시적으로 `reason_codes += mock_ner.uncalibrated`를 붙인다.

### 6.3 NER v3 현재 상태

fine-tuned NER v3는 production candidate로 채택되었지만, 현재 scoring 관점에서는 `temperature=1.0`이며 사실상 uncalibrated 상태다. M5 이후 문서와 구현은 이를 calibration 완료로 간주하지 않는다.

v3는 `calibration.json`의 per-entity threshold를 임시 운영 기준으로 사용한다.

| Pipeline entity | NER v3 threshold |
|---|---:|
| PERSON_NAME | 0.85 |
| ADDRESS_FULL | 0.80 |
| ORGANIZATION | 0.75 |

NER raw score는 `[0, 1]` score band에 그대로 투입한다. threshold 미만의 low-confidence span도 raw offset 계약을 만족하면 candidate로 남길 수 있으며, dictionary/context 보강 또는 resolver 판단의 입력으로 사용할 수 있다. 단, NER v3는 `NAME`, `ADDRESS`, `ORG` 이외 entity를 직접 생성하지 않는다.

ECE, reliability diagram, temperature scaling 또는 isotonic calibration은 M10 evaluation/tuning 후속 작업으로 남긴다.

### 6.4 검증 지표

| Metric | 목적 |
|---|---|
| ECE | confidence calibration 품질 |
| reliability diagram | score 구간별 실제 정답률 확인 |
| entity-wise ECE | PERSON/ADDRESS 등 entity별 과신 확인 |

## 7. Context adjustment

### 7.1 Boost rules

| Rule | 적용 entity | Delta | 조건 |
|---|---|---:|---|
| `field_label.name` | PERSON_NAME | +0.25 | 같은 문장에 `성명`, `고객명`, `이름` |
| `field_label.phone` | PHONE | +0.15 | 같은 문장에 `연락처`, `전화번호`, `휴대폰` |
| `field_label.address` | ADDRESS | +0.20 | 같은 문장에 `주소`, `배송지`, `거주지` |
| `field_label.account` | BANK_ACCOUNT | +0.30 | 같은 문장에 `계좌`, `입금`, `송금` |
| `bank_cooccur` | BANK_ACCOUNT | +0.25 | 같은 문장에 은행명 |
| `title_after_name` | PERSON_NAME | +0.15 | 후보 뒤 `님`, `씨`, `과장`, `팀장` 등 |
| `phone_cooccur` | PERSON_NAME | +0.20 | 같은 문장에 PHONE 존재 |
| `address_cooccur` | PERSON_NAME | +0.15 | 같은 문장에 ADDRESS 존재 |
| `full_address_detail` | ADDRESS_FULL | +0.20 | 도로명/번지/동호수 결합 |
| `medical_label` | MEDICAL_RECORD_NO/HOSPITAL/HEALTH_INFO | +0.20 | `환자`, `진료`, `차트`, `의무기록` |

### 7.2 Penalty rules

| Rule | 적용 entity | Delta | 조건 |
|---|---|---:|---|
| `example_context` | all | -0.15 | `예시`, `샘플`, `테스트` |
| `weather_context` | PERSON_NAME | -0.35 | `하늘`, `가을`, `봄` 등이 날씨/계절 문맥 |
| `public_phone_context` | PHONE | -0.25 | `대표번호`, `고객센터`, `공공기관 안내` |
| `code_or_log_context` | PERSON_NAME/ADDRESS | -0.20 | 코드, stack trace, placeholder 문맥 |
| `organization_not_person` | PERSON_NAME | -0.25 | 후보가 상호/조직명 내부에 포함 |
| `private_ip` | IP_ADDRESS | -0.25 | 사설 IP 또는 localhost |

## 8. Threshold 및 action mapping

### 8.1 Global score bands

| Score band | 기본 의미 |
|---|---|
| `>= 0.90` | high confidence, mask/block |
| `0.75 <= score < 0.90` | mask 또는 review |
| `0.55 <= score < 0.75` | context judge 대상 |
| `< 0.55` | pass, 단 composite 또는 P0 특례 제외 |

### 8.2 Risk-level 별 action

| Risk | Score | Action |
|---|---:|---|
| P0 | `>= 0.55` | mask 또는 block |
| P0 | `< 0.55` | review if structured-like |
| P1 | `>= 0.75` | mask |
| P1 | `0.55~0.75` | context judge, 안전 우선 mask 가능 |
| P1 | `<0.55` | pass unless composite |
| P2 | `>=0.90` | mask/review |
| P2 | `0.75~0.90` | review 또는 context judge |
| P2 | `<0.75` | pass unless composite |
| P3 | `>=0.90` | review |
| P3 | `<0.90` | pass unless composite |

### 8.3 P0 action policy

| Entity | Default action |
|---|---|
| API_KEY_SECRET | block |
| RRN | mask 또는 block, profile별 |
| FRN | mask 또는 block, profile별 |
| CREDIT_CARD | mask |
| PASSPORT | mask |
| DRIVER_LICENSE | mask |

## 9. Single-turn composite escalation

v0.2의 composite는 같은 입력 텍스트 내부에 한정한다.

### 9.1 Composite 조건

| 조합 | 조건 | Risk adjustment |
|---|---|---|
| PERSON + PHONE | 같은 문장 | P1 |
| PERSON + EMAIL | 같은 문장 | P1 |
| PERSON + ADDRESS_FULL | 같은 문장 | P1 |
| PERSON + BANK_ACCOUNT | 같은 문장 | P1 |
| DOB + ADDRESS_UNIT + SCHOOL | 같은 문장 또는 짧은 field block | P1/P2 |
| CUSTOMER_ID + PHONE/EMAIL | 같은 문장 | P1 |
| MEDICAL_RECORD_NO + HOSPITAL | 같은 문장 | P1 |

### 9.2 Composite 처리 책임

| Layer | 책임 |
|---|---|
| L5 Context Scorer | composite evidence 표시 |
| L6 Span Resolver | `is_composite=true`, risk_level 조정 최종 결정 |
| L7 Policy Router | composite면 policy 강화 |

## 10. Tuning 절차

1. v0.2 초기값으로 평가셋 실행
2. entity별 PR curve 작성
3. P0/P1 high-risk recall 목표 우선 충족
4. P2/P3 false positive 확인
5. context boost/penalty 조정
6. threshold profile 확정
7. 변경 전후 ablation report 작성

## 11. 구현 위치

| 항목 | 파일 |
|---|---|
| base score | `configs/scoring.yaml` |
| context delta | `configs/context_rules.yaml` |
| risk/action mapping | `configs/policy_profiles.yaml` |
| score composition code | `src/pii_guardrail/interfaces.py`, `context_scorer.py` 예정 |
| tests | `tests/test_scoring.py` 예정 |
