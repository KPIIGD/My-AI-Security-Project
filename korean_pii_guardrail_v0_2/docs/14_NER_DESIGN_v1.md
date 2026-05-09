# NER 설계 명세서 v1

| | |
|---|---|
| **NER Owner** | 김민우 |
| **Version** | v1 (계획안) |
| **Date** | 2026-05-09 |
| **Status** | 학습 직전 (GPU 환경 결정 보류 중) |
| **대상 통합** | `korean_pii_guardrail_v0_2` (M5/M6/M9/M10) |
| **참조** | `docs/06_INTERFACE_SPEC.md`, `docs/03_SCORING_POLICY_SPEC.md`, `configs/scoring.yaml`, `configs/josa_rules.yaml`, `data/eval/hard_cases_v0.jsonl` |

---

## 0. 현재 진행 상태

- **학습 데이터 준비 완료**
  - KLUE-NER train 21,008 + Faker-ko 합성 10,000 = 31,008 (8:1:1 셔플 분할)
  - 외부 평가용 KLUE-NER validation 5,000 (`klue_test`)
  - 라벨 분포 (train): NAME 15,944 / ORG 9,870 / ADDRESS 8,338
- **데이터 품질 보정 완료**
  - Faker `ko_KR.address()` 의 시·도+시·군·구 무작위 조합 + 인명 포함 괄호 부속 텍스트 (예: "충청남도 삼척시 압구정6거리 221-98 (상현이이면)") 발견
  - `cosmosfarm/korea-administrative-district` v20241209 정적 JSON으로 교체 → 228개 실 (시·도, 시·군·구) 페어 + 자체 도로명 합성기
  - 재생성 후 ADDR span 3,832개 전수 검증: 괄호 0건 / 시·도 prefix 누락 0건 / 인명 침입 0건
- **Pre-flight 통과**: tokenizer alignment, transformers 4.51.3 호환성, BIO 라벨 정렬 확인
- **유일한 blocker**: GPU 환경 (Colab Free vs Vast.ai T4)

---

## 1. Base model + tokenizer

| 항목 | 값 |
|---|---|
| Base model | `klue/bert-base` (BERT, 110M params, MLM-only pretrain) |
| Phase 2 ablation 후보 | `klue/roberta-base` (NER head 없어 from-scratch fine-tune) |
| Tokenizer | `BertTokenizerFast` (`AutoTokenizer.from_pretrained("klue/bert-base")`) |
| 토큰화 방식 | wordpiece. 한국어 char-level 분할 우세 → token offset ↔ char offset 1:1 |
| 라이선스 | KLUE CC-BY-SA → fine-tuned 가중치 재배포 가능 |

**왜 klue/bert-base?**
- KLUE-NER train 데이터와 동일 코퍼스 family로 distribution shift 최소
- Phase 6 alphagyuu (TF weights) / mncai 의 라이선스 모호함을 회피
- 상용 배포 가능한 깨끗한 라이선스 체인

---

## 2. 출력 방식

**BIO token classification** (BIOES 아님).

- HuggingFace `AutoModelForTokenClassification` 표준
- 모델 forward → token별 7-way logits
- 후처리에서 `B-X ... I-X*` → contiguous span 으로 변환

span classification(전체 sentence를 동시에 후보 span 추출하는 방식) 아님. 이유: KLUE-NER 데이터가 BIO 포맷이고, span classification은 학습 비용·복잡도·효과 모두 BIO 대비 marginal.

---

## 3. 모델 label 목록

7개 라벨 (BIO, NER 학습용):

```
O           (id=0)
B-NAME      (id=1)
I-NAME      (id=2)
B-ADDRESS   (id=3)
I-ADDRESS   (id=4)
B-ORG       (id=5)
I-ORG       (id=6)
```

**의도적 minimal 설계**: NAME / ADDRESS / ORG 3 entity만 NER이 학습. 나머지 30+ 종 entity (RRN, PHONE, EMAIL, CREDIT_CARD, RELATION, MEDICAL_RECORD_NO 등) 은 regex + dict 가 담당.

**이유**:
1. 한국어 NER 학습 데이터 확보 비용 (라벨러 부족)
2. 정형 entity (RRN/PHONE/CARD) 는 regex가 NER보다 정확하고 빠름
3. NER이 모든 entity를 다루면 FP rate 폭증 (Phase 6의 alphagyuu any-detection 100% 사례)
4. v0.2 architecture가 detector를 source별로 분리하도록 설계됨 (regex / dict / ner / context)

---

## 4. label → EntityType 매핑표

