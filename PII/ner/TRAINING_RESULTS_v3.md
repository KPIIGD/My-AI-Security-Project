# PII NER v3 — 학습 결과 보고서 (Production)

| | |
|---|---|
| **NER Owner** | 김민우 |
| **Date** | 2026-05-12 |
| **Status** | ★ **PRODUCTION** |
| **Final model** | `models/pii_ner_v3/final/` (klue/roberta-large, 1.3GB) |
| **이전 보고서** | [TRAINING_RESULTS_v1.md](TRAINING_RESULTS_v1.md) |

---

## 1. 학습 이력 요약

| Run | Base | Data | Setup | Our test | KLUE val | 비고 |
|---:|---|---:|---|---:|---:|---|
| 1 | bert-base | 31k | 2ep | 0.776 | 0.630 | baseline |
| 2 | bert-base | 31k | 5ep, batch32 | 0.798 | 0.669 | |
| 3 | roberta-base | 31k | 5ep | 0.830 | 0.697 | |
| **4 (v1)** | **roberta-large** | **31k** | **5ep** | **0.865** | **0.764** | v1 final |
| 5 (v2) | roberta-large | 139k | LWLR + ext-val-stop | 0.708 | 0.664 | ❌ 실패 |
| **6 (v3)** | **roberta-large** | **34k** | **v1 setup + augment** | **0.878** | **0.766** | ★ Production |

---

## 2. v2 실패 분석 (중요 lesson)

**시도**: AI 토론 결과 따라 Naver NER 90k + WikiAnn 20k 통합 (총 139k)
**예상**: KLUE val +0.05~0.08
**실제**: KLUE val **-0.100** (0.764 → 0.664)

### 원인 진단
1. **Naver NER 압도적 비중 (81%)** → 모델이 Naver 분포에 fit
2. **어절 단위 라벨 → char-level 변환 시 노이즈**
   - "이병헌이" 같은 명사+조사 결합 어절이 NAME 전체로 라벨됨
   - 조사 부분까지 NAME으로 학습 → 잘못된 학습 신호
3. **WikiAnn 라벨 quality 의심** — 다국어 머신 매핑 라벨
4. **Layer-wise LR decay 0.9** — Phase 1+2 freeze/unfreeze 패턴 대신 단순 학습으로 변경되어 v1 success 패턴 깨짐

### 메타 lesson
- AI 토론은 가설 brainstorming용, **데이터 quality는 직접 검증 필수**
- "더 많은 데이터" ≠ "더 좋은 모델"
- 검증된 setup 함부로 바꾸지 말 것 (Layer-wise LR + FGM 등 동시 변경 → 변수 격리 어려움)

---

## 3. v3 설계 (Conservative)

v2 실패 후 conservative pivot:
- ❌ Naver NER 제거 (어절 라벨 노이즈)
- ❌ WikiAnn 제거 (라벨 quality 의심)
- ❌ Layer-wise LR decay 제거 (v1 setup 복귀)
- ❌ FGM 제거 (fp16 호환 + marginal gain)
- ✅ **v1 setup 그대로 유지**
- ✅ Faker conjunctive composite 2k 추가 (v1 한계 보완)
- ✅ Hard negatives 1k 추가 (FP 방지)

### 데이터 구성

| Source | Count | License |
|---|---:|---|
| KLUE-NER train | 21,008 | CC-BY-SA |
| Faker baseline | 10,000 | 자체 합성 |
| Faker composite (v3 신규) | 2,000 | 자체 합성 |
| Hard negatives (v3 신규) | 1,000 | 자체 합성 |
| **TOTAL train pool** | **34,008** | |

KLUE val 5,000 → 외부 평가 (학습 미포함)

### Composite 템플릿 예시
```python
"저는 {name}이고 {address}에 거주합니다."
"저는 {name}이며 {org} 소속입니다."
"{name}과 {name2}가 {address}에서 만났습니다."
"{name}/{name2} 공동저자, 소속 {org}."
```

### Hard negative 패턴
```python
"오늘 {weather}이 {adj}네요."        # weather ∈ [하늘, 별, 햇빛, ...]
"{abstract}은 중요한 가치입니다."     # abstract ∈ [사랑, 우정, 평화, ...]
"고객센터 대표번호는 1588-{4d}입니다."
"예시 전화번호는 010-0000-0000입니다."
```

---

## 4. 학습 결과 (v3 최종)

