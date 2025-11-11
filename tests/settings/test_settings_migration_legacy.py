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
                }
            },
            "simulation": {"physics_dt": 0.0025},
        },
        "defaults_snapshot": {
            "graphics": {
                "environment": {
                    "probe_brightness": 0.75,
                    "iblSource": "C\\HDR\\legacy_default.hdr",
                }
            },
            "simulation": {"physics_dt": 0.0025},
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

    assert stored["legacy"] == {"unused": True}
