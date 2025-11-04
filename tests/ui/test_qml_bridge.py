"""Unit tests for :mod:`src.ui.qml_bridge` and helpers exposed to QML."""

from __future__ import annotations

import pytest

from src.common.settings_manager import SettingsManager
from src.ui.scene_bridge import SceneBridge
from src.ui.qml_bridge import QMLBridge

try:  # pragma: no cover - optional dependency for headless environments
    from PySide6 import QtCore, QtTest  # noqa: F401 - used to detect availability
except Exception:  # pragma: no cover - allow tests to be skipped when PySide6 is missing
    PYSIDE_AVAILABLE = False
else:  # pragma: no cover - executed only when PySide6 is present
    PYSIDE_AVAILABLE = True


def test_prepare_for_qml_adds_camel_case_aliases() -> None:
    payload = {
        "auto_rotate_speed": 1.0,
        "min_distance": 5,
        "nested": {"max_distance": 10},
    }

    result = QMLBridge._prepare_for_qml(payload)

    assert result["auto_rotate_speed"] == 1.0
    assert result["autoRotateSpeed"] == 1.0
    assert result["min_distance"] == 5
    assert result["minDistance"] == 5
    assert result["nested"]["max_distance"] == 10
    assert result["nested"]["maxDistance"] == 10


def test_prepare_for_qml_does_not_override_existing_camel_case() -> None:
    payload = {"autoRotate": True, "auto_rotate": False}

    result = QMLBridge._prepare_for_qml(payload)

    assert result["autoRotate"] is True
    assert result["auto_rotate"] is False


def test_settings_manager_loads_orbit_presets() -> None:
    manager = SettingsManager()

    presets = manager.get_orbit_presets()

    assert isinstance(presets, dict)
    assert presets.get("version") >= 1

    preset_ids = {entry.get("id") for entry in presets.get("presets", []) if isinstance(entry, dict)}
    assert {
        "baseline",
        "rigid",
        "smooth",
        "cinematic",
        "mobile_touch",
        "vr_precision",
        "low_motion",
    }.issubset(preset_ids)

    index = presets.get("index", {})
    baseline = index.get("baseline")
    assert baseline is not None
    assert baseline["values"]["orbit_inertia_enabled"] is True
    assert pytest.approx(baseline["values"]["orbit_inertia"], rel=1e-3) == 0.4


@pytest.mark.skipif(not PYSIDE_AVAILABLE, reason="PySide6 is required for SceneBridge")
def test_camera_hud_context() -> None:
    manager = SettingsManager()
    bridge = SceneBridge(settings_manager=manager)

    camera_payload = bridge.camera
    presets = manager.get_orbit_presets()

    assert "orbitPresets" in camera_payload
    assert camera_payload.get("orbitPresetVersion") == manager.get_orbit_presets().get("version")

    telemetry = camera_payload.get("hudTelemetry")
    assert isinstance(telemetry, dict)
    assert telemetry["pivot"]["z"] == pytest.approx(0.5, rel=1e-3)
    assert telemetry["distance"] >= 0.0
    assert telemetry["orbitPresetDefault"] == presets.get("default")
    assert telemetry["orbitPresetVersion"] == presets.get("version")

    latest = bridge.latestUpdates
    assert "camera" in latest


def test_scene_bridge_augments_camera_updates() -> None:
    manager = SettingsManager()
    bridge = SceneBridge(settings_manager=manager)

    payload = {
        "orbit_distance": 5.1,
        "orbit_target": {"x": 0.1, "y": -0.2, "z": 0.3},
        "orbit_inertia": 0.42,
        "orbit_inertia_enabled": True,
        "orbit_rotate_smoothing": 0.18,
        "orbit_pan_smoothing": 0.16,
        "orbit_zoom_smoothing": 0.2,
        "orbit_friction": 0.05,
    }

    bridge.dispatch_updates({"camera": payload})

    camera_state = bridge.camera
    telemetry = camera_state.get("hudTelemetry")

    assert isinstance(telemetry, dict)
    assert telemetry["distance"] == pytest.approx(5.1, rel=1e-3)
    assert telemetry["pivot"]["x"] == pytest.approx(0.1, rel=1e-3)
    assert telemetry["inertiaEnabled"] is True
    assert telemetry["rotateSmoothing"] == pytest.approx(0.18, rel=1e-3)
    assert telemetry["orbitPresetDefault"] == camera_state.get("orbitPresetDefault")
    assert telemetry["orbitPresetVersion"] == camera_state.get("orbitPresetVersion")

    presets = camera_state.get("orbitPresets")
    assert isinstance(presets, list) and presets
    assert camera_state.get("orbitPresetDefault")


@pytest.mark.skipif(not PYSIDE_AVAILABLE, reason="PySide6 is required for SceneBridge")
def test_scene_bridge_refresh_orbit_presets_emits_updates(monkeypatch) -> None:
    manager = SettingsManager()
    bridge = SceneBridge(settings_manager=manager)

    from PySide6 import QtTest  # type: ignore

    spy = QtTest.QSignalSpy(bridge.cameraChanged)

    manifest = manager.get_orbit_presets()
    updated_manifest = {
        "version": manifest.get("version", 0) + 1,
        "default": manifest.get("default"),
        "presets": manifest.get("presets", []),
        "index": manifest.get("index", {}),
    }

    def fake_refresh() -> dict[str, object]:
        manager._orbit_presets = updated_manifest  # type: ignore[attr-defined]
        return updated_manifest

    monkeypatch.setattr(manager, "refresh_orbit_presets", fake_refresh)

    result = bridge.refresh_orbit_presets()

    assert result["version"] == updated_manifest["version"]
    assert spy.count() >= 1

    camera_payload = bridge.camera
    assert camera_payload.get("orbitPresetVersion") == updated_manifest["version"]
    assert bridge.latestUpdates["camera"]["orbitPresetVersion"] == updated_manifest["version"]
