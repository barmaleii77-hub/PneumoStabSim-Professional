"""System-level checks for the 3-DOF physics integrator."""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np
import pytest

from config.constants import (
    get_physics_integrator_constants,
    get_physics_suspension_constants,
    get_simulation_settings,
)
from physics.integrator import (
    create_default_rigid_body,
    step_dynamics,
)
from physics.odes import (
    RigidBody3DOF,
    create_initial_conditions,
    f_rhs,
)

pytestmark = pytest.mark.system

_SPRING_STIFFNESS = get_physics_suspension_constants()["spring_constant"]
_SIMULATION_SETTINGS = get_simulation_settings()
_DT_PHYSICS = float(_SIMULATION_SETTINGS["physics_dt"])
_TIME_HORIZON = float(_SIMULATION_SETTINGS["max_frame_time"]) * 10.0
_INTEGRATION_STEPS = max(1, int(round(_TIME_HORIZON / _DT_PHYSICS)))
_INTEGRATOR_SETTINGS = get_physics_integrator_constants()
_PRIMARY_METHOD = str(_INTEGRATOR_SETTINGS["solver"]["primary_method"])


def _suspension_displacements(
    params: RigidBody3DOF, state: np.ndarray
) -> Iterable[float]:
    """Return vertical displacements of all suspension points."""
    y, roll, pitch, *_ = state
    for x_pos, z_pos in params.attachment_points.values():
        yield y + x_pos * roll + z_pos * pitch


def _total_mechanical_energy(params: RigidBody3DOF, state: np.ndarray) -> float:
    """Approximate total mechanical energy of the rigid body state."""
    y, roll, pitch, dy, droll, dpitch = state

    kinetic = 0.5 * params.M * dy**2
    kinetic += 0.5 * params.Iz * droll**2
    kinetic += 0.5 * params.Ix * dpitch**2

    gravitational = params.M * params.g * y

    suspension = sum(
        0.5 * _SPRING_STIFFNESS * disp**2
        for disp in _suspension_displacements(params, state)
    )

    return kinetic + gravitational + suspension


@pytest.fixture(scope="module")
def default_params() -> RigidBody3DOF:
    return create_default_rigid_body()


@pytest.fixture(scope="module")
def nominal_state() -> np.ndarray:
    return create_initial_conditions(heave=0.01, roll=0.005, pitch=0.002)


def test_step_dynamics_stable_response(
    default_params: RigidBody3DOF,
    nominal_state: np.ndarray,
    capsys: pytest.CaptureFixture[str],
) -> None:
    """Integrator should remain stable for small perturbations."""
    dt = _DT_PHYSICS
    t = 0.0
    y = nominal_state.copy()

    max_energy = 0.0
    max_angle = 0.0

    initial_energy = _total_mechanical_energy(default_params, y)

    for _ in range(_INTEGRATION_STEPS):
        result = step_dynamics(
            y,
            t,
            dt,
            default_params,
            system=None,
            gas=None,
            method=_PRIMARY_METHOD,
        )
        assert result.success, result.message
        assert np.all(np.isfinite(result.y_final)), "State vector must remain finite"
        assert result.n_evaluations > 0
        assert result.t_final > t

        y = result.y_final
        t = result.t_final

        max_energy = max(
            max_energy,
            _total_mechanical_energy(default_params, y),
        )
        max_angle = max(max_angle, float(np.max(np.abs(y[1:3]))))

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

    expected_time = _INTEGRATION_STEPS * dt
    assert math.isclose(t, expected_time, rel_tol=0.0, abs_tol=1e-12)
    assert max_energy < initial_energy * 10.0, (
        "Energy growth indicates unstable integration"
    )
    assert max_angle < default_params.angle_limit, (
        "Angular deviation should stay within configured limits"
    )

    accelerations = f_rhs(t, y, default_params, None, None)[3:]
    assert np.linalg.norm(accelerations) < default_params.g, (
        "Accelerations should remain bounded"
    )


def test_step_dynamics_invalid_method(
    default_params: RigidBody3DOF, nominal_state: np.ndarray
) -> None:
    """Unknown integration methods must report a failure without crashing."""
    result = step_dynamics(
        nominal_state,
        t0=0.0,
        dt=0.01,
        params=default_params,
        system=None,
        gas=None,
        method="NotAMethod",
    )

    assert not result.success
    assert "failed" in result.message.lower()
    assert result.method_used == "FAILED"


def test_step_dynamics_invalid_inertia_matrix(
    nominal_state: np.ndarray,
) -> None:
    """Degenerate inertia matrices should surface integration errors."""
    bad_params = RigidBody3DOF(M=1500.0, Ix=0.0, Iz=3000.0)

    with pytest.warns(RuntimeWarning):
        result = step_dynamics(
            nominal_state,
            t0=0.0,
            dt=0.01,
            params=bad_params,
            system=None,
            gas=None,
            method=_PRIMARY_METHOD,
        )

    assert not result.success
    assert "failed" in result.message.lower()
    assert result.method_used == "FAILED"
