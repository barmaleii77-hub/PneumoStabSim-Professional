"""High-level reliability tests for the pneumatic gas network."""

from __future__ import annotations

import math
from typing import Dict

import pytest

from src.common.units import PA_ATM, R_AIR, T_AMBIENT
from src.pneumo.cylinder import CylinderSpec
from src.pneumo.enums import (
    CheckValveKind,
    Line,
    ReceiverVolumeMode,
    Wheel,
)
from src.pneumo.gas_state import (
    create_line_gas_state,
    create_tank_gas_state,
    p_from_mTV,
)
from src.pneumo.geometry import CylinderGeom, LeverGeom
from src.pneumo.network import GasNetwork
from src.pneumo.receiver import ReceiverSpec, ReceiverState
from src.pneumo.system import PneumaticSystem, create_standard_diagonal_system
from src.pneumo.valves import CheckValve


def _build_default_system_and_network() -> tuple[PneumaticSystem, GasNetwork]:
    """Construct a pneumatic system and matching gas network for tests."""

    lever_geom = LeverGeom(
        L_lever=0.75,
        rod_joint_frac=0.45,
        d_frame_to_lever_hinge=0.42,
    )
    cylinder_geom = CylinderGeom(
        D_in_front=0.11,
        D_in_rear=0.11,
        D_out_front=0.13,
        D_out_rear=0.13,
        L_inner=0.46,
        t_piston=0.025,
        D_rod=0.035,
        link_rod_diameters_front_rear=True,
        L_dead_head=0.018,
        L_dead_rod=0.02,
        residual_frac_min=0.01,
        Y_tail=0.45,
        Z_axle=0.55,
    )

    cylinder_specs = {
        Wheel.LP: CylinderSpec(cylinder_geom, True, lever_geom),
        Wheel.PP: CylinderSpec(cylinder_geom, True, lever_geom),
        Wheel.LZ: CylinderSpec(cylinder_geom, False, lever_geom),
        Wheel.PZ: CylinderSpec(cylinder_geom, False, lever_geom),
    }

    def _valve(kind: CheckValveKind) -> CheckValve:
        return CheckValve(kind=kind, delta_open=5_000.0, d_eq=0.008)

    line_configs = {
        line: {
            "cv_atmo": _valve(CheckValveKind.ATMO_TO_LINE),
            "cv_tank": _valve(CheckValveKind.LINE_TO_TANK),
            "p_line": PA_ATM,
        }
        for line in (Line.A1, Line.B1, Line.A2, Line.B2)
    }

    receiver_state = ReceiverState(
        spec=ReceiverSpec(V_min=0.0018, V_max=0.0045),
        V=0.003,
        p=PA_ATM,
        T=T_AMBIENT,
        mode=ReceiverVolumeMode.ADIABATIC_RECALC,
    )

    system = create_standard_diagonal_system(
        cylinder_specs=cylinder_specs,
        line_configs=line_configs,
        receiver=receiver_state,
        master_isolation_open=False,
    )
    system.update_system_from_lever_angles({wheel: 0.0 for wheel in Wheel})

    volumes = {
        line: info["total_volume"] for line, info in system.get_line_volumes().items()
    }
    line_states = {
        line: create_line_gas_state(line, PA_ATM, T_AMBIENT, volume)
        for line, volume in volumes.items()
    }
    tank_state = create_tank_gas_state(
        V_initial=0.0035,
        p_initial=PA_ATM,
        T_initial=T_AMBIENT,
        mode=ReceiverVolumeMode.ADIABATIC_RECALC,
    )

    gas_network = GasNetwork(
        lines=line_states,
        tank=tank_state,
        system_ref=system,
        master_isolation_open=False,
    )
    return system, gas_network


def _recompute_mass(pressure: float, temperature: float, volume: float) -> float:
    """Return the mass that yields *pressure* at *temperature* and *volume*."""

    return pressure * volume / (R_AIR * temperature)


@pytest.fixture()
def default_network():
    return _build_default_system_and_network()


