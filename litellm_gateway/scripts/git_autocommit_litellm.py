# -*- coding: utf-8 -*-
"""
litellm_gateway 자동 동기화 + 커밋 + push — 작업 스케줄러가 1시간마다 호출.

설계 (사용자 결정 2026-06-12: "기존 repo 하위폴더 + 자동동기화"):
  - c:/litellm 은 git repo 아님 + Docker 절대경로 박힘 → 통째 이동 불가.
  - My-AI-Security-Project repo(=PUBLIC, github.com/vmaca123/My-AI-Security-Project)의
    `litellm-gateway` 브랜치를 **별도 worktree**(sparse-checkout)로 격리.
    → 메인 체크아웃의 활성 브랜치(fix/rrn-label-mask 등)·작업을 절대 안 건드림.
  - 매시간: c:/litellm 의 **큐레이트된 소스만** litellm_gateway/ 로 미러 → 시크릿 스캔 → commit → push.

🔴 PUBLIC repo 안전벨트:
  - 화이트리스트 확장자만 (소스/문서/설정). .env/.pem/키/대용량 데이터/PII json 제외.
  - 파일명 + **내용** 시크릿 스캔. 하나라도 걸리면 전체 ABORT (커밋 안 함).

실행: python scripts/git_autocommit_litellm.py
"""
import os
import re
import shutil
import subprocess
import sys
import datetime
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

SRC = Path("c:/litellm")
REPO = Path("c:/My-AI-Security-Project")
WORKTREE = Path("c:/litellm-gw")          # sparse worktree (litellm_gateway 만 materialize)
BRANCH = "litellm-gateway"
SUBDIR = "litellm_gateway"
LOG = SRC / "logs" / "git_autocommit.log"
MAX_BYTES = 1_500_000                       # 파일당 1.5MB 상한 (대용량 데이터/바이너리 컷)

# 동기화할 확장자(소스/문서/설정) — .json 은 제외(대부분 eval 데이터)
INCLUDE_EXT = {".py", ".md", ".yaml", ".yml", ".html", ".toml", ".cfg", ".ini",
               ".txt", ".sh", ".dockerfile"}
INCLUDE_NAMES = {"Dockerfile", ".coderabbit.yaml", "requirements.txt"}

# 경로에 이게 들어가면 제외 (정규화 후 소문자, '/' 기준)
EXCLUDE_PARTS = (
    ".git/", ".serena", ".obsidian", ".claude", "__pycache__", ".pytest_cache",
    "debate_history", "/logs/", "multi_ai/logs", "eval_harness/reports",
    "dataset_view", "video_cache", "node_modules", ".bak",
)
# 파일명 자체가 시크릿/데이터면 제외
EXCLUDE_NAME_RE = re.compile(
    r"(^|/)\.env($|\.)|\.pem$|\.key$|\.pfx$|\.p12$|\.session\b"
    r"|^eval_.*\.json$|^payloads.*\.json$|^ab_.*\.json$|^analyze_.*\.json$|^temptree\.json$"
    r"|^c:tmp", re.I)

# 내용 시크릿 패턴 (PUBLIC repo — 하나라도 매치 = ABORT)
SECRET_CONTENT_RE = re.compile(
    r"sk-ant-[A-Za-z0-9_\-]{20,}"          # Anthropic
    r"|sk-[A-Za-z0-9]{20,}"                # OpenAI (sk-1234 같은 dev placeholder 는 짧아서 안 걸림)
    r"|AKIA[0-9A-Z]{16}"                   # AWS access key id
    r"|aws_secret_access_key\s*[:=]\s*[A-Za-z0-9/+]{30,}"
    r"|AIza[0-9A-Za-z_\-]{30,}"            # Google
    r"|gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}"  # GitHub
    r"|xox[baprs]-[A-Za-z0-9\-]{10,}"      # Slack
    r"|-----BEGIN [A-Z ]*PRIVATE KEY-----" # PEM
)


def git(*args, cwd=WORKTREE):
    return subprocess.run(["git", "-C", str(cwd), *args], capture_output=True, text=True)


def log(line):
    print(line)
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(line + "\n")
    except Exception:
        pass


def included(rel: str) -> bool:
    low = rel.replace("\\", "/").lower()
    if any(part in low for part in EXCLUDE_PARTS):
        return False
    name = low.rsplit("/", 1)[-1]
    if EXCLUDE_NAME_RE.search(name) or EXCLUDE_NAME_RE.search(low):
        return False
    base = os.path.basename(rel)
    ext = os.path.splitext(base)[1].lower()
    return ext in INCLUDE_EXT or base in INCLUDE_NAMES


