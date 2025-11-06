"""
Gas network management and valve flow calculations
Manages interconnections between lines, receiver, and atmosphere
"""

import logging
from dataclasses import dataclass
from typing import Dict, Optional
from .enums import Line, ThermoMode
from .gas_state import (
    LineGasState,
    TankGasState,
    iso_update,
    adiabatic_update,
    p_from_mTV,
)
from .flow import mass_flow_orifice, mass_flow_unlimited
from .system import PneumaticSystem
from src.common.units import PA_ATM, T_AMBIENT


@dataclass
class GasNetwork:
    """Complete gas network with lines, tank, and valves.

    All pressures stored in the network remain **absolute** values. Downstream
    consumers that require gauge pressure must explicitly convert using the
    utilities in :mod:`src.common.units`.
    """

    lines: Dict[Line, LineGasState]  # Four diagonal lines
    tank: TankGasState  # Receiver tank
    system_ref: PneumaticSystem  # Reference to pneumatic system
    master_isolation_open: bool = False  # Master isolation valve state
    ambient_temperature: float = T_AMBIENT  # Ambient temperature in Kelvin
    relief_min_threshold: float = 1.05 * PA_ATM
    relief_stiff_threshold: float = 1.5 * PA_ATM
    relief_safety_threshold: float = 2.0 * PA_ATM

    def __post_init__(self):
        """Validate network configuration"""
        expected_lines = {Line.A1, Line.B1, Line.A2, Line.B2}
        actual_lines = set(self.lines.keys())

        if actual_lines != expected_lines:
            raise ValueError(
                f"Network must have all 4 lines. Expected {expected_lines}, got {actual_lines}"
            )

    def compute_line_volumes(self) -> Dict[Line, float]:
        """Compute current volumes for all lines from cylinder states

        Returns:
            Dictionary mapping Line to total volume (m?)
        """
        system_volumes = self.system_ref.get_line_volumes()
        return {name: data["total_volume"] for name, data in system_volumes.items()}

    def update_pressures_with_explicit_volumes(
        self, volumes: Dict[Line, float], thermo_mode: ThermoMode
    ) -> None:
        """Update line pressures using externally supplied volumes."""

        for line_name, new_volume in volumes.items():
            line_state = self.lines[line_name]

            if thermo_mode == ThermoMode.ISOTHERMAL:
                iso_update(line_state, new_volume, self.ambient_temperature)
            elif thermo_mode == ThermoMode.ADIABATIC:
                adiabatic_update(line_state, new_volume)
            else:
                raise ValueError(f"Unknown thermo mode: {thermo_mode}")

    def update_pressures_due_to_volume(self, thermo_mode: ThermoMode):
        """Update line pressures due to volume changes from kinematics

        Args:
            thermo_mode: ISOTHERMAL or ADIABATIC process
        """
        volumes = self.compute_line_volumes()
        self.update_pressures_with_explicit_volumes(volumes, thermo_mode)

    def apply_valves_and_flows(
        self, dt: float, log: Optional[logging.Logger] = None
    ) -> Dict[str, Dict[str, float]]:
        """Apply valve flows for one time step

        Args:
            dt: Time step (s)
            log: Optional logger for diagnostics
        """
        if dt <= 0:
            raise ValueError(f"Time step must be positive: {dt}")

        # Process flows for each line
        line_flows: Dict[Line, Dict[str, float]] = {
            line_name: {"flow_atmo": 0.0, "flow_tank": 0.0}
            for line_name in self.lines.keys()
        }
        for line_name, line_state in self.lines.items():
            pneumo_line = self.system_ref.lines[line_name]

            # ATMOSPHERE -> LINE flow
            cv_atmo = pneumo_line.cv_atmo
            if cv_atmo.is_open(PA_ATM, line_state.p):
                m_dot_atmo = mass_flow_orifice(
                    PA_ATM,
                    self.ambient_temperature,
                    line_state.p,
                    line_state.T,
                    cv_atmo.d_eq,
                )

                # Add mass to line
                mass_added = m_dot_atmo * dt
                self._add_mass_to_line(line_state, mass_added, self.ambient_temperature)
                line_flows[line_name]["flow_atmo"] = float(m_dot_atmo)

                if log:
                    log.debug(
                        f"Atmo->Line {line_name.value}: +{mass_added:.6f}kg, m_dot={m_dot_atmo:.6f}kg/s"
                    )

            # LINE -> TANK flow
            cv_tank = pneumo_line.cv_tank
            if cv_tank.is_open(line_state.p, self.tank.p):
                m_dot_tank = mass_flow_orifice(
                    line_state.p, line_state.T, self.tank.p, self.tank.T, cv_tank.d_eq
                )

                # Transfer mass from line to tank without leaving artificial residue
                mass_requested = m_dot_tank * dt
                actual_mass_transferred = self._transfer_mass_line_to_tank(
                    line_state, mass_requested
                )
                if actual_mass_transferred > 0.0:
                    line_flows[line_name]["flow_tank"] = float(
                        actual_mass_transferred / dt
                    )
                else:
                    line_flows[line_name]["flow_tank"] = 0.0

                if log:
                    log.debug(
                        f"Line->Tank {line_name.value}: -{actual_mass_transferred:.6f}kg, m_dot={line_flows[line_name]['flow_tank']:.6f}kg/s"
                    )

        # Process receiver relief valves
        relief_flows = self._apply_receiver_relief_valves(dt, log)

        return {"lines": line_flows, "relief": relief_flows}

    def _add_mass_to_line(
        self, line_state: LineGasState, mass_added: float, T_inlet: float
    ):
        """Add mass to line with temperature mixing

        Args:
            line_state: Line to add mass to
            mass_added: Mass to add (kg)
            T_inlet: Temperature of incoming gas (K)
        """
        if mass_added <= 0:
            return

        # Temperature mixing (mass-weighted average)
        old_mass = line_state.m
        new_total_mass = old_mass + mass_added

        if new_total_mass > 0:
            line_state.T = (
                old_mass * line_state.T + mass_added * T_inlet
            ) / new_total_mass

        line_state.m = new_total_mass

        # Recalculate pressure
        line_state.p = p_from_mTV(line_state.m, line_state.T, line_state.V_curr)

    def _transfer_mass_line_to_tank(
        self, line_state: LineGasState, mass_requested: float
    ) -> float:
        """Transfer mass from line to tank with temperature mixing.

        Returns the actual mass moved, which may be lower than the requested
        amount when the line does not contain enough gas.
        """

        if mass_requested <= 0.0:
            return 0.0

        if line_state.m <= 0.0:
            return 0.0

        actual_transfer = min(mass_requested, line_state.m)
        line_state.m = max(line_state.m - actual_transfer, 0.0)

        old_tank_mass = self.tank.m
        new_tank_mass = old_tank_mass + actual_transfer

        if new_tank_mass > 0.0:
            self.tank.T = (
                old_tank_mass * self.tank.T + actual_transfer * line_state.T
            ) / new_tank_mass

        self.tank.m = new_tank_mass

        if line_state.m > 0.0:
            line_state.p = p_from_mTV(line_state.m, line_state.T, line_state.V_curr)
        else:
            line_state.p = 0.0

        if self.tank.m > 0.0:
            self.tank.p = p_from_mTV(self.tank.m, self.tank.T, self.tank.V)
        else:
            self.tank.p = 0.0

        return actual_transfer

    def _apply_receiver_relief_valves(
        self, dt: float, log: Optional[logging.Logger] = None
    ) -> Dict[str, float]:
        """Apply receiver relief valve flows

        Args:
            dt: Time step (s)
            log: Optional logger
        """
        # Get relief valves from system (we'll need to add these to the system)
        # For now, use default thresholds

        p_min_threshold = self.relief_min_threshold
        p_stiff_threshold = self.relief_stiff_threshold
        p_safety_threshold = self.relief_safety_threshold

        d_eq_min_bleed = 1.0e-3  # 1mm throttle
        d_eq_stiff_bleed = 1.0e-3  # 1mm throttle

        total_mass_out = 0.0
        relief_log = {"flow_min": 0.0, "flow_stiff": 0.0, "flow_safety": 0.0}

        # MIN_PRESS relief (maintain minimum pressure)
        if self.tank.p > p_min_threshold:
            m_dot_min = mass_flow_orifice(
                self.tank.p,
                self.tank.T,
                PA_ATM,
                self.ambient_temperature,
                d_eq_min_bleed,
            )
            mass_out_min = m_dot_min * dt
            total_mass_out += mass_out_min
            relief_log["flow_min"] = float(m_dot_min)

            if log:
                log.debug(
                    f"MIN_PRESS relief: -{mass_out_min:.6f}kg, m_dot={m_dot_min:.6f}kg/s"
                )

        # STIFFNESS relief
        if self.tank.p > p_stiff_threshold:
            m_dot_stiff = mass_flow_orifice(
                self.tank.p,
                self.tank.T,
                PA_ATM,
                self.ambient_temperature,
                d_eq_stiff_bleed,
            )
            mass_out_stiff = m_dot_stiff * dt
            total_mass_out += mass_out_stiff
            relief_log["flow_stiff"] = float(m_dot_stiff)

            if log:
                log.debug(
                    f"STIFFNESS relief: -{mass_out_stiff:.6f}kg, m_dot={m_dot_stiff:.6f}kg/s"
                )

        # SAFETY relief (unlimited flow)
        if self.tank.p > p_safety_threshold:
            m_dot_safety = mass_flow_unlimited(self.tank.p, self.tank.T)
            mass_out_safety = m_dot_safety * dt
            total_mass_out += mass_out_safety
            relief_log["flow_safety"] = float(m_dot_safety)

            if log:
                log.debug(
                    f"SAFETY relief: -{mass_out_safety:.6f}kg, m_dot={m_dot_safety:.6f}kg/s"
                )

        # Remove total mass from tank (prevent negative mass)
        if total_mass_out > 0:
            self.tank.m = max(0.0, self.tank.m - total_mass_out)

            # Recalculate pressure
            if self.tank.m > 0:
                self.tank.p = p_from_mTV(self.tank.m, self.tank.T, self.tank.V)
            else:
                self.tank.p = 0.0

        return relief_log

    def enforce_master_isolation(self, log: Optional[logging.Logger] = None):
        """Enforce master isolation when enabled - equalize all line pressures

        Args:
            log: Optional logger
        """
        if not self.master_isolation_open:
            return

        # Calculate total mass and volume
        total_mass = sum(line.m for line in self.lines.values())

        volumes = self.compute_line_volumes()
        total_volume = sum(volumes.values())

        if total_mass <= 0 or total_volume <= 0:
            return

        # Calculate mass-weighted average temperature
        total_enthalpy = sum(line.m * line.T for line in self.lines.values())
        avg_temperature = (
            total_enthalpy / total_mass if total_mass > 0 else self.ambient_temperature
        )

        # Calculate equalized pressure
        equalized_pressure = p_from_mTV(total_mass, avg_temperature, total_volume)

        # Redistribute mass to each line proportional to its volume
        for line_name, line_state in self.lines.items():
            line_volume = volumes[line_name]
            line_mass_fraction = line_volume / total_volume

            line_state.m = total_mass * line_mass_fraction
            line_state.T = avg_temperature
            line_state.p = equalized_pressure
            line_state.V_curr = line_volume

        if log:
            log.debug(
                f"Master isolation: equalized p={equalized_pressure:.0f}Pa, T={avg_temperature:.1f}K"
            )

    def validate_invariants(self) -> Dict[str, any]:
        """Validate all gas network invariants

        Returns:
            Dictionary with validation results
        """
        errors = []
        warnings = []

        # Check line states
        for line_name, line_state in self.lines.items():
            if line_state.m < 0:
                errors.append(
                    f"Line {line_name.value} has negative mass: {line_state.m}"
                )
            if line_state.T <= 0:
                errors.append(
                    f"Line {line_name.value} has non-positive temperature: {line_state.T}"
                )
            if line_state.p < 0:
                errors.append(
                    f"Line {line_name.value} has negative pressure: {line_state.p}"
                )
            if line_state.V_curr <= 0:
                errors.append(
                    f"Line {line_name.value} has non-positive volume: {line_state.V_curr}"
                )

        # Check tank state
        if self.tank.m < 0:
            errors.append(f"Tank has negative mass: {self.tank.m}")
        if self.tank.T <= 0:
            errors.append(f"Tank has non-positive temperature: {self.tank.T}")
        if self.tank.p < 0:
            errors.append(f"Tank has negative pressure: {self.tank.p}")
        if self.tank.V <= 0:
            errors.append(f"Tank has non-positive volume: {self.tank.V}")

        # Check master isolation consistency
        if self.master_isolation_open:
            pressures = [line.p for line in self.lines.values()]
            if (
                len(set(f"{p:.0f}" for p in pressures)) > 1
            ):  # Round to Pa for comparison
                max_p_diff = max(pressures) - min(pressures)
                if max_p_diff > 1000:  # > 1000 Pa difference
                    warnings.append(
                        f"Master isolation enabled but pressures not equalized: diff={max_p_diff:.0f}Pa"
                    )

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}
