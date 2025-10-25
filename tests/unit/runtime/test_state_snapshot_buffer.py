from __future__ import annotations

import importlib.util
import pathlib
from types import SimpleNamespace
from typing import Any

import pytest


def _load_state_snapshot_buffer() -> Any:
    module_path = pathlib.Path(__file__).resolve().parents[3] / "src/runtime/sync.py"
    spec = importlib.util.spec_from_file_location("_runtime_sync_test", module_path)
    if spec is None or spec.loader is None:  # pragma: no cover - safety
        raise RuntimeError("Failed to load runtime.sync module for testing")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.StateSnapshotBuffer


StateSnapshotBuffer = _load_state_snapshot_buffer()


def _create_snapshot(step: int) -> SimpleNamespace:
    return SimpleNamespace(step_number=step, simulation_time=step * 0.01)


def test_snapshot_buffer_keeps_most_recent_entries() -> None:
    buffer = StateSnapshotBuffer(maxlen=3)

    for step in range(5):
        buffer.append(_create_snapshot(step))

    snapshots = buffer.to_list()

    assert len(snapshots) == 3
    assert [snap.step_number for snap in snapshots] == [2, 3, 4]
    latest = buffer.latest()
    assert latest is not None
    assert latest.step_number == 4


def test_snapshot_buffer_clear_and_length() -> None:
    buffer = StateSnapshotBuffer(maxlen=2)
    buffer.append(_create_snapshot(1))
    buffer.append(_create_snapshot(2))

    assert len(buffer) == 2

    buffer.clear()

    assert len(buffer) == 0
    assert buffer.latest() is None


def test_snapshot_buffer_to_list_returns_copy() -> None:
    buffer = StateSnapshotBuffer(maxlen=2)
    buffer.append(_create_snapshot(1))

    snapshots = buffer.to_list()
    snapshots.clear()

    # Clearing the returned list should not affect the buffer contents
    assert len(buffer) == 1


def test_snapshot_buffer_rejects_non_positive_capacity() -> None:
    with pytest.raises(ValueError):
        StateSnapshotBuffer(maxlen=0)
