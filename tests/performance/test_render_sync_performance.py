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


@pytest.mark.performance
@pytest.mark.usefixtures("settings_manager")
def test_prepare_for_qml_handles_interaction_payloads_fast(settings_manager) -> None:
    payload = {
        "three_d": {
            "interaction": {
                "enabled": True,
                "pan_speed": 0.02,
                "orbit_target": {"x": 0.1, "y": -0.2, "z": 1.5},
                "lock_axis": "z",
            },
            "flow_network": {
                "lines": {line.value: {"pressure": 110_000} for line in Line}
            },
        },
        "render": {
            "samples": [1, 2, 4, 8],
            "output": {"path": Path("./reports/render/output.exr"), "bit_depth": 16},
        },
    }

    iterations = 120
    start = time.perf_counter()
    prepared = None
    for _ in range(iterations):
        prepared = QMLBridge._prepare_for_qml(payload)
    elapsed = time.perf_counter() - start
    assert prepared is not None

    average_ms = (elapsed / iterations) * 1000.0
    _persist_metric(
        "prepare_for_qml_interaction_payload",
        {
            "iterations": iterations,
            "total_seconds": elapsed,
            "average_ms": average_ms,
            "budget_ms": 3.0,
        },
    )

    assert average_ms < 3.0, "QML payload preparation exceeds interaction budget"


@pytest.mark.performance
@pytest.mark.usefixtures("settings_manager")
def test_batched_dispatch_merges_without_allocation_spikes(settings_manager) -> None:
    service = VisualizationService(settings_manager=settings_manager)
    updates = {
        "scene": {
            "scale_factor": 1.25,
            "ambient_occlusion": {"enabled": True, "radius": 0.4},
        },
        "lighting": {"exposure": 1.15, "contrast_curve": [0.1, 0.5, 1.0]},
        "materials": {"brdf": {"name": "ggx", "roughness": 0.32}},
    }

    service.dispatch_updates(updates)
    iterations = 180
    start = time.perf_counter()
    snapshot = None
    for _ in range(iterations):
        snapshot = service.dispatch_updates(updates)
        merged: dict[str, dict[str, object]] = {}
        QMLBridge._deep_merge_dicts(merged, snapshot)  # type: ignore[arg-type]
    elapsed = time.perf_counter() - start

    assert snapshot is not None
    average_ms = (elapsed / iterations) * 1000.0
    _persist_metric(
        "render_state_merge",
        {
            "iterations": iterations,
            "total_seconds": elapsed,
            "average_ms": average_ms,
            "budget_ms": 3.5,
        },
    )

    assert average_ms < 3.5, "State merge routine exceeds render sync budget"
