"""Force calculation utilities for 3-DOF dynamics.

Handles projection of suspension forces and moment calculations while remaining
fully deterministic. The helpers in this module are intentionally lightweight –
they operate purely on NumPy arrays and primitive containers so that they can be
reused by the physics integrator, the diagnostics suite and smoke tests without
pulling in the heavier simulation layers. Previous revisions relied on an
implicit global ``numpy`` import which made the functions crash as soon as they
were exercised; we now validate the inputs explicitly so that issues are caught
in a controlled manner during automated test runs.
"""

from __future__ import annotations

from typing import Any, Dict, Tuple
from collections.abc import Iterable, Mapping

import math
import numpy as np
from numpy.typing import ArrayLike, NDArray

from src.common.units import to_gauge_pressure

from config.constants import (
    get_physics_reference_axes,
    get_physics_suspension_constants,
    get_physics_validation_constants,
)


def _to_vector3(value: ArrayLike, *, name: str) -> NDArray[np.float64]:
    """Convert ``value`` into a 3D float vector.

    The helper performs a strict shape check which keeps subtle mistakes (for
    example passing a 2D array or a list of length other than three) from
    propagating deeper into the physics calculations where they would cause
    cryptic NumPy broadcasting errors.
    """

    array = np.asarray(value, dtype=float)
    if array.shape != (3,):  # pragma: no cover - sanity guard
        raise ValueError(f"{name} must be a 3-vector, got shape {array.shape!r}")
    return array


def _normalise_axis(axis: ArrayLike) -> NDArray[np.float64]:
    """Return a unit vector for ``axis`` ensuring numerical stability."""

    vector = _to_vector3(axis, name="axis")
    norm = float(np.linalg.norm(vector))
    if norm == 0.0:
        raise ValueError("Axis vector must not be zero")
    return vector / norm


def _load_vertical_axis() -> NDArray[np.float64]:
    axes = get_physics_reference_axes()
    vertical = axes.get("vertical_world")
    if vertical is None:
        raise KeyError(
            "Missing constants.physics.reference_axes.vertical_world in settings"
        )
    return _normalise_axis(vertical)


def _load_suspension_defaults() -> dict[str, Any]:
    mapping = get_physics_suspension_constants()
    required_scalars: Mapping[str, str] = {
        "spring_constant": "k_spring",
        "damper_coefficient": "c_damper",
        "damper_force_threshold_n": "F_damper_min",
        "spring_rest_position_m": "x_spring_rest",
        "cylinder_head_area_m2": "A_head",
        "cylinder_rod_area_m2": "A_rod",
    }

    result: dict[str, Any] = {}
    for source_key, target_key in required_scalars.items():
        value = mapping.get(source_key)
        if not isinstance(value, (int, float)):
            raise TypeError(
                "Invalid type for constants.physics.suspension"
                f".{source_key}: expected number, got {type(value).__name__}"
            )
        result[target_key] = float(value)

    axis_value = mapping.get("axis_unit_world")
    if axis_value is None:
        raise KeyError(
            "Missing constants.physics.suspension.axis_unit_world in settings"
        )
    result["axis_unit_world"] = _normalise_axis(axis_value)
    return result


def _load_validation_limits() -> dict[str, float]:
    mapping = get_physics_validation_constants()
    limits: dict[str, float] = {}
    for key in ("max_force_n", "max_moment_n_m"):
        value = mapping.get(key)
        if not isinstance(value, (int, float)):
            raise TypeError(
                "Invalid type for constants.physics.validation"
                f".{key}: expected number, got {type(value).__name__}"
            )
        limits[key] = float(value)
    return limits


VERTICAL_AXIS = _load_vertical_axis()
_SUSPENSION_DEFAULTS = _load_suspension_defaults()
_VALIDATION_LIMITS = _load_validation_limits()


def compute_point_velocity_world(
    r_local: ArrayLike,
    body_velocity: ArrayLike,
    body_angular_velocity: ArrayLike,
) -> NDArray[np.float64]:
    """Compute velocity of a point on a rigid body in world coordinates.

    Args:
        r_local: Position vector in body frame (``x``, ``y``, ``z``).
        body_velocity: Linear velocity of body centre of mass.
        body_angular_velocity: Angular velocity vector (``ωx``, ``ωy``, ``ωz``).

    Returns:
        Point velocity in the world reference frame.
    """

    r_vec = _to_vector3(r_local, name="r_local")
    v_body = _to_vector3(body_velocity, name="body_velocity")
    w_body = _to_vector3(body_angular_velocity, name="body_angular_velocity")
    return v_body + np.cross(w_body, r_vec)


def compute_axis_velocity(
    axis_unit_world: ArrayLike, point_velocity_world: ArrayLike
) -> float:
    """Compute velocity component along cylinder axis

    Args:
        axis_unit_world: Unit vector of cylinder axis in world coordinates (3,)
        point_velocity_world: Velocity of attachment point in world coordinates (3,)

    Returns:
        Axial velocity (scalar, positive = extension)
    """
    axis = _normalise_axis(axis_unit_world)
    velocity = _to_vector3(point_velocity_world, name="point_velocity_world")
    return float(np.dot(axis, velocity))


