# NER Backlog from Guardrail Evaluation

Version: v0.2-single-turn  
Date: 2026-05-22  
Status: Draft handoff note for NER team

## 1. 목적

이 문서는 Korean PII Guardrail v0.2 평가 중 발견된 NER, 즉 개체명 인식 모델 후보 생성 이슈를 NER팀 backlog로 분리하기 위한 기록이다.

이번 문서는 구현 지시서가 아니다. 목적은 guardrail 평가 결과에서 관찰된 실패 유형, 재현 조건, 기대 동작, 완료 기준을 충분히 상세하게 남겨 NER팀이 별도 이슈나 PR 범위를 잡을 수 있게 하는 것이다.

Guardrail v0.2는 single-turn, 즉 단일 입력 텍스트 후처리만 담당한다. RAG, 멀티턴, 세션 추적, Redis, LLM judge는 범위에 포함하지 않는다. NER 모델 파일, 학습 코드, 모델 가중치도 이 PR에서 수정하지 않는다.

## 2. 범위와 책임 경계

### 2.1 Guardrail 책임

Guardrail은 NER와 regex, dictionary, context, resolver, policy 결과를 결합해 최종 action을 결정한다.

- `ContextScorer`, 즉 문맥 점수 조정기는 후보 주변 문맥을 보고 점수를 올리거나 낮춘다.
- `PolicyRouter`, 즉 정책 라우터는 후보별 최종 조치를 `pass`, `mask`, `hash`, `block` 중에서 고른다.
- `SpanResolver`, 즉 겹침 후보 해결기는 같은 위치에 여러 후보가 있을 때 우선순위와 병합 규칙을 적용한다.
- 정규식 탐지기와 validator, 즉 유효성 검사기는 주민등록번호, 전화번호, 계좌번호, 사업자등록번호처럼 구조가 명확한 값을 담당한다.

이 영역에서는 release 안전성을 위해 일부 false positive, 즉 오탐 완화가 필요하다. 다만 guardrail은 NER 후보 생성 품질 자체를 영구적으로 대체하지 않는다.

### 2.2 NER팀 책임으로 분리할 영역

다음 문제는 guardrail에서 임시 완화할 수 있지만, 근본 소유권은 NER 후보 생성과 학습 데이터 품질에 있다.

- 일반 문서 설명어가 `PERSON_NAME`, 즉 사람 이름 후보로 생성됨.
- 예시 키워드가 `PERSON_NAME` 후보로 생성됨.
- 추상명사나 가치 표현이 `PERSON_NAME` 후보로 생성됨.
- 이름처럼 보이는 짧은 일반 명사가 강한 문맥 없이 높은 신뢰도 후보로 생성됨.
- `NAME`, `ADDRESS`, `ORG` 세 라벨만 직접 생성하는 NER v3 설계에서 `NAME`과 일반 명사의 경계가 일부 불안정함.

## 3. 평가 근거 요약

### 3.1 Release gate 현재 기준

최신 `reports/release_gate_v0_2.json` 기준 release gate는 통과했다.

| 항목 | 값 |
|---|---:|
| records processed | 5,000 |
| overall precision, 즉 전체 정밀도 | 0.7357 |
| overall recall, 즉 전체 재현율 | 0.9432 |
| overall F1, 즉 정밀도와 재현율의 조화 평균 | 0.8267 |
| actionable precision, 즉 실제 조치 대상 정밀도 | 0.8003 |
| actionable recall, 즉 실제 조치 대상 재현율 | 0.8119 |
| actionable F1 | 0.8061 |
| actionable high-risk recall, 즉 실제 조치 기준 고위험 재현율 | 0.9539 |
| raw PII logging count, 즉 원문 개인정보 로그 수 | 0 |
| invalid offset count, 즉 잘못된 span 위치 수 | 0 |
| release gate status | pass |

