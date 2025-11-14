"""Pytest configuration and shared fixtures."""

import importlib
import os
import sys
from ctypes import util as ctypes_util
from functools import lru_cache
from pathlib import Path
from collections.abc import Callable
from typing import Any

import pytest
from pytest import MonkeyPatch

from tests._qt_headless import (
    HEADLESS_DEFAULTS,
    HEADLESS_FLAG,
    apply_headless_defaults,
    headless_requested,
)
from tests.physics.cases import build_case_loader
from tests._qt_runtime import QT_SKIP_REASON, disable_pytestqt
from tests.helpers import ensure_qt_runtime, require_qt_modules

pytest_plugins: tuple[str, ...] = ()

_ORIGINAL_IMPORTORSKIP = pytest.importorskip


def _strict_importorskip(module_name: str, *args, **kwargs):
    """Enforce hard failures for Qt-related optional imports."""

    if module_name.startswith(("PySide6", "pytestqt")):
        module, *_ = require_qt_modules(module_name)
        return module
    return _ORIGINAL_IMPORTORSKIP(module_name, *args, **kwargs)


pytest.importorskip = _strict_importorskip

# --- pytest-qt plugin bootstrap -------------------------------------------------


def _load_pytestqt_plugin(config: pytest.Config) -> None:
    """(Re)import pytest-qt plugin when available and not blocked by runtime guards."""
    pm = config.pluginmanager
    if QT_SKIP_REASON is not None:
        disable_pytestqt(pm)
        return

    plugin = pm.get_plugin("pytestqt.plugin")
    if plugin is None:
        # Some environments register the plugin under the ``pytestqt`` alias
        # before we get a chance to import it. Guard against double
        # registration by probing common aliases and ignoring the error if the
        # module is already present.
        plugin = pm.get_plugin("pytestqt")
    if plugin is None:
        try:
            pm.import_plugin("pytestqt.plugin")
        except ValueError as exc:
            # ``pytest`` raises ``ValueError`` when the plugin is already
            # registered under a different name. That scenario is harmless for
            # our bootstrap routine, so swallow the error and continue.
            if "already registered" not in str(exc):
                raise
    os.environ.setdefault("PYTEST_QT_API", "pyside6")
    _install_qtbot_compat_shims()


def _install_qtbot_compat_shims() -> None:
    """Inject backward-compatibility helpers for older tests.

    * addCleanup: Some historical test suites relied on ``qtbot.addCleanup`` mirroring
      unittest semantics. Modern pytest-qt exposes finalizers through ``request`` only.
    """
    if QT_SKIP_REASON is not None:
        return
    try:
        from pytestqt.qtbot import QtBot  # type: ignore
    except Exception:
        return
    if hasattr(QtBot, "addCleanup"):
        return

    def addCleanup(self, func):  # type: ignore[override]
        """Register a finalizer callable for the current test."""
        req = getattr(self, "_request", None)
        if req is not None:
            try:
                req.addfinalizer(func)
            except Exception:
                pass

    QtBot.addCleanup = addCleanup  # type: ignore[attr-defined]


# --- Fallback qtbot fixture (если плагин pytest-qt недоступен) ------------------
# Добавляем минимальный адаптор, чтобы тесты не падали при отсутствии плагина.
# Реализованы методы wait, waitUntil, addWidget, addCleanup для совместимости.
try:
    import importlib.util as _imp_util

    _spec = _imp_util.find_spec("pytestqt.plugin")
except Exception:
    _spec = None

if _spec is None:

    @pytest.fixture
    def qtbot(qapp):  # noqa: D401
        """Упрощённый QtBot fallback без полного функционала pytest-qt.

        Предназначен для базовых ожиданий и регистрации виджетов.
        """
        from PySide6.QtTest import QTest
        import time

        class _FallbackQtBot:  # минимальный адаптер
            def __init__(self):
                self._cleanups: list[Callable[[], Any]] = []

            def addWidget(self, widget):  # совместимость с тестами
                # В реальном QtBot происходит трекинг; нам достаточно ссылки
                setattr(self, "_last_widget", widget)

            def wait(self, ms: int) -> None:
                QTest.qWait(ms)

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
                    QTest.qWait(interval)
                raise AssertionError("waitUntil timeout")

            def addCleanup(self, func: Callable[[], Any]) -> None:
                self._cleanups.append(func)

        bot = _FallbackQtBot()
        yield bot
        for c in bot._cleanups:
            try:
                c()
            except Exception:
                pass