def compute_suspension_point_kinematics(
    wheel_name: str,
    y: ArrayLike,
    attachment_points: dict[str, tuple[float, float]],
    axis_directions: Mapping[str, Iterable[float]],
) -> dict[str, Any]:
    """Compute kinematic state for a suspension point

    Args:
        wheel_name: Identifier for wheel (LP, PP, LZ, PZ)
        y: State vector [Y, ?z, ?x, dY, d?z, d?x]
        attachment_points: Dictionary mapping wheel names to (x, z) coordinates

    Returns:
        Dictionary with kinematic information
    """
    state = np.asarray(y, dtype=float)
    if state.shape != (6,):  # pragma: no cover - sanity guard
        raise ValueError(
            f"State vector must contain six values, got shape {state.shape!r}"
        )

    Y, phi_z, theta_x, dY, dphi_z, dtheta_x = state

    # Get attachment point coordinates
    if wheel_name not in attachment_points:
        raise ValueError(f"Unknown wheel name: {wheel_name}")

    x_attach, z_attach = attachment_points[wheel_name]

    # Position vector of attachment point in body frame
    r_local = np.array([x_attach, 0.0, z_attach], dtype=float)

    # Body center velocity in world frame
    body_velocity = np.array([0.0, dY, 0.0], dtype=float)

    # Angular velocity vector: ? = [d?x, 0, d?z] (small angle approximation)
    body_angular_velocity = np.array([dtheta_x, 0.0, dphi_z], dtype=float)

    # Attachment point velocity in world frame
    point_velocity = compute_point_velocity_world(
        r_local, body_velocity, body_angular_velocity
    )

    if wheel_name not in axis_directions:
        raise KeyError(
            f"Missing axis direction for wheel '{wheel_name}'."
            " Ensure settings.physics.suspension.axis_unit_world is"
            " exposed in the UI and provided here."
        )

    axis_unit_world = _normalise_axis(axis_directions[wheel_name])

    # Axial velocity
    v_axis = compute_axis_velocity(axis_unit_world, point_velocity)

    return {
        "position_local": r_local,
        "velocity_world": point_velocity,
        "axis_unit_world": axis_unit_world,
        "axial_velocity": v_axis,
    }


def compute_cylinder_force(
    p_head: float, p_rod: float, A_head: float, A_rod: float
) -> float:
    """Compute net pneumatic cylinder force along axis

    Args:
        p_head: Head side pressure (Pa)
        p_rod: Rod side pressure (Pa)
        A_head: Head side effective area (m?)
        A_rod: Rod side effective area (m?) (= A_head - A_rod_steel)

    Returns:
        Net force along cylinder axis (N, positive = extension)
    """
    p_head_f = float(p_head)
    p_rod_f = float(p_rod)
    A_head_f = float(A_head)
    A_rod_f = float(A_rod)

    for name, value in ("p_head", p_head_f), ("p_rod", p_rod_f):
        if not math.isfinite(value):
            raise ValueError(f"{name} must be a finite number")

    for name, value, predicate, message in (
        ("A_head", A_head_f, lambda v: v > 0.0, "Head side area must be positive"),
        (
            "A_rod",
            A_rod_f,
            lambda v: v >= 0.0,
            "Rod side area must be non-negative",
        ),
    ):
        if not math.isfinite(value):
            raise ValueError(f"{name} must be a finite number")
        if not predicate(value):
            raise ValueError(message)

    if A_rod_f > A_head_f:
        raise ValueError("Rod side area cannot exceed head side area")

    # Net force = (p_head − p_atm) × head area − (p_rod − p_atm) × rod area
    p_head_gauge = to_gauge_pressure(p_head_f)
    p_rod_gauge = to_gauge_pressure(p_rod_f)
    F_net = p_head_gauge * A_head_f - p_rod_gauge * A_rod_f
    return F_net


def compute_spring_force(x_current: float, x_rest: float, k_spring: float) -> float:
    """Compute one-sided spring force (compression only)

    Args:
        x_current: Current position along axis (m)
        x_rest: Rest position (m)
        k_spring: Spring constant (N/m)

    Returns:
        Spring force (N, positive when compressed)
    """
    # One-sided spring: only works in compression
    compression = x_rest - x_current
    if compression > 0:
        return k_spring * compression
    else:
        return 0.0


def compute_damper_force(v_axis: float, c_damper: float, F_min: float) -> float:
    """Compute linear damper force with minimum threshold

    Args:
        v_axis: Axial velocity (m/s)
        c_damper: Damping coefficient (N?s/m)
        F_min: Minimum force threshold (N) - below this, force = 0

    Returns:
        Damper force (N)
    """
    F_damper = c_damper * v_axis

    # Apply minimum threshold
    if abs(F_damper) < F_min:
        return 0.0
    else:
        return F_damper


