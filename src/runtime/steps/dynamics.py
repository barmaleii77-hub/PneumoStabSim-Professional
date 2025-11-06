"""Rigid-body integration helper for physics step execution."""

from __future__ import annotations

from src.physics.integrator import step_dynamics

from .context import PhysicsStepState


def integrate_body(state: PhysicsStepState) -> None:
    """Integrate rigid-body dynamics for the current step."""

    if state.rigid_body is None:
        return

    try:
        result = step_dynamics(
            y0=state.physics_state,
            t0=state.simulation_time,
            dt=state.dt,
            params=state.rigid_body,
            system=state.pneumatic_system,
            gas=state.gas_network,
            method="Radau",
        )
    except Exception as exc:  # pragma: no cover - defensive logging
        state.performance.integration_failures += 1
        state.logger.error(f"Integration error: {exc}")
        return

    if not result.success:
        state.performance.integration_failures += 1
        state.logger.warning(f"Integration failed: {result.message}")
        return

    prev_vel = state.physics_state[3:6].copy()
    state.physics_state = result.y_final
    velocities = state.physics_state[3:6]
    if state.dt > 0:
        state.latest_frame_accel = (velocities - prev_vel) / state.dt
    state.prev_frame_velocities = velocities.copy()
