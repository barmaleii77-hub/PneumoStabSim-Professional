import json
import sys
import types
import copy
from pathlib import Path

import pytest

from src.app_runner import ApplicationRunner
from src.common import settings_manager as settings_manager_module


REQUIRED_MATERIALS = {
    "frame",
    "lever",
    "tail",
    "cylinder",
    "piston_body",
    "piston_rod",
    "joint_tail",
    "joint_arm",
    "joint_rod",
}


# Base settings for tests
def _base_settings() -> dict:
    current = {
        "simulation": {
            "physics_dt": 0.001,
            "render_vsync_hz": 60,
            "max_steps_per_frame": 8,
            "max_frame_time": 0.25,
        },
        "pneumatic": {
            "receiver_volume_limits": {"min_m3": 0.01, "max_m3": 0.05},
            "receiver_volume": 0.02,
            "volume_mode": "MANUAL",
            "master_isolation_open": True,
            "thermo_mode": "ADIABATIC",
        },
        "geometry": {"wheelbase": 2.0},
        "graphics": {"materials": {name: {"id": name} for name in REQUIRED_MATERIALS}},
    }
    return {
        "current": current,
        "defaults_snapshot": copy.deepcopy(current),
        "metadata": {"units_version": "si_v2"},
    }


@pytest.fixture(autouse=True)
def stub_qmessagebox(monkeypatch):
    class DummyMessageBox:
        calls = []

        @classmethod
        def critical(cls, parent, title, text):
            cls.calls.append((parent, title, text))

    qtwidgets = types.ModuleType("PySide6.QtWidgets")
    qtwidgets.QMessageBox = DummyMessageBox
    pyside = types.ModuleType("PySide6")
    setattr(pyside, "QtWidgets", qtwidgets)

    monkeypatch.setitem(sys.modules, "PySide6", pyside)
    monkeypatch.setitem(sys.modules, "PySide6.QtWidgets", qtwidgets)

    return DummyMessageBox


@pytest.fixture
def runner() -> ApplicationRunner:
    return ApplicationRunner(
        object,
        lambda *args, **kwargs: None,
        object,
        object,
    )


@pytest.fixture
def write_config(tmp_path: Path, monkeypatch):
    def _write(data: dict) -> Path:
        path = tmp_path / "settings.json"
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        monkeypatch.setenv("PSS_SETTINGS_FILE", str(path))
        monkeypatch.setattr(settings_manager_module, "_settings_manager", None)
        return path

    return _write


# Helper to get last QMessageBox error
def _last_error(stub_qmessagebox) -> str:
    assert stub_qmessagebox.calls, "QMessageBox.critical was not called"
    return stub_qmessagebox.calls[-1][2]


# Test cases
def test_validate_settings_missing_simulation_section(
    runner: ApplicationRunner, write_config, stub_qmessagebox
):
    settings = _base_settings()
    settings["current"].pop("simulation")
    write_config(settings)

    with pytest.raises(ValueError) as exc:
        runner._validate_settings_file()

    assert "обязательная секция current.simulation" in str(exc.value)
    assert "current.simulation" in _last_error(stub_qmessagebox)


def test_validate_settings_missing_physics_dt(
    runner: ApplicationRunner, write_config, stub_qmessagebox
):
    settings = _base_settings()
    settings["current"]["simulation"].pop("physics_dt")
    write_config(settings)

    with pytest.raises(ValueError) as exc:
        runner._validate_settings_file()

    assert "physics_dt" in str(exc.value)
    assert "physics_dt" in _last_error(stub_qmessagebox)


def test_validate_settings_missing_receiver_limit(
    runner: ApplicationRunner, write_config, stub_qmessagebox
):
    settings = _base_settings()
    settings["current"]["pneumatic"]["receiver_volume_limits"].pop("min_m3")
    write_config(settings)

    with pytest.raises(ValueError) as exc:
        runner._validate_settings_file()

    assert "receiver_volume_limits" in str(exc.value)
    assert "receiver_volume_limits" in _last_error(stub_qmessagebox)


def test_validate_settings_missing_geometry_section(
    runner: ApplicationRunner, write_config, stub_qmessagebox
):
    settings = _base_settings()
    settings["current"].pop("geometry")
    write_config(settings)

    with pytest.raises(ValueError) as exc:
        runner._validate_settings_file()

    assert "current.geometry" in str(exc.value)
    assert "geometry" in _last_error(stub_qmessagebox)


def test_validate_settings_missing_volume_mode(
    runner: ApplicationRunner, write_config, stub_qmessagebox
):
    settings = _base_settings()
    settings["current"]["pneumatic"].pop("volume_mode")
    write_config(settings)

    with pytest.raises(ValueError) as exc:
        runner._validate_settings_file()

    assert "volume_mode" in str(exc.value)
    assert "volume_mode" in _last_error(stub_qmessagebox)
