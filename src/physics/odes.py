"""
3-DOF rigid body dynamics for vehicle frame
Handles heave (Y), roll (phi_z), and pitch (theta_x) motion with suspension forces
"""

import math
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

import numpy as np

from src.core.settings_service import SettingsService
from src.core.settings_validation import SettingsValidationError
from src.pneumo.enums import Port, Wheel

from .forces import compute_cylinder_force

# Coordinate system: X-lateral (left/right), Y-vertical (down positive), Z-longitudinal


@dataclass
class RigidBody3DOF:
    """3-DOF rigid body parameters, geometry, and static load state."""

    M: float  # Total mass (kg)
    Ix: float  # Moment of inertia around X-axis (pitch) (kg*m^2)
    Iz: float  # Moment of inertia around Z-axis (roll) (kg*m^2)
    g: float = 9.81  # Gravitational acceleration (m/s^2)

    # Suspension attachment points in body frame (x_i, z_i)
    # y-coordinate taken as current heave
    attachment_points: Dict[str, Tuple[float, float]] | None = None

    # Vehicle dimensions for reference
    track: float = 1.6  # Track width (m)
    wheelbase: float = 3.2  # Wheelbase (m)

    # Numerical stability
    angle_limit: float = 0.5  # Maximum angle in radians (~28.6 degrees)
    damping_coefficient: float = 0.1  # Viscous damping on angles

    # Static load distribution (reaction forces, positive downwards)
    static_wheel_loads: Mapping[str | Wheel, float] | None = None
    static_load_tolerance: float = 0.05

    _static_wheel_loads: Dict[Wheel, float] = field(init=False, repr=False)
    _static_total_load: float = field(init=False, repr=False)
    _static_pitch_moment: float = field(init=False, repr=False)
    _static_roll_moment: float = field(init=False, repr=False)

    def __post_init__(self) -> None:
        """Initialise geometry defaults and normalise static loads."""
        if self.attachment_points is None:
            half_track = self.track / 2.0
            half_wheelbase = self.wheelbase / 2.0
            self.attachment_points = {
                "LP": (-half_track, -half_wheelbase),
                "PP": (+half_track, -half_wheelbase),
                "LZ": (-half_track, +half_wheelbase),
                "PZ": (+half_track, +half_wheelbase),
            }
        self._initialise_static_loads()

    def _initialise_static_loads(self) -> None:
        """Normalise provided static loads so they counteract gravity."""
        target_sum = -self.M * self.g
        provided = dict(self.static_wheel_loads or {})
        resolved: Dict[Wheel, float] = {}

        for wheel in Wheel:
            load = None
            if wheel in provided:
                load = provided[wheel]
            elif wheel.value in provided:
                load = provided[wheel.value]
            if load is not None:
                resolved[wheel] = float(load)

        if not resolved:
            equal_share = target_sum / len(Wheel)
            resolved = {wheel: equal_share for wheel in Wheel}
        else:
            missing = [wheel for wheel in Wheel if wheel not in resolved]
            if missing:
                remaining = target_sum - sum(resolved.values())
                share = remaining / len(missing) if missing else 0.0
                for wheel in missing:
                    resolved[wheel] = share

        sum_loads = sum(resolved.values())
        tolerance = max(1.0, abs(target_sum)) * 1e-9
        if abs(sum_loads) <= tolerance:
            equal_share = target_sum / len(Wheel)
            resolved = {wheel: equal_share for wheel in Wheel}
            sum_loads = target_sum
        elif not math.isclose(
            sum_loads, target_sum, rel_tol=self.static_load_tolerance, abs_tol=tolerance
        ):
            scale = target_sum / sum_loads
            for wheel in resolved:
                resolved[wheel] *= scale

        self._static_wheel_loads = resolved
        self._static_total_load = target_sum
        self._static_pitch_moment = sum(
            resolved[wheel] * self.attachment_points[wheel.value][1] for wheel in Wheel
        )
        self._static_roll_moment = sum(
            resolved[wheel] * self.attachment_points[wheel.value][0] for wheel in Wheel
        )

    def static_load_for(self, wheel: Wheel | str) -> float:
        """Return static reaction force for ``wheel`` (positive downwards)."""
        if isinstance(wheel, str):
            try:
                wheel = Wheel[wheel]
            except KeyError as exc:
                raise KeyError(f"Unknown wheel identifier {wheel!r}") from exc
        return self._static_wheel_loads[wheel]

    @property
    def static_total_load(self) -> float:
        """Sum of static suspension reactions (should equal ``-M*g``)."""
        return self._static_total_load

    @property
    def static_pitch_moment(self) -> float:
        """Pitch moment contributed by static suspension reactions."""
        return self._static_pitch_moment

    @property
    def static_roll_moment(self) -> float:
        """Roll moment contributed by static suspension reactions."""
        return self._static_roll_moment

    @property
    def static_wheel_load_map(self) -> Dict[Wheel, float]:
        """Expose a copy of the normalised static wheel loads."""
        return dict(self._static_wheel_loads)