```
NER label   →  v0.2 EntityType
─────────────────────────────────
NAME        →  PERSON_NAME
ADDRESS     →  ADDRESS_FULL    (ADDRESS_UNIT 은 후처리 dict 분기)
ORG         →  ORGANIZATION    (SCHOOL / HOSPITAL 은 후처리 dict reclassify)
```

**세분 entity 처리**:
- `SCHOOL` / `HOSPITAL` / `BUSINESS_REG_NO` 등 ORGANIZATION 하위 분류는 NER이 emit 안 함
- NER이 `ORGANIZATION` 으로 일괄 emit → dict (organization_suffix / school_suffix / hospital_suffix) 가 reclassify 결정
- `GuardrailOptions.allow_experimental_entities=True` 일 때만 NER 이 ORG 세분화 시도 옵션 가능

**ADDRESS 처리**:
- NER 은 `ADDRESS_FULL` 만 (e.g. "서울시 강남구 테헤란로 123")
- `ADDRESS_UNIT` (e.g. "101동 1203호") 은 dict + regex 가 분리 인식
- 복합 ADDRESS ("서울 강남구 역삼동 101동 1203호") 는 span resolver 가 통합

---

## 5. 모델 출력 offset이 token offset인지 char offset인지

| 단계 | offset 종류 |
|---|---|
| 모델 raw 출력 | **subword token offset** (BERT wordpiece) |
| 학습 입력 | char list (한글 1자 = 1 word, `is_split_into_words=True`) |
| 결과적으로 | token offset ↔ **char offset** 사실상 1:1 (한국어 wordpiece가 1 char 안 쪼개짐) |

**확인**: 학습 데이터의 `tokens` 필드는 char 리스트, `labels` 도 char 단위 7-way id. tokenizer pre-tokenized input 처리 시 word_ids() 가 입력 char index 를 그대로 가리킴.

---

## 6. raw text → offset 복원 방법

```
[1] raw_text → char_list = list(raw_text)
[2] enc = tokenizer(char_list, is_split_into_words=True,
                    return_offsets_mapping=True,
                    truncation=True, max_length=256)
[3] word_ids = enc.word_ids()  # 각 subword 가 가리키는 char index
[4] forward → logits → argmax → token labels
[5] BIO → contiguous span 결합 (B-X 시작, I-X 누적, O 또는 다른 B 만나면 종료)
[6] span 의 (token_start, token_end) → word_ids 통해 (char_start, char_end)
[7] PIISpan(start=char_start, end=char_end, text=raw_text[char_start:char_end], ...)
```

**v0.2 계약 보장**: `span.text == raw_text[span.start:span.end]` 100% 성립.

이유: char list 가 raw_text 의 lossless 표현 (한글 1자 = 1 element). word_ids 가 결정론적 매핑이라 round-trip 손실 없음.

---

## 7. 조사 / 어미 / 호칭 모델 포함 여부

**제외**. 학습 데이터에 NAME / ADDRESS / ORG **본체만 라벨**.

| 입력 | NER 출력 |
|---|---|
| "홍길동이 신청했습니다" | `홍길동` (3자, NAME) |
| "김민수에게 연락하세요" | `김민수` (3자, NAME) |
| "서울시 강남구 테헤란로 123에 거주합니다" | `서울시 강남구 테헤란로 123` (ADDRESS) |

**근거**:
- KLUE-NER PS/LC/OG 라벨이 본체만 잡음
- Faker 합성 데이터도 entity_text 자체만 라벨링 (`labels[start:end]` 만 BIO)
- 조사 (`이/가/을/를/에/에게/...`) 는 boundary corrector 가 분리 책임
- v0.2 `josa_rules.yaml` 의 22개 조사 + 4개 honorific + 7개 ending 규칙과 호환

**예외 처리**: 모델이 학습 노이즈로 조사를 span에 포함하는 edge case 발생 시 boundary corrector 가 후처리 분리.

---

## 8. confidence / logit 가용성

가능. 두 가지 score 옵션 제공:

```python
logits = model(input_ids).logits          # (batch, seq_len, 7)
probs = softmax(logits, dim=-1)           # token별 7-way 확률

# Span score 계산 옵션
# A. mean pooling (권장)
span_score = mean([probs[t, entity_id] for t in span_tokens])

# B. first-token max
span_score = max(probs[span.first_token, entity_ids])
```

**선택**: A (mean pooling) 권장. B 는 짧은 span 에서 over-confident 경향.

**reason_codes** (v0.2 계약상 ≥1 개 필수):
```
ner.argmax
ner.softmax_mean
ner.span_length_<n>
ner.calibrated_v1   # calibration 적용 시
```

---

## 9. threshold / calibration 계획

