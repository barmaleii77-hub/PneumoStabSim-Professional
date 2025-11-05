from __future__ import annotations

from typing import Any, Dict

import pytest

from src.ui.services.visualization_service import VisualizationService


def test_visualization_service_dispatch_and_reset() -> None:
    service = VisualizationService()

    updates = service.dispatch_updates({"geometry": {"mesh": "baseline"}})
    assert updates["geometry"]["mesh"] == "baseline"
    assert service.state_for("geometry")["mesh"] == "baseline"

    service.reset(["geometry"])
    assert service.state_for("geometry") == {}


def test_visualization_service_enriches_camera_payload() -> None:
    class DummyManager:
        def __init__(self) -> None:
            self._camera = {
                "orbitPresetId": "default",
                "orbit_target": {"x": 1.0, "y": 2.0, "z": 3.0},
            }

        def get(self, path: str, default: Any | None = None) -> Any:
            if path == "current.graphics.camera":
                return dict(self._camera)
            return default

        def refresh_orbit_presets(self) -> Dict[str, Any]:
            return self.get_orbit_presets()

        def get_orbit_presets(self) -> Dict[str, Any]:
            return {
                "version": 1,
                "default": "default",
                "presets": [
                    {
                        "id": "default",
                        "label": {"en": "Default"},
                    }
                ],
                "index": {"default": {"label": {"en": "Default"}}},
            }

    service = VisualizationService(settings_manager=DummyManager())

    payload = service.prepare_camera_payload({})
    assert payload["orbitPresetLabel"] == "Default"
    assert payload["orbit_target"]["x"] == pytest.approx(1.0)

    manifest = service.refresh_orbit_presets()
    assert manifest["default"] == "default"
