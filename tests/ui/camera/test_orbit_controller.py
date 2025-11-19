from __future__ import annotations

import json
from typing import Any

import pytest

from tests.helpers.qt import require_qt_modules

QtCore, *_ = require_qt_modules("PySide6.QtCore", "PySide6.QtGui", "PySide6.QtWidgets")
Qt = QtCore.Qt

from src.common.settings_manager import SettingsManager  # noqa: E402

try:  # pragma: no cover - exercised in Qt-enabled environments
    from src.ui.camera import CameraWidget, OrbitController
    from src.ui.hud.diagnostics_overlay import DiagnosticsOverlay
    from src.ui.hud.diagnostics_service import DiagnosticsService
except ImportError as exc:  # pragma: no cover - exercised in Qt-enabled environments
    pytest.fail(
        "Qt UI dependencies must be importable for cross-platform tests. "
        f"Re-run `python -m tools.cross_platform_test_prep --use-uv --run-tests`: {exc}"
    )


class _StubVisualizationService:
    def __init__(self) -> None:
        self.prepared: list[dict[str, Any]] = []
        self.dispatched: list[dict[str, dict[str, Any]]] = []

    def prepare_camera_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        snapshot = dict(payload)
        snapshot.setdefault(
            "hudTelemetry", {"distance": payload.get("orbit_distance", 0.0)}
        )
        self.prepared.append(snapshot)
        return snapshot

    def dispatch_updates(
        self, updates: dict[str, dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        self.dispatched.append({key: dict(value) for key, value in updates.items()})
        return updates


@pytest.fixture()
def settings_manager(tmp_path, monkeypatch) -> SettingsManager:
    settings_path = tmp_path / "app_settings.json"
    settings_payload = {
        "metadata": {},
        "current": {"graphics": {"camera": {"orbit_distance": 2.0}}},
        "defaults_snapshot": {"graphics": {"camera": {}}},
    }
    settings_path.write_text(json.dumps(settings_payload), encoding="utf-8")

    manifest_path = tmp_path / "orbit_presets.json"
    manifest_payload = {
        "version": 1,
        "default": "rigid",
        "presets": [
            {
                "id": "rigid",
                "values": {
                    "orbit_distance": 4.4,
                    "orbit_pitch": -18.0,
                    "orbit_inertia_enabled": False,
                },
            }
        ],
    }
    manifest_path.write_text(json.dumps(manifest_payload), encoding="utf-8")
    monkeypatch.setenv("PSS_ORBIT_PRESETS_FILE", str(manifest_path))

    return SettingsManager(settings_path)


def test_orbit_controller_applies_preset_and_updates_settings(settings_manager, qtbot):
    service = _StubVisualizationService()
    controller = OrbitController(
        settings_manager=settings_manager, visualization_service=service
    )

    manifest = controller.manifest()
    assert manifest["version"] == 1

    with qtbot.waitSignal(controller.presetApplied) as blocker:
        payload = controller.apply_preset("rigid")

    assert payload["orbitPresetId"] == "rigid"
    assert settings_manager.get("current.graphics.camera.orbitPresetId") == "rigid"
    assert service.prepared[-1]["orbitPresetId"] == "rigid"

    signal_preset, signal_payload = blocker.args
    assert signal_preset == "rigid"
    assert signal_payload["orbitPresetId"] == "rigid"


def test_orbit_controller_refreshes_manifest(
    settings_manager, qtbot, monkeypatch, tmp_path
):
    controller = OrbitController(settings_manager=settings_manager)

    manifest_path = tmp_path / "updated_presets.json"
    updated_manifest = {
        "version": 2,
        "default": "rigid",
        "presets": [
            {"id": "rigid", "values": {"orbit_distance": 4.8}},
            {"id": "cinematic", "values": {"orbit_distance": 5.1}},
        ],
    }
    manifest_path.write_text(json.dumps(updated_manifest), encoding="utf-8")
    monkeypatch.setenv("PSS_ORBIT_PRESETS_FILE", str(manifest_path))

    with qtbot.waitSignal(controller.manifestChanged):
        controller.refresh_presets()

    refreshed = controller.manifest()
    assert refreshed["version"] == 2
    assert any(entry.get("id") == "cinematic" for entry in refreshed.get("presets", []))


def test_camera_widget_double_click_triggers_auto_fit(qtbot):
    widget = CameraWidget()
    qtbot.addWidget(widget)

    with qtbot.assertNotEmitted(widget.autoFitRequested):
        qtbot.mouseClick(widget, Qt.LeftButton)

    with qtbot.waitSignal(widget.autoFitRequested):
        qtbot.mouseDClick(widget, Qt.LeftButton)


def test_diagnostics_overlay_routes_service_signals(qtbot):
    service = DiagnosticsService()
    overlay = DiagnosticsOverlay(diagnostics_service=service)

    with qtbot.waitSignal(overlay.metricsChanged) as metrics_blocker:
        service.publish_metrics({"frameTime": 16.7, "": "skip"})

    metrics_payload = metrics_blocker.args[0]
    assert metrics_payload["frameTime"] == 16.7
    assert "" not in metrics_payload
    assert overlay.metrics["frameTime"] == 16.7

    with qtbot.waitSignal(overlay.visibilityChanged):
        overlay.setVisible(True)
    assert overlay.visible is True

    with qtbot.waitSignal(overlay.metricsChanged):
        overlay.updateMetrics({"frameTime": 12.3})
    assert service.metrics()["frameTime"] == 12.3