def project_forces_to_vertical_and_moments(
    suspension_states: dict[str, dict],
    attachment_points: dict[str, tuple[float, float]],
) -> tuple[np.ndarray, float, float]:
    """Project suspension forces to vertical components and compute moments

    Args:
        suspension_states: Dictionary with force information for each wheel
        attachment_points: Wheel positions (x, z) in body frame

    Returns:
        Tuple of (vertical_forces, tau_x, tau_z)
        vertical_forces: Array of vertical forces at each wheel (N, positive down)
        tau_x: Total moment about X-axis (pitch) (N?m)
        tau_z: Total moment about Z-axis (roll) (N?m)
    """
    wheel_names = ["LP", "PP", "LZ", "PZ"]  # Standard order
    vertical_forces = np.zeros(4)
    tau_x = 0.0  # Pitch moment
    tau_z = 0.0  # Roll moment

    for i, wheel_name in enumerate(wheel_names):
        if wheel_name not in suspension_states:
            continue

        state = suspension_states[wheel_name]

        # Get total axial force
        if "F_total_axis" not in state:
            raise KeyError(
                f"Missing F_total_axis for wheel '{wheel_name}' in suspension state"
            )
        if "axis_unit_world" not in state:
            raise KeyError(
                f"Missing axis_unit_world for wheel '{wheel_name}' in suspension state"
            )

        F_total_axis = float(state["F_total_axis"])
        axis_unit = _normalise_axis(state["axis_unit_world"])

        # Project to vertical component
        F_vertical = float(np.dot(axis_unit, VERTICAL_AXIS)) * F_total_axis
        vertical_forces[i] = F_vertical

        # Get attachment point for moment calculation
        if wheel_name in attachment_points:
            x_i, z_i = attachment_points[wheel_name]

            # Moment arms:
            # Pitch (about X): force ? longitudinal distance
            # Roll (about Z): force ? lateral distance
            tau_x += F_vertical * z_i
            tau_z += F_vertical * x_i

    return vertical_forces, tau_x, tau_z


def get_body_angular_velocity_from_euler_rates(
    euler_rates: np.ndarray, euler_angles: np.ndarray
) -> np.ndarray:
    """Convert Euler angle rates to body angular velocity

    For small angles (our case), this is approximately:
    ? ? [d?x, 0, d?z]

    Args:
        euler_rates: [dY, d?z, d?x] (heave rate, roll rate, pitch rate)
        euler_angles: [Y, ?z, ?x] (heave, roll, pitch)

    Returns:
        Angular velocity vector ? = [?x, ?y, ?z] in body frame
    """
    _, dphi_z, dtheta_x = euler_rates
    _, phi_z, theta_x = euler_angles

    # For small angles, transformation is approximately identity
    # ? ? [pitch_rate, yaw_rate, roll_rate] = [d?x, 0, d?z]
    return np.array([dtheta_x, 0.0, dphi_z])


def validate_force_calculation(
    forces: np.ndarray, moments: tuple[float, float]
) -> tuple[bool, str]:
    """Validate computed forces and moments for reasonableness

    Args:
        forces: Array of vertical forces (N)
        moments: (tau_x, tau_z) moments (N?m)

    Returns:
        (is_valid, error_message)
    """
    # Check for NaN/inf
    if not np.all(np.isfinite(forces)):
        return False, "Forces contain NaN or infinite values"

    tau_x, tau_z = moments
    if not (np.isfinite(tau_x) and np.isfinite(tau_z)):
        return False, "Moments contain NaN or infinite values"

    max_force = _VALIDATION_LIMITS["max_force_n"]
    if np.any(np.abs(forces) > max_force):
        return (
            False,
            f"Forces exceed reasonable limit: max={np.max(np.abs(forces)):.1f}N",
        )

    max_moment = _VALIDATION_LIMITS["max_moment_n_m"]
    if abs(tau_x) > max_moment or abs(tau_z) > max_moment:
        return (
            False,
            f"Moments exceed reasonable limit: ?x={tau_x:.1f}, ?z={tau_z:.1f} N?m",
        )

    return True, ""


# Default suspension parameters for testing
DEFAULT_SUSPENSION_PARAMS = {
    key: _SUSPENSION_DEFAULTS[key]
    for key in (
        "k_spring",
        "c_damper",
        "F_damper_min",
        "x_spring_rest",
        "A_head",
        "A_rod",
    )
}


def create_test_suspension_state(
    wheel_name: str, F_cyl: float = 0.0, F_spring: float = 0.0, F_damper: float = 0.0
) -> dict[str, Any]:
    """Create test suspension state for validation

    Args:
        wheel_name: Wheel identifier
        F_cyl: Cylinder force (N)
        F_spring: Spring force (N)
        F_damper: Damper force (N)

    Returns:
        Suspension state dictionary
    """
    return {
        "wheel_name": wheel_name,
        "F_cyl_axis": F_cyl,
        "F_spring_axis": F_spring,
        "F_damper_axis": F_damper,
        "F_total_axis": F_cyl + F_spring + F_damper,
        "axis_unit_world": _SUSPENSION_DEFAULTS["axis_unit_world"].copy(),
        "axial_velocity": 0.0,
    }
