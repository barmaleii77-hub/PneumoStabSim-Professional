"""Integration tests covering legacy settings migration via SettingsService."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.core.settings_models import dump_settings
from src.core.settings_service import SettingsService

REPO_ROOT = Path(__file__).resolve().parents[2]
LEGACY_SETTINGS = REPO_ROOT / "tmp_legacy" / "app_settings.json"
SCHEMA_PATH = REPO_ROOT / "schemas" / "settings" / "app_settings.schema.json"


def test_settings_service_migrates_real_legacy_payload(tmp_path: Path) -> None:
    """SettingsService.load should migrate an old settings payload end-to-end."""

    legacy_copy = tmp_path / "app_settings.json"
    legacy_copy.write_bytes(LEGACY_SETTINGS.read_bytes())

    service = SettingsService(settings_path=legacy_copy, schema_path=SCHEMA_PATH)

    settings = service.load()
    payload = dump_settings(settings)

    assert payload["metadata"]["units_version"] == "si_v2"

    current_env = payload["current"]["graphics"]["environment"]
    assert current_env["skybox_brightness"] == pytest.approx(1.6)
    assert current_env["ibl_source"] == "assets/hdr/legacy_added.hdr"

    defaults_env = payload["defaults_snapshot"]["graphics"]["environment"]
    assert defaults_env["skybox_brightness"] == pytest.approx(0.75)
    assert defaults_env["ibl_source"] == "c:/hdr/legacy_default.hdr"

    current_effects = payload["current"]["graphics"]["effects"]
    assert current_effects["tonemap_enabled"] is True
    assert current_effects["bloom_hdr_max"] == pytest.approx(3.5)
    assert current_effects["motion_blur"] is False

    defaults_effects = payload["defaults_snapshot"]["graphics"]["effects"]
    assert defaults_effects["tonemap_enabled"] is False
    assert defaults_effects["adjustment_brightness"] == pytest.approx(1.15)

    current_camera = payload["current"]["graphics"]["camera"]
    assert current_camera["manual_camera"] is True

    defaults_camera = payload["defaults_snapshot"]["graphics"]["camera"]
    assert defaults_camera["manual_camera"] is False

    current_geometry = payload["current"].get("geometry", {})
    assert current_geometry["frame_length_m"] == pytest.approx(2.5)
    assert current_geometry["lever_length_m"] == pytest.approx(0.64)
    assert current_geometry["lever_length"] == pytest.approx(0.64)

    defaults_geometry = payload["defaults_snapshot"].get("geometry", {})
    assert defaults_geometry["frame_length_m"] == pytest.approx(1.8)
    assert defaults_geometry["lever_length_m"] == pytest.approx(0.55)
    assert defaults_geometry["lever_length"] == pytest.approx(0.55)

    assert payload["legacy"] == {"unused": True}
