"""Rotated-file cleanup for audit log backups.

The M8 audit logger writes JSONL to a size-rotating handler so the active
file never grows unbounded. The compliance spec
(``docs/09`` processing context ``retention_ttl_days``) defines a 90-day
retention target, which is a calendar concern, not a disk-safety concern.

This script removes exact ``RotatingFileHandler`` backups whose file mtime
is older than the retention window. A cleanup candidate must be named as
the active base filename plus ``.<positive integer>``, such as
``audit.log.jsonl.1``. The active log file (no numeric suffix) is left
alone so the running application never loses its current sink.

This is not event-level TTL enforcement. Low-volume active logs can retain
events older than 90 days until rotation, and high-volume logs can lose
rotated backups before 90 days via ``backupCount`` eviction. Run this script
from a cron / Task Scheduler entry; the audit logger itself does not invoke it.

Usage::

    python scripts/cleanup_audit_logs.py --log-path ./logs/audit.log.jsonl
    python scripts/cleanup_audit_logs.py --log-path ./logs/audit.log.jsonl --retention-days 90 --dry-run
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path


def _is_rotated_backup(candidate: Path, base: Path) -> bool:
    """True if ``candidate`` is a numbered rotation of ``base``.

    Python's ``RotatingFileHandler`` names backups ``audit.log.jsonl.1``,
    ``audit.log.jsonl.2``, ... -- i.e. the base filename plus a positive
    integer suffix. Other files sharing the same prefix are not backups.
    """
    prefix = f"{base.name}."
    if not candidate.name.startswith(prefix):
        return False
    suffix = candidate.name[len(prefix) :]
    return suffix.isascii() and suffix.isdecimal() and not suffix.startswith("0")


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
    """Remove or report rotated backups older than ``retention_days``.

    Returns ``(would_remove, retained)`` when ``dry_run=True`` and
    ``(removed, retained)`` otherwise. ``retained`` includes exact rotated
    backups that are still within the retention window. The active log file
    and non-matching files are never returned or removed.
    """
    base = log_path
    parent = base.parent
    if not parent.is_dir():
        return [], []
    cutoff = (now_epoch if now_epoch is not None else time.time()) - retention_days * 86400
    expired: list[Path] = []
    retained: list[Path] = []
    for path in sorted(
        p for p in parent.iterdir() if p.is_file() and _is_rotated_backup(p, base)
    ):
        if path.stat().st_mtime < cutoff:
            expired.append(path)
        else:
            retained.append(path)
    if dry_run:
        return expired, retained
    removed: list[Path] = []
    for path in expired:
        path.unlink()
        removed.append(path)
    return removed, retained


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Audit log rotated-backup cleanup (mtime-based; not event-level TTL)"
    )
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
        help=(
            "Remove exact rotated backups whose file mtime is older than this many "
            "days (default: 90). This does not enforce event-level TTL."
        ),
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

    removed_or_would_remove, _retained = cleanup_expired_backups(
        log_path, args.retention_days, dry_run=args.dry_run
    )
    action = "would remove" if args.dry_run else "removed"
    targets = removed_or_would_remove
    for path in targets:
        print(f"{action}: {path}")
    print(f"total: {len(targets)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
