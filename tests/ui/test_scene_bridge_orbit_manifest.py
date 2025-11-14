"""Дополнительный тест покрытия refresh_orbit_presets SceneBridge."""

from __future__ import annotations

import pytest

from src.common.settings_manager import SettingsManager
from src.ui.scene_bridge import SceneBridge

pytestmark = pytest.mark.usefixtures("qt_runtime_ready")


def test_scene_bridge_refresh_orbit_presets_manifest_version_increment(monkeypatch):
    manager = SettingsManager()
    bridge = SceneBridge(settings_manager=manager)

    original = manager.get_orbit_presets()
    base_version = int(original.get("version", 0))

    updated_manifest = {
        "version": base_version + 5,
        "default": original.get("default"),
        "presets": original.get("presets", []),
        "index": original.get("index", {}),
    }

    def fake_refresh() -> dict[str, object]:  # noqa: D401
        manager._orbit_presets = updated_manifest  # type: ignore[attr-defined]
        return updated_manifest

    monkeypatch.setattr(manager, "refresh_orbit_presets", fake_refresh)

    received = bridge.refresh_orbit_presets()
    assert received["version"] == updated_manifest["version"]
    assert bridge.camera.get("orbitPresetVersion") == updated_manifest["version"]
    assert (
        bridge.latestUpdates["camera"]["orbitPresetVersion"]
        == updated_manifest["version"]
    )
