"""Extended pytest configuration with enhanced qtbot and monkeypatch shims."""

from __future__ import annotations
import os
import sys
import time
import importlib.util
from pathlib import Path
from collections.abc import Callable
import pytest
import types

from tools.quality.skip_policy import EXPECTED_SKIP_TOKEN
from tests._qt_runtime import QT_SKIP_REASON

PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
SRC_PATH = PROJECT_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(1, str(SRC_PATH))

os.environ.setdefault("PYTHONHASHSEED", "0")
os.environ.setdefault("PSS_FORCE_NONBLOCKING_DIALOGS", "1")
os.environ.setdefault("PSS_SUPPRESS_UI_DIALOGS", "1")


def _env_flag(name: str, default: bool = False) -> bool:
    value = os.environ.get(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


_MARKERS = [
    "unit: Unit tests",
    "integration: Integration tests",
    "smoke: Smoke tests",
    "system: System tests",
    "slow: Slow tests",
    "performance: Performance budgets and timing checks",
    "gui: GUI/QML tests",
    "headless: Headless Qt tests",
    "scenario: Scenario physics tests",
    "qtbot: pytest-qt qtbot tests",
    "qt_no_exception_capture: Disable pytest-qt exception capture",
    "ui: Legacy UI tests",
]

_PYTESTQT_LOAD_ERROR: str | None = None


def _ensure_pytestqt_loaded(config: pytest.Config) -> None:
    """Load the pytest-qt plugin when plugin autoload is disabled.

    CI runs set ``PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`` to avoid picking up
    globally-installed plugins. In this mode ``pytest-qt`` is not loaded
    automatically even though it is present in the environment, which would
    leave the ``qtbot`` fixture unresolved. Import the plugin explicitly when
    available and remember any failure so we can skip qtbot-driven tests with
    a descriptive reason instead of raising fixture errors.
    """

    global _PYTESTQT_LOAD_ERROR

    if QT_SKIP_REASON is not None:
        return

    plugin_manager = config.pluginmanager
    if plugin_manager.get_plugin("pytestqt") or plugin_manager.get_plugin(
        "pytestqt.plugin"
    ):
        return

    try:
        plugin_manager.import_plugin("pytestqt.plugin")
    except Exception as exc:  # pragma: no cover - environment specific
        _PYTESTQT_LOAD_ERROR = str(exc)


@pytest.hookimpl(tryfirst=True)
def pytest_configure(config: pytest.Config) -> None:
    for marker in _MARKERS:
        config.addinivalue_line("markers", marker)

    _ensure_pytestqt_loaded(config)


@pytest.hookimpl(tryfirst=True)
def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    if QT_SKIP_REASON is None and _PYTESTQT_LOAD_ERROR is None:
        return

    skip_reason = QT_SKIP_REASON or _PYTESTQT_LOAD_ERROR or "pytest-qt unavailable"
    skip_marker = pytest.mark.skip(  # pytest-skip-ok: skip when Qt runtime is missing
        reason=skip_reason
    )

    for item in items:
        if "qtbot" in getattr(item, "fixturenames", ()):  # pragma: no branch
            item.add_marker(skip_marker)


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--allow-skips",
        action="store_true",
        default=False,
        help=(
            "Allow skipped tests without failing the run. "
            "Use only when paired with CI_SKIP_REASON for traceability."
        ),
    )


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
def baseline_images_dir(tmp_path_factory: pytest.TempPathFactory) -> Path:
    """Provide baseline render artifacts for visual regression tests."""

    from PIL import Image

    base_dir = tmp_path_factory.mktemp("baseline_images")
    reference_path = base_dir / "qt_scene_reference.png"
    if not reference_path.exists():
        reference_image = Image.new("RGB", (8, 8), color=(120, 160, 200))
        reference_image.save(reference_path)
    return reference_path.parent


@pytest.fixture(scope="session")
def headless_env() -> dict[str, str]:
    """Apply Qt headless defaults to the process environment."""

    from tests._qt_headless import apply_headless_defaults

    apply_headless_defaults(os.environ)
    return os.environ


