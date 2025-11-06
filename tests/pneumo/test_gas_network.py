"""Integration tests for pneumatic gas network thermodynamics and leaks."""

from __future__ import annotations

import pytest

from src.common.units import GAMMA_AIR, PA_ATM, R_AIR
from src.pneumo.enums import Line, ThermoMode
from src.pneumo.thermo import adiabatic_constant_pV, adiabatic_p, PolytropicParameters
from tests.helpers.pneumo_network import build_default_system_and_network


@pytest.fixture()
def gas_network():
    _system, network = build_default_system_and_network()
    return network


def test_polytropic_without_coupling_matches_adiabatic(gas_network, monkeypatch):
    """Polytropic update with zero coupling should reduce to the adiabatic curve."""

    line = Line.A1
    state = gas_network.lines[line]
    initial_volume = state.V_curr
    initial_pressure = state.p
    initial_temperature = state.T

    gas_network.polytropic_params = PolytropicParameters(
        heat_transfer_coeff=0.0,
        exchange_area=0.0,
        ambient_temperature=gas_network.ambient_temperature,
    )

    new_volume = initial_volume * 0.82
    volumes = {name: s.V_curr for name, s in gas_network.lines.items()}
    volumes[line] = new_volume
    monkeypatch.setattr(gas_network, "compute_line_volumes", lambda: volumes.copy())

    gas_network.update_pressures_due_to_volume(ThermoMode.POLYTROPIC)

    expected_pressure = adiabatic_p(
        new_volume, adiabatic_constant_pV(initial_pressure, initial_volume)
    )
    expected_temperature = initial_temperature * (
        (initial_volume / new_volume) ** (GAMMA_AIR - 1.0)
    )

    assert state.p == pytest.approx(expected_pressure, rel=1e-6)
    assert state.T == pytest.approx(expected_temperature, rel=1e-6)


def test_apply_valves_reports_leak_flow(gas_network):
    """Line leaks must report mass loss proportional to pressure drop."""

    dt = 0.1
    gas_network.leak_coefficient = 1.5e-06
    gas_network.leak_reference_area = 2.5e-04

    line = Line.B2
    state = gas_network.lines[line]
    state.p = PA_ATM + 45_000.0
    state.m = state.p * state.V_curr / (R_AIR * state.T)

    gas_network.tank.p = state.p + 5_000.0
    gas_network.tank.m = (
        gas_network.tank.p * gas_network.tank.V / (R_AIR * gas_network.tank.T)
    )

    initial_mass = state.m
    expected_loss = min(
        gas_network.leak_coefficient
        * gas_network.leak_reference_area
        * (state.p - PA_ATM)
        * dt,
        initial_mass,
    )

    flows = gas_network.apply_valves_and_flows(dt)

    actual_loss = initial_mass - state.m
    assert actual_loss == pytest.approx(expected_loss, rel=1e-9)
    assert flows["lines"][line]["flow_leak"] == pytest.approx(
        expected_loss / dt, rel=1e-9
    )
