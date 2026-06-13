"""v4_1 데이터-변형 ablation (원격 GPU 실행).

검증 권고: silver/synth 가 KLUE val 을 실제로 올리나 격리 측정(v2 교훈: 변수 하나씩).
4 변형을 같은 setup 으로 학습 → klue_test per-entity F1 비교:
  baseline(47k 기존 v4) / +silver(51.8k) / +synth(87k) / +silver_synth(91.8k)
val/test/klue_test 는 4 변형 모두 동일(누설차단됨) → 공정 비교.

abort-threshold=0 : 전부 완주(production 교체 아닌 측정용이라 abort 불필요).
resume + incremental summary : 끊겨도 이어서, 부분결과 보존.

출력: results/ablation_summary.json  (vast_launch 가 이 파일 폴링)
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]   # /workspace/ner
VARIANTS = ["baseline", "silver", "synth", "silver_synth"]
SUMMARY = HERE / "results" / "ablation_summary.json"


def _klue_metrics(model_dir: Path) -> dict:
    kf = model_dir / "klue_test_results.json"
    if not kf.exists():
        ab = model_dir / "ABORTED.json"
        return {"error": "klue_test_results.json 없음", "aborted": ab.exists()}
    m = json.loads(kf.read_text(encoding="utf-8"))
    # f1 관련 키만 추림 (macro/micro + per-entity NAME/ADDRESS/ORG)
    return {k: v for k, v in m.items() if "f1" in k.lower()}


def main() -> None:
    (HERE / "results").mkdir(exist_ok=True)
    (HERE / "logs").mkdir(exist_ok=True)
    results = json.loads(SUMMARY.read_text(encoding="utf-8")) if SUMMARY.exists() else {}

    for v in VARIANTS:
        if v in results and "error" not in results[v]:
            print(f"[skip] {v} 이미 완료: {results[v]}", flush=True)
            continue
        data = HERE / "data" / f"pii_ner_v4_1_{v}.json"
        out = HERE / "models" / f"v4_1_{v}"
        if not data.exists():
            results[v] = {"error": f"데이터 없음: {data.name}"}
            SUMMARY.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  ⚠️ {results[v]}", flush=True)
            continue
        print(f"\n=== [{v}] 학습 시작 ({data.name}) ===", flush=True)
        subprocess.run(
            [sys.executable, str(HERE / "scripts" / "train_v4.py"),
             "--data", str(data), "--output", str(out),
             "--klue-abort-threshold", "0",
             "--klue-abort-log", str(HERE / "logs" / f"{v}_klue.jsonl")],
            cwd=str(HERE),
        )
        results[v] = _klue_metrics(out)
        SUMMARY.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"  → [{v}] KLUE: {results[v]}", flush=True)

    print("\n=== ablation 완료 ===", flush=True)
    print(json.dumps(results, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
