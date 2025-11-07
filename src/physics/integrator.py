"""
ODE integration wrapper using scipy.solve_ivp
Handles stepping, events, and fallback methods for 3-DOF dynamics
"""

import logging
import math
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from scipy.integrate import solve_ivp

from config.constants import (
    get_current_section,
    get_physics_integrator_constants,
    get_physics_rigid_body_constants,
    get_simulation_settings,
)
from config.constants import refresh_cache as refresh_settings_cache
from src.core.settings_validation import SettingsValidationError
from src.pneumo.enums import ThermoMode, Wheel

from .odes import RigidBody3DOF, f_rhs, validate_state


def _require_number(mapping: Mapping[str, Any], key: str, context: str) -> float:
    if key not in mapping:
        raise SettingsValidationError(f"В секции {context} отсутствует параметр {key}")
    value = mapping[key]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SettingsValidationError(f"Параметр {key} в {context} должен быть числом")
    return float(value)


def _require_int(mapping: Mapping[str, Any], key: str, context: str) -> int:
    value = _require_number(mapping, key, context)
    if not float(value).is_integer():
        raise SettingsValidationError(
            f"Параметр {key} в {context} должен быть целым числом"
        )
    return int(value)


def _require_bool(mapping: Mapping[str, Any], key: str, context: str) -> bool:
    if key not in mapping:
        raise SettingsValidationError(f"В секции {context} отсутствует параметр {key}")
    value = mapping[key]
    if not isinstance(value, bool):
        raise SettingsValidationError(f"Параметр {key} в {context} должен быть булевым")
    return value


def _require_string(mapping: Mapping[str, Any], key: str, context: str) -> str:
    if key not in mapping:
        raise SettingsValidationError(f"В секции {context} отсутствует параметр {key}")
    value = mapping[key]
    if not isinstance(value, str):
        raise SettingsValidationError(f"Параметр {key} в {context} должен быть строкой")
    return value


def _require_string_list(
    mapping: Mapping[str, Any], key: str, context: str
) -> list[str]:
    if key not in mapping:
        raise SettingsValidationError(f"В секции {context} отсутствует параметр {key}")
    value = mapping[key]
    if not isinstance(value, list) or not value:
        raise SettingsValidationError(
            f"Параметр {key} в {context} должен быть непустым списком строк"
        )
    result: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise SettingsValidationError(
                f"Все значения {context}.{key} должны быть строками"
            )
        result.append(item)
    return result


