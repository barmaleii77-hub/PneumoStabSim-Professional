"""Focused tests for the uv sync helper used in Copilot workflows."""

from __future__ import annotations

import subprocess

import pytest

from tools import cipilot_environment


def test_run_uv_sync_missing_executable(monkeypatch: pytest.MonkeyPatch) -> None:
    """A descriptive error is raised when uv is unavailable."""

    monkeypatch.setattr(cipilot_environment.shutil, "which", lambda _: None)

    with pytest.raises(RuntimeError, match="uv executable not found"):
        cipilot_environment.run_uv_sync()


def test_run_uv_sync_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """The helper delegates to uv sync and returns True on success."""

    monkeypatch.setattr(cipilot_environment.shutil, "which", lambda _: "/usr/bin/uv")

    captured: dict[str, list[str]] = {}

    def fake_run(command: list[str]) -> subprocess.CompletedProcess[str]:
        captured["command"] = command
        return subprocess.CompletedProcess(command, 0, stdout="synced\n")

    monkeypatch.setattr(cipilot_environment, "_run_command", fake_run)

    assert cipilot_environment.run_uv_sync() is True
    assert captured["command"] == ["/usr/bin/uv", "sync"]


def test_run_uv_sync_failure_reports_output(
    monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    """Failure surfaces the command output for easier diagnostics."""

    monkeypatch.setattr(cipilot_environment.shutil, "which", lambda _: "/usr/bin/uv")

    def fake_run(command: list[str]) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, 1, stdout="boom\n")

    monkeypatch.setattr(cipilot_environment, "_run_command", fake_run)

    with pytest.raises(RuntimeError) as excinfo:
        cipilot_environment.run_uv_sync()

    out = capsys.readouterr().out
    assert "boom" in out
    assert "boom" in str(excinfo.value)
