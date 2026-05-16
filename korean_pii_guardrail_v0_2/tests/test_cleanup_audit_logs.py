"""Tests for audit log rotated-backup cleanup."""

from __future__ import annotations

import importlib.util
import os
from pathlib import Path
from types import ModuleType


NOW_EPOCH = 1_700_000_000.0
DAY_SECONDS = 86400


def _load_cleanup_module() -> ModuleType:
    script_path = (
        Path(__file__).resolve().parents[1] / "scripts" / "cleanup_audit_logs.py"
    )
    spec = importlib.util.spec_from_file_location("cleanup_audit_logs", script_path)
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


cleanup = _load_cleanup_module()


def _touch(path: Path, *, age_days: int) -> Path:
    path.write_text("x\n", encoding="utf-8")
    mtime = NOW_EPOCH - age_days * DAY_SECONDS
    os.utime(path, (mtime, mtime))
    return path


def _names(paths: list[Path]) -> list[str]:
    return sorted(path.name for path in paths)


def test_find_expired_backups_only_matches_exact_rotating_filehandler_names(
    tmp_path: Path,
) -> None:
    base = tmp_path / "audit.log.jsonl"
    _touch(base, age_days=365)
    _touch(tmp_path / "audit.log.jsonl.1", age_days=91)
    _touch(tmp_path / "audit.log.jsonl.2", age_days=120)
    _touch(tmp_path / "audit.log.jsonl.3", age_days=2)

    # Prefix-sharing files are not RotatingFileHandler backups.
    _touch(tmp_path / "audit.log.jsonl.debug.1", age_days=120)
    _touch(tmp_path / "audit.log.jsonl.evidence.123", age_days=120)
    _touch(tmp_path / "audit.log.jsonl.old.2", age_days=120)
    _touch(tmp_path / "audit.log.jsonl2.1", age_days=120)
    _touch(tmp_path / "audit.log.jsonl.0", age_days=120)
    _touch(tmp_path / "audit.log.jsonl.01", age_days=120)

    expired = cleanup.find_expired_backups(base, 90, now_epoch=NOW_EPOCH)

    assert _names(expired) == ["audit.log.jsonl.1", "audit.log.jsonl.2"]


def test_cleanup_expired_backups_dry_run_reports_without_deleting(
    tmp_path: Path,
) -> None:
    base = tmp_path / "audit.log.jsonl"
    active = _touch(base, age_days=365)
    expired = _touch(tmp_path / "audit.log.jsonl.1", age_days=91)
    retained_backup = _touch(tmp_path / "audit.log.jsonl.2", age_days=3)
    non_backup = _touch(tmp_path / "audit.log.jsonl.debug.1", age_days=120)

    would_remove, retained = cleanup.cleanup_expired_backups(
        base, 90, dry_run=True, now_epoch=NOW_EPOCH
    )

    assert _names(would_remove) == ["audit.log.jsonl.1"]
    assert _names(retained) == ["audit.log.jsonl.2"]
    assert active.exists()
    assert expired.exists()
    assert retained_backup.exists()
    assert non_backup.exists()


def test_cleanup_expired_backups_deletes_only_expired_exact_backups(
    tmp_path: Path,
) -> None:
    base = tmp_path / "audit.log.jsonl"
    active = _touch(base, age_days=365)
    expired = _touch(tmp_path / "audit.log.jsonl.1", age_days=91)
    retained_backup = _touch(tmp_path / "audit.log.jsonl.2", age_days=3)
    non_backup = _touch(tmp_path / "audit.log.jsonl.old.2", age_days=120)

    removed, retained = cleanup.cleanup_expired_backups(
        base, 90, dry_run=False, now_epoch=NOW_EPOCH
    )

    assert _names(removed) == ["audit.log.jsonl.1"]
    assert _names(retained) == ["audit.log.jsonl.2"]
    assert not expired.exists()
    assert active.exists()
    assert retained_backup.exists()
    assert non_backup.exists()


def _touch_relative_to_now(path: Path, *, age_days: float) -> Path:
    """Touch ``path`` with mtime ``age_days`` ago relative to ``time.time()``.

    CLI tests cannot inject ``now_epoch`` (only the library API can), so
    fixtures used through ``cleanup.main`` must use real-time-relative
    mtimes.
    """
    import time as _time

    path.write_text("x\n", encoding="utf-8")
    mtime = _time.time() - age_days * DAY_SECONDS
    os.utime(path, (mtime, mtime))
    return path


def test_cli_main_default_does_not_print_retained_files(
    tmp_path: Path, capsys,
) -> None:
    """Without --verbose, CLI lists only removed/would-remove targets.

    Retained backups are kept implicit by default to keep the cron output
    short. This is the contract operators see in their nightly job log.
    """
    base = tmp_path / "audit.log.jsonl"
    _touch_relative_to_now(base, age_days=365)
    _touch_relative_to_now(tmp_path / "audit.log.jsonl.1", age_days=91)
    _touch_relative_to_now(tmp_path / "audit.log.jsonl.2", age_days=3)

    exit_code = cleanup.main(["--log-path", str(base), "--dry-run"])
    captured = capsys.readouterr().out

    assert exit_code == 0
    assert "would remove: " in captured
    assert "audit.log.jsonl.1" in captured
    assert "audit.log.jsonl.2" not in captured  # retained — not surfaced by default
    assert "retained:" not in captured


def test_cli_main_verbose_lists_retained_backups(
    tmp_path: Path, capsys,
) -> None:
    """With --verbose, CLI also lists retained rotated backups.

    Operators verifying that the right files were spared can opt into
    this output mode.
    """
    base = tmp_path / "audit.log.jsonl"
    _touch_relative_to_now(base, age_days=365)
    _touch_relative_to_now(tmp_path / "audit.log.jsonl.1", age_days=91)
    _touch_relative_to_now(tmp_path / "audit.log.jsonl.2", age_days=3)

    exit_code = cleanup.main(
        ["--log-path", str(base), "--dry-run", "--verbose"]
    )
    captured = capsys.readouterr().out

    assert exit_code == 0
    assert "would remove: " in captured
    assert "audit.log.jsonl.1" in captured
    assert "retained: " in captured
    assert "audit.log.jsonl.2" in captured