def _load_loop_defaults() -> dict[str, Any]:
    integrator = get_physics_integrator_constants()

    solver = integrator.get("solver")
    if not isinstance(solver, Mapping):
        raise SettingsValidationError(
            "Секция constants.physics.integrator.solver должна быть объектом"
        )
    loop = integrator.get("loop")
    if not isinstance(loop, Mapping):
        raise SettingsValidationError(
            "Секция constants.physics.integrator.loop должна быть объектом"
        )

    solver_context = "constants.physics.integrator.solver"
    loop_context = "constants.physics.integrator.loop"

    simulation = get_simulation_settings()
    sim_context = "current.simulation"
    pneumo = get_current_section("pneumatic")
    pneumo_context = "current.pneumatic"

    dt_physics = _require_number(simulation, "physics_dt", sim_context)
    vsync_hz = _require_number(simulation, "render_vsync_hz", sim_context)
    if vsync_hz <= 0.0:
        raise SettingsValidationError(
            "Параметр render_vsync_hz в current.simulation должен быть > 0"
        )
    max_step_divisor = _require_number(solver, "max_step_divisor", solver_context)
    if max_step_divisor <= 0.0:
        raise SettingsValidationError(
            "Параметр max_step_divisor в constants.physics.integrator.solver должен быть > 0"
        )

    thermo_name = _require_string(pneumo, "thermo_mode", pneumo_context)
    try:
        thermo_mode = ThermoMode[thermo_name.upper()]
    except KeyError as exc:
        raise SettingsValidationError(
            "Неизвестное значение thermo_mode в current.pneumatic"
        ) from exc

    clip_min = _require_number(loop, "lever_ratio_clip_min", loop_context)
    clip_max = _require_number(loop, "lever_ratio_clip_max", loop_context)
    if clip_min >= clip_max:
        raise SettingsValidationError(
            "Параметры lever_ratio_clip_min/max в constants.physics.integrator.loop"
            " должны задавать возрастающий диапазон"
        )

    max_linear_velocity = _require_number(loop, "max_linear_velocity_m_s", loop_context)
    if max_linear_velocity <= 0.0:
        raise SettingsValidationError(
            "Параметр max_linear_velocity_m_s в constants.physics.integrator.loop"
            " должен быть больше 0"
        )

    max_angular_velocity = _require_number(
        loop, "max_angular_velocity_rad_s", loop_context
    )
    if max_angular_velocity <= 0.0:
        raise SettingsValidationError(
            "Параметр max_angular_velocity_rad_s в constants.physics.integrатор.loop"
            " должен быть больше 0"
        )

    return {
        "dt_physics": dt_physics,
        "dt_render": 1.0 / vsync_hz,
        "max_steps_per_render": _require_int(
            loop, "max_steps_per_render", loop_context
        ),
        "solver_primary": _require_string(solver, "primary_method", solver_context),
        "solver_fallbacks": _require_string_list(
            solver, "fallback_methods", solver_context
        ),
        "solver_rtol": _require_number(solver, "relative_tolerance", solver_context),
        "solver_atol": _require_number(solver, "absolute_tolerance", solver_context),
        "solver_max_step_divisor": max_step_divisor,
        "lever_ratio_clip_min": clip_min,
        "lever_ratio_clip_max": clip_max,
        "statistics_min_total_steps": _require_int(
            loop, "statistics_min_total_steps", loop_context
        ),
        "max_linear_velocity_m_s": max_linear_velocity,
        "max_angular_velocity_rad_s": max_angular_velocity,
        "nan_replacement_value": _require_number(
            loop, "nan_replacement_value", loop_context
        ),
        "posinf_replacement_value": _require_number(
            loop, "posinf_replacement_value", loop_context
        ),
        "neginf_replacement_value": _require_number(
            loop, "neginf_replacement_value", loop_context
        ),
        "max_steps_per_frame": _require_int(
            simulation, "max_steps_per_frame", sim_context
        ),
        "max_frame_time": _require_number(simulation, "max_frame_time", sim_context),
        "thermo_mode": thermo_mode,
        "master_isolation_open": _require_bool(
            pneumo, "master_isolation_open", pneumo_context
        ),
    }


_LOOP_DEFAULTS: dict[str, Any] = _load_loop_defaults()


def refresh_physics_loop_defaults() -> None:
    """Reload cached loop defaults from the settings file."""

    global _LOOP_DEFAULTS
    refresh_settings_cache()
    _LOOP_DEFAULTS = _load_loop_defaults()


@dataclass
class IntegrationResult:
    """Result of integration step"""

    success: bool
    y_final: np.ndarray
    t_final: float
    message: str
    method_used: str
    n_evaluations: int
    solve_time: float


