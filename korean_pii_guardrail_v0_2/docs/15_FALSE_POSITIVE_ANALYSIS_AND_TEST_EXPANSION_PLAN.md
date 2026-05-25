# 오탐 감소 및 분류 보정 분석 계획

Version: v0.2-single-turn
Date: 2026-05-24
Status: Historical plan with latest release gate update

## 1. 목적

이 문서는 Korean PII Guardrail v0.2의 release gate 결과에서 확인된 오탐과 일부 개인정보 유형 분류 오류를 더 정확히 파악하기 위한 분석 계획서다.

현재 구현은 원문 위치 보존, 한국어 조사 경계 보정, 원문 개인정보 로그 차단, 주요 고위험 개인정보 재현율에서 좋은 결과를 보인다. 다만 실제 릴리스 품질을 높이려면 테스트 값을 늘리고, 오류를 유형별로 나누어 원인을 확인한 뒤, 설정과 탐지 규칙을 좁혀야 한다.

이 문서의 목표는 다음과 같다.

- 오탐, 미탐, 유형 혼동을 사람이 이해할 수 있는 기준으로 분류한다.
- 부족한 테스트 데이터를 어떤 방향으로 늘릴지 정의한다.
- 함수와 처리 단계를 한국어 설명으로 연결해 수정 위치를 찾기 쉽게 만든다.
- 수정 후 어떤 수치가 좋아져야 하는지 검증 기준을 정한다.

## 2. 용어 정리

| 용어 | 한국어 설명 | 의미 |
|---|---|---|
| False Positive | 오탐 | 개인정보가 아닌데 개인정보라고 잡은 경우 |
| False Negative | 미탐 | 개인정보인데 탐지하지 못한 경우 |
| Type Confusion | 유형 혼동 | 위치는 잡았지만 개인정보 유형을 잘못 붙인 경우 |
| Over Detection | 과다 탐지 | 맞는 span보다 너무 넓게 잡은 경우 |
| Precision | 정밀도 | 잡았다고 한 것 중 실제 정답인 비율 |
| Recall | 재현율 | 실제 정답 중 시스템이 잡아낸 비율 |
| F1 | 정밀도와 재현율의 조화 평균 | 정밀도와 재현율을 함께 보는 대표 점수 |
| Span | 원문 위치 범위 | 원문 문자열에서 시작 위치와 끝 위치로 표현되는 구간 |
| Boundary | 경계 | 개인정보 본문과 조사, 어미, 주변 문자를 나누는 기준 |

## 3. 현재 기준 수치

현재 기준은 2026-05-25에 재생성한 `reports/release_gate_v0_2.json`의 5,000개 synthetic release gate 결과다. 이 문서의 5장 이후에는 2026-05-22 당시의 개선 계획과 단계별 보정 기록이 포함되어 있으므로, 최신 전체 수치는 아래 표를 우선 기준으로 삼는다.

| 항목 | 값 |
|---|---:|
| 전체 F1 | 0.9243 |
| 전체 정밀도 | 0.8803 |
| 전체 재현율 | 0.9729 |
| actionable F1 | 0.9457 |
| actionable 정밀도 | 0.9975 |
| actionable 재현율 | 0.8991 |
| 고위험 개인정보 재현율 | 0.9645 |
| actionable 고위험 개인정보 재현율 | 0.9645 |
| high-risk structured recall | 1.0000 |
| 조사 경계 정확도 | 0.9989 |
| 잘못된 offset 수 | 0 |
| 원문 개인정보 로그 유출 수 | 0 |
| 감사 이벤트 원문 값 유출 수 | 0 |
| release gate status | pass |

오류 유형별 집계는 다음과 같다.

| 오류 유형 | 건수 | 해석 |
|---|---:|---|
| 오탐 | 750 | hard negative에서 public candidate로 남은 경우다. 최종 action은 모두 `pass`다. |
| 미탐 | 156 | 대부분 `single_turn_composite`의 `PERSON_NAME` 누락이다. |
| 유형 혼동 | 13 | 일부 이름 fixture 또는 경계 케이스가 `ADDRESS_FULL`로 오분류된 경우다. |
| 과다 탐지 | 0 | 최신 failure JSONL 기준 별도 과다 탐지 row는 없다. |

개인정보 유형별 주요 오류는 다음과 같다.

| 유형 | 주요 문제 | 건수 |
|---|---|---:|
| PERSON_NAME, 사람 이름 | 오탐 | 500 |
| PERSON_NAME, 사람 이름 | 미탐 | 156 |
| EMAIL, 전자우편 주소 | 오탐 | 125 |
| PHONE_MOBILE, 휴대전화 번호 | 오탐 | 125 |
| ADDRESS_FULL, 주소 전체 | 유형 혼동 | 13 |

최신 기준에서 production high-risk structured recall은 1.0000이다. `CUSTOMER_ID`, `EMPLOYEE_ID`, `STUDENT_ID`는 조직별 포맷 근거가 필요한 custom identifier profile 범위이므로 production 기본 release gate에서 제외한다. 따라서 현재 우선순위는 `PERSON_NAME` NER 후보 품질과 hard negative candidate noise로 둔다.

## 4. 처리 흐름과 함수별 한국어 설명

아래는 현재 pipeline에서 후보가 만들어지고 최종 마스킹까지 가는 흐름이다.

| 코드 이름 | 한국어 설명 | 주요 책임 |
|---|---|---|
| `GuardrailPipeline.process()` | 전체 가드레일 처리 함수 | 전처리, 탐지, 경계 보정, 문맥 점수, 병합, 정책, 마스킹, 감사 이벤트 생성을 순서대로 실행한다. |
| `preprocess_text()` | 원문 전처리 함수 | 정규화 문자열과 원문 위치 복원 정보를 만든다. 변형된 한국어 숫자나 초성 표현도 탐지 가능한 후보로 만든다. |
| `BaseRegexDetector.detect()` | 정규식 기반 탐지 실행 함수 | 전화번호, 전자우편, 주민등록번호처럼 구조가 뚜렷한 후보를 찾는다. |
| `PhoneRegexDetector._detect()` | 휴대전화 번호 후보 탐지 함수 | 휴대전화 번호처럼 보이는 숫자 패턴을 찾는다. |
| `EmailRegexDetector._detect()` | 전자우편 주소 후보 탐지 함수 | 전자우편 주소처럼 보이는 문자열을 찾는다. |
| `RRNRegexDetector._detect()` | 주민등록번호 후보 탐지 함수 | 주민등록번호처럼 보이는 숫자 패턴을 찾는다. |
| `CorporateRegNoRegexDetector._detect()` | 법인등록번호 후보 탐지 함수 | 법인등록번호처럼 보이는 숫자 패턴을 찾는다. |
| `DictionaryDetector.detect()` | 사전 기반 탐지 실행 함수 | 사람 이름, 주소, 기관명, 병원명, 학교명 등 사전 기반 후보를 찾는다. |
| `DictionaryDetector._detect_person_names()` | 사람 이름 후보 탐지 함수 | 사람 이름처럼 보이는 단어를 후보로 만든다. |
| `DictionaryDetector._detect_addresses()` | 주소 후보 탐지 함수 | 시, 구, 동, 도로명, 상세 주소 후보를 찾는다. |
| `KoreanBoundaryCorrector.correct()` | 한국어 경계 보정 함수 | 개인정보 본문 뒤에 붙은 조사, 호칭, 어미를 분리한다. |
| `ContextScorer.score()` | 문맥 점수 조정 함수 | 주변 단어를 보고 후보 점수를 올리거나 낮춘다. |
| `ContextScorer._evaluate_boost()` | 점수 상승 조건 검사 함수 | "고객명", "연락처", "주소" 같은 강한 문맥을 찾는다. |
| `ContextScorer._evaluate_penalty()` | 점수 감점 조건 검사 함수 | "예시", "테스트", "샘플" 같은 비개인정보 문맥을 찾는다. |
| `SpanResolver.resolve()` | 후보 정리 함수 | 중복, 겹침, 주소 조각, 복합 위험을 정리해 최종 후보를 만든다. |
| `SpanResolver._resolve_overlaps()` | 겹치는 후보 정리 함수 | 서로 겹치는 후보 중 어떤 유형을 남길지 결정한다. |
| `SpanResolver._merge_address_fragments()` | 주소 조각 병합 함수 | 주소 조각들을 필요할 때 하나의 주소 후보로 합친다. |
| `PolicyRouter.route()` | 정책 결정 함수 | 후보별로 통과, 마스킹, 해시, 차단 중 어떤 행동을 할지 정한다. |
| `SuffixPreservingMasker.apply()` | 조사 보존 마스킹 함수 | 개인정보 본문만 마스킹하고 조사나 어미는 가능한 한 보존한다. |
| `build_failure_analysis_rows()` | 실패 분석 행 생성 함수 | 평가 결과에서 오탐, 미탐, 유형 혼동을 JSONL 행으로 만든다. |
| `build_release_gate_report()` | 릴리스 기준 보고서 생성 함수 | release gate 통과 여부와 주요 지표를 만든다. |

