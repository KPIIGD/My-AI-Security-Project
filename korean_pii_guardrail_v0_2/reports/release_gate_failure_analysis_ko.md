# Korean PII Guardrail v0.2 5,000건 Release Gate 최신 분석 보고서

생성일: 2026-05-24 KST
평가 대상: `release_gate_v0_2` 5,000건 합성 평가셋
평가 방식: `scripts/run_release_gate.py --cases-per-bucket 1000`
NER 모드: real NER (`ner.finetuned.klue-roberta-large-v3`)
원문 정책: 이 보고서는 raw PII 값을 포함하지 않고, case ID/템플릿/집계 수치만 기록한다.

## 1. 요약

이번 5,000건 재평가에서 release gate는 통과했다. 구조형 PII와 주소/조직/학교/병원 계열은 안정화됐고, 남은 점수 손실은 `PERSON_NAME` 후보 품질과 hard negative candidate noise에 집중되어 있다.

| 지표 | 값 |
|---|---:|
| Release gate | PASS |
| Overall precision | 0.8803 |
| Overall recall | 0.9729 |
| Overall F1 | 0.9243 |
| Actionable precision | 0.9974 |
| Actionable recall | 0.8776 |
| Actionable F1 | 0.9337 |
| High-risk recall | 0.9647 |
| Actionable high-risk recall | 0.9308 |
| Boundary accuracy | 1.0000 |
| raw PII logging count | 0 |
| invalid offset count | 0 |
| deterministic latency p95 | 293.9683 ms |

`deterministic latency p95`는 real NER 경로가 포함된 실행값이다. deterministic-only CPU path 기준과 real NER latency는 별도 계측해야 한다.

## 2. 버킷별 결과

| 버킷 | F1 | Precision | Recall | 주요 해석 |
|---|---:|---:|---:|---|
| `structured_pii` | 1.0000 | 1.0000 | 1.0000 | 정형 식별자류는 release gate 범위에서 안정적이다. |
| `adversarial_boundary` | 0.9991 | 0.9991 | 0.9991 | 경계/변형 대응은 안정적이며, 잔여 1건은 이름/주소 타입 혼동이다. |
| `name_address_affiliation` | 1.0000 | 1.0000 | 1.0000 | 이름, 주소, 조직/학교/병원 조합 버킷은 현재 기준 통과한다. |
| `single_turn_composite` | 0.9597 | 0.9940 | 0.9276 | 이름+연락처/계좌 문맥에서 `PERSON_NAME` 누락이 남아 있다. |
| `hard_negative` | 0.0000 | 0.0000 | 0.0000 | positive label이 없는 버킷이라 F1 자체는 해석 가치가 낮다. 최종 action은 모두 `pass`다. |

## 3. 실패 유형 집계

`reports/failure_cases_release_gate_v0_2.jsonl` 기준 failure row는 다음과 같다.

| 유형 | 건수 | 설명 |
|---|---:|---|
| FN | 156 | gold label이 있는데 탐지하지 못한 경우 |
| FP | 750 | hard negative에서 public candidate로 남은 경우 |
| TYPE_CONFUSION | 13 | 위치는 겹치지만 엔티티 타입이 다른 경우 |
| 총 failure row | 919 | 하나의 case가 여러 failure row를 가질 수 있음 |

엔티티별 상위 실패는 다음과 같다.

| 엔티티 / 실패 | 건수 | 해석 |
|---|---:|---|
| `PERSON_NAME` FP | 500 | hard negative에서 이름형 일반명사가 candidate로 남는다. 대부분 최종 action은 `pass`다. |
| `PERSON_NAME` FN | 156 | composite positive 문맥에서 이름을 놓친다. |
| `EMAIL` FP | 125 | 예시 이메일 candidate가 public span에 남지만 최종 action은 `pass`다. |
| `PHONE_MOBILE` FP | 125 | 예시 전화번호 candidate가 public span에 남지만 최종 action은 `pass`다. |
| `ADDRESS_FULL` TYPE_CONFUSION | 13 | 일부 이름 fixture 또는 경계 케이스가 주소로 오분류된다. |

## 4. 누락(FN) 분석

`PERSON_NAME` FN 156건은 거의 모두 `single_turn_composite` 버킷에 집중된다.

| 패턴 | 실패 엔티티 | 건수 | 원인 |
|---|---|---:|---|
| `{PERSON}의 연락처 {PHONE}` 계열 | `PERSON_NAME` | 155 | real NER가 소유격/연락처 문맥의 이름을 안정적으로 잡지 못한다. |
| adversarial boundary tail case | `PERSON_NAME` | 1 | 이름 위치가 `ADDRESS_FULL`로 오분류된 특이 케이스다. |

구조형 PII 경로 자체의 recall 문제는 현재 release gate에서 확인되지 않았다. `structured_pii` 버킷의 전체 F1은 1.0000이다.

## 5. 오탐 및 타입 혼동 분석

현재 candidate-level FP는 hard negative에 집중되어 있다. 중요한 점은 이 후보들이 사용자-visible action으로 이어지지 않는다는 것이다.

