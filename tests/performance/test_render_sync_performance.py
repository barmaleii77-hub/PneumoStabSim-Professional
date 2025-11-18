"""Performance checks for render payload preparation and sync loops."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from src.pneumo.enums import Line
from src.runtime.state import StateSnapshot
from src.ui.qml_bridge import QMLBridge
from src.ui.services.visualization_service import VisualizationService

REPORT_PATH = Path("reports/tests/render_sync_performance.json")


def _persist_metric(metric: str, payload: dict[str, object]) -> None:
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    existing: dict[str, object] = {}
    if REPORT_PATH.exists():
        try:
            existing = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            existing = {}
    existing[metric] = payload
    REPORT_PATH.write_text(json.dumps(existing, indent=2), encoding="utf-8")


def _make_snapshot() -> StateSnapshot:
    snapshot = StateSnapshot()
    snapshot.simulation_time = 1.2

    line_a1 = snapshot.lines[Line.A1]
    line_a1.flow_atmo = 0.12
    line_a1.flow_tank = 0.02
    line_a1.pressure = 110_000.0

    line_b1 = snapshot.lines[Line.B1]
    line_b1.flow_atmo = 0.03
    line_b1.flow_tank = 0.08
    line_b1.pressure = 105_000.0

    snapshot.tank.pressure = 125_000.0
    snapshot.tank.temperature = 304.0
    snapshot.tank.flow_min = 0.06
    snapshot.tank.flow_stiff = 0.02
    snapshot.tank.flow_safety = 0.01

    return snapshot


@pytest.mark.performance
@pytest.mark.usefixtures("settings_manager")
def test_snapshot_payload_under_latency_budget(settings_manager) -> None:
    snapshot = _make_snapshot()
    iterations = 250

    start = time.perf_counter()
    payload = None
    for _ in range(iterations):
        payload = QMLBridge._snapshot_to_payload(snapshot)
    elapsed = time.perf_counter() - start
    assert payload is not None

    average_ms = (elapsed / iterations) * 1000.0
    _persist_metric(
        "snapshot_to_payload",
        {
            "iterations": iterations,
            "total_seconds": elapsed,
            "average_ms": average_ms,
            "budget_ms": 5.0,
        },
    )

    assert average_ms < 5.0, "Snapshot payload generation exceeds latency budget"


@pytest.mark.performance
@pytest.mark.usefixtures("settings_manager")
def test_visualization_service_dispatch_is_lightweight(settings_manager) -> None:
    service = VisualizationService(settings_manager=settings_manager)
    updates = {
        "quality": {"msaa": 4},
        "camera": {"orbit_target": {"x": 0.1, "y": 0.2, "z": -1.2}},
        "threeD": {"flowNetwork": {"lines": {}}},
    }

    iterations = 500
    start = time.perf_counter()
    latest = None
    for _ in range(iterations):
        latest = service.dispatch_updates(updates)
    elapsed = time.perf_counter() - start
    assert latest is not None

    average_ms = (elapsed / iterations) * 1000.0
    _persist_metric(
        "visualization_dispatch",
        {
            "iterations": iterations,
            "total_seconds": elapsed,
            "average_ms": average_ms,
            "budget_ms": 4.0,
        },
    )

    assert latest["quality"]["msaa"] == 4
    assert average_ms < 4.0, "Visualization dispatch path exceeds latency budget"
