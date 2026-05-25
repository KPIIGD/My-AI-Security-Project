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
| field label 예외 | 대부분 같은 문장 내 전체 위치 허용. 단, PERSON_NAME의 name_label은 후보 앞쪽 가까운 위치에 있어야 한다. |
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
주소 일부는 서울시 강남구 테헤란로까지만 입력됐습니다.
```

- 시/구/동 + 도로명은 있으나 건물번호가 없음
- ADDRESS_UNIT P2
- 도로명 끝의 `로`는 조사로 자르지 않음
- action은 pass 가능.

```text
배송지는 서울시 강남구 테헤란로 123 101동 1203호입니다.
```

- 배송지 label
- 도로명 + 번지 + 동호수 결합
- ADDRESS_FULL P1
- action은 mask.

```text
방문 주소 테헤란로 123로 와 주세요.
```

- 시/구/동이 없어도 도로명 + 건물번호가 있으면 ADDRESS_FULL P1
- 뒤따르는 `로`는 조사 suffix로 보존
- action은 mask.

## 5. Context feature categories

### 5.1 Field label feature

| Label group | Examples | Target entity |
|---|---|---|
| name_label | 성명, 이름, 고객명, 신청자, 담당자, 작성자, 환자명, 수령인, 예약자, 직원명, 보호자, 문의자, 요청자, 상담 기록 | PERSON_NAME |
| phone_label | 연락처, 전화번호, 휴대폰, 핸드폰 | PHONE_MOBILE/PHONE_LANDLINE |
| email_label | 이메일, 메일, 전자우편 | EMAIL |
| address_label | 주소, 배송지, 거주지, 수령지 | ADDRESS_FULL |
| account_label | 계좌, 계좌번호, 입금, 송금, 환불계좌, 이체, bank account, account no, account number, deposit account, refund account | BANK_ACCOUNT |
| organization_label | 소속, 근무, 재직, 대표, 회사 | ORGANIZATION |
| medical_label | 환자번호, 차트번호, 진료기록 | MEDICAL_RECORD_NO |

PERSON_NAME의 name_label은 `고객명 하늘`, `신청자 이름은 이서연`, `상담 기록에는 유진님`처럼 candidate 앞쪽 가까운 위치에서만 boost한다. `하늘 모델은 테스트용 분류기 이름입니다`처럼 candidate 뒤쪽의 일반 설명에 등장하는 `이름`은 field label로 보지 않는다.

Production 기본 context 규칙은 `CUSTOMER_ID`, `EMPLOYEE_ID`, `STUDENT_ID`용 `id_label`을 제공하지 않는다. `고객번호`, `회원ID`, `사번`, `직원번호`, `학번`, `학생번호`는 조직별 custom identifier profile이 활성화될 때만 field label로 사용해야 한다. 기본값에서 라벨만으로 임의의 숫자/영문 토큰을 내부 식별자로 추정하면 주문번호, 상품코드, 티켓번호 같은 비개인 업무 식별자를 개인정보로 오탐할 수 있다.

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
| example_context | 예시, 예제, 샘플, 테스트, 더미, dummy, sample, placeholder, fixture, 목업, 교육 자료, 검증용, 스토리북, seed, synthetic, 형식 설명, 마스킹 테스트 | penalty |
| weather_context | 하늘 맑음, 비, 날씨, 계절 | PERSON penalty |
| public_number | 대표번호, 고객센터, 안내번호 | PHONE penalty |
| code_context | stack trace, 변수명, JSON key, 로그, error, debug, 컬럼명, 클래스, 브랜치 | name/address penalty |
| business_name | 김밥, 식당, 상호, 브랜드, 상품명, 팀 | PERSON penalty |
| abstract_value | 중요한 가치, 가치입니다, 원칙입니다, 개념입니다 | PERSON penalty |

`example_context`는 후보 점수 감점뿐 아니라 정책 단계에서도 사용한다. `PHONE_MOBILE`, `PHONE_LANDLINE`, `EMAIL` 후보가 예시·샘플·테스트·placeholder처럼 명시적 예시 문맥에 있으면 정규식 후보는 남기되 최종 action은 `pass`로 둘 수 있다. 다만 `연락처`, `전화번호`, 사람 이름 `작성자`처럼 실제 개인정보를 가리키는 positive label이나 composite 근거가 있으면 example penalty만으로 최종 `pass`를 강제하지 않는다. 이는 `test@example.com`, `010-0000-0000` 같은 문서용 값 오탐을 줄이면서도 `설치 가이드 문서 연락처 010-...` 같은 실제 연락처 recall을 보존하기 위한 규칙이다.

단, example term은 후보 span 바깥의 주변 문맥에서만 본다. 예를 들어 `sample@example.org`의 `sample`처럼 전자우편 주소 내부에 포함된 문자열은 예시 문맥으로 보지 않는다. 반대로 `샘플 이메일 sample@example.org`처럼 후보 앞뒤 설명에 `샘플`이 있으면 example context로 본다.

PERSON_NAME, 즉 사람 이름 후보에서는 예외적으로 후보 span 자체가 `예시`, `샘플`, `테스트` 같은 예시 키워드인 경우에도 negative로 본다. real NER가 `샘플 email user@example.com`의 `샘플`을 이름 후보로 올려도 EMAIL과 composite 마스킹으로 승격하지 않게 하기 위한 규칙이다.

`public_number`는 `대표번호`, `고객센터`, `안내번호`, `콜센터`처럼 개인 연락처가 아니라 공개 안내 번호를 설명하는 문맥이다. 전화번호 후보가 이 문맥에 있으면 field label이 함께 있어도 최종 action은 `pass`로 둔다.

`abstract_value`는 `사랑은 중요한 가치입니다`처럼 사람 이름 후보와 같은 표면형이 추상 가치나 개념으로 쓰인 문맥이다. 이 문맥은 PERSON_NAME, 즉 사람 이름 후보를 감점한다. 다만 NER 후보 생성 오류를 guardrail 정책으로 과하게 덮지 않기 위해 이 근거만으로 최종 action을 강제 `pass`로 바꾸지는 않는다.

### 5.4 구조형 식별자 immediate-label feature

`immediate-label`은 후보 값 바로 왼쪽에 붙는 짧은 라벨을 뜻한다. 예를 들어 `법인등록번호 ...`, `등기번호 ...`, `corp number ...`처럼 값 직전 문맥이 명시적 법인 라벨이면 13자리 숫자가 주민등록번호 checksum을 통과하더라도 `RRN`, 즉 주민등록번호 후보로 만들지 않는다. 같은 방식으로 `FRN`, 즉 외국인등록번호 후보와 `CREDIT_CARD`, 즉 신용카드 후보도 법인등록번호 문맥에서는 제외한다.

반대로 `주민등록번호 ...`, `주민번호 ...`, `RRN ...`, `resident registration number ...`처럼 값 직전 문맥이 명시적 개인 식별 라벨이면 주민등록번호 후보를 유지한다. 이 규칙은 P0 recall을 낮추지 않기 위해 넓은 문장 전체가 아니라 후보 바로 왼쪽 라벨에만 적용한다.

여권번호와 운전면허번호도 같은 immediate-label 원칙을 따른다. 두 형식은 제품코드, 주문번호, 티켓번호, 부품코드와 형태가 쉽게 겹치므로 `여권번호`, `passport number`, `운전면허번호`, `driver license number`처럼 값 바로 왼쪽에 강한 라벨이 있을 때만 P0 후보로 만든다. 라벨 없는 `A12345678` 또는 `12-34-567890-12` 모양 문자열은 일반 업무 식별자일 가능성이 높으므로 후보로 만들지 않는다.

### 5.5 비개인 숫자 식별자 immediate-label feature

`structured_identifier_contexts`는 숫자형 식별자의 guardrail 단계 분류 보정 라벨이다. `주문번호`, `주문ID`, `예약번호`, `접수번호`, `송장번호`, `운송장번호`, `결제번호`, `order id`, `invoice no`, `tracking no`, `payment no`처럼 값 바로 왼쪽이 주문·접수·배송·결제 식별자를 뜻하면 숫자 모양이 전화번호, 사업자등록번호, 계좌번호, 신용카드와 비슷해도 개인정보 후보로 올리지 않는다.

이 라벨은 과적합을 막기 위해 두 가지 범위로만 적용한다. 주문번호·사업자등록번호·법인등록번호·주민등록번호·의무기록번호 라벨은 값 바로 왼쪽에 붙어 있을 때만 적용한다. 라벨 내부 띄어쓰기는 선택적으로 허용해 `법인 식별 번호`, `법인 식별번호`, `법인식별번호` 같은 표기 차이를 같은 라벨로 본다. 계좌 라벨은 은행명이 값 앞에 끼는 실제 양식을 허용하기 위해 같은 필드 구간에서만 적용하며, 쉼표·마침표·줄바꿈 뒤의 다음 필드까지 전파하지 않는다.

이 규칙은 값 바로 왼쪽의 짧은 라벨에만 적용한다. `연락처 010-1234-5678`, `사업자등록번호 123-45-67891`, `계좌번호 110-123-456789`처럼 명시적 개인정보 라벨이 붙은 양성 사례의 재현율은 유지한다.

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
Step 1. Strong context 확인 (`context.boost.*`, `context.composite.*`)
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

    if has_strong_context(span):
        return "mask"

    if has_strong_negative_context(span, context):
        return "pass"

    if has_single_turn_composite(span, context):
        return "mask"

    if span.risk_level == "P1" and span.score >= p1_mask_min_score:
        return "mask"

    if (
        span.risk_level == "P1"
        and span.score >= p1_context_judge_min_score
        and has_strong_context(span)
    ):
        return "mask"

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
