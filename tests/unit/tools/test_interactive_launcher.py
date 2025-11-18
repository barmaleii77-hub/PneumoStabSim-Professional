"""Tests for the interactive launcher helpers."""

from __future__ import annotations

from pathlib import Path
from subprocess import CompletedProcess

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


def test_launch_app_missing_python(monkeypatch, tmp_path: Path) -> None:
    """A clear error is raised when the interpreter path is invalid."""

    def fake_root() -> Path:
        return tmp_path

    monkeypatch.setattr(launcher, "project_root", fake_root)
    (tmp_path / "app.py").write_text("print('hi')", encoding="utf-8")
    missing_python = tmp_path / "bin" / "python"
    monkeypatch.setattr(launcher, "detect_venv_python", lambda prefer_console: missing_python)

    with pytest.raises(FileNotFoundError) as excinfo:
        launcher.launch_app(args=[], env={}, mode="capture", force_console=False)

    assert str(missing_python) in str(excinfo.value)


def test_run_log_analysis_rejects_file_instead_of_dir(monkeypatch, tmp_path: Path) -> None:
    """Non-directory log targets produce a readable error."""

    def fake_root() -> Path:
        return tmp_path

    monkeypatch.setattr(launcher, "project_root", fake_root)
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir(parents=True)
    (tools_dir / "analyze_logs.py").write_text("print('noop')", encoding="utf-8")
    graphics_path = tmp_path / "logs" / "graphics"
    graphics_path.parent.mkdir(parents=True)
    graphics_path.write_text("not-a-directory", encoding="utf-8")

    message = launcher.run_log_analysis({})

    assert "ожидалась директория" in message.lower()


def test_run_log_analysis_reports_failed_process(monkeypatch, tmp_path: Path) -> None:
    """Non-zero analyzer exit codes are surfaced with command context."""

    def fake_root() -> Path:
        return tmp_path

    monkeypatch.setattr(launcher, "project_root", fake_root)
    tools_dir = tmp_path / "tools"
    tools_dir.mkdir(parents=True)
    (tools_dir / "analyze_logs.py").write_text("print('noop')", encoding="utf-8")
    graphics_dir = tmp_path / "logs" / "graphics"
    graphics_dir.mkdir(parents=True)

    def fake_run(cmd, cwd=None, env=None):
        return CompletedProcess(cmd, 1, stdout="failure", stderr="boom")

    monkeypatch.setattr(launcher, "run_command_logged", fake_run)

    message = launcher.run_log_analysis({})

    assert "завершился с ошибкой" in message.lower()
    assert "failure" in message