# --- MonkeyPatch compatibility wrapper ------------------------------------------


@pytest.fixture
def monkeypatch():  # type: ignore[override]
    """Extended MonkeyPatch fixture accepting the legacy ``raising`` kw in ``setitem``.

    Some tests still invoke ``monkeypatch.setitem(..., raising=False)`` which is only
    supported in newer pytest versions. This shim ignores the flag for backwards
    compatibility while delegating to the original implementation.
    """
    mp = MonkeyPatch()
    original_setitem = mp.setitem

    def _setitem(mapping, name, value, raising=True):  # noqa: D401
        return original_setitem(mapping, name, value)

    mp.setitem = _setitem  # type: ignore[assignment]
    try:
        yield mp
    finally:
        mp.undo()


# --- Path / deterministic environment -------------------------------------------

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
src_path = str(project_root / "src")
if src_path not in sys.path:
    sys.path.insert(1, src_path)

os.environ.setdefault("PYTHONHASHSEED", "0")
# Глобально отключаем блокирующие UI-диалоги в тестах
os.environ.setdefault("PSS_FORCE_NONBLOCKING_DIALOGS", "1")
os.environ.setdefault("PSS_SUPPRESS_UI_DIALOGS", "1")

# --- Marker & headless configuration -------------------------------------------


def _register_headless_marker(config: pytest.Config) -> None:
    config.addinivalue_line(
        "markers",
        "headless: request Qt headless defaults (sets PSS_HEADLESS=1, QT_QPA_PLATFORM=offscreen)",
    )


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--pss-headless",
        action="store_true",
        default=False,
        help="Force Qt headless defaults for the entire test session (equivalent to PSS_HEADLESS=1).",
    )
    parser.addoption(
        "--allow-skips",
        action="store_true",
        default=False,
        help=(
            "Permit skipped tests without failing the session. "
            "Use sparingly: CI and local quality gates treat skips as errors by default."
        ),
    )


def _configure_session_headless(config: pytest.Config) -> None:
    cli = bool(config.getoption("--pss-headless"))
    env_flag = headless_requested()
    active = cli or env_flag
    setattr(config, "_pss_headless_session", active)
    if cli and not env_flag:
        os.environ[HEADLESS_FLAG] = "1"
    if active:
        apply_headless_defaults()


# --- Skip enforcement -----------------------------------------------------------


def _parse_env_bool(value: str | None) -> bool | None:
    if value is None:
        return None
    normalized = value.strip().lower()
    if not normalized:
        return None
    truthy = {"1", "true", "yes", "on"}
    falsy = {"0", "false", "no", "off"}
    if normalized in truthy:
        return True
    if normalized in falsy:
        return False
    return None


def _skips_allowed(config: pytest.Config) -> bool:
    env_override = _parse_env_bool(os.environ.get("PSS_ALLOW_SKIPPED_TESTS"))
    if env_override is not None:
        return env_override
    return bool(config.getoption("--allow-skips"))


# --- Platform capability checks -------------------------------------------------


def _qt_display_available() -> bool:
    platform = os.environ.get("QT_QPA_PLATFORM", "").strip().lower()
    if platform in {"offscreen", "minimal"}:
        return True
    if sys.platform.startswith("linux"):
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
    return True


def _libgl_available() -> bool:
    if not sys.platform.startswith("linux"):
        return True
    if ctypes_util.find_library("GL"):
        return True
    return any(
        Path(p).exists()
        for p in (
            "/usr/lib/x86_64-linux-gnu/libGL.so.1",
            "/usr/lib64/libGL.so.1",
        )
    )


try:
    _pytestqt_spec = importlib.util.find_spec("pytestqt.plugin")
except ModuleNotFoundError:
    _pytestqt_spec = None
_qtwidgets_spec = importlib.util.find_spec("PySide6.QtWidgets")
if _pytestqt_spec is None:
    _gui_skip_reason = "pytest-qt plugin is not installed"
elif _qtwidgets_spec is None:
    _gui_skip_reason = "PySide6 is not available"
elif not _libgl_available():
    _gui_skip_reason = "System OpenGL libraries (libGL) are missing"
elif not _qt_display_available():
    _gui_skip_reason = "No display backend detected for Qt"
else:
    _gui_skip_reason = None

try:
    importlib.import_module("PySide6.QtCharts")
except Exception as _qtcharts_exc:  # pragma: no cover - platform dependent
    _qtcharts_skip_reason = f"PySide6.QtCharts import failed: {_qtcharts_exc}"
