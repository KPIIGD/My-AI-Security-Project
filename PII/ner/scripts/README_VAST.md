# Vast.ai V100 학습 자동화 — 사용 가이드

> NEXT_SESSION.md task #7 "v4 학습 실행 + 외부 평가" 자동화.
> 한 명령으로 인스턴스 띄우기 → 학습 → 결과 회수 → 인스턴스 destroy.

---

## 사전 준비 (1회만)

### 1. Vast.ai 계정 + 결제

- https://vast.ai 가입
- 결제 정보 등록 후 **$10 credit 충전** (4-step ablation 비용 ~$1, 여유)
- 우상단 계정 → Account → **API Key** 복사

### 2. SSH 키 등록

- 로컬 PowerShell: `ssh-keygen -t ed25519` (있으면 스킵)
- `Get-Content $env:USERPROFILE\.ssh\id_ed25519.pub` 출력 복사
- Vast.ai 우상단 → Account → **SSH Keys** → 붙여넣기

### 3. PowerShell 환경

```powershell
# vastai CLI 설치
pip install vastai

# API key 등록 (한 번만)
vastai set api-key <PASTE_YOUR_KEY_HERE>

# Windows 10/11 은 ssh/scp 내장 — 별도 설치 불필요
ssh -V   # 버전 출력되면 OK
```

---

## 실행 (한 줄)

### 추천: 4-step ablation (~2.5h, ~$0.85)

```powershell
cd C:\My-AI-Security-Project\PII\ner
python scripts/vast_launch.py --mode ablation
```

자동으로:
1. V100 16GB 인스턴스 가장 싼 매물 검색 + 생성
2. SSH 준비 대기
3. `scripts/`, `data/external/`, `data/pii_ner_v3.json` 업로드
4. tmux 세션 안에서 ablation runner 실행 (4 step × 30분)
5. 매 60초 진행률 폴링 + log tail 출력
6. **v2 가드 트리거** (KLUE 외부 < 0.766) 또는 완료 시 자동 종료
7. `models/` + `results/` 다운로드 → `./vast_results/`
8. 인스턴스 destroy (비용 멈춤)

### 단일 학습 (~30분, ~$0.17)

```powershell
python scripts/vast_launch.py --mode single
```

### Dry-run (인스턴스 생성 X, 매물만 확인)

```powershell
python scripts/vast_launch.py --dry-run
```

---

## 옵션

| flag | 기본값 | 설명 |
|------|---|------|
| `--mode` | `ablation` | `single` 또는 `ablation` |
| `--abort-threshold` | `0.766` | KLUE 외부 macro-F1 임계값 (v2 트랩 가드) |
| `--max-price` | `0.50` | 시간당 최대 USD |
| `--image` | `pytorch/pytorch:2.3.0-cuda12.1-cudnn8-runtime` | Docker 이미지 |
| `--max-hours` | `4.0` | 총 timeout (초과 시 결과 회수 + destroy) |
| `--instance-id <ID>` `--skip-create` | — | 기존 인스턴스 재사용 (재시작 시) |
| `--skip-upload` | — | 업로드 스킵 (모델만 다시 학습할 때) |
| `--no-destroy` | — | 끝나도 인스턴스 살려둠 (**비용 계속 발생, 디버깅용**) |
| `--output` | `./vast_results` | 결과 다운로드 경로 |

---

## v2 트랩 가드 (자동 abort)

`klue_abort_callback.py` 의 `KlueAbortCallback` 이 매 epoch 끝에:
1. `data["klue_test"]` (5,000 sentence) eval
2. `macro_f1 < threshold` (기본 0.766) 이면 `control.should_training_stop = True`
3. `ABORTED.json` 으로 표시 → `final/` 모델 저장 스킵 (**v3 production 보호**)
4. `run_ablation_remote.py` 가 후속 step 자동 건너뜀 (비용 보호)

v2 가 KLUE 외부 0.764 → 0.664 박살난 패턴 재발 차단.

---

## 결과 파일 (다운로드 후 위치)

```
vast_results/
├── results/
│   ├── ablation_summary.json     ← step별 KLUE per-entity F1 요약
│   └── ablation.log              ← 전체 학습 로그
└── models/
    ├── pii_ner_v4_stepB/
    │   ├── final/                ← 모델 (체크포인트는 destroy 전 정리됨)
    │   ├── klue_test_results.json
    │   ├── klue_epoch_log.jsonl  ← 매 epoch 외부 transfer 추이
    │   └── test_results.json
    ├── pii_ner_v4_stepC/
    ├── pii_ner_v4_stepD/
    └── pii_ner_v4_stepE/
```

`ablation_summary.json` 예:
```json
{
  "abort_threshold": 0.766,
  "results": [
    {"step": "stepA_v3_baseline", "klue_test_per_entity_f1": {"NAME": 0.853, ...}},
    {"step": "stepB_org_pool_only", "aborted": false, "klue_test_metrics": {...}},
    {"step": "stepC_corpus_30k", ...},
    ...
  ]
}
```

---

## 다음 단계 (학습 완료 후)

### task #8 사이드카 swap

가장 좋은 step 의 `final/` 모델로 v3 → v4 교체:

```yaml
# C:\litellm\docker-compose.yml
volumes:
  - C:/My-AI-Security-Project/PII/ner/vast_results/models/pii_ner_v4_stepE/final:/models/ner_v3:ro
```

```powershell
docker compose restart pii-guardrail
docker logs --tail 20 litellm-pii-guardrail-1
```

### task #7 자아성찰 (의무)

```powershell
python scripts/auto_verify_loop.py init `
  --artifact vast_results/models/pii_ner_v4_stepE/final `
  --request ai_research/v4_training_result_verification_request.md `
  --log logs/verify/v4_training_result.log.md
```

NER CLAUDE.md §3.2 — leakage / 평가 누설 / 산식 일관성 검증 필수.

---

## 트러블슈팅

### "매물 없음"

```powershell
python scripts/vast_launch.py --max-price 1.0 --dry-run
```

검색 옵션 풀어서 매물 확인. 가격대 ↑ 또는 시간대 다르게 재시도.

### SSH 연결 실패

- Vast.ai 콘솔에서 인스턴스 status 확인 (running 인지)
- SSH 키 등록 안 됐을 수도 — 콘솔 → SSH Keys 확인
- `python scripts/vast_launch.py --instance-id <ID> --skip-create` 로 재시도

### 학습 도중 인스턴스 끊김

```powershell
# 1) 같은 인스턴스 살아있으면
python scripts/vast_launch.py --instance-id <ID> --skip-create --skip-upload

# 2) 죽었으면 새로 띄우고 처음부터
python scripts/vast_launch.py --mode ablation
```

`run_ablation_remote.py` 가 매 step 끝마다 `ablation_summary.json` 에 부분 저장하므로 진행 단계는 잃지 않음.

### 비용이 걱정될 때

```powershell
# 현재 떠 있는 인스턴스 확인
vastai show instances

# 강제 destroy
vastai destroy instance <ID>
```

`--no-destroy` 옵션 절대 평소엔 쓰지 말 것 (잊으면 시간당 청구 계속됨).
