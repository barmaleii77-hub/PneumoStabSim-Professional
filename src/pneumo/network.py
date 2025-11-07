"""
Gas network management and valve flow calculations
Manages interconnections between lines, receiver, and atmosphere
"""

import logging
from dataclasses import dataclass, field
from functools import lru_cache
from collections.abc import Mapping, Sequence
from .enums import Line, ThermoMode
from .gas_state import (
    LineGasState,
    TankGasState,
    iso_update,
    adiabatic_update,
    polytropic_update,
    p_from_mTV,
)
from .flow import mass_flow_orifice, mass_flow_unlimited
from .system import PneumaticSystem
from .thermo import PolytropicParameters
from config.constants import (
    get_pneumo_relief_orifices,
    get_pneumo_relief_thresholds,
)
from src.common.units import PA_ATM, T_AMBIENT


@lru_cache(maxsize=1)
def _relief_threshold_defaults() -> Mapping[str, float]:
    """Load relief valve pressure thresholds from the settings service."""

    thresholds = get_pneumo_relief_thresholds()
    return {
        "min": float(thresholds["min"]),
        "stiff": float(thresholds["stiff"]),
        "safety": float(thresholds["safety"]),
    }


def _default_relief_min_threshold() -> float:
    return _relief_threshold_defaults()["min"]


def _default_relief_stiff_threshold() -> float:
    return _relief_threshold_defaults()["stiff"]


def _default_relief_safety_threshold() -> float:
    return _relief_threshold_defaults()["safety"]


@lru_cache(maxsize=1)
def _relief_orifice_defaults() -> Mapping[str, float]:
    diameters = get_pneumo_relief_orifices()
    return {
        "min": float(diameters["min"]),
        "stiff": float(diameters["stiff"]),
    }


def _default_relief_min_orifice() -> float:
    return _relief_orifice_defaults()["min"]


def _default_relief_stiff_orifice() -> float:
    return _relief_orifice_defaults()["stiff"]


