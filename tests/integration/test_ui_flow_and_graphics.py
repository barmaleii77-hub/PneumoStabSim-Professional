"""Integration checks for flow visualisation, telemetry charts, and graphics payloads."""

from __future__ import annotations

from typing import Any

import pytest

from src.pneumo.enums import Line
from src.runtime.state import StateSnapshot
from src.ui.bridge.telemetry_bridge import TelemetryDataBridge
from src.ui.qml_bridge import QMLBridge
from src.ui.services.visualization_service import VisualizationService


def _make_snapshot() -> StateSnapshot:
    snapshot = StateSnapshot()
    snapshot.simulation_time = 2.5

    line_a1 = snapshot.lines[Line.A1]
    line_a1.flow_atmo = 0.08
    line_a1.flow_tank = 0.02
    line_a1.pressure = 120_000.0
    line_a1.temperature = 305.0
    line_a1.cv_atmo_open = True

    line_b1 = snapshot.lines[Line.B1]
    line_b1.flow_atmo = 0.01
    line_b1.flow_tank = 0.05
    line_b1.pressure = 118_000.0
    line_b1.temperature = 300.0
    line_b1.cv_tank_open = True

    snapshot.tank.pressure = 130_000.0
    snapshot.tank.temperature = 303.0
    snapshot.tank.flow_min = 0.05
    snapshot.tank.relief_min_open = True
    snapshot.tank.flow_stiff = -0.02
    snapshot.tank.relief_stiff_open = True
    snapshot.tank.flow_safety = 0.01
    snapshot.tank.relief_safety_open = False

    snapshot.master_isolation_open = True
    snapshot.frame.heave = 0.12
    snapshot.frame.roll = 0.02
    snapshot.frame.pitch = -0.01

    return snapshot


def test_qml_bridge_snapshot_includes_flow_network_metadata() -> None:
    snapshot = _make_snapshot()

    payload = QMLBridge._snapshot_to_payload(snapshot)
    three_d = payload["threeD"]
    flow_network = three_d["flowNetwork"]

    lines = flow_network["lines"]
    assert set(lines.keys()) >= {"a1", "b1"}
    assert lines["a1"]["direction"] == "intake"
    assert lines["b1"]["direction"] == "exhaust"

    max_line_intensity = flow_network["maxLineIntensity"]
    assert pytest.approx(max_line_intensity, rel=1e-6) == 0.06
    assert pytest.approx(lines["a1"]["animationSpeed"], rel=1e-6) == 1.0
    assert pytest.approx(lines["b1"]["animationSpeed"], rel=1e-6) == pytest.approx(
        0.04 / 0.06, rel=1e-6
    )

    receiver = flow_network["receiver"]
    assert pytest.approx(receiver["pressures"]["a1"], rel=1e-6) == pytest.approx(
        snapshot.lines[Line.A1].pressure, rel=1e-6
    )
    assert pytest.approx(receiver["tankPressure"], rel=1e-6) == pytest.approx(
        snapshot.tank.pressure, rel=1e-6
    )
    assert receiver["minPressure"] <= receiver["maxPressure"]
    assert three_d["receiver"] == receiver

    relief = flow_network["relief"]
    assert relief["min"]["direction"] == "exhaust"
    assert relief["stiff"]["direction"] == "intake"
    assert relief["safety"]["direction"] == "exhaust"

    tank_flows = flow_network["tank"]["flows"]
    expected_total = (
        snapshot.tank.flow_min + snapshot.tank.flow_stiff + snapshot.tank.flow_safety
    )
    assert pytest.approx(tank_flows["total"], rel=1e-6) == pytest.approx(
        expected_total, rel=1e-6
    )


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_telemetry_bridge_streams_flow_metrics(qapp) -> None:
    snapshot = _make_snapshot()

    bridge = TelemetryDataBridge(max_samples=32)
    bridge.setActiveMetrics(["flow.inflow", "flow.outflow", "flow.tank_relief"])

    samples: list[dict[str, Any]] = []

    def _capture(payload: dict[str, Any]) -> None:
        samples.append({key: value for key, value in payload.items()})

    bridge.sampleAppended.connect(_capture)
    bridge.push_snapshot(snapshot)
    qapp.processEvents()

    assert samples, "Telemetry bridge did not emit any samples"
    latest = samples[-1]
    values = latest["values"]
    assert pytest.approx(values["flow.inflow"], rel=1e-6) == pytest.approx(
        0.09, rel=1e-6
    )
    assert pytest.approx(values["flow.outflow"], rel=1e-6) == pytest.approx(
        0.07, rel=1e-6
    )
    assert pytest.approx(values["flow.tank_relief"], rel=1e-6) == pytest.approx(
        0.04, rel=1e-6
    )


class _StubAccessControl:
    def __init__(self) -> None:
        self._profile = {
            "role": "engineer",
            "actor": "integration",
            "description": "integration test",
            "uiFlags": {"graphics": True},
            "simulationProfile": "test",
            "editablePrefixes": ["current.graphics.camera"],
        }

    def can_modify(self, target: str) -> bool:
        return target.endswith("camera")

    def describe_access_profile(self) -> dict[str, Any]:
        return dict(self._profile)


def test_visualization_service_enriches_graphics_payload(settings_manager) -> None:
    service = VisualizationService(
        settings_manager=settings_manager,
        access_control=_StubAccessControl(),
    )

    updates = {
        "quality": {"msaa": 8, "taa": "high"},
        "camera": {
            "orbit_target": {"x": 1.0, "y": 2.0, "z": -0.5},
            "pan": {"x": 0.1, "y": -0.2, "z": 0.0},
            "speed": 0.25,
        },
        "threeD": {"flowNetwork": {"lines": {}}},
    }

    sanitized = service.dispatch_updates(updates)
    assert set(sanitized.keys()) == {"quality", "camera", "threeD"}

    quality_payload = sanitized["quality"]
    assert quality_payload is not updates["quality"], "Payload should be defensive copy"
    assert quality_payload["_access"]["canEdit"] is False

    camera_payload = sanitized["camera"]
    assert camera_payload["_access"]["canEdit"] is True
    telemetry = camera_payload.get("hudTelemetry")
    assert telemetry is not None and telemetry["pivot"]["z"] == pytest.approx(
        -0.5, rel=1e-6
    )

    latest = service.latest_updates()["camera"]
    assert latest["hudTelemetry"]["pivot"]["x"] == pytest.approx(1.0, rel=1e-6)
    assert latest["_access"]["role"] == "engineer"
