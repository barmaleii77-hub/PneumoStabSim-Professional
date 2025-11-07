import builtins
import os
from types import SimpleNamespace
from typing import Callable

import pytest

from src.app_runner import ApplicationRunner
from src.bootstrap.environment import configure_qt_environment


@pytest.fixture
def fake_os(monkeypatch: pytest.MonkeyPatch) -> dict[str, str]:
    """Return a fake os.environ mapping isolated per test."""

    env: dict[str, str] = {}
    fake_os_module = SimpleNamespace(environ=env, pathsep=os.pathsep)
    monkeypatch.setattr("src.bootstrap.environment.os", fake_os_module)
    return env


def test_safe_mode_does_not_force_backend(fake_os: dict[str, str]) -> None:
    fake_os["QSG_RHI_BACKEND"] = "opengl"
    messages: list[str] = []

    configure_qt_environment(safe_mode=True, log=messages.append)

    assert "QSG_RHI_BACKEND" not in fake_os
    assert any("safe mode" in message.lower() for message in messages)


def test_standard_mode_sets_backend(fake_os: dict[str, str]) -> None:
    messages: list[str] = []

    configure_qt_environment(safe_mode=False, log=messages.append)

    assert fake_os["QSG_RHI_BACKEND"] == "opengl"
    assert any("standard mode" in message.lower() for message in messages)


def test_surface_format_skipped_when_safe_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    runner = ApplicationRunner(lambda *args, **kwargs: None, lambda *a, **k: None, SimpleNamespace(), object())
    runner.safe_mode_requested = True

    original_import: Callable[..., object] = builtins.__import__
    attempted: dict[str, bool] = {"pyside": False}

    def guard(name: str, globals: dict | None = None, locals: dict | None = None, fromlist: tuple | None = None, level: int = 0) -> object:  # type: ignore[override]
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
    runner = ApplicationRunner(lambda *args, **kwargs: None, lambda *a, **k: None, SimpleNamespace(), object())
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

    monkeypatch.setattr("src.ui.main_window_legacy.MainWindow", DummyLegacyWindow)

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
