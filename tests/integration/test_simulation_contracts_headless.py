from __future__ import annotations

import pytest


@pytest.mark.integration
@pytest.mark.headless
@pytest.mark.usefixtures("headless_env", "headless_qt_modules")
def test_training_preset_service_contract_headless(settings_manager, headless_qtbot):
    from tests.helpers.fake_components import (
        FakeSettingsOrchestrator,
    )
    from src.simulation.presets import get_default_training_library
    from src.simulation.service import TrainingPresetService

    library = get_default_training_library()
    preset = library.list_presets()[0]
    orchestrator = FakeSettingsOrchestrator(
        initial_state={
            "current": {"simulation": {"physics_dt": preset.simulation["physics_dt"]}},
            "defaults_snapshot": {},
        }
    )
    service = TrainingPresetService(orchestrator=orchestrator, library=library)
    unsubscribe = lambda: None

    try:
        payload = service.list_presets()
        assert payload, "Preset catalogue should not be empty"

        observer_calls: list[str] = []
        unsubscribe = service.register_active_observer(observer_calls.append)

        updates = service.apply_preset(preset.id)
        assert updates
        assert all(key.startswith("current.") for key in updates.keys())

        headless_qtbot.waitUntil(
            lambda: observer_calls and observer_calls[-1] == preset.id
        )

        orchestrator.inject_external_change({"current.simulation.physics_dt": 0.123})
        headless_qtbot.waitUntil(lambda: service.active_preset_id() == "")
    finally:
        unsubscribe()
        service.close()


@pytest.mark.integration
@pytest.mark.headless
@pytest.mark.usefixtures("headless_env", "headless_qt_modules")
def test_scene_bridge_dispatches_enriched_updates_headless(
    settings_manager, headless_qtbot
):
    from tests.helpers.fake_components import FakeVisualizationClient
    from src.ui.scene_bridge import SceneBridge
    from src.ui.services.visualization_service import VisualizationService

    service = VisualizationService(settings_manager=settings_manager)
    bridge = SceneBridge(
        visualization_service=service, settings_manager=settings_manager
    )
    client = FakeVisualizationClient()
    client.bind(bridge)

    try:
        assert bridge.dispatch_updates(
            {
                "geometry": {"nodes": 128},
                "camera": {"orbit_target": {"x": 1.0, "y": 2.0, "z": 3.0}},
            }
        )

        headless_qtbot.waitUntil(
            lambda: any(name == "updatesDispatched" for name, _ in client.events),
            timeout=1000,
        )
        dispatched = [
            payload for name, payload in client.events if name == "updatesDispatched"
        ]
        assert dispatched, "Bridge should emit consolidated payloads"
        bundle = dispatched[-1]
        assert "geometry" in bundle and "camera" in bundle
        camera_payload = bundle["camera"]
        assert "_access" in camera_payload
        assert "hudTelemetry" in camera_payload
    finally:
        client.dispose()
        bridge.deleteLater()
