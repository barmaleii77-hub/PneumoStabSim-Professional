from __future__ import annotations

import types
from typing import Any

import pytest


class _DummyQt:
    class HighDpiScaleFactorRoundingPolicy:
        PassThrough = 0

    class QCoreApplication:
        @staticmethod
        def instance() -> Any:
            return None

    is_headless = False
    headless_reason = None


class _DummyTimer:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._single = False
        self._cb = None

    def setSingleShot(self, value: bool) -> None:
        self._single = value

    def timeout(self) -> Any:
        return self

    def connect(self, cb: Any) -> None:
        self._cb = cb

    def start(self, msec: int) -> None:  # pragma: no cover - not used here
        if callable(self._cb):
            self._cb()


class _DummyApp:
    def __init__(self, *args: Any, **kwargs: Any) -> None:
        self._about_to_quit = types.SimpleNamespace(connect=lambda *_: None)

    def setApplicationName(self, *_: Any) -> None:
        pass

    def setApplicationVersion(self, *_: Any) -> None:
        pass

    def setOrganizationName(self, *_: Any) -> None:
        pass

    def aboutToQuit(self) -> Any:  # type: ignore[override]
        return self._about_to_quit

    def exec(self) -> int:
        return 0

    def quit(self) -> None:
        pass


class _DummyMainWindow:
    def __init__(self, *, use_qml_3d: bool) -> None:
        self.use_qml_3d = use_qml_3d

    def show(self) -> None:
        pass

    def raise_(self) -> None:  # noqa: A003 - Qt naming
        pass

    def activateWindow(self) -> None:
        pass

    def close(self) -> bool:
        return True


@pytest.fixture(autouse=True)
def patch_main_windows(monkeypatch: pytest.MonkeyPatch) -> None:
    # Подменяем ModernMainWindow и LegacyMainWindow, а также регистрацию QML типов
    def _fake_register_qml_types() -> None:
        return None

    monkeypatch.setenv("PSS_POST_DIAG_TRACE", "")
    monkeypatch.setenv("QT_QPA_PLATFORM", "offscreen")
    monkeypatch.setenv("QSG_RHI_BACKEND", "opengl")

    monkeypatch.setitem(
        __import__("sys").modules,
        "src.ui.main_window",
        types.SimpleNamespace(MainWindow=_DummyMainWindow),
    )
    monkeypatch.setitem(
        __import__("sys").modules,
        "src.ui.main_window_legacy",
        types.SimpleNamespace(MainWindow=_DummyMainWindow),
    )
    monkeypatch.setitem(
        __import__("sys").modules,
        "src.ui.qml_registration",
        types.SimpleNamespace(register_qml_types=_fake_register_qml_types),
    )


@pytest.mark.gui
def test_application_runner_disables_qml_when_flag_passed(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.app_runner import ApplicationRunner

    # Фейки для QApplication и Qt
    QApplication = _DummyApp
    qInstallMessageHandler = lambda *_, **__: None
    Qt = _DummyQt
    QTimer = _DummyTimer

    args = types.SimpleNamespace(
        no_qml=True,
        legacy=False,
        safe_mode=False,
        safe_cli_mode=False,
        safe_runtime=False,
        test_mode=False,
        verbose=False,
        diag=False,
    )

    runner = ApplicationRunner(QApplication, qInstallMessageHandler, Qt, QTimer)
    code = runner.run(args)

    assert code == 0
    assert runner.use_qml_3d_schema is False


@pytest.mark.gui
def test_application_runner_legacy_overrides_qml(monkeypatch: pytest.MonkeyPatch) -> None:
    from src.app_runner import ApplicationRunner

    QApplication = _DummyApp
    qInstallMessageHandler = lambda *_, **__: None
    Qt = _DummyQt
    QTimer = _DummyTimer

    args = types.SimpleNamespace(
        no_qml=False,
        legacy=True,
        safe_mode=False,
        safe_cli_mode=False,
        safe_runtime=False,
        test_mode=False,
        verbose=False,
        diag=False,
    )

    runner = ApplicationRunner(QApplication, qInstallMessageHandler, Qt, QTimer)
    code = runner.run(args)

    assert code == 0
    assert runner.use_qml_3d_schema is False
