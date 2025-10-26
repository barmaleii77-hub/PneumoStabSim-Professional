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


def test_settings_manager_preserves_current_structure(legacy_settings: Path) -> None:
    manager = SettingsManager(settings_file=legacy_settings)

    new_graphics = {"scene": {"exposure": 2.0}}
    manager.set("graphics", new_graphics)

    assert manager.get("current.graphics.scene.exposure") == 2.0

    payload = json.loads(legacy_settings.read_text(encoding="utf-8"))
    assert payload["current"]["graphics"]["scene"]["exposure"] == 2.0
    extra_keys = set(payload) - {"metadata", "current", "defaults_snapshot"}
    assert "graphics" not in extra_keys


def test_get_settings_manager_caches_instance(
    legacy_settings: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PSS_SETTINGS_FILE", str(legacy_settings))
    monkeypatch.setattr(settings_manager_module, "_settings_manager", None)

    first = get_settings_manager()
    second = get_settings_manager()

    assert first is second


def test_get_category_returns_copy(legacy_settings: Path) -> None:
    manager = SettingsManager(settings_file=legacy_settings)

    geometry = manager.get_category("geometry")
    assert geometry is not None

    geometry["wheelbase"] = 99.0

    assert manager.get("current.geometry.wheelbase") != 99.0


def test_set_category_updates_current_section(legacy_settings: Path) -> None:
    manager = SettingsManager(settings_file=legacy_settings)

    manager.set_category("geometry", {"wheelbase": 3.6}, auto_save=False)

    assert manager.get("current.geometry.wheelbase") == 3.6

    payload = json.loads(legacy_settings.read_text(encoding="utf-8"))
    assert payload["current"]["geometry"]["wheelbase"] != 3.6

    manager.save()
    payload = json.loads(legacy_settings.read_text(encoding="utf-8"))
    assert payload["current"]["geometry"]["wheelbase"] == 3.6


def test_reset_to_defaults_category(legacy_settings: Path) -> None:
    manager = SettingsManager(settings_file=legacy_settings)

    manager.set("current.geometry.wheelbase", 4.2)
    assert manager.get("current.geometry.wheelbase") == 4.2

    manager.reset_to_defaults(category="geometry")

    default_value = manager.get("defaults_snapshot.geometry.wheelbase")
    assert manager.get("current.geometry.wheelbase") == default_value

    payload = json.loads(legacy_settings.read_text(encoding="utf-8"))
    assert payload["current"]["geometry"]["wheelbase"] == default_value


def test_save_current_as_defaults_category(legacy_settings: Path) -> None:
    manager = SettingsManager(settings_file=legacy_settings)

    manager.set("current.geometry.wheelbase", 5.1)

    manager.save_current_as_defaults(category="geometry")

    assert manager.get("defaults_snapshot.geometry.wheelbase") == 5.1

    payload = json.loads(legacy_settings.read_text(encoding="utf-8"))
    assert payload["defaults_snapshot"]["geometry"]["wheelbase"] == 5.1


def test_reset_to_defaults_unknown_category_raises(legacy_settings: Path) -> None:
    manager = SettingsManager(settings_file=legacy_settings)

    with pytest.raises(KeyError):
        manager.reset_to_defaults(category="missing")