## 5. 문제 가설

### 5.1 사람 이름 오탐

사람 이름 오탐은 가장 큰 문제다. 현재 오류 중 `PERSON_NAME` 오탐이 825건이다.

가능한 원인은 다음과 같다.

- 짧은 한국어 단어가 이름 후보로 너무 쉽게 승격된다.
- 이름 사전과 일반 명사 사이의 경계가 부족하다.
- "고객명", "담당자", "환자명" 같은 강한 문맥이 없어도 후보가 최종 마스킹까지 남는다.
- "오늘", "예시", "테스트", "날씨", "가치", "문장" 같은 비개인정보 문맥 감점이 부족하다.
- 신경망 탐지기 결과가 사전 후보와 결합될 때 낮은 확신 후보가 충분히 걸러지지 않는다.

수정 방향은 다음과 같다.

- 사람 이름은 단독 사전 매칭만으로 높은 위험으로 올리지 않는다.
- 강한 이름 문맥이 있을 때만 점수를 올린다.
- 일반 명사, 감정 표현, 날씨 표현, 예시 문맥에서는 점수를 낮춘다.
- 사람 이름 후보가 1글자이거나 너무 짧을 때는 더 강한 문맥을 요구한다.
- release gate에서 hard negative 문장 묶음을 별도로 늘려 회귀를 확인한다.

### 5.2 휴대전화 번호 오탐

휴대전화 번호는 재현율이 높지만 오탐이 많다. 현재 `PHONE_MOBILE` 오탐은 375건이다.

가능한 원인은 다음과 같다.

- 휴대전화 번호처럼 보이는 예시 값이 실제 연락처처럼 처리된다.
- "예시 전화번호", "테스트 번호", "샘플 번호", "더미 번호" 문맥 감점이 충분하지 않다.
- 숫자 패턴이 주문번호, 문서번호, 코드값과 충분히 구분되지 않는다.

수정 방향은 다음과 같다.

- "연락처", "전화", "휴대폰", "문자" 문맥은 유지한다.
- "예시", "샘플", "더미", "테스트", "문서용" 문맥은 강하게 감점한다.
- 주문번호, 접수번호, 인증코드, 상품코드 근처의 숫자는 휴대전화 후보에서 제외하거나 낮은 점수로 둔다.
- 재현율을 무너뜨리지 않도록 실제 연락처 문맥과 예시 문맥을 쌍으로 테스트한다.

### 5.3 주소 전체와 주소 일부 혼동

현재 주소 문제는 단순히 주소를 못 찾는 문제가 아니라, 주소의 세부 유형을 잘못 붙이는 문제다.

`ADDRESS_UNIT`, 즉 주소 일부는 267건 미탐으로 기록되어 있다. 동시에 `ADDRESS_FULL`, 즉 주소 전체는 280건 유형 혼동이 발생했다. 이는 주소 일부가 주소 전체로 승격되었을 가능성이 높다.

가능한 원인은 다음과 같다.

- 시, 구, 동 수준의 짧은 주소가 주소 전체로 분류된다.
- 주소 조각 병합 단계가 너무 적극적으로 동작한다.
- 평가 데이터의 "주소 일부" 기준과 코드의 "주소 전체" 기준이 일치하지 않는다.

분류 기준은 다음과 같이 정리한다.

| 입력 형태 | 권장 유형 | 설명 |
|---|---|---|
| "강남구" | 주소 일부 | 위치 단서지만 전체 주소는 아니다. |
| "역삼동" | 주소 일부 | 동 단위 주소 조각이다. |
| "서울시 강남구" | 주소 일부 | 시와 구가 있어도 상세 주소는 아니다. |
| "서울시 강남구 테헤란로" | 주소 일부 또는 주소 전체 후보 | 도로명은 있지만 건물번호가 없으면 불완전할 수 있다. |
| "서울시 강남구 테헤란로 123" | 주소 전체 | 실제 위치 특정성이 높다. |
| "서울시 강남구 테헤란로 123 5층" | 주소 전체 | 상세 주소까지 포함한다. |

수정 방향은 다음과 같다.

- 주소 전체 승격에는 도로명과 건물번호, 지번, 상세 주소 중 충분한 증거를 요구한다.
- 시, 구, 동만 있는 경우 기본값은 주소 일부로 둔다.
- `SpanResolver._merge_address_fragments()`에서 주소 조각 병합 조건을 좁힌다.
- 평가 데이터에도 주소 일부와 주소 전체 기준을 명확히 나누어 넣는다.

### 5.4 전자우편 주소 오탐

`EMAIL`, 즉 전자우편 주소 오탐은 125건이다. 현재 전자우편 재현율은 높지만, 예시 주소가 실제 개인정보처럼 처리되는 문제가 있을 수 있다.

가능한 원인은 다음과 같다.

- `test@example.com` 같은 문서 예시 주소가 개인정보로 처리된다.
- "예시", "샘플", "테스트", "문서", "형식" 문맥 감점이 부족하다.
- 특정 예약 도메인이나 예시 도메인을 실제 개인정보와 동일하게 취급한다.

수정 방향은 다음과 같다.

- 예시 도메인과 문서 예시 문맥을 별도 negative fixture로 늘린다.
- 다만 실제 사용자가 입력한 전자우편은 강하게 보호해야 하므로, 이메일 정규식 자체를 약화하기보다는 문맥 기반 감점을 우선 적용한다.

### 5.5 법인등록번호와 주민등록번호 혼동

`CORPORATE_REG_NO`, 즉 법인등록번호는 5건 미탐이고, 같은 위치가 `RRN`, 즉 주민등록번호로 잘못 분류된 사례가 5건 있다.

가능한 원인은 다음과 같다.

- 법인등록번호와 주민등록번호의 숫자 형태가 겹친다.
- 겹치는 후보를 정리하는 단계에서 주민등록번호 우선순위가 너무 높다.
- "법인등록번호", "법인번호", "등기번호" 같은 문맥이 우선순위 결정에 충분히 반영되지 않는다.

수정 방향은 다음과 같다.

- 법인 문맥이 가까이 있으면 법인등록번호가 주민등록번호보다 우선해야 한다.
- 주민등록번호 문맥이 명확할 때만 주민등록번호로 확정한다.
- `SpanResolver._resolve_overlaps()`와 `_win_key()`의 우선순위가 문맥 점수를 충분히 반영하는지 확인한다.

## 6. 테스트 데이터 확장 계획

현재 테스트 값이 부족하므로, 단순히 총량만 늘리는 것이 아니라 오류 원인별로 데이터를 나누어 늘린다.

### 6.1 권장 데이터 묶음

| 데이터 묶음 | 목적 | 권장 추가 수 |
|---|---|---:|
| hard_negative_name | 사람 이름처럼 보이는 일반 단어 오탐 확인 | 500 |
| hard_negative_phone | 전화번호처럼 보이는 예시, 샘플, 코드값 오탐 확인 | 300 |
| hard_negative_email | 예시 전자우편과 예약 도메인 오탐 확인 | 200 |
| address_unit_vs_full | 주소 일부와 주소 전체 분류 기준 확인 | 500 |
| corporate_vs_rrn | 법인등록번호와 주민등록번호 혼동 확인 | 200 |
| person_context_positive | 실제 사람 이름 문맥 재현율 확인 | 300 |
| phone_email_positive | 실제 연락처와 전자우편 재현율 유지 확인 | 300 |
| adversarial_boundary_extra | 조사, 어미, 띄어쓰기 변형 경계 확인 | 300 |

초기 목표는 최소 2,600개를 추가해 release gate를 7,600개 이상으로 늘리는 것이다. 이후 오류가 집중되는 묶음은 1,000개 단위로 더 확장한다.

### 6.2 각 테스트 행에 필요한 필드

평가 데이터는 원문 개인정보를 사용하지 않고 synthetic fixture로 만든다. 각 행은 최소 다음 정보를 가져야 한다.