이 문서의 NER backlog는 release gate 실패를 의미하지 않는다. release gate는 현재 guardrail 완화 덕분에 통과하고 있지만, 일부 완화 규칙은 NER 후보 생성 오류를 후처리에서 막는 형태다. 장기적으로는 NER 모델 쪽에서 후보 자체의 품질을 개선하는 것이 바람직하다.

### 3.2 Stage1 사람 이름 평가 기준

`reports/eval_stage1_person_name_expanded.json` 기준 stage1 사람 이름 확장 평가는 다음 특징을 보였다.

| 항목 | 값 |
|---|---:|
| records processed | 800 |
| candidate overall precision, 즉 후보 기준 전체 정밀도 | 0.3989 |
| candidate overall recall, 즉 후보 기준 전체 재현율 | 1.0000 |
| candidate overall F1 | 0.5703 |
| actionable overall precision | 1.0000 |
| actionable overall recall | 1.0000 |
| actionable overall F1 | 1.0000 |
| PERSON_NAME spurious detections, 즉 사람 이름 불필요 후보 | 452 |
| spans detected | 752 |
| spans masked | 300 |
| raw PII logging count | 0 |
| invalid offset count | 0 |

해석:

- 최종 action 기준으로는 stage1이 통과한다.
- 그러나 candidate, 즉 후보 기준에서는 `PERSON_NAME` false positive가 많다.
- 이는 guardrail 정책 단계에서 오탐 후보를 최종 `pass`로 낮추고 있음을 뜻한다.
- 후보 생성 단계에서 불필요한 `PERSON_NAME`이 줄면 guardrail 규칙을 더 단순하게 유지할 수 있다.

## 4. 관찰된 NER 후보 생성 이슈

### 4.1 예시 키워드가 PERSON_NAME 사람 이름 후보로 생성됨

#### 현상

문서 예시, 테스트 데이터, 템플릿 설명에 쓰이는 단어가 NER에서 `PERSON_NAME` 후보로 올라오는 사례가 있었다. 대표 유형은 다음과 같다.

| 유형 | raw PII-free 예시 형태 | 기대 동작 |
|---|---|---|
| 예시 키워드 + 전자우편 설명 | `샘플 이메일 [EMAIL_EXAMPLE]` | `샘플`은 `PERSON_NAME` 후보가 아니어야 함 |
| 테스트 설명 + 연락처 예시 | `테스트 연락처 [PHONE_EXAMPLE]` | `테스트`는 `PERSON_NAME` 후보가 아니어야 함 |
| 템플릿 설명 + 입력값 자리 | `템플릿 이름 필드: [PLACEHOLDER]` | 설명어는 이름 후보가 아니어야 함 |
| 문서용 값 설명 | `문서용 계정 예시 [EMAIL_EXAMPLE]` | 문서 설명어는 이름 후보가 아니어야 함 |

여기서 `[EMAIL_EXAMPLE]`, `[PHONE_EXAMPLE]`, `[PLACEHOLDER]`는 raw PII를 남기지 않기 위한 대체 표기다.

#### 현재 guardrail 완화

- `ContextScorer`, 즉 문맥 점수 조정기는 `example_context` 예시 문맥을 감점한다.
- `example_keyword_for_person`, 즉 예시 키워드 사람 이름 감점은 후보 span 자체가 `예시`, `샘플`, `테스트` 같은 예시 키워드일 때 `PERSON_NAME` 점수를 낮춘다.
- `PolicyRouter`, 즉 정책 라우터는 예시 문맥의 연락처/전자우편/사람 이름 조합이 composite, 즉 복합 개인정보로 승격되어 마스킹되는 일을 제한한다.

#### 왜 NER backlog인가

예시 키워드는 개인을 식별하는 이름이 아니라 문서 작성자가 예시 값을 설명하기 위해 쓰는 메타 텍스트다. 이런 단어가 `PERSON_NAME`으로 반복 생성되면 guardrail이 단어 denylist, 즉 차단 단어 목록을 계속 늘리게 된다.

