"""FastAPI 파이프라인 API — n8n(Docker)이 HTTP로 호출해 데이터센터 단계를 실행한다.

왜: n8n 컨테이너는 호스트 파이썬/스크립트를 직접 못 돌린다. 그래서 무거운 파이썬
(torch/milvus/스크립트)은 호스트에 두고, n8n 은 이 API 를 HTTP 로 호출만 한다(오케스트레이션).

전체 자동 파이프라인 (n8n 노드 순서):
  collect → distill → stats → leakage_gate → curate → export → commit_push

실행 (호스트):
  cd C:\\My-AI-Security-Project\\PII\\ner
  python datacenter/pipeline_api.py            # http://0.0.0.0:8000  (docs: /docs)

n8n HTTP 노드에서:  http://host.docker.internal:8000/<endpoint>
"""
from __future__ import annotations

import datetime
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

from fastapi import FastAPI

DC = Path(__file__).resolve().parent          # .../datacenter
PYNER = DC.parent                              # .../PII/ner  (스크립트 실행 cwd)
DB = DC / "ner_datacenter.db"
DATA = PYNER / "data"                          # 큐레이션 결과 위치
DATA_REPO = "https://github.com/KPIIGD/My-AI-Security-Project-data.git"
DATA_CLONE = Path("C:/tmp/ner-data-repo")

app = FastAPI(title="NER Datacenter Pipeline API", version="0.2")


def run(script: str, *args: str, timeout: int = 3600) -> dict:
    """datacenter/<script> 를 서브프로세스로 실행하고 요약 반환."""
    cmd = [sys.executable, str(DC / script), *args]
    p = subprocess.run(
        cmd, cwd=PYNER, capture_output=True, text=True,
        encoding="utf-8", errors="replace", timeout=timeout,
    )
    return {
        "script": script,
        "args": list(args),
        "ok": p.returncode == 0,
        "returncode": p.returncode,
        "stdout_tail": (p.stdout or "")[-2000:],
        "stderr_tail": (p.stderr or "")[-500:],
    }


def _git(*a, **k):
    return subprocess.run(["git", *a], capture_output=True, text=True,
                          encoding="utf-8", errors="replace", timeout=180, **k)


@app.get("/health")
def health():
    return {"ok": True, "service": "datacenter-pipeline"}


@app.get("/stats")
def stats():
    # 정확한 실 건수(COUNT). 16GB DB라 첫 호출 ~수초(이후 OS 캐시로 빠름).
    con = sqlite3.connect(DB)
    out = {}
    for t in ("ner_examples", "weak_examples", "gazetteers"):
        try:
            out[t] = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
        except Exception:
            out[t] = None
    con.close()
    return out


@app.post("/collect")
def collect(limit: int = 200, only: str = ""):
    """① 수집 — collector 실행 (소스별 limit 상한) + content_hash dedup.
    데모 안정성: 기본은 호출자가 only=synth_conv_name 처럼 지정(웹 의존X)."""
    args = (["--only", only] if only else []) + ["--limit", str(limit)]
    return run("run_collectors.py", *args, timeout=1800)


@app.post("/distill")
def distill(n: int = 30, max_cost: float = 0.05):
    """② 라벨링/정제 — weak → gpt-4o-mini 재라벨(silver).
    ⚠️ 비용 발생: 안전망 기본 n=30, max_cost=$0.05.
    OPENAI_API_KEY(env 또는 C:\\litellm\\.env) 없으면 스크립트가 종료 → ok=false 로 보고하지만
    HTTP 200 이라 파이프라인은 계속 진행."""
    return run("distill_silver.py", "--n", str(n), "--max-cost", str(max_cost), timeout=1800)


@app.post("/leakage_gate")
def leakage_gate():
    """④ KLUE test 누수 검사."""
    return run("leakage_gate.py")


@app.post("/curate")
def curate(source: str = "weak", limit: int = 2000, threshold: float = 0.92):
    """③ Milvus 다양성 큐레이션 (임베딩 캐시 있으면 빠름)."""
    return run("diversity_curate.py", "--source", source,
               "--limit", str(limit), "--threshold", str(threshold))


@app.post("/export")
def export():
    """⑤ 라이선스+누수 필터 → 깨끗한 학습 후보셋 export."""
    return run("export_clean.py")


@app.post("/commit_push")
def commit_push():
    """⑥ 큐레이션 결과(data/curated_*.json)를 private 데이터 repo에 자동 commit+push."""
    # clone or pull
    if not (DATA_CLONE / ".git").exists():
        _git("clone", DATA_REPO, str(DATA_CLONE))
    else:
        _git("-C", str(DATA_CLONE), "pull", "--quiet", "--no-edit")
    # copy curated outputs
    dest = DATA_CLONE / "curated"
    dest.mkdir(parents=True, exist_ok=True)
    copied = []
    for f in sorted(DATA.glob("curated_*.json")):
        shutil.copy(f, dest / f.name)
        copied.append(f.name)
    # commit + push
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    _git("-C", str(DATA_CLONE), "add", "-A")
    commit = _git("-C", str(DATA_CLONE), "-c", "user.name=KPIIGD",
                  "-c", "user.email=minwoo123451@naver.com",
                  "commit", "-q", "-m", f"auto(n8n): 큐레이션 결과 업데이트 {ts}")
    nothing = "nothing to commit" in (commit.stdout + commit.stderr).lower()
    push = _git("-C", str(DATA_CLONE), "push", "--quiet") if not nothing else None
    return {
        "copied": copied,
        "committed": commit.returncode == 0,
        "nothing_to_commit": nothing,
        "pushed": (push.returncode == 0) if push else "skipped(no change)",
        "ok": nothing or (push is not None and push.returncode == 0),
        "repo": "KPIIGD/My-AI-Security-Project-data",
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
