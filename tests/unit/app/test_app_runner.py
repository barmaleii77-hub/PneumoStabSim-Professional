from __future__ import annotations

import argparse
from dataclasses import dataclass

import pytest

from src.app_runner import ApplicationRunner


@dataclass
class _DummyAppInstance:
    """Minimal QApplication stub used to drive :class:`ApplicationRunner`."""

    exec_result: int = 0

    is_headless: bool = False
    headless_reason: str | None = None

    def setApplicationName(self, _: str) -> None:  # pragma: no cover - trivial
        pass

    def setApplicationVersion(self, _: str) -> None:  # pragma: no cover - trivial
        pass

    def setOrganizationName(self, _: str) -> None:  # pragma: no cover - trivial
        pass

    def exec(self) -> int:
        return self.exec_result

    def quit(self) -> None:  # pragma: no cover - trivial
        pass


class _DummyQtModule:
    """Subset of the Qt module interface consumed by the runner."""

    class HighDpiScaleFactorRoundingPolicy:  # pragma: no cover - behaviour mocked
        PassThrough = object()

    is_headless = False
    headless_reason = None


def _build_runner(
    monkeypatch: pytest.MonkeyPatch, *, exec_result: int = 0
) -> tuple[ApplicationRunner, list[str]]:
    """Return a runner instance prepared for deterministic testing."""

    runner = ApplicationRunner(
        object, lambda *args, **kwargs: None, _DummyQtModule, object
    )

    # Prevent side effects from subsystems that talk to the real environment.
    monkeypatch.setattr(runner, "setup_logging", lambda verbose_console: None)
    monkeypatch.setattr(runner, "setup_high_dpi", lambda: None)

    def _fake_create_application() -> None:
        app = _DummyAppInstance(exec_result)
        runner.app_instance = app
        runner._is_headless = app.is_headless
        runner._headless_reason = app.headless_reason

    monkeypatch.setattr(runner, "create_application", _fake_create_application)
    monkeypatch.setattr(runner, "_validate_settings_file", lambda: None)
    monkeypatch.setattr(runner, "create_main_window", lambda: None)
    monkeypatch.setattr(runner, "setup_signals", lambda: None)
    monkeypatch.setattr(runner, "setup_test_mode", lambda enabled: None)

    diagnostics_calls: list[str] = []

    def _record_diagnostics() -> None:
        diagnostics_calls.append("called")

    monkeypatch.setattr("src.diagnostics.logs.run_log_diagnostics", _record_diagnostics)

    return runner, diagnostics_calls


def _make_args(*, diag: bool = False) -> argparse.Namespace:
    return argparse.Namespace(verbose=False, test_mode=False, diag=diag)


def test_run_skips_post_diagnostics_without_flag(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner, calls = _build_runner(monkeypatch)

    exit_code = runner.run(_make_args(diag=False))

    assert exit_code == 0
    assert calls == []


def test_run_executes_diagnostics_when_flag_enabled(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner, calls = _build_runner(monkeypatch)

    exit_code = runner.run(_make_args(diag=True))

    assert exit_code == 0
    assert calls == ["called"]


def test_run_executes_diagnostics_on_fatal_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    runner, calls = _build_runner(monkeypatch)

    def _failing_main_window() -> None:
        raise RuntimeError("boom")

    monkeypatch.setattr(runner, "create_main_window", _failing_main_window)

    exit_code = runner.run(_make_args(diag=False))

    assert exit_code == 1
    assert calls == ["called"]


def test_run_executes_diagnostics_when_env_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("PSS_POST_DIAG_TRACE", "auto")
    runner, calls = _build_runner(monkeypatch)

    exit_code = runner.run(_make_args(diag=False))

    assert exit_code == 0
    assert calls == ["called"]