@pytest.fixture(scope="session")
def headless_qt_modules():
    """Provide lightweight PySide6/pytestqt shims for headless execution.

    When the real modules are unavailable (e.g. in minimal CI runners), inject
    stub implementations sufficient for tests that rely only on simple Qt
    behaviours such as event pumping and timing helpers.
    """

    from tests._qt_headless import headless_requested

    added: list[str] = []
    force_stub = headless_requested(os.environ)

    def _install(name: str, module: object) -> None:
        if name not in sys.modules:
            sys.modules[name] = module
            added.append(name)

    def _spec(name: str):
        return importlib.util.spec_from_loader(name, loader=None)

    try:
        if force_stub:
            raise ImportError("force stubbed Qt modules for headless mode")
        import PySide6  # type: ignore  # noqa: F401
    except Exception:
        qt_package = types.SimpleNamespace(__spec__=_spec("PySide6"), __path__=[])

        class _StubSignal:
            def __init__(self, *args, **kwargs):  # noqa: D401
                self._handlers: list[Callable[..., None]] = []

            def connect(self, handler: Callable[..., None]) -> None:
                self._handlers.append(handler)

            def disconnect(self, handler: Callable[..., None]) -> None:
                try:
                    self._handlers.remove(handler)
                except ValueError:
                    return None

            def emit(self, *args, **kwargs) -> None:  # noqa: ANN002, ANN003
                for handler in list(self._handlers):
                    handler(*args, **kwargs)

        class _StubProperty:  # pragma: no cover - descriptor semantics
            def __init__(self, _type: str, fget=None, fset=None, notify=None):
                self.fget = fget
                self.fset = fset

            def __get__(self, instance, owner=None):  # noqa: ANN001
                if instance is None:
                    return self
                if self.fget is None:
                    return None
                return self.fget(instance)

            def __set__(self, instance, value):  # noqa: ANN001, ANN204
                if self.fset is not None:
                    self.fset(instance, value)

        class _StubQCoreApplication:
            @staticmethod
            def processEvents() -> None:  # noqa: N802 - Qt naming convention
                return None

        class _StubQt:
            LeftButton = 1
            NoModifier = 0

        class _StubQEvent:
            class Type:
                KeyPress = "key_press"
                KeyRelease = "key_release"
                MouseButtonPress = "mouse_press"
                MouseButtonRelease = "mouse_release"

        class _StubQObject:
            def __init__(self, *args, **kwargs):  # noqa: ANN001, D401
                super().__init__()

        class _StubQApplication:
            _instance = None

            def __init__(self, *args, **kwargs):  # noqa: ANN001, D401
                type(self)._instance = self

            @classmethod
            def instance(cls):  # noqa: D401
                return cls._instance

            @staticmethod
            def sendEvent(*args, **kwargs) -> None:  # noqa: ANN001, ANN003
                return None

            def quit(self) -> None:
                type(self)._instance = None

        class _StubQMouseEvent:
            def __init__(self, *args, **kwargs):  # noqa: ANN001, D401
                self.args = args
                self.kwargs = kwargs

        class _StubQKeyEvent(_StubQMouseEvent):
            pass

        class _StubQTest:
            @staticmethod
            def qWait(ms: int) -> None:
                time.sleep(ms / 1000.0)

            @staticmethod
            def qWaitForWindowExposed(widget) -> None:  # noqa: ANN001, D401
                return None

            @staticmethod
            def keyClick(*args, **kwargs) -> None:  # noqa: ANN002, ANN003
                return None

            @staticmethod
            def keyClicks(*args, **kwargs) -> None:  # noqa: ANN002, ANN003
                return None

            @staticmethod
            def mouseClick(*args, **kwargs) -> None:  # noqa: ANN002, ANN003
                return None

            @staticmethod
            def mouseDClick(*args, **kwargs) -> None:  # noqa: ANN002, ANN003
                return None

        qt_core = types.SimpleNamespace(
            QCoreApplication=_StubQCoreApplication,  # type: ignore[assignment]
            Qt=_StubQt,
            QEvent=_StubQEvent,
            QObject=_StubQObject,
            Signal=_StubSignal,
            Property=_StubProperty,
            __spec__=_spec("PySide6.QtCore"),
        )
        qt_widgets = types.SimpleNamespace(
            QApplication=_StubQApplication, __spec__=_spec("PySide6.QtWidgets")
        )
        qt_test = types.SimpleNamespace(
            QTest=_StubQTest, __spec__=_spec("PySide6.QtTest")
        )
        qt_gui = types.SimpleNamespace(
            QMouseEvent=_StubQMouseEvent,
            QKeyEvent=_StubQKeyEvent,
            __spec__=_spec("PySide6.QtGui"),
        )
        qt_qml = types.SimpleNamespace(QJSValue=None, __spec__=_spec("PySide6.QtQml"))

        _install("PySide6", qt_package)
        _install("PySide6.QtCore", qt_core)
        _install("PySide6.QtWidgets", qt_widgets)
        _install("PySide6.QtTest", qt_test)
        _install("PySide6.QtGui", qt_gui)
        _install("PySide6.QtQml", qt_qml)

    try:
        import pytestqt  # type: ignore  # noqa: F401
    except Exception:
        _install("pytestqt", types.SimpleNamespace())

    try:
        yield
    finally:
        for name in added:
            sys.modules.pop(name, None)


@pytest.fixture
def headless_qtbot(request):
    """Provide a QtBot substitute when pytest-qt is unavailable."""

    try:
        return request.getfixturevalue("qtbot")
    except pytest.FixtureLookupError:
        pass

    class _StubQtBot:
        def waitUntil(self, condition: Callable[[], bool], timeout: int = 1000) -> None:
            deadline = time.time() + timeout / 1000.0
            while time.time() < deadline:
                if condition():
                    return None
                time.sleep(0.01)
            raise AssertionError("waitUntil timed out")

        def wait(self, timeout: int = 100) -> None:
            """Mimic pytest-qt's ``wait`` helper using a simple sleep."""

            time.sleep(timeout / 1000.0)

    return _StubQtBot()


