# 축소/일반화 점검 해결 기록

Version: v0.2-single-turn
Date: 2026-05-24

## 목적

이 문서는 stage1-5 false positive 개선 뒤 리뷰에서 나온 "축소/일반화 필요" 항목을 어떻게 줄였는지 기록한다. 목표는 guardrail 책임 범위 안에서 숫자형 식별자 혼동을 줄이되, 특정 stage 데이터셋에만 맞춘 규칙이나 NER 후보 생성 오류를 과하게 덮는 정책을 피하는 것이다.

외부 자료조사는 진행하지 않았다. 이번 판단에 필요한 근거는 모두 저장소 내부의 설계 문서, stage5 평가 데이터, 기존 회귀 테스트에서 확인할 수 있었다. 특히 v0.2는 single-turn deterministic core이고, 숫자형 식별자 혼동은 `regex_detectors.py` 정규식 탐지기와 `validators.py` 유효성 검사기의 책임 경계 안에 있다.

## 해결 단계

### 1. 숫자형 식별자 문맥 라벨을 config로 이동

이전 구현은 `regex_detectors.py` 정규식 탐지기에 주문번호, 계좌, 법인등록번호, 주민등록번호, 의무기록번호 라벨 목록을 코드 상수로 직접 넣었다. 이는 동작 소유권이 config에 있어야 한다는 프로젝트 규칙과 맞지 않았다.

변경 후에는 `configs/context_rules.yaml`의 `structured_identifier_contexts`가 라벨 목록을 소유한다. `load_structured_context_terms`, 즉 구조형 식별자 문맥 설정 로더가 이 설정을 읽고, `RRNRegexDetector` 주민등록번호 정규식 탐지기, `FRNRegexDetector` 외국인등록번호 정규식 탐지기, `BusinessRegNoDetector` 사업자등록번호 정규식 탐지기, `BankAccountCandidateDetector` 계좌번호 후보 정규식 탐지기, `CreditCardRegexDetector` 신용카드 정규식 탐지기가 동일한 설정을 사용한다.

근거:
- `docs/10_DEVELOPMENT_HANDOFF.md`는 score/context rule을 코드에 하드코딩하지 말고 config로 두라고 명시한다.
- `tests/test_context_scorer.py::test_structured_identifier_context_terms_loaded_from_yaml`가 설정 로더 동작을 고정한다.

### 2. 계좌 문맥 차단 범위 축소

이전 구현은 값 앞 64자 안에 계좌 관련 단어가 있으면 `BUSINESS_REG_NO`, 즉 사업자등록번호 후보를 차단했다. 이 방식은 같은 문장에 계좌와 사업자등록번호가 함께 있는 정상 정산 문서에서 사업자등록번호 recall, 즉 실제 탐지율을 낮출 수 있다.

변경 후에는 계좌 문맥을 같은 필드 구간 안에서만 본다. 쉼표, 마침표, 줄바꿈, 세미콜론, 파이프 뒤의 다음 필드로는 계좌 문맥을 전파하지 않는다. 다만 실제 계좌 양식에서는 계좌 라벨과 값 사이에 은행명이 들어갈 수 있으므로, 계좌 라벨은 값 바로 왼쪽이 아니라 같은 필드 구간 안에 있으면 인정한다.

근거:
- `stage5_numeric_identifier_expanded` 데이터는 계좌 라벨과 은행명 사이에 값이 들어가는 양식을 포함한다.
- `tests/test_regex_detectors.py::test_business_reg_no_detector_keeps_business_label_after_account_field`는 계좌 필드 뒤 별도 사업자등록번호 필드의 recall을 고정한다.
- `tests/test_regex_detectors.py::test_business_reg_no_detector_rejects_account_field_with_intermediate_bank_name`는 은행명이 중간에 있는 계좌 필드가 사업자등록번호로 승격되지 않음을 고정한다.

### 3. 주문번호·사업자·법인·개인등록·의무기록 라벨은 즉시 왼쪽으로 제한

주문번호성 식별자와 법인/개인 등록번호, 의무기록번호 라벨은 값 바로 왼쪽 라벨일 때만 적용한다. 이 범위는 false positive를 줄이면서도 다른 필드의 P0/P1 식별자 recall을 침범하지 않기 위한 제한이다.

stage1-4 리포트를 최종 코드 기준으로 재생성하는 과정에서 `법인 식별번호` 표기처럼 라벨 내부 띄어쓰기가 설정의 `법인 식별 번호`와 다른 케이스가 발견됐다. 이에 구조형 라벨 매칭은 범위는 그대로 immediate-label로 유지하되, 라벨 내부 공백은 선택적으로 허용하도록 일반화했다.