_SUSPENSION_SETTINGS_CACHE: dict[str, float] | None = None
_WHEEL_ORDER = ["LP", "PP", "LZ", "PZ"]


def _load_suspension_settings() -> dict[str, float]:
    """Fetch suspension configuration from the settings file."""

    global _SUSPENSION_SETTINGS_CACHE
    if _SUSPENSION_SETTINGS_CACHE is not None:
        return _SUSPENSION_SETTINGS_CACHE

    service = SettingsService(validate_schema=False)
    raw_settings = service.get("current.physics.suspension")
    if not isinstance(raw_settings, Mapping):
        raise SettingsValidationError(
            "Отсутствует секция current.physics.suspension в файле настроек"
        )

    try:
        spring_constant = float(raw_settings["spring_constant"])
    except KeyError as exc:
        raise SettingsValidationError(
            "В секции current.physics.suspension отсутствует параметр spring_constant"
        ) from exc
    except (TypeError, ValueError) as exc:
        raise SettingsValidationError(
            "Параметр spring_constant в current.physics.suspension должен быть числом"
        ) from exc

    try:
        damper_coefficient = float(raw_settings["damper_coefficient"])
    except KeyError as exc:
        raise SettingsValidationError(
            "В секции current.physics.suspension отсутствует параметр damper_coefficient"
        ) from exc
    except (TypeError, ValueError) as exc:
        raise SettingsValidationError(
            "Параметр damper_coefficient в current.physics.suspension должен быть числом"
        ) from exc

    _SUSPENSION_SETTINGS_CACHE = {
        "spring_constant": spring_constant,
        "damper_coefficient": damper_coefficient,
    }
    return _SUSPENSION_SETTINGS_CACHE


def reset_suspension_settings_cache() -> None:
    """Сбросить кэш параметров подвески (используется в тестах)."""

    global _SUSPENSION_SETTINGS_CACHE
    _SUSPENSION_SETTINGS_CACHE = None


@dataclass
class SuspensionPointState:
    """State of a single suspension point"""

    wheel_name: str  # Wheel identifier
    axis_unit_world: np.ndarray  # Unit vector of cylinder axis in world coords (3,)
    F_cyl_axis: float  # Pneumatic cylinder force along axis (N)
    Fs_axis: float  # Spring force along axis (N)
    Fd_axis: float  # Damper force along axis (N)
    lever_arm_local: np.ndarray  # Position vector in body frame (3,) -> (x, 0, z)

    def __post_init__(self):
        """Validate arrays"""
        self.axis_unit_world = np.asarray(self.axis_unit_world, dtype=float)
        self.lever_arm_local = np.asarray(self.lever_arm_local, dtype=float)

        if self.axis_unit_world.shape != (3,):
            raise ValueError(
                f"axis_unit_world must be shape (3,), got {self.axis_unit_world.shape}"
            )
        if self.lever_arm_local.shape != (3,):
            raise ValueError(
                f"lever_arm_local must be shape (3,), got {self.lever_arm_local.shape}"
            )


def axis_vertical_projection(F_axis: float, axis_unit_world: np.ndarray) -> float:
    """Calculate vertical component of axial force

    Args:
        F_axis: Force magnitude along cylinder axis (N)
        axis_unit_world: Unit vector of axis in world coordinates

    Returns:
        Vertical force component (N, positive downward)
    """
    eY = np.array([0.0, 1.0, 0.0])  # Vertical axis (down positive)
    return np.dot(axis_unit_world, eY) * F_axis


def _resolve_line_pressure(system: Any, gas: Any, wheel: Wheel, port: Port) -> float:
    """Return pressure for the line connected to the specified port."""

    if system is None or gas is None:
        return 0.0

    system_lines = getattr(system, "lines", None)
    gas_lines = getattr(gas, "lines", None)

    if system_lines is None or gas_lines is None:
        tank = getattr(gas, "tank", None)
        return float(getattr(tank, "p", 0.0))

    try:
        line_items = system_lines.items()
    except AttributeError:
        line_items = []

    for line_name, line in line_items:
        endpoints = getattr(line, "endpoints", ())
        for endpoint_wheel, endpoint_port in endpoints:
            if endpoint_wheel == wheel and endpoint_port == port:
                try:
                    gas_state = gas_lines[line_name]
                except Exception:
                    gas_state = None
                if gas_state is not None and hasattr(gas_state, "p"):
                    return float(gas_state.p)

    tank = getattr(gas, "tank", None)
    return float(getattr(tank, "p", 0.0))


