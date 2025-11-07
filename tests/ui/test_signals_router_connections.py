"""Unit tests for the SignalsRouter connection policies."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any, Callable

import pytest

from src.ui.main_window_pkg.signals_router import SignalsRouter, Qt


class _RecordingSignal:
    """Lightweight stand-in for Qt signals recording ``connect`` calls."""

    def __init__(self) -> None:
        self.calls: list[tuple[Callable[..., Any], Any]] = []

    def connect(self, handler: Callable[..., Any], connection_type: Any = None) -> None:
        self.calls.append((handler, connection_type))


class _RecordingBus:
    def __init__(self) -> None:
        self.state_ready = _RecordingSignal()
        self.physics_error = _RecordingSignal()


@pytest.fixture()
def fake_window() -> Any:
    def _dummy_handler(*_args: Any, **_kwargs: Any) -> None:
        return None

    bus = _RecordingBus()
    simulation_manager = SimpleNamespace(state_bus=bus)

    window = SimpleNamespace(
        simulation_manager=simulation_manager,
        _on_state_update=_dummy_handler,
        _on_physics_error=_dummy_handler,
    )
    return window


def test_simulation_signals_use_queued_connection(fake_window: Any) -> None:
    """All cross-thread simulation bus links must request queued delivery."""

    SignalsRouter._connect_simulation_signals(fake_window)

    for signal in (
        fake_window.simulation_manager.state_bus.state_ready,
        fake_window.simulation_manager.state_bus.physics_error,
    ):
        assert signal.calls, "Signal was not connected"
        for handler, connection_type in signal.calls:
            assert callable(handler)
            assert connection_type == Qt.QueuedConnection
