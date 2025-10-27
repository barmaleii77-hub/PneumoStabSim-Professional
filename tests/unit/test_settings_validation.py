import json
import sys
import types
from pathlib import Path

import pytest

from src.app_runner import ApplicationRunner
from src.common import settings_manager as settings_manager_module
from src.core.settings_validation import (
    SettingsValidationError,
    determine_settings_source,
    validate_settings_file,
)


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROJECT_SETTINGS = PROJECT_ROOT / "config" / "app_settings.json"


# Base settings for tests
def _base_settings() -> dict:
    return json.loads(PROJECT_SETTINGS.read_text(encoding="utf-8"))


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

    DummyMessageBox.calls = []

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

    with pytest.raises(SettingsValidationError) as exc:
        runner._validate_settings_file()

    error_text = str(exc.value)
    assert "current: 'simulation' is a required property" in error_text
    assert "'simulation' is a required property" in _last_error(stub_qmessagebox)


def test_validate_settings_missing_physics_dt(
    runner: ApplicationRunner, write_config, stub_qmessagebox
):
    settings = _base_settings()
    settings["current"]["simulation"].pop("physics_dt")
    write_config(settings)

    with pytest.raises(SettingsValidationError) as exc:
        runner._validate_settings_file()

    assert "physics_dt" in str(exc.value)
    assert "physics_dt" in _last_error(stub_qmessagebox)


def test_validate_settings_missing_receiver_limit(
    runner: ApplicationRunner, write_config, stub_qmessagebox
):
    settings = _base_settings()
    settings["current"]["pneumatic"]["receiver_volume_limits"].pop("min_m3")
    write_config(settings)

    with pytest.raises(SettingsValidationError) as exc:
        runner._validate_settings_file()

    assert "receiver_volume_limits" in str(exc.value)
    assert "receiver_volume_limits" in _last_error(stub_qmessagebox)


def test_validate_settings_missing_geometry_section(
    runner: ApplicationRunner, write_config, stub_qmessagebox
):
    settings = _base_settings()
    settings["current"].pop("geometry")
    write_config(settings)

    with pytest.raises(SettingsValidationError) as exc:
        runner._validate_settings_file()

    error_text = str(exc.value)
    assert "current: 'geometry' is a required property" in error_text
    assert "'geometry' is a required property" in _last_error(stub_qmessagebox)


def test_validate_settings_missing_volume_mode(
    runner: ApplicationRunner, write_config, stub_qmessagebox
):
    settings = _base_settings()
    settings["current"]["pneumatic"].pop("volume_mode")
    write_config(settings)

    with pytest.raises(SettingsValidationError) as exc:
        runner._validate_settings_file()

    assert "volume_mode" in str(exc.value)
    assert "volume_mode" in _last_error(stub_qmessagebox)


def test_validate_settings_success(
    runner: ApplicationRunner, write_config, stub_qmessagebox
):
    write_config(_base_settings())

    runner._validate_settings_file()

    assert stub_qmessagebox.calls == []


def test_validate_settings_invalid_bool(
    runner: ApplicationRunner, write_config, stub_qmessagebox
):
    settings = _base_settings()
    settings["current"]["pneumatic"]["master_isolation_open"] = "да"
    write_config(settings)

    with pytest.raises(SettingsValidationError) as exc:
        runner._validate_settings_file()

    message = str(exc.value)
    assert "is not of type 'boolean'" in message
    assert "master_isolation_open" in _last_error(stub_qmessagebox)


def test_validate_settings_file_helper(tmp_path: Path, monkeypatch):
    path = tmp_path / "settings.json"
    path.write_text(
        json.dumps(_base_settings(), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    monkeypatch.delenv("PSS_SETTINGS_FILE", raising=False)

    validate_settings_file(path)


def test_determine_settings_source(monkeypatch, tmp_path: Path):
    custom_path = tmp_path / "custom.json"
    monkeypatch.setenv("PSS_SETTINGS_FILE", str(custom_path))
    assert determine_settings_source(custom_path) == "ENV"

    monkeypatch.delenv("PSS_SETTINGS_FILE", raising=False)
    project_cfg = tmp_path / "project" / "app_settings.json"
    project_cfg.parent.mkdir(parents=True, exist_ok=True)
    project_cfg.write_text("{}", encoding="utf-8")
    assert (
        determine_settings_source(project_cfg, project_default=project_cfg) == "PROJECT"
    )

    fallback_path = tmp_path / "other.json"
    fallback_path.write_text("{}", encoding="utf-8")
    assert (
        determine_settings_source(fallback_path, project_default=project_cfg) == "CWD"
    )
