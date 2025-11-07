from __future__ import annotations

import builtins
import os
import sys
from types import SimpleNamespace
from typing import Callable

import pytest

from src.app_runner import ApplicationRunner
from src.bootstrap.environment import configure_qt_environment


@pytest.fixture
def fake_environment(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Provide an isolated environment mapping for configure_qt_environment tests."""

    env: dict[str, str] = {}
    fake_os = SimpleNamespace(environ=env, pathsep=os.pathsep)
    monkeypatch.setattr("src.bootstrap.environment.os", fake_os)
    return env


def test_safe_mode_does_not_force_backend(fake_environment: dict[str, str]) -> None:
    fake_environment["QSG_RHI_BACKEND"] = "opengl"
    messages: list[str] = []

    configure_qt_environment(safe_mode=True, log=messages.append)

    assert "QSG_RHI_BACKEND" not in fake_environment
    assert any("safe mode" in message.lower() for message in messages)


def test_standard_mode_sets_backend(fake_environment: dict[str, str]) -> None:
    messages: list[str] = []

    configure_qt_environment(safe_mode=False, log=messages.append)

    assert fake_environment["QSG_RHI_BACKEND"] == "opengl"
    assert any("standard mode" in message.lower() for message in messages)


def test_surface_format_skipped_when_safe_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = ApplicationRunner(
        lambda *args, **kwargs: None,
        lambda *args, **kwargs: None,
        SimpleNamespace(),
        object(),
    )
    runner.safe_mode_requested = True

    original_import: Callable[..., object] = builtins.__import__
    attempted: dict[str, bool] = {"pyside": False}

    def guard(
        name: str,
        globals: dict | None = None,
        locals: dict | None = None,
        fromlist: tuple | None = None,
        level: int = 0,
    ) -> object:
        if name.startswith("PySide6"):
            attempted["pyside"] = True
            raise AssertionError("PySide6 import attempted despite safe mode")
        return original_import(name, globals, locals, fromlist or (), level)

    with monkeypatch.context() as context:
        context.setattr(builtins, "__import__", guard)
        runner._configure_default_surface_format()

    assert attempted["pyside"] is False
    assert runner._surface_format_configured is False


def test_legacy_mode_uses_widgets(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = ApplicationRunner(
        lambda *args, **kwargs: None,
        lambda *args, **kwargs: None,
        SimpleNamespace(),
        object(),
    )
    runner.use_legacy_ui = True

    created: dict[str, object] = {}

    class DummyLegacyWindow:
        def __init__(self, *, use_qml_3d: bool) -> None:
            created["use_qml_3d"] = use_qml_3d

        def show(self) -> None:
            created["show"] = True

        def raise_(self) -> None:  # noqa: D401 - Qt-style naming
            created["raise"] = True

        def activateWindow(self) -> None:
            created["activate"] = True

    legacy_module = SimpleNamespace(MainWindow=DummyLegacyWindow)
    monkeypatch.setitem(sys.modules, "src.ui.main_window_legacy", legacy_module)

    qml_called = False

    def fake_register() -> None:
        nonlocal qml_called
        qml_called = True

    monkeypatch.setattr("src.app_runner.register_qml_types", fake_register)

    runner.create_main_window()

    assert created["use_qml_3d"] is False
    assert created["show"] is True
    assert created["raise"] is True
    assert created["activate"] is True
    assert qml_called is False
    assert isinstance(runner.window_instance, DummyLegacyWindow)


def test_run_disables_qml_when_force_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = ApplicationRunner(
        lambda *args, **kwargs: None,
        lambda *args, **kwargs: None,
        SimpleNamespace(),
        object(),
    )

    stub_logger = SimpleNamespace(
        info=lambda *args, **kwargs: None,
        warning=lambda *args, **kwargs: None,
        debug=lambda *args, **kwargs: None,
        error=lambda *args, **kwargs: None,
        critical=lambda *args, **kwargs: None,
        exception=lambda *args, **kwargs: None,
    )

    monkeypatch.setattr(runner, "_print_header", lambda: None)
    monkeypatch.setattr(runner, "_log_startup_environment", lambda: None)
    monkeypatch.setattr(runner, "setup_high_dpi", lambda: None)
    monkeypatch.setattr(runner, "_validate_settings_file", lambda: None)
    monkeypatch.setattr(runner, "setup_signals", lambda: None)
    monkeypatch.setattr(runner, "setup_test_mode", lambda *_: None)
    monkeypatch.setattr("src.diagnostics.warnings.print_warnings_errors", lambda: None)
    monkeypatch.setattr("src.diagnostics.logs.run_log_diagnostics", lambda: None)

    monkeypatch.setattr(runner, "setup_logging", lambda verbose: stub_logger)

    monkeypatch.setattr(
        runner,
        "create_application",
        lambda: setattr(runner, "app_instance", SimpleNamespace(exec=lambda: 0)),
    )

    recorded: dict[str, bool] = {}

    def fake_create_main_window() -> None:
        recorded["use_qml_3d_schema"] = runner.use_qml_3d_schema
        runner.window_instance = object()

    monkeypatch.setattr(runner, "create_main_window", fake_create_main_window)

    args = SimpleNamespace(
        diag=False,
        test_mode=False,
        verbose=False,
        safe_mode=False,
        legacy=False,
        force_disable_qml_3d=True,
        force_disable_qml_3d_reasons=("headless",),
    )

    result = runner.run(args)

    assert result == 0
    assert recorded["use_qml_3d_schema"] is False
