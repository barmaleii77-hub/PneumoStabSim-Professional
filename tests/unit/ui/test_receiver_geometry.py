from __future__ import annotations

import copy
import logging
import math
from types import SimpleNamespace
from typing import Any

import pytest

from src.runtime.sim_loop import PhysicsWorker
from src.runtime.state import TankState
from src.pneumo.enums import ReceiverVolumeMode
from src.pneumo.gas_state import R_AIR, TankGasState
from src.pneumo.receiver import ReceiverSpec, ReceiverState
from src.ui.main_window_pkg.signals_router import SignalsRouter


class _DummySignal:
    """Collects emitted arguments for inspection in tests."""

    def __init__(self) -> None:
        self.emitted: list[tuple[Any, ...]] = []

    def emit(self, *args: Any) -> None:  # pragma: no cover - exercised indirectly
        self.emitted.append(tuple(args))


class _DummyStateBus:
    def __init__(self, receiver_signal: Any | None = None) -> None:
        self.set_receiver_volume = receiver_signal or _DummySignal()


class _DummySimulationManager:
    def __init__(self, state_bus: Any | None = None) -> None:
        self.state_bus = state_bus or _DummyStateBus()


class _PanelPneumoTank:
    def __init__(self, volume: float) -> None:
        self.V = volume
        self.mode = ReceiverVolumeMode.NO_RECALC
        self.history: list[tuple[float, ReceiverVolumeMode]] = []

    def apply_instant_volume_change(self, new_volume: float) -> None:
        self.history.append((new_volume, self.mode))
        self.V = new_volume


class _ProxySignal:
    def __init__(self, worker: PhysicsWorker) -> None:
        self.worker = worker
        self.emitted: list[tuple[float, str]] = []

    def emit(self, volume: float, mode: str) -> None:
        self.emitted.append((volume, mode))
        self.worker.set_receiver_volume(volume, mode)


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
    def __init__(self, state_bus: Any | None = None) -> None:
        self.settings_updates: list[tuple[str, dict[str, Any]]] = []
        self.settings_manager = _GeometrySettingsManager()
        self.simulation_manager = _DummySimulationManager(state_bus)

    def _apply_settings_update(self, category: str, payload: dict[str, Any]) -> None:
        self.settings_updates.append((category, copy.deepcopy(payload)))
        if category == "pneumatic":
            self.settings_manager._categories.setdefault("pneumatic", {}).update(
                payload
            )


def _make_physics_worker() -> PhysicsWorker:
    worker = PhysicsWorker.__new__(PhysicsWorker)
    worker.logger = logging.getLogger("test.receiver_geometry.physics")
    worker.error_occurred = _DummySignal()
    worker.receiver_volume = 0.02
    worker.receiver_volume_mode = "MANUAL"
    worker.preserve_user_volume_mode = True
    worker._latest_tank_state = TankState(
        pressure=101325.0,
        temperature=293.15,
        mass=0.0,
        volume=0.02,
    )

    receiver_spec = ReceiverSpec(V_min=0.01, V_max=0.5)
    receiver_state = ReceiverState(
        spec=receiver_spec,
        V=0.02,
        p=101325.0,
        T=293.15,
        mode=ReceiverVolumeMode.NO_RECALC,
    )
    pneumo_tank = _PanelPneumoTank(0.02)
    worker.pneumatic_system = SimpleNamespace(
        receiver=receiver_state,
        tank=pneumo_tank,
    )
    worker._test_pneumo_tank = pneumo_tank  # type: ignore[attr-defined]

    tank_mass = (101325.0 * 0.02) / (R_AIR * 293.15)
    tank_state = TankGasState(
        V=0.02,
        p=101325.0,
        T=293.15,
        m=tank_mass,
        mode=ReceiverVolumeMode.NO_RECALC,
    )
    worker.gas_network = SimpleNamespace(tank=tank_state)

    return worker


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


def test_panel_geometry_update_reaches_physics_worker(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Panel-driven geometry edits must propagate to the physics worker."""

    worker = _make_physics_worker()
    proxy_signal = _ProxySignal(worker)
    state_bus = SimpleNamespace(set_receiver_volume=proxy_signal)
    window = _DummyWindow(state_bus=state_bus)

    monkeypatch.setattr(SignalsRouter, "_push_pneumatic_state", lambda *_: None)

    payload = {
        "receiver_diameter": 0.36,
        "receiver_length": 1.2,
        "volume_mode": "geometric",
    }

    SignalsRouter.handle_pneumatic_settings_changed(window, payload)

    expected_volume = (
        math.pi * (payload["receiver_diameter"] / 2.0) ** 2 * payload["receiver_length"]
    )

    assert proxy_signal.emitted, "Receiver volume signal should reach the worker"
    emitted_volume, emitted_mode = proxy_signal.emitted[-1]
    assert emitted_volume == pytest.approx(expected_volume)
    assert emitted_mode == "GEOMETRIC"

    assert worker.receiver_volume == pytest.approx(expected_volume)
    assert worker.receiver_volume_mode == "GEOMETRIC"

    pneumo_tank = worker._test_pneumo_tank  # type: ignore[attr-defined]
    assert pneumo_tank.V == pytest.approx(expected_volume)
    assert pneumo_tank.history, "Pneumatic tank should track mode updates"
    recorded_volume, recorded_mode = pneumo_tank.history[-1]
    assert recorded_volume == pytest.approx(expected_volume)
    assert recorded_mode is ReceiverVolumeMode.ADIABATIC_RECALC

    assert worker.gas_network.tank.V == pytest.approx(expected_volume)
