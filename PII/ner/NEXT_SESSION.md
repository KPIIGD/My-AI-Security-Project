# NER v4 — VS Code 다음 세션 가이드

> **🔥 "v4" = NER 모델 v4** (klue/roberta-large fine-tuned). 가드레일 발표자료 pptx v4 아님.
> **본 작업 위치**: `C:\My-AI-Security-Project\PII\ner\` (NER 학습 폴더). 가드레일 자체는 `C:\litellm\` (별개).
> **목표**: v3 production (KLUE 외부 macro-F1 0.766, per-entity ORG 0.635 약점) → v4에서 ORG 보강.
>
> 2026-05-29 Cowork + VS Code 세션 후 업데이트. 본 문서는 **VS Code (Claude Code 또는 PowerShell)** 인계용. 직전 세션 기록은 `SESSION_HISTORY.md` 맨 아래 섹션 참조.
>
> **다음 세션 첫 명령 (사용자가 박을 것)**: `CLAUDE.md 읽고 NEXT_SESSION.md 읽고 시작`. 또는 `C:/My-AI-Security-Project/PII/ner/` 폴더에 들어가면 Claude Code가 CLAUDE.md 자동 로드 → §0 룰에 따라 본 파일 자동 읽음.

---

## 본 세션 직전 상태 (2026-05-29 Cowork 끝난 시점)

### 데이터셋 ✅ 풀 생성 완료
- `data/pii_ner_v4_full.json` (79.97 MB) — train 47,205 / val 5,901 / test 5,901 / klue_test 5,000
- 소스 비중: corpus4ev 50.6% / klue 35.8% / faker 11.9% / hard_neg 1.6%
- B-entity: ORG 29,858 / NAME 23,987 / ADDRESS 21,907 (v3 ORG 약점 보강 의도)

### 학습 자동화 ✅ 코드 완료, 실행 대기
- `scripts/klue_abort_callback.py` — v2 트랩 가드 TrainerCallback (KLUE < 0.766 → abort)
- `scripts/train_v4.py` — `--klue-abort-threshold` flag 추가
- `scripts/run_ablation_remote.py` — 4-step (B/C/D/E) 자동 실행 + 중간 저장
- `scripts/vast_launch.py` — Windows PowerShell 친화 V100 오케스트레이터
- `scripts/README_VAST.md` — 사전 준비 + 한 줄 실행 + 트러블슈팅

### Corrupt 파일 (사용자 수동 cleanup 필요)
```
data/pii_ner_v4.json        87 MB  (직전 세션 mid-write 잘림)
data/pii_ner_v4_30k.json    25 MB
data/pii_ner_v4_fast.json   50 MB  (본 세션 timeout 흔적)
data/pii_ner_v4_test.json   34 MB
tmp/pii_ner_v4_run.json     80 MB  (mount 안 tmp/ 디렉터리)
```
→ Windows ACL 로 sandbox 에서 `rm` 안 됨. PowerShell `Remove-Item` 로 직접.

---

## 실행 순서 (VS Code / PowerShell)

### 0. Corrupt 파일 정리
```powershell
cd C:\My-AI-Security-Project\PII\ner
Remove-Item data\pii_ner_v4.json, data\pii_ner_v4_30k.json, `
           data\pii_ner_v4_fast.json, data\pii_ner_v4_test.json -Force
Remove-Item -Recurse tmp\
```

### 1. Vast.ai 사전 준비 (1회)
`scripts/README_VAST.md` 의 "사전 준비" 섹션 참고:
- vastai 계정 + 결제 + API key
- SSH 키 등록
- `pip install vastai` + `vastai set api-key <KEY>`

### 2. 매물 검색 (옵션, 비용 0)
```powershell
python scripts/vast_launch.py --dry-run
```
검색 결과 상위 5개 인스턴스 출력. 매물 없으면 `--max-price 1.0` 풀어서 재시도.

### 3. 학습 실행 (~2.5h, ~$0.85)
```powershell
python scripts/vast_launch.py --mode ablation
```
자동 단계: V100 매물 검색·생성 → SSH 대기 → 업로드 → tmux 학습 → 60s 폴링 → 결과 다운로드 → destroy.

**단일 학습** (~30분, ~$0.17) 만 원하면 `--mode single`.

### 4. 결과 확인
```
vast_results/
├── results/ablation_summary.json    ← step별 KLUE per-entity F1 요약
├── results/ablation.log
└── models/
    ├── pii_ner_v4_stepB/{final/, klue_test_results.json, klue_epoch_log.jsonl}
    ├── pii_ner_v4_stepC/...
    ├── pii_ner_v4_stepD/...
    └── pii_ner_v4_stepE/...
```

`ablation_summary.json` 의 각 step 결과를 v3 baseline (NAME 0.853 / ADDR 0.692 / ORG 0.635) 와 비교 — best step 결정.

