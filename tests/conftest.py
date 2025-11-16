"""Extended pytest configuration with enhanced qtbot and monkeypatch shims."""

from __future__ import annotations
import os
import sys
import time
from pathlib import Path
from collections.abc import Callable
import pytest

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(1, str(SRC_PATH))

os.environ.setdefault("PYTHONHASHSEED", "0")
os.environ.setdefault("PSS_FORCE_NONBLOCKING_DIALOGS", "1")
os.environ.setdefault("PSS_SUPPRESS_UI_DIALOGS", "1")

_MARKERS = [
    "unit: Unit tests",
    "integration: Integration tests",
    "smoke: Smoke tests",
    "system: System tests",
    "slow: Slow tests",
    "gui: GUI/QML tests",
    "headless: Headless Qt tests",
    "scenario: Scenario physics tests",
    "qtbot: pytest-qt qtbot tests",
    "qt_no_exception_capture: Disable pytest-qt exception capture",
    "ui: Legacy UI tests",
]


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    for marker in _MARKERS:
        config.addinivalue_line("markers", marker)


@pytest.fixture(scope="session", autouse=True)
def _path_snapshot() -> None:
    report_dir = PROJECT_ROOT / "reports" / "tests" / "path_diagnostics"
    report_dir.mkdir(parents=True, exist_ok=True)
    payload = {"cwd": os.getcwd(), "project_root": str(PROJECT_ROOT)}
    try:
        (report_dir / "session_paths.json").write_text(
            __import__("json").dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
    except Exception:
        pass


@pytest.fixture(scope="session")
def qapp():
    try:
        from PySide6.QtWidgets import QApplication  # type: ignore
    except Exception:
        yield None
        return
    app = QApplication.instance() or QApplication(sys.argv)
    yield app
    try:
        app.quit()
    except Exception:
        pass


@pytest.fixture(scope="session")
def qt_runtime_ready(qapp):
    """Ensure Qt runtime is available for tests requiring QML/QtQuick3D."""
    try:
        from tests.helpers.qt import ensure_qt_runtime

        ensure_qt_runtime()
    except Exception as exc:
        pytest.skip(f"Qt runtime not available: {exc}")  # pytest-skip-ok
    yield


@pytest.fixture
def settings_manager(tmp_path, monkeypatch):
    """Provide a SettingsManager instance with temp config for tests."""
    import json
    from src.common.settings_manager import SettingsManager

    settings_path = tmp_path / "app_settings.json"
    # Load baseline config from project
    try:
        baseline = json.loads(
            (PROJECT_ROOT / "config" / "app_settings.json").read_text(encoding="utf-8")
        )
    except Exception:
        baseline = {
            "metadata": {"units_version": "si_v2"},
            "current": {},
            "defaults_snapshot": {},
        }

    settings_path.write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    manager = SettingsManager(settings_path)
    yield manager


@pytest.fixture
def integration_reports_dir(tmp_path):
    """Provide a temporary directory for integration test reports."""
    reports_dir = tmp_path / "reports" / "integration"
    reports_dir.mkdir(parents=True, exist_ok=True)
    return reports_dir


@pytest.fixture
def structlog_logger_config():
    """Provide basic structlog config for diagnostic tests."""
    from src.diagnostics.logger_factory import LoggerConfig, DEFAULT_LOG_LEVEL

    return LoggerConfig(
        name="test.logger",
        level=DEFAULT_LOG_LEVEL,
        context=(("subsystem", "diagnostics"), ("component", "logger")),
    )


@pytest.fixture
def reference_suspension_linkage():
    """Provide reference suspension linkage geometry for tests."""
    # Minimal reference geometry from baseline config
    from src.mechanics.geometry import SuspensionLinkage

    try:
        from src.mechanics.geometry import SuspensionLinkage
    except Exception:
        # Backwards-compatible import path
        from src.mechanics.linkage_geometry import SuspensionLinkage

    # Baseline geometry parameters in metres (simple canonical linkage)
    linkage = SuspensionLinkage.from_mm(
        pivot=(200.0, 0.0),
        free_end=(500.0, 0.0),
        rod_joint=(450.0, 0.0),
        cylinder_tail=(150.0, 500.0),
        cylinder_body_length=300.0,
    )
    return linkage


@pytest.fixture
def temp_settings_file(tmp_path):
    """Provide a temporary settings file for tests."""
    import json

    settings_path = tmp_path / "config" / "app_settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load baseline config
    try:
        baseline = json.loads(
            (PROJECT_ROOT / "config" / "app_settings.json").read_text(encoding="utf-8")
        )
    except Exception:
        baseline = {
            "metadata": {"units_version": "si_v2"},
            "current": {},
            "defaults_snapshot": {},
        }
    
    settings_path.write_text(
        json.dumps(baseline, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return settings_path


@pytest.fixture
def hysteretic_check_valve():
    """Provide a check valve with hysteresis for testing state transitions."""
    from src.pneumo.valves import CheckValve
    
    # Калиброванный клапан: открывается при Δp > 1.5 kPa,
    # закрывается при Δp < 0.9 kPa (гистерезис 600 Pa)
    return CheckValve(
        delta_open_min=1500.0,  # 1.5 kPa
        d_eq=0.008,  # 8mm equivalent diameter
        hyst=600.0,  # 600 Pa hysteresis
    )


@pytest.fixture
def relief_valve_reference():
    """Provide a reference relief valve for testing flow and hysteresis."""
    from src.pneumo.valves import ReliefValve
    from src.pneumo.enums import ReliefValveKind
    
    # Клапан давления: открывается при p > 205 kPa,
    # закрывается при p < 200 kPa (гистерезис 5 kPa)
    return ReliefValve(
        kind=ReliefValveKind.STIFFNESS,
        p_set=200_000.0,  # 200 kPa
        hyst=5000.0,  # 5 kPa
        d_eq=0.02,  # throttle coefficient
    )


# Enhanced qtbot fallback implementing required methods used by tests
@pytest.fixture
def qtbot(qapp):
    try:
        from PySide6.QtTest import QTest  # type: ignore
        from PySide6.QtCore import Qt, QEvent, QObject
        from PySide6.QtGui import QMouseEvent, QKeyEvent
        from PySide6.QtWidgets import QApplication
    except Exception:
        QTest = None  # type: ignore
        Qt = None  # type: ignore
        QApplication = None  # type: ignore
        QObject = object  # type: ignore

    class _Bot:
        def __init__(self) -> None:
            self._cleanups: list[Callable[[], object]] = []

        def addWidget(self, widget) -> None:
            try:
                if hasattr(widget, "show"):
                    widget.show()
            except Exception:
                pass

        def wait(self, ms: int) -> None:
            if QTest is not None:
                try:
                    QTest.qWait(ms)
                    return
                except Exception:
                    pass
            time.sleep(ms / 1000.0)

        def waitUntil(
            self, func: Callable[[], bool], timeout: int = 1000, interval: int = 25
        ) -> None:
            deadline = time.time() + timeout / 1000.0
            while time.time() < deadline:
                try:
                    if func():
                        return
                except Exception:
                    pass
                self.wait(interval)
            raise AssertionError("waitUntil timeout")

        def waitSignal(self, signal, timeout: int = 1000):
            class _Ctx:
                def __init__(self, sig):
                    self._sig = sig
                    self._received = False
                    self.args = []

                def __enter__(self):
                    try:
                        self._sig.connect(self._on_emit)
                    except Exception:
                        pass
                    return self

                def _on_emit(self, *a):
                    self._received = True
                    self.args = list(a)

                def __exit__(self, exc_type, exc, tb):
                    deadline = time.time() + timeout / 1000.0
                    while not self._received and time.time() < deadline:
                        try:
                            if QTest is not None:
                                QTest.qWait(10)
                            else:
                                time.sleep(0.01)
                        except Exception:
                            break
                    try:
                        self._sig.disconnect(self._on_emit)
                    except Exception:
                        pass
                    if not self._received:
                        raise AssertionError("waitSignal timeout")
                    return False

            return _Ctx(signal)

        def addCleanup(self, func: Callable[[], object]) -> None:
            self._cleanups.append(func)

        def keyClick(self, widget, key, modifier=None, delay: int = 0) -> None:
            if QTest is not None and Qt is not None:
                try:
                    QTest.keyClick(widget, key, modifier or Qt.NoModifier, delay)
                    return
                except Exception:
                    pass
            try:
                if Qt is None:
                    return
                if not widget.hasFocus():
                    widget.setFocus()
                press = QKeyEvent(QEvent.Type.KeyPress, key, modifier or Qt.NoModifier)
                release = QKeyEvent(
                    QEvent.Type.KeyRelease, key, modifier or Qt.NoModifier
                )
                QApplication.sendEvent(widget, press)
                QApplication.sendEvent(widget, release)
            except Exception:
                pass

        def keyClicks(self, widget, text: str, modifier=None, delay: int = 0) -> None:
            if QTest is not None:
                try:
                    QTest.keyClicks(widget, text, modifier or Qt.NoModifier, delay)
                    return
                except Exception:
                    pass
            for ch in str(text):
                try:
                    self.keyClick(
                        widget,
                        ord(ch),
                        modifier or (Qt.NoModifier if Qt else None),
                        delay,
                    )
                except Exception:
                    pass

        def mouseClick(self, widget, button=None) -> None:
            if QTest is not None and Qt is not None:
                try:
                    QTest.mouseClick(widget, button or Qt.LeftButton)
                    return
                except Exception:
                    pass
            try:
                if button is None and Qt is not None:
                    button = Qt.LeftButton
                ev = QMouseEvent(
                    QEvent.Type.MouseButtonPress,
                    widget.rect().center(),
                    button,
                    button,
                    Qt.NoModifier,
                )  # type: ignore[arg-type]
                QApplication.sendEvent(widget, ev)
                ev2 = QMouseEvent(
                    QEvent.Type.MouseButtonRelease,
                    widget.rect().center(),
                    button,
                    button,
                    Qt.NoModifier,
                )  # type: ignore[arg-type]
                QApplication.sendEvent(widget, ev2)
            except Exception:
                pass

        def mouseDClick(self, widget, button=None) -> None:
            if QTest is not None and Qt is not None:
                try:
                    from PySide6.QtTest import QTest as _QTest

                    _QTest.mouseDClick(widget, button or Qt.LeftButton)
                    return
                except Exception:
                    pass
            # Fallback: two clicks
            self.mouseClick(widget, button)
            self.mouseClick(widget, button)

        def assertNotEmitted(self, signal, timeout: int = 100) -> None:
            emitted = False

            def _on(*_):
                nonlocal emitted
                emitted = True

            try:
                signal.connect(_on)
            except Exception:
                pass
            deadline = time.time() + timeout / 1000.0
            while time.time() < deadline:
                if emitted:
                    break
                self.wait(10)
            try:
                signal.disconnect(_on)
            except Exception:
                pass
            assert not emitted, "Signal was emitted unexpectedly"

        def waitExposed(self, widget, timeout: int = 1000) -> None:
            # Basic exposure detection
            def _visible():
                try:
                    wh = (
                        widget.windowHandle()
                        if hasattr(widget, "windowHandle")
                        else None
                    )
                    return bool(getattr(widget, "isVisible", lambda: True)()) and (
                        wh is None or getattr(wh, "isExposed", lambda: True)()
                    )
                except Exception:
                    return True

            if hasattr(widget, "show"):
                try:
                    widget.show()
                except Exception:
                    pass
            self.waitUntil(_visible, timeout=timeout, interval=25)

    bot = _Bot()
    yield bot
    for c in bot._cleanups:
        try:
            c()
        except Exception:
            pass


@pytest.fixture
def monkeypatch():  # custom to ignore raising kw
    from pytest import MonkeyPatch

    mp = MonkeyPatch()
    original_setitem = mp.setitem

    def _setitem(mapping, name, value, raising=True):  # noqa: D401
        return original_setitem(mapping, name, value)

    mp.setitem = _setitem  # type: ignore[assignment]
    try:
        yield mp
    finally:
        mp.undo()

@pytest.fixture
def legacy_gas_state_factory():
    """Factory fixture producing LegacyGasState instances for legacy tests."""
    from src.pneumo.gas_state import LegacyGasState

    def _factory(*, pressure: float, volume: float, temperature: float, mass: float | None = None):
        return LegacyGasState(
            pressure=pressure,
            volume=volume,
            temperature=temperature,
            mass=mass,
        )

    return _factory