이 방식은 다음 위험이 있다.

- 특정 평가셋 단어에 과적합된다.
- 새 예시 키워드가 생길 때마다 guardrail 설정이 커진다.
- `PERSON_NAME` 후보 품질 문제와 최종 정책 문제가 섞인다.
- 이메일/전화번호와 같은 실제 구조형 후보와 co-occurrence, 즉 동시 등장할 때 composite으로 잘못 승격될 수 있다.

#### NER팀 검토 포인트

구현 방법을 지정하지는 않지만, NER팀이 검토할 수 있는 축은 다음과 같다.

- 예시/샘플/테스트/더미/템플릿/문서용/가이드/placeholder 계열 표현을 `NAME` negative sample, 즉 사람 이름이 아닌 반례로 보강할지 검토한다.
- 전자우편, 전화번호, 코드값 앞의 설명어가 이름으로 라벨링되지 않도록 annotation guideline, 즉 라벨링 지침을 확인한다.
- `NAME` score가 높은 경우에도 주변 문맥이 예시 설명이면 confidence calibration, 즉 신뢰도 보정이 가능한지 확인한다.
- `[EMAIL_EXAMPLE]`, `[PHONE_EXAMPLE]` 같은 구조형 예시와 함께 등장하는 앞 단어를 사람 이름으로 학습하지 않도록 hard negative, 즉 어려운 반례 묶음을 추가할지 검토한다.

#### NER 완료 기준 제안

- 예시 키워드 hard negative 평가에서 해당 키워드가 `PERSON_NAME` 후보로 생성되지 않거나 낮은 신뢰도로 생성된다.
- 실제 이름 라벨이 있는 문장, 예를 들어 `고객명 [PERSON_SYNTH]`, `담당자 [PERSON_SYNTH]`에서는 `PERSON_NAME` recall이 유지된다.
- guardrail의 `raw_pii_logging_count == 0`과 `invalid_offset_count == 0` 기준은 계속 유지된다.
- 예시 문맥 완화 규칙을 줄여도 release gate의 actionable false positive가 증가하지 않는다.

### 4.2 추상명사와 가치 표현이 PERSON_NAME 사람 이름 후보로 생성됨

#### 현상

일반 추상명사나 가치 표현이 사람 이름 후보로 올라오는 문제가 관찰되었다. raw PII를 피하기 위해 아래는 실제 문장을 그대로 옮기지 않고 유형만 남긴다.

| 유형 | raw PII-free 예시 형태 | 기대 동작 |
|---|---|---|
| 추상명사 + 가치 설명 | `[ABSTRACT_NOUN]은 중요한 가치입니다` | `[ABSTRACT_NOUN]`은 `PERSON_NAME` 후보가 아니어야 함 |
| 추상명사 + 원칙 설명 | `[ABSTRACT_NOUN]은 운영 원칙입니다` | 일반 명사 또는 O 라벨이어야 함 |
| 개념어 + 정의 문장 | `[CONCEPT_WORD]는 핵심 개념입니다` | `PERSON_NAME` 후보가 아니어야 함 |
| 감정/상태 명사 + 설명 | `[ABSTRACT_NOUN]은 문장 주제입니다` | 사람 이름 후보로 승격되지 않아야 함 |

#### 현재 guardrail 완화

- `abstract_value_context_for_person`, 즉 추상 가치 문맥 사람 이름 감점이 추가되어 있다.
- 이 근거는 `ContextScorer` 문맥 점수 조정기에서 `PERSON_NAME` 점수를 낮추는 데 사용된다.
- 현재 정리된 방향에서는 이 근거만으로 `PolicyRouter` 정책 라우터가 강제 `pass`를 적용하지 않고, 점수 감점 근거로만 사용한다.

#### 왜 NER backlog인가

