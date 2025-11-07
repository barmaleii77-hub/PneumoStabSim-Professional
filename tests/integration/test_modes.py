"""Integration tests for the new launch modes (safe/legacy)."""

from __future__ import annotations

import os
import sys
import types

import pytest

from src.bootstrap.environment import configure_qt_environment
from src.cli.arguments import parse_arguments
from src.app_runner import ApplicationRunner


class _DummyQApplication:  # Minimal stub for ApplicationRunner dependency
    def __init__(self, *_: object, **__: object) -> None:  # pragma: no cover - stub
        pass


class _DummyQTimer:
    def __init__(self, *_: object, **__: object) -> None:  # pragma: no cover - stub
        pass


def test_parse_arguments_supports_modes() -> None:
    """Both --safe-mode and --legacy flags should be recognised by the parser."""

    args = parse_arguments(["--safe-mode", "--legacy"])
    assert args.safe_mode is True
    assert args.legacy is True


def test_configure_qt_environment_safe_mode(monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]) -> None:
    """Safe mode must remove forced backends and log the fallback behaviour."""

    monkeypatch.setenv("QSG_RHI_BACKEND", "opengl")
    configure_qt_environment(safe_mode=True)
    out = capsys.readouterr().out.lower()

    assert "safe mode" in out
    assert "qt quick scene graph backend" in out
    assert os.environ.get("QSG_RHI_BACKEND") in (None, "")


def test_application_runner_legacy_mode_uses_legacy_main_window(monkeypatch: pytest.MonkeyPatch) -> None:
    """Legacy mode should instantiate the legacy MainWindow without registering QML."""

    calls: dict[str, int] = {"legacy_inits": 0}

    class _LegacyWindow:
        def __init__(self, *, use_qml_3d: bool) -> None:
            calls["legacy_inits"] += 1
            self.use_qml_3d = use_qml_3d
            self.shown = False
            self.raised = False
            self.activated = False

        def show(self) -> None:
            self.shown = True

        def raise_(self) -> None:  # pragma: no cover - simple state flag
            self.raised = True

        def activateWindow(self) -> None:  # pragma: no cover - simple state flag
            self.activated = True

    def _fail_register_qml_types() -> None:  # pragma: no cover - defensive guard
        raise AssertionError("register_qml_types must not be called in legacy mode")

    def _fail_main_window(*_: object, **__: object) -> None:  # pragma: no cover - guard
        raise AssertionError("Legacy mode should not import refactored MainWindow")

    failing_main_window = types.SimpleNamespace(MainWindow=_fail_main_window)

    monkeypatch.setitem(
        sys.modules,
        "src.ui.main_window_legacy",
        types.SimpleNamespace(MainWindow=_LegacyWindow),
    )
    monkeypatch.setitem(sys.modules, "src.ui.main_window", failing_main_window)
    monkeypatch.setattr("src.app_runner.register_qml_types", _fail_register_qml_types)

    runner = ApplicationRunner(_DummyQApplication, object, object, _DummyQTimer)
    runner._is_headless = False
    runner.use_legacy_ui = True
    runner.use_qml_3d_schema = True  # Should be ignored for legacy
    runner._check_qml_initialization = lambda *_: None
    runner.app_logger = None

    runner.create_main_window()

    assert isinstance(runner.window_instance, _LegacyWindow)
    assert runner.window_instance.use_qml_3d is False
    assert runner.window_instance.shown is True
    assert calls["legacy_inits"] == 1