def assemble_forces(
    system: Any, gas: Any, y: np.ndarray, params: RigidBody3DOF
) -> Tuple[np.ndarray, float, float]:
    """Assemble forces and moments from suspension system

    Args:
        system: Pneumatic system (provides geometry, cylinder states)
        gas: Gas network (provides pressures)
        y: State vector [Y, phi_z, theta_x, dY, dphi_z, dtheta_x]
        params: Rigid body parameters

    Returns:
        Tuple of (vertical_forces[4], tau_x, tau_z)
        vertical_forces: Force at each wheel (N, positive down)
        tau_x: Moment around X-axis (pitch) (N*m)
        tau_z: Moment around Z-axis (roll) (N*m)
    """
    Y, phi_z, theta_x, dY, dphi_z, dtheta_x = y

    wheel_names = _WHEEL_ORDER  # Left Front, Right Front, Left Rear, Right Rear
    vertical_forces = np.zeros(len(_WHEEL_ORDER))

    suspension_config = _load_suspension_settings()
    k_spring = suspension_config["spring_constant"]  # N/m (spring stiffness per wheel)
    c_damper = suspension_config[
        "damper_coefficient"
    ]  # N*s/m (damping coefficient per wheel)

    # Calculate forces at each wheel
    include_static = system is None and gas is None

    for i, wheel_name in enumerate(wheel_names):
        # Get attachment point
        if wheel_name in params.attachment_points:
            x_i, z_i = params.attachment_points[wheel_name]
        else:
            # Default positions if not specified
            x_i = (-1.0 if "L" in wheel_name else 1.0) * params.track / 2.0
            z_i = (-1.0 if "P" in wheel_name else 1.0) * params.wheelbase / 2.0

        # Calculate wheel vertical displacement accounting for frame angles
        # Simplified: assume small angles, so wheel displacement ? Y
        wheel_displacement = Y

        # Add contribution from roll (z-axis rotation)
        # Wheel moves up/down based on lateral distance and roll angle
        wheel_displacement += x_i * phi_z

        # Add contribution from pitch (x-axis rotation)
        # Wheel moves up/down based on longitudinal distance and pitch angle
        wheel_displacement += z_i * theta_x

        # Spring force (resists compression, acts upward = negative force)
        # Positive displacement = compression = upward force
        F_spring = -k_spring * wheel_displacement

        # Damper force (resists velocity)
        # Calculate wheel velocity including angular contributions
        wheel_velocity = dY + x_i * dphi_z + z_i * dtheta_x
        F_damper = -c_damper * wheel_velocity

        F_pneumatic = 0.0
        cylinder = None
        try:
            wheel_enum = Wheel[wheel_name]
        except KeyError:
            wheel_enum = None

        if wheel_enum is not None and system is not None:
            cylinders = getattr(system, "cylinders", {})
            cylinder = cylinders.get(wheel_enum)

        if cylinder is not None:
            geom = cylinder.spec.geometry
            area_head = geom.area_head(cylinder.spec.is_front)
            area_rod = geom.area_rod(cylinder.spec.is_front)
            head_pressure = _resolve_line_pressure(system, gas, wheel_enum, Port.HEAD)
            rod_pressure = _resolve_line_pressure(system, gas, wheel_enum, Port.ROD)
            F_pneumatic = compute_cylinder_force(
                head_pressure, rod_pressure, area_head, area_rod
            )

        # Total vertical force (positive downward)
        static_reaction = 0.0
        if include_static:
            static_reaction = params.static_load_for(wheel_enum or wheel_name)

        vertical_forces[i] = F_spring + F_damper + F_pneumatic + static_reaction

    # Calculate moments about center of mass
    tau_x = 0.0  # Pitch moment
    tau_z = 0.0  # Roll moment

    for i, wheel_name in enumerate(wheel_names):
        if wheel_name in params.attachment_points:
            x_i, z_i = params.attachment_points[wheel_name]

            # Moment arms for pitch (about X-axis) and roll (about Z-axis)
            tau_x += vertical_forces[i] * z_i  # Pitch: force x longitudinal arm
            tau_z += vertical_forces[i] * x_i  # Roll: force x lateral arm

    return vertical_forces, tau_x, tau_z


