"""Regression tests for diagonal cylinder linking logic."""

from __future__ import annotations

import math

import pytest

from src.common.units import PA_ATM, R_AIR, T_AMBIENT
from src.pneumo.enums import Line, Port, ReceiverVolumeMode, ThermoMode, Wheel
from src.pneumo.gas_state import LineGasState, TankGasState, create_line_gas_state, p_from_mTV
from src.pneumo.line import PneumoLine
from src.pneumo.network import GasNetwork
from src.pneumo.receiver import ReceiverSpec, ReceiverState
from src.pneumo.system import PneumaticSystem
from src.pneumo.valves import CheckValve


class _StubCylinder:
    """Minimal cylinder stub exposing volume helpers used by the network."""

    def __init__(self, head: float, rod: float) -> None:
        self.head = head
        self.rod = rod

    def vol_head(self) -> float:
        return self.head

    def vol_rod(self) -> float:
        return self.rod


def _make_valve() -> CheckValve:
    return CheckValve(delta_open=10.0, d_eq=0.01, p_upstream=PA_ATM, p_downstream=PA_ATM)


def _build_system(initial_volumes: dict[Line, tuple[float, float]]) -> PneumaticSystem:
    cylinders = {
        Wheel.LP: _StubCylinder(head=0.42, rod=0.31),
        Wheel.PP: _StubCylinder(head=0.41, rod=0.32),
        Wheel.LZ: _StubCylinder(head=0.55, rod=0.29),
        Wheel.PZ: _StubCylinder(head=0.53, rod=0.28),
    }

    lines = {
        Line.A1: PneumoLine(
            name=Line.A1,
            endpoints=((Wheel.LP, Port.ROD), (Wheel.PZ, Port.HEAD)),
            cv_atmo=_make_valve(),
            cv_tank=_make_valve(),
            p_line=PA_ATM,
        ),
        Line.B1: PneumoLine(
            name=Line.B1,
            endpoints=((Wheel.LP, Port.HEAD), (Wheel.PZ, Port.ROD)),
            cv_atmo=_make_valve(),
            cv_tank=_make_valve(),
            p_line=PA_ATM,
        ),
        Line.A2: PneumoLine(
            name=Line.A2,
            endpoints=((Wheel.PP, Port.ROD), (Wheel.LZ, Port.HEAD)),
            cv_atmo=_make_valve(),
            cv_tank=_make_valve(),
            p_line=PA_ATM,
        ),
        Line.B2: PneumoLine(
            name=Line.B2,
            endpoints=((Wheel.PP, Port.HEAD), (Wheel.LZ, Port.ROD)),
            cv_atmo=_make_valve(),
            cv_tank=_make_valve(),
            p_line=PA_ATM,
        ),
    }

    receiver = ReceiverState(
        spec=ReceiverSpec(V_min=0.01, V_max=0.2),
        V=0.05,
        p=PA_ATM,
        T=T_AMBIENT,
        mode=ReceiverVolumeMode.NO_RECALC,
    )

    system = PneumaticSystem(cylinders=cylinders, lines=lines, receiver=receiver)

    # Sanity check: ensure initial volumes match expectations when provided.
    volumes = system.get_line_volumes()
    for line_name, (head_volume, rod_volume) in initial_volumes.items():
        assert math.isclose(
            volumes[line_name]["total_volume"], head_volume + rod_volume, rel_tol=1e-9
        )

    return system


def test_diagonal_line_total_volume_matches_sum() -> None:
    system = _build_system(
        {
            Line.A1: (0.53, 0.31),
            Line.B1: (0.42, 0.28),
            Line.A2: (0.55, 0.32),
            Line.B2: (0.41, 0.29),
        }
    )

    volumes = system.get_line_volumes()

    assert volumes[Line.A1]["endpoints"] == [
        {"wheel": Wheel.LP.value, "port": Port.ROD.value, "volume": pytest.approx(0.31)},
        {"wheel": Wheel.PZ.value, "port": Port.HEAD.value, "volume": pytest.approx(0.53)},
    ]
    assert volumes[Line.A1]["total_volume"] == pytest.approx(0.31 + 0.53)
    assert volumes[Line.B2]["total_volume"] == pytest.approx(0.41 + 0.29)


def test_gas_network_volume_update_uses_diagonal_totals() -> None:
    system = _build_system(
        {
            Line.A1: (0.53, 0.31),
            Line.B1: (0.42, 0.28),
            Line.A2: (0.55, 0.32),
            Line.B2: (0.41, 0.29),
        }
    )

    # Initialise line gas states with the current combined volumes.
    line_states: dict[Line, LineGasState] = {}
    for line_name, data in system.get_line_volumes().items():
        V_initial = data["total_volume"]
        state = create_line_gas_state(
            name=line_name,
            p_initial=PA_ATM,
            T_initial=T_AMBIENT,
            V_initial=V_initial,
        )
        line_states[line_name] = state

    tank_mass = PA_ATM * 0.05 / (R_AIR * T_AMBIENT)
    tank_state = TankGasState(
        V=0.05, p=PA_ATM, T=T_AMBIENT, m=tank_mass, mode=ReceiverVolumeMode.NO_RECALC
    )
    network = GasNetwork(lines=line_states, tank=tank_state, system_ref=system)

    # Modify cylinder volumes to emulate diagonal transfer.
    system.cylinders[Wheel.LP].rod = 0.29
    system.cylinders[Wheel.PZ].head = 0.56
    system.cylinders[Wheel.PP].head = 0.38
    system.cylinders[Wheel.LZ].rod = 0.33

    previous_volumes = {name: state.V_curr for name, state in line_states.items()}

    network.update_pressures_due_to_volume(ThermoMode.ISOTHERMAL)

    for line_name, state in line_states.items():
        combined_volume = system.get_line_volumes()[line_name]["total_volume"]
        assert state.V_curr == pytest.approx(combined_volume)
        assert state.V_prev == pytest.approx(previous_volumes[line_name])
        expected_pressure = p_from_mTV(state.m, state.T, state.V_curr)
        assert state.p == pytest.approx(expected_pressure)