@dataclass
class GasNetwork:
    """Complete gas network with lines, tank, and valves.

    All pressures stored in the network remain **absolute** values. Downstream
    consumers that require gauge pressure must explicitly convert using the
    utilities in :mod:`src.common.units`.
    """

    lines: dict[Line, LineGasState]  # Four diagonal lines
    tank: TankGasState  # Receiver tank
    system_ref: PneumaticSystem  # Reference to pneumatic system
    master_isolation_open: bool = False  # Master isolation valve state
    ambient_temperature: float = T_AMBIENT  # Ambient temperature in Kelvin
    relief_min_threshold: float = field(default_factory=_default_relief_min_threshold)
    relief_stiff_threshold: float = field(
        default_factory=_default_relief_stiff_threshold
    )
    relief_safety_threshold: float = field(
        default_factory=_default_relief_safety_threshold
    )
    relief_min_orifice_diameter: float = field(
        default_factory=_default_relief_min_orifice
    )
    relief_stiff_orifice_diameter: float = field(
        default_factory=_default_relief_stiff_orifice
    )
    polytropic_params: PolytropicParameters | None = None
    leak_coefficient: float = 0.0
    leak_reference_area: float = 0.0
    master_equalization_diameter: float = 0.0

    def __post_init__(self):
        """Validate network configuration"""
        expected_lines = {Line.A1, Line.B1, Line.A2, Line.B2}
        actual_lines = set(self.lines.keys())

        if actual_lines != expected_lines:
            raise ValueError(
                f"Network must have all 4 lines. Expected {expected_lines}, got {actual_lines}"
            )

        threshold_checks = (
            (self.relief_min_threshold, "relief_min_threshold"),
            (self.relief_stiff_threshold, "relief_stiff_threshold"),
            (self.relief_safety_threshold, "relief_safety_threshold"),
        )
        for value, name in threshold_checks:
            if value <= 0.0:
                raise ValueError(f"{name} must be positive, got {value}")

        diameter_checks = (
            (self.relief_min_orifice_diameter, "relief_min_orifice_diameter"),
            (self.relief_stiff_orifice_diameter, "relief_stiff_orifice_diameter"),
        )
        for value, name in diameter_checks:
            if value <= 0.0:
                raise ValueError(f"{name} must be positive, got {value}")

        if self.master_equalization_diameter < 0.0:
            raise ValueError(
                "master_equalization_diameter must be non-negative, "
                f"got {self.master_equalization_diameter}"
            )

    def compute_line_volumes(self) -> dict[Line, float]:
        """Compute current volumes for all lines from cylinder states

        Returns:
            Dictionary mapping Line to total volume (m?)
        """
        system_volumes = self.system_ref.get_line_volumes()
        return {name: data["total_volume"] for name, data in system_volumes.items()}

    def update_pressures_with_explicit_volumes(
        self, volumes: dict[Line, float], thermo_mode: ThermoMode
    ) -> None:
        """Update line pressures using externally supplied volumes."""

        for line_name, new_volume in volumes.items():
            line_state = self.lines[line_name]

            if thermo_mode == ThermoMode.ISOTHERMAL:
                iso_update(line_state, new_volume, self.ambient_temperature)
            elif thermo_mode == ThermoMode.ADIABATIC:
                adiabatic_update(line_state, new_volume)
            elif thermo_mode == ThermoMode.POLYTROPIC:
                params = self.polytropic_params or PolytropicParameters(
                    0.0, 0.0, ambient_temperature=self.ambient_temperature
                )
                polytropic_update(line_state, new_volume, params)
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
        self, dt: float, log: logging.Logger | None = None
    ) -> dict[str, dict[str, float]]:
        """Apply valve flows for one time step

        Args:
            dt: Time step (s)
            log: Optional logger for diagnostics
        """
        if dt <= 0:
            raise ValueError(f"Time step must be positive: {dt}")

        # Process flows for each line
        line_flows: dict[Line, dict[str, float]] = {
            line_name: {"flow_atmo": 0.0, "flow_tank": 0.0, "flow_leak": 0.0}
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

            # Apply distributed leaks based on configured coefficients
            leaked_mass = self._apply_line_leak(line_state, dt)
            if leaked_mass > 0.0:
                line_flows[line_name]["flow_leak"] = float(leaked_mass / dt)

        # Process receiver relief valves
        relief_flows = self._apply_receiver_relief_valves(dt, log)

        return {"lines": line_flows, "relief": relief_flows}

    def _aggregate_diagonal(self, members: Sequence[Line]) -> dict[str, float]:
        total_mass = 0.0
        total_volume = 0.0
        total_enthalpy = 0.0

        for member in members:
            state = self.lines[member]
            mass = max(0.0, float(state.m))
            volume = max(0.0, float(state.V_curr))
            temperature = float(state.T)

            total_mass += mass
            total_volume += volume
            total_enthalpy += mass * temperature

        if total_mass <= 0.0 or total_volume <= 0.0:
            return {
                "mass": total_mass,
                "volume": total_volume,
                "temperature": self.ambient_temperature,
                "pressure": PA_ATM,
            }

        avg_temperature = total_enthalpy / total_mass
        pressure = p_from_mTV(total_mass, avg_temperature, total_volume)

        return {
            "mass": total_mass,
            "volume": total_volume,
            "temperature": avg_temperature,
            "pressure": pressure,
        }

    def _remove_mass_from_lines(
        self, members: Sequence[Line], requested_mass: float
    ) -> float:
        if requested_mass <= 0.0:
            return 0.0

        states = [self.lines[line] for line in members]
        available_mass = sum(max(0.0, float(state.m)) for state in states)
        if available_mass <= 0.0:
            return 0.0

        actual_removed = 0.0
        for state in states:
            state_mass = max(0.0, float(state.m))
            if state_mass <= 0.0:
                continue
            fraction = state_mass / available_mass
            removal = min(state_mass, requested_mass * fraction)
            if removal <= 0.0:
                continue
            state.m = state_mass - removal
            if state.m > 0.0:
                state.p = p_from_mTV(state.m, state.T, state.V_curr)
            else:
                state.p = 0.0
            actual_removed += removal

        return actual_removed

    def _distribute_mass_to_lines(
        self, members: Sequence[Line], added_mass: float, inlet_temperature: float
    ) -> None:
        if added_mass <= 0.0:
            return

        states = [self.lines[line] for line in members]
        total_volume = sum(max(0.0, float(state.V_curr)) for state in states)
        if total_volume <= 0.0:
            return

        for state in states:
            volume = max(0.0, float(state.V_curr))
            if volume <= 0.0:
                continue
            share = volume / total_volume
            increment = added_mass * share
            self._add_mass_to_line(state, increment, inlet_temperature)

    def _apply_master_equalisation(
        self, dt: float, log: logging.Logger | None = None
    ) -> tuple[str, float, float]:
        diameter = float(self.master_equalization_diameter)
        if diameter <= 0.0 or dt <= 0.0:
            return ("none", 0.0, 0.0)

        diagonal_a = (Line.A1, Line.B1)
        diagonal_b = (Line.A2, Line.B2)

        state_a = self._aggregate_diagonal(diagonal_a)
        state_b = self._aggregate_diagonal(diagonal_b)

        pressure_delta = state_a["pressure"] - state_b["pressure"]
        if abs(pressure_delta) < 1.0:
            return ("none", 0.0, 0.0)

        if pressure_delta > 0.0:
            upstream_state = state_a
            downstream_state = state_b
            upstream_lines = diagonal_a
            downstream_lines = diagonal_b
            direction = "A_to_B"
        else:
            upstream_state = state_b
            downstream_state = state_a
            upstream_lines = diagonal_b
            downstream_lines = diagonal_a
            direction = "B_to_A"

        m_dot = mass_flow_orifice(
            upstream_state["pressure"],
            upstream_state["temperature"],
            downstream_state["pressure"],
            downstream_state["temperature"],
            diameter,
        )

        if m_dot <= 0.0:
            return ("none", 0.0, 0.0)

        requested_mass = m_dot * dt
        transferred_mass = self._remove_mass_from_lines(upstream_lines, requested_mass)
        if transferred_mass <= 0.0:
            return ("none", 0.0, 0.0)

        self._distribute_mass_to_lines(
            downstream_lines, transferred_mass, upstream_state["temperature"]
        )

        mass_flow = transferred_mass / dt

        if log:
            log.debug(
                "Master isolation throttle %s: -%.6fkg, m_dot=%.6fkg/s",
                direction,
                transferred_mass,
                mass_flow,
            )

        return (direction, transferred_mass, mass_flow)

    def _equalise_instantaneously(self, log: logging.Logger | None = None) -> None:
        total_mass = sum(line.m for line in self.lines.values())

        volumes = self.compute_line_volumes()
        total_volume = sum(volumes.values())

        if total_mass <= 0 or total_volume <= 0:
            return

        total_enthalpy = sum(line.m * line.T for line in self.lines.values())
        avg_temperature = (
            total_enthalpy / total_mass if total_mass > 0 else self.ambient_temperature
        )

        equalized_pressure = p_from_mTV(total_mass, avg_temperature, total_volume)

        for line_name, line_state in self.lines.items():
            line_volume = volumes[line_name]
            line_mass_fraction = line_volume / total_volume

            line_state.m = total_mass * line_mass_fraction
            line_state.T = avg_temperature
            line_state.p = equalized_pressure
            line_state.V_curr = line_volume

        if log:
            log.debug(
                "Master isolation: equalized p=%0.0fPa, T=%0.1fK",
                equalized_pressure,
                avg_temperature,
            )

    def _apply_line_leak(self, line_state: LineGasState, dt: float) -> float:
        """Apply configured leak losses to *line_state* and return lost mass."""

        coeff = max(0.0, self.leak_coefficient)
        area = max(0.0, self.leak_reference_area)
        if coeff <= 0.0 or area <= 0.0 or dt <= 0.0:
            return 0.0

        if line_state.m <= 0.0:
            return 0.0

        pressure_drop = max(line_state.p - PA_ATM, 0.0)
        if pressure_drop <= 0.0:
            return 0.0

        leak_rate = coeff * area * pressure_drop
        if leak_rate <= 0.0:
            return 0.0

        mass_loss = min(leak_rate * dt, line_state.m)
        if mass_loss <= 0.0:
            return 0.0

        line_state.m = max(line_state.m - mass_loss, 0.0)
        if line_state.m <= 0.0:
            line_state.p = 0.0
        else:
            line_state.p = p_from_mTV(line_state.m, line_state.T, line_state.V_curr)

        return mass_loss

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
        self, dt: float, log: logging.Logger | None = None
    ) -> dict[str, float]:
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

        d_eq_min_bleed = self.relief_min_orifice_diameter
        d_eq_stiff_bleed = self.relief_stiff_orifice_diameter

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

    def enforce_master_isolation(
        self,
        log: logging.Logger | None = None,
        dt: float | None = None,
    ):
        """Enforce master isolation when enabled - equalize all line pressures

        Args:
            log: Optional logger
        """
        if not self.master_isolation_open:
            return
        if dt is not None and dt > 0.0 and self.master_equalization_diameter > 0.0:
            self._apply_master_equalisation(dt, log)
            return

        self._equalise_instantaneously(log)

    def validate_invariants(self) -> dict[str, any]:
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
            if len({f"{p:.0f}" for p in pressures}) > 1:  # Round to Pa for comparison
                max_p_diff = max(pressures) - min(pressures)
                if max_p_diff > 1000:  # > 1000 Pa difference
                    warnings.append(
                        f"Master isolation enabled but pressures not equalized: diff={max_p_diff:.0f}Pa"
                    )

        return {"is_valid": len(errors) == 0, "errors": errors, "warnings": warnings}
