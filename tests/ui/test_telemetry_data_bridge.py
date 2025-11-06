"""Tests for the TelemetryDataBridge streaming helper."""

from __future__ import annotations

import math

from PySide6.QtTest import QSignalSpy

from src.pneumo.enums import Line
from src.runtime.state import StateSnapshot
from src.ui.bridge.telemetry_bridge import TelemetryDataBridge


def _make_snapshot(
    time_s: float,
    *,
    pressures: dict[Line, float],
    tank_pressure: float | None = None,
    frame: dict[str, float] | None = None,
):
    snapshot = StateSnapshot()
    snapshot.simulation_time = time_s
    frame = frame or {}
    for line_enum, value in pressures.items():
        snapshot.lines[line_enum].pressure = value
    snapshot.tank.pressure = (
        pressures.get(Line.A1, 0.0) if tank_pressure is None else tank_pressure
    )
    snapshot.frame.heave = frame.get("heave", 0.0)
    snapshot.frame.roll = frame.get("roll", 0.0)
    snapshot.frame.pitch = frame.get("pitch", 0.0)
    return snapshot


def test_push_snapshot_emits_active_metrics():
    bridge = TelemetryDataBridge(max_samples=8)
    spy = QSignalSpy(bridge.sampleAppended)

    snapshot = _make_snapshot(
        0.1,
        pressures={
            Line.A1: 101325.0,
            Line.B1: 110000.0,
            Line.A2: 108000.0,
            Line.B2: 109000.0,
        },
        tank_pressure=120000.0,
        frame={"heave": 0.02},
    )

    bridge.push_snapshot(snapshot)
    assert len(spy) == 1
    payload = spy[0][0]
    values = payload["values"]
    assert set(values.keys()) == {"pressure.a1", "pressure.b1", "pressure.a2"}
    assert math.isclose(values["pressure.a1"], 101325.0)

    exported = bridge.exportSeries(["pressure.a1", "pressure.tank"])
    assert "series" in exported
    assert len(exported["series"]["pressure.a1"]) == 1
    assert exported["series"]["pressure.tank"][0]["value"] == 120000.0


def test_update_interval_throttles_samples():
    bridge = TelemetryDataBridge(max_samples=8)
    bridge.setUpdateInterval(3)
    spy = QSignalSpy(bridge.sampleAppended)

    for idx in range(1, 5):
        snapshot = _make_snapshot(
            idx * 0.1,
            pressures={Line.A1: 100000.0 + idx * 1000},
            tank_pressure=105000.0,
        )
        bridge.push_snapshot(snapshot)

    assert len(spy) == 1
    payload = spy[0][0]
    assert math.isclose(payload["timestamp"], 0.3)

    exported = bridge.exportSeries(["pressure.a1"])
    assert len(exported["series"]["pressure.a1"]) == 1


def test_pause_and_reset_behaviour():
    bridge = TelemetryDataBridge(max_samples=8)
    spy = QSignalSpy(bridge.sampleAppended)

    first = _make_snapshot(0.1, pressures={Line.A1: 100000.0}, tank_pressure=100000.0)
    bridge.push_snapshot(first)
    assert len(spy) == 1

    bridge.setPaused(True)
    second = _make_snapshot(0.2, pressures={Line.A1: 105000.0}, tank_pressure=110000.0)
    bridge.push_snapshot(second)
    assert len(spy) == 1, "Paused bridge should not emit new samples"

    bridge.resetStream()
    exported = bridge.exportSeries(["pressure.a1"])
    assert exported["series"] == {}
    assert exported["oldestTimestamp"] == 0.0
*** End of File