@pytest.mark.parametrize("delta_pressure", [8_000.0, 12_000.0])
def test_apply_valves_replenishes_low_pressure_lines(default_network, delta_pressure):
    """Atmospheric check valves must add mass when the line pressure drops."""

    _system, gas_network = default_network
    dt = 0.05

    line = Line.A1
    line_state = gas_network.lines[line]

    target_pressure = PA_ATM - delta_pressure
    assert target_pressure > 0

    line_state.p = target_pressure
    line_state.m = _recompute_mass(target_pressure, line_state.T, line_state.V_curr)
    depleted_mass = line_state.m

    flows = gas_network.apply_valves_and_flows(dt)
    assert line_state.m > depleted_mass
    assert flows["lines"][line]["flow_atmo"] > 0.0
    assert line_state.p > target_pressure


@pytest.mark.parametrize("excess_pressure", [12_000.0, 20_000.0])
def test_apply_valves_transfers_mass_to_tank(default_network, excess_pressure):
    """Line over-pressure must push mass into the receiver tank safely."""

    _system, gas_network = default_network
    dt = 0.05

    line = Line.A2
    line_state = gas_network.lines[line]

    gas_network.tank.p = PA_ATM - 3_000.0
    gas_network.tank.m = _recompute_mass(
        gas_network.tank.p, gas_network.tank.T, gas_network.tank.V
    )
    tank_mass_before = gas_network.tank.m

    target_pressure = PA_ATM + excess_pressure
    line_state.p = target_pressure
    line_state.m = _recompute_mass(target_pressure, line_state.T, line_state.V_curr)
    line_mass_before = line_state.m

    flows = gas_network.apply_valves_and_flows(dt)

    assert gas_network.tank.m > tank_mass_before
    assert line_state.m < line_mass_before
    assert line_state.m > 0.0
    assert flows["lines"][line]["flow_tank"] > 0.0


@pytest.mark.parametrize("tank_multiplier", [1.6, 2.1])
def test_relief_valves_protect_tank_overpressure(default_network, tank_multiplier):
    """Receiver relief valves must vent mass when the tank is over pressurised."""

    _system, gas_network = default_network
    dt = 0.05

    gas_network.tank.p = PA_ATM * tank_multiplier
    gas_network.tank.m = _recompute_mass(
        gas_network.tank.p, gas_network.tank.T, gas_network.tank.V
    )
    tank_mass_before = gas_network.tank.m

    flows = gas_network.apply_valves_and_flows(dt)

    assert gas_network.tank.m < tank_mass_before
    assert any(value > 0.0 for value in flows["relief"].values())


def test_master_isolation_equalises_pressures(default_network):
    """When enabled the master isolation valve must equalise all line states."""

    _system, gas_network = default_network
    gas_network.master_isolation_open = True

    volumes: Dict[Line, float] = {
        line: state.V_curr for line, state in gas_network.lines.items()
    }

    # Perturb each line with different masses and temperatures to ensure the
    # equalisation logic normalises all degrees of freedom.
    for idx, (line, state) in enumerate(gas_network.lines.items(), start=1):
        factor = 0.5 + 0.2 * idx
        state.m = max(1e-5, state.m * factor)
        state.T = T_AMBIENT + 5.0 * idx
        state.p = p_from_mTV(state.m, state.T, state.V_curr)
        state.V_curr = volumes[line]

    total_mass = sum(state.m for state in gas_network.lines.values())
    total_volume = sum(volumes.values())
    average_temperature = (
        sum(state.m * state.T for state in gas_network.lines.values()) / total_mass
    )
    expected_pressure = p_from_mTV(total_mass, average_temperature, total_volume)

    gas_network.enforce_master_isolation()

    for line, state in gas_network.lines.items():
        assert math.isclose(state.p, expected_pressure, rel_tol=1e-6)
        assert math.isclose(state.T, average_temperature, rel_tol=1e-6)
        expected_mass = total_mass * (volumes[line] / total_volume)
        assert math.isclose(state.m, expected_mass, rel_tol=1e-6)
        assert state.V_curr == volumes[line]
