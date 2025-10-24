import json
from pathlib import Path

import pytest

from src.common import settings_manager as settings_manager_module
from src.common.settings_manager import SettingsManager, get_settings_manager


@pytest.fixture
def legacy_settings(tmp_path: Path) -> Path:
    """Return a copy of the settings file with legacy metadata for migration tests."""

    source = Path("config/app_settings.json")
    data = json.loads(source.read_text(encoding="utf-8"))
    data.setdefault("metadata", {})["units_version"] = "legacy"
    data.setdefault("current", {}).setdefault("simulation", {})["physics_dt"] = 0.0025
    data.setdefault("defaults_snapshot", {}).setdefault("simulation", {})[
        "physics_dt"
    ] = 0.0025

    target_dir = tmp_path / "config"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / "app_settings.json"
    target_file.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return target_file


def test_settings_manager_si_units_migration(legacy_settings: Path) -> None:
    manager = SettingsManager(settings_file=legacy_settings)

    assert manager.get("metadata.units_version") == "si_v2"


def test_settings_manager_save_persists_units_migration(legacy_settings: Path) -> None:
    manager = SettingsManager(settings_file=legacy_settings)

    manager.save()

    payload = json.loads(legacy_settings.read_text(encoding="utf-8"))
    assert payload["metadata"]["units_version"] == "si_v2"


def test_get_settings_manager_si_units(
    legacy_settings: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PSS_SETTINGS_FILE", str(legacy_settings))
    monkeypatch.setattr(settings_manager_module, "_settings_manager", None)

    manager = get_settings_manager()

    assert manager.get("metadata.units_version") == "si_v2"


def test_settings_manager_round_trip_updates_file(legacy_settings: Path) -> None:
    manager = SettingsManager(settings_file=legacy_settings)

    assert manager.get("current.simulation.physics_dt") == 0.0025

    manager.set("current.simulation.physics_dt", 0.004)

    assert manager.get("current.simulation.physics_dt") == 0.004

    payload = json.loads(legacy_settings.read_text(encoding="utf-8"))
    assert payload["current"]["simulation"]["physics_dt"] == 0.004


def test_settings_manager_updates_defaults_snapshot(legacy_settings: Path) -> None:
    manager = SettingsManager(settings_file=legacy_settings)

    manager.set("defaults_snapshot.simulation.render_vsync_hz", 120)

    assert manager.get("defaults_snapshot.simulation.render_vsync_hz") == 120

    payload = json.loads(legacy_settings.read_text(encoding="utf-8"))
    assert payload["defaults_snapshot"]["simulation"]["render_vsync_hz"] == 120


def test_settings_manager_missing_path_returns_default(legacy_settings: Path) -> None:
    manager = SettingsManager(settings_file=legacy_settings)

    assert manager.get("current.simulation.unknown_key", default=42) == 42


def test_settings_manager_set_without_auto_save(legacy_settings: Path) -> None:
    manager = SettingsManager(settings_file=legacy_settings)

    manager.set("current.simulation.physics_dt", 0.006, auto_save=False)

    assert manager.get("current.simulation.physics_dt") == 0.006
    payload = json.loads(legacy_settings.read_text(encoding="utf-8"))
    assert payload["current"]["simulation"]["physics_dt"] == 0.0025

    manager.save()
    payload = json.loads(legacy_settings.read_text(encoding="utf-8"))
    assert payload["current"]["simulation"]["physics_dt"] == 0.006


def test_settings_manager_sets_extra_sections(legacy_settings: Path) -> None:
    manager = SettingsManager(settings_file=legacy_settings)

    manager.set("telemetry", {"interval_seconds": 2})

    assert manager.get("telemetry.interval_seconds") == 2
    payload = json.loads(legacy_settings.read_text(encoding="utf-8"))
    assert payload["telemetry"]["interval_seconds"] == 2


def test_get_settings_manager_caches_instance(
    legacy_settings: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PSS_SETTINGS_FILE", str(legacy_settings))
    monkeypatch.setattr(settings_manager_module, "_settings_manager", None)

    first = get_settings_manager()
    second = get_settings_manager()

    assert first is second
