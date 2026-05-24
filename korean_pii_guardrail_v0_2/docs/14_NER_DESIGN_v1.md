# NER 설계 명세서

| | |
|---|---|
| **NER Owner** | 김민우 |
| **Document version** | v3 (guardrail release gate feedback 반영) |
| **Initial date** | 2026-05-09 |
| **Last updated** | 2026-05-24 |
| **Status** | ★ **Production candidate** (모델 v3 채택, guardrail 평가 기반 NER backlog 있음) |
| **Final model** | `models/pii_ner_v3/final/` (klue/roberta-large) |
| **HuggingFace Hub** | [`vmaca123/korean-pii-ner-v3`](https://huggingface.co/vmaca123/korean-pii-ner-v3) |
| **대상 통합** | `korean_pii_guardrail_v0_2` (M5/M6/M9/M10) |
| **참조** | `docs/06_INTERFACE_SPEC.md`, `docs/03_SCORING_POLICY_SPEC.md`, `configs/scoring.yaml`, `configs/josa_rules.yaml`, `data/eval/hard_cases_v0.jsonl` |
| **결과 보고** | `TRAINING_RESULTS_v1.md`, `TRAINING_RESULTS_v3.md` (로컬 학습 산출물; PR 본문 댓글 참조) |

> **변경 요약 (v1 계획안 → v3 문서)**
> 초기 v1 설계서(2026-05-09 작성)는 학습 *직전* 계획. 이후 4회 모델 비교 → v3 production candidate 채택. 2026-05-24에는 guardrail release gate 결과를 반영해 `PERSON_NAME` recall/precision, `ADDRESS` granularity, score calibration 후속 과제를 명시했다.

---

## 0. 현재 진행 상태 — Production candidate

- ✅ **학습 6회 완료**: bert-base(2/5ep) → roberta-base → roberta-large(v1) → v2(실패) → **v3(production)**
- ✅ **v3 production candidate 모델**: macro-F1 **0.878 (internal)** / **0.766 (KLUE 외부)**
- ✅ **Conjunctive 패턴 모델 자체 처리** (v1 한계 보완 완료)
- ✅ **Wrapper smoke test 10/10 통과** (초기 hard negative 포함)
- ✅ **데이터 quality 보정**: cosmosfarm 행정구역 + Faker conjunctive composite + hard_neg augment
- ✅ **비용**: Vast.ai $0.92 누계 (6 runs)

### 0.1 Guardrail release gate 피드백

2026-05-24 기준 `reports/release_gate_v0_2.json`에서 release gate는 통과했다. 다만 real NER가 포함된 guardrail 통합 평가에서는 다음 후속 과제가 남았다.

| 항목 | 최신 관찰 | NER 후속 과제 |
|---|---|---|
| `PERSON_NAME` | precision 0.6755, recall 0.8697, F1 0.7604 | 소유격/연락처/계좌 composite 문맥의 이름 recall 보강 |
| hard negative `PERSON_NAME` | candidate FP 500건, 최종 action은 대부분 `pass` | 예시 키워드, 추상명사, 일반명사 hard negative calibration |
| `ADDRESS` | pipeline 매핑은 `ADDRESS_FULL`, 일부 이름 fixture가 `ADDRESS_FULL`로 오분류 | `ADDRESS` granularity 기준과 `NAME`/`ADDRESS` confidence 분리 |
| score calibration | temperature 1.0, score 1.000 쏠림 가능성 | entity별 ECE, threshold sweep, calibration set 보강 |

따라서 이 문서의 "production" 표현은 모델 artifact와 wrapper가 통합 가능한 수준이라는 뜻이며, guardrail 전체 품질 관점에서는 `docs/17_NER_BACKLOG_FROM_GUARDRAIL_EVAL.md`의 NER backlog를 후속으로 처리해야 한다.

---

## 1. Base model + tokenizer

| 항목 | 값 |
|---|---|
| **Final base model** | **`klue/roberta-large`** (335M params) |
| 비교 ablation | klue/bert-base (Run 1/2), klue/roberta-base (Run 3), **klue/roberta-large (Run 4/6 = v1/v3)** |
| Tokenizer | `RobertaTokenizerFast` (`AutoTokenizer.from_pretrained("klue/roberta-large")`) |
| 토큰화 방식 | BPE-based, 한국어 char-level 분할 우세 → token offset ↔ char offset 1:1 |
| 라이선스 | KLUE CC-BY-SA → fine-tuned 가중치 재배포 가능 |

**선택 근거** (4회 비교):
| Run | Base | Our test | KLUE val |
|---:|---|---:|---:|
| 1 | bert-base | 0.776 | 0.630 |
| 2 | bert-base 5ep | 0.798 | 0.669 |
| 3 | roberta-base | 0.830 | 0.697 |
| **4 (v1)** | **roberta-large** | **0.865** | **0.764** |
| **6 (v3)** | **roberta-large + augment** | **0.878** | **0.766** |

---

## 2. 출력 방식

**BIO token classification** (BIOES 아님).

- HuggingFace `AutoModelForTokenClassification` 표준
- 모델 forward → token별 7-way logits
- 후처리에서 `B-X ... I-X*` → contiguous span 으로 변환

span classification 아님 — KLUE-NER이 BIO 포맷이고 BIO가 marginal에서도 충분 정확.

---

## 3. 모델 label 목록

7개 라벨 (BIO):

```
O           (id=0)
B-NAME      (id=1)
I-NAME      (id=2)
B-ADDRESS   (id=3)
I-ADDRESS   (id=4)
B-ORG       (id=5)
I-ORG       (id=6)
```

**의도적 minimal 설계**: NAME / ADDRESS / ORG 3 entity만 NER이 학습. 나머지 30+ 종 (RRN, PHONE, EMAIL, CREDIT_CARD, RELATION, MEDICAL_RECORD_NO 등) 은 regex + dict 가 담당.

---

## 4. label → EntityType 매핑표

```
NER label   →  v0.2 EntityType
─────────────────────────────────
NAME        →  PERSON_NAME
ADDRESS     →  ADDRESS_FULL    (ADDRESS_UNIT 은 후처리 dict 분기)
ORG         →  ORGANIZATION    (SCHOOL / HOSPITAL 은 후처리 dict reclassify)
```

`label_map.json` 산출물: `models/pii_ner_v3/final/label_map.json` (HF Hub 패키지 포함):
```json
{
  "id_to_label": { "0": "O", "1": "B-NAME", "2": "I-NAME", "3": "B-ADDRESS",
                   "4": "I-ADDRESS", "5": "B-ORG", "6": "I-ORG" },
  "label_to_entity_type": { "NAME": "PERSON_NAME", "ADDRESS": "ADDRESS_FULL",
                            "ORG": "ORGANIZATION" },
  "version": "v3", "base_model": "klue/roberta-large"
}
```

---

## 5. 모델 출력 offset이 token offset인지 char offset인지

| 단계 | offset 종류 |
|---|---|
| 모델 raw 출력 | **subword token offset** (RoBERTa BPE) |
| 학습 입력 | char list (한글 1자 = 1 word, `is_split_into_words=True`) |
| 결과적으로 | token offset ↔ **char offset** 사실상 1:1 (한국어 BPE 가 1 char 안 쪼개짐) |

**실측 검증** (smoke test): `span.text == raw_text[start:end]` 100% 성립.

---

## 6. raw text → offset 복원 방법

```
[1] raw_text → char_list = list(raw_text)
[2] enc = tokenizer(char_list, is_split_into_words=True,
                    truncation=True, max_length=256)
[3] word_ids = enc.word_ids()  # 각 subword 가 가리키는 char index
[4] forward → logits → argmax → token labels
[5] BIO → contiguous span 결합 (B-X 시작, I-X 누적, O 또는 다른 B 만나면 종료)
[6] span 의 (token_start, token_end) → word_ids 통해 (char_start, char_end)
[7] PIISpan(start=char_start, end=char_end, text=raw_text[char_start:char_end], ...)
```

**v0.2 계약 보장**: `span.text == raw_text[span.start:span.end]` 100% 성립. 구현체: `ner_wrapper.py` `_infer_single_window` + `_bio_to_spans`.

---

## 7. 조사 / 어미 / 호칭 모델 포함 여부

**제외**. 학습 데이터에 NAME / ADDRESS / ORG **본체만 라벨**.

### v3 핵심 개선 — Conjunctive 패턴 모델 자체 처리

v1 학습 시 발견된 한계: `"저는 홍길동이고 서울시 강남구..."` → 모델이 "홍길동이고 서울시...152" 전체를 ADDRESS로 묶음 (wrapper heuristic split 필요)

**v3 해결**: Faker composite augment 2k 학습 데이터에 추가
```
"저는 {name}이고 {address}에 거주합니다."
"저는 {name}이며 {org} 소속입니다."
"{name}과 {name2}가 {address}에서 만났습니다."
"{name}이랑 {org}에 다닙니다."
```

**v3 실측**:
| 입력 | 결과 |
|---|---|
| "저는 홍길동이고 서울시 강남구..." | NAME=홍길동 (1.000) + ADDR=서울시 강남구... (1.000) |
| "박정희이고 부산광역시 해운대구에 거주하며 LG전자" | NAME + ADDR + ORG 모두 분리 |
| "오정웅이랑 LG전자에 다닙니다" | NAME + ORG 모두 분리 |

**Wrapper heuristic split 의존 사실상 제거됨** (안전망으로 코드 유지).

---

## 8. confidence / logit 가용성

가능. 두 가지 score 옵션:

```python
logits = model(input_ids).logits          # (batch, seq_len, 7)
probs = softmax(logits, dim=-1)

# A. mean pooling (권장, 현재 wrapper 구현)
span_score = mean([probs[t, entity_id] for t in span_tokens])

# B. first-token max
span_score = max(probs[span.first_token, entity_ids])
```

**reason_codes** (v0.2 계약 ≥1 필수):
```
ner.argmax
ner.softmax_mean
ner.length_<n>
ner.heuristic_split_v1   # (v3에서는 거의 트리거 안 됨)
```

---

## 9. threshold / calibration 계획

### v3 현재
- `per_entity_threshold` 적용 (`calibration.json`):
  - PERSON_NAME: 0.85
  - ADDRESS_FULL: 0.80
  - ORGANIZATION: 0.75
- temperature = 1.0 (uncalibrated)
- v3 raw output score 1.000 대부분 (모델 self-confidence 매우 높음)

### v2 calibration plan (TODO, 양유상 M6 결정 후)
| 단계 | 방식 |
|---|---|
| 1 | val set에서 temperature scaling (Platt 또는 isotonic) |
| 2 | hard_cases_v0 + normal_kr 10k 에서 FP@threshold 측정 |
| 3 | per-entity threshold 미세 조정 |

**v0.2 scoring.yaml 호환**:
- `score_bands`: high_confidence 0.90 / safety_mask 0.75 / context_judge 0.55
- NER raw score → 그대로 `[0,1]` band 투입
- low-conf span 도 candidate 로 emit → dict/context 보강 기회

---

## 10. max sequence length + 긴 문장 처리

| 항목 | 값 |
|---|---|
| 학습 max_length | **128** char |
| inference max_length | 256 char (필요 시 512) |
| 긴 문서 처리 | sliding window stride 128, overlap score mean pooling, span IoU≥0.5 merge |
| 한 문장 > max_length | 어절 경계 split (조사 끝 / 마침표 기준) |

구현: `ner_wrapper.py` `_sliding_window_detect` + `_merge_overlapping`.

---

## 11. CPU / GPU inference + 실측 latency

### 학습 시 측정 (RTX 3090 24GB)
- batch 16 fp16: 학습 5.5 it/s × 1701 step/epoch
- eval 1140 samples/sec

### 추론 latency (계획 — production 시 측정 필요)
| 환경 | 예상 latency (256 char) | 비고 |
|---|---|---|
| CPU PyTorch native FP32 | 150~250 ms | klue/roberta-large 335M |
| CPU ONNX FP32 | 60~120 ms | aegis 패턴 (37ms) 참조 |
| GPU T4/3090 FP16 | 15~30 ms | batch 16에서 ~2ms/sample |

**Phase 6 비교 기준**:
- alphagyuu (TF→pt): 221 ms
- mncai (PyTorch CPU): 178 ms
- aegis (ONNX CPU): 37 ms (가장 빠름)

→ ONNX export 산출물 함께 제공 예정 (TODO).

---

## 12. unknown label 처리

- 모델 출력은 7 라벨만 → pipeline taxonomy 매핑 없는 entity 는 **emit 안 함**
- ORG → SCHOOL / HOSPITAL / BUSINESS_REG_NO reclassification 은 dict 후처리 책임
- `allow_experimental_entities=True` 시에도 NER 단독으로 새 entity 만들지 않음 (혼란 방지)
- 모델 confidence 0.5 미만 ORG 는 candidate 에서 제외 (FP 방지)

---

## 13. hard negative 처리 — v3 초기 완료 및 추가 보강 필요

### 학습 데이터에 통합 완료 (v3)
| Hard negative 유형 | 처리 | v3 학습 데이터 |
|---|---|---|
| 하늘 / 사랑 / 별 (일반명사) | 학습 데이터에 1,000건 augment | ✅ `gen_hard_neg` |
| 예시 전화번호 010-0000-0000 | NER scope 밖 (regex 책임) | ✅ scope 정의 |
| 대표번호 1588-XXXX | 동일 | ✅ scope 정의 |
| API 키 sk-test-... | NER scope 밖 | ✅ scope 정의 |

### v3 hard_negative 템플릿 예시
```python
"오늘 {weather}이 {adj}네요."          # weather ∈ [하늘, 별, 햇빛, ...]
"{abstract}은 중요한 가치입니다."       # abstract ∈ [사랑, 우정, 평화, ...]
"고객센터 대표번호는 1588-{4d}입니다."
"예시 전화번호는 010-0000-0000입니다."
```

### 실측 결과 (wrapper smoke test)
```
✅ "오늘 하늘이 맑네요."        → (no spans)
✅ "사랑은 중요한 가치입니다."  → (no spans)
✅ "예시 전화번호는 010-0000-0000입니다." → (no spans)
```

---

## 14. 제출 산출물 — v3 완성

HF Hub 배포: [`vmaca123/korean-pii-ner-v3`](https://huggingface.co/vmaca123/korean-pii-ner-v3)

```
PII/ner/
├── models/pii_ner_v3/final/
│   ├── model.safetensors              (1.3 GB, klue/roberta-large fine-tuned)
│   ├── config.json
│   ├── tokenizer.json + vocab.txt + special_tokens_map.json + tokenizer_config.json
│   ├── label_map.json                 (id↔label, label↔EntityType)
│   ├── calibration.json               (per-entity threshold)
│   └── eval/
│       ├── test_results.json          (our test, macro-F1 0.878)
│       └── klue_test_results.json     (KLUE-NER val, macro-F1 0.766)
├── ner_wrapper.py                     (BaseNERDetector Protocol)
├── TRAINING_RESULTS_v1.md             (v1 결과)
└── TRAINING_RESULTS_v3.md             (v3 production 결과 ★)
```

### v0.2 통합 인터페이스 예시

```python
from ner_wrapper import FinetunedKoreanNERDetector
from pii_guardrail.enums import EntityType, RiskLevel
from pii_guardrail.schema import PIISpan

class FinetunedKoreanNERAdapter:  # implements BaseNERDetector
    detector_id = "ner.finetuned.klue-roberta-large-v3"

    def __init__(self):
        self._impl = FinetunedKoreanNERDetector(
            model_path="models/pii_ner_v3/final",
            calibration_path="models/pii_ner_v3/final/calibration.json",
        )

    def detect(self, raw_text, preprocessed, request) -> list[PIISpan]:
        candidates = self._impl.detect(raw_text)
        return [
            PIISpan(
                start=c["start"], end=c["end"], text=c["text"],
                entity_type=EntityType(c["entity_type"]),
                score=c["score"],
                sources=c["sources"],
                risk_level=RiskLevel(c["risk_level"]),
                detector_ids=c["detector_ids"],
                reason_codes=c["reason_codes"],
            )
            for c in candidates
        ]
```

---

## 결정 / 양유상 답변 받을 사항 (5건)

1. **ADDRESS_UNIT 분기 책임**: NER은 ADDRESS 라벨만 emit하고 pipeline은 기본적으로 ADDRESS_FULL에 매핑한다. 다만 guardrail 평가 기준에서는 ADDRESS_UNIT granularity 기준과 score hint 제공 가능성을 재검토해야 한다.
2. **ORG 세분화 책임**: SCHOOL / HOSPITAL 을 dict 후처리로 reclassify — v0.2 architecture 와 어긋나지 않나?
3. **Phase 6 baseline 통합 평가**: 우리 NER + L0 vs alphagyuu + L0 같은 framework 으로 비교 결과 같이 낼지?
4. **제출 시점**: v3 production candidate 모델 + wrapper는 완성되었고 real NER release gate에 연결됐다. 다음 제출 단위는 NER calibration과 backlog 보강이다.
5. **M6 NER score resolver 반영 방식** — 현재 가정: regex > validator > NER > dictionary > context 우선순위.

---

## v1 한계 → v3 해결 요약

| 항목 | v1 (Run 4, 0.865/0.764) | v3 (Run 6, 0.878/0.766) |
|---|---|---|
| Base model | klue/roberta-large | klue/roberta-large (동일) |
| 학습 데이터 | KLUE 21k + Faker 10k = 31k | + Faker composite 2k + hard_neg 1k = 34k |
| Conjunctive 패턴 | wrapper heuristic split 필요 | **모델 자체 처리** |
| Internal test | 0.865 | **0.878 (+0.013)** |
| KLUE val (외부) | 0.764 | **0.766 (+0.002)** |
| Hard negative robustness | 부분 (wrapper 의존) | **학습 데이터에 통합** |

---

## v2 실패 기록 (Naver NER + WikiAnn 통합)

v1과 v3 사이 시도된 Run 5:
- Naver NER 90k + WikiAnn 20k 통합 → 139k 학습 데이터
- 결과: KLUE val **0.664 (v1 대비 -0.100)**
- 원인: 어절 단위 라벨의 char-level 노이즈 + multi-source distribution shift
- 결론: v1 setup 그대로 + 데이터 augment만 추가하는 conservative pivot이 효과적

자세한 내용은 `TRAINING_RESULTS_v3.md` §2 참조.

---

## 변경 이력

| Version | Date | 작성자 | 변경 |
|---|---|---|---|
| v1 (계획안) | 2026-05-09 | 김민우 | 학습 직전 14개 항목 답변 |
| **v2 (실측 반영)** | **2026-05-13** | 김민우 | 학습 6회 완료, v3 production 채택, 모든 항목 실측값 + 검증 결과로 업데이트 |
| **v3 (guardrail feedback)** | **2026-05-24** | Codex | release gate 통합 평가 기준의 PERSON_NAME, ADDRESS granularity, calibration backlog 반영 |
