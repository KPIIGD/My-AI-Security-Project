# LLM Security Framework — Korean PII Guardrail

## Active Development Note

The active implementation package is `korean_pii_guardrail_v0_2/`.
AI agents should start from `AGENTS.md` and `docs/index.md`, then follow
`korean_pii_guardrail_v0_2/AGENTS.md` for package work.

Treat `PII/` as the older five-layer research and evaluation stack. It is
reference material for the active package unless an integration task explicitly
changes scope.

> LiteLLM Gateway 환경에서 **한국어 특화 5계층 PII 가드레일 스택**을 구축·평가한 캡스톤 연구 결과물.
>
> **핵심 기여**: Layer 0 (한국어 정규화 + 키워드 사전, LLM 없음)가 GPT-4o-mini judge 대비 +8.99%p 더 잘 한국어 텍스트형 PII를 탐지하면서, 비용 $0 · 지연 220배 낮음.

---

## 레포 구조

```
PII/
├── layer_0/        Korean Normalizer + Detector (본 연구의 핵심 기여)
│   └── tests/      pytest suite (89 tests, CI-ready)
├── layer_1/        Microsoft Presidio (regex/NER)
├── layer_2/        AWS Bedrock Guardrails (ML-based, 50+ entities)
├── layer_3/        Lakera Guard v2 (prompt injection primary)
├── layer_4/        GPT-4o-mini Judge (LLM-as-Judge, post_call)
├── fuzzer/         Validity-First 한국어 PII 퍼저 v4 (91+ PII types)
├── evaluation/     LiteLLM Gateway 호출 평가기 + 집계 + 시각화
├── results/
│   ├── summaries/  최종 집계 JSON + RESULTS_10k_summary.md
│   ├── figures/    PNG (fig1~12) — 4-way / hardest PII / latency
│   ├── data/       Raw case-level JSON (10k × 4 configs)
│   ├── phase1/     Latency p99 + McNemar + FP test
│   └── phase3/     Ablation + L4 smart skip
├── config/         LiteLLM config.yaml + docker-compose.yml
└── datasets/       HuggingFace dataset card (CC BY-NC 4.0)

.github/workflows/   Layer 0 CI (Python 3.11/3.12)
scripts/             run_eval_pipeline.sh + build_pptx_v5.py
Makefile             Single-command reproduction (`make all`)
```

각 폴더에 자체 README 있음. 빠른 탐색은 아래 Index 참조.

## 🗂 Research Outcomes Index

| 질문 | 결과 | 파일 |
|---|---|---|
| 4-way 비교 (A/B/C/D) | C(Layer 0) 94.32% vs B(LLM judge) 90.96% | [run_e_final_summary.json](PII/results/summaries/run_e_final_summary.json) |
| KR_semantic head-to-head | C 96.39% vs B 87.40% (+8.99%p) | [fig11](PII/results/figures/fig11_kr_semantic_4way.png) |
| **통계적 유의성 (McNemar)** | B vs C: p < 1e-28 *** | [phase1/phase1_mcnemar.json](PII/results/phase1/phase1_mcnemar.json) |
| **Latency p99** | C 830ms vs B 4,819ms (5.8x 빠름) | [phase1/phase1_latency_precise.json](PII/results/phase1/phase1_latency_precise.json) |
| **False positive (정상 텍스트)** | 2% (98% clean pass) | [phase1/phase1_fp_test.json](PII/results/phase1/phase1_fp_test.json) |
| **Layer 0 내부 분해 (Ablation)** | Dict 96% 기여 / Norm 0.31%p | [phase3/phase3_ablation.json](PII/results/phase3/phase3_ablation.json) |
| **L4 Smart Skip** | 94% 호출 절감, 동일 detection | [phase3/phase3_l4_smart_skip.json](PII/results/phase3/phase3_l4_smart_skip.json) |
| **v4 퍼저 baseline robustness** | Δ TRUE ≤ 2%p (모든 슬라이스) | (Phase 2 — in progress) |
| 재현 방법 | `make all` (4시간, ~$5) | [Makefile](Makefile) |
| CI 테스트 | 89 unit tests, Py 3.11+3.12 | [.github/workflows](.github/workflows/layer_0_tests.yml) |
| 발표 PPTX (v5) | 16 슬라이드 | [AI_Gateway_가드레일_프로젝트_발표_v5.pptx](AI_Gateway_가드레일_프로젝트_발표_v5.pptx) |

## 아키텍처

