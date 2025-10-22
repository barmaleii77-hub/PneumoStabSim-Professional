"""Pytest-based smoke tests for runtime state and sync components."""

import sys
from pathlib import Path

import pytest

project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

pytest.importorskip("PySide6")

from runtime.state import StateSnapshot, StateBus, Line, Wheel  # noqa: E402
from runtime.sync import LatestOnlyQueue, PerformanceMetrics  # noqa: E402


def test_state_snapshot_defaults_are_valid():
    snapshot = StateSnapshot()

    assert snapshot.step_number == 0
    assert snapshot.simulation_time == pytest.approx(0.0)
    assert snapshot.validate()
    expected_wheels = {Wheel.LP, Wheel.PP, Wheel.LZ, Wheel.PZ}
    expected_lines = {Line.A1, Line.B1, Line.A2, Line.B2}

    assert set(snapshot.wheels.keys()) == expected_wheels
    assert set(snapshot.lines.keys()) == expected_lines


def test_state_snapshot_invalid_pressure_fails_validation():
    snapshot = StateSnapshot()
    first_line = next(iter(snapshot.lines.values()))
    first_line.pressure = -10.0

    assert not snapshot.validate()


def test_latest_only_queue_keeps_only_latest_item():
    queue = LatestOnlyQueue()

    assert queue.get_nowait() is None

    assert queue.put_nowait("first")
    assert queue.put_nowait("second")

    assert queue.get_nowait() == "second"
    assert queue.get_nowait() is None

    stats = queue.get_stats()
    assert stats["put_count"] == 2
    assert stats["dropped_count"] == 1
    assert stats["get_count"] == 1
    assert stats["efficiency"] == pytest.approx(0.5)


def test_performance_metrics_accumulates_statistics():
    metrics = PerformanceMetrics()

    metrics.update_step_time(0.002)
    metrics.update_step_time(0.003)

    assert metrics.total_steps == 2
    assert metrics.total_time == pytest.approx(0.005)
    assert metrics.min_step_time == pytest.approx(0.002)
    assert metrics.max_step_time == pytest.approx(0.003)
    assert metrics.avg_step_time == pytest.approx(0.0025)
    assert metrics.get_fps() == pytest.approx(400.0)

    metrics.update_realtime_factor(sim_dt=0.0025, real_dt=0.0025)
    assert metrics.realtime_factor == pytest.approx(1.0)
    assert metrics.is_realtime(tolerance=0.05)

    metrics.update_realtime_factor(sim_dt=0.0025, real_dt=0.0)
    assert metrics.realtime_factor == pytest.approx(1.0)


def test_state_bus_provides_qt_signals():
    bus = StateBus()

    assert hasattr(bus, "state_ready")
    assert hasattr(bus, "start_simulation")
    assert callable(bus.state_ready.emit)
    assert callable(bus.start_simulation.emit)