### 5. 자아성찰 (의무, ~30-60분, $0)
NER CLAUDE.md §3.2 "v4 본 학습 결과 + 외부 transfer 주장" trigger. 본 학습 결과 자아성찰 안 하면 사이드카 swap 금지.

```powershell
# verification request 작성 (NEXT_SESSION.md 직전 세션의 _verification_request_template.md 참고)
notepad ai_research\v4_training_result_verification_request.md

# 자아성찰 init
python scripts/auto_verify_loop.py init `
  --artifact vast_results/models/pii_ner_v4_<best_step>/final `
  --request ai_research/v4_training_result_verification_request.md `
  --log logs/verify/v4_training_result.log.md
```

검증 각도 (CLAUDE.md §4):
- **stat**: 평가 누설 (KLUE val 로 early stop + 같은 KLUE val 외부 보고)
- **data**: dedup 룰, char-level 변환, BIO 일관성
- **ops**: v2 실패 재발 (다중 변수 동시), plateau 트랩, 외부 transfer 환상

본 자아성찰 통과 = 3-Agent 3/3 PASS + raw 위조 가드 7개.

### 6. 사이드카 swap (자아성찰 PASS 후, ~15분)
```yaml
# C:\litellm\docker-compose.yml 수정
volumes:
  - C:/My-AI-Security-Project/PII/ner/vast_results/models/pii_ner_v4_<best_step>/final:/models/ner_v3:ro
```
```powershell
docker compose -f C:\litellm\docker-compose.yml restart pii-guardrail
docker logs --tail 30 litellm-pii-guardrail-1
# health check
curl http://localhost:8080/health
```

이것도 자아성찰 의무 (§3.2 사이드카 모델 swap).

---

## v2 트랩 모니터링 (자동화 완료)

본 세션에 `KlueAbortCallback` 으로 자동화됨. 매 epoch 끝 `klue_test` (5,000 sentence) eval → macro_f1 < 0.766 이면:
1. `control.should_training_stop = True` (학습 즉시 종료)
2. `ABORTED.json` 기록 — train_v4 가 `final/` 저장 스킵 (v3 production 보호)
3. `run_ablation_remote.py` 가 후속 step 자동 스킵 (비용 보호)

수동 모니터링 불요. 매 epoch 진행은 `models/<step>/klue_epoch_log.jsonl` 에 append.

---

## 비용/시간 예상

| 단계 | 시간 | 비용 |
|---|---:|---:|
| (0) Corrupt 정리 + Vast 셋업 | 15분 | $0 |
| (3) 4-step ablation 학습 | 2.5시간 | $0.85 (V100) |
| (4) 결과 분석 | 15분 | $0 |
| (5) 자아성찰 (학습) | 30-60분 | $0 |
| (6) 사이드카 swap + 검증 | 15분 + 자아성찰 30분 | $0 |
| **합계** | **~4.5시간** | **~$1** |

---

## 모든 task 상태

| # | 상태 | 내용 |
|---:|---|---|
| 1 | ✅ | 현재 NER v3 상태 풀 파악 |
| 2 | ✅ | KLUE val per-entity 분해 (NAME 0.853 / ADDR 0.692 / ORG 0.635) |
| 3 | ✅ | 데이터 인벤토리 확정 |
| 4 | ✅ | v4 데이터셋 prep (`data_prep_v4.py`) |
| 5 | ⏸️ | Conjunctive composite v2 (v3에 이미 들어감) |
| 6 | ✅ | v4 학습 스크립트 (`train_v4.py` + v2 가드 추가, 2026-05-29 Cowork) |
| **6.1** | ✅ | **v4 데이터셋 풀 생성 완료** (`pii_ner_v4_full.json` 79.97MB, 2026-05-29 Cowork) |
| **6.2** | ✅ | **Vast.ai 학습 자동화 패키지** (`vast_launch.py` + `run_ablation_remote.py` + `klue_abort_callback.py`, 2026-05-29 Cowork) |
| 7 | 🟡 | **v4 학습 실행 + 외부 평가** (VS Code 사용자 PowerShell 실행 대기) |
| 8 | ⏸️ | 사이드카 swap (자아성찰 PASS 후) |
| 9 | ⏸️ | v4-pre ablation 4-step (`run_ablation_remote.py` 안에서 자동) |
| 10 | ✅ | 자아성찰 인프라 (`auto_verify_loop.py`) |
| 11 | ✅ | 메타 자아성찰 (ESCALATE_NO_PROGRESS 정직 종료, 영구 면제 확정) |
| 12 | ✅ | data_prep_v4 자아성찰 2 round, 8 결함 닫음 |
| **13** | ✅ | **SESSION_HISTORY.md 기록** (2026-05-29 Cowork) |