@dataclass
class PhysicsLoopConfig:
    """Configuration for physics loop"""

    dt_physics: float = field(
        default_factory=lambda: float(_LOOP_DEFAULTS["dt_physics"])
    )
    dt_render: float = field(default_factory=lambda: float(_LOOP_DEFAULTS["dt_render"]))
    max_steps_per_render: int = field(
        default_factory=lambda: int(_LOOP_DEFAULTS["max_steps_per_render"])
    )
    solver_primary: str = field(
        default_factory=lambda: str(_LOOP_DEFAULTS["solver_primary"])
    )
    solver_fallbacks: tuple[str, ...] = field(
        default_factory=lambda: tuple(_LOOP_DEFAULTS["solver_fallbacks"])
    )
    rtol: float = field(default_factory=lambda: float(_LOOP_DEFAULTS["solver_rtol"]))
    atol: float = field(default_factory=lambda: float(_LOOP_DEFAULTS["solver_atol"]))
    solver_max_step_divisor: float = field(
        default_factory=lambda: float(_LOOP_DEFAULTS["solver_max_step_divisor"])
    )
    max_step: Optional[float] = None
    thermo_mode: ThermoMode = field(
        default_factory=lambda: _LOOP_DEFAULTS["thermo_mode"]
    )
    master_isolation_open: bool = field(
        default_factory=lambda: bool(_LOOP_DEFAULTS["master_isolation_open"])
    )

    def __post_init__(self):
        if self.solver_max_step_divisor <= 0:
            raise ValueError("solver_max_step_divisor must be positive")
        if not self.solver_fallbacks:
            raise ValueError("At least one fallback solver must be configured")

        if self.max_step is None:
            self.max_step = self.dt_physics / self.solver_max_step_divisor
        elif self.max_step <= 0:
            raise ValueError("max_step must be positive")
        if isinstance(self.thermo_mode, str):
            try:
                self.thermo_mode = ThermoMode[self.thermo_mode.upper()]
            except KeyError as exc:
                raise ValueError(f"Unknown thermo_mode '{self.thermo_mode}'") from exc


def step_dynamics(
    y0: np.ndarray,
    t0: float,
    dt: float,
    params: RigidBody3DOF,
    system: Any,
    gas: Any,
    method: Optional[str] = None,
    rtol: Optional[float] = None,
    atol: Optional[float] = None,
    max_step: Optional[float] = None,
) -> IntegrationResult:
    """Perform one integration step of 3-DOF dynamics

    Args:
        y0: Initial state vector [Y, ?z, ?x, dY, d?z, d?x]
        t0: Initial time (s)
        dt: Time step (s)
        params: Rigid body parameters
        system: Pneumatic system
        gas: Gas network
        method: Integration method (defaults to settings primary solver)
        rtol: Relative tolerance (defaults to settings value)
        atol: Absolute tolerance (defaults to settings value)
        max_step: Maximum step size (defaults to dt / max_step_divisor)

    Returns:
        IntegrationResult with final state and diagnostics
    """
    start_time = time.perf_counter()

    # Validate initial state
    is_valid, error_msg = validate_state(y0, params)
    if not is_valid:
        return IntegrationResult(
            success=False,
            y_final=y0,
            t_final=t0,
            message=f"Invalid initial state: {error_msg}",
            method_used=method,
            n_evaluations=0,
            solve_time=0.0,
        )

    # Set default max_step
    method_to_use = method or _LOOP_DEFAULTS["solver_primary"]
    explicit_method_requested = method is not None
    rtol_value = rtol if rtol is not None else _LOOP_DEFAULTS["solver_rtol"]
    atol_value = atol if atol is not None else _LOOP_DEFAULTS["solver_atol"]

    if max_step is None:
        max_step = dt / _LOOP_DEFAULTS["solver_max_step_divisor"]

    # Define RHS function with fixed parameters
    def rhs_func(t, y):
        return f_rhs(t, y, params, system, gas)

    # Integration time span
    t_span = (t0, t0 + dt)

    # Try integration with specified method
    methods_to_try = [method_to_use]
    if not explicit_method_requested:
        for fallback in _LOOP_DEFAULTS["solver_fallbacks"]:
            if fallback not in methods_to_try:
                methods_to_try.append(fallback)

    last_error = ""

    for method_attempt in methods_to_try:
        try:
            # Solve ODE
            sol = solve_ivp(
                fun=rhs_func,
                t_span=t_span,
                y0=y0,
                method=method_attempt,
                rtol=rtol_value,
                atol=atol_value,
                max_step=max_step,
                dense_output=False,
                vectorized=False,
            )

            solve_time = time.perf_counter() - start_time

            if sol.success:
                y_final = sol.y[:, -1]  # Final state

                # Validate final state
                is_valid, error_msg = validate_state(y_final, params)
                if not is_valid:
                    # Clamp to valid ranges if possible
                    y_final = clamp_state(y_final, params)

                    # Re-validate
                    is_valid, error_msg = validate_state(y_final, params)
                    if not is_valid:
                        last_error = f"Final state invalid: {error_msg}"
                        continue

                return IntegrationResult(
                    success=True,
                    y_final=y_final,
                    t_final=sol.t[-1],
                    message=f"Integration successful with {method_attempt}",
                    method_used=method_attempt,
                    n_evaluations=sol.nfev,
                    solve_time=solve_time,
                )

            else:
                last_error = f"Method {method_attempt} failed: {sol.message}"

        except Exception as e:
            last_error = f"Method {method_attempt} raised exception: {str(e)}"
            continue

    # All methods failed
    solve_time = time.perf_counter() - start_time
    return IntegrationResult(
        success=False,
        y_final=y0,  # Return original state
        t_final=t0,
        message=f"All integration methods failed. Last error: {last_error}",
        method_used="FAILED",
        n_evaluations=0,
        solve_time=solve_time,
    )


