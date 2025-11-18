"""CLI error handling for backup commands."""

from __future__ import annotations

from pathlib import Path

from src.cli import backup


def test_restore_missing_archive(tmp_path: Path, capsys) -> None:
    missing = tmp_path / "missing.zip"

    exit_code = backup.run(["--root", str(tmp_path), "restore", str(missing)])

    captured = capsys.readouterr().out
    assert exit_code == 1
    assert "Archive not found" in captured


def test_prune_negative_keep(tmp_path: Path, capsys) -> None:
    exit_code = backup.run(["--root", str(tmp_path), "prune", "-1"])

    captured = capsys.readouterr().out
    assert exit_code == 1
    assert "keep must be non-negative" in captured
