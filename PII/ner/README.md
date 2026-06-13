# 한국어 PII NER 모듈

> **NER Owner**: 민우 / **Pipeline Owner**: 팀원
> **버전**: v0.1 (W1 D1, 2026-05-08)

## 디렉토리

```
ner/
├── README.md                      # 이 문서
├── schema.py                      # PIISpan contract (Pipeline Owner와 공유)
├── mock_ner.py                    # W3 통합용 mock (실제 모델 결정 전)
├── mapping_rules.py               # NER label → PII 매핑 + ADDRESS 후처리 + boundary correction
├── ner_wrapper.py                 # (예정) 실제 모델 wrapper, A-primary 결정 후 작성
├── train_fallback.py              # (예정) C-fallback 학습 스크립트
├── data/                          # 데이터 작업 (W2)
├── scripts/
│   └── check_checkpoints.py       # W1 D3 — 3개 후보 sanity check
├── reports/
│   ├── label_guide_v1.md          # ★ 라벨링 일관성 (모든 데이터 기반)
│   ├── checkpoint_report.json     # W1 금 산출물
│   ├── checkpoint_comparison.md   # W2 금 산출물 (성능 비교)
│   └── error_analysis.md          # W5 금 산출물 (50건 분석)
└── tests/                         # pytest
```

## W1~W6 마일스톤

| 주차 | 주요 deliverable |
|---|---|
| **W1** | 라벨 가이드 v1, schema.py, mock_ner.py, checkpoint sanity check |
| **W2** | KLUE-NER 재라벨링, Faker-ko 합성, A-primary 결정 (화 EOD) |
| **W3** | ner_wrapper.py 실제 모델 교체, mapping_rules 보강, ADDRESS 후처리 |
| **W4** | 외부 평가 (KLUE-NER test + KoJailFuzz unseen 6종) + 50건 오류분석 |
| **W5** | Pipeline Owner와 Span Ledger 통합, latency 측정 |
| **W6** | 최종 표·그림·발표 |

## 5개 핵심 deliverable

1. **`reports/checkpoint_report.json`** — 3개 후보 라벨/라이선스/F1 (W1 금)
2. **`mock_ner.py` + `schema.py`** — Pipeline Owner W3 통합 의존성 해소 (W2 화)
3. **`reports/checkpoint_comparison.md`** — A-primary 후보 성능 비교 (W2 금)
4. **`train_fallback.py`** — C-fallback 학습 (조건부, W3+)
5. **`reports/error_analysis.md`** — 50건 오류분석 (W5 금)

## A-primary 후보 + 라이선스 ⚠️

| 모델 | 라이선스 | 캡스톤 | GitHub |
|---|---|---|---|
| `monologg/koelectra-base-v3-naver-ner` | CC-BY-NC-SA 4.0 (비영리) | OK | ❌ 위반 |
| `KPF/KPF-bert-ner` | 확인 필요 | 조건부 | 조건부 |
| `Leo97/KoELECTRA-small-v3-modu-ner` | 모두의 말뭉치 약관 | OK | ❌ 재배포 제약 |
| (fallback) `klue/bert-base` + KLUE-NER | CC-BY-SA | OK | OK |

→ **모두 회색이면 KLUE-NER 자체 학습 (C-fallback)이 가장 깨끗.**

## C-fallback 발동 기준

W2 화요일 EOD 기준, 3개 후보 중 최고 macro-F1:
- **≥ 0.75** → A-primary 확정
- **0.60 ~ 0.75** → ADDRESS 후처리 1일 시도 후 재측정
- **< 0.60** → 즉시 C-fallback 발동

## C-fallback 학습 (encoder freeze 1ep + unfreeze 2ep)

```python
# Phase 1: head only, LR 5e-4
for n, p in model.named_parameters():
    if not n.startswith("classifier"):
        p.requires_grad = False
TrainingArguments(num_train_epochs=1, learning_rate=5e-4, ...)

# Phase 2: full unfreeze, LR 2e-5
for p in model.parameters():
    p.requires_grad = True
TrainingArguments(num_train_epochs=2, learning_rate=2e-5, warmup_ratio=0.1, ...)
```

## 사용 예시

```bash
# 1. 체크포인트 sanity check
cd c:/My-AI-Security-Project/PII/ner/scripts
python check_checkpoints.py --model all

# 2. mock NER 데모
cd c:/My-AI-Security-Project/PII/ner
python mock_ner.py

# 3. 매핑 룰 + 후처리 데모
python mapping_rules.py
```

## 평가 메트릭

- **span-exact macro-F1** (1순위, 모델 선택 기준)
- **Tier 1 recall ≥ 99%** (gate, 미달 시 모델 탈락)
- **Tier 4 FPR < 5%** (gate)
- **외부 평가셋**: KLUE-NER test + KoJailFuzz unseen 6종 (W6 1회만)

## 함정 & 예방책

| 함정 | 예방책 |
|---|---|
| `klue/roberta-base` 단독 사용 (NER head 없음) | 위 라이선스 표 참조, base만 쓰면 학습 필수 |
| BIO subword alignment | `word_ids()` 첫 subword만 라벨, 나머지 -100 |
| Boundary correction 책임 혼선 | NAME suffix 분리는 NER (mapping_rules.py), Span Ledger merge는 Pipeline |
| Faker-ko 과신 | 본문 숫자는 KLUE-NER test + KoJailFuzz unseen만 |
| W6 외부셋 폭발 | W4에 외부 1차 완료, W5 룰 수정 |
