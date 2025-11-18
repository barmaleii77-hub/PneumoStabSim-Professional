from __future__ import annotations

import os
import types

import pytest

from src.app_runner import ApplicationRunner

from src.ui.startup import (
    bootstrap_graphics_environment,
    choose_scenegraph_backend,
    detect_headless_environment,
)


@pytest.mark.parametrize(
    "platform,expected",
    [
        ("win32", "d3d11"),
        ("darwin", "metal"),
        ("linux", "opengl"),
        ("linux-x86_64", "opengl"),
        ("macos", "metal"),
    ],
)
def test_choose_scenegraph_backend(platform: str, expected: str) -> None:
    assert choose_scenegraph_backend(platform) == expected


@pytest.mark.parametrize(
    "env,expected_reasons",
    [
        (
            {"CI": "true", "QT_QPA_PLATFORM": "xcb", "DISPLAY": ":0"},
            ("ci-flag",),
        ),
        (
            {"QT_QPA_PLATFORM": "", "DISPLAY": ""},
            ("no-display-server", "qt-qpa-platform-missing"),
        ),
        (
            {"PSS_HEADLESS": "1"},
            ("flag:pss-headless",),
        ),
        ({"QT_QPA_PLATFORM": "xcb", "DISPLAY": ":0"}, ()),
    ],
)
def test_detect_headless_environment(
    env: dict[str, str], expected_reasons: tuple[str, ...]
) -> None:
    headless, reasons = detect_headless_environment(env)
    assert reasons == expected_reasons
    assert headless is bool(expected_reasons)


def test_bootstrap_graphics_environment_sets_backend_when_not_safe() -> None:
    env: dict[str, str] = {"QT_QPA_PLATFORM": "xcb", "DISPLAY": ":0"}
    state = bootstrap_graphics_environment(env, platform="win32", safe_mode=False)

    assert env["QSG_RHI_BACKEND"] == "d3d11"
    assert env["QT_QPA_PLATFORM"] == "xcb"
    assert "PSS_FORCE_NO_QML_3D" not in env
    assert state.backend == "d3d11"
    assert state.headless is False
    assert state.use_qml_3d is True


def test_bootstrap_graphics_environment_enables_headless_defaults() -> None:
    env: dict[str, str] = {}
    state = bootstrap_graphics_environment(env, platform="linux", safe_mode=False)

    assert env["QT_QPA_PLATFORM"] == "offscreen"
    assert env["PSS_FORCE_NO_QML_3D"] == "1"
    assert env["QSG_RHI_BACKEND"] == "opengl"
    assert state.headless is True
    assert "qt-qpa-platform-missing" in state.headless_reasons
    assert state.use_qml_3d is False


def test_bootstrap_graphics_environment_preserves_display_defaults() -> None:
    env: dict[str, str] = {"DISPLAY": ":1"}

    state = bootstrap_graphics_environment(env, platform="linux", safe_mode=False)

    assert "QT_QPA_PLATFORM" not in env
    assert env["QSG_RHI_BACKEND"] == "opengl"
    assert state.headless is False
    assert state.use_qml_3d is True


def test_bootstrap_graphics_environment_respects_custom_headless_platform() -> None:
    env: dict[str, str] = {"QT_QPA_PLATFORM": "minimal"}

    state = bootstrap_graphics_environment(env, platform="linux", safe_mode=False)

    assert env["QT_QPA_PLATFORM"] == "minimal"
    assert env["PSS_FORCE_NO_QML_3D"] == "1"
    assert state.headless is True
    assert "qt-qpa-platform:minimal" in state.headless_reasons


def test_bootstrap_graphics_environment_respects_safe_mode() -> None:
    env: dict[str, str] = {"QT_QPA_PLATFORM": "xcb", "DISPLAY": ":0"}
    state = bootstrap_graphics_environment(env, platform="darwin", safe_mode=True)

    assert "QSG_RHI_BACKEND" not in env
    assert "PSS_FORCE_NO_QML_3D" not in env
    assert state.backend == "metal"
    assert state.safe_mode is True
    assert state.use_qml_3d is True


def test_bootstrap_graphics_environment_respects_pss_headless_flag() -> None:
    env: dict[str, str] = {"PSS_HEADLESS": "1"}

    state = bootstrap_graphics_environment(env, platform="win32", safe_mode=False)

    assert state.headless is True
    assert state.use_qml_3d is False
    assert env["QT_QPA_PLATFORM"] == "offscreen"


class _DummySignal:
    def __init__(self) -> None:
        self._callback = None

    def connect(self, callback):  # type: ignore[no-untyped-def]
        self._callback = callback

    def trigger(self) -> None:
        if callable(self._callback):
            self._callback()


class _DummyQTimer:
    def __init__(self, _parent: object | None = None) -> None:
        self.timeout = _DummySignal()
        self.single_shot: bool | None = None
        self.started_with: int | None = None

    def setSingleShot(self, value: bool) -> None:  # pragma: no cover - trivial
        self.single_shot = value

    def start(self, milliseconds: int) -> None:
        self.started_with = milliseconds

    @staticmethod
    def singleShot(delay: int, callback):  # type: ignore[no-untyped-def]
        if callable(callback):
            callback()

    def trigger(self) -> None:
        self.timeout.trigger()