def clamp_state(y: np.ndarray, params: RigidBody3DOF) -> np.ndarray:
    """Clamp state vector to valid ranges

    Args:
        y: State vector [Y, ?z, ?x, dY, d?z, d?x]
        params: System parameters with limits

    Returns:
        Clamped state vector
    """
    y_clamped = y.copy()

    # Clamp angles to limits
    y_clamped[1] = np.clip(y[1], -params.angle_limit, params.angle_limit)
    y_clamped[2] = np.clip(y[2], -params.angle_limit, params.angle_limit)

    # Clamp velocities to reasonable ranges
    max_velocity = float(_LOOP_DEFAULTS["max_linear_velocity_m_s"])
    max_angular_velocity = float(_LOOP_DEFAULTS["max_angular_velocity_rad_s"])
    nan_replacement = float(_LOOP_DEFAULTS["nan_replacement_value"])
    posinf_replacement = float(_LOOP_DEFAULTS["posinf_replacement_value"])
    neginf_replacement = float(_LOOP_DEFAULTS["neginf_replacement_value"])

    y_clamped[3] = np.clip(y[3], -max_velocity, max_velocity)
    y_clamped[4] = np.clip(y[4], -max_angular_velocity, max_angular_velocity)
    y_clamped[5] = np.clip(y[5], -max_angular_velocity, max_angular_velocity)

    # Remove NaN/inf
    y_clamped = np.nan_to_num(
        y_clamped,
        nan=nan_replacement,
        posinf=posinf_replacement,
        neginf=neginf_replacement,
    )

    return y_clamped