### epoch별 곡선 (val set)
| Epoch | macro-F1 | micro-F1 |
|---:|---:|---:|
| Phase 1 (freeze) | 0.281 | 0.312 |
| Phase 2 ep1 | 0.817 | 0.828 |
| Phase 2 ep2 | 0.856 | 0.864 |
| Phase 2 ep3 | 0.861 | 0.868 |
| Phase 2 ep4 | 0.870 | 0.876 |
| **Phase 2 ep5** | **0.872** | **0.880** |

### 최종 평가
| Eval set | macro-F1 | micro-F1 | size |
|---|---:|---:|---:|
| Internal val | 0.872 | 0.880 | 3,401 |
| **Internal test** | **0.878** | **0.887** | 3,401 |
| **KLUE-NER val (외부)** | **0.766** | **0.792** | 5,000 |

### v1 vs v3 비교
| Metric | v1 | v3 | Δ |
|---|---:|---:|---:|
| Internal val | 0.873 | 0.872 | -0.001 |
| Internal test | 0.865 | **0.878** | **+0.013** |
| KLUE val (외부) | 0.764 | **0.766** | +0.002 |

v3는 v1과 거의 동일하지만:
- **Internal test +1.3%p** (composite 케이스 학습됨)
- **Conjunctive 패턴 모델 자체가 처리** (wrapper heuristic 의존 ↓)

---

## 5. Wrapper smoke test (v3, 10 cases)

```
✅ "안녕하세요, 저는 홍길동이고 서울시 강남구 테헤란로 152에 거주합니다. 삼성전자 소속입니다."
   → NAME=홍길동 (1.000) | ADDR=서울시 강남구 테헤란로 152 (1.000) | ORG=삼성전자 (1.000)
   ★ v1에서는 wrapper heuristic 필요했음 (score 0.900 감점). v3는 모델 자체가 분리.

✅ "홍길동씨가 신청했습니다."                                   → NAME=홍길동
✅ "저는 박정희이고 부산광역시 해운대구에 거주하며 LG전자 소속" → NAME + ADDR + ORG
✅ "담당자 김민수 과장님께 연락 바랍니다."                     → NAME=김민수
✅ "오늘 하늘이 맑네요."                                       → (no spans) ★ hard neg
✅ "사랑은 중요한 가치입니다."                                 → (no spans) ★ hard neg
✅ "환자 김연아님 (서울대학교 소속)이 진료 받으셨습니다."       → NAME + ORG
✅ "고객명: 이정순, 가입일자는 어제입니다."                    → NAME=이정순
✅ "예시 전화번호는 010-0000-0000입니다."                      → (no spans) ★ NER scope 밖
✅ "오정웅이랑 LG전자에 다닙니다."                             → NAME + ORG (이랑 conjunctive)
```

10/10 정상. **모든 conjunctive 케이스 모델 자체가 분리 → wrapper heuristic split 비활성화 가능**.

---

## 6. 비용·시간 누계 (3회 학습 세션 합산)

| 항목 | 비용 | 시간 |
|---|---:|---:|
| v1 학습 4회 (BERT base/RoBERTa base/large) | $0.44 | 4 hours |
| v2 학습 1회 (실패) | $0.31 | 1 hour |
| v3 학습 1회 (Production) | $0.17 | 30 min |
| **총합** | **$0.92** | ~5.5 hours |

Vast.ai credit 잔액 $8.61.

---

## 7. 제출 산출물 (v3)

```
models/pii_ner_v3/final/
├── model.safetensors                  (1.3 GB, klue/roberta-large fine-tuned)
├── config.json
├── tokenizer.json, vocab.txt, ...
├── label_map.json                     (id↔label, label↔EntityType)
├── calibration.json                   (per-entity threshold)
└── eval/
    ├── test_results.json              (our test, macro-F1 0.878)
    └── klue_test_results.json         (KLUE-NER val, macro-F1 0.766)

PII/ner/
├── ner_wrapper.py                     (BaseNERDetector Protocol)
├── TRAINING_RESULTS_v1.md             (v1 보고)
└── TRAINING_RESULTS_v3.md             (이 문서)
```

`ner_wrapper.py` 의 heuristic split 로직은 v3에서도 유지 (안전망). 다만 v3 모델은 raw output 자체가 정확해서 heuristic이 거의 트리거 안 됨.

---

## 8. v0.2 통합 진입점

v0.2 `BaseNERDetector` Protocol 그대로 준수. v0.2 wrapper 통합 시:

```python
from ner_wrapper import FinetunedKoreanNERDetector

class FinetunedKoreanNERAdapter:
    detector_id = "ner.finetuned.klue-roberta-large-v3"

    def __init__(self):
        self._impl = FinetunedKoreanNERDetector(
            model_path="models/pii_ner_v3/final",
            calibration_path="models/pii_ner_v3/final/calibration.json",
        )

    def detect(self, raw_text, preprocessed, request) -> list[PIISpan]:
        candidates = self._impl.detect(raw_text)
        return [PIISpan(...) for c in candidates]  # v0.2 dataclass 변환
```

