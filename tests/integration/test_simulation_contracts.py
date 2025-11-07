"""Contract tests covering simulation ⇄ UI messaging protocols."""

from __future__ import annotations

import math

import pytest

from tests.helpers.fake_components import (
    FakeEcuGateway,
    FakeSettingsOrchestrator,
    FakeVisualizationClient,
)

from src.simulation.presets import get_default_training_library
from src.simulation.service import TrainingPresetService
from src.ui.scene_bridge import SceneBridge
from src.ui.services.visualization_service import VisualizationService


def _initial_state_from_preset(preset) -> dict[str, dict[str, object]]:
    return {
        "current": {
            "simulation": {
                key: float(value) for key, value in preset.simulation.items()
            },
            "pneumatic": dict(preset.pneumatic),
        }
    }


def test_training_preset_service_contract():
    """The service must expose deterministic payloads and drift detection."""

    library = get_default_training_library()
    preset = library.list_presets()[0]
    orchestrator = FakeSettingsOrchestrator(
        initial_state=_initial_state_from_preset(preset)
    )

    service = TrainingPresetService(orchestrator=orchestrator, library=library)

    unsubscribe = lambda: None
    try:
        payload = service.list_presets()
        assert payload, "Preset catalogue should not be empty"
        qml_payload = service.describe_preset(preset.id)
        assert qml_payload["metadata"]["scenarioId"]

        observer_calls: list[str] = []
        unsubscribe = service.register_active_observer(observer_calls.append)
        assert observer_calls[-1] == preset.id

        updates = service.apply_preset(preset.id)
        assert updates
        assert all(key.startswith("current.") for key in updates.keys())

        orchestrator.inject_external_change({"current.simulation.physics_dt": 0.123})
        assert service.active_preset_id() == ""
        assert observer_calls[-1] == ""
    finally:
        unsubscribe()
        service.close()


def test_ecu_gateway_delivers_latest_snapshot():
    """Only the most recent physics snapshot should reach the ECU."""

    gateway = FakeEcuGateway()

    for index in range(5):
        gateway.publish_state({"frame": index})

    latest = gateway.poll()
    assert latest == {"frame": 4}

    stats = gateway.statistics()
    assert math.isclose(stats["put_count"], 5.0)
    assert math.isclose(stats["dropped_count"], 4.0)
    assert math.isclose(stats["get_count"], 1.0)

    assert gateway.poll() is None, (
        "Queue should be empty after consuming the latest state"
    )


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_scene_bridge_dispatches_enriched_updates(qtbot, settings_manager):
    """Visualization updates must surface access metadata and telemetry."""

    pytest.importorskip("PySide6.QtCore")

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

        def _have_payload() -> bool:
            return any(name == "updatesDispatched" for name, _ in client.events)

        qtbot.waitUntil(_have_payload, timeout=1000)
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


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_state_bus_signals_logged(caplog):
    """Signal tracer must record StateBus events for diagnostics."""

    pytest.importorskip("PySide6.QtCore")

    from src.diagnostics import SignalTracer
    from src.runtime.state import StateBus

    caplog.set_level("INFO", logger="diagnostics.signals")

    bus = StateBus()
    tracer = SignalTracer(max_records=10)
    detach = tracer.attach(bus, "start_simulation", alias="bus:start")

    try:
        bus.start_simulation.emit()
        records = tracer.records
        assert records, "No signals were captured"
        assert records[-1].signal == "bus:start"
        assert not records[-1].args
        assert any(record.message == "signal_trace_event" for record in caplog.records)
    finally:
        detach()
        tracer.dispose()
        bus.deleteLater()
