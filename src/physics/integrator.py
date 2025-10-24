"""
ODE integration wrapper using scipy.solve_ivp
Handles stepping, events, and fallback methods for 3-DOF dynamics
"""

import numpy as np
from scipy.integrate import solve_ivp
from typing import Dict, Any, Optional
import logging
import time
from dataclasses import dataclass

from .odes import RigidBody3DOF, f_rhs, validate_state


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

    dt_physics: float = 0.001  # Physics timestep (1ms)
    dt_render: float = 0.016  # Render timestep (60 FPS)
    max_steps_per_render: int = 50  # Max physics steps per render frame
    rtol: float = 1e-6  # Relative tolerance
    atol: float = 1e-9  # Absolute tolerance
    max_step: Optional[float] = None  # Maximum step size (None = dt/4)

    def __post_init__(self):
        if self.max_step is None:
            self.max_step = self.dt_physics / 4.0


def step_dynamics(
    y0: np.ndarray,
    t0: float,
    dt: float,
    params: RigidBody3DOF,
    system: Any,
    gas: Any,
    method: str = "Radau",
    rtol: float = 1e-6,
    atol: float = 1e-9,
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
        method: Integration method ("Radau", "BDF", "RK45")
        rtol: Relative tolerance
        atol: Absolute tolerance
        max_step: Maximum step size (None = dt/4)

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
    if max_step is None:
        max_step = dt / 4.0

    # Define RHS function with fixed parameters
    def rhs_func(t, y):
        return f_rhs(t, y, params, system, gas)

    # Integration time span
    t_span = (t0, t0 + dt)

    # Try integration with specified method
    methods_to_try = [method]

    # Add fallback methods
    if method == "Radau":
        methods_to_try.extend(["BDF", "RK45"])
    elif method == "BDF":
        methods_to_try.extend(["Radau", "RK45"])
    elif method == "RK45":
        methods_to_try.extend(["Radau", "BDF"])

    last_error = ""

    for method_attempt in methods_to_try:
        try:
            # Solve ODE
            sol = solve_ivp(
                fun=rhs_func,
                t_span=t_span,
                y0=y0,
                method=method_attempt,
                rtol=rtol,
                atol=atol,
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
    max_velocity = 10.0  # 10 m/s heave
    max_angular_velocity = 10.0  # 10 rad/s

    y_clamped[3] = np.clip(y[3], -max_velocity, max_velocity)
    y_clamped[4] = np.clip(y[4], -max_angular_velocity, max_angular_velocity)
    y_clamped[5] = np.clip(y[5], -max_angular_velocity, max_angular_velocity)

    # Remove NaN/inf
    y_clamped = np.nan_to_num(y_clamped, nan=0.0, posinf=0.0, neginf=0.0)

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

    def step_physics_fixed(self, dt_real: float) -> Dict[str, Any]:
        """Advance physics with fixed timestep, accumulating real time

        Args:
            dt_real: Real time elapsed since last call (s)

        Returns:
            Dictionary with step results and diagnostics
        """
        self.time_accumulator += dt_real
        steps_taken = 0
        results = []

        # Take fixed physics steps
        while (
            self.time_accumulator >= self.config.dt_physics
            and steps_taken < self.config.max_steps_per_render
        ):
            # Update gas system before physics step
            # TODO: Integrate with actual gas network

            # Take physics step
            result = step_dynamics(
                y0=self.y_current,
                t0=self.time_physics,
                dt=self.config.dt_physics,
                params=self.params,
                system=self.system,
                gas=self.gas,
                method="Radau",
                rtol=self.config.rtol,
                atol=self.config.atol,
                max_step=self.config.max_step,
            )

            results.append(result)

            if result.success:
                self.y_current = result.y_final
                self.time_physics = result.t_final
                self.successful_steps += 1
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
            "stats": self.get_statistics(),
        }

    def get_statistics(self) -> Dict[str, Any]:
        """Get performance statistics"""
        total_steps = self.successful_steps + self.failed_steps
        denominator = max(total_steps, 1)

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
    # Typical medium vehicle parameters
    M = 1500.0  # 1500 kg total mass
    Ix = 2000.0  # Pitch inertia (kg?m?)
    Iz = 3000.0  # Roll inertia (kg?m?)

    return RigidBody3DOF(
        M=M,
        Ix=Ix,
        Iz=Iz,
        g=9.81,
        track=1.6,
        wheelbase=3.2,
        angle_limit=0.5,
        damping_coefficient=0.1,
    )