| 필드 | 설명 |
|---|---|
| `case_id` | 테스트 케이스 고유 식별자 |
| `bucket` | 데이터 묶음 이름 |
| `text` | synthetic 입력 문장 |
| `labels` | 정답 span 목록 |
| `expected_action` | 기대 행동: 통과, 마스킹, 차단 등 |
| `negative_reason` | negative 케이스라면 왜 개인정보가 아닌지 |
| `risk_focus` | 확인하려는 위험: 이름 오탐, 주소 혼동 등 |

### 6.3 negative 테스트 원칙

negative 테스트는 개인정보가 없어야 하는 문장이다. 이 묶음에서는 탐지 결과가 비어 있거나, 최소한 최종 행동이 `pass`, 즉 통과가 되어야 한다.

추가해야 할 negative 유형은 다음과 같다.

- 사람 이름처럼 보이지만 일반 명사인 단어
- 감정, 날씨, 가치, 상품명, 팀명, 프로젝트명
- 예시 전화번호와 더미 전화번호
- 예시 전자우편 주소와 문서 형식 설명
- 주문번호, 접수번호, 상품코드, 인증코드처럼 숫자 구조가 있는 비개인정보
- 주소처럼 보이는 지역명 일반 언급

### 6.4 positive 테스트 원칙

positive 테스트는 실제 개인정보로 처리되어야 하는 synthetic 문장이다. 오탐을 줄이는 과정에서 재현율이 떨어지지 않는지 확인하기 위해 반드시 같이 늘려야 한다.

추가해야 할 positive 유형은 다음과 같다.

- "고객명", "담당자", "환자명", "신청자"가 붙은 사람 이름
- "연락처", "휴대폰", "전화"가 붙은 휴대전화 번호
- "이메일", "계정", "회신 주소"가 붙은 전자우편 주소
- 도로명과 건물번호가 있는 주소 전체
- 시, 구, 동만 있는 주소 일부
- 법인등록번호 문맥과 주민등록번호 문맥이 각각 명확한 케이스

## 7. 분석 절차

테스트 데이터를 늘린 뒤 다음 순서로 문제를 확인한다.

1. 새 평가 데이터를 bucket별로 나누어 생성한다.
2. `scripts/run_eval.py`로 기본 평가를 실행한다.
3. `scripts/run_release_gate.py`로 release gate 보고서를 만든다.
4. `reports/failure_cases_release_gate_v0_2.jsonl`을 오류 유형, 개인정보 유형, bucket 기준으로 집계한다.
5. 오류 상위 20개 패턴을 뽑아 사람이 읽을 수 있는 분석 표로 만든다.
6. 수정 후보를 config, 정규식, 문맥 점수, resolver 중 하나로 분류한다.
7. 가장 큰 오탐 원인부터 하나씩 수정한다.
8. 수정 후 전체 테스트와 release gate를 다시 실행한다.

## 8. 수정 우선순위

| 우선순위 | 작업 | 이유 |
|---:|---|---|
| 1 | `PERSON_NAME` NER recall 개선 | 최신 release gate의 FN 156건이 사람 이름에 집중된다. |
| 2 | hard negative `PERSON_NAME` candidate 감소 | 최신 release gate의 candidate FP 500건이 사람 이름형 일반명사/추상명사에 집중된다. |
| 3 | NER `ADDRESS` granularity와 이름-주소 타입 혼동 점검 | 남은 TYPE_CONFUSION 13건이 `ADDRESS_FULL`에 남아 있다. |
| 4 | candidate-level metric과 actionable metric 분리 | hard negative candidate FP는 최종 action에서는 `pass`라 사용자-visible 오탐과 구분해야 한다. |
| 5 | real NER latency 별도 계측 | real NER 경로와 deterministic-only 경로를 나눠 release gate 기준을 명확히 한다. |
| 6 | 구조형 숫자 식별자 퍼저 변형 보강 | release gate는 안정적이나 공격적 퍼저 변형에서는 normalization과 타입 충돌 장기 과제가 남아 있다. |

## 9. 검증 기준

수정 후에는 단순히 전체 F1만 보지 않는다. 오탐을 줄이다가 재현율이 무너지면 안 되기 때문이다.

1차 목표는 다음과 같다.

| 지표 | 현재 | 1차 목표 |
|---|---:|---:|
| 전체 정밀도 | 0.8803 | 0.9000 이상 |
| 전체 재현율 | 0.9729 | 0.9700 이상 유지 |
| actionable 정밀도 | 0.9975 | 0.9900 이상 유지 |
| actionable 재현율 | 0.8991 | 0.9000 이상 유지 |
| 고위험 개인정보 재현율 | 0.9645 | 0.9600 이상 유지 |
| hard negative candidate FP | 750 | 300 이하 |
| PERSON_NAME candidate FP | 500 | 200 이하 |
| PERSON_NAME FN | 156 | 50 이하 |
| ADDRESS_FULL type confusion | 13 | 0 |
| invalid offset count | 0 | 0 유지 |
| raw PII logging count | 0 | 0 유지 |

2차 목표는 다음과 같다.

| 지표 | 2차 목표 |
|---|---:|
| 전체 F1 | 0.9400 이상 |
| actionable F1 | 0.9400 이상 |
| hard negative candidate FP | 100 이하 |
| `PERSON_NAME` recall | 0.9300 이상 |
| 주소/이름 유형 혼동 | 0 |
| deterministic-only p95 latency | 100ms 이하 별도 입증 |

## 10. 리스크와 주의사항

- 오탐을 줄이기 위해 threshold를 과하게 올리면 미탐이 늘어날 수 있다.
- 사람 이름 오탐을 줄이다가 실제 이름을 놓치면 개인정보 보호 목적이 약해진다.
- 전화번호와 전자우편 정규식을 약하게 만들면 고위험 개인정보 재현율이 떨어질 수 있다.
- 주소 전체와 주소 일부 기준은 코드만 바꾸지 말고 annotation guideline과 평가 데이터 기준도 함께 맞춰야 한다.
- release report와 failure report에는 원문 개인정보가 들어가면 안 된다. synthetic fixture만 사용하고, 보고서에는 span 길이와 유형, reason code 중심으로 기록한다.
- v0.2 범위에는 RAG, 멀티턴 세션, fragment ledger, subject tracker를 넣지 않는다.

## 11. 산출물

이 작업이 끝나면 다음 산출물이 있어야 한다.

- 확장된 synthetic 평가 데이터
- bucket별 평가 보고서
- failure case 집계 보고서
- 오탐 감소 전후 비교표
- 주소 유형 분류 기준 문서화
- release gate 재실행 결과
- raw PII 로그 유출 0건 증거
- invalid offset 0건 증거

## 12. 다음 작업

1. 테스트 데이터 생성 스크립트 또는 fixture 파일 위치를 정한다.
2. 위 bucket 기준으로 최소 2,600개 synthetic case를 추가한다.
3. 현재 release gate를 새 데이터로 재실행한다.
4. 오류 상위 패턴을 다시 집계한다.
5. 사람 이름 오탐 감소부터 수정 PR을 분리한다.

## 13. 1단계 실행 계획

1단계는 모델이나 규칙을 바로 수정하지 않고, 정확한 테스트 데이터를 만들고 평가 결과를 비교할 수 있는 기반을 고정하는 단계다.

### 13.1 1단계 산출물

| 산출물 | 위치 | 목적 |
|---|---|---|
| 마커 기반 데이터 생성기 | `scripts/build_marker_eval_dataset.py` | 사람이 `start`, `end` offset을 직접 세지 않고 평가 JSONL을 생성한다. |
| 사람 이름 seed 원본 | `data/eval/markers/stage1_person_name_seed.jsonl` | 사람 이름 오탐과 실제 이름 재현율을 함께 확인하는 작은 시작 데이터다. |
| 생성된 평가 JSONL | `data/eval/generated/stage1_person_name_seed.jsonl` | `run_eval.py`에 바로 넣을 수 있는 평가 데이터다. |
| 평가 리포트 | `reports/eval_stage1_person_name_seed.json` | seed 데이터 기준 정밀도, 재현율, 실패 유형을 확인한다. |
| 실패 분석 리포트 | `reports/failure_cases_stage1_person_name_seed.jsonl` | 어떤 케이스가 오탐, 미탐, 유형 혼동인지 확인한다. |

### 13.2 마커 작성 규칙

positive 케이스는 아래처럼 개인정보 본문만 마커로 감싼다.

```text
고객명 <PERSON_NAME risk="P1">하늘</PERSON_NAME>, 연락처는 별도 확인 예정입니다.
```

