"""
Gas state helpers for pneumatic simulation tests and runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .enums import Line, ReceiverVolumeMode
from .thermo import ThermoMode
from src.common.units import R_AIR, GAMMA_AIR, PA_ATM, T_AMBIENT


@dataclass
class LineGasState:
    """Gas state for a pneumatic line storing absolute pressure."""

    name: Line
    m: float
    T: float
    p: float
    V_prev: float
    V_curr: float

    def __post_init__(self) -> None:
        self._validate_state()

    def _validate_state(self) -> None:
        if self.m < 0:
            raise ValueError(f"Mass cannot be negative: {self.m}")
        if self.T <= 0:
            raise ValueError(f"Temperature must be positive: {self.T}")
        if self.p < 0:
            raise ValueError(f"Pressure cannot be negative: {self.p}")
        if self.V_prev <= 0:
            raise ValueError(f"Previous volume must be positive: {self.V_prev}")
        if self.V_curr <= 0:
            raise ValueError(f"Current volume must be positive: {self.V_curr}")

    def set_volume(self, new_volume: float) -> None:
        if new_volume <= 0:
            raise ValueError(f"Volume must be positive, got {new_volume}")
        self.V_prev = self.V_curr
        self.V_curr = new_volume

    def update_pressure(self) -> None:
        self.p = p_from_mTV(self.m, self.T, self.V_curr)


@dataclass
class TankGasState:
    """Gas state for the receiver tank storing absolute pressure."""

    V: float
    p: float
    T: float
    m: float
    mode: ReceiverVolumeMode
    gamma: float = GAMMA_AIR
    V_prev: Optional[float] = None

    def __post_init__(self) -> None:
        if self.V <= 0:
            raise ValueError(f"Volume must be positive: {self.V}")
        if self.p <= 0:
            raise ValueError(f"Pressure must be positive: {self.p}")
        if self.T <= 0:
            raise ValueError(f"Temperature must be positive: {self.T}")
        if self.m < 0:
            raise ValueError(f"Mass cannot be negative: {self.m}")
        if self.gamma <= 1.0:
            raise ValueError(f"Adiabatic gamma must be >1.0, got {self.gamma}")
        self.V_prev = self.V

    def update_ideal_gas(self) -> None:
        self.p = p_from_mTV(self.m, self.T, self.V)


@dataclass
class GasState:
    """Combined gas state for a line and a tank."""

    line: LineGasState
    tank: TankGasState

    @property
    def total_mass(self) -> float:
        return self.line.m + self.tank.m

    @property
    def total_volume(self) -> float:
        return self.line.V_curr + self.tank.V

    @property
    def total_pressure(self) -> float:
        # Average the pressures based on volume
        total_volume = self.total_volume
        if total_volume <= 0:
            raise ValueError("Total volume must be positive to compute pressure")
        return (
            self.line.p * self.line.V_curr + self.tank.p * self.tank.V
        ) / total_volume

    @property
    def total_temperature(self) -> float:
        # Energy balance based temperature
        if self.total_mass <= 0:
            raise ValueError("Total mass must be positive to compute temperature")
        return (self.line.m * self.line.T + self.tank.m * self.tank.T) / self.total_mass

    def update_states(self) -> None:
        """Update the line and tank states based on the current combined state."""
        self.line.m = self.line.p * self.line.V_curr / (R_AIR * self.line.T)
        self.tank.m = self.tank.p * self.tank.V / (R_AIR * self.tank.T)
        self.line.update_pressure()
        self.tank.update_ideal_gas()


@dataclass
class LegacyGasState:
    """Simple ideal-gas state helper used by legacy tests.

    The original test-suite expects a lightweight container with
    ``pressure``, ``temperature`` and ``volume`` attributes as well as a
    method that updates the state for isothermal and adiabatic volume
    changes. The modern implementation refactored the gas handling logic
    into :class:`LineGasState` and :class:`TankGasState`, which broke the
    direct import used by the tests. This compatibility shim restores the
    expected API while reusing the validated thermodynamic helpers from the
    new module.
    """

    pressure: float
    temperature: float
    volume: float
    mass: Optional[float] = None
    gas_constant: float = R_AIR
    gamma: float = GAMMA_AIR

    def __post_init__(self) -> None:
        self._validate_state()
        if self.mass is None:
            self.mass = gas_mass_from_pVT(
                self.pressure, self.volume, self.temperature, self.gas_constant
            )
        else:
            if self.mass <= 0:
                raise ValueError(f"Mass must be positive, got {self.mass}")
            self.mass = float(self.mass)

        self._recalculate_pressure()

    def _validate_state(self) -> None:
        if self.pressure <= 0:
            raise ValueError(f"Pressure must be positive, got {self.pressure}")
        if self.temperature <= 0:
            raise ValueError(f"Temperature must be positive, got {self.temperature}")
        if self.volume <= 0:
            raise ValueError(f"Volume must be positive, got {self.volume}")
        if self.gas_constant <= 0:
            raise ValueError(f"Gas constant must be positive, got {self.gas_constant}")
        if self.gamma <= 1.0:
            raise ValueError(f"Adiabatic gamma must be >1.0, got {self.gamma}")

    def _recalculate_pressure(self) -> None:
        self.pressure = p_from_mTV(self.mass, self.temperature, self.volume)

    def update_volume(self, new_volume: float, *, mode: ThermoMode) -> None:
        """Update the gas state for a volume change.

        Args:
            new_volume: Target volume in cubic metres.
            mode: Thermodynamic process mode describing the heat exchange.
        """

        if new_volume <= 0:
            raise ValueError(f"Volume must be positive, got {new_volume}")

        if mode == ThermoMode.ISOTHERMAL:
            self.volume = float(new_volume)
            self._recalculate_pressure()
            return

        if mode == ThermoMode.ADIABATIC:
            pv_constant = self.pressure * (self.volume**self.gamma)
            tv_constant = self.temperature * (self.volume ** (self.gamma - 1.0))

            self.volume = float(new_volume)
            self.pressure = pv_constant / (self.volume**self.gamma)
            self.temperature = tv_constant / (self.volume ** (self.gamma - 1.0))
            return

        raise ValueError(f"Unsupported thermo mode: {mode}")

    def add_mass(
        self, delta_mass: float, inlet_temperature: Optional[float] = None
    ) -> None:
        """Add mass to the control volume preserving energy balance."""

        if delta_mass == 0:
            return
        if self.mass + delta_mass <= 0:
            raise ValueError("Resulting mass must remain positive")

        inlet_T = self.temperature if inlet_temperature is None else inlet_temperature
        if inlet_T <= 0:
            raise ValueError(f"Inlet temperature must be positive, got {inlet_T}")

        new_mass = self.mass + delta_mass
        self.temperature = (
            self.mass * self.temperature + delta_mass * inlet_T
        ) / new_mass
        self.mass = new_mass
        self._recalculate_pressure()


def p_from_mTV(mass: float, temperature: float, volume: float) -> float:
    """Ideal gas law helper (p = m*R*T / V)."""
    if volume <= 0:
        raise ValueError("Volume must be positive to compute pressure")
    if temperature <= 0:
        raise ValueError("Temperature must be positive to compute pressure")
    if mass < 0:
        raise ValueError("Mass must be non-negative to compute pressure")
    return (mass * R_AIR * temperature) / volume


def gas_mass_from_pVT(
    pressure: float, volume: float, temperature: float, gas_constant: float = R_AIR
) -> float:
    """Расчёт массы по p, V, T для идеального газа (m = p*V/(R*T))."""
    if volume <= 0:
        raise ValueError("Volume must be positive to compute mass")
    if temperature <= 0:
        raise ValueError("Temperature must be positive to compute mass")
    if gas_constant <= 0:
        raise ValueError("Gas constant must be positive to compute mass")
    if pressure < 0:
        raise ValueError("Pressure must be non-negative to compute mass")
    return (pressure * volume) / (gas_constant * temperature)


def iso_update(
    state: LineGasState, new_volume: float, target_temperature: float
) -> None:
    """Perform an isothermal update on a line gas state."""
    if target_temperature <= 0:
        raise ValueError(
            f"Target temperature must be positive, got {target_temperature}"
        )
    state.set_volume(new_volume)
    state.T = target_temperature
    state.update_pressure()


def adiabatic_update(
    state: LineGasState, new_volume: float, gamma: float = GAMMA_AIR
) -> None:
    """Perform an adiabatic update on a line gas state."""
    if gamma <= 1.0:
        raise ValueError(f"Adiabatic gamma must be >1.0, got {gamma}")
    prev_volume = state.V_curr
    prev_temperature = state.T
    state.set_volume(new_volume)
    volume_ratio = prev_volume / state.V_curr
    state.T = prev_temperature * (volume_ratio ** (gamma - 1.0))
    state.update_pressure()


def apply_instant_volume_change(
    tank: TankGasState, new_volume: float, gamma: float = GAMMA_AIR
) -> None:
    """Apply an instantaneous volume change to the receiver tank."""
    if new_volume <= 0:
        raise ValueError(f"Tank volume must be positive, got {new_volume}")
    tank.V_prev = tank.V
    tank.V = new_volume

    if tank.mode == ReceiverVolumeMode.NO_RECALC:
        return

    if tank.mode == ReceiverVolumeMode.ADIABATIC_RECALC:
        if gamma <= 1.0:
            raise ValueError(f"Adiabatic gamma must be >1.0, got {gamma}")
        volume_ratio = tank.V_prev / tank.V
        tank.T = tank.T * (volume_ratio ** (gamma - 1.0))
        tank.update_ideal_gas()
        return

    raise ValueError(f"Unsupported receiver volume mode: {tank.mode}")


def create_line_gas_state(
    name: Line,
    p_initial: float,
    T_initial: float,
    V_initial: float,
    *,
    mass: Optional[float] = None,
) -> LineGasState:
    """Factory for line gas states used in tests and defaults."""
    if V_initial <= 0:
        raise ValueError("Initial volume must be positive")
    if T_initial <= 0:
        raise ValueError("Initial temperature must be positive")
    if p_initial < 0:
        raise ValueError("Initial pressure cannot be negative")
    if mass is None:
        mass = (p_initial * V_initial) / (R_AIR * T_initial)
    return LineGasState(
        name=name,
        m=mass,
        T=T_initial,
        p=p_initial,
        V_prev=V_initial,
        V_curr=V_initial,
    )


def create_tank_gas_state(
    V_initial: float,
    p_initial: float = PA_ATM,
    T_initial: float = T_AMBIENT,
    mode: ReceiverVolumeMode = ReceiverVolumeMode.NO_RECALC,
    *,
    gamma: float = GAMMA_AIR,
) -> TankGasState:
    """Factory for receiver tank gas state."""
    if V_initial <= 0:
        raise ValueError("Initial tank volume must be positive")
    if p_initial <= 0:
        raise ValueError("Initial tank pressure must be positive")
    if T_initial <= 0:
        raise ValueError("Initial tank temperature must be positive")
    tank_mass = (p_initial * V_initial) / (R_AIR * T_initial)
    return TankGasState(
        V=V_initial,
        p=p_initial,
        T=T_initial,
        m=tank_mass,
        mode=mode,
        gamma=gamma,
    )
