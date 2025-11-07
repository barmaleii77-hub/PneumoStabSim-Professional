"""High-level reliability tests for the pneumatic gas network."""

from __future__ import annotations

import math

import pytest

from src.common.units import PA_ATM, R_AIR, T_AMBIENT, GAMMA_AIR
from src.pneumo.enums import Line, ThermoMode
from src.pneumo.gas_state import p_from_mTV
from src.pneumo.thermo import adiabatic_constant_pV, adiabatic_p, PolytropicParameters
from tests.helpers.pneumo_network import build_default_system_and_network


def _recompute_mass(pressure: float, temperature: float, volume: float) -> float:
    """Return the mass that yields *pressure* at *temperature* and *volume*."""

    return pressure * volume / (R_AIR * temperature)


@pytest.fixture()
def default_network():
    return build_default_system_and_network()


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


def test_apply_valves_allow_line_to_empty(default_network, monkeypatch):
    """Mass transfer to the tank must deplete a line when sufficient flow occurs."""

    _system, gas_network = default_network
    dt = 1.0

    line = Line.A1
    line_state = gas_network.lines[line]

    monkeypatch.setattr(
        gas_network,
        "_apply_receiver_relief_valves",
        lambda dt, log=None: {"flow_min": 0.0, "flow_stiff": 0.0, "flow_safety": 0.0},
    )

    gas_network.tank.p = PA_ATM - 3_000.0
    gas_network.tank.m = _recompute_mass(
        gas_network.tank.p, gas_network.tank.T, gas_network.tank.V
    )

    line_state.p = PA_ATM + 50_000.0
    line_state.m = _recompute_mass(line_state.p, line_state.T, line_state.V_curr)
    tank_mass_before = gas_network.tank.m

    flows = gas_network.apply_valves_and_flows(dt)

    assert flows["lines"][line]["flow_tank"] > 0.0
    assert line_state.m == pytest.approx(0.0, abs=1e-12)
    assert line_state.p == pytest.approx(0.0, abs=1e-6)
    assert gas_network.tank.m > tank_mass_before


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


def test_line_to_tank_flow_log_reflects_actual_transfer(default_network):
    """Logged line-to-tank flow must honour the available mass in the line."""

    _system, gas_network = default_network
    dt = 1.0

    line = Line.A1
    line_state = gas_network.lines[line]

    gas_network.tank.p = PA_ATM - 15_000.0
    gas_network.tank.m = _recompute_mass(
        gas_network.tank.p, gas_network.tank.T, gas_network.tank.V
    )

    target_pressure = PA_ATM + 80_000.0
    line_state.p = target_pressure
    line_state.m = _recompute_mass(target_pressure, line_state.T, line_state.V_curr)
    mass_before = line_state.m

    flows = gas_network.apply_valves_and_flows(dt)

    actual_transfer = mass_before - line_state.m
    assert actual_transfer > 0.0
    assert flows["lines"][line]["flow_tank"] == pytest.approx(actual_transfer / dt)


def test_master_isolation_equalises_pressures(default_network):
    """When enabled the master isolation valve must equalise all line states."""

    _system, gas_network = default_network
    gas_network.master_isolation_open = True
    gas_network.master_equalization_diameter = 0.0

    volumes: dict[Line, float] = {
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


def test_master_isolation_throttle_limits_equalisation():
    """A finite coupling diameter must equalise diagonals gradually."""

    system, gas_network = build_default_system_and_network(
        master_equalization_diameter=0.001
    )
    gas_network.master_isolation_open = True

    high_lines = (Line.A1, Line.B1)
    low_lines = (Line.A2, Line.B2)

    for line in high_lines:
        state = gas_network.lines[line]
        state.T = T_AMBIENT
        state.p = PA_ATM + 40_000.0
        state.m = _recompute_mass(state.p, state.T, state.V_curr)

    for line in low_lines:
        state = gas_network.lines[line]
        state.T = T_AMBIENT
        state.p = PA_ATM - 30_000.0
        state.m = _recompute_mass(state.p, state.T, state.V_curr)

    initial_delta = gas_network.lines[Line.A1].p - gas_network.lines[Line.A2].p
    assert initial_delta > 0.0

    gas_network.enforce_master_isolation(dt=0.05)

    updated_delta = gas_network.lines[Line.A1].p - gas_network.lines[Line.A2].p
    assert updated_delta > 0.0
    assert updated_delta < initial_delta


def test_polytropic_volume_update_between_limits(default_network, monkeypatch):
    """Polytropic updates must interpolate between isothermal and adiabatic curves."""

    _system, gas_network = default_network
    line = Line.A1
    line_state = gas_network.lines[line]

    initial_volume = line_state.V_curr
    initial_pressure = line_state.p
    initial_temperature = line_state.T
    initial_mass = line_state.m

    ambient_temperature = initial_temperature - 15.0
    gas_network.ambient_temperature = ambient_temperature
    gas_network.polytropic_params = PolytropicParameters(
        heat_transfer_coeff=120.0,
        exchange_area=0.18,
        ambient_temperature=ambient_temperature,
    )

    new_volume = initial_volume * 0.9
    volumes = {
        name: state.V_curr if name != line else new_volume
        for name, state in gas_network.lines.items()
    }
    monkeypatch.setattr(gas_network, "compute_line_volumes", lambda: volumes.copy())

    ambient_limited_pressure = (initial_mass * R_AIR * ambient_temperature) / new_volume
    adiabatic_pressure = adiabatic_p(
        new_volume, adiabatic_constant_pV(initial_pressure, initial_volume)
    )
    adiabatic_temperature = initial_temperature * (
        (initial_volume / new_volume) ** (GAMMA_AIR - 1.0)
    )

    gas_network.update_pressures_due_to_volume(ThermoMode.POLYTROPIC)

    assert ambient_limited_pressure <= line_state.p <= adiabatic_pressure
    assert ambient_temperature < line_state.T < adiabatic_temperature


def test_apply_valves_accounts_for_line_leak(default_network):
    """Line leaks must remove mass proportional to pressure drop and coefficients."""

    _system, gas_network = default_network
    dt = 0.2

    gas_network.leak_coefficient = 1.2e-06
    gas_network.leak_reference_area = 2.5e-04

    line = Line.B1
    line_state = gas_network.lines[line]
    line_state.p = PA_ATM + 60_000.0
    line_state.m = _recompute_mass(line_state.p, line_state.T, line_state.V_curr)

    gas_network.tank.p = line_state.p + 20_000.0
    gas_network.tank.m = _recompute_mass(
        gas_network.tank.p, gas_network.tank.T, gas_network.tank.V
    )

    initial_mass = line_state.m
    pressure_drop = line_state.p - PA_ATM
    expected_loss = min(
        gas_network.leak_coefficient
        * gas_network.leak_reference_area
        * pressure_drop
        * dt,
        initial_mass,
    )

    flows = gas_network.apply_valves_and_flows(dt)

    actual_loss = initial_mass - line_state.m
    assert actual_loss == pytest.approx(expected_loss, rel=1e-9)
    assert flows["lines"][line]["flow_leak"] == pytest.approx(expected_loss / dt)
