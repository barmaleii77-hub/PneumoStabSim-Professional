"""
Discrete time stepping for gas simulation
Advances gas state without body dynamics (no ODE solver)
"""

import logging
from typing import Optional, Dict
from .network import GasNetwork
from .system import PneumaticSystem
from .enums import ThermoMode, Line


def advance_gas(
    dt: float,
    system: PneumaticSystem,
    net: GasNetwork,
    thermo_mode: ThermoMode,
    log: Optional[logging.Logger] = None,
    volumes_override: Optional[Dict[Line, float]] = None,
):
    """Advance gas simulation by one time step

    Args:
        dt: Time step (s)
        system: Pneumatic system (provides current cylinder positions)
        net: Gas network (updated in-place)
        thermo_mode: Thermodynamic process mode
        log: Optional logger for diagnostics
        volumes_override: Optional mapping of line volumes to use instead of
            querying the pneumatic system (e.g. to account for stop penetration)
    """
    if dt <= 0:
        raise ValueError(f"Time step must be positive: {dt}")

    if log:
        log.debug(f"=== Gas step: dt={dt:.4f}s, mode={thermo_mode.value} ===")

    # Step 1: Update pressures due to volume changes from kinematics
    if log:
        log.debug("Step 1: Updating pressures from volume changes")

    if volumes_override is not None:
        net.update_pressures_with_explicit_volumes(volumes_override, thermo_mode)
    else:
        net.update_pressures_due_to_volume(thermo_mode)

    if log:
        for line_name, line_state in net.lines.items():
            log.debug(
                f"  {line_name.value}: V={line_state.V_curr:.6f}m?, p={line_state.p:.0f}Pa, T={line_state.T:.1f}K"
            )

    # Step 2: Apply valve flows and mass transfer
    if log:
        log.debug("Step 2: Applying valve flows")

    net.apply_valves_and_flows(dt, log)

    # Step 3: Enforce master isolation if enabled
    if net.master_isolation_open:
        if log:
            log.debug("Step 3: Enforcing master isolation")
        net.enforce_master_isolation(log, dt=dt)

    # Step 4: Final state logging
    if log:
        log.debug("Final state:")
        log.debug(
            f"  Tank: V={net.tank.V:.6f}m?, p={net.tank.p:.0f}Pa, T={net.tank.T:.1f}K, m={net.tank.m:.6f}kg"
        )
        for line_name, line_state in net.lines.items():
            log.debug(
                f"  {line_name.value}: p={line_state.p:.0f}Pa, T={line_state.T:.1f}K, m={line_state.m:.6f}kg"
            )


def run_gas_simulation(
    total_time: float,
    dt: float,
    system: PneumaticSystem,
    net: GasNetwork,
    thermo_mode: ThermoMode,
    log_interval: Optional[float] = None,
    log: Optional[logging.Logger] = None,
) -> dict[str, list]:
    """Run gas simulation for specified duration

    Args:
        total_time: Total simulation time (s)
        dt: Time step (s)
        system: Pneumatic system
        net: Gas network
        thermo_mode: Thermodynamic process mode
        log_interval: Logging interval (s), None for no periodic logging
        log: Optional logger

    Returns:
        Dictionary with time history of key variables
    """
    if total_time <= 0:
        raise ValueError(f"Total time must be positive: {total_time}")
    if dt <= 0 or dt > total_time:
        raise ValueError(f"Invalid time step: {dt} (total_time: {total_time})")

    # Initialize history storage
    history = {
        "time": [],
        "tank_pressure": [],
        "tank_mass": [],
        "line_pressures": {line: [] for line in net.lines.keys()},
        "line_masses": {line: [] for line in net.lines.keys()},
    }

    current_time = 0.0
    step_count = 0
    last_log_time = 0.0

    if log:
        log.info(
            f"Starting gas simulation: T={total_time}s, dt={dt}s, steps={int(total_time / dt)}"
        )

    while current_time < total_time:
        # Adjust final step to not overshoot
        actual_dt = min(dt, total_time - current_time)

        # Advance gas state
        advance_gas(
            actual_dt,
            system,
            net,
            thermo_mode,
            (
                log
                if (
                    log_interval is None or current_time - last_log_time >= log_interval
                )
                else None
            ),
        )

        current_time += actual_dt
        step_count += 1

        # Store history
        history["time"].append(current_time)
        history["tank_pressure"].append(net.tank.p)
        history["tank_mass"].append(net.tank.m)

        for line_name, line_state in net.lines.items():
            history["line_pressures"][line_name].append(line_state.p)
            history["line_masses"][line_name].append(line_state.m)

        # Periodic logging
        if (
            log
            and log_interval is not None
            and (current_time - last_log_time) >= log_interval
        ):
            log.info(
                f"t={current_time:.3f}s: Tank p={net.tank.p:.0f}Pa, Lines p=[{', '.join(f'{line.p:.0f}' for line in net.lines.values())}]Pa"
            )
            last_log_time = current_time

    if log:
        log.info(
            f"Gas simulation completed: {step_count} steps, final_time={current_time:.3f}s"
        )

        # Validate final state
        validation = net.validate_invariants()
        if not validation["is_valid"]:
            log.warning("Final state validation failed:")
            for error in validation["errors"]:
                log.warning(f"  ERROR: {error}")

    return history