근거:
- `stage5_numeric_identifier_expanded`의 `hard_negative_numeric_identifier` bucket은 주문번호성 라벨 바로 뒤 숫자가 개인정보로 마스킹되지 않아야 한다는 요구를 검증한다.
- `stage4_corporate_rrn_expanded`는 법인등록번호 라벨 바로 뒤 값이 주민등록번호로 오분류되지 않아야 한다는 요구를 검증한다.
- `tests/test_regex_detectors.py::test_credit_card_detector_rejects_non_card_structured_context`는 법인/계좌 문맥에서 신용카드 후보가 만들어지지 않는 회귀를 고정한다.
- `tests/test_regex_detectors.py::test_rrn_detector_rejects_corporate_context_with_spacing_variant`는 `법인 식별번호` 같은 띄어쓰기 변형에서도 주민등록번호 후보가 만들어지지 않는 회귀를 고정한다.

### 4. 추상 가치 사람 이름 문맥은 policy 강제 pass에서 제거

`abstract_value_context_for_person`, 즉 추상 가치 문맥의 사람 이름 감점은 NER가 일반 명사를 `PERSON_NAME`, 즉 사람 이름 후보로 올리는 문제를 완화하기 위한 보정이다. 하지만 이 근거만으로 `PolicyRouter`, 즉 최종 조치 라우터가 고신뢰 사람 이름 후보를 강제 `pass`하면 실제 사람 이름 recall을 낮출 수 있다.

변경 후에는 이 문맥을 점수 감점으로만 사용한다. 점수는 `-0.35`에서 `-0.20`으로 완화했고, 최종 action 강제 pass 조건에서는 제외했다. 즉 이름 라벨, 연락처 결합, 높은 NER 신뢰도 같은 positive evidence가 있으면 실제 사람 이름 후보가 계속 마스킹될 수 있다.

근거:
- `tests/test_policy.py::test_abstract_value_context_does_not_force_high_confidence_person_name_to_pass`는 추상 가치 문맥만으로 고신뢰 사람 이름 후보를 강제 pass하지 않음을 고정한다.
- `tests/test_context_scorer.py::test_abstract_value_context_suppresses_person_name_candidate`는 문맥 점수 감점 근거가 여전히 남아 있음을 고정한다.

## NER backlog로 남긴 사항

`example_keyword_for_person`, 즉 예시 키워드 사람 이름 감점과 `abstract_value_context_for_person`의 근본 원인은 NER 후보 생성 품질이다. guardrail은 release gate 안전을 위해 최소한의 정책 방어를 유지하지만, "샘플", "사랑" 같은 일반 단어가 사람 이름 후보로 반복 생성되는 문제는 NER 학습 데이터와 calibration, 즉 신뢰도 보정 backlog로 넘겨야 한다.

이번 PR에서는 NER 모델 파일, 학습 코드, 모델 가중치를 수정하지 않았다.

## 검증 기준

이번 축소/일반화 작업의 검증 기준은 다음과 같다.

- raw offset 보존: 모든 span은 `span.text == raw_text[span.start:span.end]`를 만족해야 한다.
- raw PII 안전: 로그, audit, public span, 평가 리포트에 raw PII를 추가하지 않는다.
- P0/P1 recall 보존: 사업자등록번호, 법인등록번호, 주민등록번호, 전화번호, 계좌번호의 positive recall을 낮추지 않는다.
- stage5 actionable precision 유지: 주문번호성 숫자 식별자가 실제 mask/block/hash action으로 이어지지 않아야 한다.

## 현재 권장 후속 검증

집중 테스트 뒤에는 다음을 실행해 PR 근거를 갱신한다.

```bash
python -m pytest tests/test_regex_detectors.py tests/test_context_scorer.py tests/test_policy.py tests/test_pipeline.py -q
python scripts/build_marker_eval_dataset.py --input data/eval/markers/stage5_numeric_identifier_expanded.jsonl --output data/eval/generated/stage5_numeric_identifier_expanded.jsonl
python scripts/run_eval.py --config-dir configs --dataset data/eval/generated/stage5_numeric_identifier_expanded.jsonl --output reports/eval_stage5_numeric_identifier_expanded.json --failure-output reports/failure_cases_stage5_numeric_identifier_expanded.jsonl --audit-safety-output reports/audit_safety_stage5_numeric_identifier_expanded.json --mock-ner
python scripts/run_release_gate.py --config-dir configs --progress-interval 500
python -m pytest
```

## 2026-05-22 검증 결과

이번 축소/일반화 반영 후 실행한 검증 결과는 다음과 같다.

### PR review 반영

PR review에서 `데모`, `가이드`, `문서`, `데이터셋` 같은 넓은 negative 단어가 같은 문장에 있다는 이유만으로 실제 연락처나 사람 이름이 `pass`될 수 있다는 recall 위험이 확인됐다. 이에 다음을 반영했다.

