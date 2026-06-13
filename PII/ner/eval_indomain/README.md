# in-domain 평가셋 구축 (NER v4)

> 검증 지적(2026-06-04): **"평가셋 도메인 불일치 — KLUE 뉴스로 평가하는데 실제 타겟은 챗 PII."**
> → 챗/대화 도메인 문장을 모아 **사람 2인 독립 라벨 → 조정**으로 in-domain 정답셋을 만든다.
> 구조형 PII(여권/면허/카드/계좌/RRN)는 **합성 자동정답**(사람 불필요)으로 별 트랙.

⚠️ **라벨 자체는 자동화 불가.** 본 폴더는 그 일을 **가능하게 하는 인프라**(후보추출·라벨도구·조정·가이드)다. NER 정답 라벨은 민우+양유상이 직접 단다.

---

## 파일

| 파일 | 역할 |
|---|---|
| `synth_structured.py` | 구조형 PII 합성(여권/면허/법인/차량/카드/계좌/RRN, 정확 형식+체크섬) → `structured_eval.jsonl`. 자동정답, 사람 X. v0.2 detector 평가 호환(라벨문맥 + 음성 케이스). |
| `build_candidates.py` | 챗 도메인 weak 문장 샘플 + 구조형 합성 → 누설필터(KLUE test)·dedup → `candidates.jsonl` |
| `make_annotation_sheets.py` | `candidates.jsonl` → 2인 독립 시트 `annotator_A.jsonl`/`annotator_B.jsonl` |
| `reconcile.py` | 두 라벨 → span-exact 일치도(F1)·불일치 추출·합의 gold → `eval_indomain_gold.jsonl` + `disagreements.jsonl` |
| `LABEL_GUIDE_eval.md` | 라벨 기준(= label_guide_v1.md + 챗 특화 + 마크업법) |

---

## 워크플로우

```powershell
cd C:\My-AI-Security-Project\PII\ner

# 1. 후보 생성 (챗 400 + 구조형합성 150) — 누설/중복 자동 제거
python eval_indomain/build_candidates.py --n-chat 400 --n-struct 150

# 2. 구조형 PII 자동정답 셋 (사람 라벨 불필요)
python eval_indomain/synth_structured.py --n 200 --out eval_indomain/structured_eval.jsonl

# 3. 2인 독립 라벨 시트 생성
python eval_indomain/make_annotation_sheets.py --annotators minwoo,yangyusang

# 4. ✍️ 민우·양유상이 각자 annotator_minwoo.jsonl / annotator_yangyusang.jsonl 의
#    'annotation' 필드를 {{NAME|텍스트}} 마크업으로 채운다 (서로 안 보고).
#    기준: LABEL_GUIDE_eval.md

# 5. 조정 — 일치도 + 불일치 + 합의 gold
python eval_indomain/reconcile.py --a eval_indomain/annotator_minwoo.jsonl `
                                  --b eval_indomain/annotator_yangyusang.jsonl

# 6. disagreements.jsonl 을 둘이 모여 조정 → 최종 eval_indomain_gold.jsonl 확정
```

---

## 목표 규모 / 기준

- **NER in-domain gold**: ~300~500 문장 (검증 권고). 챗 도메인.
- **구조형 PII**: 합성 ~200 (자동정답).
- **라벨러 일치도(IAA) 목표**: span-exact F1 ≥ 0.80. < 0.70 이면 가이드 합의 부족 → 보강 후 재라벨.
- 평가 시 이 gold 로 NER v3/v4 의 **in-domain** 성능 측정(KLUE 외부 점수와 별도 보고).

---

## 왜 이렇게 (검증 지적 직결)

| 검증 지적 | 본 인프라의 답 |
|---|---|
| 평가셋 도메인 불일치(뉴스 vs 챗) | 챗 도메인(dialogue/safe_conv/review/privacy/medical) 후보 |
| 구조형 PII 갭 | `synth_structured` 정확 형식+체크섬 합성 |
| 누설(KLUE) 위험 | `build_candidates` 가 KLUE test content_hash 제거 |
| 라벨 신뢰성 | 2인 독립 + IAA + 조정 (단일 라벨러 편향 차단) |
