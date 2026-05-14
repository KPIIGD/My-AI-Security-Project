# 평가 계획서 — Korean PII Guardrail v0.2

Version: v0.2-single-turn  
Date: 2026-05-09

## 1. 평가 목적

v0.2 평가는 단일 텍스트 기준 개인정보 탐지 및 마스킹 pipeline의 안전성, 정확도, 한국어 경계 처리 품질, 운영 적합성을 검증한다.

RAG와 멀티턴은 평가 범위에서 제외한다.

## 2. 평가 범위

### 포함

- 구조형 PII 탐지
- 이름/주소/조직 등 의미형 PII 탐지
- 한국어 조사·호칭·어미 boundary correction
- context scoring
- single-turn composite risk
- span resolver
- masking policy
- raw PII logging zero
- latency

### 제외

- session leakage rate
- multi-turn fragmented PII recall
- RAG document leakage
- subject-level leakage across turns
- retrieval context sanitization

## 3. 평가 데이터셋 구성

| Bucket | 목표 수량 | 목적 |
|---|---:|---|
| Structured PII-heavy | 300 | RRN, PHONE, EMAIL, CARD, ACCOUNT, SECRET |
| Name/address-heavy | 500 | 조사 결합, 짧은 이름, 주소 상세도, 조직/학교 |
| Single-turn composite | 200 | 같은 문장 내 이름+전화, 이름+주소, ID+연락처 |
| Adversarial | 200 | zero-width, 띄어쓰기 오류, 한글 숫자, 혼합 표기 |
| Hard negative | 200 | 하늘/사랑/가을, 대표번호, 예시/테스트, 상호명 |
| 총합 | 1,400 | v0.2 gold set 목표 |

## 4. Gold label schema

각 샘플은 JSONL 한 줄로 저장한다.

```json
{
  "id": "case-0001",
  "text": "홍길동이 010-1234-5678로 연락했습니다.",
  "expected_masked_text": "[PERSON_1]이 [PHONE_1]로 연락했습니다.",
  "labels": [
    {
      "start": 0,
      "end": 3,
      "entity_type": "PERSON_NAME",
      "risk_level": "P1",
      "suffix": "이"
    },
    {
      "start": 5,
      "end": 18,
      "entity_type": "PHONE_MOBILE",
      "risk_level": "P1",
      "suffix": "로"
    }
  ],
  "tags": ["boundary", "person_phone", "single_turn_composite"]
}
```

## 5. 라벨링 원칙

### 5.1 Offset

- start/end는 raw text 기준 character offset이다.
- suffix는 PII 본체 span에서 제외한다.
- `text[start:end]`가 PII 본체여야 한다.

### 5.2 Boundary

| 원문 | Label span | suffix |
|---|---|---|
| `홍길동이` | `홍길동` | `이` |
| `김민수에게` | `김민수` | `에게` |
| `010-1234-5678로` | `010-1234-5678` | `로` |
| `test@example.com입니다` | `test@example.com` | `입니다` |

### 5.3 Hard negative

이름 후보처럼 보이지만 문맥상 일반명사인 경우 label을 달지 않는다.

예:

```text
오늘 하늘이 맑네요.
```

- `하늘`에 PERSON label 없음.

### 5.4 Composite

단일 문장 내부에서 조합 위험이 있는 경우 `tags`에 `single_turn_composite`를 추가한다.

## 6. 평가 지표

### 6.1 Span metrics

| Metric | 설명 |
|---|---|
| Entity precision/recall/F1 | entity type 기준 |
| Exact span F1 | start/end/entity 정확히 일치 |
| Partial span F1 | overlap 허용 |
| Token-level F1 | character/token overlap |

### 6.2 Korean-specific metrics

| Metric | 설명 |
|---|---|
| Josa boundary accuracy | PII 본체와 suffix 분리 정확도 |
| Honorific boundary accuracy | `님`, `씨`, 직함 처리 |
| Name ambiguity FP rate | 하늘/사랑/가을 등 오탐률 |
| Address granularity accuracy | 주소 상세도 risk 판정 |

