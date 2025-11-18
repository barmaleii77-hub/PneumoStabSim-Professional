import json
from pathlib import Path

import pytest

from src.common.settings_manager import SettingsManager
from src.core.parameter_manager import ParameterManager, ParameterValidationError
from src.core.settings_models import dump_settings
from src.core.settings_service import SettingsService


def _copy_settings(tmp_path: Path) -> Path:
    source = Path("config/app_settings.json")
    target = tmp_path / "app_settings.json"
    target.write_text(source.read_text(encoding="utf-8"), encoding="utf-8")
    return target


def test_parameter_manager_accepts_default_config(tmp_path: Path) -> None:
    settings_path = _copy_settings(tmp_path)
    service = SettingsService(settings_path=settings_path)

    snapshot = ParameterManager(settings_service=service).validate()

    assert snapshot.geometry["cyl_diam_m"] > snapshot.geometry["rod_diameter_m"]
    assert (
        snapshot.pneumatic["relief_safety_pressure"]
        > snapshot.pneumatic["relief_stiff_pressure"]
    )


def test_detects_invalid_cylinder_geometry(tmp_path: Path) -> None:
    settings_path = _copy_settings(tmp_path)
    payload = json.loads(settings_path.read_text(encoding="utf-8"))
    payload["current"]["geometry"]["rod_diameter_m"] = payload["current"]["geometry"][
        "cyl_diam_m"
    ]
    settings_path.write_text(json.dumps(payload), encoding="utf-8")

    service = SettingsService(settings_path=settings_path)
    manager = ParameterManager(settings_service=service)

    with pytest.raises(ParameterValidationError) as excinfo:
        manager.validate()

    assert any("rod diameter" in error.lower() for error in excinfo.value.errors)


def test_detects_pressure_hierarchy_regression(tmp_path: Path) -> None:
    settings_path = _copy_settings(tmp_path)
    payload = json.loads(settings_path.read_text(encoding="utf-8"))
    pneumo = payload["current"]["pneumatic"]
    pneumo["relief_safety_pressure"] = pneumo["relief_stiff_pressure"] * 1.05
    settings_path.write_text(json.dumps(payload), encoding="utf-8")

    manager = ParameterManager(
        settings_service=SettingsService(settings_path=settings_path)
    )

    with pytest.raises(ParameterValidationError) as excinfo:
        manager.validate()

    assert any("20%" in error for error in excinfo.value.errors)


def test_receiver_volume_range_uses_settings_manager(tmp_path: Path) -> None:
    settings_path = _copy_settings(tmp_path)
    payload = json.loads(settings_path.read_text(encoding="utf-8"))
    payload["current"]["pneumatic"]["receiver_volume"] = 2.5
    payload["current"]["pneumatic"]["receiver_volume_limits"]["min_m3"] = 0.5
    payload["current"]["pneumatic"]["receiver_volume_limits"]["max_m3"] = 1.0
    settings_path.write_text(json.dumps(payload), encoding="utf-8")

    manager = SettingsManager(settings_file=settings_path)
    param_manager = ParameterManager(settings_manager=manager)

    with pytest.raises(ParameterValidationError) as excinfo:
        param_manager.validate()

    assert any("receiver volume" in error.lower() for error in excinfo.value.errors)


def test_validate_payload_works_with_dumped_settings(tmp_path: Path) -> None:
    settings_path = _copy_settings(tmp_path)
    service = SettingsService(settings_path=settings_path)

    payload = dump_settings(service.load())
    snapshot = ParameterManager.validate_payload(payload)

    assert snapshot.geometry["stroke_m"] > 0


def test_validate_payload_fails_without_sections() -> None:
    with pytest.raises(ParameterValidationError) as excinfo:
        ParameterManager.validate_payload({"current": {}})

    assert "geometry" in ",".join(excinfo.value.errors).lower()


def test_settings_service_exposes_dependency_validation(tmp_path: Path) -> None:
    settings_path = _copy_settings(tmp_path)
    service = SettingsService(settings_path=settings_path)

    snapshot = service.validate_dependencies()

    assert snapshot.geometry["cyl_diam_m"] > snapshot.geometry["rod_diameter_m"]


def test_settings_manager_dependency_validation(tmp_path: Path) -> None:
    settings_path = _copy_settings(tmp_path)
    manager = SettingsManager(settings_file=settings_path)
    manager.set("current.pneumatic.receiver_volume", 2.0)
    manager.set("current.pneumatic.receiver_volume_limits.max_m3", 1.0)

    with pytest.raises(ParameterValidationError):
        manager.validate_dependencies()
