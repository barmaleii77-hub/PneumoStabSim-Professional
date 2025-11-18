from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest

from src.common.errors import ModelConfigError, ThermoError
from src.runtime.sim_loop import PhysicsWorker
from src.runtime.state import TankState
from src.pneumo.enums import ReceiverVolumeMode
from src.pneumo.gas_state import R_AIR, TankGasState
from src.pneumo.receiver import ReceiverSpec, ReceiverState, ReceiverVolumeUpdate


class _DummySignal:
    def __init__(self) -> None:
        self.emitted: list[tuple] = []

    def emit(self, *args) -> None:  # pragma: no cover - behaviour exercised indirectly
        self.emitted.append(tuple(args))


class _StubPneumoTank:
    def __init__(self, volume: float) -> None:
        self.V = volume
        self.mode = ReceiverVolumeMode.NO_RECALC
        self.history: list[tuple[float, ReceiverVolumeMode]] = []

    def apply_instant_volume_change(self, new_volume: float) -> None:
        self.history.append((new_volume, self.mode))
        self.V = new_volume


def _make_worker() -> PhysicsWorker:
    worker = PhysicsWorker.__new__(PhysicsWorker)
    worker.logger = logging.getLogger("test.physics_worker")
    worker.error_occurred = _DummySignal()
    worker.receiver_volume_changed = _DummySignal()  # type: ignore[attr-defined]
    worker.receiver_volume = 0.02
    worker.receiver_volume_mode = "MANUAL"
    worker._latest_tank_state = TankState(
        pressure=101325.0,
        temperature=293.15,
        mass=0.0,
        volume=0.02,
    )
    return worker


