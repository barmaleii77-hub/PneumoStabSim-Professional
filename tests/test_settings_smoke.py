import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path

import pytest

from src.common import settings_manager as settings_manager_module
from src.common.settings_manager import SettingsManager, get_settings_manager
from src.core.settings_service import SettingsService
from src.ui.environment_schema import ENVIRONMENT_SLIDER_RANGE_DEFAULTS


@pytest.fixture
def legacy_settings(tmp_path: Path) -> Path:
    """Return a copy of the settings file with legacy metadata for migration tests."""

    source = Path("config/app_settings.json")
    data = json.loads(source.read_text(encoding="utf-8"))

    # Preserve ENTIRE defaults_snapshot from source to ensure all categories exist
    # Only modify units_version and simulation values for testing
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


def test_settings_manager_expands_environment_settings_path(
    legacy_settings: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("PSS_CONFIG_ROOT", str(legacy_settings.parent))
    monkeypatch.setenv("PSS_SETTINGS_FILE", "${PSS_CONFIG_ROOT}/app_settings.json")
    monkeypatch.setattr(settings_manager_module, "_settings_manager", None)

    manager = SettingsManager()

    assert manager.settings_file == legacy_settings
    assert manager.get("metadata.units_version") == "si_v2"


def test_settings_manager_round_trip_updates_file(legacy_settings: Path) -> None:
    manager = SettingsManager(settings_file=legacy_settings)

    assert manager.get("current.simulation.physics_dt") == 0.0025

    manager.set("current.simulation.physics_dt", 0.004)

    assert manager.get("current.simulation.physics_dt") == 0.004

    payload = json.loads(legacy_settings.read_text(encoding="utf-8"))
    assert payload["current"]["simulation"]["physics_dt"] == 0.004


def test_settings_manager_updates_last_modified_on_save(
    legacy_settings: Path,
) -> None:
    manager = SettingsManager(settings_file=legacy_settings)

    before = manager.get("metadata.last_modified")
    manager.set("current.simulation.physics_dt", 0.006)

    after = manager.get("metadata.last_modified")
    assert isinstance(after, str)
    assert after != before

    payload = json.loads(legacy_settings.read_text(encoding="utf-8"))
    persisted = payload["metadata"].get("last_modified")
    assert persisted == after

    parsed = datetime.fromisoformat(persisted.replace("Z", "+00:00"))
    assert parsed.tzinfo == timezone.utc


def test_settings_manager_updates_defaults_snapshot(legacy_settings: Path) -> None:
    manager = SettingsManager(settings_file=legacy_settings)

    manager.set("defaults_snapshot.simulation.render_vsync_hz", 120)

    assert manager.get("defaults_snapshot.simulation.render_vsync_hz") == 120

    payload = json.loads(legacy_settings.read_text(encoding="utf-8"))
    assert payload["defaults_snapshot"]["simulation"]["render_vsync_hz"] == 120


def test_settings_manager_missing_path_returns_default(legacy_settings: Path) -> None:
    manager = SettingsManager(settings_file=legacy_settings)

    assert manager.get("current.simulation.unknown_key", default=42) == 42


def test_environment_slider_ranges_are_defined() -> None:
    manager = SettingsManager()

    # Диапазоны слайдеров хранятся в metadata.environment_slider_ranges
    ranges = manager.get("metadata.environment_slider_ranges")
    assert isinstance(ranges, dict)

    for key, default_range in ENVIRONMENT_SLIDER_RANGE_DEFAULTS.items():
        entry = ranges.get(key)
        assert isinstance(entry, dict), f"Missing range for {key}"
        assert entry["min"] == pytest.approx(default_range.minimum)
        assert entry["max"] == pytest.approx(default_range.maximum)
        assert entry["step"] == pytest.approx(default_range.step)


def test_metadata_environment_slider_ranges_match_defaults() -> None:
    manager = SettingsManager()

    ranges = manager.get("metadata.environment_slider_ranges")
    assert isinstance(ranges, dict)

    for key, default_range in ENVIRONMENT_SLIDER_RANGE_DEFAULTS.items():
        entry = ranges.get(key)
        assert isinstance(entry, dict), f"Missing metadata range for {key}"
        assert entry["min"] == pytest.approx(default_range.minimum)
        assert entry["max"] == pytest.approx(default_range.maximum)
        assert entry["step"] == pytest.approx(default_range.step)


def test_settings_service_strips_null_environment_slider_metadata(
    tmp_path: Path,
) -> None:
    payload = json.loads(Path("config/app_settings.json").read_text(encoding="utf-8"))
    slider_ranges = payload.setdefault("metadata", {}).setdefault(
        "environment_slider_ranges", {}
    )

    slider_ranges.setdefault("ibl_intensity", {}).update(
        {"decimals": None, "units": None}
    )
    slider_ranges["unused"] = {"min": None, "max": None, "step": None}

    settings_path = tmp_path / "app_settings.json"
    service = SettingsService(settings_path=settings_path, validate_schema=False)
    service.save(payload)

    stored = json.loads(settings_path.read_text(encoding="utf-8"))
    metadata_ranges = stored["metadata"]["environment_slider_ranges"]

    assert "decimals" not in metadata_ranges["ibl_intensity"]
    assert "units" not in metadata_ranges["ibl_intensity"]
    assert "unused" not in metadata_ranges


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


def test_settings_manager_overwrites_existing_extra_section(
    legacy_settings: Path,
) -> None:
    manager = SettingsManager(settings_file=legacy_settings)

    manager.set("telemetry", {"interval_seconds": 2})
    manager.set("telemetry", {"interval_seconds": 5, "enabled": True})

    assert manager.get("telemetry.interval_seconds") == 5
    assert manager.get("telemetry.enabled") is True

    payload = json.loads(legacy_settings.read_text(encoding="utf-8"))
    assert payload["telemetry"] == {"interval_seconds": 5, "enabled": True}
    assert "telemetry" not in payload["telemetry"]


def test_settings_manager_preserves_current_structure(legacy_settings: Path) -> None:
    manager = SettingsManager(settings_file=legacy_settings)

    new_graphics = {
        "scene": {
            "scale_factor": 1.0,
            "exposure": 2.0,
            "default_clear_color": "#1b1f27",
            "model_base_color": "#9da3aa",
            "model_roughness": 0.42,
            "model_metalness": 0.82,
            "suspension": {"rod_warning_threshold_m": 0.001},
        }
    }
    manager.set("graphics", new_graphics)

    assert manager.get("current.graphics.scene.exposure") == 2.0

    payload = json.loads(legacy_settings.read_text(encoding="utf-8"))
    assert payload["current"]["graphics"]["scene"]["exposure"] == 2.0
    extra_keys = set(payload) - {"metadata", "current", "defaults_snapshot"}
    assert "graphics" not in extra_keys


def test_settings_manager_replaces_root_sections(legacy_settings: Path) -> None:
    manager = SettingsManager(settings_file=legacy_settings)

    new_metadata = {"units_version": "legacy", "profile": "debug"}
    manager.set("metadata", new_metadata)

    assert manager.get("metadata.profile") == "debug"
    assert manager.get("metadata.units_version") == "si_v2"

    payload = json.loads(legacy_settings.read_text(encoding="utf-8"))
    assert payload["metadata"]["profile"] == "debug"
    assert payload["metadata"]["units_version"] == "si_v2"

    new_current = {"simulation": {"physics_dt": 0.01}}
    manager.set("current", new_current)

    assert manager.get("current.simulation.physics_dt") == 0.01

    payload = json.loads(legacy_settings.read_text(encoding="utf-8"))
    assert payload["current"] == new_current
    assert "current" not in payload["current"]

    new_defaults = {"simulation": {"physics_dt": 0.02}}
    manager.set("defaults_snapshot", new_defaults)

    assert manager.get("defaults_snapshot.simulation.physics_dt") == 0.02

    payload = json.loads(legacy_settings.read_text(encoding="utf-8"))
    assert payload["defaults_snapshot"] == new_defaults
    assert "defaults_snapshot" not in payload["defaults_snapshot"]


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

    # SettingsManager автоматически удаляет legacy material ключи (specular, transmission, ior)
    # Обновим ожидания, удалив эти ключи из expected
    for key, expected in stray_categories.items():
        actual = persisted["current"]["graphics"][key]
        if key == "materials":
            # Удаляем legacy ключи из expected для корректного сравнения
            for mat_name, mat_payload in expected.items():
                if isinstance(mat_payload, dict):
                    for legacy_key in (
                        "specular",
                        "specular_tint",
                        "transmission",
                        "ior",
                    ):
                        mat_payload.pop(legacy_key, None)
        assert actual == expected


def test_reset_to_defaults_category(legacy_settings: Path) -> None:
    manager = SettingsManager(settings_file=legacy_settings)

    # Сначала сохраним текущую геометрию как дефолты, чтобы defaults_snapshot.geometry существовал
    current_geometry = manager.get("current.geometry")
    if current_geometry:
        manager.set("defaults_snapshot.geometry", current_geometry, auto_save=True)

    # Изменим текущее значение
    manager.set("current.geometry.wheelbase", 4.2)
    assert manager.get("current.geometry.wheelbase") == 4.2

    # Сброс к дефолтам
    manager.reset_to_defaults(category="geometry")

    # Проверка восстановления
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


def test_settings_manager_hydrates_point_light_defaults(tmp_path: Path) -> None:
    payload = {
        "metadata": {"units_version": "si_v2"},
        "current": {"graphics": {"lighting": {"point": {"range": 0.0}}}},
        "defaults_snapshot": {
            "graphics": {
                "lighting": {
                    "point": {
                        "constant_fade": None,
                        "linear_fade": None,
                        "quadratic_fade": 0,
                    }
                }
            }
        },
    }

    settings_path = tmp_path / "app_settings.json"
    settings_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    manager = SettingsManager(settings_file=settings_path)

    current_point = manager.get("current.graphics.lighting.point")
    defaults_point = manager.get("defaults_snapshot.graphics.lighting.point")

    expected_linear = pytest.approx(2.0 / 3.6)

    assert current_point["range"] == pytest.approx(3.6)
    assert current_point["constant_fade"] == pytest.approx(1.0)
    assert current_point["linear_fade"] == expected_linear
    assert defaults_point["constant_fade"] == pytest.approx(1.0)
    assert defaults_point["linear_fade"] == expected_linear
    assert defaults_point["quadratic_fade"] == pytest.approx(1.0)


def test_legacy_geometry_values_are_scaled(tmp_path: Path) -> None:
    payload = {
        "metadata": {"units_version": "legacy"},
        "current": {
            "geometry": {
                # ВСЕ legacy значения с явными _mm суффиксами
                "wheelbase_mm": 3200.0,
                "track_width_mm": 1600.0,
                "frame_height_mm": 650.0,  # legacy mm
                "frame_length_mm": 3400.0,
                "lever_length_mm": 800.0,
                "rod_diameter_mm": 35.0,
            }
        },
        "defaults_snapshot": {
            "geometry": {
                "wheelbase_mm": 3000.0,
                "frame_height_mm": 600.0,  # legacy mm
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

    # After migration: mm suffixes normalized to meters, values scaled /1000
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
