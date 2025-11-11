"""Regression tests covering migration of legacy settings payloads."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.common.settings_manager import PROJECT_ROOT, SettingsManager


def _write_legacy_payload(tmp_path: Path) -> Path:
    legacy_payload = {
        "metadata": {"units_version": "legacy"},
        "current": {
            "graphics": {
                "environment": {
                    "probeBrightness": 1.6,
                    "iblSource": str(
                        (PROJECT_ROOT / "assets" / "hdr" / "legacy_added.hdr").resolve()
                    ),
                },
                "effects": {
                    "tonemapActive": True,
                    "bloomHDRMaximum": 3.5,
                    "motionBlurEnabled": False,
                },
                "camera": {"manualMode": True},
            },
            "simulation": {"physics_dt": 0.0025},
            "geometry": {
                "frame_length_mm": 2500,
                "lever_length_visual_mm": 640.0,
            },
        },
        "defaults_snapshot": {
            "graphics": {
                "environment": {
                    "probe_brightness": 0.75,
                    "iblSource": "C\\HDR\\legacy_default.hdr",
                },
                "effects": {
                    "tonemapenabled": False,
                    "colorBrightness": 1.15,
                },
                "camera": {"manualMode": False},
            },
            "simulation": {"physics_dt": 0.0025},
            "geometry": {
                "frame_length_mm": 1800,
                "lever_length_visual": 0.55,
            },
        },
        "legacy": {"unused": True},
    }

    settings_path = tmp_path / "app_settings.json"
    settings_path.write_text(
        json.dumps(legacy_payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return settings_path


def test_settings_manager_migrates_environment_section(tmp_path: Path) -> None:
    settings_path = _write_legacy_payload(tmp_path)

    manager = SettingsManager(settings_file=settings_path)

    assert manager.get("metadata.units_version") == "si_v2"

    environment = manager.get("current.graphics.environment")
    assert environment["skybox_brightness"] == pytest.approx(1.6)
    assert environment["ibl_source"] == "assets/hdr/legacy_added.hdr"

    defaults_environment = manager.get("defaults_snapshot.graphics.environment")
    assert defaults_environment["skybox_brightness"] == pytest.approx(0.75)
    assert defaults_environment["ibl_source"] == "c:/hdr/legacy_default.hdr"

    geometry = manager.get("current.geometry")
    assert geometry["frame_length_m"] == pytest.approx(2.5)
    assert geometry["lever_length_m"] == pytest.approx(0.64)
    assert geometry["lever_length"] == pytest.approx(0.64)

    defaults_geometry = manager.get("defaults_snapshot.geometry")
    assert defaults_geometry["frame_length_m"] == pytest.approx(1.8)
    assert defaults_geometry["lever_length_m"] == pytest.approx(0.55)
    assert defaults_geometry["lever_length"] == pytest.approx(0.55)

    effects = manager.get("current.graphics.effects")
    assert effects["tonemap_enabled"] is True
    assert effects["bloom_hdr_max"] == pytest.approx(3.5)
    assert effects["motion_blur"] is False

    defaults_effects = manager.get("defaults_snapshot.graphics.effects")
    assert defaults_effects["tonemap_enabled"] is False
    assert defaults_effects["adjustment_brightness"] == pytest.approx(1.15)

    camera = manager.get("current.graphics.camera")
    assert camera["manual_camera"] is True

    defaults_camera = manager.get("defaults_snapshot.graphics.camera")
    assert defaults_camera["manual_camera"] is False


def test_settings_manager_persists_migrated_payload(tmp_path: Path) -> None:
    settings_path = _write_legacy_payload(tmp_path)

    manager = SettingsManager(settings_file=settings_path)
    manager.save()

    stored = json.loads(settings_path.read_text(encoding="utf-8"))

    assert stored["metadata"]["units_version"] == "si_v2"

    current_env = stored["current"]["graphics"]["environment"]
    assert "probeBrightness" not in current_env
    assert "probe_brightness" not in current_env
    assert current_env["skybox_brightness"] == pytest.approx(1.6)
    assert current_env["ibl_source"] == "assets/hdr/legacy_added.hdr"

    defaults_env = stored["defaults_snapshot"]["graphics"]["environment"]
    assert "probe_brightness" not in defaults_env
    assert defaults_env["skybox_brightness"] == pytest.approx(0.75)
    assert defaults_env["ibl_source"] == "c:/hdr/legacy_default.hdr"

    current_effects = stored["current"]["graphics"].get("effects", {})
    assert "tonemapActive" not in current_effects
    assert current_effects["tonemap_enabled"] is True
    assert current_effects["bloom_hdr_max"] == pytest.approx(3.5)
    assert current_effects["motion_blur"] is False

    defaults_effects = stored["defaults_snapshot"]["graphics"].get("effects", {})
    assert "colorBrightness" not in defaults_effects
    assert defaults_effects["adjustment_brightness"] == pytest.approx(1.15)

    current_camera = stored["current"]["graphics"].get("camera", {})
    assert current_camera["manual_camera"] is True

    defaults_camera = stored["defaults_snapshot"]["graphics"].get("camera", {})
    assert defaults_camera["manual_camera"] is False

    current_geometry = stored["current"].get("geometry", {})
    assert "frame_length_mm" not in current_geometry
    assert current_geometry["frame_length_m"] == pytest.approx(2.5)
    assert current_geometry["lever_length_m"] == pytest.approx(0.64)
    assert current_geometry["lever_length"] == pytest.approx(0.64)

    defaults_geometry = stored["defaults_snapshot"].get("geometry", {})
    assert "frame_length_mm" not in defaults_geometry
    assert defaults_geometry["frame_length_m"] == pytest.approx(1.8)
    assert defaults_geometry["lever_length_m"] == pytest.approx(0.55)
    assert defaults_geometry["lever_length"] == pytest.approx(0.55)

    assert stored["legacy"] == {"unused": True}
