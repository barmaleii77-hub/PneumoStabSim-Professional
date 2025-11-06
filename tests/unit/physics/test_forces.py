"""Unit tests for low level force helpers."""

from __future__ import annotations

import math

import numpy as np
import pytest

from config.constants import get_physics_suspension_constants
from src.common.units import PA_ATM
from src.physics.forces import (
    compute_axis_velocity,
    compute_cylinder_force,
    compute_damper_force,
    compute_point_velocity_world,
    compute_spring_force,
    compute_suspension_point_kinematics,
    create_test_suspension_state,
    get_body_angular_velocity_from_euler_rates,
    project_forces_to_vertical_and_moments,
    validate_force_calculation,
)


def test_compute_point_velocity_world_matches_rigid_body_kinematics() -> None:
    r_local = np.array([0.3, -0.1, 0.45])
    body_velocity = np.array([0.0, 0.25, -0.05])
    angular_velocity = np.array([1.2, -0.4, 0.8])

    expected = body_velocity + np.cross(angular_velocity, r_local)
    result = compute_point_velocity_world(r_local, body_velocity, angular_velocity)

    assert np.allclose(result, expected)


def test_compute_axis_velocity_normalises_provided_axis() -> None:
    axis = np.array([0.0, 2.0, 0.0])
    velocity = np.array([0.2, -1.5, 0.3])

    # After normalisation the axis should align with global Y.
    expected = velocity[1]
    result = compute_axis_velocity(axis, velocity)

    assert math.isclose(result, expected)


def test_compute_suspension_point_kinematics_supports_custom_axis() -> None:
    state = np.array([0.02, 0.01, -0.015, -0.03, 0.4, -0.6])
    attachment_points = {"LP": (-0.8, -1.2)}
    axis_map = {"LP": (0.0, 2.0, 2.0)}

    result = compute_suspension_point_kinematics(
        "LP", state, attachment_points, axis_directions=axis_map
    )

    axis = np.array([0.0, 2.0, 2.0]) / math.sqrt(8.0)
    expected_velocity = compute_point_velocity_world(
        np.array([-0.8, 0.0, -1.2]),
        np.array([0.0, state[3], 0.0]),
        np.array([state[5], 0.0, state[4]]),
    )

    assert np.allclose(result["axis_unit_world"], axis)
    assert np.allclose(result["velocity_world"], expected_velocity)
    assert math.isclose(
        result["axial_velocity"],
        compute_axis_velocity(axis, expected_velocity),
    )


def test_compute_suspension_point_kinematics_requires_axis_mapping() -> None:
    state = np.zeros(6)
    attachment_points = {"LP": (0.0, 0.0)}

    with pytest.raises(KeyError):
        compute_suspension_point_kinematics(
            "LP", state, attachment_points, axis_directions={}
        )


def test_compute_suspension_point_kinematics_unknown_wheel_raises() -> None:
    with pytest.raises(ValueError):
        compute_suspension_point_kinematics("XX", np.zeros(6), {}, axis_directions={})


def test_compute_cylinder_force_uses_pressures_and_areas() -> None:
    assert math.isclose(
        compute_cylinder_force(120000.0, 80000.0, 0.0045, 0.0032),
        (120000.0 - PA_ATM) * 0.0045 - (80000.0 - PA_ATM) * 0.0032,
    )


def test_compute_cylinder_force_rejects_invalid_geometry() -> None:
    with pytest.raises(ValueError, match="positive"):
        compute_cylinder_force(120000.0, 80000.0, 0.0, 0.0032)
    with pytest.raises(ValueError, match="non-negative"):
        compute_cylinder_force(120000.0, 80000.0, 0.0045, -0.0001)
    with pytest.raises(ValueError, match="exceed"):
        compute_cylinder_force(120000.0, 80000.0, 0.0030, 0.0032)


def test_compute_cylinder_force_rejects_non_finite_pressures() -> None:
    with pytest.raises(ValueError, match="p_head"):
        compute_cylinder_force(float("nan"), 80000.0, 0.0045, 0.0032)
    with pytest.raises(ValueError, match="p_rod"):
        compute_cylinder_force(120000.0, float("inf"), 0.0045, 0.0032)


def test_compute_spring_force_compression_only() -> None:
    assert math.isclose(compute_spring_force(0.1, 0.2, 30000.0), 3000.0)
    assert math.isclose(compute_spring_force(0.3, 0.2, 30000.0), 0.0)


def test_compute_damper_force_applies_threshold() -> None:
    assert math.isclose(compute_damper_force(0.2, 1000.0, F_min=500.0), 0.0)
    # Negative velocity produces a restoring force (negative sign).
    assert math.isclose(compute_damper_force(-0.8, 1500.0, F_min=100.0), -1200.0)


def test_project_forces_to_vertical_and_moments() -> None:
    states = {
        "LP": {"F_total_axis": 1000.0, "axis_unit_world": np.array([0.0, 1.0, 0.0])},
        "PP": {"F_total_axis": 800.0, "axis_unit_world": np.array([0.0, 1.0, 0.0])},
    }
    attachments = {"LP": (-0.9, -1.1), "PP": (0.9, -1.1)}

    vertical, tau_x, tau_z = project_forces_to_vertical_and_moments(states, attachments)

    assert np.allclose(vertical[:2], np.array([1000.0, 800.0]))
    # Only the longitudinal coordinate contributes to pitch moment.
    assert math.isclose(tau_x, -1.1 * (1000.0 + 800.0))
    # Unequal forces create a residual roll moment.
    assert math.isclose(tau_z, -180.0)


def test_get_body_angular_velocity_from_euler_rates_small_angles() -> None:
    rates = np.array([0.0, 0.25, -0.75])
    angles = np.array([0.0, 0.1, -0.2])

    result = get_body_angular_velocity_from_euler_rates(rates, angles)
    assert np.allclose(result, np.array([-0.75, 0.0, 0.25]))


def test_validate_force_calculation_detects_invalid_inputs() -> None:
    ok_forces = np.array([100.0, 120.0, 130.0, 90.0])
    assert validate_force_calculation(ok_forces, (100.0, -50.0)) == (True, "")

    bad_forces = np.array([np.nan, 0.0, 0.0, 0.0])
    assert validate_force_calculation(bad_forces, (0.0, 0.0))[0] is False

    extreme_moment = (1.2e7, 0.0)
    assert validate_force_calculation(ok_forces, extreme_moment)[0] is False


def test_create_test_suspension_state_constructs_consistent_payload() -> None:
    state = create_test_suspension_state("LP", F_cyl=10.0, F_spring=5.0, F_damper=-3.0)

    suspension_constants = get_physics_suspension_constants()
    axis = np.asarray(suspension_constants["axis_unit_world"], dtype=float)
    axis = axis / np.linalg.norm(axis)

    assert state["wheel_name"] == "LP"
    assert math.isclose(state["F_total_axis"], 12.0)
    assert np.allclose(state["axis_unit_world"], axis)
