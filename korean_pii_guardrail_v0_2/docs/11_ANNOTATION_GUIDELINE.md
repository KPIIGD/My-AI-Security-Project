# Annotation Guideline 초안 — Korean PII Guardrail v0.2

Version: v0.2-single-turn  
Date: 2026-05-09

## 1. 목적

본 문서는 v0.2 평가셋과 NER 학습셋 구축을 위한 개인정보 라벨링 기준을 정의한다.

## 2. 공통 원칙

1. label span은 raw text 기준 character offset으로 기록한다.
2. 조사·호칭·어미는 PII 본체 span에서 제외하고 `suffix`로 기록한다.
3. entity label은 `configs/entities.yaml`에 정의된 값만 사용한다.
4. 모호한 일반명사는 문맥이 충분할 때만 PERSON_NAME으로 라벨링한다.
5. 단일 입력 텍스트 내부 조합 위험은 `tags`에 기록한다.
6. 이전 턴 또는 세션 맥락은 라벨링하지 않는다.

## 3. Label format

```json
{
  "start": 0,
  "end": 3,
  "entity_type": "PERSON_NAME",
  "risk_level": "P1",
  "suffix": "이",
  "notes": "조사 이 분리"
}
```

## 4. Entity labels

### 4.1 Direct identifiers

| Entity | 라벨 기준 |
|---|---|
| RRN | 주민등록번호 형태의 고유식별번호 |
| FRN | 외국인등록번호 형태 |
| PASSPORT | 여권번호 |
| DRIVER_LICENSE | 운전면허번호 |
| PHONE_MOBILE | 휴대전화 번호 |
| PHONE_LANDLINE | 유선전화 번호 |
| EMAIL | 이메일 주소 전체 |
| CREDIT_CARD | 카드번호 |
| BANK_ACCOUNT | 계좌번호, 금융 context 필요 |
| PERSON_NAME | 실명 또는 실명 가능성이 높은 이름 |
| ADDRESS_FULL | 상세주소, 도로명/번지/동호수 등 |

### 4.2 Quasi identifiers

| Entity | 라벨 기준 |
|---|---|
| DOB | 생년월일 |
| AGE | 나이 |
| GENDER | 성별 |
| ADDRESS_UNIT | 시/구/동 등 부분 주소 |
| SCHOOL | 학교명 |
| ORGANIZATION | 회사/기관/단체명 |
| FAMILY_RELATION | 가족관계 표현 |
| EMPLOYEE_ID | 사번 |
| STUDENT_ID | 학번 |
| CUSTOMER_ID | 고객번호/회원번호 |

### 4.3 Security secrets

| Entity | 라벨 기준 |
|---|---|
| API_KEY_SECRET | API key, token, secret, credential |
| DEVICE_ID | device identifier |
| IP_ADDRESS | IP address |
| MAC_ADDRESS | MAC address |

## 5. Boundary rules

### 5.1 조사 분리

| 원문 | label span | suffix |
|---|---|---|
| 홍길동이 | 홍길동 | 이 |
| 홍길동은 | 홍길동 | 은 |
| 김민수에게 | 김민수 | 에게 |
| 민지랑 | 민지 | 랑 |
| 서울시에 | 서울시 | 에 |

### 5.2 호칭 분리

| 원문 | label span | suffix |
|---|---|---|
| 홍길동님 | 홍길동 | 님 |
| 윤정씨 | 윤정 | 씨 |
| 김팀장에게 | 김팀장 또는 김 | 에게 |

`김팀장`은 정책 결정이 필요하다. 실명을 특정할 수 없고 성+직함만 있는 경우 `PERSON_NAME` 대신 `PERSON_REF`가 필요할 수 있으나, v0.2 taxonomy에는 `PERSON_REF`가 없으므로 다음 기준을 사용한다.

- 특정 개인을 지칭하는 문맥이면 `PERSON_NAME` 또는 `FAMILY_RELATION/ORGANIZATION`이 아닌 `PERSON_NAME` 후보로 라벨링 가능
- 단순 직책 일반표현이면 라벨링하지 않음

### 5.3 종결어미 분리

| 원문 | label span | suffix |
|---|---|---|
| test@example.com입니다 | test@example.com | 입니다 |
| 010-1234-5678입니다 | 010-1234-5678 | 입니다 |

## 6. Ambiguous names

다음 단어는 문맥에 따라 이름 또는 일반명사일 수 있다.

```text
하늘, 사랑, 가을, 겨울, 나라, 우주, 봄, 유진, 지민
```

### 6.1 PERSON으로 라벨링하는 경우

```text
고객명 하늘, 연락처 010-1111-2222
하늘님이 신청했습니다.
가을이가 접수했습니다.
성명: 유진
```

### 6.2 라벨링하지 않는 경우

```text
오늘 하늘이 맑네요.
사랑은 중요한 가치입니다.
가을이 왔습니다.
```

## 7. Address granularity

| 표현 | Entity | Risk hint |
|---|---|---|
| 서울 | ADDRESS_UNIT | P3 |
| 서울시 강남구 | ADDRESS_UNIT | P2 |
| 역삼동 | ADDRESS_UNIT | P2 |
| 테헤란로 123 | ADDRESS_FULL | P1 |
| 101동 1203호 | ADDRESS_FULL/ADDRESS_UNIT | P1 |
| 서울시 강남구 테헤란로 123 101동 1203호 | ADDRESS_FULL | P1 |

주소 label은 가능한 한 식별 위험이 있는 연속 span으로 잡는다.

## 8. Financial numbers

숫자열만으로 계좌번호를 라벨링하지 않는다. 다음 문맥이 있을 때 `BANK_ACCOUNT`로 라벨링한다.

- 은행명: 신한은행, 국민은행, 우리은행 등
- field label: 계좌, 입금, 송금, 환불계좌
- 문맥: `로 입금`, `계좌번호`, `받는 계좌`

## 9. Public/example numbers

다음 문맥은 hard negative로 라벨링할 수 있다.

```text
예시 전화번호는 010-0000-0000입니다.
테스트 계좌는 000-000-000000입니다.
고객센터 대표번호는 1588-0000입니다.
```

단, 제품 정책상 public representative number도 masking할지 여부는 별도 policy에서 결정한다. 평가셋에서는 `tags`에 `public_number`를 추가한다.

## 10. Single-turn composite tags

같은 입력 텍스트 내부에서 다음 조합이 있으면 `tags`에 추가한다.

| Tag | 조건 |
|---|---|
| `person_phone` | PERSON_NAME + PHONE |
| `person_email` | PERSON_NAME + EMAIL |
| `person_address` | PERSON_NAME + ADDRESS_FULL |
| `bank_context` | BANK_ACCOUNT + bank/context |
| `medical_context` | MEDICAL_RECORD_NO + hospital/medical label |
| `quasi_combo` | DOB/AGE/GENDER/ADDRESS_UNIT/SCHOOL 등 조합 |

## 11. Inter-annotator agreement

v0.2 목표:

- 1차 라벨러 + 1차 검수
- 샘플 subset에 대해 Cohen's kappa 0.8 이상 목표
- 충돌 유형은 guideline에 반영

## 12. Label conflict resolution

| 충돌 | 해결 |
|---|---|
| 이름 본체에 조사 포함 여부 | 조사 제외 |
| 주소 세부 fragment 분리 여부 | 가능한 ADDRESS_FULL로 merge |
| 조직명 내부 사람 이름 | ORGANIZATION 우선 |
| 이메일 username 이름 오탐 | EMAIL 우선 |
| 계좌번호 context 부족 | label 제외 또는 candidate-only tag |
