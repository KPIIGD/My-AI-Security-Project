"""Retention enforcement for rotated audit log files.

The M8 audit logger writes JSONL to a size-rotating handler so the active
file never grows unbounded. The compliance spec
(``docs/09 §4 retention_ttl_days``) demands a separate 90-day retention
policy, which is a calendar concern, not a disk-safety concern.

This script removes *rotated* backups whose mtime is older than the
retention window. The active log file (no numeric suffix) is left alone
so the running application never loses its current sink. Run it from a
cron / Task Scheduler entry; the audit logger itself does not invoke it.

Usage::

    python scripts/cleanup_audit_logs.py --log-path ./logs/audit.log.jsonl
    python scripts/cleanup_audit_logs.py --log-path ./logs/audit.log.jsonl --retention-days 90 --dry-run
"""

from __future__ import annotations

import argparse
import re
import sys
import time
from pathlib import Path


_ROTATION_SUFFIX = re.compile(r"\.\d+$")


def _is_rotated_backup(candidate: Path, base: Path) -> bool:
    """True if ``candidate`` is a numbered rotation of ``base``.

    Python's ``RotatingFileHandler`` names backups ``audit.log.jsonl.1``,
    ``audit.log.jsonl.2``, ... — i.e. the base filename plus ``.<int>``.
    """
    if not candidate.name.startswith(base.name):
        return False
    return bool(_ROTATION_SUFFIX.search(candidate.name))


def find_expired_backups(
    log_path: Path, retention_days: int, now_epoch: float | None = None
) -> list[Path]:
    base = log_path
    parent = base.parent
    if not parent.is_dir():
        return []
    cutoff = (now_epoch if now_epoch is not None else time.time()) - retention_days * 86400
    return sorted(
        p
        for p in parent.iterdir()
        if p.is_file()
        and _is_rotated_backup(p, base)
        and p.stat().st_mtime < cutoff
    )


def cleanup_expired_backups(
    log_path: Path,
    retention_days: int,
    *,
    dry_run: bool = False,
    now_epoch: float | None = None,
) -> tuple[list[Path], list[Path]]:
    """Remove rotated backups older than ``retention_days``.

    Returns ``(removed, skipped)`` lists. The active log file is never
    removed. ``skipped`` includes files that match the rotation pattern
    but are still within the retention window.
    """
    expired = find_expired_backups(log_path, retention_days, now_epoch=now_epoch)
    if dry_run:
        return [], expired
    removed: list[Path] = []
    for path in expired:
        path.unlink()
        removed.append(path)
    return removed, []


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Audit log retention cleanup")
    parser.add_argument(
        "--log-path",
        required=True,
        type=Path,
        help="Active audit log path (e.g. ./logs/audit.log.jsonl). "
        "Rotated backups in the same directory are the cleanup targets.",
    )
    parser.add_argument(
        "--retention-days",
        type=int,
        default=90,
        help="Remove rotated backups older than this many days (default: 90).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="List candidates without deleting them.",
    )
    args = parser.parse_args(argv)

    log_path: Path = args.log_path
    if not log_path.parent.is_dir():
        print(f"error: parent directory does not exist: {log_path.parent}", file=sys.stderr)
        return 2

    removed, skipped = cleanup_expired_backups(
        log_path, args.retention_days, dry_run=args.dry_run
    )
    action = "would remove" if args.dry_run else "removed"
    targets = skipped if args.dry_run else removed
    for path in targets:
        print(f"{action}: {path}")
    print(f"total: {len(targets)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
