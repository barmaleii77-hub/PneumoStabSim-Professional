import math

import numpy as np

from src.physics.odes import RigidBody3DOF, f_rhs
from src.pneumo.enums import Wheel


def test_rigidbody_default_static_loads_match_weight() -> None:
    params = RigidBody3DOF(M=1850.0, Ix=2100.0, Iz=2300.0)

    assert math.isclose(
        params.static_total_load,
        -params.M * params.g,
        rel_tol=1e-9,
        abs_tol=1e-9,
    )

    loads = params.static_wheel_load_map
    assert set(loads.keys()) == set(Wheel)

    per_wheel = params.static_total_load / 4.0
    for value in loads.values():
        assert math.isclose(value, per_wheel, rel_tol=1e-9, abs_tol=1e-9)


def test_f_rhs_rest_state_is_equilibrium() -> None:
    params = RigidBody3DOF(M=1850.0, Ix=2100.0, Iz=2300.0)
    state = np.zeros(6, dtype=float)

    derivatives = f_rhs(0.0, state, params, system=None, gas=None)

    assert np.allclose(derivatives, np.zeros(6), atol=1e-9)
