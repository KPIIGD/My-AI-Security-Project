---
license: cc-by-sa-4.0
language:
- ko
task_categories:
- token-classification
task_ids:
- named-entity-recognition
size_categories:
- 10K<n<100K
tags:
- pii
- privacy
- korean
- ner
- klue
- guardrail
pretty_name: Korean PII NER v3
---

# Korean PII NER v3

한국어 개인정보(PII) 탐지용 Named Entity Recognition 학습 데이터셋. 3가지 entity type — **NAME / ADDRESS / ORG** — 을 7-way BIO 라벨로 학습한다. 학부 정보보안 캡스톤 프로젝트(한국어 PII Guardrail v0.2)의 NER 컴포넌트 학습에 사용된 데이터셋의 production release 버전.

연관 모델: [vmaca123/korean-pii-ner-v3](https://huggingface.co/vmaca123/korean-pii-ner-v3) (klue/roberta-large fine-tuned, KLUE val macro-F1 = 0.766)

## 데이터셋 구성

| Source | 양 | 설명 |
|---|---:|---|
| KLUE-NER train | 21,008 | KAIST KLUE 벤치마크 한국어 NER train split |
| Faker-ko baseline | 10,000 | `faker` 라이브러리 `ko_KR` locale로 합성한 가짜 한국 PII |
| Composite augmentation | 2,000 | Conjunctive 패턴 (`"저는 {name}이고 {address}에 거주합니다"`) 자체 합성 |
| Hard negative | 1,000 | 헷갈리기 쉬운 일반명사 (`"오늘 하늘이 맑네요"` 등) — 라벨 없음 |

총 **34,008 examples**를 `train` / `val` / `test` split에 분배. 추가로 **5,000 examples**의 `klue_test` split을 외부 평가용으로 별도 보관.

### Splits

| Split | Examples | 용도 |
|---|---:|---|
| `train` | 27,206 | 학습 |
| `val` | 3,401 | hyperparameter tuning + early stopping |
| `test` | 3,401 | 내부 평가 |
| `klue_test` | 5,000 | 외부 검증 (KLUE-NER official test) |

## Label schema (7-way BIO)

| ID | Label |
|---:|---|
| 0 | O |
| 1 | B-NAME |
| 2 | I-NAME |
| 3 | B-ADDRESS |
| 4 | I-ADDRESS |
| 5 | B-ORG |
| 6 | I-ORG |

**NAME**: 사람 이름 (실명·예명·핸들). 공인 인물(역사·정치인)은 제외.
**ADDRESS**: 행정구역 + 도로명 + 동호수를 모두 포함하는 full span 우선.
**ORG**: 회사·학교·병원·기관·정부·협회. 부서/팀 단독은 제외(별도 DEPT 클래스).

자세한 라벨 가이드: [NER_DESIGN_v1.md](https://github.com/vmaca123/My-AI-Security-Project/blob/main/PII/ner/NER_DESIGN_v1.md)

## Example schema

각 sample은 다음 5개 필드를 가진다.

```json
{
  "tokens": ["김", "민", "수", "님", "께", " ", "감", "사", "드", "립", "니", "다", "."],
  "labels": [1, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  "label_names": ["B-NAME", "I-NAME", "I-NAME", "O", "O", "O", "O", "O", "O", "O", "O", "O", "O"],
  "sentence": "김민수님께 감사드립니다.",
  "source": "faker_baseline_v3"
}
```

- `tokens`: char-level 토큰 (한글 1자 = 1 token)
- `labels` / `label_names`: 토큰별 BIO 라벨 (정수 + 문자열 둘 다)
- `sentence`: 원본 문장
- `source`: `klue_train` / `faker_baseline_v3` / `composite_v3` / `hard_negative_v3`

## 사용 예시

```python
from datasets import load_dataset

ds = load_dataset("vmaca123/korean-pii-ner-v3")
print(ds)
# DatasetDict({
#     train: Dataset({ features: [...], num_rows: 27206 })
#     val: Dataset({ features: [...], num_rows: 3401 })
#     test: Dataset({ features: [...], num_rows: 3401 })
#     klue_test: Dataset({ features: [...], num_rows: 5000 })
# })

sample = ds["train"][0]
print(sample["sentence"])
print(list(zip(sample["tokens"], sample["label_names"])))
```

## 학습 결과 (v3 production)

| Metric | Value |
|---|---|
| Base model | klue/roberta-large (335M params) |
| Training setup | Phase 1 freeze 1 epoch (LR 5e-4) + Phase 2 unfreeze 5 epochs (LR 2e-5), batch 16 |
| Internal val macro-F1 | 0.872 |
| Internal test macro-F1 | 0.878 |
| **KLUE val macro-F1 (외부)** | **0.766** |
| 학습 시간 | 30분 (Vast.ai RTX 3090 Korea) |

자세한 학습 결과: [TRAINING_RESULTS_v3.md](https://github.com/vmaca123/My-AI-Security-Project/blob/main/PII/ner/TRAINING_RESULTS_v3.md)

## v1 → v3 학습 이력 (meta lesson)

| Version | Data | KLUE val F1 | 결과 |
|---|---|---:|---|
| v1 | KLUE 21k + Faker 10k = 31k | 0.764 | 좋음 |
| v2 | + Naver 90k + WikiAnn 20k = 139k | 0.664 (-10%p) | ❌ 실패 |
| **v3** | KLUE 21k + Faker 10k + composite 2k + hard_neg 1k = **34k** | **0.766** | ✅ production |

**Meta lesson**: "더 많은 데이터 ≠ 더 좋은 모델". v2는 Naver NER 라벨 quality + WikiAnn 다국어 잡음 + setup 동시 변경으로 실패. v3는 v1 setup 유지 + minimal augment만 추가한 conservative pivot으로 성공.

## License

본 데이터셋은 [Creative Commons Attribution-ShareAlike 4.0 International (CC-BY-SA-4.0)](https://creativecommons.org/licenses/by-sa/4.0/) 라이선스 하에 배포된다.

라이선스 의무:
- **Attribution**: 사용 시 원본 출처(이 dataset card)를 명시할 것.
- **ShareAlike**: 본 데이터셋을 수정·확장한 파생물도 CC-BY-SA-4.0 또는 호환 라이선스로 배포할 것.

### 출처별 라이선스 매트릭스

| Source | 비율 | 원본 라이선스 | 본 dataset 라이선스 |
|---|---:|---|---|
| KLUE-NER | 62% | CC-BY-SA-4.0 (KLUE-Benchmark, 2021) | CC-BY-SA-4.0 |
| Faker-ko 합성 | 29% | MIT (Faker library) — 합성 데이터 자체는 저작권 없음 | CC-BY-SA-4.0 (본 release 통합) |
| Composite augmentation | 6% | 자체 합성 (Faker 베이스) | CC-BY-SA-4.0 |
| Hard negative | 3% | 자체 합성 | CC-BY-SA-4.0 |

KLUE 라이선스가 가장 엄격(ShareAlike)하므로 통합 release는 CC-BY-SA-4.0로 가져간다.

## Citation

```bibtex
@dataset{korean_pii_ner_v3_2026,
  title  = {Korean PII NER v3: Training Dataset for Korean Personal Information NER},
  author = {vmaca123},
  year   = {2026},
  url    = {https://huggingface.co/datasets/vmaca123/korean-pii-ner-v3},
  note   = {Includes KLUE-NER train (CC-BY-SA-4.0), Faker-ko synthesis, and curated augmentation}
}
```

KLUE-NER 원본도 같이 인용해주세요:

```bibtex
@article{park2021klue,
  title  = {KLUE: Korean Language Understanding Evaluation},
  author = {Park, Sungjoon and Moon, Jihyung and Kim, Sungdong and others},
  journal= {arXiv preprint arXiv:2105.09680},
  year   = {2021}
}
```

## Privacy notice

본 데이터셋은 **합성 또는 공개 코퍼스 기반**으로 제작되었으며, 실제 개인의 PII는 포함하지 않는다.

- KLUE-NER 부분은 공개된 한국어 코퍼스(뉴스, 위키 등)에서 라벨링된 데이터로, KLUE 벤치마크가 이미 공개된 상태.
- Faker / composite / hard_negative 부분은 모두 합성 데이터로, 실제 인물·주소·조직과 무관.

다만 합성 PII라도 실존 인물·기관과 우연히 일치할 가능성이 있으므로, 본 데이터셋을 활용한 모델을 production에 배포할 때는 별도 PII 마스킹 파이프라인(예: 본 프로젝트의 v0.2 guardrail)을 통과시킬 것을 권장한다.

## 관련 자료

- **모델**: [vmaca123/korean-pii-ner-v3](https://huggingface.co/vmaca123/korean-pii-ner-v3)
- **GitHub repository**: [vmaca123/My-AI-Security-Project](https://github.com/vmaca123/My-AI-Security-Project)
- **상위 프로젝트**: 한국어 PII Guardrail v0.2 (LiteLLM Gateway 한국어 PII 가드레일 캡스톤)