def test_set_receiver_volume_updates_pneumatic_and_gas_network(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """PhysicsWorker should update pneumatic receiver and gas tank immediately."""

    worker = _make_worker()
    caplog.set_level(logging.INFO, logger="test.physics_worker")

    receiver_spec = ReceiverSpec(V_min=0.01, V_max=0.5)
    receiver_state = ReceiverState(
        spec=receiver_spec,
        V=0.02,
        p=101325.0,
        T=293.15,
        mode=ReceiverVolumeMode.NO_RECALC,
    )
    pneumo_tank = _StubPneumoTank(0.02)
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

    new_volume = 0.03
    expected_pressure = receiver_state.p * ((receiver_state.V / new_volume) ** 1.4)
    expected_temperature = receiver_state.T * ((receiver_state.V / new_volume) ** 0.4)

    update = worker.set_receiver_volume(new_volume, ReceiverVolumeMode.ADIABATIC_RECALC)

    assert isinstance(update, ReceiverVolumeUpdate)
    assert update.volume == pytest.approx(new_volume)
    assert update.mode is ReceiverVolumeMode.ADIABATIC_RECALC
    assert update.pressure == pytest.approx(expected_pressure)
    assert update.temperature == pytest.approx(expected_temperature)

    pneumo_tank = worker._test_pneumo_tank  # type: ignore[attr-defined]

    assert worker.receiver_volume == pytest.approx(new_volume)
    assert worker.receiver_volume_mode == ReceiverVolumeMode.ADIABATIC_RECALC.value
    assert worker.pneumatic_system.receiver.mode is ReceiverVolumeMode.ADIABATIC_RECALC
    assert worker.pneumatic_system.receiver.V == pytest.approx(new_volume)
    assert worker.pneumatic_system.receiver.p == pytest.approx(expected_pressure)
    assert worker.pneumatic_system.receiver.T == pytest.approx(expected_temperature)
    assert pneumo_tank.V == pytest.approx(new_volume)
    assert pneumo_tank.history, "Pneumatic tank should record volume updates"
    recorded_volume, recorded_mode = pneumo_tank.history[-1]
    assert recorded_volume == pytest.approx(new_volume)
    assert recorded_mode is ReceiverVolumeMode.ADIABATIC_RECALC

    assert worker.gas_network.tank.V == pytest.approx(new_volume)
    assert worker._latest_tank_state.volume == pytest.approx(new_volume)
    assert worker._latest_tank_state.pressure == pytest.approx(
        worker.gas_network.tank.p
    )
    assert worker._latest_tank_state.mass == pytest.approx(worker.gas_network.tank.m)
    assert worker._latest_tank_state.temperature == pytest.approx(
        worker.gas_network.tank.T
    )

    log_record = next(
        (
            record
            for record in caplog.records
            if "Receiver volume updated" in record.message
        ),
        None,
    )
    assert log_record is not None, "Receiver volume update log entry is missing"
    log_context = getattr(log_record, "context", {})
    assert log_context["volume_m3"] == pytest.approx(new_volume)
    assert log_context["mode"] == ReceiverVolumeMode.ADIABATIC_RECALC.value
    assert log_context["receiver_pressure_pa"] == pytest.approx(expected_pressure)
    assert log_context["receiver_temperature_k"] == pytest.approx(
        expected_temperature
    )
    assert log_context["pneumatic_tank_volume_m3"] == pytest.approx(new_volume)
    assert log_context["tank_pressure_pa"] == pytest.approx(worker.gas_network.tank.p)
    assert log_context["tank_mass_kg"] == pytest.approx(worker.gas_network.tank.m)
    assert log_context["tank_temperature_k"] == pytest.approx(
        worker.gas_network.tank.T
    )
    assert worker.error_occurred.emitted == []

    signal_emissions = worker.receiver_volume_changed.emitted
    assert signal_emissions, "Receiver volume changed signal must fire"
    sig_volume, sig_mode, sig_update = signal_emissions[-1]
    assert sig_volume == pytest.approx(new_volume)
    assert sig_mode == ReceiverVolumeMode.ADIABATIC_RECALC.value
    assert isinstance(sig_update, ReceiverVolumeUpdate)
    assert sig_update.volume == pytest.approx(new_volume)
    assert sig_update.mode is ReceiverVolumeMode.ADIABATIC_RECALC
    assert sig_update.pressure == pytest.approx(expected_pressure)
    assert sig_update.temperature == pytest.approx(expected_temperature)


def test_set_receiver_volume_updates_latest_state_without_gas_network(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """PhysicsWorker should still update latest tank state and emit signals."""

    worker = _make_worker()
    worker.gas_network = None
    caplog.set_level(logging.INFO, logger="test.physics_worker")

    receiver_spec = ReceiverSpec(V_min=0.01, V_max=0.5)
    receiver_state = ReceiverState(
        spec=receiver_spec,
        V=0.02,
        p=101325.0,
        T=293.15,
        mode=ReceiverVolumeMode.NO_RECALC,
    )
    pneumo_tank = _StubPneumoTank(0.02)
    worker.pneumatic_system = SimpleNamespace(
        receiver=receiver_state,
        tank=pneumo_tank,
    )

    new_volume = 0.03
    expected_pressure = receiver_state.p * ((receiver_state.V / new_volume) ** 1.4)
    expected_temperature = receiver_state.T * ((receiver_state.V / new_volume) ** 0.4)

    update = worker.set_receiver_volume(new_volume, "geometric")

    assert isinstance(update, ReceiverVolumeUpdate)
    assert update.pressure == pytest.approx(expected_pressure)
    assert update.temperature == pytest.approx(expected_temperature)

    latest_state = worker._latest_tank_state
    assert latest_state.volume == pytest.approx(new_volume)
    assert latest_state.pressure == pytest.approx(expected_pressure)
    assert latest_state.temperature == pytest.approx(expected_temperature)

    log_record = next(
        (
            record
            for record in caplog.records
            if "Receiver volume updated" in record.message
        ),
        None,
    )
    assert log_record is not None, "Receiver volume update log entry is missing"
    log_context = getattr(log_record, "context", {})
    assert log_context["tank_pressure_pa"] == pytest.approx(expected_pressure)
    assert log_context["tank_temperature_k"] == pytest.approx(expected_temperature)
    assert log_context["pneumatic_tank_volume_m3"] == pytest.approx(new_volume)
    assert log_context["receiver_pressure_pa"] == pytest.approx(expected_pressure)
    assert log_context["receiver_temperature_k"] == pytest.approx(
        expected_temperature
    )

    signal_emissions = worker.receiver_volume_changed.emitted
    assert signal_emissions, "Receiver volume changed signal must fire"
    sig_volume, sig_mode, sig_update = signal_emissions[-1]
    assert sig_volume == pytest.approx(new_volume)
    assert sig_mode == ReceiverVolumeMode.ADIABATIC_RECALC.value
    assert isinstance(sig_update, ReceiverVolumeUpdate)
    assert sig_update.pressure == pytest.approx(expected_pressure)
    assert sig_update.temperature == pytest.approx(expected_temperature)


def test_receiver_state_set_volume_returns_updated_state() -> None:
    spec = ReceiverSpec(V_min=0.01, V_max=0.5)
    state = ReceiverState(
        spec=spec,
        V=0.02,
        p=101325.0,
        T=293.15,
        mode=ReceiverVolumeMode.NO_RECALC,
    )

    update = state.set_volume(0.03, mode=ReceiverVolumeMode.ADIABATIC_RECALC)
    assert isinstance(update, ReceiverVolumeUpdate)
    assert update.volume == pytest.approx(0.03)
    assert update.mode is ReceiverVolumeMode.ADIABATIC_RECALC
    assert state.mode is ReceiverVolumeMode.ADIABATIC_RECALC
    assert state.V == pytest.approx(0.03)

    expected_pressure = 101325.0 * ((0.02 / 0.03) ** 1.4)
    expected_temperature = 293.15 * ((0.02 / 0.03) ** 0.4)
    assert update.pressure == pytest.approx(expected_pressure)
    assert update.temperature == pytest.approx(expected_temperature)
    assert state.p == pytest.approx(expected_pressure)
    assert state.T == pytest.approx(expected_temperature)

    second_state = ReceiverState(
        spec=spec,
        V=0.03,
        p=update.pressure,
        T=update.temperature,
        mode=ReceiverVolumeMode.ADIABATIC_RECALC,
    )
    no_recalc_update = second_state.set_volume(0.025, recompute=False)
    assert no_recalc_update.volume == pytest.approx(0.025)
    assert no_recalc_update.pressure == pytest.approx(update.pressure)
    assert no_recalc_update.temperature == pytest.approx(update.temperature)
    assert no_recalc_update.mode is ReceiverVolumeMode.ADIABATIC_RECALC
    assert second_state.mode is ReceiverVolumeMode.ADIABATIC_RECALC
    assert second_state.V == pytest.approx(0.025)


def test_receiver_state_set_volume_does_not_mutate_on_error() -> None:
    spec = ReceiverSpec(V_min=0.01, V_max=0.5)
    state = ReceiverState(
        spec=spec,
        V=0.02,
        p=101325.0,
        T=293.15,
        mode=ReceiverVolumeMode.NO_RECALC,
    )

    with pytest.raises(ModelConfigError):
        state.set_volume(
            0.005, mode=ReceiverVolumeMode.ADIABATIC_RECALC, recompute=False
        )

    assert state.V == pytest.approx(0.02)
    assert state.p == pytest.approx(101325.0)
    assert state.T == pytest.approx(293.15)
    assert state.mode is ReceiverVolumeMode.NO_RECALC


def test_receiver_state_set_volume_recompute_error_restores_mode() -> None:
    spec = ReceiverSpec(V_min=0.01, V_max=0.5)
    state = ReceiverState(
        spec=spec,
        V=0.02,
        p=101325.0,
        T=293.15,
        mode=ReceiverVolumeMode.NO_RECALC,
    )

    with pytest.raises(ThermoError):
        state.set_volume(0.8, mode=ReceiverVolumeMode.ADIABATIC_RECALC)

    assert state.mode is ReceiverVolumeMode.NO_RECALC
    assert state.V == pytest.approx(0.02)
    assert state.p == pytest.approx(101325.0)
    assert state.T == pytest.approx(293.15)
