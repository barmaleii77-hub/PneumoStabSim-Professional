"""Tests for the interactive launcher helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from scripts import interactive_launcher as launcher


def test_launch_app_missing_entrypoint(monkeypatch, tmp_path: Path) -> None:
    """Launch fails fast with a clear message when app.py is absent."""

    def fake_root() -> Path:
        return tmp_path

    monkeypatch.setattr(launcher, "project_root", fake_root)

    with pytest.raises(FileNotFoundError) as excinfo:
        launcher.launch_app(args=[], env={}, mode="capture", force_console=False)

    assert "Application entrypoint not found" in str(excinfo.value)


def test_run_log_analysis_reports_missing_logs(monkeypatch, tmp_path: Path) -> None:
    """Log analysis returns a helpful message when logs are unavailable."""

    def fake_root() -> Path:
        return tmp_path

    monkeypatch.setattr(launcher, "project_root", fake_root)

    message = launcher.run_log_analysis({})

    assert "Логи графики отсутствуют" in message or "Не найден анализатор" in message
