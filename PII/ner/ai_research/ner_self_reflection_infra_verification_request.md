# NER 자아성찰 인프라 — 메타 적대 검증 요청

> **재사용 템플릿 인스턴스.** 2026-05-28 NER 자아성찰 인프라 빌드 직후 메타 검증.
>
> **이 파일을 읽는 AI에게**: 너는 새 Claude Code 세션이고, NER 자아성찰 인프라 자체를 **적대적으로 검증**하는 역할이다. 칭찬 금지. 공격해라. 자기참조 (인프라가 자기 룰로 자기를 검증) 함정도 짚어라.
>
> **사용법 (사용자)**: 새 Claude Code 대화 → `C:/My-AI-Security-Project/PII/ner/ai_research/ner_self_reflection_infra_verification_request.md 읽고 그대로 수행해줘`.

---

## ⚠️ 편향 차단 규칙 (핵심)

1. **작성자(직전 세션 Claude)는 finance 패턴을 잘 이식했다고 믿는 편향이 있다.** "동작 확인 ✅"는 `--help`/`import` 통과지 "옳다"가 아님.
2. **요약 말고 실제 코드/문서 직접 읽고 판단하라.**
3. **채점 아니라 재공격**: (a) 가짜 이식 (이름만 바꾸고 본질 같지 않음) (b) finance에선 통했지만 NER에선 안 통할 invariant 깨짐.
4. **자기참조 함정 우선**: 인프라가 자기 룰로 자기를 검증한다 = 가드 자체에 결함 있으면 검증도 결함. 어느 가드가 메타 검증에서 무력화되나?
5. **일반론 금지** — 구체적 결함만 (`file_path:line_no` 인용).
6. **가능하면 코드 dry-run** — Python 으로 `auto_verify_loop.py` import / `_validate_pass_confirmation` 직접 호출 / state machine 엣지 시뮬.

---

## NER 시스템 하드원 교훈 (이 안에서 판단)

### finance 자아성찰 원본 (5/21 + 5/24)
- "완결 산출물 = 별도 세션 적대 검증" — 사용자 5/21 명령
- auto_verify_loop = 자동 트랙 (5/24) — 가드 7개 + state machine
- **메타 자아성찰 결과 (5/24)**: auto_verify_loop이 자기 자신 검증 → 4 round → final 2/3 PASS → **ESCALATE_NO_PROGRESS** (자기 한계 정직 인식). 메타 검증 PASS 통과 자체가 어려움을 인정.

### NER 본 인프라의 핵심 변경 (5/28)
- 5번 원칙: `C:/finence/CLAUDE.md` → `C:/My-AI-Security-Project/PII/ner/CLAUDE.md`
- FOCUS_ANGLES 3개: 통계/코드/운영 → **stat/data/ops** (NER 카테고리)
- PASS_CONFIRMATION 키워드 그룹: NER 어휘 (leakage/dedup/plateau/transfer 등)
- 진입 장벽: "트레이딩 자본 없음" 사유로 finance보다 낮춤 (CLAUDE.md §3.2 면제 3종)

---

## 5/23 finance 메모리 룰 (NER에도 적용 — 정합 점검)

- **DATA vs INFER 혼동**: NER CLAUDE.md 가 측정값(v3 0.766)과 해석(외부 transfer 약함)을 섞어 박았나?
- **zero-base 정합**: 본 인프라가 finance 패턴(v2 실패=Naver 어절)을 pre-filter로 박아 char-level 외 다른 길 차단하나?
- **함정 #23**: NER CLAUDE.md 가 사용자 결정 영역(HF v3 모델 삭제, LIVE swap) 침범하는가?

---

## 직접 읽을 것 (작성자 요약 말고 *이 파일들*)

1. `C:/My-AI-Security-Project/PII/ner/CLAUDE.md` — NER 자아성찰 룰 본문 (~120 lines)
2. `C:/My-AI-Security-Project/PII/ner/ai_research/_verification_request_template.md` — 검증 요청서 템플릿 (~110 lines)
3. `C:/My-AI-Security-Project/PII/ner/scripts/auto_verify_loop.py` — state machine + 가드 7개 (~430 lines)
4. `C:/finence/scripts/auto_verify_loop.py` — 원본 비교용 (~480 lines)
5. `C:/finence/ai_research/_verification_request_template.md` — 원본 비교용
6. `C:/finence/CLAUDE.md` 5/24 섹션 — 원본 룰 정합 검증용

---

## 이 산출물이 *주장*하는 것 (참인지 검증)

