import pytest

from src.runtime.sync import (
    LatestOnlyQueue,
    StateSnapshotBuffer,
    TimingAccumulator,
)


def test_latest_only_queue_retains_only_latest_item() -> None:
    queue = LatestOnlyQueue()

    assert queue.is_empty()

    first_put = queue.put_nowait({"value": 1})
    second_put = queue.put_nowait({"value": 2})

    assert first_put is True
    assert second_put is True
    assert queue.qsize() == 1

    item = queue.get_nowait()
    assert item == {"value": 2}

    stats = queue.get_stats()
    assert stats["put_count"] == pytest.approx(2.0)
    assert stats["get_count"] == pytest.approx(1.0)
    assert stats["dropped_count"] == pytest.approx(1.0)
    assert stats["efficiency"] == pytest.approx(0.5)


def test_latest_only_queue_does_not_leak_unfinished_tasks() -> None:
    queue = LatestOnlyQueue()

    for value in range(5):
        queue.put_nowait({"value": value})

    # ``LatestOnlyQueue`` owns the lifecycle of the underlying queue, so it
    # should keep the unfinished task counter aligned with the actual number of
    # buffered items (0 or 1). Accessing the protected attribute keeps the test
    # narrowly focused on the regression we are guarding against.
    assert queue._queue.unfinished_tasks == 1  # type: ignore[attr-defined]

    queue.get_nowait()

    assert queue._queue.unfinished_tasks == 0  # type: ignore[attr-defined]


def test_timing_accumulator_respects_limits_and_updates_metrics() -> None:
    accumulator = TimingAccumulator(
        target_dt=0.01, max_steps_per_frame=5, max_frame_time=0.05
    )

    # Simulate a long frame; the accumulator should clamp to max_frame_time
    accumulator.last_time -= 0.12
    steps = accumulator.update()
    assert steps == 5
    assert accumulator.steps_taken == 5
    assert accumulator.total_sim_time == pytest.approx(0.05)
    assert accumulator.total_real_time == pytest.approx(0.05)
    assert accumulator.get_realtime_factor() == pytest.approx(1.0)

    # With half a timestep of real time only accumulation should change
    accumulator.last_time -= accumulator.target_dt * 0.5
    steps = accumulator.update()
    assert steps == 0
    assert accumulator.get_interpolation_alpha() == pytest.approx(0.5, abs=1e-3)
    assert accumulator.frames_processed == 2
    assert accumulator.total_real_time > accumulator.total_sim_time
    assert accumulator.get_realtime_factor() < 1.0

    accumulator.reset()
    assert accumulator.steps_taken == 0
    assert accumulator.total_real_time == pytest.approx(0.0)
    assert accumulator.total_sim_time == pytest.approx(0.0)


def test_state_snapshot_buffer_capacity_and_isolation() -> None:
    buffer = StateSnapshotBuffer(maxlen=3)

    buffer.append({"frame": 0})
    buffer.extend([{"frame": 1}, {"frame": 2}])
    assert buffer.capacity == 3
    assert len(buffer) == 3
    assert buffer.latest() == {"frame": 2}
    assert buffer.to_list() == [{"frame": 0}, {"frame": 1}, {"frame": 2}]

    buffer.append({"frame": 3})
    assert len(buffer) == 3
    assert buffer.to_list() == [{"frame": 1}, {"frame": 2}, {"frame": 3}]
    assert buffer.latest() == {"frame": 3}

    copy_snapshot = buffer.to_list()
    copy_snapshot.append({"frame": 99})
    assert buffer.to_list() == [{"frame": 1}, {"frame": 2}, {"frame": 3}]

    buffer.clear()
    assert len(buffer) == 0
    assert buffer.latest() is None


@pytest.mark.parametrize("invalid_size", [0, -1])
def test_state_snapshot_buffer_rejects_non_positive_capacity(invalid_size: int) -> None:
    with pytest.raises(ValueError):
        StateSnapshotBuffer(maxlen=invalid_size)
