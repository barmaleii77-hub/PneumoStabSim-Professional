"""System-level checks for the 3-DOF physics integrator."""

from __future__ import annotations

import math
from typing import Iterable

import numpy as np
import pytest

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

_SPRING_STIFFNESS = 50_000.0


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
    dt = 0.001
    t = 0.0
    y = nominal_state.copy()

    max_energy = 0.0
    max_angle = 0.0

    for _ in range(500):
        result = step_dynamics(
            y,
            t,
            dt,
            default_params,
            system=None,
            gas=None,
            method="Radau",
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
        max_angle = max(
            max_angle,
            float(np.max(np.abs(y[1:3]))),
        )

    captured = capsys.readouterr()
    assert captured.out == ""
    assert captured.err == ""

    assert math.isclose(t, 0.5, rel_tol=0.0, abs_tol=1e-12)
    assert max_energy < 5_000.0, "Energy growth indicates unstable integration"
    assert max_angle < math.radians(
        5.0
    ), "Angular deviation should stay within 5 degrees"

    accelerations = f_rhs(t, y, default_params, None, None)[3:]
    assert np.linalg.norm(accelerations) < 5.0, "Accelerations should remain bounded"


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
            method="Radau",
        )

    assert not result.success
    assert "failed" in result.message.lower()
    assert result.method_used == "FAILED"
