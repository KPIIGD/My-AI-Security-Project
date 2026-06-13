"""GPU ablation 진행 추적 — vast 인스턴스 상태 + 비용 + 원격 ablation 결과.

사용 (PowerShell, C:/My-AI-Security-Project/PII/ner):
  python scripts/ablation_status.py            # 1회
  python scripts/ablation_status.py --watch    # 30초마다 갱신 (Ctrl+C 종료)
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import time
from pathlib import Path

SSH_KEY = os.path.expanduser("~/.ssh/id_ed25519_vastai")
REMOTE = "/workspace/ner/results"
VARIANTS = ["baseline", "silver", "synth", "silver_synth"]


def _instances() -> list[dict]:
    r = subprocess.run(["vastai", "show", "instances", "--raw"], capture_output=True, text=True)
    try:
        return json.loads(r.stdout)
    except Exception:
        return []


def _ssh(host: str, port, cmd: str, timeout: int = 20) -> str:
    full = ["ssh", "-i", SSH_KEY, "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null", "-o", f"ConnectTimeout={timeout}",
            "-p", str(port), f"root@{host}", cmd]
    try:
        return subprocess.run(full, capture_output=True, text=True, timeout=timeout + 10).stdout
    except Exception:
        return ""


def _fmt_klue(m: dict) -> str:
    if "error" in m:
        return f"❌ {m['error']}"
    # macro + per-entity 우선 추림
    macro = m.get("klue_test_macro_f1") or m.get("macro_f1")
    parts = []
    if macro is not None:
        parts.append(f"macro {macro:.3f}")
    for ent in ("NAME", "ADDRESS", "ORG"):
        for k in (f"klue_test_{ent}_f1", f"{ent}_f1", f"klue_test_{ent.lower()}_f1"):
            if k in m:
                parts.append(f"{ent} {m[k]:.3f}"); break
    return "  ".join(parts) or str(m)


def show() -> bool:
    insts = _instances()
    if not insts:
        print("○ 실행 중인 인스턴스 없음 (학습 종료/미시작).")
        local = Path(__file__).resolve().parents[1] / "vast_results" / "results" / "ablation_summary.json"
        if local.exists():
            print(f"  로컬 결과 {local}:")
            for v, m in json.loads(local.read_text(encoding="utf-8")).items():
                print(f"    {v:14} {_fmt_klue(m)}")
        return False

    i = insts[0]
    host, port = i.get("ssh_host"), i.get("ssh_port")
    dur = i.get("duration", 0) or 0
    cost = dur / 3600 * (i.get("dph_total", 0) or 0)
    print(f"● 인스턴스 {i['id']}  {i.get('actual_status')}  {i.get('gpu_name')}  "
          f"${i.get('dph_total', 0):.3f}/h  경과 {dur/60:.0f}분  ~${cost:.2f}")

    summ = _ssh(host, port, f"cat {REMOTE}/ablation_summary.json 2>/dev/null")
    done = {}
    if summ.strip():
        try:
            done = json.loads(summ)
        except Exception:
            pass
    for v in VARIANTS:
        if v in done:
            print(f"  ✅ {v:14} {_fmt_klue(done[v])}")
        else:
            print(f"  ⏳ {v:14} 대기/학습중")
    # 현재 학습 로그 끝줄
    tail = _ssh(host, port, f"tail -2 {REMOTE}/ablation.log 2>/dev/null")
    if tail.strip():
        last = [l for l in tail.splitlines() if l.strip()]
        if last:
            print(f"  log: {last[-1][:90]}")
    return True


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch", action="store_true")
    ap.add_argument("--interval", type=int, default=30)
    args = ap.parse_args()
    if not args.watch:
        show(); return
    print(f"=== ablation watch ({args.interval}s 간격, Ctrl+C 종료) ===")
    try:
        while True:
            print(f"\n--- {time.strftime('%H:%M:%S') if False else ''} ---".rstrip(" -"))
            if not show():
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nwatch 중단 (학습은 GPU에서 계속).")


if __name__ == "__main__":
    main()
