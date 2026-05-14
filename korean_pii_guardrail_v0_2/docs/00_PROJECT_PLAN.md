# Korean PII Guardrail v0.2 상세 계획서

Version: v0.2-single-turn  
Date: 2026-05-09  
Scope: 한국어 단일 턴 개인정보 탐지 및 비식별화 deterministic core

## 1. 프로젝트 목적

본 프로젝트는 한국어 텍스트에서 개인정보 및 보안비밀 후보를 탐지하고, 한국어 문장 구조를 보존하면서 정책에 맞게 비식별화하는 가드레일을 구현한다.

v0.2의 목표는 단일 입력 텍스트 기준으로 다음을 완성하는 것이다.

1. raw text offset 기준의 개인정보 후보 탐지
2. 한국어 조사·호칭·어미 boundary correction
3. detector별 score 산정과 context 기반 보정
4. 중복·겹침 span resolver
5. LLM Gateway target별 masking policy
6. raw PII 없는 audit event
7. 평가셋과 ablation harness

## 2. 범위

### 2.1 포함 범위

| 영역 | 포함 내용 |
|---|---|
| 입력 | 단일 문자열 `text` |
| 스캔 위치 | `input`, `output` |
| 전처리 | L0 기반 한국어 변형 공격 대응, Unicode/NFKC, dash 정규화, zero-width 제거, 숫자 variant, raw offset map |
| 탐지 | regex, validator, dictionary, mock/fine-tuned NER interface |
| 한국어 보정 | 조사, 호칭, 종결어미, 숫자형 PII 후행 조사 trimming |
| 문맥 | 단일 입력 텍스트 내부 context window |
| 조합 위험 | 같은 문장 또는 field block 내부 composite PII |
| 판정 | risk level, score threshold, deterministic context judge |
| 마스킹 | LLM Gateway MVP 기준 label mask, HMAC hash, block |
| 로그 | raw PII 없는 audit event |
| 평가 | 단일 턴 gold set, hard cases, adversarial, ablation |

### 2.2 제외 범위

| 영역 | 제외 내용 |
|---|---|
| RAG | retrieval context scan, RAG document sanitization |
| 멀티턴 | session graph, fragment ledger, subject tracker, 이전 턴 누적 위험 |
| LLM judge | 실시간 LLM 기반 추가 판정 |
| 운영 UI | human review dashboard |
| 모델 연구 | NER fine-tuning 자체는 interface 이후 별도 진행 |
| 복원형 토큰화 | v0.2 기본값은 비복원 label mask |

> Milestone note: 이 문서는 초기 상세 계획서이며, 최신 milestone 번호와 구현 순서는 `docs/07_IMPLEMENTATION_ROADMAP.md`를 기준으로 한다. 최신 기준에서 M7은 LLM Gateway MVP용 policy router와 masker이고, evaluation harness는 M10이다.

## 3. 핵심 산출물

| 산출물 | 파일 | 책임 |
|---|---|---|
| 요구사항 명세 | `docs/01_REQUIREMENTS_SPEC.md` | PM/Tech Lead |
| 아키텍처 명세 | `docs/02_ARCHITECTURE_SPEC.md` | Pipeline Owner |
| 점수 정책 | `docs/03_SCORING_POLICY_SPEC.md`, `configs/scoring.yaml` | Pipeline Owner |
| context 정책 | `docs/04_CONTEXT_POLICY_SPEC.md`, `configs/context_rules.yaml` | Pipeline Owner |
| 마스킹 정책 | `docs/05_MASKING_POLICY_SPEC.md`, `configs/policy_profiles.yaml` | Pipeline Owner |
| 인터페이스 | `docs/06_INTERFACE_SPEC.md`, `api/openapi.yaml`, `schemas/*.json` | Tech Lead |
| 평가 계획 | `docs/08_EVALUATION_PLAN.md`, `data/eval/hard_cases_v0.jsonl` | Evaluation Owner |
| 컴플라이언스 | `docs/09_COMPLIANCE_AND_AUDIT_SPEC.md` | Compliance Owner |
| 개발 skeleton | `src/pii_guardrail/` | Pipeline Owner |

## 4. 역할 분담

### 4.1 Pipeline Owner

- schema 및 enum 확정
- preprocessor와 raw offset map 구현
- regex detector와 validator 구현
- dictionary loader 구현
- Korean boundary corrector 구현
- context scorer 구현
- span resolver 구현
- masker 구현
- audit logger 구현
- evaluation harness 구현

### 4.2 NER Owner

- annotation guideline 개선
- NER label mapping 정의
- mock NER 출력 형식 검증
- baseline NER wrapper 구현
- fine-tuned NER 모델 교체 준비
- NER calibration 결과를 pipeline score 체계에 연결

