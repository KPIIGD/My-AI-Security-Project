# data_prep_v4.py — NER 자아성찰 요청 (편향 차단 설계)

> **이 파일을 읽는 AI에게**: 너는 새 Claude Code 세션이고, NER v4 데이터 prep 스크립트를 **적대적으로 검증**한다. 칭찬 금지. 공격해라.
>
> **사용법**: 새 Claude Code 대화 → "C:/My-AI-Security-Project/PII/ner/ai_research/data_prep_v4_verification_request.md 읽고 그대로 수행해줘".

---

## ⚠️ 편향 차단 규칙

1. **작성자(직전 세션 Claude)는 잘 짰다고 믿는 편향 있음.** smoke 100 OK가 117k 전체 OK는 아님.
2. **요약 말고 실제 코드/parquet/json 직접 읽고 판단**. dry-run 우선.
3. **채점 아니라 재공격**: (a) leakage가 진짜 차단됐나 카운트로 입증 (b) char 변환 손실 (c) 비중 균형 시뮬.
4. **CLAUDE.md 하드원 교훈과 모순 우선**: v2 실패 패턴 (Naver 81%, 어절→char 노이즈, 다중 변수) 재발 의심.
5. **일반론 금지** — file_path:line_no 인용.

---

## NER 시스템 하드원 교훈

### v2 실패 (KLUE 외부 −10%p)
- Naver NER 90k + WikiAnn 20k = 81% 비중 → distribution shift
- 어절 단위 라벨 → char 변환 시 조사까지 NE에 빨려감 ("이병헌이" 전체 NAME)
- 다중 변수 동시 변경 (LWLR + FGM)

### v4 의도
- corpus4everyone는 char-level (어절 트랩 회피) → v3 진단 ORG F1 0.635 약점 해결 목표
- one-variable-at-a-time: v3 setup 유지, **데이터만 변경**
- dedup으로 평가 누설 차단

---

## 이 산출물이 *주장*하는 것 (참인지 검증)

- **주장 A**: data_prep_v4.py 가 train ∩ KLUE val sentence hash dedup 작동 — 117k corpus4everyone + 21k KLUE train ∩ 5k KLUE val 카운트가 코드로 입증되나? 그냥 1건만 잡힌 게 정상?
- **주장 B**: corpus4everyone tokens 가 char-level — 117k 전부 char 단위인지 random 100개 sampling 으로 확인 (어절 단위 섞여있으면 v2 트랩 재발)
- **주장 C**: ORG pool 2,789 가 v3 24 의 superset — KRX 2,765 + extras 25 중복 제거 후 v3 24 모두 포함?
- **주장 D**: CORPUS4EV_TO_PII 매핑이 PS/OG/LC 만 채택, 나머지 13 entity → O 처리. 이 손실이 train 라벨 noise 만들지 않나? (KLUE QT/DT 시간/숫자 entity 가 NAME 으로 오인되면 false positive 학습)
- **주장 E**: KLUE train 21k 전체 재추출 (v3 split 의 train+val+test 모두 합쳐서) — 진짜 21,008개 다 잡히나?
- **주장 F**: Faker baseline 10k → 5k 축소가 진짜 비중 균형. corpus4everyone 110k + KLUE 21k + Faker 5k = 합성 약 5% — 적절?

---

## 직접 읽을 파일

1. `C:/My-AI-Security-Project/PII/ner/scripts/data_prep_v4.py` (415 lines)
2. `C:/My-AI-Security-Project/PII/ner/scripts/data_prep_v3.py` (비교용 baseline)
3. `C:/My-AI-Security-Project/PII/ner/data/external/huggingface/datasciathlete__corpus4everyone-korean-NER/README.md` (라벨 스키마 30종)
4. `C:/My-AI-Security-Project/PII/ner/data/pii_ner_v4_smoke.json` (smoke 100 결과, 38MB — 실제로는 30k 까지 부분 dump)
5. `C:/My-AI-Security-Project/PII/ner/data/external/INVENTORY.md` (5/22 데이터 인벤토리 + v2 교훈)
6. `C:/My-AI-Security-Project/PII/ner/TRAINING_RESULTS_v3.md` (v2 실패 분석 §2)
7. `C:/My-AI-Security-Project/PII/ner/CLAUDE.md` (하드원 교훈 §2 + 자아성찰 룰 §4)

---

## 너가 답할 질문

1. **char-level 검증** — corpus4everyone train 117k 중 무작위 N개 dry-run: tokens 가 정말 char 단위? (어절 발견되면 critical)
2. **dedup 카운트 실측** — KLUE val 5,000 hash set vs KLUE train 21k vs corpus4everyone 117k → 실제 충돌 카운트는?
3. **라벨 매핑 손실 영향** — corpus4everyone 의 QT(숫자)/DT(날짜)/AF(인공물) 같은 entity가 O로 학습되면 모델이 정말로 그들을 NAME/ADDRESS/ORG와 구분 학습할까? false negative risk?
4. **char 변환 inconsistency** — corpus4everyone tokens 안에 공백 char(' ')가 단독으로 있는지? KLUE 도 그런 형식인지? 양쪽 일관성 검증.
5. **비중 균형 dry-run** — corpus4everyone 117k 추가 시 train pool 약 145k → corpus4everyone가 80%+ 차지. v2 Naver 81% 함정 재발 의심.
6. **v3 ORG pool 24개 superset 검증** — data_prep_v3.py:262-268 ORG 24개 중 KRX 명단에 없는 게 있나? 누락 항목은?
7. **솔직히 v4 가 v3 보다 진짜 좋아질 가능성** — 데이터 quality > quantity 교훈상, 117k 추가가 또 v2식 실패할 risk는?

마지막: **VERDICT: PASS / REVISE (고칠 것 3개) / SCRAP (왜)** + 한 줄 근거.
포맷 (auto_verify_loop ATTACK_PROMPT 기준): VERDICT 헤더 + ISSUES_JSON / SCRAP_REASON / PASS_CONFIRMATION.