def collect_src_files():
    out = []
    for root, dirs, files in os.walk(SRC):
        # 디렉토리 가지치기 (속도 + 대용량 회피)
        dirs[:] = [d for d in dirs if not any(p.strip("/") == d.lower() or p in (root.replace("\\","/").lower()+"/"+d.lower()+"/")
                                              for p in EXCLUDE_PARTS)]
        for f in files:
            full = Path(root) / f
            rel = str(full.relative_to(SRC))
            if not included(rel):
                continue
            try:
                if full.stat().st_size > MAX_BYTES:
                    continue
            except Exception:
                continue
            out.append((full, rel))
    return out


def secret_scan(files):
    """파일명+내용 스캔. 위반 목록 반환 (비어있으면 안전)."""
    bad = []
    for full, rel in files:
        try:
            txt = full.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        m = SECRET_CONTENT_RE.search(txt)
        if m:
            bad.append(f"{rel} :: {m.group(0)[:12]}…")
    return bad


def ensure_worktree():
    """sparse worktree 보장. 없으면 생성(litellm_gateway + 루트만 materialize)."""
    if (WORKTREE / ".git").exists():
        return True
    # origin/main 기준으로 worktree + 브랜치 생성
    git("fetch", "origin", "main", cwd=REPO)
    r = git("worktree", "add", "--no-checkout", "-b", BRANCH, str(WORKTREE), "origin/main", cwd=REPO)
    if r.returncode != 0 and "already exists" not in (r.stderr + r.stdout):
        # 브랜치가 이미 있으면 그걸로
        r2 = git("worktree", "add", "--no-checkout", str(WORKTREE), BRANCH, cwd=REPO)
        if r2.returncode != 0:
            log(f"[ABORT] worktree 생성 실패: {r.stderr.strip()[:200]} / {r2.stderr.strip()[:200]}")
            return False
    git("sparse-checkout", "init", "--cone")
    git("sparse-checkout", "set", SUBDIR, ".github")
    git("checkout")
    return True


def mirror(files):
    """큐레이트 소스를 worktree/litellm_gateway 로 미러(스테일 삭제 포함)."""
    target_root = WORKTREE / SUBDIR
    target_root.mkdir(parents=True, exist_ok=True)
    wanted = set()
    for full, rel in files:
        dst = target_root / rel
        wanted.add(dst.resolve())
        dst.parent.mkdir(parents=True, exist_ok=True)
        try:
            shutil.copy2(full, dst)
        except Exception as e:
            log(f"[WARN] copy 실패 {rel}: {e}")
    # 스테일 제거 (소스에서 사라진 파일)
    for root, _, fs in os.walk(target_root):
        for f in fs:
            p = (Path(root) / f).resolve()
            if p not in wanted:
                try:
                    p.unlink()
                except Exception:
                    pass


def main():
    no_push = "--no-push" in sys.argv     # 로컬 미러+커밋만 (초기 셋업/사람 검토용)
    if not REPO.exists():
        log(f"[ABORT] repo 없음: {REPO}")
        sys.exit(1)
    if not ensure_worktree():
        sys.exit(1)

    files = collect_src_files()
    bad = secret_scan(files)
    if bad:
        log(f"[ABORT] 시크릿 의심 {len(bad)}건 — 커밋 중단: {bad[:5]}")
        sys.exit(1)

    mirror(files)

    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    git("add", "-A", "--", SUBDIR, ".github", ".coderabbit.yaml")
    # 변경 없으면 밀린 push 만
    if git("diff", "--cached", "--quiet").returncode == 0:
        ahead = git("rev-list", "--count", f"origin/{BRANCH}..{BRANCH}").stdout.strip()
        if ahead.isdigit() and int(ahead) > 0 and not no_push:
            r = git("push", "-q", "origin", BRANCH)
            log(f"[{ts}] 변경없음 — 밀린 push {ahead}개 {'완료' if r.returncode==0 else 'FAIL '+r.stderr.strip()[:120]}")
        else:
            print(f"[{ts}] 변경 없음 — skip" + (f" (로컬 {ahead}개 미push, --no-push)" if no_push and ahead.isdigit() and int(ahead)>0 else ""))
        return

    n = len(git("diff", "--cached", "--name-only").stdout.splitlines())
    git("commit", "-q", "-m", f"auto(litellm_gateway): {ts} ({n}개 파일)")
    if no_push:
        log(f"[{ts}] 로컬 커밋 완료 ({n}개 파일, {len(files)}개 동기화) — push 보류(--no-push)")
        return
    r = git("push", "-q", "origin", BRANCH)
    if r.returncode == 0:
        log(f"[{ts}] 자동커밋+push 완료 ({n}개 파일, {len(files)}개 동기화)")
    else:
        log(f"[{ts}] 커밋 완료, [PUSH-FAIL] {r.stderr.strip()[:160]} — 다음 시간 재시도")


if __name__ == "__main__":
    main()
