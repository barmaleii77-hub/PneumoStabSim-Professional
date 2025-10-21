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
    """Gas state for a pneumatic line."""

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
    """Gas state for the receiver tank."""

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


def p_from_mTV(mass: float, temperature: float, volume: float) -> float:
    """Ideal gas law helper (p = m*R*T / V)."""
    if volume <= 0:
        raise ValueError("Volume must be positive to compute pressure")
    if temperature <= 0:
        raise ValueError("Temperature must be positive to compute pressure")
    if mass < 0:
        raise ValueError("Mass must be non-negative to compute pressure")
    return (mass * R_AIR * temperature) / volume


def iso_update(
    state: LineGasState, new_volume: float, target_temperature: float
) -> None:
    """Perform an isothermal update on a line gas state."""
    if target_temperature <= 0:
        raise ValueError(f"Target temperature must be positive, got {target_temperature}")
    state.set_volume(new_volume)
    state.T = target_temperature
    state.update_pressure()


def adiabatic_update(state: LineGasState, new_volume: float, gamma: float = GAMMA_AIR) -> None:
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
