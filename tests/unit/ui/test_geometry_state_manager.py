import json
from pathlib import Path

from src.common.settings_manager import SettingsManager
from src.ui.panels.geometry.defaults import DEFAULT_GEOMETRY
from src.ui.panels.geometry.state_manager import GeometryStateManager


def _write_settings_file(path: Path) -> None:
    geometry_payload = {**DEFAULT_GEOMETRY}
    geometry_payload.update(
        {
            "tail_mount_offset_m": 0.12,
            "joint_tail_scale": 1.0,
            "joint_arm_scale": 1.0,
            "joint_rod_scale": 1.0,
            "cylinder_cap_length_m": 0.05,
        }
    )

    payload = {
        "metadata": {
            "version": "test",
            "schema_version": "0.0.0",
            "last_modified": "2025-01-01T00:00:00Z",
            "units_version": "si_v2",
        },
        "current": {"geometry": geometry_payload},
        "defaults_snapshot": {"geometry": geometry_payload},
    }

    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def test_save_state_strips_legacy_geometry_keys(tmp_path: Path) -> None:
    settings_path = tmp_path / "app_settings.json"
    _write_settings_file(settings_path)

    manager = SettingsManager(settings_file=settings_path)
    state_manager = GeometryStateManager(manager)

    state_manager.save_state()
    manager.save_current_as_defaults(category="geometry")

    current_geometry = manager.get("current.geometry")
    defaults_geometry = manager.get("defaults_snapshot.geometry")

    legacy_keys = {
        "tail_mount_offset_m",
        "joint_tail_scale",
        "joint_arm_scale",
        "joint_rod_scale",
        "cylinder_cap_length_m",
    }

    assert legacy_keys.isdisjoint(current_geometry)
    assert legacy_keys.isdisjoint(defaults_geometry)
    assert "tail_rod_length_m" in current_geometry
    assert "tail_rod_length_m" in defaults_geometry

    saved = json.loads(settings_path.read_text(encoding="utf-8"))
    assert legacy_keys.isdisjoint(saved["current"]["geometry"])  # type: ignore[index]
    assert legacy_keys.isdisjoint(saved["defaults_snapshot"]["geometry"])  # type: ignore[index]
    assert "tail_rod_length_m" in saved["current"]["geometry"]  # type: ignore[index]
    assert "tail_rod_length_m" in saved["defaults_snapshot"]["geometry"]  # type: ignore[index]


def test_load_state_records_legacy_geometry(tmp_path: Path) -> None:
    settings_path = tmp_path / "app_settings.json"
    _write_settings_file(settings_path)

    payload = json.loads(settings_path.read_text(encoding="utf-8"))
    payload["current"]["geometry"]["tail_mount_offset_m"] = 0.25
    payload["defaults_snapshot"]["geometry"]["joint_tail_scale"] = 1.5
    settings_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    manager = SettingsManager(settings_file=settings_path)
    GeometryStateManager(manager)

    saved = json.loads(settings_path.read_text(encoding="utf-8"))

    assert "tail_mount_offset_m" not in saved["current"]["geometry"]  # type: ignore[index]
    assert "joint_tail_scale" not in saved["defaults_snapshot"]["geometry"]  # type: ignore[index]

    metadata_legacy = saved["metadata"].get("legacy", {})
    current_legacy = metadata_legacy.get("current", {}).get("geometry", {})
    defaults_legacy = metadata_legacy.get("defaults_snapshot", {}).get("geometry", {})

    assert current_legacy["tail_mount_offset_m"] == 0.25
    assert defaults_legacy["joint_tail_scale"] == 1.5