```
User Input
    │
    ▼
┌─────────────────────┐
│ Layer 0 (Korean)    │   pre_call   한국어 정규화 + 33→42종 PII 키워드 사전
│ Normalizer+Detector │              (LLM 없음, ~10ms, $0)
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ Layer 1 Presidio    │   pre_call   regex + NER, 영어 중심
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ Layer 2 Bedrock     │   during_call  AWS 관리형 가드레일
└─────────────────────┘
    │
    ▼
┌─────────────────────┐
│ Layer 3 Lakera      │   pre_call    인젝션 전용 (PII는 0% catch)
└─────────────────────┘
    │
    ▼
    LLM (GPT/Claude/etc)
    │
    ▼
┌─────────────────────┐
│ Layer 4 GPT-4o      │   post_call   LLM-as-judge 최종 검증
│ Judge (mini)        │
└─────────────────────┘
```

## 핵심 결과 (10k stratified 평가, TRUE detection 기준)

### 4-way head-to-head

| Config | 구성 | TRUE | Real bypass |
|---|---|---:|---:|
| A) Baseline | L1~L3 (prod stack, no LLM) | 80.15% | 19.85% |
| B) Baseline + L4 | L1~L4 (+ GPT-4o-mini judge) | 90.96% | 9.04% |
| **C) With Layer 0** | **L0~L3 (no LLM)** | **94.32%** | **5.68%** |
| D) Full | L0~L4 (everything) | 97.23% | 2.77% |

### KR_semantic (한국어 텍스트형 PII, n=1,302)

| Config | TRUE | Bypass |
|---|---:|---:|
| A) Baseline | 49.62% | 50.38% |
| B) + LLM judge | 87.40% | 12.60% |
| **C) + Layer 0** | **96.39%** | **3.61%** |
| D) Full | 98.85% | 1.15% |

→ **Layer 0가 GPT-4o judge를 +8.99%p 능가** (KR_semantic slice)

### 비용/지연

| | L4 (GPT-4o-mini) | L0 (Korean normalizer) |
|---|---:|---:|
| Latency/건 | ~2,200ms | ~10ms (**220배 빠름**) |
| 비용/건 | ~$0.0001 | **$0** |
| 인터넷 의존 | 필요 (OpenAI API) | 없음 (로컬) |
| KR_semantic TRUE | 87.40% | **96.39%** |

### Layer 0 단독 차단 PII (11개 100% 차단)

`allergy, company, job_title, gps, degree, blood, marital, dept, jwt, diagnosis, religion` → 각각 0% bypass

자세한 결과는 [PII/results/summaries/RESULTS_10k_summary.md](PII/results/summaries/RESULTS_10k_summary.md).

## 재현 가이드

```bash
# 1. 컨테이너 기동 (LiteLLM + PostgreSQL + Presidio)
cd PII/config
cp ../../.env.example .env  # 시크릿 채움
docker compose up -d
docker start presidio-analyzer presidio-anonymizer

# 2. Layer 0 배포
bash -c "
  docker cp ../layer_0/korean_*.py litellm-litellm-1:/app/
  docker cp config.yaml litellm-litellm-1:/app/config.yaml
  docker compose restart litellm
"

# 3. 평가 실행 (전체 파이프라인은 PII/evaluation/README.md)
cd ../evaluation
python sample_10k.py
python guardrail_evaluator.py --input payloads_10k.json \
  --output eval_10k_l1l3.json \
  --layers "Presidio PII,Bedrock Guardrail,Lakera"
python cascade_evaluator.py --input eval_10k_l1l3.json \
  --output eval_10k_l1l4_full.json \
  --all --concurrency 5 --sleep 0.3
# ... (L0 포함도 동일)
python run_e_final_4way.py
python make_figures_final.py
```

## 환경 요구사항

- Docker Desktop (WSL2 backend)
- Python 3.12
- 환경변수: `OPENAI_API_KEY`, `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `BEDROCK_GUARDRAIL_ID`, `LAKERA_API_KEY`
- Python 패키지: `httpx`, `matplotlib`, `python-docx`, `python-pptx`

## 데이터 윤리

- 모든 PII seed는 synthetic. 실존 인물 매칭 확인 안 함.
- Account generator는 의도적으로 checksum/real-account validation 안 함 (계좌 enumeration 방지).
- 한국 금융기관 공식 체크섬 규칙은 공개 표준이 아니므로 "그럴듯한" 포맷만 모델링.

## 인용

```
@misc{korean_pii_guardrail_2026,
  title  = {Korean PII Guardrail: A Five-Layer Defense Stack with Normalization-First Layer 0},
  author = {민우 et al.},
  year   = {2026},
  note   = {LiteLLM Gateway + Presidio/Bedrock/Lakera/GPT-4o-mini judge, evaluated on 10k stratified payloads}
}
```

## License

TBD — 학술용. 상용 이용 시 문의.