---

## 9. 결론 — Production 상태

**v3 NER 모델이 production 사용 준비 완료**:
- ✅ macro-F1 0.878 (internal) / 0.766 (KLUE 외부)
- ✅ Conjunctive 패턴 자체 처리
- ✅ Hard negative robustness (하늘/사랑/대표번호/예시번호)
- ✅ Wrapper PIISpan contract 준수
- ✅ 라이선스 깨끗 (KLUE CC-BY-SA + 자체 합성)
- ✅ 학습 재현 가능 ($0.17, 30분)

다음 단계: 양유상의 v0.2 deterministic core (regex/dict/boundary/resolver/masker) 작업 진행 후 W-017에서 NER wrapper 통합 → 단일 가드레일 99% 목표 달성.

---

## 변경 이력
| Version | Date | 변경 |
|---|---|---|
| v1 | 2026-05-11 | 초기 production (klue/roberta-large, 31k) |
| v2 | 2026-05-12 | 실패 — Naver NER + WikiAnn 통합 후 -10%p |
| **v3** | **2026-05-12** | **Production — v1 setup + composite/hard_neg augment** |
| v3-onnx | 2026-05-18 | ONNX FP32 (opset 18) + INT8 dynamic quantization 산출물 추가 |

---

## 10. ONNX export + INT8 quantization — W-017 (2026-05-18 추가)

### 10.1 측정 환경
- **CPU**: Intel Core Ultra 7 258V (8 cores / 8 threads, 2.2 GHz base)
- **RAM**: 32 GB
- **OS**: Windows 11 Home 10.0.26200
- **Python**: 3.12 / torch 2.11.0 (CPU) / transformers 4.51.3 / onnx 1.21.0 / onnxruntime 1.26.0 / optimum 2.1.0
- **입력**: 256 chars 한국어 adversarial payload → 122 subword tokens

### 10.2 산출물

| 파일 | 크기 | 용도 |
|---|---:|---|
| `models/pii_ner_v3/final/model.safetensors` | 1.3 GB | PyTorch FP32 (학습 산출물) |
| `models/pii_ner_v3/onnx/model.onnx` | 1.3 GB | ONNX FP32 (opset 18) |
| `models/pii_ner_v3/onnx_int8/model.onnx` | **322 MB** | ONNX INT8 dynamic quantized (**4x 작아짐**) |

### 10.3 Latency 실측 (warmup 30 + measure 100 iters)

| Backend | p50 (ms) | p95 (ms) | p99 (ms) | mean±std (ms) | Speedup |
|---|---:|---:|---:|---:|---:|
| PyTorch CPU FP32 | 546.9 | 810.0 | 940.4 | 590.5 ± 113.0 | 1.0x |
| ONNX CPU FP32 | 374.8 | 458.6 | 497.2 | 383.4 ± 37.5 | **1.46x** |
| **ONNX CPU INT8** | **135.5** | **177.2** | **196.8** | **140.4 ± 17.7** | **4.04x** |

### 10.4 INT8 vs FP32 정확도 (test 200 샘플)

- **전체 token-level agreement: 99.747%** (5,135 / 5,148 토큰 일치)
- 발산이 1개 이상인 문장: 12 / 200 (6.0%)
- 평균 발산 토큰/문장: 1.08개 (boundary tokens 위주)

Per-label agreement (예측 라벨별):

| Label | Agreement | Total |
|---|---:|---:|
| I-NAME | **100.00%** | 134 |
| O | 99.86% | 4,388 |
| I-ADDRESS | 99.26% | 270 |
| B-NAME | 99.22% | 129 |
| B-ORG | 98.73% | 79 |
| B-ADDRESS | 98.18% | 55 |
| I-ORG | 97.85% | 93 |

### 10.5 결론

- **INT8 quantization으로 4x speedup + 99.7% agreement 유지** → production trade-off 양호
- PyTorch 절대값(546.9ms)이 본 spec docs/14 §11 v2 예상치(150~250ms)보다 ~2.5배 느림. 측정 CPU(노트북 저전력)가 server-class 대비 느린 것으로 추정. 상대 speedup은 환경 독립적
- INT8 발산 13건 모두 1~2 tokens, 주로 boundary 위치 — entity-level F1 영향은 1~2%p 예상
- 다음 단계: GPU 환경 latency 측정 + per-entity threshold calibration + M10 evaluation_harness 통합 후 entity-level F1 직접 측정