def f_rhs(
    t: float, y: np.ndarray, params: RigidBody3DOF, system: Any, gas: Any
) -> np.ndarray:
    """Right-hand side of 3-DOF ODE system

    State vector: y = [Y, phi_z, theta_x, dY, dphi_z, dtheta_x]

    Args:
        t: Time (s)
        y: State vector [position; velocity]
        params: Rigid body parameters
        system: Pneumatic system
        gas: Gas network

    Returns:
        Derivative vector dy/dt
    """
    # Unpack state
    Y, phi_z, theta_x, dY, dphi_z, dtheta_x = y

    # Clamp angles to prevent numerical issues
    phi_z = np.clip(phi_z, -params.angle_limit, params.angle_limit)
    theta_x = np.clip(theta_x, -params.angle_limit, params.angle_limit)

    # Get suspension forces
    vertical_forces, tau_x, tau_z = assemble_forces(system, gas, y, params)

    static_forces = np.array([params.static_load_for(name) for name in _WHEEL_ORDER])
    includes_static = system is None and gas is None

    if includes_static:
        total_vertical_forces = vertical_forces
    else:
        total_vertical_forces = vertical_forces + static_forces
        for idx, wheel_name in enumerate(_WHEEL_ORDER):
            x_i, z_i = params.attachment_points[wheel_name]
            tau_x += static_forces[idx] * z_i
            tau_z += static_forces[idx] * x_i

    # Gravitational force (positive downward)
    F_gravity = params.M * params.g

    # Sum of vertical forces from suspension (dynamic + static reactions)
    F_suspension_total = np.sum(total_vertical_forces)

    # Remove static reaction moments so that neutral pose stays stable
    tau_x -= params.static_pitch_moment
    tau_z -= params.static_roll_moment

    # Equations of motion
    # Heave: vertical acceleration
    d2Y = (F_gravity + F_suspension_total) / params.M

    # Roll: angular acceleration about Z-axis
    d2phi_z = tau_z / params.Iz - params.damping_coefficient * dphi_z

    # Pitch: angular acceleration about X-axis
    d2theta_x = tau_x / params.Ix - params.damping_coefficient * dtheta_x

    # Return derivative vector [velocity; acceleration]
    return np.array([dY, dphi_z, dtheta_x, d2Y, d2phi_z, d2theta_x])


def create_initial_conditions(
    heave: float = 0.0,
    roll: float = 0.0,
    pitch: float = 0.0,
    heave_rate: float = 0.0,
    roll_rate: float = 0.0,
    pitch_rate: float = 0.0,
) -> np.ndarray:
    """Create initial condition vector

    Args:
        heave: Initial vertical position (m, positive down)
        roll: Initial roll angle (rad)
        pitch: Initial pitch angle (rad)
        heave_rate: Initial vertical velocity (m/s)
        roll_rate: Initial roll rate (rad/s)
        pitch_rate: Initial pitch rate (rad/s)

    Returns:
        Initial state vector y0
    """
    return np.array([heave, roll, pitch, heave_rate, roll_rate, pitch_rate])


def validate_state(y: np.ndarray, params: RigidBody3DOF) -> Tuple[bool, str]:
    """Validate state vector for physical reasonableness

    Args:
        y: State vector
        params: System parameters

    Returns:
        (is_valid, error_message)
    """
    if len(y) != 6:
        return False, f"State vector must have 6 elements, got {len(y)}"

    Y, phi_z, theta_x, dY, dphi_z, dtheta_x = y

    # Check for NaN/inf
    if not np.all(np.isfinite(y)):
        return False, "State contains NaN or infinite values"

    # Check angle limits
    if abs(phi_z) > params.angle_limit:
        return (
            False,
            f"Roll angle {phi_z:.3f} exceeds limit +/-{params.angle_limit:.3f}",
        )

    if abs(theta_x) > params.angle_limit:
        return (
            False,
            f"Pitch angle {theta_x:.3f} exceeds limit +/-{params.angle_limit:.3f}",
        )

    # Check reasonable velocity limits (100 m/s, 50 rad/s)
    if abs(dY) > 100.0:
        return False, f"Heave velocity {dY:.3f} m/s is unreasonable"

    if abs(dphi_z) > 50.0:
        return False, f"Roll rate {dphi_z:.3f} rad/s is unreasonable"

    if abs(dtheta_x) > 50.0:
        return False, f"Pitch rate {dtheta_x:.3f} rad/s is unreasonable"

    return True, ""


# Legacy API compatibility
def rigid_body_3dof_ode(
    t: float, y: np.ndarray, params: RigidBody3DOF, system: Any = None, gas: Any = None
) -> np.ndarray:
    """Legacy wrapper for f_rhs

    This function provides backward compatibility with tests that use the old API.

    Args:
        t: Time (s)
        y: State vector [Y, phi_z, theta_x, dY, dphi_z, dtheta_x]
        params: Rigid body parameters
        system: Pneumatic system (optional)
        gas: Gas network (optional)

    Returns:
        Derivative vector dy/dt
    """
    return f_rhs(t, y, params, system, gas)


__all__ = [
    "RigidBody3DOF",
    "SuspensionPointState",
    "axis_vertical_projection",
    "assemble_forces",
    "f_rhs",
    "rigid_body_3dof_ode",  # Legacy API
    "create_initial_conditions",
    "validate_state",
]
