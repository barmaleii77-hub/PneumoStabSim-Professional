"""Comprehensive pytest coverage for runtime utilities."""

import sys
import pytest
from pathlib import Path

project_root = Path(__file__).parent.parent
src_path = project_root / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

pytest.importorskip("PySide6")

import runtime.sync as sync_module  # noqa: E402
from runtime.state import FrameState, Line, StateSnapshot, Wheel  # noqa: E402
from runtime.sync import (  # noqa: E402
    LatestOnlyQueue,
    PerformanceMetrics,
    TimingAccumulator,
)


def test_state_snapshot_arrays_and_validation():
    snapshot = StateSnapshot()
    snapshot.simulation_time = 1.0
    snapshot.step_number = 100
    snapshot.frame = FrameState(heave=0.01, roll=0.005, pitch=0.002)

    pressures = snapshot.get_pressure_array()
    flows = snapshot.get_flow_array()

    assert pressures.shape == (4,)
    assert all(value > 0 for value in pressures)
    assert flows == pytest.approx([0.0, 0.0, 0.0])
    assert snapshot.validate()


def test_state_snapshot_invalid_orientation_fails_validation():
    snapshot = StateSnapshot()
    snapshot.frame.roll = 1.0

    assert not snapshot.validate()


def test_latest_only_queue_stats_reset():
    queue = LatestOnlyQueue()
    queue.put_nowait({"value": 1})
    queue.put_nowait({"value": 2})
    assert queue.get_nowait() == {"value": 2}

    queue.reset_stats()
    stats = queue.get_stats()
    assert stats["put_count"] == 0
    assert stats["get_count"] == 0
    assert stats["dropped_count"] == 0
    assert stats["efficiency"] == 0


def test_performance_metrics_summary_values():
    metrics = PerformanceMetrics(target_dt=0.01)
    metrics.update_step_time(0.02)
    metrics.update_realtime_factor(sim_dt=0.02, real_dt=0.02)

    summary = metrics.get_summary()
    assert summary["steps"] == 1
    assert summary["fps_actual"] == pytest.approx(50.0)
    assert summary["fps_target"] == pytest.approx(100.0)
    assert summary["realtime_factor"] == pytest.approx(1.0)


def test_timing_accumulator_regular_updates(monkeypatch):
    time_values = iter([100.0, 100.015, 100.03])
    monkeypatch.setattr(
        sync_module.time,
        "perf_counter",
        lambda: next(time_values),
    )

    accumulator = TimingAccumulator(target_dt=0.01, max_steps_per_frame=5)

    steps_first = accumulator.update()
    assert steps_first == 1
    assert 0.0 < accumulator.get_interpolation_alpha() < 1.0

    steps_second = accumulator.update()
    assert steps_second == 2
    assert accumulator.get_interpolation_alpha() == pytest.approx(0.0)
    assert accumulator.get_realtime_factor() == pytest.approx(1.0)


def test_timing_accumulator_respects_step_limit(monkeypatch):
    time_values = iter([200.0, 200.2])
    monkeypatch.setattr(
        sync_module.time,
        "perf_counter",
        lambda: next(time_values),
    )

    accumulator = TimingAccumulator(
        target_dt=0.01,
        max_steps_per_frame=3,
        max_frame_time=0.05,
    )

    steps = accumulator.update()
    assert steps == 3
    assert accumulator.get_interpolation_alpha() > 1.0


def test_state_snapshot_wheel_population():
    snapshot = StateSnapshot()
    for wheel in (Wheel.LP, Wheel.PP, Wheel.LZ, Wheel.PZ):
        assert wheel in snapshot.wheels
        assert snapshot.wheels[wheel].wheel == wheel

    for line in (Line.A1, Line.B1, Line.A2, Line.B2):
        assert line in snapshot.lines
        assert snapshot.lines[line].line == line