else:
    _qtcharts_skip_reason = None


def _iter_targets_file(path: Path) -> list[str]:
    if not path.exists():
        return []
    return [
        line.strip()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    ]


@lru_cache(maxsize=1)
def _integration_target_roots(config_root: Path) -> tuple[Path, ...]:
    candidates: list[Path] = []
    targets_file = config_root / "pytest_integration_targets.txt"
    for entry in _iter_targets_file(targets_file):
        candidate = (config_root / entry).resolve()
        if candidate.exists():
            candidates.append(candidate)
    default_root = (config_root / "tests" / "integration").resolve()
    if default_root.exists() and default_root not in candidates:
        candidates.append(default_root)
    return tuple(candidates)


# --- Global pytest hooks --------------------------------------------------------


def pytest_configure(config: pytest.Config) -> None:
    os.environ.setdefault("PSS_SUPPRESS_UI_DIALOGS", "1")

    _load_pytestqt_plugin(config)
    _register_headless_marker(config)
    _configure_session_headless(config)
    # Ensure critical markers always registered (including 'gui')
    for name, description in (
        ("unit", "Unit tests for individual components"),
        ("integration", "Integration tests"),
        ("smoke", "Lightweight smoke scenarios"),
        ("system", "End-to-end system tests"),
        ("ui", "Qt widgets, panel controllers, and state sync tests"),
        ("gui", "Tests requiring GUI/QML"),  # добавлено явное объявление
        (
            "qtbot",
            "Tests using pytest-qt QtBot fixture",
        ),  # регистрация маркера для ошибок коллекции
        ("scenario", "Scenario-based end-to-end checks for pneumatic coupling"),
    ):
        try:
            config.addinivalue_line("markers", f"{name}: {description}")
        except Exception:
            pass

    # Автосоздание локальной директории basetemp (--basetemp=.tmp/pytest)
    try:
        base_temp_dir = getattr(config.option, "basetemp", None)
        if base_temp_dir:
            Path(str(base_temp_dir)).mkdir(parents=True, exist_ok=True)
            os.environ.setdefault(
                "PSS_PYTEST_BASETEMP", str(Path(str(base_temp_dir)).resolve())
            )
    except Exception:
        # Тихо игнорируем ошибки — pytest сам упадёт при невозможности записи
        pass

    # Pre-import real physics helpers to prevent test stubs from shadowing them
    # across the entire session (tests/physics/test_runtime_pneumo_system.py installs
    # a minimal 'src.physics.forces' stub if the module isn't loaded yet).
    try:
        importlib.import_module("src.physics.forces")
    except Exception:
        # If import fails here, individual tests will surface proper diagnostics.
        pass


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    roots = _integration_target_roots(Path(str(config.rootpath)).resolve())
    if not roots:
        return
    for item in items:
        try:
            item_path = Path(str(item.fspath)).resolve()
        except Exception:
            continue
        for root in roots:
            try:
                relative = item_path.is_relative_to(root)
            except AttributeError:  # pragma: no cover - Python <3.9 guard
                try:
                    item_path.relative_to(root)
                    relative = True
                except Exception:
                    relative = False
            if relative:
                item.add_marker("integration")
                break


def pytest_runtest_setup(item: pytest.Item) -> None:
    gui_fixtures = {"qtbot", "qapp"}
    if QT_SKIP_REASON is not None and (
        "gui" in item.keywords
        or set(getattr(item, "fixturenames", ())).intersection(gui_fixtures)
    ):
        pytest.fail(
            "Qt runtime prerequisites are not satisfied: "
            f"{QT_SKIP_REASON}.\nRun `python -m tools.cross_platform_test_prep --use-uv --run-tests` "
            "from the repository root to install missing dependencies on the active platform."
        )


def pytest_report_header(config: pytest.Config) -> list[str]:
    if QT_SKIP_REASON is None:
        return ["Qt runtime validation: ready"]
    return ["Qt runtime validation: missing prerequisites", f"Reason: {QT_SKIP_REASON}"]


def pytest_terminal_summary(terminalreporter, exitstatus: int, config: pytest.Config):  # noqa: D401
    """Fail the session when tests were skipped without explicit approval."""

    if _skips_allowed(config):
        return

    skipped = terminalreporter.stats.get("skipped", [])
    if not skipped:
        return

    count = len(skipped)
    plural = "s" if count != 1 else ""
    terminalreporter.write_sep(
        "!",
        (
            f"{count} skipped test{plural} detected; rerun after installing missing dependencies. "
            "Use --allow-skips or PSS_ALLOW_SKIPPED_TESTS=1 only when intentionally acknowledging the skips."
        ),
    )
    session = getattr(terminalreporter, "_session", None)
    if session is not None:
        session.exitstatus = pytest.ExitCode.TESTSFAILED
    setattr(config, "_pss_skip_failure", True)