class _DummyQtModule:
    class QCoreApplication:
        _instance = types.SimpleNamespace(exit_code=None, quit_called=False)

        @classmethod
        def instance(cls):  # pragma: no cover - trivial proxy
            return cls._instance


def test_runner_bootstrap_records_headless_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(os, "environ", {})

    runner = ApplicationRunner(
        object, lambda *_, **__: None, types.SimpleNamespace(), _DummyQTimer
    )
    runner.platform_slug = "linux"
    runner.safe_mode_requested = False

    state = runner._bootstrap_graphics_environment()

    assert state.headless is True
    assert runner._is_headless is True
    assert runner.use_qml_3d_schema is False
    assert os.environ["QT_QPA_PLATFORM"] == "offscreen"
    assert os.environ["QSG_RHI_BACKEND"] == "opengl"
    assert "bootstrap-headless:" in os.environ.get("PSS_POST_DIAG_TRACE", "")


def test_runner_bootstrap_respects_safe_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "environ", {"QT_QPA_PLATFORM": "xcb"})

    runner = ApplicationRunner(
        object, lambda *_, **__: None, types.SimpleNamespace(), _DummyQTimer
    )
    runner.platform_slug = "darwin"
    runner.safe_mode_requested = True

    state = runner._bootstrap_graphics_environment()

    assert state.backend == "metal"
    assert state.safe_mode is True
    assert runner._is_headless is False
    assert runner.use_qml_3d_schema is True
    assert "QSG_RHI_BACKEND" not in os.environ


def test_schedule_safe_exit_exits_cleanly(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(os, "environ", {})

    qt_core = _DummyQtModule.QCoreApplication._instance

    def _exit(code: int) -> None:  # pragma: no cover - trivial assignment
        qt_core.exit_code = code

    qt_core.exit = _exit
    qt_core.quit = lambda: setattr(qt_core, "quit_called", True)

    runner = ApplicationRunner(
        object, lambda *_, **__: None, _DummyQtModule, _DummyQTimer
    )
    runner.app_instance = types.SimpleNamespace()

    runner._schedule_safe_exit(
        reason="test", log_message="log", console_message="console", timer_ms=5
    )

    assert isinstance(runner._safe_exit_timer, _DummyQTimer)
    runner._safe_exit_timer.trigger()

    assert qt_core.exit_code == 0
    assert "safe-exit:test" in os.environ.get("PSS_POST_DIAG_TRACE", "")


def test_startup_environment_snapshot_includes_diag_trace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("QSG_RHI_BACKEND", "opengl")
    monkeypatch.setenv("PSS_HEADLESS", "1")
    monkeypatch.setenv("PSS_POST_DIAG_TRACE", "headless|safe-exit")

    snapshot = ApplicationRunner._gather_startup_environment_snapshot()

    assert snapshot["QT_QPA_PLATFORM"] == "offscreen"
    assert snapshot["PSS_HEADLESS"] == "1"
    assert snapshot["PSS_POST_DIAG_TRACE"] == "headless|safe-exit"


def test_run_triggers_post_diagnostics_and_records_trace(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(os, "environ", {})

    class _Args:
        verbose = False
        safe_mode = False
        safe_cli_mode = True
        safe_runtime = True
        test_mode = False
        diag = True
        legacy = False
        no_qml = False
        force_disable_qml_3d = False
        force_disable_qml_3d_reasons: tuple[str, ...] = ()

    runner = ApplicationRunner(
        object, lambda *_, **__: None, _DummyQtModule, _DummyQTimer
    )
    runner.platform_slug = "linux"
    runner.app_instance = types.SimpleNamespace(exec=lambda: 0)

    def _fake_bootstrap() -> GraphicsBootstrapState:
        from src.ui.startup import GraphicsBootstrapState as _State

        state = _State(
            backend="opengl",
            use_qml_3d=False,
            safe_mode=False,
            headless=True,
            headless_reasons=("ci-flag",),
        )
        runner.graphics_state = state
        runner._is_headless = True
        runner._headless_reason = "ci-flag"
        runner._append_post_diag_trace("bootstrap-ci")
        return state

    diagnostics_called: list[bool] = []
    scheduled: list[str] = []

    runner._bootstrap_graphics_environment = _fake_bootstrap  # type: ignore[assignment]
    runner._log_startup_environment = lambda: None  # type: ignore[assignment]
    runner.setup_high_dpi = lambda: None  # type: ignore[assignment]
    runner.create_application = lambda: None  # type: ignore[assignment]
    runner._validate_settings_file = lambda: None  # type: ignore[assignment]
    runner.create_main_window = lambda: None  # type: ignore[assignment]
    runner.setup_signals = lambda: None  # type: ignore[assignment]
    runner.setup_test_mode = lambda _flag: None  # type: ignore[assignment]
    runner._run_post_diagnostics = lambda: diagnostics_called.append(True)  # type: ignore[assignment]

    def _fake_schedule(**kwargs) -> None:
        scheduled.append(kwargs["reason"])
        runner._append_post_diag_trace(f"safe-test:{kwargs['reason']}")

    runner._schedule_safe_exit = _fake_schedule  # type: ignore[assignment]

    result = runner.run(_Args())

    assert result == 0
    assert diagnostics_called == [True]
    assert "safe-test:" in os.environ.get("PSS_POST_DIAG_TRACE", "")
    assert "bootstrap-ci" in os.environ["PSS_POST_DIAG_TRACE"]
    assert scheduled == ["cli-safe"]