추상명사는 사람 이름과 표면형이 겹칠 수 있다. 예를 들어 어떤 단어는 일반 명사이면서 동시에 별칭, 예명, 닉네임, 드문 이름일 수 있다. 따라서 guardrail이 단어 자체를 강하게 차단하면 실제 사람 이름 recall, 즉 실제 탐지율이 떨어질 수 있다.

이 문제는 단어 목록을 늘리는 방식으로 풀기 어렵다.

- 추상명사 목록은 끝이 없다.
- hard negative 데이터셋에 나온 표현만 잘 통과하는 과적합이 생긴다.
- 실제 이름과 일반 명사의 경계는 모델의 문맥 이해와 라벨링 데이터 품질에 더 가깝다.
- guardrail에서 강한 차단으로 처리하면 `PERSON_NAME` P1 보호를 약화시킬 수 있다.

#### NER팀 검토 포인트

- 추상명사, 감정 명사, 가치 표현, 개념 설명 문장을 `NAME` negative sample로 추가할지 검토한다.
- `은/는`, `이다`, `입니다`, `가치`, `원칙`, `개념`, `문장`, `주제` 같은 서술 문맥에서 `NAME` score가 과도하게 높아지는지 분석한다.
- 실제 이름이 같은 표면형으로 등장하는 positive sample도 함께 유지해 recall 회귀를 방지한다.
- 짧은 단어가 단독으로 등장할 때와 `고객명`, `담당자`, `환자명`, `신청자` 같은 이름 라벨 뒤에 등장할 때 confidence 차이가 충분한지 확인한다.

#### NER 완료 기준 제안

- 추상명사 hard negative 묶음에서 `PERSON_NAME` 후보 수가 유의미하게 감소한다.
- 이름 라벨이 있는 positive 묶음에서는 `PERSON_NAME` recall이 유지된다.
- 별칭/예명/닉네임처럼 일반명사와 겹칠 수 있는 positive 묶음을 별도로 두어 과도한 차단을 방지한다.
- guardrail의 `abstract_value_context_for_person` 감점 의존도를 낮춰도 release gate가 유지된다.

### 4.3 짧은 일반 명사와 이름 사전 경계

#### 현상

사람 이름은 한국어 일반 명사와 표면형이 겹칠 수 있다. NER 또는 dictionary, 즉 사전 기반 후보 생성이 짧은 단어를 사람 이름 후보로 올리면 false positive가 늘어난다.

| 유형 | raw PII-free 예시 형태 | 기대 동작 |
|---|---|---|
| 한 글자 이름 후보 | `[ONE_CHAR_TOKEN]` 단독 등장 | 강한 이름 문맥 없이는 action 대상이 아니어야 함 |
| 일반 명사와 이름 표면형 겹침 | `[COMMON_NOUN] 안내 문장` | 설명어는 사람 이름 후보가 아니어야 함 |
| 상품/브랜드/프로젝트 이름 | `[TOKEN] 모델 테스트` | 사람 이름보다 코드/문서/상품 문맥으로 봐야 함 |
| 이름 라벨 있는 실제 값 | `고객명 [PERSON_SYNTH]` | `PERSON_NAME`으로 유지되어야 함 |

#### 현재 guardrail 완화

- `DictionaryDetector`, 즉 사전 기반 탐지기는 한 글자 given name, 즉 이름 후보를 단독으로 강하게 올리지 않도록 조정되어 있다.
- `ContextScorer` 문맥 점수 조정기는 이름 라벨이 후보 앞쪽 가까운 위치에 있을 때만 `field_label_name` 이름 필드 라벨 boost, 즉 점수 상승을 적용한다.
- `business_name`, `code_or_log_context`, `example_context` 같은 negative context, 즉 비개인정보 문맥이 사람 이름 후보 점수를 낮춘다.

#### 왜 NER backlog인가