def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:  # noqa: D401
    """Ensure skip enforcement propagates to the exit status when needed."""

    if _skips_allowed(session.config):
        return
    if getattr(session.config, "_pss_skip_failure", False):
        session.exitstatus = pytest.ExitCode.TESTSFAILED


# --- Security audit log ---------------------------------------------------------
_security_audit_dir = project_root / "reports" / "security_audit"
_security_audit_dir.mkdir(parents=True, exist_ok=True)
os.environ.setdefault("PSS_SECURITY_AUDIT_LOG", str(_security_audit_dir / "test.log"))

_SETTINGS_TEMPLATE = Path("config/app_settings.json").read_text(encoding="utf-8")


def _write_settings_payload(target: Path) -> Path:
    target.write_text(_SETTINGS_TEMPLATE, encoding="utf-8")
    return target


@pytest.fixture(autouse=True)
def _apply_headless_marker(
    request: pytest.FixtureRequest, monkeypatch: MonkeyPatch
) -> None:
    if getattr(request.config, "_pss_headless_session", False):
        return
    marker = request.node.get_closest_marker("headless")
    if marker is None:
        return
    monkeypatch.setenv(HEADLESS_FLAG, "1")
    for key, value in HEADLESS_DEFAULTS.items():
        monkeypatch.setenv(key, value)


# --- Shared fixtures ------------------------------------------------------------


@pytest.fixture(scope="session")
def project_root_path() -> Path:
    return project_root


@pytest.fixture(scope="session")
def reports_tests_dir(project_root_path: Path) -> Path:
    target = project_root_path / "reports" / "tests"
    target.mkdir(parents=True, exist_ok=True)
    return target


@pytest.fixture(scope="session")
def integration_reports_dir(reports_tests_dir: Path) -> Path:
    target = reports_tests_dir / "integration"
    target.mkdir(parents=True, exist_ok=True)
    return target


@pytest.fixture(scope="session")
def qt_runtime_ready() -> None:
    ensure_qt_runtime()


@pytest.fixture(scope="session")
def baseline_images_dir(project_root_path: Path) -> Path:
    target = project_root_path / "tests" / "baseline_images"
    target.mkdir(parents=True, exist_ok=True)
    reference_path = target / "qt_scene_reference.png"
    if not reference_path.exists():
        image_module = pytest.importorskip(
            "PIL.Image", reason="Pillow required for baseline image"
        )
        image = image_module.new("RGB", (8, 8), color=(120, 160, 200))
        image.save(reference_path)
    return target


@pytest.fixture(scope="session")
def physics_case_loader():
    return build_case_loader()


@pytest.fixture
def sample_geometry_params():
    from src.core.geometry import GeometryParams

    geometry = GeometryParams()
    geometry.wheelbase = 2.5
    geometry.lever_length = 0.4
    geometry.cylinder_inner_diameter = 0.08
    geometry.enforce_track_from_geometry()
    return geometry


@pytest.fixture
def sample_cylinder_params() -> dict[str, float]:
    return {
        "inner_diameter": 0.08,
        "rod_diameter": 0.035,
        "piston_thickness": 0.02,
        "body_length": 0.25,
        "dead_zone_rod": 0.001,
        "dead_zone_head": 0.001,
    }


@pytest.fixture(scope="session")
def qapp():  # noqa: D401
    pytest.importorskip(
        "PySide6.QtWidgets",
        reason="PySide6 QtWidgets required for QApplication fixture",
    )
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance() or QApplication(sys.argv)
    yield app


@pytest.fixture
def temp_settings_file(tmp_path: Path) -> Path:
    return _write_settings_payload(tmp_path / "app_settings.json")


@pytest.fixture
def settings_service(monkeypatch: MonkeyPatch, temp_settings_file: Path):
    from src.core.settings_service import SettingsService

    monkeypatch.setenv("PSS_SETTINGS_FILE", str(temp_settings_file))
    return SettingsService(settings_path=temp_settings_file)


