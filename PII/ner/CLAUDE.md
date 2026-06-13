# PII NER — Owner Working Memory

> NER 강화 트랙 (v3 production → v4+). 본 파일은 *NER 한정* 작업 룰.
> 상위 시스템 룰은 `c:/finence/CLAUDE.md` (자아성찰/유치원생/함정 #23 등) 참조.
> Pipeline 위치는 `c:/litellm/` (한국어 PII LiteLLM Gateway, NER은 사이드카 부품).

---

## 🔥 0. 세션 시작 시 자동 인계 (의무)

**다음 세션 첫 응답 전 반드시 이 두 파일 자동 읽기:**
1. `C:/My-AI-Security-Project/PII/ner/NEXT_SESSION.md` — 직전 세션 상태 + 다음 실행 순서
2. `C:/My-AI-Security-Project/PII/ner/SESSION_HISTORY.md` 맨 마지막 섹션 — 직전 세션 히스토리

**"v4 가 뭐냐 / 이게 무슨 작업이냐" 같은 질문 절대 X.** 위 두 파일에 다 박혀있음.

**용어 빠른 매핑** (사용자가 한 단어만 던질 때):
- "v4" = **NER 모델 v4** (klue/roberta-large, KLUE 외부 0.766 → 향상 목표). 가드레일 발표자료 v4 (`AI_Gateway_가드레일_프로젝트_발표_v4_final.pptx`) X.
- "가드레일" = `C:\litellm\` LiteLLM Gateway (논문 제출 완료, 운영 중)
- "NER" = `C:\My-AI-Security-Project\PII\ner\` (지금 강화 트랙)
- "사이드카" = `C:\litellm\pii-sidecar\` (NER 모델을 HTTP로 노출, NER_MODEL_PATH로 v3/v4 swap)
- "자아성찰" = `scripts/auto_verify_loop.py` (cross-session 적대 검증, finance 5/24 패턴 NER 5/28 이식)

**연결 관계**: NER 모델은 가드레일의 부품. v4 학습은 NER 폴더, swap은 가드레일 폴더.

---

## 1. 한 줄 정체성

한국어 PII Gateway의 **단일 통합 가드레일**용 NER 모델 (klue/roberta-large fine-tuned). v3 production: Internal test 0.878 / KLUE 외부 0.766. ONNX INT8 quantization 완료 (4x speedup, 99.7% agreement). HF Hub `vmaca123/korean-pii-ner-v3`.

---

## 2. 하드원 교훈 (모든 자아성찰의 기준점)

### v2 실패 (2026-05-12, KLUE 외부 −10%p)
- AI 토론 권고대로 Naver NER 90k + WikiAnn 20k 통합 → KLUE val 0.764 → **0.664** 박살.
- 원인 4개:
  1. **Naver 81% 비중** → 모델이 Naver 분포에 fit
  2. **어절 단위 라벨 → char-level 변환 노이즈** ("이병헌이" 전체가 NAME으로 학습)
  3. **WikiAnn 다국어 머신 매핑** 라벨 quality 의심
  4. **Layer-wise LR + FGM 동시 변경** → 변수 격리 불가

### 메타 lesson (절대 잊지 말 것)
1. **AI 토론 ≠ 실험 검증** — 토론은 가설 brainstorm용. 데이터 quality는 직접 ablation 으로만.
2. **데이터 quality > quantity** — 31k → 139k 키운 v2가 KLUE F1 0.766 → 0.664.
3. **검증된 setup 보호** — v1 success 패턴 (Phase 1 freeze + Phase 2 unfreeze) 깨뜨린 LWLR/FGM 동시 변경이 변수 격리 불가능하게 함.
4. **conservative pivot 효과** — v3 = "v1 + minimal augment" 만이 정답. 모든 변화 한 번에 X.
5. **plateau 멈춤 트랩** — v1 ep4→ep5 +0.001 = plateau로 해석했지만, 외부 transfer 0.764는 약점 신호였음. plateau ≠ 종료 조건.

---

## 3. 자아성찰 (cross-session adversarial verification)

### 3.1 명칭 통일
**검증 워크플로우 / round N attack / cross-session 검증 / 자기 검증 자동화 트랙 = "자아성찰"** (finance 5/27 룰 NER에도 적용).

### 3.2 NER 자아성찰 대상 (트레이딩 자본 아님 → 진입 장벽 조정)
**자아성찰 풀로 (적용 의무)**:
- v4 본 학습 결과 (KLUE 외부 0.766 → 목표 끌어올린 주장)
- v4 데이터셋 prep 코드 (leakage / dedup / char 변환)
- 사이드카 모델 swap (v3 → v4 production 교체)
- 평가 산식 변경 (macro/micro/span-exact 정의 변경 시)
- **§6 금지 룰 영역 결정** (체크포인트 덮어쓰기 / HF Hub 모델 삭제 / v3 백업 우회) — *결정 자체*에 자아성찰
- **plateau 멈춤 결정** (v1 ep4→ep5 트랩 재발 방지)

**메타 자아성찰 (검증 인프라 자체 검증) 영구 면제** (2026-05-28 결정):
- `scripts/auto_verify_loop.py` / `ai_research/_verification_request_template.md` / 본 CLAUDE.md §3 자체를 ARTIFACT로 자아성찰 시 ESCALATE_NO_PROGRESS 발생이 정상. finance 5/24 메타 검증 + NER 5/28 메타 검증 둘 다 동일 패턴 입증.
- 사유: ARTIFACT가 검증 도구 자체일 때 자기참조 가드는 본질적으로 무력화됨 (방어 측 패배 비대칭). 매 라운드 우회 패턴 발견 < 진짜 가드 fix 비용.
- 메타 자아성찰 결과는 ESCALATE_NO_PROGRESS로 정직 종료, **재시도 X**. 인프라 룰 변경 시에만 reopen.
- 메타 검증의 의미: 한 번 돌려서 자기 한계 정직 인식 + 가드 일부 fix 적용. 그 이상은 ritual.

**자아성찰 풀로 (사용자 결정 시 면제)** — *정의 명시*:
- **"작은 ablation 1회"** = ① 데이터셋 변경 X (v3 데이터 그대로) + ② 학습 setup 변경 1개 이하 + ③ 학습 시간 ≤ 30분 + ④ 외부 평가(KLUE val) 영향 ≤ ±0.005 예상. **4 조건 모두 충족** 시만 "작은". v2 LWLR+FGM 동시 = 조건 ② 위반 → 면제 X.
- **"hyperparam 1개 sweep"** = 단일 hyperparam (LR / batch / warmup / weight_decay 등) 의 값 변경. *동시에 둘 이상* 변경 = sweep 아님 → 면제 X. seed sweep 은 항상 가능.
- **"데이터 통계 조회"** = read-only SQL/pandas 집계만. *새 split 생성 / dedup 룰 변경 / leakage 검증 후 데이터 수정* = 면제 X.

**면제 결정 자체에 자아성찰 X**: 면제 결정은 *사용자만* (Claude 자기 결정 금지 — 자기 합리화 우회 차단).

**R2-i03 fix — 면제 적용 강제 증거 룰**:
- Claude 가 면제 적용 보고 시 **사용자 명시 chat 인용 의무** (paraphrase X, 원문 quote)
- 예: "사용자 면제: '이건 작은 ablation이니까 그냥 진행해' (2026-05-28 chat)"
- 인용 없이 면제 적용 = 사이코판트 = 룰 위반
- 사용자가 면제 *명시 안 한* 상황에 면제 적용 = 함정 #23 위반 (사용자 결정 침범)

### 3.3 워크플로우
1. 산출물 완성 → `ai_research/<artifact>_verification_request.md` 작성 (템플릿 사용)
2. `python scripts/auto_verify_loop.py init --artifact ... --request ... --log logs/verify/<name>.log.md`
3. `next-prompts` → 외부 Claude Code 세션 띄워서 Agent 실행
4. Agent raw 결과 파일로 저장 → `record --verdict ... --raw-files ...`
5. PASS 받으려면 final 3-Agent **3/3 동의** + raw 위조 가드 7개 통과

### 3.4 가드 7개 (절대 풀지 말 것)
1. **raw 강제**: PASS verdict는 Agent raw 응답 파일 필수
2. **PASS_CONFIRMATION 검증**: (a)(b) 항목 + ≥80자 + final은 focus 2/3 다뤄야
3. **raw 중복 거부**: path / sha256 hash 둘 다 unique
4. **ARTIFACT mention + VERDICT 헤더 강제**: 가짜 raw 차단
5. **fixes 강제**: 직전 REVISE 후 record는 `--fixes` 필수
6. **수렴 가드**: 동일 이슈 hash 2회 연속 / 이슈 개수 3라운드 비감소 → ESCALATE
7. **MAX_ATTACK_ITER=5 + FINAL_AGENTS=3 + 3/3 PASS 강제**

### 3.5 ESCALATE 결과 정직 보고
PASS / ESCALATE_NO_PROGRESS / ESCALATE_CONVERGENCE_SAME_ISSUES / ESCALATE_MAX_ITER / SCRAP — 셋 중 하나로 종료. **ESCALATE를 PASS로 보고 = 사이코판트 = 룰 위반.**

### 3.6 PASS 후 reopen 룰 (R1-i07 fix)
PASS 받은 산출물에서 추후 새 결함 발견 시:
1. 기존 log_path 그대로 두고 (감사 trail 보존)
2. 새 verification_request: `<artifact>_v2_verification_request.md` (버전 명시)
3. 새 log_path: `logs/verify/<name>_v2.log.md`
4. `init` 호출 후 v1 PASS 결과를 prior_round 0 으로 명시 참조

→ 영구 PASS 우상화 차단. PASS = "특정 시점 / 특정 결함 셋" 에 대한 PASS 일 뿐.

---

## 4. NER 특화 적대 검증 각도 (자아성찰 attack 카테고리)

### 4.1 stat (통계·평가 건전성)
- **데이터 leakage**: train에 KLUE val/test 문장 우연 포함? (corpus4everyone이 KLUE 파생이라 위험 high)
- **평가 누설**: KLUE val로 early stop 했는데 같은 KLUE val을 외부 평가로 보고하면 누설
- **산식 일관성**: macro vs micro, entity-level vs token-level, span-exact vs partial — 보고마다 같은가?
- **재현성**: seed / batch 순서 / dropout / fp16 / DataLoader shuffle 고정?
- **숫자 부풀리기**: 0.05~0.10 차이가 산식 선택에서 나올 수 있음. 명시 의무.

### 4.2 data (데이터 정확성)
- **char-level 변환 정확성**: 어절 단위 데이터 흡수 시 조사 분리 검증
- **dedup 룰**: 학습/평가 분리 후 dedup인가? hash 충돌은? near-dup (편집거리 3 이내)는?
- **라벨 매핑 정합성**: PS→NAME, LC→ADDRESS, OG→ORG 매핑이 데이터셋마다 일관?
- **합성 비중**: Faker:실데이터 비율이 모델 distribution을 왜곡하지 않나? (v2 = Naver 81% 함정)
- **BIO 일관성**: B 없이 I 시작 케이스, B-X I-Y 연속 등 무효 시퀀스 비율

### 4.3 ops (ML 운영 리스크)
- **v2 실패 재발**: 데이터 추가 + setup 변경이 한 PR에 같이 있나? (변수 격리 검증)
- **plateau 트랩**: epoch ↑로 외부 transfer 좋아지는지 확인했나? internal F1 plateau로 멈추면 외부 약점 가림
- **외부 transfer 환상**: KLUE val로 early stop = KLUE에 fit. 진짜 외부는 KLUE test 또는 KoJailFuzz
- **HF 모델 배포·롤백**: v4 production swap 시 v3 백업? rollback 절차?
- **사이드카 호환**: pii-sidecar의 `NER_MODEL_PATH` 환경변수만 바꾸면 swap 되는가?

---

## 5. NER 자아성찰 비용 견적 (사용자 우려 "오래 걸린다" 안전망)

| 작업 | 자아성찰 round 평균 | 인지 자본 |
|---|---:|---:|
| v4 데이터셋 prep 코드 | 2~3 round (≈30분) | 중 |
| v4 학습 결과 (수치 검증) | 3~4 round (≈1시간) | 높음 (leakage 검증) |
| 사이드카 모델 swap | 1~2 round (≈20분) | 낮음 |

**임계**: 산출물 하나당 자아성찰 1.5시간 초과 시 사용자에게 보고. 사용자가 면제 결정 가능.

---

## 6. 절대 하지 말 것 (자아성찰 + NER 종합)

- ESCALATE를 PASS로 보고 (= 사이코판트)
- raw 파일 손으로 위조 (= 자동화 자체 파괴)
- v2 실패 패턴 재발 (Naver 어절 / 다중 변수 동시 변경 / AI 토론 즉시 수용)
- KLUE val을 early stop + 보고에 동시 사용 (= 평가 누설)
- v3 production 체크포인트 덮어쓰기 (백업 의무)
- HF Hub의 v3 모델 삭제 (외부 의존자 있을 수 있음 — vmaca123/korean-pii-ner-v3 public)
- 자아성찰 진입 장벽 임의 낮추기 (사용자만 결정)
- finance CLAUDE.md 룰 무단 무시 — 본 NER 룰은 상위 룰의 *NER 한정 적용 가이드*일 뿐