dictionary 조정은 guardrail 책임 안에 있지만, NER가 일반 명사를 높은 신뢰도의 `NAME`으로 생성하는 경우에는 guardrail이 계속 후처리 규칙을 추가해야 한다. 이는 장기적으로 NER와 guardrail의 책임 경계를 흐린다.

#### NER팀 검토 포인트

- 짧은 일반 명사와 사람 이름 positive를 함께 둔 contrastive set, 즉 대조 평가 묶음을 만든다.
- `고객명`, `신청자`, `담당자`, `환자명`, `수령인` 등 이름 라벨이 있을 때와 없을 때 score 차이를 확인한다.
- 상품명, 모델명, 프로젝트명, 문서명, 코드 식별자 문맥에서 `NAME` 라벨이 과도하게 생성되는지 점검한다.
- guardrail의 이름 사전 확장으로 NER recall 부족을 계속 보완하는 구조가 되지 않게 NER positive/negative 라벨 기준을 정리한다.

#### NER 완료 기준 제안

- 이름 라벨 없는 짧은 일반 명사의 `PERSON_NAME` 후보 생성률이 낮아진다.
- 이름 라벨 있는 실제 합성 이름의 recall은 유지된다.
- dictionary-only 후보와 NER 후보가 결합될 때 false positive가 증가하지 않는다.
- `span.text == raw_text[span.start:span.end]` offset 계약이 NER 출력에서도 유지된다.

## 5. NER팀 이슈 작성용 요약

### 5.1 이슈 제목 후보

`PERSON_NAME 후보 생성에서 예시 키워드와 추상명사 오탐 개선`

### 5.2 이슈 본문 초안

Guardrail v0.2 release gate와 stage1 사람 이름 확장 평가에서 `PERSON_NAME`, 즉 사람 이름 후보 생성 오탐이 확인되었다. Guardrail 정책 단계에서 최종 action은 대부분 `pass`로 낮춰 release gate는 통과하지만, 후보 단계 false positive가 많아 후처리 규칙이 복잡해지고 있다.

관찰된 주요 유형:

- 예시/샘플/테스트/템플릿/문서용 같은 설명어가 `PERSON_NAME` 후보로 생성됨.
- 추상명사나 가치/원칙/개념 설명어가 `PERSON_NAME` 후보로 생성됨.
- 짧은 일반 명사 또는 상품/모델/문서 문맥의 단어가 이름 후보로 생성됨.

Guardrail 현재 완화:

- `ContextScorer` 문맥 점수 조정기에서 `example_context`, `example_keyword_for_person`, `abstract_value_context_for_person` 감점 적용.
- `PolicyRouter` 정책 라우터에서 예시 문맥의 composite, 즉 복합 개인정보 승격을 제한.
- `DictionaryDetector` 사전 기반 탐지기에서 한 글자 이름 후보와 이름 라벨 boost 조건을 보수화.

NER팀 검토 요청:

- 예시 키워드, 추상명사, 문서 설명어, 코드/상품/모델 문맥을 `NAME` negative sample로 추가할지 검토.
- 실제 이름 라벨 positive sample을 함께 유지해 `PERSON_NAME` recall 회귀 방지.
- 짧은 일반 명사와 실제 이름을 구분하는 confidence calibration, 즉 신뢰도 보정 가능성 검토.
- NER 후보 출력에서도 raw offset 계약을 유지.

완료 기준:

- Guardrail stage1 사람 이름 확장 평가에서 후보 기준 `PERSON_NAME` spurious detection이 감소.
- 실제 조치 기준 precision/recall/F1 회귀 없음.
- release gate에서 raw PII logging count 0, invalid offset count 0 유지.
- Guardrail 쪽 특정 단어 denylist 확장 없이 동일 유형 오탐 감소.

## 6. Guardrail PR에 남길 설명

