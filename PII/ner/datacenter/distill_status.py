"""증류(distill_silver) 진행률 확인.

사용 (PowerShell, C:/My-AI-Security-Project/PII/ner):
  python datacenter/distill_status.py            # 1회 스냅샷
  python datacenter/distill_status.py --watch    # 5초마다 갱신 (Ctrl+C 종료)
  python datacenter/distill_status.py --watch --interval 10
"""
from __future__ import annotations

import argparse
import sqlite3
import subprocess
import time
from pathlib import Path

_DB = Path(__file__).resolve().parent / "ner_datacenter.db"
TARGET = 50000              # distill_silver --n 기본값
COST_PER = 2.6 / 50000     # 문장당 추정 비용(실측 기반, gpt-4o-mini)


def snapshot() -> tuple[int, int]:
    c = sqlite3.connect(str(_DB), timeout=30)
    n = c.execute("SELECT COUNT(*) FROM ner_examples WHERE source='distill_silver'").fetchone()[0]
    e = c.execute("SELECT COALESCE(SUM(n_entities),0) FROM ner_examples WHERE source='distill_silver'").fetchone()[0]
    c.close()
    return n, e


def is_alive() -> bool | None:
    """distill_silver 프로세스가 살아있나 (best-effort)."""
    try:
        out = subprocess.run(
            ["wmic", "process", "where", "name='python.exe'", "get", "CommandLine"],
            capture_output=True, text=True, timeout=10,
        ).stdout
        return "distill_silver" in out
    except Exception:
        return None


def _bar(pct: float, width: int = 30) -> str:
    f = int(pct / 100 * width)
    return "█" * f + "░" * (width - f)


def show(prev: int | None = None, dt: float | None = None) -> int:
    n, e = snapshot()
    pct = 100 * n / TARGET
    cost = n * COST_PER
    line = f"{_bar(pct)} {pct:5.1f}%  {n:,}/{TARGET:,}  엔티티 {e:,}  ~${cost:.2f}"
    if prev is not None and dt:
        rate = (n - prev) / dt
        if rate > 0:
            eta = (TARGET - n) / rate / 60
            line += f"  {rate:.1f}/s  ETA {eta:.0f}분"
        else:
            line += "  (멈춤?)"
    a = is_alive()
    line += "  ● 돌는중" if a else ("  ○ 완료/중단" if a is False else "")
    print(line, flush=True)
    return n


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--watch", action="store_true", help="주기적 갱신")
    ap.add_argument("--interval", type=int, default=5, help="갱신 주기(초)")
    args = ap.parse_args()

    if not args.watch:
        show()
        return

    print(f"=== 증류 진행 watch (목표 {TARGET:,}, {args.interval}초 간격, Ctrl+C 종료) ===")
    prev = None
    try:
        while True:
            prev_now = show(prev, args.interval)
            if is_alive() is False and prev_now >= TARGET - 50:
                print("→ 증류 종료(목표 도달).")
                break
            prev = prev_now
            time.sleep(args.interval)
    except KeyboardInterrupt:
        print("\nwatch 중단 (증류 자체는 백그라운드에서 계속 진행).")


if __name__ == "__main__":
    main()
