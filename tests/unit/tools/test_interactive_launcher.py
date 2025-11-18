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


def test_summarize_log_tail_counts(tmp_path: Path) -> None:
    """Tail summariser reports errors and warnings."""

    log = tmp_path / "sample.log"
    log.write_text(
        "\n".join(
            [
                "info: start",
                "Warning: be careful",
                "Error: missing module",
                "traceback: detail",
            ]
        ),
        encoding="utf-8",
    )

    tail, counts, highlights = launcher.summarize_log_tail(log, max_lines=10)

    assert len(tail) == 4
    assert counts == {"error": 2, "warning": 1}
    assert any("Error" in line for line in highlights)


def test_detect_failure_hint_pytest_failure() -> None:
    """Pytest failures produce a directed hint."""

    lines = ["pytest session", "FAILED test_sample.py::test_demo", "short traceback"]

    hint = launcher._detect_failure_hint(lines)  # noqa: SLF001

    assert "упали тесты" in hint


def test_build_custom_pytest_command_includes_args(tmp_path: Path) -> None:
    """Custom pytest command builder keeps targets and extra arguments."""

    python_exe = tmp_path / "python"
    cmd = launcher.build_custom_pytest_command(
        python_exe, targets=["tests/unit"], extra_args=["-k", "smoke"]
    )

    assert cmd[:3] == [str(python_exe), "-m", "pytest"]
    assert cmd[-2:] == ["-k", "smoke"]


def test_build_testing_entrypoint_command_all_scope(tmp_path: Path) -> None:
    """Unified entrypoint commands support the 'all' scope."""

    python_exe = tmp_path / "python"

    cmd = launcher.build_testing_entrypoint_command(python_exe, "all")

    assert cmd[-2:] == ["--scope", "all"]
