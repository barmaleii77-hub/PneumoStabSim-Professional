from __future__ import annotations

import logging
from types import SimpleNamespace

import pytest

from src.runtime.sim_loop import PhysicsWorker
from src.runtime.state import TankState
from src.pneumo.enums import ReceiverVolumeMode
from src.pneumo.gas_state import R_AIR, TankGasState
from src.pneumo.receiver import ReceiverSpec, ReceiverState


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
    worker.set_receiver_volume(new_volume, "geometric")

    pneumo_tank = worker._test_pneumo_tank  # type: ignore[attr-defined]

    assert worker.receiver_volume == pytest.approx(new_volume)
    assert worker.receiver_volume_mode == "GEOMETRIC"
    assert worker.pneumatic_system.receiver.mode is ReceiverVolumeMode.ADIABATIC_RECALC
    assert worker.pneumatic_system.receiver.V == pytest.approx(new_volume)
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
    assert log_record.volume_m3 == pytest.approx(new_volume)
    assert log_record.mode == "GEOMETRIC"
    assert log_record.receiver_pressure_pa == pytest.approx(receiver_state.p)
    assert log_record.receiver_temperature_k == pytest.approx(receiver_state.T)
    assert log_record.pneumatic_tank_volume_m3 == pytest.approx(new_volume)
    assert log_record.tank_pressure_pa == pytest.approx(worker.gas_network.tank.p)
    assert log_record.tank_mass_kg == pytest.approx(worker.gas_network.tank.m)
    assert log_record.tank_temperature_k == pytest.approx(worker.gas_network.tank.T)