class PhysicsLoop:
    """Physics simulation loop with fixed timestep and render sync."""

    def __init__(
        self,
        config: PhysicsLoopConfig,
        params: RigidBody3DOF,
        system: Any,
        gas: Any,
    ):
        self.config = config
        self.params = params
        self.system = system
        self.gas = gas
        self.thermo_mode = config.thermo_mode
        self.master_isolation_open = config.master_isolation_open

        # State
        self.time_physics = 0.0
        self.time_render = 0.0
        self.time_accumulator = 0.0
        self.step_count = 0

        # Statistics
        self.successful_steps = 0
        self.failed_steps = 0
        self.total_solve_time = 0.0

        # Logging
        self.logger = logging.getLogger(__name__)

    def reset(self, y0: np.ndarray, t0: float = 0.0):
        """Reset physics loop to initial conditions"""
        self.y_current = y0.copy()
        self.time_physics = t0
        self.time_render = t0
        self.time_accumulator = 0.0
        self.step_count = 0
        self.successful_steps = 0
        self.failed_steps = 0
        self.total_solve_time = 0.0
        try:
            self._update_pneumatics_from_state(self.y_current, apply_flows=False)
        except Exception:
            # Surface the error to caller to avoid masking configuration issues
            raise

    def step_physics_fixed(self, dt_real: float) -> dict[str, Any]:
        """Advance physics with fixed timestep, accumulating real time

        Args:
            dt_real: Real time elapsed since last call (s)

        Returns:
            Dictionary with step results and diagnostics
        """
        self.time_accumulator += dt_real
        steps_taken = 0
        results: list[IntegrationResult] = []
        gas_logs: list[dict[str, Any]] = []

        # Take fixed physics steps
        while (
            self.time_accumulator >= self.config.dt_physics
            and steps_taken < self.config.max_steps_per_render
        ):
            flow_log = self._update_pneumatics_from_state(
                self.y_current, apply_flows=True
            )
            if flow_log is not None:
                gas_logs.append(flow_log)

            # Take physics step
            result = step_dynamics(
                y0=self.y_current,
                t0=self.time_physics,
                dt=self.config.dt_physics,
                params=self.params,
                system=self.system,
                gas=self.gas,
                method=self.config.solver_primary,
                rtol=self.config.rtol,
                atol=self.config.atol,
                max_step=self.config.max_step,
            )

            results.append(result)

            if result.success:
                self.y_current = result.y_final
                self.time_physics = result.t_final
                self.successful_steps += 1
                # Synchronise pneumatic state with the new configuration
                self._update_pneumatics_from_state(self.y_current, apply_flows=False)
            else:
                self.failed_steps += 1
                self.logger.warning("Physics step failed: %s", result.message)
                # Keep state but advance time to avoid stalls
                self.time_physics += self.config.dt_physics

            self.total_solve_time += result.solve_time
            self.time_accumulator -= self.config.dt_physics
            steps_taken += 1
            self.step_count += 1

        # Check if render update is due
        render_due = (self.time_physics - self.time_render) >= self.config.dt_render
        if render_due:
            self.time_render = self.time_physics

        return {
            "steps_taken": steps_taken,
            "physics_time": self.time_physics,
            "render_due": render_due,
            "y_current": self.y_current.copy(),
            "results": results,
            "gas_flows": gas_logs,
            "stats": self.get_statistics(),
        }

    def _update_pneumatics_from_state(
        self, state: np.ndarray, *, apply_flows: bool
    ) -> dict[str, Any] | None:
        """Project body state to pneumatic system and gas network."""

        if self.system is None or self.gas is None:
            return None

        lever_angles = self._compute_lever_angles(state)
        if lever_angles:
            self.system.update_system_from_lever_angles(lever_angles)

        line_volumes = self.system.get_line_volumes()
        for line_name, volume_info in line_volumes.items():
            total_volume = float(volume_info.get("total_volume", 0.0))
            if total_volume <= 0:
                raise ValueError(
                    f"Computed non-positive volume for line {line_name}: {total_volume}"
                )
            gas_state = self.gas.lines.get(line_name)
            if gas_state is None:
                raise KeyError(f"Gas network missing state for line {line_name}")
            gas_state.set_volume(total_volume)

        self.gas.master_isolation_open = self.master_isolation_open
        self.gas.update_pressures_due_to_volume(self.thermo_mode)

        if not apply_flows:
            return None

        flow_log = self.gas.apply_valves_and_flows(self.config.dt_physics, self.logger)
        self.gas.enforce_master_isolation(self.logger, dt=self.config.dt_physics)
        return flow_log

    def _compute_lever_angles(self, state: np.ndarray) -> dict[Wheel, float]:
        """Derive lever angles for all wheels from the rigid-body state."""

        if not hasattr(self.system, "cylinders"):
            return {}

        attachments = getattr(self.params, "attachment_points", {})
        Y, phi_z, theta_x = state[:3]
        angles: dict[Wheel, float] = {}

        for wheel_enum, cylinder in self.system.cylinders.items():
            if not isinstance(wheel_enum, Wheel):
                try:
                    wheel_enum = Wheel[wheel_enum]
                except Exception as exc:  # pragma: no cover - defensive
                    raise TypeError(
                        f"Unsupported wheel key type: {wheel_enum!r}"
                    ) from exc

            attach_key = wheel_enum.name
            x_i, z_i = attachments.get(attach_key, (0.0, 0.0))
            displacement = Y + x_i * phi_z + z_i * theta_x

            lever = getattr(cylinder.spec, "lever_geom", None)
            lever_length = getattr(lever, "L_lever", None)
            if lever_length is None or lever_length <= 0:
                raise ValueError(
                    f"Cylinder for wheel {wheel_enum.value} has invalid lever geometry"
                )

            ratio = displacement / lever_length
            ratio = float(
                np.clip(
                    ratio,
                    _LOOP_DEFAULTS["lever_ratio_clip_min"],
                    _LOOP_DEFAULTS["lever_ratio_clip_max"],
                )
            )
            angles[wheel_enum] = math.asin(ratio)

        return angles

    def get_statistics(self) -> dict[str, Any]:
        """Get performance statistics"""
        total_steps = self.successful_steps + self.failed_steps
        denominator = max(total_steps, _LOOP_DEFAULTS["statistics_min_total_steps"])

        return {
            "total_steps": total_steps,
            "successful_steps": self.successful_steps,
            "failed_steps": self.failed_steps,
            "success_rate": self.successful_steps / denominator,
            "average_solve_time": self.total_solve_time / denominator,
            "physics_frequency": 1.0 / self.config.dt_physics,
            "render_frequency": 1.0 / self.config.dt_render,
        }


