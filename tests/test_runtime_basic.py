"""Pytest-based smoke tests for runtime state and sync components."""

import sys
from pathlib import Path

import pytest

PA_ATM = 101325.0
T_AMBIENT = 293.15

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

    for wheel_state in snapshot.wheels.values():
        wheel_state.lever_angle = 0.0
        wheel_state.lever_angle_min = -0.5
        wheel_state.lever_angle_max = 0.5
        wheel_state.vol_head = 1e-4
        wheel_state.vol_head_min = 5e-5
        wheel_state.vol_head_max = 2e-4
        wheel_state.vol_rod = 1e-4
        wheel_state.vol_rod_min = 5e-5
        wheel_state.vol_rod_max = 2e-4

    for line_state in snapshot.lines.values():
        line_state.pressure = PA_ATM
        line_state.pressure_min = PA_ATM * 0.5
        line_state.pressure_max = PA_ATM * 5.0
        line_state.volume = 1e-4
        line_state.volume_min = 5e-5
        line_state.volume_max = 2e-4
        line_state.temperature = T_AMBIENT

    snapshot.tank.pressure = PA_ATM
    snapshot.tank.pressure_min = PA_ATM * 0.5
    snapshot.tank.pressure_max = PA_ATM * 5.0
    snapshot.tank.volume = 5e-3
    snapshot.tank.volume_min = 1e-3
    snapshot.tank.volume_max = 1e-2
    snapshot.tank.temperature = T_AMBIENT

    assert snapshot.validate()
    expected_wheels = {Wheel.LP, Wheel.PP, Wheel.LZ, Wheel.PZ}
    expected_lines = {Line.A1, Line.B1, Line.A2, Line.B2}

    assert set(snapshot.wheels.keys()) == expected_wheels
    assert set(snapshot.lines.keys()) == expected_lines


def test_state_snapshot_invalid_pressure_fails_validation():
    snapshot = StateSnapshot()

    for wheel_state in snapshot.wheels.values():
        wheel_state.lever_angle = 0.0
        wheel_state.lever_angle_min = -0.5
        wheel_state.lever_angle_max = 0.5
        wheel_state.vol_head = 1e-4
        wheel_state.vol_head_min = 5e-5
        wheel_state.vol_head_max = 2e-4
        wheel_state.vol_rod = 1e-4
        wheel_state.vol_rod_min = 5e-5
        wheel_state.vol_rod_max = 2e-4

    for line_state in snapshot.lines.values():
        line_state.pressure = PA_ATM
        line_state.pressure_min = PA_ATM * 0.5
        line_state.pressure_max = PA_ATM * 5.0
        line_state.volume = 1e-4
        line_state.volume_min = 5e-5
        line_state.volume_max = 2e-4
        line_state.temperature = T_AMBIENT

    snapshot.tank.pressure = PA_ATM
    snapshot.tank.pressure_min = PA_ATM * 0.5
    snapshot.tank.pressure_max = PA_ATM * 5.0
    snapshot.tank.volume = 5e-3
    snapshot.tank.volume_min = 1e-3
    snapshot.tank.volume_max = 1e-2
    snapshot.tank.temperature = T_AMBIENT

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
