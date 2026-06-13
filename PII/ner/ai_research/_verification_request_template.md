# [산출물 이름] — NER 자아성찰 요청 (편향 차단 설계)

> **재사용 템플릿.** 완결 산출물 하나 만들 때마다 이 파일을 복사 → `<artifact>_verification_request.md` 로 저장하고 [대괄호] 채움.
>
> **이 파일을 읽는 AI에게**: 너는 새 Claude Code 세션이고, 아래 NER 산출물을 **적대적으로 검증** 하는 역할이다. 칭찬 금지. 공격해라.
>
> **사용법 (사용자)**: 새 Claude Code 대화 → `C:/My-AI-Security-Project/PII/ner/ai_research/[이 파일명] 읽고 그대로 수행해줘`.

---

## ⚠️ 편향 차단 규칙 (핵심 — 반드시 지킬 것)

1. **작성자(직전 세션 Claude)는 잘 만들었다고 믿는 편향이 있다.** 메모리/문서의 "✅완료/PASS/통과"를 믿지 마라 — "테스트 돌았다" ≠ "옳다".
2. **요약 말고 실제 코드/파일/raw 평가 결과를 직접 읽고 판단하라.** (자축 요약은 참고만, 근거 X.)
3. **채점 아니라 재공격**: (a) 가짜 fix (이름만 바꾸고 본질 그대로) 색출 (b) 작성자가 놓친 새 결함
4. **너도 CLAUDE.md 읽을 수 있다** — 우리 하드원 교훈과 *모순* 되는 곳 우선
5. **일반론 금지** ("데이터 더 붙여라" 류는 무가치). 구체적 결함만 (`file_path:line_no` 인용).
6. **가능하면 코드 실행 / dry-run** — Python으로 dedup 실제 hit, leakage 실제 카운트, 산식 실제 계산까지

---

## NER 시스템 하드원 교훈 (이 안에서 판단)

### v2 실패 (2026-05-12)
- AI 토론 권고 → Naver NER 90k + WikiAnn 20k 통합 → KLUE val 0.764 → **0.664** 박살.
- 원인: (1) Naver 81% 비중 (2) 어절 라벨 → char 변환 노이즈 (3) WikiAnn 머신 라벨 (4) LWLR + FGM 동시 변경

### 메타 lesson
- **데이터 quality > quantity** — 31k → 139k 키운 v2가 외부 F1 −10%p
- **AI 토론은 가설 brainstorm, 실험 ≠ 검증**
- **변수 한 번에 하나만** — v3 conservative pivot 만이 정답
- **plateau ≠ 종료 조건** — v1 internal plateau 가 외부 약점 가렸음
- **검증된 setup 보호** — Phase 1/2 freeze/unfreeze 패턴 함부로 바꾸지 말 것

---

## 5/23 finance 메모리 룰 (NER에도 적용 — 정합 점검)

- **DATA vs INFER 혼동**: 산출물이 측정값(F1 0.X)과 해석(이게 외부 transfer 의미함)을 섞어 박지 않았나?
- **zero-base 정합**: 산출물이 옛 결론(v3 setup 이 정답, char-level 만 안전 등)을 pre-filter로 박지 않았나? v2 실패 트라우마가 v4 가능성도 차단하지 않았나?
- **함정 #23**: 산출물이 사용자 결정 영역(LIVE 모델 swap, HF Hub 공개 등) 침범하는가? "이렇게 살아야 합니다" 톤?

---

## NER 특화 attack 각도 (이번 산출물에 적용)

### stat (통계·평가)
- 데이터 leakage 가능성 (corpus4everyone ↔ KLUE val/test 중복)
- 평가 누설 (KLUE val로 early stop + 같은 KLUE val로 보고)
- 산식 일관성 (macro vs micro, entity-level vs token-level, span-exact)
- 재현성 (seed, batch shuffle, dropout, fp16)
- 숫자 부풀리기 (산식 선택에서 0.05+ 변동 가능)

### data
- char-level 변환 정확성
- dedup 룰 (exact / near-dup / hash)
- 라벨 매핑 정합 (PS→NAME, LC→ADDRESS, OG→ORG)
- 합성 비중 (v2 = Naver 81% 함정 재발)
- BIO 시퀀스 무효 케이스 비율

### ops
- 변수 격리 (데이터 추가 + setup 변경이 한 PR?)
- plateau 트랩 (internal F1 멈춤이 외부 약점 가림)
- 외부 transfer 환상 (KLUE val ≠ 진짜 외부)
- HF 모델 배포 / 롤백
- 사이드카 swap 호환성

---

## 직접 읽을 것 (작성자 요약 말고 *이 파일들*)

- [파일1 — 무엇] (예: `scripts/data_prep_v4.py` — dedup 룰 검증)
- [파일2] (예: `data/pii_ner_v4.json` — leakage 실측, train ∩ klue_val 카운트)
- [파일3] (예: `models/pii_ner_v4/final/eval/klue_test_results.json` — 평가 raw)
- [파일4] (예: `models/pii_ner_v4/all_eval_results.json` — per-entity F1)
- [파일5] (예: `TRAINING_RESULTS_v4.md` — 변수 격리 검증)

---

## 이 산출물이 *주장* 하는 것 (참인지 검증)

- [주장 A] (예: "KLUE 외부 macro-F1 0.766 → 0.XX 향상")
- [주장 B] (예: "Naver 어절 트랩 회피 — corpus4everyone char-level만 사용")
- [주장 C] (예: "v3 대비 변수 하나만 변경 (데이터셋만, setup 동일)")
- [주장 D] (예: "leakage 없음 — train ∩ KLUE val/test = 0")

---

## 너가 답할 질문

1. **가짜 fix / 이름만 바뀐 것** 있나? 어디 · 왜.
2. **작성자가 놓친 가장 치명적 결함** 하나.
3. **하드원 교훈과 모순되는 곳** — v2 실패 패턴 재발 의심 우선.
4. **leakage 실측** — train ∩ eval 가 진짜 0 인지 코드로 확인했나? (작성자 주장 X, raw 카운트 O)
5. **재현성** — 다른 seed로 같은 결과 나오나? plateau 가 우연 아닌지?
6. **숫자 산식** — macro / micro / span-exact 정의가 보고서마다 같나?
7. **솔직히 이거 가치 있나, 인지 자본 낭비인가?**

마지막: **VERDICT: PASS / REVISE (고칠 것 3개) / SCRAP (왜)** + 한 줄 근거.

REVISE 인 경우 다음 줄에:
```
ISSUES_JSON:
[
  {"id":"rN-i01","severity":"high|med|low","category":"stat|data|ops","description":"...","file_refs":["path:line"]},
  ...
]
```

SCRAP 인 경우 다음 줄에:
```
SCRAP_REASON: <근본 결함>
```

PASS 인 경우 다음 줄에:
```
PASS_CONFIRMATION:
(a) 읽은 파일: ...
(b) 체크리스트 처리 결과: ...
(c) minor 무시 사항: ...
```
PASS_CONFIRMATION 본문 ≥80자. final 라운드는 focus 카테고리 (stat/data/ops) 중 2개 이상 다뤄야 함.
