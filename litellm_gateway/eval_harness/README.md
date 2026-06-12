# eval_harness — "LLM 이 한 것 전부 평가" 하네스

> 목적: 이 캡스톤의 핵심 측정(Layer4 GPT-4o Judge)·멀티-AI 토론 등 **LLM 이 내린 모든 판정을 자동 평가**.
> 원칙: **AI 판정 ≠ 진실.** deterministic 우선 → 독립 모델 교차검증 → 사람 5-10% 재검토.
> (Claude Code 스킬 [ai-judgment-check] 와 짝.)

## 구성
| 파일 | 용도 |
|------|------|
| `judge_everything.py` | 메인. Layer4/파이프라인 판정을 독립 무료모델로 재판정 + 토론 로그 group-think 점검 → 리포트 |
| `llm_judge_wrapper.py` | deepeval 용 무료모델 래퍼(`FreeJudge`) — G-Eval 등을 $0 으로 |
| `reports/` | 생성된 리포트 (md + json) |

## 빠른 시작
```bash
# 스키마 확인
python eval_harness/judge_everything.py --source eval_full.json --probe

# Layer4 판정 30건을 독립 모델(groq_gptoss)로 재판정 + 토론 로그 점검
python eval_harness/judge_everything.py --source eval_full.json --sample 30

# 토론 로그만
python eval_harness/judge_everything.py --debate-logs
```

## 무엇을 측정하나
1. **파이프라인 recall** — gold(PII 존재) 대비 탐지율.
2. **독립 모델 recall (judge-the-judge)** — 별도 모델이 같은 입력에서 BLOCK 판정하는 비율 = 판정 난이도/신뢰도 프록시.
3. **파이프라인 ↔ 독립 일치율.**
4. 🔴 **확증된 실제 우회** — 파이프라인 ALLOW(우회) & 독립 BLOCK → 가드레일이 놓친 진짜 우회.
5. 👤 **사람 검토 큐** — 불일치 케이스 (5-10% 재검토 룰).
6. 토론 로그 **group-think/에러율.**

## 안전 규칙
- raw PII 는 외부 모델에 보내기 전 `[PII]` 로 **마스킹** (PUBLIC repo + 외부 API 노출 방지).
- 검증 모델은 프로젝트 BYPASS 정의를 모를 수 있음 → deterministic(정규식/사전) 결과와 반드시 교차.
- 리포트 결과도 *측정*일 뿐 — 불일치/확증우회는 사람이 최종 판단.

## deepeval (옵션)
`pip install -r eval_harness/requirements.txt` 후 `llm_judge_wrapper.FreeJudge` 로 G-Eval 메트릭을 무료모델로 구동.

## 자동화
- 자동커밋 스케줄러와 별개로, eval 갱신 시 `judge_everything.py` 를 돌려 `reports/` 에 누적.
- 새 eval 결과(`eval_*.json`) 생성 → 이 하네스로 판정 신뢰도 회귀 점검 → 대시보드/논문에 반영.