- **주장 A**: state machine 코드는 finance 그대로, 프롬프트만 NER 특화. (`auto_verify_loop.py:1-483` finance vs NER diff)
- **주장 B**: 가드 7개 보존 (raw 강제 / PASS_CONFIRMATION 검증 / raw 중복 거부 / ARTIFACT mention / fixes 강제 / 수렴 가드 / MAX_ITER+FINAL_AGENTS)
- **주장 C**: NER 어휘 PASS_CONFIRMATION 키워드 그룹이 stat/data/ops 3개 카테고리 다 커버
- **주장 D**: 진입 장벽(`CLAUDE.md §3.2`) 면제 3종이 finance보다 낮지만 의무 4종은 명확히 박힘
- **주장 E**: `_win_encoding` 의존 제거 + `sys.stdout.reconfigure(encoding="utf-8")` 으로 Windows 한글 출력 OK
- **주장 F**: 메타 자아성찰 시 본 인프라가 자기 자신을 공정하게 검증 가능 (자기참조 무력화 없음)

---

## 너가 답할 질문

1. **가짜 이식**: finance → NER 옮기면서 이름만 바뀌고 본질 안 옮긴 곳? (예: 5번 원칙 경로만 바꾸고 NER 하드원 교훈 실제 검증 안 들어감?)

2. **PASS_CONFIRMATION 키워드 그룹 적정성**: NER 어휘 그룹 hit 기준이 너무 느슨/엄격? 예시:
   - "F1 micro 0.766 측정함" — stat hit (F1, micro 둘 다)? hit 1개로 카운트?
   - "데이터 추가했음" — data hit? "데이터" 자체는 그룹에 없음, "라벨/dedup" 만 hit
   - dry-run: `_validate_pass_confirmation("PASS_CONFIRMATION: (a) 읽은 파일 train.py (b) 산식 macro F1 검증, BIO 라벨 일관성 확인, 사이드카 호환성 점검", require_focus_keywords=True)` 결과는?

3. **자기참조 함정**: 본 인프라가 자기 룰로 자기 검증 시 어느 가드가 무력화? (예: ARTIFACT mention 가드는 ARTIFACT 자체가 auto_verify_loop.py 이면 trivially 통과 — 가짜 raw 차단 효과 0?)

4. **state machine 엣지 케이스**:
   - attack round 1에서 SCRAP → 즉시 종료. 그런데 NER에서 인프라 빌드는 첫 라운드부터 SCRAP 받을 만큼 형편없을 가능성 낮음 → 가드 작동 검증 못함
   - final 3-agent 3/3 PASS 후 추가 ablation 발견되면? 재시작 메커니즘?

5. **finance 메타 자아성찰이 ESCALATE_NO_PROGRESS로 끝났던 이유**가 NER 메타 자아성찰에도 적용되나? 즉 본 메타 검증도 PASS 못 받을 가능성?

6. **NER CLAUDE.md §3.2 면제 조건의 함정**: "작은 ablation 1회 (raw 결과 self-check 만)" — 작성자가 자기 합리화로 매번 "이건 작은 ablation이라 면제"라 우회 가능?

7. **하드원 교훈 누락**: NER CLAUDE.md §2가 v2 실패 4개 원인 잡았지만, v1 → v3 plateau 트랩 (ep4→ep5 +0.001로 멈춤 = 외부 transfer 약점 가림) 은 §2에 명시적 박힘? 아니면 §3.4/§4.3에 흩어져 있음?

8. **PASS_CONFIRMATION focus 키워드 NER 그룹의 한 가지 빈 칸**:
   - stat 그룹: "macro", "micro" 들어있지만 "macro-F1", "micro-F1" 처럼 하이픈 표기는 lowercase 부분 매치되나? (`F1` 단독은 stat 그룹에 있음)
   - dry-run: `"macro-F1 0.766"` 안에 `"f1"` lowercase 매치되나?

9. **솔직히 이 인프라 가치 있나, 인지 자본 낭비인가?**

마지막: **VERDICT: PASS / REVISE (고칠 것 3개) / SCRAP (왜)** + 한 줄 근거.

REVISE 인 경우:
```
ISSUES_JSON:
[
  {"id":"r1-i01","severity":"high|med|low","category":"stat|data|ops","description":"...","file_refs":["path:line"]},
  ...
]
```

SCRAP 인 경우:
```
SCRAP_REASON: <근본 결함>
```

PASS 인 경우:
```
PASS_CONFIRMATION:
(a) 읽은 파일: ...
(b) 체크리스트 처리 결과: ...
(c) minor 무시 사항: ...
```
PASS_CONFIRMATION 본문 ≥80자. final 라운드는 stat/data/ops 중 2개 이상 다뤄야 함.