| 단계 | 방식 | 산출물 |
|---|---|---|
| 1차 (학습 직후) | uniform threshold 0.85 | — |
| 2차 (calibration) | val set 기준 PERSON_NAME 에 **temperature scaling** 또는 **isotonic regression** | `calibration.json` |
| 3차 (FP tuning) | hard_cases_v0 의 negative + normal_kr 10k 에서 FP@threshold 측정 → per-entity threshold 미세조정 | `calibration.json` 갱신 |

**v0.2 `scoring.yaml` 호환성**:
- `score_bands`: high_confidence 0.90 / mask_or_review 0.75 / context_judge 0.55
- NER raw score 를 `[0,1]` normalize → 그대로 score band 에 투입
- low-confidence span (score < 0.55) 도 `candidate` 로 emit → dict / context booster 가 보강할 기회 제공

**calibration metadata 포맷**:
```json
{
  "method": "temperature_scaling",
  "temperature": 1.23,
  "fitted_on_split": "val_v1",
  "fitted_at": "2026-05-XX",
  "per_entity_threshold": {
    "PERSON_NAME": 0.85,
    "ADDRESS_FULL": 0.80,
    "ORGANIZATION": 0.75
  },
  "fp_rate_at_threshold": {
    "PERSON_NAME": 0.0046,
    "ADDRESS_FULL": 0.002,
    "ORGANIZATION": 0.008
  }
}
```

---

## 10. max sequence length + 긴 문장 처리

| 항목 | 값 |
|---|---|
| 학습 max_length | 128 char |
| inference max_length | 256 char (또는 필요 시 512) |
| 긴 문서 처리 | sliding window stride 128, overlap score mean pooling, span IoU ≥ 0.5 merge |
| 한 문장 > max_length | 어절 경계 split (조사 끝 / 마침표 기준) |

**Sliding window 의사코드**:
```python
windows = [text[i:i+256] for i in range(0, len(text), 128)]
all_spans = []
for w_start, window in enumerate(windows):
    spans = ner_inference(window)
    # window 내 span 의 char offset 을 raw_text offset 으로 보정
    for s in spans:
        s.start += w_start
        s.end += w_start
    all_spans.extend(spans)

# overlap span merge: same entity_type + IoU ≥ 0.5 → score mean
merged = merge_overlapping_spans(all_spans, iou_threshold=0.5)
```

---

## 11. CPU / GPU inference + 예상 latency

| 환경 | 예상 latency (per request, 256 char) | 비고 |
|---|---|---|
| CPU PyTorch native FP32 | 100~200 ms | klue/bert-base 110M, single core |
| CPU ONNX FP32 | 40~80 ms | aegis 패턴 (37ms) 참조 |
| GPU T4 PyTorch FP16 | 10~20 ms | batch 16에서 ~2ms/sample |

**Phase 6 비교 기준**:
- alphagyuu: 221 ms (PyTorch CPU, TF weights→pt 변환 오버헤드)
- mncai: 178 ms (PyTorch CPU)
- aegis: 37 ms (ONNX CPU, 가장 빠름)

**우리 모델 목표**: PyTorch CPU 에서 mncai 수준 (150 ms ±), ONNX 변환 시 aegis 수준 (50 ms ±). ONNX export 산출물 함께 제공 예정.

---

## 12. unknown label 처리

- 모델 출력은 7 라벨 (`O, B/I-NAME, B/I-ADDRESS, B/I-ORG`) 만
- pipeline taxonomy 에 매핑 없는 entity 는 **emit 안 함**
- ORG → SCHOOL / HOSPITAL / BUSINESS_REG_NO reclassification 은 dict 후처리 책임
- `allow_experimental_entities=True` 시에도 NER 단독으로 새 entity 만들지 않음 (혼란 방지)
- 모델 confidence 0.5 미만 ORG 는 candidate 에서 제외 (FP 방지 안전장치)

---

## 13. hard negative 처리 계획

### 학습 데이터 augment

| Hard negative 유형 | 처리 |
|---|---|
| **하늘 / 사랑 / 별** (일반명사) | KLUE-NER 일부 포함, **+ Faker hard-neg 1k augment 추가 예정** ("오늘 하늘이 맑네요" 같은 패턴 합성) |
| **예시 전화번호** (010-0000-0000) | NER scope 밖 (regex 책임). 우리 NER 은 PHONE 학습 안 함 |
| **대표번호** (1588-XXXX) | 동일 (regex + `context_penalties.public_phone_context` 처리) |
| **API 키** (sk-test-...) | NER scope 밖 |

### Calibration / FP 측정

- `hard_cases_v0.jsonl` 의 NAME-negative 케이스 (`case-0008` 하늘 weather, `case-0014` 사랑 abstract) 를 calibration set 에 흡수
- Phase 6 의 `normal_kr_10k.json` (PII 미포함 한국어 1만 건) 에서 FP rate 측정
- **FP target**: alphagyuu 0.46% (incomplete 8000건 측정 결과) 수준