### 6.3 Risk/policy metrics

| Metric | 설명 |
|---|---|
| High-risk recall | P0/P1 누락률 관리 |
| False block rate | 1,000 text당 block 오탐 |
| Over-masking rate | label 없는 span 마스킹 |
| Under-masking rate | label 있는 span 누락 |
| Policy accuracy | output target별 method 일치율 |
| Single-turn composite recall | 같은 입력 내 조합 위험 탐지율 |

### 6.4 Operational metrics

| Metric | 설명 |
|---|---|
| deterministic p50/p95/p99 latency | regex/dictionary/boundary/resolver CPU path 처리 지연 |
| real NER p50/p95/p99 latency | NER v3 adapter 포함 처리 지연, deterministic path와 별도 집계 |
| raw PII logging count | 0이어야 함 |
| invalid offset count | detector 품질 |
| context override ratio | context로 action 변경된 비율 |
| boundary corrected ratio | boundary corrector 개입 비율 |

## 7. Ablation plan

| Group | 구성 | 검증 가설 |
|---|---|---|
| A | regex only | 구조형 baseline |
| B | A + validator | 구조형 FP 감소 |
| C | B + dictionary | 주소/조직/이름 후보 recall 증가 |
| D | C + boundary correction | 한국어 조사 결합 exact span F1 증가 |
| E1 | D + mock NER | NER interface와 downstream resolver/policy 연결 검증 |
| E2 | D + real v3 NER | 자유형 이름/주소/조직 recall 증가 및 NER FP 확인 |
| F | E1 또는 E2 + context scorer | 중의적 이름/일반명사 FP 감소 및 composite recall 증가 |
| G | F + policy router/masker | LLM Gateway target별 masking/hash/block 품질 검증 |

초기 슬라이드의 session monitor ablation은 v0.2에서 제거한다.

Real NER v3 평가는 local model artifact가 있거나 HuggingFace Hub에서 모델을 받을 수 있을 때만 실행한다. 모델 산출물 접근이 불가능한 환경에서는 E2를 skipped로 기록하고 E1 mock NER 결과를 기본 integration evidence로 사용한다.

## 8. Release criteria

| Gate | 목표 |
|---|---:|
| P0 structured recall | >= 99% |
| PHONE/EMAIL recall | >= 98% |
| Josa boundary accuracy | >= 95% |
| Exact span F1 | baseline 대비 개선 확인 |
| Name ambiguity FP rate | hard negative set에서 관리 가능 수준 |
| Raw PII logging count | 0 |
| Invalid offset count | 0 |
| p95 latency | 100ms 이하, NER 제외 CPU path 기준 |
| Real NER latency | 별도 측정, CPU/GPU/ONNX 배포 방식별 report |
| Ablation report | 작성 완료 |

## 9. Error analysis template

각 false positive/false negative는 다음 항목으로 기록한다.

```json
{
  "case_id": "case-0123",
  "error_type": "FN",
  "entity_type": "PERSON_NAME",
  "text_hash": "hmac-sha256:...",
  "reason": "name_with_title_boundary_missed",
  "layer_suspected": "boundary_corrector",
  "suggested_fix": "add title suffix pattern",
  "raw_value_logged": false
}
```

## 10. 리포트 산출물

| Report | 파일명 예시 |
|---|---|
| Entity metrics | `reports/entity_metrics_v0_2.json` |
| Boundary metrics | `reports/boundary_metrics_v0_2.json` |
| Ablation report | `reports/ablation_v0_2.md` |
| Failure analysis | `reports/failure_cases_v0_2.jsonl` |
| Release gate | `reports/release_gate_v0_2.json` |
| Audit safety report | `reports/audit_safety_v0_2.json` |

## 11. 평가 실행 예시

```bash
python scripts/run_eval.py \
  --config-dir configs \
  --dataset data/eval/hard_cases_v0.jsonl \
  --output reports/eval_v0_2.json

python scripts/run_ablation.py \
  --config-dir configs \
  --dataset data/eval/hard_cases_v0.jsonl \
  --output reports/ablation_v0_2.md
```