마커 밖에 있는 조사, 어미, 문장 부호는 label span에 포함하지 않는다. suffix를 명시해야 하는 경우에는 다음처럼 쓴다.

```text
<PERSON_NAME risk="P1" suffix="이">홍길동</PERSON_NAME>이 신청했습니다.
```

negative 케이스는 마커를 쓰지 않는다.

```text
오늘 하늘이 맑네요.
```

### 13.3 실행 명령

마커 원본을 평가 JSONL로 변환한다.

```powershell
python scripts\build_marker_eval_dataset.py `
  --input data\eval\markers\stage1_person_name_seed.jsonl `
  --output data\eval\generated\stage1_person_name_seed.jsonl `
  --validate
```

생성된 평가 JSONL을 mock NER 기준으로 빠르게 평가한다.

```powershell
python scripts\run_eval.py `
  --config-dir configs `
  --dataset data\eval\generated\stage1_person_name_seed.jsonl `
  --output reports\eval_stage1_person_name_seed.json `
  --failure-output reports\failure_cases_stage1_person_name_seed.jsonl `
  --audit-safety-output reports\audit_safety_stage1_person_name_seed.json `
  --mock-ner
```

real NER 기준 평가는 local model 또는 HuggingFace model 접근이 가능한 환경에서 같은 데이터셋으로 다시 실행한다.

### 13.4 1단계 통과 기준

1단계는 정확도 목표를 달성하는 단계가 아니라, 평가 체계가 안전하게 작동하는지 확인하는 단계다.

| 기준 | 기대값 |
|---|---|
| 생성기 실행 | 성공 |
| 생성된 JSONL 평가 loader 검증 | 성공 |
| marker span offset | 원문 기준 start/end와 일치 |
| negative 케이스 labels | 빈 목록 |
| raw PII logging count | 0 |
| invalid offset count | 0 |
| 실패 분석 JSONL 생성 | 성공 |

### 13.5 1단계 이후 확장

seed 평가가 정상 동작하면 같은 형식으로 `hard_negative_name` 500건과 `person_context_positive` 300건을 먼저 확장한다. 이후 phone, email, address, corporate/RRN bucket을 순서대로 추가한다.

### 13.6 1단계 seed 실행 결과

`stage1_person_name_seed`는 사람 이름 오탐을 확인하기 위한 작은 시작 데이터셋이다. 이 데이터셋은 `hard_negative_name` 12건과 `person_context_positive` 12건, 총 24건으로 구성한다.

mock NER 기준 첫 실행 결과는 다음과 같다.

| 항목 | 값 |
|---|---:|
| 처리 케이스 수 | 24 |
| 전체 F1 | 0.7059 |
| 정밀도 | 0.5455 |
| 재현율 | 1.0000 |
| 고위험 재현율 | 1.0000 |
| 경계 정확도 | 0.9167 |
| 잘못된 offset 수 | 0 |
| 원문 개인정보 로그 유출 수 | 0 |
| 마스킹 텍스트 정확 일치율 | 0.7500 |

실패 분석에서는 `PERSON_NAME` 오탐 10건이 확인되었다. 이 중 대부분은 negative 문장 안에서 일반 명사, 예시 변수명, 프로젝트명, 모델명, 상호, 컬럼명, 문서 예제명을 사람 이름으로 잡은 경우다.

따라서 다음 수정 후보는 다음 순서로 본다.

1. `DictionaryDetector._detect_person_names()` 사람 이름 후보 탐지 함수가 단독 이름 후보를 너무 쉽게 만들고 있는지 확인한다.
2. `ContextScorer._evaluate_penalty()` 감점 조건 검사 함수에 예시, 프로젝트명, 모델명, 상호, 컬럼명, 문서 예제 문맥이 충분히 반영되는지 확인한다.
3. `ContextScorer._evaluate_boost()` 점수 상승 조건 검사 함수가 "고객명", "담당자", "신청자", "환자명" 같은 positive 문맥을 유지하는지 확인한다.
4. 수정 후 이 seed 데이터셋에서 정밀도를 먼저 올리고, 이후 500건 이상 확장 데이터로 다시 확인한다.

## 14. 1-2단계 사람 이름 확장 평가

1-2단계는 seed 24건을 800건으로 확장해 사람 이름 오탐과 재현율 문제를 더 안정적으로 확인하는 단계다.

### 14.1 1-2단계 산출물

| 산출물 | 위치 | 목적 |
|---|---|---|
| 확장 marker 생성기 | `scripts/generate_stage1_person_name_markers.py` | 500개 negative와 300개 positive marker 원본을 결정적으로 생성한다. |
| 확장 marker 원본 | `data/eval/markers/stage1_person_name_expanded.jsonl` | 사람이 검토 가능한 synthetic 원본이다. |
| 확장 평가 JSONL | `data/eval/generated/stage1_person_name_expanded.jsonl` | 평가기에 바로 넣는 offset 포함 JSONL이다. |
| 확장 평가 리포트 | `reports/eval_stage1_person_name_expanded.json` | 800건 기준 평가 결과다. |
| 확장 실패 분석 | `reports/failure_cases_stage1_person_name_expanded.jsonl` | 오탐과 미탐을 case id, entity type, reason code 중심으로 기록한다. |
| 확장 감사 안전 리포트 | `reports/audit_safety_stage1_person_name_expanded.json` | 보고서와 응답에 raw PII가 남지 않는지 확인한다. |

### 14.2 데이터 구성

| bucket | 건수 | 설명 |
|---|---:|---|
| `hard_negative_name` | 500 | 이름처럼 보이는 토큰을 날씨, 추상 명사, 프로젝트명, 모델명, 상호, 컬럼명, 문서 예제명, 파일명, 클래스명, 브랜치명 등 비개인정보 문맥에 넣는다. |
| `person_context_positive` | 300 | 같은 토큰을 고객명, 담당자, 신청자 이름, 환자명, 수령인, 예약자, 직원명, 보호자 이름, 문의자, 계약 담당자, 상담 기록, 요청자 성명 문맥에 넣는다. |

이 구성은 오탐을 줄이는 수정이 실제 이름 재현율을 떨어뜨리는지 동시에 확인하기 위한 paired dataset이다.

### 14.3 실행 명령

확장 marker 원본 생성:

```powershell
python scripts\generate_stage1_person_name_markers.py `
  --output data\eval\markers\stage1_person_name_expanded.jsonl
```

평가 JSONL 변환:

```powershell
python scripts\build_marker_eval_dataset.py `
  --input data\eval\markers\stage1_person_name_expanded.jsonl `
  --output data\eval\generated\stage1_person_name_expanded.jsonl `
  --validate
```

mock NER 기준 평가:

```powershell
python scripts\run_eval.py `
  --config-dir configs `
  --dataset data\eval\generated\stage1_person_name_expanded.jsonl `
  --output reports\eval_stage1_person_name_expanded.json `
  --failure-output reports\failure_cases_stage1_person_name_expanded.jsonl `
  --audit-safety-output reports\audit_safety_stage1_person_name_expanded.json `
  --mock-ner
