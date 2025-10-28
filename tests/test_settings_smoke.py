import json
from copy import deepcopy
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


def test_settings_manager_set_graphics_updates_current_section(
    legacy_settings: Path,
) -> None:
    manager = SettingsManager(settings_file=legacy_settings)

    graphics_state = manager.get("graphics")
    assert isinstance(graphics_state, dict)

    graphics_state = deepcopy(graphics_state)
    graphics_state.setdefault("environment", {})["ibl_intensity"] = 2.5

    manager.set("graphics", graphics_state, auto_save=False)

    assert manager.get("current.graphics.environment.ibl_intensity") == 2.5

    manager.save()
    payload = json.loads(legacy_settings.read_text(encoding="utf-8"))
    assert "graphics" not in payload
    assert payload["current"]["graphics"]["environment"]["ibl_intensity"] == 2.5


def test_settings_manager_migrates_legacy_graphics_categories(
    legacy_settings: Path,
) -> None:
    payload = json.loads(legacy_settings.read_text(encoding="utf-8"))
    graphics = payload["current"]["graphics"]

    stray_categories = {
        "camera": deepcopy(graphics["camera"]),
        "effects": deepcopy(graphics["effects"]),
        "environment": deepcopy(graphics["environment"]),
        "materials": deepcopy(graphics["materials"]),
    }

    stray_categories["camera"]["fov"] = stray_categories["camera"]["fov"] + 5.0
    stray_categories["effects"]["bloom_intensity"] = (
        stray_categories["effects"]["bloom_intensity"] + 0.1
    )
    stray_categories["environment"]["ibl_intensity"] = (
        stray_categories["environment"]["ibl_intensity"] + 0.2
    )
    stray_categories["materials"]["frame"]["base_color"] = "#abcdef"

    for key, value in stray_categories.items():
        payload[key] = value

    legacy_settings.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    manager = SettingsManager(settings_file=legacy_settings)

    assert (
        manager.get("current.graphics.camera.fov") == stray_categories["camera"]["fov"]
    )
    assert (
        manager.get("current.graphics.effects.bloom_intensity")
        == stray_categories["effects"]["bloom_intensity"]
    )
    assert (
        manager.get("current.graphics.environment.ibl_intensity")
        == stray_categories["environment"]["ibl_intensity"]
    )
    assert (
        manager.get("current.graphics.materials.frame.base_color")
        == stray_categories["materials"]["frame"]["base_color"]
    )

    manager.save()
    persisted = json.loads(legacy_settings.read_text(encoding="utf-8"))
    extra_keys = set(persisted) - {"metadata", "current", "defaults_snapshot"}
    assert not extra_keys & stray_categories.keys()

    for key, expected in stray_categories.items():
        assert persisted["current"]["graphics"][key] == expected


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


def test_settings_manager_migrates_root_graphics_section(tmp_path: Path) -> None:
    payload = {
        "metadata": {"units_version": "si_v2"},
        "current": {"graphics": {"environment": {"ibl_intensity": 1.3}}},
        "defaults_snapshot": {},
        "graphics": {"environment": {"ibl_intensity": 2.0, "fog_density": 0.1}},
    }
    settings_path = tmp_path / "app_settings.json"
    settings_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    manager = SettingsManager(settings_file=settings_path)

    assert manager.get("current.graphics.environment.ibl_intensity") == 2.0
    assert manager.get("current.graphics.environment.fog_density") == 0.1

    manager.save()
    stored = json.loads(settings_path.read_text(encoding="utf-8"))
    assert "graphics" not in stored
    assert stored["current"]["graphics"]["environment"]["ibl_intensity"] == 2.0
    assert stored["current"]["graphics"]["environment"]["fog_density"] == 0.1


def test_legacy_geometry_values_are_scaled(tmp_path: Path) -> None:
    payload = {
        "metadata": {"units_version": "legacy"},
        "current": {
            "geometry": {
                "wheelbase": 3200.0,
                "track": 1600.0,
                "frame_height_m": 650.0,
                "frame_length_mm": 3400.0,
                "lever_length_mm": 800.0,
                "rod_diameter_mm": 35.0,
            }
        },
        "defaults_snapshot": {
            "geometry": {
                "wheelbase": 3000.0,
                "frame_height_m": 600.0,
                "frame_length_mm": 3200.0,
            }
        },
    }
    settings_dir = tmp_path / "config"
    settings_dir.mkdir(parents=True)
    settings_path = settings_dir / "app_settings.json"
    settings_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    manager = SettingsManager(settings_file=settings_path)

    geometry = manager.get("current.geometry")
    defaults = manager.get("defaults_snapshot.geometry")

    assert pytest.approx(3.2, rel=1e-9) == geometry["wheelbase"]
    assert pytest.approx(1.6, rel=1e-9) == geometry["track"]
    assert pytest.approx(0.65, rel=1e-9) == geometry["frame_height_m"]
    assert pytest.approx(3.4, rel=1e-9) == geometry["frame_length_m"]
    assert pytest.approx(0.8, rel=1e-9) == geometry["lever_length"]
    assert pytest.approx(0.035, rel=1e-9) == geometry["rod_diameter_m"]

    assert pytest.approx(3.0, rel=1e-9) == defaults["wheelbase"]
    assert pytest.approx(0.6, rel=1e-9) == defaults["frame_height_m"]
    assert pytest.approx(3.2, rel=1e-9) == defaults["frame_length_m"]


def test_graphics_key_aliases_are_normalised(tmp_path: Path) -> None:
    payload = {
        "metadata": {"units_version": "si_v2"},
        "current": {
            "graphics": {
                "effects": {
                    "tonemapActive": True,
                    "tonemapModeName": "reinhard",
                    "colorBrightness": 0.5,
                    "vignetteEnabled": True,
                },
                "environment": {
                    "iblBackgroundEnabled": True,
                    "probeBrightness": 1.2,
                },
                "camera": {"manual_mode": True},
            }
        },
        "defaults_snapshot": {
            "graphics": {"effects": {}, "environment": {}, "camera": {}}
        },
    }
    settings_dir = tmp_path / "config"
    settings_dir.mkdir(parents=True)
    settings_path = settings_dir / "app_settings.json"
    settings_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    manager = SettingsManager(settings_file=settings_path)

    effects = manager.get("current.graphics.effects")
    environment = manager.get("current.graphics.environment")
    camera = manager.get("current.graphics.camera")

    assert effects["tonemap_enabled"] is True
    assert effects["tonemap_mode"] == "reinhard"
    assert effects["adjustment_brightness"] == 0.5
    assert effects["vignette"] is True
    assert "tonemapActive" not in effects

    assert environment["skybox_enabled"] is True
    assert pytest.approx(1.2, rel=1e-9) == environment["skybox_brightness"]
    assert "probe_brightness" not in environment

    assert camera["manual_camera"] is True
    assert "manual_mode" not in camera