### Faker hard negative augment 예시 패턴

```
"오늘 {weather}이 {adj}네요"        → label: []
"{abstract_noun}은 중요한 가치입니다"  → label: []
"고객센터 대표번호는 {public_num}입니다" → label: []
"예시 전화번호는 010-0000-0000"       → label: []
```

`weather` ∈ [하늘, 별, 햇빛, 바다, 구름], `abstract_noun` ∈ [사랑, 우정, 평화, 자유, 행복] 등. 약 1,000 건 augment.

---

## 14. 제출 산출물

```
ner/
├── models/pii_ner_v1/
│   ├── pytorch_model.bin
│   ├── config.json
│   ├── tokenizer.json
│   ├── special_tokens_map.json
│   ├── vocab.txt
│   ├── label_map.json              # {id↔label, label↔EntityType}
│   ├── train_config.yaml           # base, lr, epoch, batch, seed, data version
│   ├── calibration.json            # method, temperature, per-entity threshold
│   └── onnx/model.onnx             # (옵션) ONNX export
├── ner_wrapper.py                  # BaseNERDetector Protocol 구현
├── eval/
│   ├── ner_eval_klue_test.json     # KLUE-NER validation 5k (외부)
│   ├── ner_eval_our_test.json      # 우리 8:1:1 test 3.1k
│   ├── ner_eval_hard_cases.json    # v0.2 hard_cases_v0 결과
│   └── ner_eval_normal_kr.json     # FP @ normal_kr 10k (Phase 6 데이터셋 재사용)
└── MODEL_CARD.md                   # 라이선스, 데이터 출처, 한계
```

### `label_map.json` 예시

```json
{
  "id_to_label": {
    "0": "O",
    "1": "B-NAME", "2": "I-NAME",
    "3": "B-ADDRESS", "4": "I-ADDRESS",
    "5": "B-ORG", "6": "I-ORG"
  },
  "label_to_entity_type": {
    "NAME": "PERSON_NAME",
    "ADDRESS": "ADDRESS_FULL",
    "ORG": "ORGANIZATION"
  },
  "version": "v1",
  "trained_on": "klue-ner-v1.1 + faker-ko-v1 (real admin divisions)"
}
```

### `ner_wrapper.py` 인터페이스 (v0.2 `BaseNERDetector` 준수)

```python
from pii_guardrail.ner.base import BaseNERDetector
from pii_guardrail.schema import GuardrailRequest, PIISpan
from pii_guardrail.enums import EntityType, RiskLevel

class FinetunedKoreanNERDetector:  # implements BaseNERDetector
    detector_id = "ner.finetuned.klue-bert-v1"

    def __init__(self, model_path: str, calibration_path: str):
        self.model = AutoModelForTokenClassification.from_pretrained(model_path)
        self.tokenizer = AutoTokenizer.from_pretrained(model_path)
        with open(model_path + "/label_map.json") as f:
            self.label_map = json.load(f)
        with open(calibration_path) as f:
            self.calibration = json.load(f)

    def detect(self, raw_text, preprocessed, request) -> list[PIISpan]:
        # 1. char_list = list(raw_text)
        # 2. tokenize + forward + softmax
        # 3. apply temperature scaling (calibration)
        # 4. argmax → BIO → contiguous span
        # 5. word_ids → char offset → PIISpan
        # 6. per-entity threshold filter
        # 7. return [candidate spans]
        ...
```

---

## 결정 / 양유상 답변 받을 사항

1. **ADDRESS_UNIT 분기 책임**: NER 이 ADDRESS_FULL 만 출력하고 dict 가 UNIT 분리 — 이대로 진행 OK?
2. **ORG 세분화 책임**: SCHOOL / HOSPITAL 을 dict 후처리로 reclassify — v0.2 architecture 와 어긋나지 않나?
3. **Phase 6 baseline 통합 평가**: 우리 NER + L0 vs alphagyuu + L0 같은 framework 으로 비교 결과를 같이 낼지?
4. **제출 시점**: GPU 결정 → 학습 ~2시간 → calibration → wrapper 작성. 빠르면 1주 내. M5 일정에 맞는지?
5. **NER score 가 resolver 에서 어떻게 반영되어야 하나** (M6) — 너의 결정 기다림. 현재 가정: regex > validator > NER > dictionary > context 우선순위.

---

## 변경 이력

| Version | Date | 작성자 | 변경 |
|---|---|---|---|
| v1 | 2026-05-09 | 김민우 | 최초 작성 (학습 직전) |
