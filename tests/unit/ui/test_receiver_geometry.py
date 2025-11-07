from __future__ import annotations

import copy
import math
from typing import Any

import pytest

from src.ui.main_window_pkg.signals_router import SignalsRouter


class _DummySignal:
    """Collects emitted arguments for inspection in tests."""

    def __init__(self) -> None:
        self.emitted: list[tuple[Any, ...]] = []

    def emit(self, *args: Any) -> None:  # pragma: no cover - exercised indirectly
        self.emitted.append(tuple(args))


class _DummyStateBus:
    def __init__(self) -> None:
        self.set_receiver_volume = _DummySignal()


class _DummySimulationManager:
    def __init__(self) -> None:
        self.state_bus = _DummyStateBus()


class _GeometrySettingsManager:
    def __init__(self) -> None:
        self._categories: dict[str, dict[str, Any]] = {
            "pneumatic": {
                "volume_mode": "GEOMETRIC",
                "receiver_volume": 0.02,
                "receiver_diameter": 0.45,
                "receiver_length": 1.1,
            }
        }

    def get_category(self, name: str) -> dict[str, Any]:
        payload = self._categories.get(name, {})
        return copy.deepcopy(payload)

    def get(self, path: str, default: Any = None) -> Any:
        return copy.deepcopy(self._categories.get(path, default))


class _DummyWindow:
    def __init__(self) -> None:
        self.settings_updates: list[tuple[str, dict[str, Any]]] = []
        self.settings_manager = _GeometrySettingsManager()
        self.simulation_manager = _DummySimulationManager()

    def _apply_settings_update(self, category: str, payload: dict[str, Any]) -> None:
        self.settings_updates.append((category, copy.deepcopy(payload)))
        if category == "pneumatic":
            self.settings_manager._categories.setdefault("pneumatic", {}).update(
                payload
            )


def test_geometry_recalculation_updates_receiver_volume(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Diameter/length edits in geometric mode must update the state bus."""

    window = _DummyWindow()
    dispatched: list[str] = []

    monkeypatch.setattr(
        SignalsRouter,
        "_push_pneumatic_state",
        lambda w: dispatched.append("pneumatic") if w is window else None,
    )

    payload = {
        "receiver_diameter": 0.5,
        "receiver_length": 2.0,
        "volume_mode": "geometric",
    }

    SignalsRouter.handle_pneumatic_settings_changed(window, payload)

    assert dispatched == ["pneumatic"], "Pneumatic payload should be broadcast to QML"

    assert window.settings_updates, "Settings update must be recorded"
    category, updates = window.settings_updates[-1]
    assert category == "pneumatic"

    expected_volume = (
        math.pi * (payload["receiver_diameter"] / 2.0) ** 2 * payload["receiver_length"]
    )
    assert updates["receiver_volume"] == pytest.approx(expected_volume)

    emissions = window.simulation_manager.state_bus.set_receiver_volume.emitted
    assert emissions, "State bus should receive a receiver volume update"
    volume, mode = emissions[-1]
    assert volume == pytest.approx(expected_volume)
    assert mode == "GEOMETRIC"


def test_recalculation_respects_persisted_geometric_mode(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Persisted geometric mode must trigger GEOMETRIC bus updates even without mode key."""

    window = _DummyWindow()
    dispatched: list[str] = []

    monkeypatch.setattr(
        SignalsRouter,
        "_push_pneumatic_state",
        lambda w: dispatched.append("pneumatic") if w is window else None,
    )

    payload = {
        "receiver_diameter": 0.42,
        "receiver_length": 1.8,
    }

    SignalsRouter.handle_pneumatic_settings_changed(window, payload)

    assert dispatched == ["pneumatic"], "Pneumatic payload should be broadcast to QML"

    expected_volume = (
        math.pi * (payload["receiver_diameter"] / 2.0) ** 2 * payload["receiver_length"]
    )

    category, updates = window.settings_updates[-1]
    assert category == "pneumatic"
    assert updates["receiver_volume"] == pytest.approx(expected_volume)

    volume, mode = window.simulation_manager.state_bus.set_receiver_volume.emitted[-1]
    assert volume == pytest.approx(expected_volume)
    assert mode == "GEOMETRIC"
