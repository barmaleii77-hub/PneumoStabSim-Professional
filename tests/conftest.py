"""Pytest configuration and shared fixtures."""

import inspect
import os
import sys
from pathlib import Path
from typing import Mapping

import importlib.util

import pytest
from _pytest.monkeypatch import notset
from pytest import MonkeyPatch


try:
    _pytestqt_spec = importlib.util.find_spec("pytestqt.plugin")
except ModuleNotFoundError:  # pragma: no cover - optional dependency missing
    _pytestqt_spec = None

if _pytestqt_spec is not None:
    pytest_plugins = ("pytestqt.plugin",)
else:  # pragma: no cover - fallback for minimal environments
    pytest_plugins: tuple[str, ...] = ()

if "raising" not in inspect.signature(MonkeyPatch.setitem).parameters:

    def _compat_setitem(
        self: MonkeyPatch,
        dic: Mapping[str, object] | dict[str, object],
        name: str,
        value: object,
        *,
        raising: bool = True,
    ) -> None:
        getter = getattr(dic, "get", None)
        if callable(getter):
            previous = getter(name, notset)
        else:
            previous = dic[name] if name in dic else notset  # type: ignore[index]

        self._setitem.append((dic, name, previous))
        dic[name] = value  # type: ignore[index]

    MonkeyPatch.setitem = _compat_setitem  # type: ignore[assignment]

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "src"))

# Set up environment variables for testing
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")
os.environ.setdefault("PYTHONHASHSEED", "0")


_SETTINGS_TEMPLATE = Path("config/app_settings.json").read_text(encoding="utf-8")


def _write_settings_payload(target: Path) -> Path:
    target.write_text(_SETTINGS_TEMPLATE, encoding="utf-8")
    return target


@pytest.fixture(scope="session")
def project_root_path():
    """Provide project root path"""
    return project_root


@pytest.fixture
def sample_geometry_params():
    """Provide sample geometry parameters"""
    from src.core.geometry import GeometryParams

    geometry = GeometryParams()
    geometry.wheelbase = 2.5
    geometry.lever_length = 0.4
    geometry.cylinder_inner_diameter = 0.08
    geometry.enforce_track_from_geometry()

    return geometry


@pytest.fixture
def sample_cylinder_params():
    """Provide sample cylinder parameters"""
    return {
        "inner_diameter": 0.08,
        "rod_diameter": 0.035,
        "piston_thickness": 0.02,
        "body_length": 0.25,
        "dead_zone_rod": 0.001,
        "dead_zone_head": 0.001,
    }


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication for Qt tests"""
    pytest.importorskip(
        "PySide6.QtWidgets",
        reason="PySide6 QtWidgets module is required for QApplication fixture",
        exc_type=ImportError,
    )
    from PySide6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    yield app

    # Cleanup handled by Qt


@pytest.fixture
def temp_settings_file(tmp_path: Path) -> Path:
    """Provide an isolated copy of ``config/app_settings.json`` for tests."""

    return _write_settings_payload(tmp_path / "app_settings.json")


@pytest.fixture
def settings_service(monkeypatch: MonkeyPatch, temp_settings_file: Path):
    """Return a :class:`SettingsService` bound to the temporary settings file."""

    from src.core.settings_service import SettingsService

    monkeypatch.setenv("PSS_SETTINGS_FILE", str(temp_settings_file))
    return SettingsService(settings_path=temp_settings_file)


@pytest.fixture
def settings_manager(monkeypatch: MonkeyPatch, temp_settings_file: Path):
    """Return an isolated :class:`SettingsManager` with fresh event bus."""

    from src.common import settings_manager as sm

    monkeypatch.setenv("PSS_SETTINGS_FILE", str(temp_settings_file))
    monkeypatch.setattr(sm, "_settings_manager", None, raising=False)
    monkeypatch.setattr(sm, "_settings_event_bus", sm.SettingsEventBus(), raising=False)
    return sm.SettingsManager(settings_file=temp_settings_file)


@pytest.fixture
def training_preset_bridge(settings_manager):
    """Expose a :class:`TrainingPresetBridge` connected to the isolated settings."""

    pytest.importorskip(
        "PySide6.QtCore",
        reason="PySide6 QtCore module is required for TrainingPresetBridge fixtures",
        exc_type=ImportError,
    )
    from src.simulation.presets import get_default_training_library
    from src.ui.bridge.training_bridge import TrainingPresetBridge

    bridge = TrainingPresetBridge(
        settings_manager=settings_manager,
        library=get_default_training_library(),
    )
    yield bridge
    bridge.deleteLater()


@pytest.fixture
def simulation_harness(qapp, qtbot):
    """Helper to start/stop :class:`SimulationManager` for smoke checks."""

    pytest.importorskip(
        "PySide6.QtCore",
        reason="PySide6 QtCore module is required for simulation harness",
        exc_type=ImportError,
    )
    try:
        from src.runtime.sim_loop import SimulationManager
    except Exception as exc:  # pragma: no cover - optional dependency environment
        pytest.skip(f"Simulation stack unavailable: {exc}")

    manager = SimulationManager()

    def _run(*, runtime_ms: int = 50) -> None:
        manager.start()

        def _thread_running() -> bool:
            return manager.physics_thread.isRunning()

        qtbot.waitUntil(_thread_running, timeout=2000)
        qtbot.wait(runtime_ms)
        manager.stop()
        qtbot.waitUntil(lambda: not manager.physics_thread.isRunning(), timeout=2000)

    yield _run

    try:
        manager.stop()
        manager.physics_thread.wait(500)
    finally:
        manager.deleteLater()


@pytest.fixture
def geometry_bridge(sample_geometry_params):
    """Create GeometryBridge instance"""
    pytest.importorskip(
        "PySide6.QtGui",
        reason="PySide6 QtGui module is required for geometry bridge conversion",
        exc_type=ImportError,
    )
    from src.ui.geometry_bridge import create_geometry_converter

    return create_geometry_converter(
        wheelbase=sample_geometry_params.wheelbase,
        lever_length=sample_geometry_params.lever_length,
        cylinder_diameter=sample_geometry_params.cylinder_inner_diameter,
    )


# Markers for organizing tests
def pytest_configure(config):
    """Configure custom markers"""
    config.addinivalue_line("markers", "unit: Unit tests for individual components")
    config.addinivalue_line(
        "markers", "integration: Integration tests for component interactions"
    )
    config.addinivalue_line("markers", "smoke: Lightweight application smoke scenarios")
    config.addinivalue_line("markers", "system: End-to-end system tests")
    config.addinivalue_line("markers", "slow: Tests that take significant time")
    config.addinivalue_line("markers", "gui: Tests requiring GUI/QML")


# Safe exit on test completion
def pytest_unconfigure(config):
    """Clean up after tests"""
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        return

    app = QApplication.instance()
    if app is not None:
        app.quit()