@pytest.fixture
def settings_manager(monkeypatch: MonkeyPatch, temp_settings_file: Path):
    from src.common import settings_manager as sm

    monkeypatch.setenv("PSS_SETTINGS_FILE", str(temp_settings_file))
    monkeypatch.setattr(sm, "_settings_manager", None)
    monkeypatch.setattr(sm, "_settings_event_bus", sm.SettingsEventBus())
    return sm.SettingsManager(settings_file=temp_settings_file)


@pytest.fixture
def reference_suspension_linkage():
    from src.mechanics.linkage_geometry import SuspensionLinkage

    return SuspensionLinkage.from_mm(
        pivot=(200.0, 0.0),
        free_end=(500.0, 0.0),
        rod_joint=(450.0, 0.0),
        cylinder_tail=(150.0, 500.0),
        cylinder_body_length=300.0,
    )


@pytest.fixture
def legacy_gas_state_factory() -> Callable[..., "LegacyGasState"]:
    from src.pneumo.gas_state import LegacyGasState

    def _factory(
        *, pressure: float, volume: float, temperature: float
    ) -> LegacyGasState:
        return LegacyGasState(pressure=pressure, volume=volume, temperature=temperature)

    return _factory


@pytest.fixture
def hysteretic_check_valve():
    from src.pneumo.enums import CheckValveKind
    from src.pneumo.valves import CheckValve

    return CheckValve(
        kind=CheckValveKind.ATMO_TO_LINE, delta_open_min=1_500.0, d_eq=0.02, hyst=600.0
    )


@pytest.fixture
def relief_valve_reference():
    from src.pneumo.enums import ReliefValveKind
    from src.pneumo.valves import ReliefValve

    return ReliefValve(
        kind=ReliefValveKind.STIFFNESS, p_set=200_000.0, d_eq=0.02, hyst=5_000.0
    )


@pytest.fixture
def structlog_logger_config():
    from src.diagnostics.logger_factory import LoggerConfig

    return LoggerConfig(
        name="pss.tests.structlog",
        context=(("subsystem", "diagnostics"), ("component", "logger")),
    )


@pytest.fixture
def training_preset_bridge(settings_manager):
    pytest.importorskip(
        "PySide6.QtCore", reason="PySide6 QtCore required for TrainingPresetBridge"
    )
    from src.simulation.presets import get_default_training_library
    from src.ui.bridge.training_bridge import TrainingPresetBridge

    bridge = TrainingPresetBridge(
        settings_manager=settings_manager, library=get_default_training_library()
    )
    yield bridge
    bridge.deleteLater()


@pytest.fixture
def simulation_harness(qapp, qtbot):
    pytest.importorskip(
        "PySide6.QtCore", reason="PySide6 QtCore required for simulation harness"
    )
    try:
        from src.runtime.sim_loop import SimulationManager
    except Exception as exc:  # pragma: no cover
        pytest.fail(
            (
                "Simulation stack unavailable: "
                f"{exc}. Re-run `python -m tools.cross_platform_test_prep --use-uv --run-tests` "
                "to rebuild runtime dependencies before executing GUI suites."
            ),
            pytrace=False,
        )
    manager = SimulationManager()

    def _run(*, runtime_ms: int = 50) -> dict[str, Any]:
        manager.start()

        def _thread_running() -> bool:
            return manager.physics_thread.isRunning()

        qtbot.waitUntil(_thread_running, timeout=2000)
        qtbot.wait(runtime_ms)
        metrics: dict[str, Any] | None = None
        worker = getattr(manager, "physics_worker", None)
        performance = getattr(worker, "performance", None)
        if performance is not None:
            try:
                metrics = performance.get_summary()
            except Exception:  # pragma: no cover - diagnostics only
                metrics = None

        manager.stop()
        qtbot.waitUntil(lambda: not manager.physics_thread.isRunning(), timeout=2000)

        return metrics or {}

    yield _run
    try:
        manager.stop()
        manager.physics_thread.wait(500)
    finally:
        manager.deleteLater()


@pytest.fixture
def geometry_bridge(sample_geometry_params):
    pytest.importorskip(
        "PySide6.QtGui", reason="PySide6 QtGui required for geometry bridge conversion"
    )
    from src.ui.geometry_bridge import create_geometry_converter

    return create_geometry_converter(
        wheelbase=sample_geometry_params.wheelbase,
        lever_length=sample_geometry_params.lever_length,
        cylinder_diameter=sample_geometry_params.cylinder_inner_diameter,
    )


# --- Session teardown -----------------------------------------------------------


def pytest_unconfigure(config: pytest.Config) -> None:  # noqa: D401
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        return
    app = QApplication.instance()
    if app is not None:
        app.quit()