### 4.3 Evaluation Owner

- gold set 구축
- hard negative와 adversarial case 생성
- metric runner 구현
- ablation report 작성
- release gate 검증

### 4.4 Compliance Owner

- 가명처리 목적과 처리 항목 정리
- raw PII logging 금지 검증
- HMAC key 관리 기준 정리
- 가명처리 결과서/적정성 검토 보고서 작성 체계 정리

## 5. 단계별 계획

### M0. 계약 확정

기간: 2~3일

#### 작업

- `EntityType`, `RiskLevel`, `OutputTarget`, `PolicyProfile` 확정
- `PIISpan`, `DetectionResult`, `GuardrailRequest`, `GuardrailResponse` 확정
- raw offset contract 문서화
- JSON Schema와 Python dataclass 동기화

#### 완료 기준

- schema JSON roundtrip 가능
- unknown entity type 처리 정책 확정
- raw offset invalid case 테스트 실패 처리

### M1. L0 기반 전처리 및 offset map

기간: 1~2주

#### 작업

- 기존 Layer 0에서 검증된 한국어 변형 공격 대응 전략을 v0.2 offset contract에 맞게 재구현
- offset-safe normalization: NFKC, dash/hyphen, zero-width, full-width digit, mathematical/circled digit
- structure-preserving variants: digit compact, digit-space compact, Korean keyword spacing compact
- L0-derived advanced variants: 자모 결합, 초성 복원, 야민정음 복원, 로마자 한국어 복원, 한글 숫자 복원
- Kiwi/kiwipiepy는 문장·어절·형태소 경계 품질 비교를 위한 optional reference로 검증
- normalized span → raw span 복원

#### 완료 기준

- zero-width가 포함된 전화번호를 raw offset으로 복원 가능
- emoji, 전각 숫자, 붙여쓰기 환경에서 offset mismatch 없음
- `ㅈㅜㅁㅣㄴ`, `ㅈㅁㅂㅎ`, `즈민뜽록`, `jumin`, `공일공` 계열 변형을 탐지용 variant로 생성 가능
- 모든 variant 탐지 결과를 raw text span으로 복원 가능
- 복원된 span은 `span.text == raw_text[span.start:span.end]` 조건을 만족

### M2. 구조형 detector

기간: 1~2주

#### 작업

- RRN/FRN detector
- phone mobile/landline detector
- email detector
- credit card detector + Luhn
- business registration number detector
- bank account candidate detector
- IP/MAC/API key detector
- suffix trimming 연동

#### 완료 기준

- 구조형 hard cases recall 목표치 충족
- email 내부 username을 PERSON으로 중복 마스킹하지 않음
- 숫자형 order id를 계좌로 과탐하지 않음

### M3. 한국어 boundary corrector

기간: 1주

#### 작업

- josa/honorific/ending suffix table 작성
- PERSON/ADDRESS/ORGANIZATION suffix split
- numeric PII trailing josa trim
- offset-safe reconstruction

#### 완료 기준

- `홍길동이 → [PERSON_1]이`
- `김민수에게 → [PERSON_1]에게`
- `010-1234-5678로 → [PHONE_1]로`
- `test@example.com입니다 → [EMAIL_1]입니다`

### M4. dictionary/context scorer

기간: 1~2주

#### 작업

- dictionary loader
- context window 구현
- field label boost
- co-occurrence boost
- negative context penalty
- deterministic context judge 구현

#### 완료 기준

- `하늘` 단독은 기본적으로 pass 또는 low confidence
- `고객명 하늘, 연락처 010-...`는 PERSON으로 mask
- `오늘 하늘이 맑네요`는 pass

### M5. span resolver/masker (초기 계획 번호)

기간: 1~2주

#### 작업

- 동일 span score merge
- overlap priority
- EMAIL 내부 PERSON 제거
- ADDRESS fragment merge
- single-turn composite escalation
- LLM Gateway target별 masking policy
- placeholder index 안정화

#### 완료 기준

- 중복 detector 결과가 하나의 최종 span으로 정리됨
- 같은 값은 동일 문서 내 같은 placeholder로 치환됨
- raw PII audit log 저장 없음

### M6. NER interface integration

기간: 1주

#### 작업

- `BaseNERDetector` protocol
- `MockNERDetector`
- NER v3 adapter 계약 문서화
- NER v3 label mapping: `NAME -> PERSON_NAME`, `ADDRESS -> ADDRESS_FULL`, `ORG -> ORGANIZATION`
- `SCHOOL`/`HOSPITAL`/`ADDRESS_UNIT`는 dictionary/resolver 후속 처리 책임으로 분리
- threshold 기반 calibration metadata 입력 계약
- real NER activation은 pipeline/evaluation 안정화 이후 gated task로 분리

