"""Unit tests for the SignalsRouter connection policies."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any
from collections.abc import Callable

import pytest

from src.ui.main_window_pkg.signals_router import SignalsRouter, Qt
from src.ui.qml_bridge import register_qml_signals


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
        _on_accordion_field_validation_state=_dummy_handler,
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


def test_register_qml_signals_wires_accordion(fake_window: Any) -> None:
    accordion_field = _RecordingSignal()
    accordion_preset = _RecordingSignal()
    accordion_validation = _RecordingSignal()
    geometry_updated = _RecordingSignal()

    qml_root = SimpleNamespace(
        accordionFieldCommitted=accordion_field,
        accordionPresetActivated=accordion_preset,
        accordionValidationChanged=accordion_validation,
        geometrySettingsChanged=geometry_updated,
        batchUpdatesApplied=_RecordingSignal(),
    )

    fake_window._on_qml_batch_ack = lambda *_args, **_kwargs: None
    fake_window._on_accordion_field_committed = lambda *_args, **_kwargs: None
    fake_window._on_accordion_preset_activated = lambda *_args, **_kwargs: None
    fake_window._on_accordion_validation_changed = lambda *_args, **_kwargs: None
    fake_window._on_geometry_settings_changed = lambda *_args, **_kwargs: None

    connected = register_qml_signals(fake_window, qml_root)

    names = {spec.name for spec in connected}
    assert "accordionFieldCommitted" in names
    assert "accordionPresetActivated" in names
    assert "accordionValidationChanged" in names
    assert "geometrySettingsChanged" in names
    assert accordion_field.calls
    assert accordion_preset.calls
    assert accordion_validation.calls
    assert geometry_updated.calls