@pytest.fixture(scope="session")
def qapp():
    try:
        from PySide6.QtWidgets import QApplication  # type: ignore
    except Exception:
        yield None
        return
    # Ensure Qt uses a platform plugin that works in headless Linux containers
    # while still allowing Windows/macOS agents to override as needed.
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
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


def _extract_skip_reason(report: pytest.TestReport) -> str:
    message = getattr(report, "longrepr", "")
    if isinstance(message, tuple) and len(message) == 3:
        return str(message[2])
    if hasattr(message, "reprcrash") and getattr(message.reprcrash, "message", None):
        return str(message.reprcrash.message)
    if hasattr(message, "message"):
        return str(message.message)
    return str(message)


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:  # noqa: ARG001
    config = session.config
    allow_skips = bool(config.getoption("--allow-skips"))
    env_allow = _env_flag("PSS_ALLOW_SKIPPED_TESTS") or _env_flag("CI_ALLOW_SKIPS")
    justification = os.environ.get("CI_SKIP_REASON", "").strip()
    if env_allow and not justification:
        pytest.exit(
            "CI_SKIP_REASON is required when allowing skipped tests via environment",
            returncode=1,
        )
    if allow_skips or env_allow:
        return

    terminal_reporter = config.pluginmanager.get_plugin("terminalreporter")
    if terminal_reporter is None:
        return

    skipped_reports = list(terminal_reporter.stats.get("skipped", []))
    unexpected: list[tuple[str, str]] = []
    for report in skipped_reports:
        reason = _extract_skip_reason(report)
        if EXPECTED_SKIP_TOKEN in reason:
            continue
        unexpected.append((report.nodeid, reason))

    if not unexpected:
        return

    header = f"{len(unexpected)} unexpected skipped test(s) detected"
    terminal_reporter.write_sep("=", header, red=True)
    for nodeid, reason in unexpected:
        terminal_reporter.line(f"- {nodeid}: {reason}")
    session.exitstatus = pytest.ExitCode.TESTS_FAILED


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


@pytest.fixture
def training_preset_bridge(settings_manager):
    """Provide a TrainingPresetBridge instance for UI and simulation tests."""

    from src.ui.bridge import TrainingPresetBridge

    bridge = TrainingPresetBridge(settings_manager=settings_manager)
    yield bridge
    try:
        bridge.deleteLater()
    except Exception:
        pass


@pytest.fixture
def simulation_harness():
    """Lightweight simulation harness stub used by preset bridge tests."""

    def _run(runtime_ms: int = 0) -> dict[str, float | int]:
        duration = max(0, int(runtime_ms))
        steps = max(1, duration // 2 or 1)
        return {
            "duration_ms": duration,
            "runtime_ms": duration,
            "steps": steps,
            "avg_step_time_ms": 0.5,
            "fps_actual": 60.0,
            "realtime_factor": 1.0,
            "frames_dropped": 0,
            "integration_failures": 0,
            "efficiency": 0.99,
        }

    return _run


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
                    if hasattr(widget, "isWindow") and callable(widget.isWindow):
                        try:
                            if widget.isWindow():
                                QTest.qWaitForWindowExposed(widget)
                        except Exception:
                            pass
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

        def assertNotEmitted(self, signal, timeout: int = 100) -> object:
            """Context manager asserting that a signal is NOT emitted."""

            class _NotEmittedCtx:
                def __init__(self, sig, to):
                    self._sig = sig
                    self._timeout = to
                    self._emitted = False

                def __enter__(self):
                    try:
                        self._sig.connect(self._on_emit)
                    except Exception:
                        pass
                    return self

                def _on_emit(self, *args):
                    self._emitted = True

                def __exit__(self, exc_type, exc, tb):
                    deadline = time.time() + self._timeout / 1000.0
                    while time.time() < deadline and not self._emitted:
                        if QTest is not None:
                            try:
                                QTest.qWait(10)
                            except Exception:
                                break
                        else:
                            time.sleep(0.01)
                    try:
                        self._sig.disconnect(self._on_emit)
                    except Exception:
                        pass
                    assert not self._emitted, "Signal was emitted unexpectedly"
                    return False

            return _NotEmittedCtx(signal, timeout)

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

    def _factory(
        *, pressure: float, volume: float, temperature: float, mass: float | None = None
    ):
        return LegacyGasState(
            pressure=pressure,
            volume=volume,
            temperature=temperature,
            mass=mass,
        )

    return _factory


@pytest.fixture(scope="session")
def physics_case_loader():
    """Provide access to pre-defined suspension physics regression cases."""

    from tests.physics.cases.loader import build_case_loader

    return build_case_loader()