| 실패 | 건수 | 분석 |
|---|---:|---|
| hard negative `PERSON_NAME` FP | 500 | 일반명사, 추상명사, 상호명 내부 이름형 문자열이 후보로 잡힌다. 정책 단계에서 `pass`된다. |
| hard negative `EMAIL` FP | 125 | 예시 이메일이 정규식 후보로 잡힌다. 정책 단계에서 `pass`된다. |
| hard negative `PHONE_MOBILE` FP | 125 | 예시 전화번호가 정규식 후보로 잡힌다. 정책 단계에서 `pass`된다. |
| `ADDRESS_FULL` TYPE_CONFUSION | 13 | 대부분 single-turn composite에서 이름 fixture가 주소로 오분류되는 케이스다. |

이 때문에 overall precision은 candidate-level public span의 영향을 받지만, actionable precision은 0.9974로 높게 유지된다.

## 6. NER 외 문제

NER가 큰 잔여 과제인 것은 맞지만, NER 외에도 다음 해석상 주의점이 있다.

### 6.1 Candidate-level overall metric의 해석

현재 overall 지표는 public span 후보를 모두 prediction으로 본다. 정책에서 `pass`된 hard negative 후보도 response span에 남아 있으면 FP가 된다. 따라서 실제 마스킹 오탐 판단에는 actionable metric을 함께 봐야 한다.

개선 방향:

- 보고서에서 candidate-level metric과 actionable metric을 명확히 분리한다.
- hard negative는 F1보다 최종 action이 `pass`인지, raw PII safety가 유지되는지를 우선 본다.
- public candidate noise는 NER calibration과 후처리 단순화 관점에서 별도 추적한다.

### 6.2 NER score calibration

NER v3는 `NAME`, `ADDRESS`, `ORG`만 직접 emit하고, 현재 score는 temperature 1.0 기반이다. hard negative에서 `PERSON_NAME` candidate가 500건 남는 점을 보면 confidence calibration과 hard negative 학습 보강이 필요하다.

개선 방향:

- `NAME`, `ADDRESS`, `ORG` entity별 threshold sweep을 별도 산출한다.
- composite positive와 hard negative를 함께 평가한다.
- `PERSON_NAME` recall을 올리기 위해 threshold만 낮추는 방식은 피한다.

### 6.3 ADDRESS granularity와 이름-주소 타입 혼동

`ADDRESS_UNIT` 자체는 현재 release gate에서 precision/recall/F1이 모두 1.0000이다. 다만 NER backlog 관점에서는 `ADDRESS` 라벨이 pipeline에서 `ADDRESS_FULL`로 매핑되는 구조와 이름 fixture의 `ADDRESS_FULL` 오분류 13건을 계속 추적해야 한다.

개선 방향:

- NER의 `ADDRESS` 라벨 granularity 기준을 문서화한다.
- 이름과 주소 표면형이 경쟁하는 span을 대조 평가셋에 넣는다.
- 세부주소 토큰이 없는 주소는 resolver가 `ADDRESS_UNIT`으로 낮출 수 있는지 점검한다.

## 7. NER가 개선됐을 때의 예상 영향

현재 수치:

| 항목 | 값 |
|---|---:|
| TP exact | 5,611 |
| FP | 763 |
| FN | 156 |
| Overall F1 | 0.9243 |

가정별 영향:

| 가정 | 예상 효과 |
|---|---|
| `PERSON_NAME` FN 156건 개선 | recall과 F1이 추가 상승한다. |
| hard negative `PERSON_NAME` candidate 500건 감소 | candidate precision 해석이 개선되고 후처리 규칙을 줄일 수 있다. |
| 이름의 `ADDRESS_FULL` 오분류 13건 개선 | 남은 타입 혼동이 거의 해소된다. |

## 8. 권장 개선 순서

1. `PERSON_NAME` NER 보강
   `{PERSON}의 연락처 {PHONE}`, `{PERSON} 계좌 {BANK_ACCOUNT}` 같은 composite positive 문맥을 학습/eval/calibration set에 추가한다.

2. NER hard negative calibration
   예시 키워드, 추상명사, 일반명사, 상호명 내부 이름형 문자열의 `NAME` score를 낮춘다.

3. `ADDRESS` granularity 기준 정리
   NER `ADDRESS` 출력과 pipeline `ADDRESS_FULL`/`ADDRESS_UNIT` taxonomy의 책임 경계를 명확히 한다.

4. Metric reporting 분리
   candidate-level overall, actionable overall, hard-negative final-action 지표를 문서와 발표에서 분리한다.

5. Real NER latency 별도 계측
   현재 p95는 real NER 포함 경로라 deterministic-only 기준과 분리해서 기록해야 한다.

## 9. 결론

현재 v0.2 single-turn core는 release gate를 통과했고, NER를 제외한 구조형 PII 경로는 release gate 범위에서 안정적이다. 남은 핵심은 real NER의 `PERSON_NAME` recall/precision, hard negative candidate noise, `ADDRESS` granularity와 이름-주소 타입 혼동이다.

따라서 다음 PR은 deterministic core를 크게 넓히기보다, NER 백로그와 평가/보고 지표 분리를 기준으로 작게 나누어 진행하는 것이 가장 효율적이다.
