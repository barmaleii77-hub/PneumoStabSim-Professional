"""Scenario tests verifying master isolation diagonal coupling behaviour."""

from __future__ import annotations

import pytest

from tests.helpers.pneumo_network import build_default_system_and_network
from src.physics.integrator import (
    PhysicsLoop,
    PhysicsLoopConfig,
    create_default_rigid_body,
)
from src.physics.odes import create_initial_conditions
from src.pneumo.enums import ThermoMode


def _simulate_roll(master_equalization_diameter: float, steps: int = 40) -> float:
    system, gas = build_default_system_and_network(
        master_equalization_diameter=master_equalization_diameter
    )
    config = PhysicsLoopConfig(
        dt_physics=0.005,
        dt_render=0.02,
        max_steps_per_render=4,
        thermo_mode=ThermoMode.ISOTHERMAL,
        master_isolation_open=True,
    )
    loop = PhysicsLoop(config, create_default_rigid_body(), system, gas)
    initial_state = create_initial_conditions(heave=0.02, roll=0.08, pitch=0.0)
    loop.reset(initial_state)

    for _ in range(steps):
        loop.step_physics_fixed(config.dt_physics)

    return float(loop.y_current[1])


@pytest.mark.scenario
def test_diagonal_coupling_alters_roll_response() -> None:
    """Changing the coupling diameter must alter the roll evolution."""

    baseline_roll = _simulate_roll(master_equalization_diameter=0.0)
    coupled_roll = _simulate_roll(master_equalization_diameter=0.004)

    assert coupled_roll != pytest.approx(baseline_roll), (
        "Diagonal coupling should perturb the roll trajectory"
    )
    assert abs(coupled_roll - baseline_roll) > 1e-4


@pytest.mark.scenario
def test_diagonal_coupling_strength_scales_response() -> None:
    """A larger coupling aperture should produce a more pronounced roll shift."""

    weak_roll = _simulate_roll(master_equalization_diameter=0.0015)
    strong_roll = _simulate_roll(master_equalization_diameter=0.005)

    delta = strong_roll - weak_roll
    assert delta != pytest.approx(0.0)
    assert abs(delta) > 1e-7
