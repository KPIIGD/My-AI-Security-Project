# PII NER v1 — 학습 결과 보고서

| | |
|---|---|
| **NER Owner** | 김민우 |
| **Date** | 2026-05-11 |
| **Base 문서** | `korean_pii_guardrail_v0_2/docs/14_NER_DESIGN_v1.md` (PR #3) |
| **Final model** | `models/pii_ner_v1/final/` (klue/roberta-large, 1.3GB) |

---

## 1. 학습 환경

| 항목 | 값 |
|---|---|
| Provider | Vast.ai |
| GPU | Tesla V100-SXM2-16GB |
| 인스턴스 비용 | $0.135/h × ~2h ≈ $0.27 |
| 전체 세션 비용 | **$0.44** (4회 학습) |
| PyTorch | 2.4.1 + CUDA 12.4 |
| transformers | 4.51.3 |

---

## 2. 학습 실행 4회 비교

| Run | Base | Batch | Phase 2 ep | Our test F1 | KLUE-NER F1 | Notes |
|---:|---|---:|---:|---:|---:|---|
| 1 | klue/bert-base | 16 | 2 | 0.776 | 0.630 | 기본 |
| 2 | klue/bert-base | 32 | 5 | 0.798 | 0.669 | batch ↑ + epoch ↑ |
| 3 | klue/roberta-base | 32 | 5 | 0.830 | 0.697 | RoBERTa 전환 |
| **4** | **klue/roberta-large** | **16** | **5** | **0.865** | **0.764** | **최종 채택** |

### Run 4 epoch 별 곡선 (Phase 2)

```
ep1: 0.808 → ep2: 0.850 → ep3: 0.862 → ep4: 0.872 → ep5: 0.873
```

ep4→ep5 +0.001 = **plateau 확인** (epoch 더 늘려도 향상 미미).

---

## 3. 최종 모델 (Run 4) 평가 결과

| 평가 set | macro-F1 | micro-F1 | size |
|---|---:|---:|---:|
| Val | 0.873 | 0.880 | 3,101 |
| **Our test** | **0.865** | **0.872** | 3,101 |
| **KLUE-NER val (외부)** | **0.764** | **0.790** | 5,000 |

**해석**:
- v1 NER 설계 명세 목표 macro-F1 0.85+ 달성 (our test)
- KLUE 외부 평가 0.764는 도메인 transfer 한계지만 baseline (Leo97 후처리 0.665) 대비 +0.10
- 학습 데이터 distribution (Faker + KLUE) vs KLUE-only 평가 set의 차이 일부 반영

---

## 4. Wrapper smoke test (10 케이스)

```
✅ "홍길동씨가 신청했습니다."                                    → NAME=홍길동
✅ "서울시 강남구 테헤란로 152에 거주합니다."                       → ADDRESS=서울시 강남구 테헤란로 152
✅ "삼성전자에 입사했습니다."                                     → ORG=삼성전자
✅ "담당자 김민수 과장님께 연락 바랍니다."                         → NAME=김민수
✅ "오늘 하늘이 맑네요."                                          → (no spans) ★ hard neg
✅ "사랑은 중요한 가치입니다."                                    → (no spans) ★ hard neg
✅ "저는 박정희이고 부산광역시 해운대구에 거주하며 LG전자 소속..."   → NAME + ADDRESS + ORG (분리 OK)
✅ "환자 김연아님 (서울대학교 소속)이 진료..."                     → NAME=김연아, ORG=서울대학교
✅ "고객명: 이정순, 가입일자는 어제입니다."                       → NAME=이정순
✅ "예시 전화번호는 010-0000-0000입니다."                        → (no spans) ★ PHONE = NER scope 밖
```

10/10 정상. 단 **wrapper postprocess heuristic** 동원 (아래 v1 한계 참조).

---

## 5. v1 한계 발견

### 5.1 Conjunctive 패턴 — NAME이 ADDRESS span에 빨려들어감

**증상**:
```
INPUT: "안녕하세요, 저는 홍길동이고 서울시 강남구 테헤란로 152에 거주합니다."

모델 raw token-level 출력:
  홍 = B-ADDRESS (prob 1.000)
  길 = I-ADDRESS (1.000)
  동 = I-ADDRESS (1.000)
  이 = I-ADDRESS (0.998)
  고 = I-ADDRESS (1.000)
  서 = I-ADDRESS (1.000)
  울 = I-ADDRESS (1.000)
  ...
```

**원인**: Faker 합성 데이터 템플릿에 NAME + conjunctive 조사("이고", "이며", "하고" 등) + ADDRESS/ORG 인접 패턴이 부재. 모델이 그런 케이스를 학습 안 함.

**v1 단기 fix (`ner_wrapper.py` heuristic)**:
- ADDRESS span 시작이 시·도 prefix 가 아니면 → 내부에서 시·도 위치 찾아 split
- 앞부분이 2-10 char + 조사 strip 가능 → NAME 으로 별도 emit
- NAME score 는 raw score × 0.9 (heuristic 감점)
- reason_code: `ner.heuristic_split_v1`

**검증**: smoke test 케이스 7번 (`"저는 박정희이고 부산광역시 해운대구..."`) 정상 분리 확인.

### 5.2 기타

- KLUE-NER 외부 0.764 vs 내부 0.865 격차 → Faker 합성 distribution effect
- ADDRESS_UNIT (예: "101동 1203호") NER 학습 안 됨 — dict 담당 (설계대로)
- SCHOOL/HOSPITAL 세분 안 됨 — ORG 단일 라벨로 일괄 emit (설계대로)

---

## 6. v2 Plan

### 6.1 데이터 augment (예상 +0.03~0.05 KLUE F1)

Faker 템플릿에 conjunctive composite 패턴 추가:

```python
COMPOSITE_TEMPLATES = [
    "저는 {name}이고 {address}에 거주합니다.",
    "{name}이며 {org} 소속입니다.",
    "{name}과 {name2}가 {address}에서 만났습니다.",
    "환자 {name}({age}세)는 {address}에 거주하며 {org}에서 근무합니다.",
    "{name}님은 {org}에서 일하고 {address}에 사십니다.",
    # negative: name처럼 보이는 일반명사
    "오늘 {weather}이 {adj}네요.",  # weather ∈ [하늘, 별, 햇빛]
    "{abstract}은 중요한 가치입니다.",  # abstract ∈ [사랑, 우정, 평화]
    "고객센터 대표번호는 1588-{4d}입니다.",
]
```

`hard_negative` 약 1,000 건 + composite 2,000 건 augment 예상.

### 6.2 학습 hyperparameter 조정

- klue/roberta-large epoch 5 → 8 (plateau에서 +0.005 정도 추가 가능)
- weight decay 0.01 추가
- label smoothing 0.1

### 6.3 KLUE-NER 외 추가 외부 평가셋

- AIHub 한국어 NER (있으면 비교)
- KoJailFuzz unseen 6종 (W6 외부 평가)

### 6.4 비용·시간

- 데이터 augment 코드: 1 시간 (로컬)
- 재학습: ~20 분 (Vast V100, +$0.05)
- 결과 분석 + wrapper 재테스트: 30 분

**v2 ETA**: 1-2 일 작업.

---

## 7. 제출 산출물 (`models/pii_ner_v1/final/`)

```
models/pii_ner_v1/final/
├── model.safetensors              (1.3 GB, klue/roberta-large fine-tuned)
├── config.json
├── tokenizer.json + vocab.txt + special_tokens_map.json + tokenizer_config.json
├── label_map.json                 (id↔label, label↔EntityType)
├── calibration.json               (uniform threshold v0, per-entity)
├── MODEL_CARD.md                  (라이선스·데이터·한계)
└── eval/
    ├── test_results.json          (our test, macro-F1 0.865)
    └── klue_test_results.json     (KLUE-NER val, macro-F1 0.764)
```

`ner_wrapper.py` 는 패키지 별도 보관 (`PII/ner/ner_wrapper.py`).

---

## 8. v0.2 통합 인터페이스

v0.2 `BaseNERDetector` Protocol 준수:
- `detector_id = "ner.finetuned.klue-bert-v1"` (실제로는 roberta-large)
- `detect(raw_text, preprocessed, request) -> list[PIISpan-like dict]`
- `span.text == raw_text[span.start:span.end]` 계약 100% 보장
- `reason_codes ≥ 1`, `score [0,1]`, `action=candidate`

`finetuned_wrapper.py` placeholder 교체용 코드:

```python
from ner_wrapper import FinetunedKoreanNERDetector
from pii_guardrail.enums import EntityType, RiskLevel
from pii_guardrail.schema import PIISpan

class FinetunedKoreanNERAdapter:
    detector_id = "ner.finetuned.klue-roberta-large-v1"

    def __init__(self, model_path, calibration_path):
        self._impl = FinetunedKoreanNERDetector(model_path, calibration_path)

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

## 변경 이력

| Version | Date | 작성자 | 변경 |
|---|---|---|---|
| v1 (results) | 2026-05-11 | 김민우 | 학습 4회 결과 + wrapper smoke test + v2 plan |
