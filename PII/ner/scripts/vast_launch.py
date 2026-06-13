"""Vast.ai V100 인스턴스 자동 띄우기 + v4 ablation 학습 + 결과 회수.

Windows PowerShell 친화 — vastai CLI + 내장 ssh/scp 만 사용 (rsync 불필요).

전체 흐름:
  1. vastai 로 V100 16GB 인스턴스 검색 (가격 정렬)
  2. 생성 후 SSH 준비될 때까지 대기
  3. scp 로 scripts/ + data/external/ + data/pii_ner_v3.json 업로드
     (전체 5GB 정도. 인터넷 환경에 따라 5~15분)
  4. ssh 로 의존성 설치 + run_ablation_remote.py 백그라운드 tmux 실행
  5. results/ablation_summary.json 폴링 (60s 간격)
  6. 완료 후 models/ + results/ 다운로드
  7. vastai destroy instance (인스턴스 비용 멈춤)

사용 (PowerShell):
  pip install vastai
  vastai set api-key <YOUR_KEY>
  cd C:\My-AI-Security-Project\PII\ner
  python scripts/vast_launch.py --mode ablation

  # dry run (인스턴스 생성 X, 검색 결과만 보기)
  python scripts/vast_launch.py --dry-run

  # 기존 인스턴스 재사용 (재시작 시)
  python scripts/vast_launch.py --instance-id 1234567 --skip-create
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

# 업로드 대상 (mount 기준 상대경로)
UPLOAD_ITEMS = [
    "scripts/",
    "data/external/",
    "data/pii_ner_v3.json",  # data_prep_v4 의 KLUE 캐시
    "data/korea_admin.json",  # gen_faker 의 주소 페어 데이터
]

REMOTE_BASE = "/workspace/ner"
# 등록된 vast SSH 키(vastai-ner-train-20260511)의 로컬 private key.
# 비표준 이름이라 -i 로 명시 안 하면 ssh 가 기본키만 시도→publickey 거부.
SSH_KEY = os.path.expanduser("~/.ssh/id_ed25519_vastai")


def sh(cmd, **kwargs):
    """프로세스 동기 실행. 출력 stdout 으로 실시간 stream."""
    if isinstance(cmd, str):
        print(f"$ {cmd}", flush=True)
        return subprocess.run(cmd, shell=True, **kwargs)
    print("$ " + " ".join(str(c) for c in cmd), flush=True)
    return subprocess.run(cmd, **kwargs)


def sh_out(cmd) -> str:
    """동기 실행 + stdout 캡처. encoding 명시(Windows cp949 한국어 디코드 크래시 방지)."""
    kw = {"capture_output": True, "text": True, "encoding": "utf-8", "errors": "replace"}
    if isinstance(cmd, str):
        r = subprocess.run(cmd, shell=True, **kw)
    else:
        r = subprocess.run(cmd, **kw)
    if r.returncode != 0:
        sys.stderr.write(r.stderr or "")
        raise RuntimeError(f"command failed: {cmd}")
    return r.stdout or ""


def vastai_search(min_vram: int = 16, max_price: float = 0.50) -> list[dict]:
    """RTX 3090(24GB) 이상, 시간당 max_price 이하 매물 정렬.

    V100 은 가용성 낮음 → 3090 사용(roberta-large 학습 충분, v3 도 3090). verified 제거
    (verified 매물이 자주 0개라 학습을 막음). reliability>=0.95 로 품질 보장.
    """
    query = f"gpu_name=RTX_3090 num_gpus=1 cuda_max_good>=11.8 reliability>=0.95 inet_down>=100 dph<={max_price} rentable=true"
    out = sh_out(["vastai", "search", "offers", query, "--raw"])
    offers = json.loads(out)
    # 가격순 정렬
    offers = sorted(offers, key=lambda o: o.get("dph_total", 999))
    print(f"  검색 결과 상위 5개:")
    for o in offers[:5]:
        print(
            f"    id={o['id']} GPU={o['gpu_name']}x{o['num_gpus']} "
            f"VRAM={o.get('gpu_ram', 0)/1024:.1f}GB ${o['dph_total']:.3f}/h "
            f"@ {o.get('geolocation', '?')}"
        )
    return offers


def vastai_create(offer_id: int, image: str) -> int:
    """인스턴스 생성. instance_id 반환."""
    out = sh_out([
        "vastai", "create", "instance", str(offer_id),
        "--image", image,
        "--disk", "50",
        "--ssh", "--direct",
        "--raw",
    ])
    info = json.loads(out)
    inst_id = info.get("new_contract") or info.get("id")
    print(f"  생성됨: instance_id={inst_id}")
    return int(inst_id)


def vastai_show(instance_id: int) -> dict:
    out = sh_out(["vastai", "show", "instance", str(instance_id), "--raw"])
    return json.loads(out)


def wait_ssh_ready(instance_id: int, timeout_s: int = 600) -> tuple[str, int]:
    """SSH 준비될 때까지 폴링. (host, port) 반환."""
    print(f"  SSH 준비 대기 (timeout {timeout_s}s)...")
    t0 = time.time()
    while time.time() - t0 < timeout_s:
        try:
            info = vastai_show(instance_id)
            status = info.get("actual_status") or info.get("status_msg") or "?"
            ssh_host = info.get("ssh_host")
            ssh_port = info.get("ssh_port")
            print(f"    [{int(time.time()-t0)}s] status={status} host={ssh_host} port={ssh_port}")
            if ssh_host and ssh_port and status in ("running", "ready"):
                return str(ssh_host), int(ssh_port)
        except Exception as e:
            print(f"    show 실패: {e}")
        time.sleep(15)
    raise TimeoutError(f"SSH 준비 안 됨 ({timeout_s}s)")


def ssh_run(host: str, port: int, cmd: str, check: bool = True) -> int:
    full = [
        "ssh",
        "-i", SSH_KEY,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ConnectTimeout=30",
        "-p", str(port),
        f"root@{host}",
        cmd,
    ]
    r = sh(full)
    if check and r.returncode != 0:
        raise RuntimeError(f"ssh exit {r.returncode}: {cmd[:100]}")
    return r.returncode


def ssh_capture(host: str, port: int, cmd: str) -> str:
    full = [
        "ssh",
        "-i", SSH_KEY,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-o", "ConnectTimeout=30",
        "-p", str(port),
        f"root@{host}",
        cmd,
    ]
    # encoding 명시: Windows 기본 cp949 가 원격 한국어 로그를 못 읽어 폴러가 죽었음.
    r = subprocess.run(full, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return r.stdout or ""


def scp_upload(host: str, port: int, src: Path, dst: str) -> None:
    """scp 로 폴더/파일 업로드. -r 디렉터리, 파일은 그대로."""
    src_str = str(src)
    if src.is_dir():
        full = [
            "scp", "-r",
            "-i", SSH_KEY,
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-P", str(port),
            src_str,
            f"root@{host}:{dst}",
        ]
    else:
        full = [
            "scp",
            "-i", SSH_KEY,
            "-o", "StrictHostKeyChecking=no",
            "-o", "UserKnownHostsFile=/dev/null",
            "-P", str(port),
            src_str,
            f"root@{host}:{dst}",
        ]
    r = sh(full)
    if r.returncode != 0:
        raise RuntimeError(f"scp 실패: {src} → {dst}")


def scp_download(host: str, port: int, src: str, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    full = [
        "scp", "-r",
        "-i", SSH_KEY,
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=/dev/null",
        "-P", str(port),
        f"root@{host}:{src}",
        str(dst),
    ]
    r = sh(full)
    if r.returncode != 0:
        raise RuntimeError(f"scp 다운로드 실패: {src}")


def setup_remote(host: str, port: int) -> None:
    """기본 디렉터리 + python 의존성."""
    ssh_run(host, port, f"mkdir -p {REMOTE_BASE}/scripts {REMOTE_BASE}/data {REMOTE_BASE}/models {REMOTE_BASE}/results")
    # ⭐ transformers<5 고정이 핵심(fix #8): 이미지 torch=2.3.0 인데 transformers 5.x 는
    #    torch>=2.4 요구 → torch 를 스스로 비활성화("PyTorch not found") → 모델 로드 실패.
    #    4.x(<5)는 torch 2.3 호환. torch 는 이미지 내장이라 설치 안 함(pip torch 가 깨뜨림).
    ssh_run(host, port,
        "pip install --quiet seqeval datasets faker pyarrow 'transformers>=4.40,<5'"
    )


V4_1_UPLOAD = [
    "scripts/",
    "data/pii_ner_v3.json",  # KLUE 캐시(train_v4 의존)
    "data/pii_ner_v4_1_baseline.json",
    "data/pii_ner_v4_1_silver.json",
    "data/pii_ner_v4_1_synth.json",
    "data/pii_ner_v4_1_silver_synth.json",
]


def upload_all(host: str, port: int, mode: str = "ablation") -> None:
    items = V4_1_UPLOAD if mode == "v4_1" else UPLOAD_ITEMS  # v4_1=가벼움(external 불필요)
    for rel in items:
        src = PROJECT_ROOT / rel
        if not src.exists():
            print(f"  [skip] {rel} (소스에 없음)")
            continue
        dst_dir = f"{REMOTE_BASE}/{Path(rel).parent}/"
        # 중간 디렉터리 보장
        ssh_run(host, port, f"mkdir -p {dst_dir}", check=False)
        print(f"  업로드: {rel}")
        scp_upload(host, port, src, dst_dir)


def launch_runner(host: str, port: int, abort_threshold: float, mode: str) -> None:
    """tmux 세션에서 ablation runner 시작."""
    if mode == "single":
        # 단일 학습 — 기본 data_prep_v4 default 데이터셋
        cmd = (
            f"cd {REMOTE_BASE} && python scripts/data_prep_v4.py "
            f"&& python scripts/train_v4.py --data data/pii_ner_v4.json "
            f"--output models/pii_ner_v4 --klue-abort-threshold {abort_threshold} "
            f"2>&1 | tee results/single_train.log"
        )
    elif mode == "v4_1":
        # 데이터-변형 ablation (baseline/+silver/+synth/+both) — 미리 만든 v4_1 파일
        cmd = (
            f"cd {REMOTE_BASE} && mkdir -p results logs "
            f"&& python scripts/ablate_v4_1.py 2>&1 | tee results/ablation.log"
        )
    else:
        cmd = (
            f"cd {REMOTE_BASE} && python scripts/run_ablation_remote.py "
            f"--abort-threshold {abort_threshold} "
            f"2>&1 | tee results/ablation.log"
        )

    # tmux 백그라운드, 세션명 ner_v4
    tmux_cmd = f"tmux new-session -d -s ner_v4 '{cmd}'"
    ssh_run(host, port, tmux_cmd)
    print(f"  tmux 세션 'ner_v4' 시작됨. 진행 폴링 대기...")


def poll_progress(host: str, port: int, instance_id: int, mode: str, max_hours: float) -> str:
    """진행 폴링. **절대 크래시 안 함**(전체 try/except) — 폴러가 죽어서 인스턴스를
    같이 destroy 하던 사고 방지. v4_1=flat dict{변형:점수}, ablation=old format 둘 다 지원.
    """
    summary_path = (
        f"{REMOTE_BASE}/results/ablation_summary.json"
        if mode != "single"
        else f"{REMOTE_BASE}/results/single_train.log"
    )
    log_tail_cmd = f"tail -25 {REMOTE_BASE}/results/ablation.log 2>/dev/null"
    n_target = 4 if mode == "v4_1" else 5
    t0 = time.time()
    seen: set = set()
    grace = 150  # 초기 유예(tmux 등록 + 첫 import 대기 — 조기 destroy 방지)

    while True:
        elapsed = time.time() - t0
        if elapsed > max_hours * 3600:
            print(f"\n[poll] {max_hours}h 초과 → 결과 회수")
            return "timeout"
        try:
            tmux_out = ssh_capture(host, port, "tmux ls 2>/dev/null") or ""
            tmux_alive = "ner_v4" in tmux_out

            done = {}
            if mode != "single":
                j = ssh_capture(host, port, f"cat {summary_path} 2>/dev/null") or ""
                if j.strip():
                    try:
                        done = json.loads(j)
                    except Exception:
                        done = {}
            # v4_1: {변형:점수}. ablation old: {results:[{step:..}]}
            if isinstance(done, dict) and "results" in done:
                completed = {r.get("step") for r in done.get("results", []) if isinstance(r, dict)}
            else:
                completed = set(done.keys()) if isinstance(done, dict) else set()

            for v in sorted(completed - seen):
                m = done.get(v, {}) if isinstance(done, dict) else {}
                macro = (m.get("klue_test_macro_f1") or m.get("macro_f1") or m.get("error") or "-")
                print(f"\n  ✅ [{v}] 완료 — KLUE {macro}", flush=True)
            seen = completed

            print(f"[poll {int(elapsed)}s] tmux={'O' if tmux_alive else 'X'} "
                  f"완료변형={len(completed)}/{n_target}", flush=True)

            if len(completed) >= n_target:
                return "completed"
            if not tmux_alive and elapsed > grace:
                tail = ssh_capture(host, port, log_tail_cmd) or "(로그 없음)"
                print(f"\n[poll {int(elapsed)}s] ⚠️ tmux 종료=학습 중단. 원격 로그 끝부분:\n{tail[-1800:]}",
                      flush=True)
                return "tmux_died"
        except Exception as e:  # noqa: BLE001 — 폴러는 절대 안 죽어야 함(인스턴스 보호)
            print(f"[poll {int(elapsed)}s] 일시 오류 무시: {str(e)[:90]}", flush=True)

        time.sleep(60)


def collect_results(host: str, port: int, local_out: Path) -> None:
    local_out.mkdir(parents=True, exist_ok=True)
    print(f"\n[collect] {local_out} 로 다운로드")
    # results/ 전체 + models/ 의 final/, *.json, *.jsonl 만
    scp_download(host, port, f"{REMOTE_BASE}/results", local_out)
    # models 는 큰 체크포인트 빼고 final/ 만
    ssh_run(host, port,
        f"cd {REMOTE_BASE}/models && find . -name 'phase[12]' -type d -exec rm -rf {{}} + 2>/dev/null || true"
    )
    scp_download(host, port, f"{REMOTE_BASE}/models", local_out)


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--mode", choices=["single", "ablation", "v4_1"], default="ablation")
    p.add_argument("--abort-threshold", type=float, default=0.766)
    p.add_argument("--max-price", type=float, default=0.50, help="시간당 USD")
    p.add_argument("--image", default="pytorch/pytorch:2.3.0-cuda12.1-cudnn8-runtime")
    p.add_argument("--max-hours", type=float, default=4.0, help="총 timeout 시간")
    p.add_argument("--dry-run", action="store_true", help="검색만, 인스턴스 생성 X")
    p.add_argument("--instance-id", type=int, default=None, help="기존 인스턴스 재사용")
    p.add_argument("--skip-create", action="store_true")
    p.add_argument("--skip-upload", action="store_true")
    p.add_argument("--no-destroy", action="store_true",
                   help="끝나도 인스턴스 destroy 하지 않음 (디버깅용. 비용 계속 발생!)")
    p.add_argument("--output", default=str(PROJECT_ROOT / "vast_results"))
    args = p.parse_args()

    print(f"[vast_launch] mode={args.mode} abort={args.abort_threshold}")

    # 1. 검색
    print(f"\n[1/6] V100 매물 검색 (max ${args.max_price}/h)")
    offers = vastai_search(min_vram=16, max_price=args.max_price)
    if args.dry_run:
        print("\n[dry-run] 종료 (인스턴스 생성 안 함)")
        return 0
    if not offers:
        print("매물 없음. --max-price 올리거나 나중에 재시도")
        return 1

    # 2. 생성 또는 재사용
    if args.skip_create and args.instance_id:
        instance_id = args.instance_id
        print(f"\n[2/6] 기존 인스턴스 재사용: {instance_id}")
    else:
        print(f"\n[2/6] 인스턴스 생성 (offer {offers[0]['id']})")
        instance_id = vastai_create(offers[0]["id"], args.image)

    try:
        # 3. SSH 대기
        print(f"\n[3/6] SSH 준비 대기")
        host, port = wait_ssh_ready(instance_id)
        print(f"  SSH: root@{host}:{port}")

        # 4. 셋업 + 업로드
        if not args.skip_upload:
            print(f"\n[4/6] 원격 환경 셋업 + 파일 업로드")
            setup_remote(host, port)
            upload_all(host, port, args.mode)

        # 5. 학습 시작 + 폴링
        print(f"\n[5/6] 학습 시작 (mode={args.mode})")
        launch_runner(host, port, args.abort_threshold, args.mode)
        status = poll_progress(host, port, instance_id, args.mode, args.max_hours)
        print(f"\n  최종 상태: {status}")

        # 6. 결과 회수
        print(f"\n[6/6] 결과 다운로드")
        collect_results(host, port, Path(args.output))

    finally:
        if args.no_destroy:
            print(f"\n[finally] --no-destroy → instance {instance_id} 살아있음. 수동 destroy 필요.")
            print(f"  vastai destroy instance {instance_id}")
        else:
            print(f"\n[finally] 인스턴스 {instance_id} destroy")
            try:
                sh(["vastai", "destroy", "instance", str(instance_id), "-y"])
            except Exception as e:
                print(f"  destroy 실패: {e}. 수동 확인 필요: vastai destroy instance {instance_id}")

    print(f"\n결과: {args.output}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
