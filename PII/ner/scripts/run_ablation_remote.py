"""v4 ablation 4-step runner — Vast.ai 인스턴스에서 직접 실행.

NEXT_SESSION.md task #9 "v4-pre ablation 5-step" 자동화.
CLAUDE.md §3.2 미해결 자아성찰 R1-i02 (corpus 비중), R1-i04 (NAME 희석),
R1-i05/R2-i07 (one-variable), R2-i04 (confusable trade-off) 를 단일 변수 변경으로 닫음.

Step 정의 (cumulative one-variable):
  step A: v3 baseline               — 학습 스킵, v3 모델 그대로 KLUE 평가만 (외부 기준선)
  step B: v3 + ORG pool 확장만       — corpus 비활성, Faker v3 그대로 (10k)
  step C: B + corpus4ev 30k          — R1-i02 측정
  step D: C + exclude_confusable     — R2-i04 측정
  step E: D + Faker 10k→5k (default) — R1-i04 NAME 희석 vs 균형 trade-off 측정

각 step:
  1) data_prep_v4.py 호출해 데이터셋 생성 (output 경로 step별)
  2) train_v4.py 호출해 학습 (--klue-abort-threshold 적용)
  3) klue_test_results.json 회수 → results/ablation_summary.json

사용:
  cd /workspace/ner
  python scripts/run_ablation_remote.py --abort-threshold 0.766

Vast.ai 환경 사전조건:
  - /workspace/ner/scripts/ 에 모든 .py 업로드 완료
  - /workspace/ner/data/external/ + data/pii_ner_v3.json 업로드 완료
  - GPU + transformers/torch/seqeval/faker/pyarrow 설치 완료
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # /workspace/ner
SCRIPTS = ROOT / "scripts"
DATA = ROOT / "data"
MODELS = ROOT / "models"
RESULTS = ROOT / "results"

# step 정의 — (이름, data_prep_v4 인자, 변경 변수 설명)
STEPS = [
    # step A 는 학습 스킵 (v3 baseline 비교 reference 만 사용)
    {
        "name": "stepB_org_pool_only",
        "prep_args": ["--corpus4ev-limit", "0", "--faker-baseline", "10000"],
        "data_file": "pii_ner_v4_stepB.json",
        "model_dir": "pii_ner_v4_stepB",
        "var_changed": "+ ORG pool 24→2,795 (Faker v3 10k 유지, corpus 비활성)",
    },
    {
        "name": "stepC_corpus_30k",
        "prep_args": ["--corpus4ev-limit", "30000", "--faker-baseline", "10000"],
        "data_file": "pii_ner_v4_stepC.json",
        "model_dir": "pii_ner_v4_stepC",
        "var_changed": "+ corpus4everyone 30k (R1-i02 측정: corpus 비중 50% 영향)",
    },
    {
        "name": "stepD_exclude_confusable",
        "prep_args": [
            "--corpus4ev-limit", "30000",
            "--exclude-confusable",
            "--faker-baseline", "10000",
        ],
        "data_file": "pii_ner_v4_stepD.json",
        "model_dir": "pii_ner_v4_stepD",
        "var_changed": "+ AF/EV/CV 제외 (R2-i04 측정: confusable trade-off)",
    },
    {
        "name": "stepE_faker_5k_default",
        "prep_args": [
            "--corpus4ev-limit", "30000",
            "--exclude-confusable",
            "--faker-baseline", "5000",
        ],
        "data_file": "pii_ner_v4_stepE.json",
        "model_dir": "pii_ner_v4_stepE",
        "var_changed": "+ Faker 10k→5k (R1-i04 측정: NAME 희석 vs 균형)",
    },
]


def run(cmd: list[str], cwd: Path | None = None, env: dict | None = None) -> int:
    """subprocess + live tail. 실패하면 return code 비0."""
    print(f"\n$ {' '.join(cmd)}\n  cwd={cwd or os.getcwd()}", flush=True)
    proc = subprocess.run(cmd, cwd=str(cwd) if cwd else None, env=env)
    print(f"  exit={proc.returncode}", flush=True)
    return proc.returncode


def prep_dataset(step: dict, force: bool) -> Path:
    out = DATA / step["data_file"]
    if out.exists() and not force:
        print(f"[prep] {out.name} 존재 → 스킵 (재생성하려면 --force-prep)")
        return out

    cmd = [
        sys.executable, "-u", str(SCRIPTS / "data_prep_v4.py"),
        "--output", str(out),
    ] + step["prep_args"]
    rc = run(cmd, cwd=SCRIPTS)
    if rc != 0 or not out.exists():
        raise RuntimeError(f"data_prep 실패: {step['name']}")
    return out


def train_step(
    step: dict,
    data_path: Path,
    abort_threshold: float,
    epochs_phase2: int,
    batch: int,
) -> dict:
    model_out = MODELS / step["model_dir"]
    cmd = [
        sys.executable, "-u", str(SCRIPTS / "train_v4.py"),
        "--data", str(data_path),
        "--output", str(model_out),
        "--epochs-phase2", str(epochs_phase2),
        "--batch", str(batch),
        "--klue-abort-threshold", str(abort_threshold),
    ]
    t0 = time.time()
    rc = run(cmd, cwd=SCRIPTS)
    dt = time.time() - t0

    result = {
        "step": step["name"],
        "var_changed": step["var_changed"],
        "data_file": step["data_file"],
        "model_dir": step["model_dir"],
        "train_seconds": round(dt, 1),
        "train_exit_code": rc,
        "aborted": False,
        "klue_test_metrics": None,
        "epoch_log": [],
    }

    aborted_marker = model_out / "ABORTED.json"
    klue_results = model_out / "klue_test_results.json"
    epoch_log = model_out / "klue_epoch_log.jsonl"

    if aborted_marker.exists():
        result["aborted"] = True
        result["abort_summary"] = json.load(aborted_marker.open(encoding="utf-8"))
    if klue_results.exists():
        result["klue_test_metrics"] = json.load(klue_results.open(encoding="utf-8"))
    if epoch_log.exists():
        result["epoch_log"] = [
            json.loads(l) for l in epoch_log.read_text(encoding="utf-8").splitlines() if l.strip()
        ]

    return result


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument(
        "--abort-threshold",
        type=float,
        default=0.766,
        help="KLUE 외부 macro-F1 임계값. v3 baseline 0.766. v2 트랩 가드.",
    )
    p.add_argument("--epochs-phase2", type=int, default=5)
    p.add_argument("--batch", type=int, default=16)
    p.add_argument("--force-prep", action="store_true", help="기존 데이터셋 무시하고 재생성")
    p.add_argument(
        "--steps",
        default="B,C,D,E",
        help="실행할 step (콤마 구분). 예: B,E 만 돌리려면 --steps B,E",
    )
    p.add_argument(
        "--summary",
        default=None,
        help="요약 결과 JSON 경로 (기본 results/ablation_summary.json)",
    )
    args = p.parse_args()

    RESULTS.mkdir(parents=True, exist_ok=True)
    summary_path = Path(args.summary) if args.summary else RESULTS / "ablation_summary.json"

    selected = set(args.steps.upper().split(","))
    steps_to_run = [
        s for s in STEPS if s["name"].split("_")[0][-1].upper() in selected
    ]
    print(f"[runner] steps: {[s['name'] for s in steps_to_run]}")
    print(f"[runner] abort_threshold = {args.abort_threshold}")
    print(f"[runner] epochs_phase2 = {args.epochs_phase2}, batch = {args.batch}")

    all_results = []
    t_total = time.time()

    # v3 baseline reference 기록 (학습 X, NEXT_SESSION.md task #2 결과 인용)
    all_results.append({
        "step": "stepA_v3_baseline",
        "var_changed": "(reference) v3 production = klue/roberta-large fine-tuned",
        "klue_test_per_entity_f1": {
            "NAME": 0.853,
            "ADDRESS": 0.692,
            "ORG": 0.635,
        },
        "klue_test_macro_f1": 0.766,
        "source": "NEXT_SESSION.md task #2 (v3 KLUE val per-entity 분해)",
    })

    for step in steps_to_run:
        print(f"\n{'=' * 70}\n[step {step['name']}] {step['var_changed']}\n{'=' * 70}")
        try:
            data_path = prep_dataset(step, force=args.force_prep)
            result = train_step(
                step,
                data_path,
                abort_threshold=args.abort_threshold,
                epochs_phase2=args.epochs_phase2,
                batch=args.batch,
            )
        except Exception as exc:
            result = {
                "step": step["name"],
                "var_changed": step["var_changed"],
                "error": f"{type(exc).__name__}: {exc}",
            }
        all_results.append(result)

        # 중간 저장 (인스턴스 죽어도 부분 복구 가능)
        partial = {
            "ablation_runner": "v4 4-step",
            "abort_threshold": args.abort_threshold,
            "elapsed_seconds": round(time.time() - t_total, 1),
            "results": all_results,
        }
        with summary_path.open("w", encoding="utf-8") as f:
            json.dump(partial, f, ensure_ascii=False, indent=2)
        print(f"\n[checkpoint] {summary_path} ({len(all_results)} steps recorded)")

        # v2 트랩 가드: 직전 step 이 aborted 되면 후속 step 도 자동 중단
        # (보통 후속도 비슷한 데이터에 더 변수 추가라 더 나쁠 확률 높음 → 비용 절약)
        if result.get("aborted"):
            print(f"\n[runner] {step['name']} 가드 발동 → 후속 step 자동 중단 (비용 보호)")
            break

    final = {
        "ablation_runner": "v4 4-step",
        "abort_threshold": args.abort_threshold,
        "elapsed_seconds": round(time.time() - t_total, 1),
        "results": all_results,
    }
    with summary_path.open("w", encoding="utf-8") as f:
        json.dump(final, f, ensure_ascii=False, indent=2)
    print(f"\n[done] {summary_path} ({final['elapsed_seconds']:.0f}s total)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