```

### 14.4 1-2단계 실행 결과

mock NER 기준 첫 확장 평가 결과는 다음과 같다.

| 항목 | 값 |
|---|---:|
| 처리 케이스 수 | 800 |
| 전체 F1 | 0.4192 |
| 정밀도 | 0.3721 |
| 재현율 | 0.4800 |
| 고위험 재현율 | 0.4800 |
| 경계 정확도 | 0.9167 |
| 잘못된 offset 수 | 0 |
| 원문 개인정보 로그 유출 수 | 0 |
| 마스킹 텍스트 정확 일치율 | 0.6800 |

오류 집계는 다음과 같다.

| 오류 유형 | 건수 | 해석 |
|---|---:|---|
| 오탐 | 243 | 개인정보가 아닌 이름형 토큰이나 positive 문맥 안의 주변 단어가 사람 이름으로 잡힌다. |
| 미탐 | 156 | 강한 이름 문맥 안에서도 일부 이름형 토큰이 후보로 생성되지 않는다. |

bucket별 오류는 다음과 같다.

| bucket | 오류 | 건수 | 해석 |
|---|---|---:|---|
| `hard_negative_name` | 오탐 | 218 | 비개인정보 문맥 감점 또는 후보 제거가 부족하다. |
| `person_context_positive` | 미탐 | 156 | 일부 이름형 토큰은 강한 문맥이 있어도 탐지되지 않는다. |
| `person_context_positive` | 오탐 | 25 | 이름 문맥의 주변 label 단어가 별도 사람 이름으로 잡히는 후보 정리 문제가 있다. |

### 14.5 새로 확인된 문제

seed 24건에서는 "오탐이 많다"는 사실이 주로 보였다. 800건 확장 평가에서는 문제가 두 갈래로 나뉜다.

1. 사람 이름 오탐 문제: 이름처럼 보이는 토큰이 프로젝트명, 모델명, 상호, 컬럼명, 문서 예제명, 데이터셋명, 파일명, 클래스명, 브랜치명, UI label, 지표명, 상품명, 팀명, 시나리오명, 변수명, 화면명 문맥에서 개인정보로 남는다.
2. 사람 이름 미탐 문제: 같은 토큰이 고객명, 담당자, 신청자 이름, 환자명, 수령인, 예약자, 직원명, 보호자 이름, 문의자, 계약 담당자, 상담 기록, 요청자 성명처럼 강한 문맥에 있어도 후보가 생성되지 않는 경우가 있다.
3. positive 문맥 주변 단어 오탐 문제: 이름 본문이 아닌 field label 또는 주변 단어가 별도 `PERSON_NAME` 후보로 남는 경우가 있다.

### 14.6 1-2단계 이후 수정 방향

수정은 다음 순서로 진행한다.

1. `DictionaryDetector._detect_person_names()` 사람 이름 후보 탐지 함수에서 어떤 이름형 토큰이 후보로 생성되고 어떤 토큰이 누락되는지 확인한다.
2. `configs/dictionaries.yaml`의 사람 이름 사전 범위와 테스트 데이터의 이름형 토큰 범위를 맞춘다. 단, 사전만 넓히면 오탐도 늘 수 있으므로 context gate와 함께 본다.
3. `ContextScorer._evaluate_penalty()` 감점 조건 검사 함수에 프로젝트명, 모델명, 상호, 컬럼명, 문서 예제명, 파일명, 클래스명, 브랜치명, 변수명, 화면명 등 hard negative 문맥을 추가하거나 강화한다.
4. `ContextScorer._evaluate_boost()` 점수 상승 조건 검사 함수가 고객명, 담당자, 신청자 이름, 환자명, 수령인, 예약자, 직원명, 보호자 이름, 문의자, 계약 담당자, 상담 기록, 요청자 성명 문맥을 충분히 강하게 반영하는지 확인한다.
5. `SpanResolver.resolve()` 후보 정리 함수에서 field label 또는 주변 단어가 이름 본문과 함께 남는지 확인한다.

1차 수정 목표는 `stage1_person_name_expanded` 기준으로 정밀도 0.80 이상, 재현율 0.90 이상, raw PII logging count 0, invalid offset count 0을 달성하는 것이다.

## 15. 2단계 사람 이름 수정 결과

2단계에서는 사람 이름 정확도를 높이기 전에, 먼저 `PASS` 후보와 실제 조치 후보를 분리해 보았다. 기존 M10 평가 리포트는 public span 전체를 prediction으로 계산하므로 최종 action이 `pass`인 후보도 false positive로 집계한다. 이 값은 후보 생성 노이즈를 보는 데는 유용하지만, 실제 마스킹 오탐과는 다르다.

따라서 `scripts/summarize_person_name_actions.py`를 추가해 다음 두 기준을 분리했다.

| 기준 | 설명 |
|---|---|
| candidate 기준 | public span 전체를 예측으로 본다. `pass` 후보도 포함한다. |
| actionable 기준 | 실제 조치인 `mask`, `hash`, `block`만 예측으로 본다. |

### 15.1 수정 내용

| 수정 | 파일 | 이유 |
|---|---|---|
| 1글자 단독 given-name 후보 제외 | `src/pii_guardrail/dictionary_detectors.py` | `별도`의 `별`처럼 일반 단어 일부가 이름으로 잡히는 문제를 줄인다. 단, `김별`처럼 성+1글자 이름은 유지한다. |
| 사람 이름 사전 확장 | `configs/dictionaries.yaml` | 확장 데이터의 강한 이름 문맥에서 일부 이름형 토큰이 후보로 생성되지 않는 문제를 줄인다. |
| PERSON_NAME 내부 suffix trim 보호 | `src/pii_guardrail/korean_boundary.py` | `사랑`이 `사` + `랑` 조사로 잘못 잘리는 문제를 막는다. |
| name label 확장 | `configs/context_rules.yaml` | `환자명`, `수령인`, `예약자`, `직원명`, `보호자`, `문의자`, `요청자`, `상담 기록` 문맥을 이름 label로 반영한다. |
| negative context 확장 | `configs/context_rules.yaml` | 프로젝트, 모델, 컬럼명, 문서, 데이터셋, 파일, 클래스, 브랜치, 화면 등 비개인정보 문맥을 감점한다. |
| PERSON_NAME label 위치 제한 | `src/pii_guardrail/context_scorer.py` | candidate 뒤쪽 설명의 `이름입니다`가 field label로 잘못 작동하는 문제를 막는다. |

### 15.2 수정 전후 비교

`stage1_person_name_expanded` 800건 기준 결과는 다음과 같다.

| 기준 | 수정 전 | 수정 후 |
|---|---:|---:|
| M10 전체 F1 | 0.4192 | 0.5703 |
| M10 전체 정밀도 | 0.3721 | 0.3989 |
| M10 전체 재현율 | 0.4800 | 1.0000 |
| M10 경계 정확도 | 0.9167 | 1.0000 |
| 마스킹 텍스트 정확 일치율 | 0.6800 | 1.0000 |
| invalid offset count | 0 | 0 |
| raw PII logging count | 0 | 0 |

actionable 기준 결과는 다음과 같다.

| 기준 | 수정 전 | 수정 후 |
|---|---:|---:|
| actionable 정밀도 | 0.6071 | 1.0000 |
| actionable 재현율 | 0.2267 | 1.0000 |
| actionable F1 | 0.3301 | 1.0000 |
| hard negative 실제 마스킹 오탐 | 13 | 0 |
| positive 실제 마스킹 정답 | 68 | 300 |

수정 후 action 분포는 다음과 같다.

| bucket | mask | pass |
|---|---:|---:|
| `hard_negative_name` | 0 | 452 |
| `person_context_positive` | 300 | 0 |

### 15.3 해석

수정 후 실제 조치 기준에서는 800건 모두 기대대로 동작한다.

- negative 문맥의 사람 이름형 토큰은 최종 `pass` 처리된다.
- positive 문맥의 사람 이름형 토큰은 최종 `mask` 처리된다.
- `사랑`처럼 조사와 겹치는 이름도 더 이상 1글자로 잘리지 않는다.
- 원문 개인정보 로그 유출과 잘못된 offset은 0으로 유지된다.

다만 candidate 기준 FP는 452건으로 남아 있다. 이는 대부분 negative 문장 안의 사람 이름 후보가 public span으로 남지만 최종 action은 `pass`인 경우다. 다음 release gate 해석에서는 candidate-level precision과 actionable precision을 분리해서 봐야 한다.

### 15.4 다음 작업

다음 단계는 두 갈래다.

1. M10 평가 리포트에 action-aware metrics를 정식으로 넣을지 결정한다. 현재 전체 precision은 candidate noise까지 포함하므로 실제 마스킹 품질을 과소평가할 수 있다.
2. 같은 방식으로 `PHONE_MOBILE`, `EMAIL`, `ADDRESS_UNIT`/`ADDRESS_FULL`, `CORPORATE_REG_NO`/`RRN` bucket을 확장하고, 각각 candidate 기준과 actionable 기준을 분리해 본다.

## 16. 3단계 action-aware 평가 지표 통합

3단계에서는 2단계에서 임시 분석 도구로 확인한 action-aware 지표를 M10 평가 리포트에 정식 필드로 추가했다.

기존 지표는 그대로 유지한다.

- `overall_precision`, `overall_recall`, `overall_f1`
- `per_entity`
- `overall`

새로 추가한 지표는 다음과 같다.

| 필드 | 의미 |
|---|---|
| `actionable_overall_precision` | `mask`, `hash`, `block`으로 최종 조치된 span만 prediction으로 본 전체 정밀도 |
| `actionable_overall_recall` | 최종 조치 기준 전체 재현율 |
| `actionable_overall_f1` | 최종 조치 기준 F1 |
| `actionable_high_risk_recall` | P0/P1 gold label 중 최종 조치된 span 기준 재현율 |
| `actionable_overall` | 최종 조치 기준 전체 TP/FP/FN 상세 |
| `actionable_per_entity` | 최종 조치 기준 entity별 TP/FP/FN 상세 |

`stage1_person_name_expanded` 800건을 새 평가 리포트로 다시 실행한 결과는 다음과 같다.

| 기준 | 값 |
|---|---:|
| candidate 전체 정밀도 | 0.3989 |
| candidate 전체 재현율 | 1.0000 |
| candidate 전체 F1 | 0.5703 |
| actionable 전체 정밀도 | 1.0000 |
| actionable 전체 재현율 | 1.0000 |
| actionable 전체 F1 | 1.0000 |
| actionable high-risk recall | 1.0000 |
| invalid offset count | 0 |
| raw PII logging count | 0 |

이제 이후 phone, email, address, corporate/RRN 확장 평가에서는 두 지표를 함께 본다.

- candidate 지표: detector와 후보 생성 노이즈를 줄이는 데 사용한다.
- actionable 지표: 실제 사용자에게 보이는 마스킹/차단 품질을 판단하는 데 사용한다.

## 17. 4단계 전화번호·이메일 확장 평가와 보정

4단계에서는 `PHONE_MOBILE`, `PHONE_LANDLINE`, `EMAIL`을 함께 보는 contact 확장 데이터셋을 만들었다. 목적은 예시 전화번호·예시 이메일이 실제 개인정보처럼 마스킹되는 오탐을 줄이면서, 실제 연락처와 이메일 재현율은 유지하는 것이다.

### 17.1 데이터 구성

| bucket | 건수 | 목적 |
|---|---:|---|
| `hard_negative_phone` | 400 | 예시, 예제, 샘플, 더미, placeholder, fixture, 목업, 교육 자료, 검증용, 스토리북, seed, synthetic, 형식 설명, 마스킹 테스트 문맥의 전화번호 오탐 확인 |
| `phone_positive` | 300 | 연락처, 전화번호, 회신 번호, 보호자 연락처 등 실제 전화번호 문맥 재현율 확인 |
| `hard_negative_email` | 300 | 예시, 예제, 샘플, 더미, 테스트, 형식 설명, 목업 문맥의 이메일 오탐 확인 |
| `email_positive` | 200 | 이메일, 메일 주소, 회신 주소, 고객 전자우편, 환자 보호자 이메일 등 실제 이메일 문맥 재현율 확인 |

### 17.2 수정 내용

| 수정 | 파일 | 이유 |
|---|---|---|
| contact marker 생성기 추가 | `scripts/generate_stage2_contact_markers.py` | 전화번호·이메일 positive/negative 1,200건을 결정적으로 생성한다. |
| 예시 문맥 축소 | `configs/context_rules.yaml` | `placeholder`, `fixture`, `목업`, `교육 자료`, `검증용`, `스토리북`, `seed`, `synthetic`, `형식 설명`, `마스킹 테스트`처럼 명시적 예시 표현만 example context로 본다. |
| contact 예시 문맥 정책 통과 | `src/pii_guardrail/policy.py` | 전화번호·이메일 후보가 예시 문맥에 있고 positive evidence가 없으면 후보는 남기되 최종 action은 `pass`로 둔다. |
| 공개 안내 번호 정책 통과 | `src/pii_guardrail/policy.py` | `고객센터`, `대표번호`, `안내번호`, `콜센터` 문맥의 전화번호는 개인 연락처로 마스킹하지 않는다. |
| 이메일 내부 keyword 제외 | `src/pii_guardrail/context_scorer.py` | `sample@example.org`의 `sample`처럼 이메일 값 내부 문자열을 예시 문맥으로 오해하지 않게 한다. |
| 전화번호형 계좌 후보 제외 | `src/pii_guardrail/regex_detectors.py` | `010 3456 7890`처럼 공백이 있는 전화번호가 `BANK_ACCOUNT` 후보로 오분류되는 문제를 막는다. |

### 17.3 수정 전후 비교

`stage2_contact_expanded` 1,200건 기준 결과는 다음과 같다.

| 기준 | 수정 전 | 수정 후 |
|---|---:|---:|
| candidate 전체 정밀도 | 0.3911 | 0.4032 |
| candidate 전체 재현율 | 0.9700 | 1.0000 |
| candidate 전체 F1 | 0.5575 | 0.5747 |
| actionable 전체 정밀도 | 0.4163 | 1.0000 |
| actionable 전체 재현율 | 0.9700 | 1.0000 |
| actionable 전체 F1 | 0.5826 | 1.0000 |
| actionable high-risk recall | 0.9700 | 1.0000 |
| 마스킹 텍스트 정확 일치율 | 0.4208 | 1.0000 |
| invalid offset count | 0 | 0 |
| raw PII logging count | 0 | 0 |

수정 후 actionable entity별 결과는 다음과 같다.

| entity | precision | recall | F1 | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|
| EMAIL | 1.0000 | 1.0000 | 1.0000 | 200 | 0 | 0 |
| PHONE_LANDLINE | 1.0000 | 1.0000 | 1.0000 | 90 | 0 | 0 |
| PHONE_MOBILE | 1.0000 | 1.0000 | 1.0000 | 210 | 0 | 0 |

### 17.4 해석

candidate 기준 false positive는 여전히 남아 있다. 예시 전화번호와 예시 이메일을 정규식 detector가 후보로 잡는 것은 의도된 동작이다. 중요한 변화는 정책 단계에서 이 후보들이 `pass`로 내려가 실제 마스킹 오탐이 0이 되었다는 점이다.

이번 단계에서 확인한 핵심은 다음과 같다.

1. 전화번호와 이메일 정규식은 약화하지 않는다. 약화하면 실제 개인정보 재현율이 떨어질 수 있다.
2. 예시·샘플·템플릿 여부는 정규식이 아니라 context scorer와 policy router에서 처리한다. 단, `연락처`, `전화번호` 같은 positive label이 있으면 예시 문맥만으로 최종 `pass`하지 않는다.
3. example context는 후보 span 바깥의 문맥에서만 본다. 이메일 주소 내부의 `sample`, `dummy`, `demo`는 예시 문맥으로 보지 않는다.
4. 계좌번호 후보 탐지 전에 전화번호 validator를 먼저 확인하면 `010 3456 7890` 같은 공백형 전화번호의 유형 혼동을 줄일 수 있다.

### 17.5 다음 작업

다음 단계는 주소 유형 분류 보정이다. `ADDRESS_UNIT`과 `ADDRESS_FULL`은 미탐과 유형 혼동이 동시에 발생하므로, 먼저 평가 데이터에서 주소 일부와 주소 전체의 annotation 기준을 고정한 뒤 수정해야 한다.

## 18. 5단계 주소 일부·주소 전체 확장 평가와 보정

5단계에서는 `ADDRESS_UNIT`, 즉 주소 일부와 `ADDRESS_FULL`, 즉 주소 전체를 분리해서 평가했다. 핵심 기준은 다음과 같다.

| 표현 | 권장 entity | 이유 |
|---|---|---|
| `서울시 강남구` | ADDRESS_UNIT | 시/구 수준 정보라 상세 주소가 아니다. |
| `서울시 강남구 역삼동` | ADDRESS_UNIT | 동 단위까지 있지만 건물 식별 정보가 없다. |
| `서울시 강남구 테헤란로` | ADDRESS_UNIT | 도로명은 있지만 건물번호가 없어 불완전하다. |
| `테헤란로 123` | ADDRESS_FULL | 시/구가 없어도 도로명과 건물번호가 있어 위치 특정성이 높다. |
| `서울시 강남구 테헤란로 123` | ADDRESS_FULL | 도로명과 건물번호가 있는 전체 주소다. |
| `서울시 강남구 역삼동 101동 1203호` | ADDRESS_FULL | 지역 조각과 동/호수 조각이 결합되어 상세 주소가 된다. |

### 18.1 데이터 구성

| bucket | 건수 | 목적 |
|---|---:|---|
| `address_unit_positive` | 200 | 시/구/동, 도로명까지만 있는 주소 일부가 `ADDRESS_UNIT`으로 남는지 확인 |
| `address_full_positive` | 200 | 도로명+건물번호, 층, 동/호수 조합이 `ADDRESS_FULL`로 잡히는지 확인 |
| `hard_negative_address` | 200 | 맛집, 뉴스, 날씨, 교통, 관광, 정책 자료 같은 일반 지역 언급이 실제 마스킹으로 이어지지 않는지 확인 |

### 18.2 수정 내용

| 수정 | 파일 | 이유 |
|---|---|---|
| 주소 marker 생성기 추가 | `scripts/generate_stage3_address_markers.py` | 주소 일부/전체/negative 600건을 결정적으로 생성한다. |
| 도로명만 있는 주소를 ADDRESS_UNIT으로 분류 | `src/pii_guardrail/dictionary_detectors.py` | `서울시 강남구 테헤란로`처럼 건물번호가 없는 도로명 주소를 `ADDRESS_FULL`로 올리지 않는다. |
| 독립 도로명+건물번호 탐지 | `src/pii_guardrail/dictionary_detectors.py` | `테헤란로 123`처럼 시/구가 없어도 건물번호가 있으면 `ADDRESS_FULL`로 잡는다. |
| 층 상세정보 포함 | `src/pii_guardrail/dictionary_detectors.py` | `테헤란로 123 5층`을 하나의 `ADDRESS_FULL` span으로 잡는다. |
| 시/구 토큰 내부 매칭 방지 | `src/pii_guardrail/dictionary_detectors.py` | `세종대로` 안의 `세종`을 주소 일부로 잘못 소비하지 않는다. |
| 도로명 끝 `로` 보호 | `src/pii_guardrail/korean_boundary.py` | `테헤란로`의 마지막 글자 `로`를 조사로 잘라 `테헤란`만 남기는 문제를 막는다. |
| annotation guideline 보강 | `docs/11_ANNOTATION_GUIDELINE.md` | 도로명만 있는 주소와 도로명+건물번호 기준을 문서화한다. |

### 18.3 수정 전후 비교

`stage3_address_expanded` 600건 기준 결과는 다음과 같다.

| 기준 | 수정 전 | 수정 후 |
|---|---:|---:|
| candidate 전체 정밀도 | 0.5217 | 0.7692 |
| candidate 전체 재현율 | 0.6000 | 1.0000 |
| candidate 전체 F1 | 0.5581 | 0.8696 |
| ADDRESS_FULL candidate F1 | 0.5789 | 1.0000 |
| ADDRESS_UNIT candidate F1 | 0.5417 | 0.7692 |
| 마스킹 텍스트 정확 일치율 | 0.7867 | 1.0000 |
| invalid offset count | 0 | 0 |
| raw PII logging count | 0 | 0 |

수정 후 candidate entity별 결과는 다음과 같다.

| entity | precision | recall | F1 | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|
| ADDRESS_FULL | 1.0000 | 1.0000 | 1.0000 | 200 | 0 | 0 |
| ADDRESS_UNIT | 0.6250 | 1.0000 | 0.7692 | 200 | 120 | 0 |

### 18.4 해석

주소 일부와 주소 전체의 미탐 및 유형 혼동은 사라졌다.

- `서울시 강남구 테헤란로`는 이제 `ADDRESS_UNIT`이다.
- `테헤란로 123`은 이제 `ADDRESS_FULL`이다.
- `서울 종로구 세종대로 10`에서 `세종대로` 안의 `세종`을 주소 일부로 잘못 잘라 먹지 않는다.
- `테헤란로` 끝의 `로`는 조사로 잘리지 않는다.

남은 120건의 candidate FP는 `서울 맛집`, `강남구 날씨`, `테헤란로 관광 가이드`처럼 지역명이 일반 정보로 쓰인 경우다. 현재 정책상 이 후보들은 최종 `pass`가 되므로 실제 마스킹 오탐은 없다. ADDRESS_UNIT은 P2 준식별자라 단독으로는 조치하지 않을 수 있으므로, 이 단계에서는 actionable recall보다 candidate 기준 분류 정확도를 중심으로 본다.

### 18.5 다음 작업

다음 단계는 법인등록번호와 주민등록번호 혼동 보정이다. `CORPORATE_REG_NO` 미탐과 `RRN` 유형 혼동은 건수는 적지만 P0/P1 구조형 식별자라 release gate에서 우선순위가 높다.

## 19. 6단계 법인등록번호·주민등록번호 혼동 보정

이번 단계는 `CORPORATE_REG_NO`, 즉 법인등록번호와 `RRN`, 즉 주민등록번호가 같은 13자리 숫자 구조에서 겹칠 때 생기는 유형 혼동을 확인했다. 특히 법인등록번호가 `110111` 같은 등기소 코드로 시작하면, 뒤 7자리가 우연히 주민등록번호 검증식까지 통과할 수 있다. 이 경우 기존 흐름은 `RRNRegexDetector`, 즉 주민등록번호 정규식 탐지기가 먼저 P0 후보를 만들고, `priority_order`, 즉 겹치는 후보 중 무엇을 우선 남길지 정하는 순서에서 주민등록번호가 법인등록번호보다 높아 최종 span이 주민등록번호로 선택될 수 있었다.

### 19.1 데이터 구성

| bucket | 건수 | 목적 |
|---|---:|---|
| `corporate_context_positive` | 200 | `법인등록번호`, `등기번호`, `법인번호`, `corporate reg no`, `corp number` 같은 명시적 법인 문맥에서 값을 `CORPORATE_REG_NO`로 잡는지 확인 |
| `rrn_context_positive` | 200 | `주민등록번호`, `주민번호`, `RRN`, `resident registration number` 같은 명시적 개인 식별 문맥에서 값을 `RRN`으로 유지하는지 확인 |

법인등록번호 positive 200건 중 일부는 주민등록번호 checksum, 즉 검증 숫자 계산까지 통과하도록 의도적으로 만들었다. 이렇게 해야 단순 패턴 테스트가 아니라 실제 유형 혼동을 재현할 수 있다.

### 19.2 초기 평가에서 확인한 문제

`stage4_corporate_rrn_expanded` 400건을 보정 전 기준으로 평가했을 때 결과는 다음과 같았다.

| 지표 | 값 |
|---|---:|
| overall precision | 0.6625 |
| overall recall | 0.6625 |
| overall F1 | 0.6625 |
| `CORPORATE_REG_NO` recall | 0.3250 |
| `RRN` precision | 0.6452 |
| masked text exact match rate | 0.6625 |
| invalid offset count | 0 |
| raw PII logging count | 0 |

오류 유형은 다음 세 가지였다.

| 오류 | 건수 | 해석 |
|---|---:|---|
| `RRN` type confusion | 110 | 법인 문맥인데 주민등록번호로 최종 선택됨 |
| `FRN` type confusion | 20 | 법인 문맥인데 `FRN`, 즉 외국인등록번호로 최종 선택됨 |
| `CREDIT_CARD` type confusion | 5 | 법인 문맥인데 `CREDIT_CARD`, 즉 신용카드로 최종 선택됨 |

### 19.3 수정 내용

| 수정 | 파일 | 이유 |
|---|---|---|
| 법인/RRN marker 생성기 추가 | `scripts/generate_stage4_corporate_rrn_markers.py` | 법인 문맥 positive와 주민등록번호 문맥 positive 400건을 결정적으로 생성한다. |
| 명시적 법인 문맥 감지 추가 | `src/pii_guardrail/regex_detectors.py` | `법인등록번호`, `등기번호`, `법인번호`, `corporate reg no`, `corp number` 바로 뒤의 13자리 값은 주민등록번호/외국인등록번호 후보에서 제외한다. |
| 명시적 개인 식별 문맥 보존 | `src/pii_guardrail/regex_detectors.py` | `주민등록번호`, `주민번호`, `RRN`, `resident registration number` 문맥에서는 같은 prefix 값이라도 `RRN` 후보를 유지한다. |
| 신용카드 후보 차단 문맥 확장 | `src/pii_guardrail/regex_detectors.py` | 법인등록번호가 Luhn, 즉 신용카드 검증식까지 우연히 통과해도 신용카드로 선택되지 않게 한다. |
| 우선순위 표에 business/corporate 추가 | `configs/entities.yaml` | `BUSINESS_REG_NO`, 즉 사업자등록번호와 `CORPORATE_REG_NO`가 fallback 최하위 우선순위로 밀리지 않게 한다. |
| 회귀 테스트 추가 | `tests/test_regex_detectors.py`, `tests/test_pipeline.py`, `tests/test_marker_eval_dataset_builder.py` | 탐지기 단위, pipeline 최종 출력, 데이터 생성기 수량을 함께 고정한다. |

### 19.4 수정 후 결과

같은 400건을 수정 후 다시 평가한 결과는 다음과 같다.

| 지표 | 값 |
|---|---:|
| overall precision | 1.0000 |
| overall recall | 1.0000 |
| overall F1 | 1.0000 |
| actionable precision | 1.0000 |
| actionable recall | 1.0000 |
| actionable F1 | 1.0000 |
| `CORPORATE_REG_NO` precision/recall/F1 | 1.0000 / 1.0000 / 1.0000 |
| `RRN` precision/recall/F1 | 1.0000 / 1.0000 / 1.0000 |
| masked text exact match rate | 1.0000 |
| invalid offset count | 0 |
| raw PII logging count | 0 |

### 19.5 해석

`RRNRegexDetector`는 주민등록번호 정규식 탐지기다. 숫자 13자리가 생년월일, 성별 숫자, checksum을 통과하면 주민등록번호 후보를 만든다. 이 동작은 P0 고위험 개인정보 recall을 위해 유지해야 한다.

`CorporateRegNoRegexDetector`는 법인등록번호 정규식 탐지기다. 법인 문맥의 값은 개인 식별자가 아니지만, 13자리 구조가 주민등록번호/외국인등록번호/신용카드 검증식과 우연히 겹칠 수 있다.

이번 수정은 “법인 문맥이면 무조건 법인등록번호”가 아니라 “값 바로 앞의 라벨이 명시적으로 법인등록번호 계열이고, 동시에 주민등록번호 계열 라벨이 아닌 경우에만 주민등록번호/외국인등록번호 후보를 만들지 않는다”는 방식이다. 그래서 P0 보호를 약화하지 않고, 명확한 법인 라벨이 있는 경우의 false positive와 유형 혼동만 줄인다.

### 19.6 다음 작업

다음 단계는 사업자등록번호와 계좌번호/전화번호/주문번호 간 혼동을 확인하는 것이다. 특히 `BUSINESS_REG_NO`, `BANK_ACCOUNT`, `PHONE_MOBILE`, `PHONE_LANDLINE`, `ORDER_ID`처럼 숫자 길이와 하이픈 구조가 겹치는 entity는 문맥 라벨과 validator 순서가 결과를 크게 바꾼다.

## 20. 7단계 사업자등록번호·계좌번호·전화번호·주문번호성 숫자 혼동 보정

이번 단계는 `BUSINESS_REG_NO`, 즉 사업자등록번호, `BANK_ACCOUNT`, 즉 계좌번호, `PHONE_MOBILE`/`PHONE_LANDLINE`, 즉 전화번호가 주문번호·접수번호·송장번호 같은 비개인 숫자 식별자와 겹치는 문제를 확인했다. `ORDER_ID`는 v0.2 entity로 추가하지 않고, 주문번호성 문맥에서는 개인정보 후보를 만들지 않는 negative fixture로만 다룬다.

### 20.1 데이터 구성

`stage5_numeric_identifier_expanded` 900건의 구성은 다음과 같다.

| bucket | 건수 | 목적 |
|---|---:|---|
| `business_context_positive` | 200 | `사업자등록번호`, `사업자번호`, `business registration number`, `BRN`, `merchant tax id` 문맥에서 사업자등록번호 recall 유지 |
| `bank_account_positive` | 200 | 은행명과 `계좌`, `계좌번호`, `bank account`, `account no` 문맥에서 계좌번호 recall 유지 |
| `phone_positive` | 200 | `연락처`, `전화번호`, `phone no` 문맥에서 휴대전화·유선전화 recall 유지 |
| `hard_negative_numeric_identifier` | 300 | `주문번호`, `예약번호`, `접수번호`, `송장번호`, `운송장번호`, `결제번호`, `order id`, `tracking no` 문맥의 숫자가 실제 마스킹으로 이어지지 않는지 확인 |

### 20.2 확인한 문제

초기 stage5 점검에서는 세 가지 문제가 보였다.

- 주문번호성 문맥의 `010-1234-5678`이 전화번호로, `123-45-67891`이 사업자등록번호로 최종 마스킹될 수 있었다.
- `tracking no 110-123-456789`처럼 계좌번호 모양의 배송·추적 번호가 계좌 후보로 남을 수 있었다.
- 계좌 validator, 즉 계좌번호 검증기는 `123-12-12345-1`과 `3333-12-1234567` 같은 은행별 세그먼트 구조를 알고 있었지만, `BankAccountCandidateDetector`, 즉 계좌번호 정규식 탐지기의 후보 정규식이 1자리 또는 7자리 세그먼트를 후보로 잡지 못했다.

### 20.3 수정 내용

| 수정 | 파일 | 이유 |
|---|---|---|
| 숫자형 식별자 marker 생성기 추가 | `scripts/generate_stage5_numeric_identifier_markers.py` | 사업자등록번호·계좌번호·전화번호 positive와 주문번호성 negative 900건을 결정적으로 생성한다. |
| 주문번호성 immediate-label 제외 확장 | `src/pii_guardrail/regex_detectors.py` | `주문번호`, `접수번호`, `송장번호`, `운송장번호`, `결제번호`, `order id`, `invoice no`, `tracking no` 바로 뒤의 숫자는 전화번호·사업자등록번호·계좌번호·신용카드 후보에서 제외한다. |
| 계좌 문맥 보호 | `src/pii_guardrail/regex_detectors.py` | 계좌 문맥의 숫자가 신용카드나 사업자등록번호 후보로 잘못 승격되지 않게 한다. |
| 계좌 후보 세그먼트 범위 보정 | `src/pii_guardrail/regex_detectors.py` | 계좌 validator가 지원하는 1자리·7자리 세그먼트를 정규식 후보 단계에서도 잡는다. |
| 영어 계좌 라벨 추가 | `configs/context_rules.yaml`, `docs/04_CONTEXT_POLICY_SPEC.md` | `bank account`, `account no`, `account number`, `deposit account`, `refund account` 문맥에서 계좌번호 최종 action이 `mask`가 되도록 한다. |
| 회귀 테스트 추가 | `tests/test_regex_detectors.py`, `tests/test_context_scorer.py`, `tests/test_pipeline.py`, `tests/test_marker_eval_dataset_builder.py` | 탐지기 단위, 문맥 점수, pipeline 최종 조치, 데이터 생성기 수량을 함께 고정한다. |

### 20.4 수정 후 결과

`stage5_numeric_identifier_expanded` 900건 기준 결과는 다음과 같다.

| 지표 | 값 |
|---|---:|
| candidate overall precision | 0.9375 |
| candidate overall recall | 1.0000 |
| candidate overall F1 | 0.9677 |
| actionable precision | 1.0000 |
| actionable recall | 1.0000 |
| actionable F1 | 1.0000 |
| actionable high-risk recall | 1.0000 |
| masked text exact match rate | 1.0000 |
| invalid offset count | 0 |
| raw PII logging count | 0 |

수정 후 actionable entity별 결과는 다음과 같다.

| entity | precision | recall | F1 | TP | FP | FN |
|---|---:|---:|---:|---:|---:|---:|
| BANK_ACCOUNT | 1.0000 | 1.0000 | 1.0000 | 200 | 0 | 0 |
| BUSINESS_REG_NO | 1.0000 | 1.0000 | 1.0000 | 200 | 0 | 0 |
| PHONE_LANDLINE | 1.0000 | 1.0000 | 1.0000 | 100 | 0 | 0 |
| PHONE_MOBILE | 1.0000 | 1.0000 | 1.0000 | 100 | 0 | 0 |

### 20.5 해석

`PhoneRegexDetector`는 전화번호 정규식 탐지기다. 이제 값 바로 앞이 주문·접수·배송·결제 식별자 라벨이면 전화번호 후보를 만들지 않는다. `BusinessRegNoDetector`는 사업자등록번호 정규식 탐지기이며, 같은 주문번호성 문맥과 계좌 문맥에서는 후보를 억제한다. `BankAccountCandidateDetector`는 계좌번호 정규식 탐지기이며, 계좌 validator가 이미 관리하는 은행별 세그먼트 길이를 후보 정규식에서도 허용한다.

후보 기준으로는 `카카오`, `토스` 같은 은행 브랜드가 `ORGANIZATION`, 즉 조직 후보로 40건 남아 있다. 하지만 최종 action은 모두 `pass`라 실제 마스킹 오탐은 없다. stage5에서 중요한 사용자-visible 조치 기준은 모두 1.0000이다.

### 20.6 다음 작업

다음 우선순위는 최신 stage별 리포트와 전체 release gate를 다시 생성한 뒤, 남은 candidate-level 조직/주소 후보 노이즈를 다음 PR 범위로 둘지 판단하는 것이다. v0.2 범위는 계속 single-turn으로 유지하며 `ORDER_ID` entity 추가, RAG, 멀티턴, LLM judge는 포함하지 않는다.
