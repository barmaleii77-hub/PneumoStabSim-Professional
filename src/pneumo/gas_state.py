"""
Gas state management for pneumatic lines and receiver
Handles isothermal and adiabatic processes
"""

import math
from dataclasses import dataclass
from typing import Optional
from .enums import Line, ReceiverVolumeMode
from ..common.units import R_AIR, GAMMA_AIR, PA_ATM, T_AMBIENT


@dataclass
class LineGasState:
    """Gas state for a pneumatic line"""
    name: Line          # Line identifier (A1/B1/A2/B2)
    m: float           # Mass of gas (kg)
    T: float           # Temperature (K)
    p: float           # Pressure at start of step (Pa) - for diagnostics
    V_prev: float      # Previous volume (m?) - for adiabatic calculations
    V_curr: float      # Current volume (m?)
    
    def __post_init__(self):
        self._validate_state()
    
    def _validate_state(self):
        """Validate gas state parameters"""
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


@dataclass
class TankGasState:
    """Gas state for receiver tank"""
    V: float                        # Volume (m?)
    p: float                        # Pressure (Pa)
    T: float                        # Temperature (K)
    m: float                        # Mass (kg)
    mode: ReceiverVolumeMode        # Volume change mode
    
    def __post_init__(self):
        self._validate_state()
    
    def _validate_state(self):
        """Validate tank state parameters"""
        if self.V <= 0:
            raise ValueError(f"Volume must be positive: {self.V}")
        if self.p < 0:
            raise ValueError(f"Pressure cannot be negative: {self.p}")
        if self.T <= 0:
            raise ValueError(f"Temperature must be positive: {self.T}")
        if self.m < 0:
            raise ValueError(f"Mass cannot be negative: {self.m}")


def p_from_mTV(m: float, T: float, V: float) -> float:
    """Calculate pressure from mass, temperature, and volume using ideal gas law
    
    Args:
        m: Mass (kg)
        T: Temperature (K)
        V: Volume (m?)
        
    Returns:
        Pressure (Pa)
    """
    if m <= 0 or T <= 0 or V <= 0:
        raise ValueError(f"All parameters must be positive: m={m}, T={T}, V={V}")
    
    return (m * R_AIR * T) / V


def iso_update(line: LineGasState, V_new: float, T_iso: float = T_AMBIENT):
    """Update line state for isothermal process
    
    Args:
        line: Line gas state to update
        V_new: New volume (m?)
        T_iso: Isothermal temperature (K)
    """
    if V_new <= 0:
        raise ValueError(f"New volume must be positive: {V_new}")
    
    # Update volumes
    line.V_prev = line.V_curr
    line.V_curr = V_new
    
    # Isothermal: T = constant, mass unchanged, recalculate pressure
    line.T = T_iso
    line.p = p_from_mTV(line.m, line.T, line.V_curr)


def adiabatic_update(line: LineGasState, V_new: float, gamma: float = GAMMA_AIR):
    """Update line state for adiabatic process
    
    Args:
        line: Line gas state to update  
        V_new: New volume (m?)
        gamma: Heat capacity ratio
    """
    if V_new <= 0:
        raise ValueError(f"New volume must be positive: {V_new}")
    if gamma <= 1:
        raise ValueError(f"Gamma must be > 1: {gamma}")
    
    # Store old state
    T_old = line.T
    V_old = line.V_curr
    
    # Update volumes
    line.V_prev = line.V_curr
    line.V_curr = V_new
    
    # Adiabatic relations: T_new = T_old * (V_old/V_new)^(gamma-1)
    if abs(V_old) < 1e-12:
        raise ValueError("Cannot perform adiabatic update from zero volume")
    
    volume_ratio = V_old / V_new
    line.T = T_old * (volume_ratio ** (gamma - 1.0))
    
    # Calculate pressure from ideal gas law
    line.p = p_from_mTV(line.m, line.T, line.V_curr)


def apply_instant_volume_change(tank: TankGasState, V_new: float, gamma: float = GAMMA_AIR):
    """Apply instantaneous volume change to tank
    
    Args:
        tank: Tank state to update
        V_new: New volume (m?)
        gamma: Heat capacity ratio for adiabatic mode
    """
    if V_new <= 0:
        raise ValueError(f"New volume must be positive: {V_new}")
    
    if tank.mode == ReceiverVolumeMode.NO_RECALC:
        # Simply change volume, keep p and T constant
        tank.V = V_new
        
    elif tank.mode == ReceiverVolumeMode.ADIABATIC_RECALC:
        # Adiabatic process: recalculate p and T
        if abs(tank.V) < 1e-12:
            raise ValueError("Cannot perform adiabatic recalculation from zero volume")
        
        T_old = tank.T
        p_old = tank.p
        V_old = tank.V
        
        # Adiabatic relations
        volume_ratio = V_old / V_new
        tank.T = T_old * (volume_ratio ** (gamma - 1.0))
        tank.p = p_old * (volume_ratio ** gamma)
        tank.V = V_new
        
        # Verify mass consistency (should remain constant in adiabatic process)
        expected_mass = (tank.p * tank.V) / (R_AIR * tank.T)
        if abs(expected_mass - tank.m) > tank.m * 1e-6:  # 1 ppm tolerance
            # Update mass to maintain consistency
            tank.m = expected_mass
    
    else:
        raise ValueError(f"Unknown receiver volume mode: {tank.mode}")


def create_line_gas_state(line: Line, p_initial: float = PA_ATM, 
                         T_initial: float = T_AMBIENT, V_initial: float = 1e-3) -> LineGasState:
    """Create initial line gas state
    
    Args:
        line: Line identifier
        p_initial: Initial pressure (Pa)
        T_initial: Initial temperature (K)
        V_initial: Initial volume (m?)
        
    Returns:
        Initialized LineGasState
    """
    # Calculate initial mass from ideal gas law
    m_initial = (p_initial * V_initial) / (R_AIR * T_initial)
    
    return LineGasState(
        name=line,
        m=m_initial,
        T=T_initial,
        p=p_initial,
        V_prev=V_initial,
        V_curr=V_initial
    )


def create_tank_gas_state(V_initial: float, p_initial: float = PA_ATM,
                         T_initial: float = T_AMBIENT, 
                         mode: ReceiverVolumeMode = ReceiverVolumeMode.NO_RECALC) -> TankGasState:
    """Create initial tank gas state
    
    Args:
        V_initial: Initial volume (m?)
        p_initial: Initial pressure (Pa)
        T_initial: Initial temperature (K)
        mode: Volume change mode
        
    Returns:
        Initialized TankGasState
    """
    # Calculate initial mass from ideal gas law
    m_initial = (p_initial * V_initial) / (R_AIR * T_initial)
    
    return TankGasState(
        V=V_initial,
        p=p_initial,
        T=T_initial,
        m=m_initial,
        mode=mode
    )