- CONTACT, 즉 전화번호·전자우편 계열은 `context.boost.*` 또는 `context.composite.*` 같은 positive evidence가 있으면 `example_context`만으로 최종 `pass`하지 않는다.
- `example_context`는 `예시`, `예제`, `샘플`, `placeholder`, `fixture`, `형식 설명`처럼 명시적인 예시 표현 중심으로 축소했다.
- `데모`, `템플릿`, `가이드`, `샌드박스`, `매뉴얼`, `문서용`처럼 실제 업무 문장에도 자주 나오는 단어는 단독 결정적 negative 문맥에서 제외했다.
- `code_context`도 `stack`, `traceback`, `json`, `변수명`, `로그`, `error`, `debug`, `컬럼명`, `클래스`, `브랜치`처럼 코드·로그를 직접 가리키는 단어만 남기고, `문서`, `데이터셋`, `파일`, `모델`, `프로젝트`, `라벨`, `지표`, `시나리오`, `화면`처럼 실제 개인정보 문장에 자주 섞이는 단어는 제외했다.
- `작성자`는 사람을 가리키는 명시적 field label로 추가해 `이 데이터셋 문서 작성자 홍길동` 같은 실제 사람 이름 recall을 보존한다.
- 회귀 테스트는 `test_pipeline_masks_real_pii_with_broad_document_words`와 `test_pipeline_passes_explicit_example_phone`으로 고정했다.

stage1-4 리포트는 stage5 수정 뒤 최종 코드 기준으로 다시 생성했다. stage5도 같은 코드 기준으로 다시 실행해 stage별 리포트의 기준을 맞췄다.

| stage 리포트 | records | overall P/R/F1 | actionable P/R/F1 | high-risk recall | 안전 기준 |
|---|---:|---|---|---:|---|
| stage1 person name seed | 24 | 0.5714 / 1.0 / 0.7273 | 1.0 / 1.0 / 1.0 | 1.0 | raw 0, invalid offset 0, audit pass |
| stage1 person name expanded | 800 | 0.3989 / 1.0 / 0.5703 | 1.0 / 1.0 / 1.0 | 1.0 | raw 0, invalid offset 0, audit pass |
| stage2 contact expanded | 1200 | 0.4032 / 1.0 / 0.5747 | 1.0 / 1.0 / 1.0 | 1.0 | raw 0, invalid offset 0, audit pass |
| stage3 address expanded | 600 | 0.7692 / 1.0 / 0.8696 | 1.0 / 0.5 / 0.6667 | 1.0 | raw 0, invalid offset 0, audit pass |
| stage4 corporate/RRN expanded | 400 | 1.0 / 1.0 / 1.0 | 1.0 / 1.0 / 1.0 | 1.0 | raw 0, invalid offset 0, audit pass |
| stage5 numeric identifier expanded | 900 | 0.9375 / 1.0 / 0.9677 | 1.0 / 1.0 / 1.0 | 1.0 | raw 0, invalid offset 0, audit pass |

stage3의 actionable recall 0.5는 `ADDRESS_UNIT`, 즉 주소 일부 엔티티가 정책상 `pass`로 남는 설계 때문이다. 고위험 recall은 1.0으로 유지됐다.

| 검증 | 결과 | 근거 |
|---|---:|---|
| 집중 pytest | 14 passed | 라벨 기반 내부 식별자 context boost 및 order-like negative 회귀 테스트 |
| 전체 pytest | 1275 passed | `fix/release-gate-failures` 현재 작업트리 전체 단위 테스트 |
| stage5 mock NER 평가 | pass | actionable precision/recall/F1 모두 1.0 |
| stage5 raw PII 안전 | pass | `raw_pii_logging_count=0`, `invalid_offset_count=0` |
| release gate | pass | 5,000건, `overall_precision=0.8803`, `overall_recall=0.9729`, `overall_f1=0.9243` |
| release gate actionable | pass | `actionable_precision=0.9975`, `actionable_recall=0.8991`, `actionable_f1=0.9457` |
| release gate 핵심 recall | pass | high-risk structured recall 1.0, phone/email recall 1.0 |
| release gate 조사 경계 | pass | josa boundary accuracy 0.9989 |
| release gate raw PII 안전 | pass | raw PII leak 0, invalid offset 0, audit pass |

release gate는 real NER 경로를 포함하므로 deterministic-only latency 기준은 skipped로 기록되었다. 이는 `run_release_gate.py`의 기준과 맞다.

최신 production release gate 기준 잔여 failure row는 `PERSON_NAME` FN, hard negative candidate FP, `ADDRESS_FULL` type confusion이다. `CUSTOMER_ID`, `EMPLOYEE_ID`, `STUDENT_ID`는 조직별 포맷 근거가 필요한 custom identifier profile 범위이므로 production 기본 release gate에서 제외한다. 구조형 PII 경로는 production 지원 범위에서 안정적이며, 잔여 과제는 `docs/17_NER_BACKLOG_FROM_GUARDRAIL_EVAL.md`의 NER backlog와 `reports/release_gate_failure_analysis_ko.md`의 최신 분석으로 분리한다.
