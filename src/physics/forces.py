"""
Force calculation utilities for 3-DOF dynamics
Handles projection of suspension forces and moment calculations
"""

import numpy as np
from typing import Tuple, Dict, Any


def compute_point_velocity_world(
    r_local: np.ndarray, body_velocity: np.ndarray, body_angular_velocity: np.ndarray
) -> np.ndarray:
    """Compute velocity of a point on rigid body in world coordinates

    Args:
        r_local: Position vector in body frame (3,) -> (x, y, z)
        body_velocity: Linear velocity of body center of mass (3,) -> (vx, vy, vz)
        body_angular_velocity: Angular velocity vector (3,) -> (?x, ?y, ?z)

    Returns:
        Point velocity in world frame (3,)
    """
    # v_point = v_body + ? ? r
    return body_velocity + np.cross(body_angular_velocity, r_local)


def compute_axis_velocity(
    axis_unit_world: np.ndarray, point_velocity_world: np.ndarray
) -> float:
    """Compute velocity component along cylinder axis

    Args:
        axis_unit_world: Unit vector of cylinder axis in world coordinates (3,)
        point_velocity_world: Velocity of attachment point in world coordinates (3,)

    Returns:
        Axial velocity (scalar, positive = extension)
    """
    return np.dot(axis_unit_world, point_velocity_world)


def compute_suspension_point_kinematics(
    wheel_name: str, y: np.ndarray, attachment_points: Dict[str, Tuple[float, float]]
) -> Dict[str, Any]:
    """Compute kinematic state for a suspension point

    Args:
        wheel_name: Identifier for wheel (LP, PP, LZ, PZ)
        y: State vector [Y, ?z, ?x, dY, d?z, d?x]
        attachment_points: Dictionary mapping wheel names to (x, z) coordinates

    Returns:
        Dictionary with kinematic information
    """
    Y, phi_z, theta_x, dY, dphi_z, dtheta_x = y

    # Get attachment point coordinates
    if wheel_name not in attachment_points:
        raise ValueError(f"Unknown wheel name: {wheel_name}")

    x_attach, z_attach = attachment_points[wheel_name]

    # Position vector of attachment point in body frame
    r_local = np.array([x_attach, 0.0, z_attach])  # y=0 in body frame

    # Body center velocity in world frame
    body_velocity = np.array([0.0, dY, 0.0])  # Only heave motion for body center

    # Angular velocity vector: ? = [d?x, 0, d?z] (small angle approximation)
    body_angular_velocity = np.array([dtheta_x, 0.0, dphi_z])

    # Attachment point velocity in world frame
    point_velocity = compute_point_velocity_world(
        r_local, body_velocity, body_angular_velocity
    )

    # TODO: Get actual cylinder axis from system geometry
    # For now, assume vertical cylinders as placeholder
    axis_unit_world = np.array([0.0, 1.0, 0.0])  # Vertical (down positive)

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
    # Net force = head pressure ? head area - rod pressure ? rod area
    F_net = p_head * A_head - p_rod * A_rod
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


def compute_damper_force(v_axis: float, c_damper: float, F_min: float = 0.0) -> float:
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
    suspension_states: Dict[str, Dict],
    attachment_points: Dict[str, Tuple[float, float]],
) -> Tuple[np.ndarray, float, float]:
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

    eY = np.array([0.0, 1.0, 0.0])  # Vertical unit vector (down positive)

    for i, wheel_name in enumerate(wheel_names):
        if wheel_name not in suspension_states:
            continue

        state = suspension_states[wheel_name]

        # Get total axial force
        F_total_axis = state.get("F_total_axis", 0.0)
        axis_unit = state.get("axis_unit_world", eY)

        # Project to vertical component
        F_vertical = np.dot(axis_unit, eY) * F_total_axis
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
    forces: np.ndarray, moments: Tuple[float, float]
) -> Tuple[bool, str]:
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

    # Check reasonable force magnitudes (up to 100 kN per wheel)
    max_force = 100000.0  # 100 kN
    if np.any(np.abs(forces) > max_force):
        return (
            False,
            f"Forces exceed reasonable limit: max={np.max(np.abs(forces)):.1f}N",
        )

    # Check reasonable moment magnitudes (up to 1000 kN?m)
    max_moment = 1000000.0  # 1000 kN?m
    if abs(tau_x) > max_moment or abs(tau_z) > max_moment:
        return (
            False,
            f"Moments exceed reasonable limit: ?x={tau_x:.1f}, ?z={tau_z:.1f} N?m",
        )

    return True, ""


# Default suspension parameters for testing
DEFAULT_SUSPENSION_PARAMS = {
    "k_spring": 50000.0,  # Spring constant (N/m)
    "c_damper": 2000.0,  # Damping coefficient (N?s/m)
    "F_damper_min": 50.0,  # Minimum damper force (N)
    "x_spring_rest": 0.0,  # Spring rest position (m)
    "A_head": 0.005,  # Cylinder head area (m?) - 80mm bore
    "A_rod": 0.004,  # Cylinder rod area (m?)
}


def create_test_suspension_state(
    wheel_name: str, F_cyl: float = 0.0, F_spring: float = 0.0, F_damper: float = 0.0
) -> Dict[str, Any]:
    """Create test suspension state for validation

    Args:
        wheel_name: Wheel identifier
        F_cyl: Cylinder force (N)
        F_spring: Spring force (N)
        F_damper: Damper force (N)

    Returns:
        Suspension state dictionary
    """
    eY = np.array([0.0, 1.0, 0.0])  # Vertical axis

    return {
        "wheel_name": wheel_name,
        "F_cyl_axis": F_cyl,
        "F_spring_axis": F_spring,
        "F_damper_axis": F_damper,
        "F_total_axis": F_cyl + F_spring + F_damper,
        "axis_unit_world": eY,
        "axial_velocity": 0.0,
    }