이번 guardrail PR에는 release 안전성을 위한 최소 완화만 포함한다. `example_keyword_for_person` 예시 키워드 사람 이름 감점과 `abstract_value_context_for_person` 추상 가치 문맥 사람 이름 감점은 NER 후보 생성 이슈를 영구적으로 소유하기 위한 규칙이 아니라, release gate에서 raw PII 안전과 false positive 감소를 동시에 만족하기 위한 제한적 방어다.

PR 설명에는 다음 문장을 포함하는 것을 권장한다.

```text
Known follow-up:
Some PERSON_NAME false positives appear to originate from NER candidate generation, especially example keywords and abstract nouns being emitted as person-name candidates. This PR keeps only minimal guardrail-side mitigation for release safety. Longer-term correction is tracked separately with the NER team.
```

한국어 설명:

```text
알려진 후속 이슈:
일부 PERSON_NAME 사람 이름 false positive는 guardrail 규칙 문제가 아니라 NER 후보 생성 단계에서 예시 키워드와 추상명사가 사람 이름 후보로 올라오는 문제로 보인다. 이번 PR에는 release 안전성을 위한 최소 완화만 포함하고, 장기 수정은 NER팀 이슈로 별도 추적한다.
```

## 7. Raw PII 안전 원칙

NER팀으로 전달하는 이슈, 문서, 평가 리포트에는 raw PII, 즉 원문 개인정보를 넣지 않는다.

허용되는 표기:

- `[PERSON_SYNTH]`
- `[EMAIL_EXAMPLE]`
- `[PHONE_EXAMPLE]`
- `[ADDRESS_SYNTH]`
- `[ABSTRACT_NOUN]`
- `[CONCEPT_WORD]`
- `[PLACEHOLDER]`

금지되는 표기:

- 실제 사용자 이름
- 실제 전화번호
- 실제 전자우편 주소
- 실제 주소
- 실제 주민등록번호, 외국인등록번호, 여권번호, 계좌번호
- audit, report, public span에 원문 개인정보를 그대로 복사한 예시

## 8. NER팀 전달 시 우선순위

| 우선순위 | 항목 | 이유 |
|---:|---|---|
| P1 | 예시 키워드의 `PERSON_NAME` 후보 생성 억제 | composite 승격과 문서 예시 오탐에 직접 영향 |
| P1 | 추상명사/가치 표현의 `PERSON_NAME` 후보 생성 억제 | 특정 단어 denylist 확장을 막기 위해 필요 |
| P2 | 짧은 일반 명사와 실제 이름의 confidence 분리 | 이름 recall과 false positive 균형에 영향 |
| P2 | 이름 라벨 positive와 hard negative 대조 평가 추가 | 회귀 방지와 모델 calibration 근거 확보 |
| P3 | Guardrail 완화 규칙 축소 가능성 검증 | NER 개선 뒤 후처리 규칙 단순화 가능 |

## 9. Guardrail 쪽에서 당장 하지 않을 것

이번 PR 범위에서는 다음 작업을 하지 않는다.

- NER 모델 가중치 수정
- NER 학습 코드 수정
- NER 데이터셋 라벨 직접 변경
- 특정 일반 명사 denylist 대량 추가
- LLM judge 기반 후처리 추가
- 멀티턴 이력 기반 이름 판단 추가
- RAG 문맥 조회 기반 후보 보정 추가

## 10. 후속 추적 기준

NER팀 이슈가 완료되면 guardrail 쪽에서는 다음을 확인한다.

- `reports/eval_stage1_person_name_expanded.json`에서 후보 기준 `PERSON_NAME` precision이 개선되는지 확인한다.
- actionable precision/recall/F1이 유지되는지 확인한다.
- `reports/release_gate_v0_2.json`에서 release gate가 계속 pass인지 확인한다.
- `raw_pii_logging_count == 0`과 `invalid_offset_count == 0`을 확인한다.
- `example_keyword_for_person`과 `abstract_value_context_for_person` 규칙을 줄일 수 있는지 별도 PR에서 검토한다.
