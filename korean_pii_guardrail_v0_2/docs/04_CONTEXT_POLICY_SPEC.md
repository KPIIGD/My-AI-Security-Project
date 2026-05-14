# Context Window 및 Context Judge 명세서

Version: v0.2-single-turn  
Date: 2026-05-09

## 1. 목적

본 문서는 Korean PII Guardrail v0.2에서 context scorer와 context judge가 사용하는 문맥 범위, feature, 판정 순서를 정의한다.

v0.2에서는 RAG와 멀티턴을 제외하므로 context는 **현재 입력 텍스트 내부**만 본다.

## 2. Context scope

### 2.1 포함

- 같은 입력 문자열 안의 문장
- 같은 문장 안의 어절
- field label과 candidate의 위치 관계
- 같은 문장 내 다른 PII candidate와의 co-occurrence
- 같은 입력 텍스트 내부의 짧은 field block

### 2.2 제외

- 이전 사용자 발화
- 이전 모델 출력
- session memory
- RAG document context
- retrieval metadata
- user profile
- external database lookup

## 3. Context window 정의

| 항목 | 정의 |
|---|---|
| 기본 단위 | 어절, 즉 공백 기반 form word |
| 기본 크기 | candidate 기준 좌우 ±5 어절 |
| 문장 제한 | 같은 문장 경계 내부로 제한 |
| field label 예외 | 같은 문장 내 전체 위치 허용 |
| co-occurrence | 같은 문장 내 PII candidate만 인정 |
| 문단 | v0.2에서는 사용하지 않음 |
| 표/양식 | v0.2에서는 별도 form detector 없음 |

## 4. 예시

### 4.1 이름 중의성

```text
오늘 하늘이 맑네요.
```

- `하늘`은 이름 후보일 수 있으나 weather negative context가 강하다.
- PERSON_NAME score를 낮춘다.
- 기본 action은 pass.

```text
고객명 하늘, 연락처 010-1111-2222입니다.
```

- `고객명` field label 존재
- PHONE co-occurrence 존재
- `하늘` PERSON_NAME score boost
- composite flag 가능
- action은 mask.

### 4.2 계좌번호

```text
110-123-456789입니다.
```

- 숫자 패턴만으로는 BANK_ACCOUNT score 낮음
- context 없음
- action은 pass.

```text
신한은행 계좌 110-123-456789로 입금해 주세요.
```

- 은행명 co-occurrence
- 계좌/입금 field label
- BANK_ACCOUNT score 상승
- action은 mask.

### 4.3 상세주소

```text
서울입니다.
```

- ADDRESS_UNIT일 수 있으나 단독 위험 낮음
- P3 또는 pass.

```text
배송지는 서울시 강남구 테헤란로 123 101동 1203호입니다.
```

- 배송지 label
- 도로명 + 번지 + 동호수 결합
- ADDRESS_FULL P1
- action은 mask.

## 5. Context feature categories

### 5.1 Field label feature

| Label group | Examples | Target entity |
|---|---|---|
| name_label | 성명, 이름, 고객명, 신청자, 담당자 | PERSON_NAME |
| phone_label | 연락처, 전화번호, 휴대폰, 핸드폰 | PHONE_MOBILE/PHONE_LANDLINE |
| email_label | 이메일, 메일, 전자우편 | EMAIL |
| address_label | 주소, 배송지, 거주지, 수령지 | ADDRESS_FULL |
| account_label | 계좌, 입금, 송금, 환불계좌 | BANK_ACCOUNT |
| id_label | 고객번호, 회원ID, 사번, 학번 | CUSTOMER_ID/EMPLOYEE_ID/STUDENT_ID |
| medical_label | 환자번호, 차트번호, 진료기록 | MEDICAL_RECORD_NO |

### 5.2 Co-occurrence feature

| Feature | 조건 | 효과 |
|---|---|---|
| person_phone | PERSON_NAME과 PHONE이 같은 문장 | PERSON score boost, composite |
| person_email | PERSON_NAME과 EMAIL이 같은 문장 | PERSON score boost, composite |
| person_address | PERSON_NAME과 ADDRESS가 같은 문장 | composite |
| bank_account | 은행명과 계좌 후보가 같은 문장 | BANK_ACCOUNT boost |
| id_contact | 내부ID와 연락처가 같은 문장 | composite |
| medical_hospital | 환자번호와 병원명이 같은 문장 | risk 상승 |

### 5.3 Negative feature

| Feature | Examples | 효과 |
|---|---|---|
| example_context | 예시, 샘플, 테스트, dummy | penalty |
| weather_context | 하늘 맑음, 비, 날씨, 계절 | PERSON penalty |
| public_number | 대표번호, 고객센터, 안내번호 | PHONE penalty |
| code_context | stack trace, 변수명, JSON key | name/address penalty |
| business_name | 김밥, 식당, 상호, 브랜드 | PERSON penalty |

## 6. Context judge

### 6.1 호출 조건

Context judge는 다음 조건일 때 실행한다.

```text
0.55 <= final_score < 0.75
```

단, P0 entity는 score band와 별개로 별도 high-risk policy를 적용할 수 있다.

### 6.2 v0.2 judge 원칙

- LLM 호출 없음
- 외부 DB lookup 없음
- 이전 턴 참조 없음
- deterministic rule only
- recall-sensitive entity는 안전 우선

### 6.3 판정 순서

```text
Step 1. Strong field label 확인
Step 2. Entity-specific validator 재확인
Step 3. Negative context 확인
Step 4. Single-turn composite 확인
Step 5. Risk-level별 fallback action 적용
```

### 6.4 의사코드

```python
def judge(span, context):
    if span.risk_level == "P0":
        return "mask_or_block"

    if has_strong_field_label(span, context):
        return "mask"

    if has_strong_negative_context(span, context):
        return "pass"

    if has_single_turn_composite(span, context):
        return "mask"

    if span.risk_level == "P1":
        return "mask"  # safety-first

    if span.risk_level == "P2":
        return "pass"

    return "pass"
```

## 7. 문장 및 어절 분리 기준

### 7.1 문장 경계

다음 문자를 기본 문장 경계로 본다.

```text
. ? ! 。 ？ ！ \n
```

단, 이메일, URL, 소수점, 약어 내부의 `.`은 문장 경계로 보지 않도록 detector 후처리에서 보정한다.

### 7.2 어절 경계

공백 기반 split을 기본으로 한다.

```text
홍길동이 010-1234-5678로 연락했습니다.
```

어절:

```text
[홍길동이] [010-1234-5678로] [연락했습니다.]
```

형태소 분석기는 v0.2에서 필수 dependency가 아니다. 필요 시 Kiwi/MeCab-ko wrapper를 선택적으로 붙일 수 있다.

## 8. Field block 제한

v0.2에서는 복잡한 form/table detector를 구현하지 않는다. 다만 같은 줄 안의 간단한 key-value 패턴은 field label로 처리한다.

지원 예:

```text
성명: 홍길동 / 연락처: 010-1234-5678
```

미지원 예:

```text
성명


홍길동
```

field label과 candidate가 여러 줄 이상 떨어진 양식 데이터는 v1 form detector로 이관한다.

## 9. 구현 위치

| 항목 | 파일 |
|---|---|
| context terms | `configs/context_rules.yaml` |
| scoring deltas | `configs/scoring.yaml` |
| context scorer code | `src/pii_guardrail/context_scorer.py` 예정 |
| tests | `tests/test_context_scorer.py` 예정 |