#### 완료 기준

- real NER 없이 pipeline end-to-end 실행 가능
- NER output도 boundary/context/resolver/policy를 통과
- NER v3 직접 output entity가 PERSON_NAME, ADDRESS_FULL, ORGANIZATION으로 제한됨

### M7 legacy. evaluation harness

최신 로드맵에서는 evaluation harness가 M10이며, M7은 `Policy router and masker`이다. 이 절은 초기 계획 번호를 보존한 legacy note로만 사용한다.

기간: 1~2주

#### 작업

- hard cases JSONL
- metric runner
- ablation runner
- release gate check
- residual risk report template

#### 완료 기준

- regex only부터 full single-turn pipeline까지 ablation 가능
- entity별 FP/FN 리포트 출력
- raw PII logging zero 테스트 통과

## 6. 주요 의사결정

| 항목 | v0.2 결정 |
|---|---|
| detector score 결합 | 동일/겹침 span은 max score 사용, source list 보존 |
| Bayesian 결합 | detector independence 가정이 약하므로 제외 |
| context window | 후보 기준 ±5 어절, 같은 문장으로 제한 |
| field label | 같은 문장 내 label 허용, ±5 어절 제한 완화 |
| co-occurrence | 같은 문장 내부 PII만 인정 |
| context judge | LLM 호출 없음, deterministic rule 기반 |
| composite | 단일 입력 텍스트 내부만 처리 |
| L0 활용 방식 | 기존 L0 코드는 reference로 사용하고 v0.2 package에서는 offset-aware variant engine으로 재구현 |
| Kiwi 활용 방식 | optional reference/benchmark로만 사용, 원문 재작성 결과는 기본 normalized text로 사용하지 않음 |
| NER v3 활용 방식 | M5/M6에서는 adapter 계약만 확정하고 real activation은 M9/M10 gate에서 수행 |
| NER source priority | source 순서만으로 결정하지 않고 entity priority와 resolver rule로 overlap 처리 |
| P0 | threshold 낮게 두고 recall 우선, 일부 entity는 block |
| 로그 | raw PII 저장 금지 |

## 7. 리스크 및 완화책

| 리스크 | 설명 | 완화책 |
|---|---|---|
| score calibration 부재 | regex/dict/NER score 비교 어려움 | scoring spec와 calibration harness 도입 |
| boundary error | 조사·호칭 포함 마스킹 | boundary corrector와 boundary accuracy metric |
| dictionary FP | 하늘/사랑/가을 등 일반명사 오탐 | negative context와 context judge |
| 계좌번호 FP | 숫자열 과탐 | 은행명/계좌 label 없으면 낮은 score 유지 |
| raw PII log | guardrail 자체가 PII 저장소가 될 위험 | audit logger schema 제한 및 테스트 |
| 고급 정규화 offset 오류 | 초성·야민정음·로마자 복원은 입력과 출력 길이가 달라 raw span 복원이 어려움 | advanced normalization은 탐지용 variant로 분리하고 raw span mapping 실패 시 candidate reject |
| L0 직접 이식 위험 | 기존 L0는 normalize 결과 중심이며 v0.2 raw offset/public safety 계약을 직접 만족하지 않음 | L0 로직은 reference로만 사용하고 직접 import 금지 |
| NER 산출물 접근 불일치 | NER 명세의 local artifact 경로가 workspace에 없을 수 있음 | HF Hub 또는 별도 artifact 전달 전까지 mock/disabled NER path 유지 |
| NER serving latency 미확정 | v3 모델은 production candidate지만 serving 방식은 별도 측정 필요 | deterministic CPU path와 real NER latency를 분리 보고 |

## 8. Release Gate

v0.2 release 후보는 다음 조건을 만족해야 한다.

| Gate | 목표 |
|---|---:|
| P0 structured recall | 99% 이상 |
| PHONE/EMAIL recall | 98% 이상 |
| Korean variant attack recall | L0-derived hard cases에서 목표치 별도 산정 |
| josa boundary accuracy | 95% 이상 |
| raw PII logging | 0건 |
| p95 latency | SLA 내, 기본 목표 100ms 이하 CPU path |
| real NER latency | serving 방식별 별도 report |
| ablation report | 작성 완료 |
| entity별 FP/FN report | 작성 완료 |

## 9. 향후 v1 후보

v0.2 안정화 이후 다음을 v1 후보로 둔다.

- RAG document/context sanitization
- multi-turn fragment ledger
- subject tracker
- Redis TTL session store
- LLM judge selective fallback
- human review queue
- domain-specific NER adapter
- reversible tokenization interface
