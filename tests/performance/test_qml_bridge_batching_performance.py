"""Performance checks for QML bridge batching and flush flows."""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from src.ui.qml_bridge import QMLBridge

REPORT_PATH = Path("reports/tests/render_sync_performance.json")


class _StubTimer:
    def __init__(self) -> None:
        self._active = False

    def isActive(self) -> bool:  # noqa: N802 - Qt naming convention
        return self._active

    def start(self, _interval: int) -> None:
        self._active = True


class _StubRoot:
    def __init__(self) -> None:
        self.properties: dict[str, object] = {}

    def setProperty(self, key: str, value: object) -> None:  # noqa: N802 - Qt naming convention
        self.properties[key] = value


class _StubWindow:
    def __init__(self) -> None:
        self._qml_update_queue: dict[str, dict[str, object]] = {}
        self._qml_root_object = _StubRoot()
        self._qml_flush_timer = _StubTimer()
        self._suppress_qml_feedback = False


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


@pytest.mark.performance
def test_qml_bridge_flushes_batches_quickly() -> None:
    """Queueing and flushing many updates should remain under a tight budget."""

    window = _StubWindow()
    iterations = 500

    start = time.perf_counter()
    for idx in range(iterations):
        QMLBridge.queue_update(
            window,
            "threeD",
            {"flowNetwork": {"lines": {f"line_{idx}": {"pressure": idx * 10.0}}}},
        )
    queue_elapsed = time.perf_counter() - start

    QMLBridge.flush_updates(window)
    flush_elapsed = time.perf_counter() - start

    assert window._qml_update_queue == {}, "Flush should clear the pending queue"
    payload = getattr(window, "_pending_batch_ack", {})
    assert payload, "Batch acknowledgement metadata was not recorded"
    assert payload.get("batch_id") == 1

    average_queue_ms = (queue_elapsed / iterations) * 1000.0
    average_total_ms = (flush_elapsed / iterations) * 1000.0

    _persist_metric(
        "qml_bridge_batching",
        {
            "iterations": iterations,
            "queue_total_seconds": queue_elapsed,
            "average_queue_ms": average_queue_ms,
            "average_total_ms": average_total_ms,
            "budget_ms": 0.25,
        },
    )

    assert average_queue_ms < 0.25, "Queueing overhead should stay under 0.25ms"
    assert average_total_ms < 0.35, "Queue+flush overhead should stay under 0.35ms"