def create_default_rigid_body() -> RigidBody3DOF:
    """Create default rigid body parameters for testing

    Returns:
        RigidBody3DOF with typical vehicle parameters
    """
    defaults = get_physics_rigid_body_constants()
    context = "constants.physics.rigid_body"

    attachments_raw = defaults.get("attachment_points_m")
    if not isinstance(attachments_raw, Mapping):
        raise SettingsValidationError(
            "Секция constants.physics.rigid_body.attachment_points_m должна быть объектом"
        )

    attachments: dict[str, tuple[float, float]] = {}
    for wheel, entry in attachments_raw.items():
        if not isinstance(entry, Mapping):
            raise SettingsValidationError(
                "Каждый элемент attachment_points_m должен быть объектом с координатами"
            )
        wheel_context = f"{context}.attachment_points_m.{wheel}"
        attachments[wheel] = (
            _require_number(entry, "x_m", wheel_context),
            _require_number(entry, "z_m", wheel_context),
        )

    return RigidBody3DOF(
        M=_require_number(defaults, "default_mass_kg", context),
        Ix=_require_number(defaults, "default_inertia_pitch_kg_m2", context),
        Iz=_require_number(defaults, "default_inertia_roll_kg_m2", context),
        g=_require_number(defaults, "gravity_m_s2", context),
        attachment_points=attachments,
        track=_require_number(defaults, "track_width_m", context),
        wheelbase=_require_number(defaults, "wheelbase_m", context),
        angle_limit=_require_number(defaults, "angle_limit_rad", context),
        damping_coefficient=_require_number(defaults, "damping_coefficient", context),
        static_load_tolerance=_require_number(
            defaults, "static_load_tolerance", context
        ),
        load_sum_tolerance_scale=_require_number(
            defaults, "load_sum_tolerance_scale", context
        ),
        load_sum_min_reference=_require_number(
            defaults, "load_sum_min_reference", context
        ),
    )
