"""
Gas state management for pneumatic lines and receiver
Handles isothermal and adiabatic processes
"""

import math
from dataclasses import dataclass
from typing import Optional
from .enums import Line, ReceiverVolumeMode
from .thermo import ThermoMode
from src.common.units import R_AIR, GAMMA_AIR, PA_ATM, T_AMBIENT


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


class GasState:
    """Legacy wrapper for gas state - provides test compatibility
    
    This class wraps LineGasState to provide the old API that tests expect.
    New code should use LineGasState or TankGasState directly.
    """
    
    def __init__(self, pressure: float, temperature: float, volume: float, 
                 name: Optional[Line] = None):
        """Initialize gas state
        
        Args:
            pressure: Initial pressure (Pa)
            temperature: Initial temperature (K)
            volume: Initial volume (m?)
            name: Line identifier (optional, defaults to A1)
        """
        # Calculate mass from ideal gas law
        self._m = (pressure * volume) / (R_AIR * temperature)
        self._p = pressure
        self._T = temperature
        self._V = volume
        self._name = name if name is not None else Line.A1
        
    @property
    def pressure(self) -> float:
        """Get pressure (Pa)"""
        return self._p
    
    @property
    def temperature(self) -> float:
        """Get temperature (K)"""
        return self._T
    
    @property
    def volume(self) -> float:
        """Get volume (m?)"""
        return self._V
    
    @property
    def mass(self) -> float:
        """Get mass (kg)"""
        return self._m
    
    def update_volume(self, V_new: float, mode: ThermoMode = ThermoMode.ISOTHERMAL):
        """Update volume and recalculate state
        
        Args:
            V_new: New volume (m?)
            mode: Thermodynamic mode (ISOTHERMAL or ADIABATIC)
        """
        if V_new <= 0:
            raise ValueError(f"Volume must be positive: {V_new}")
        
        if mode == ThermoMode.ISOTHERMAL:
            # Isothermal: T = const, recalculate p
            self._V = V_new
            self._p = (self._m * R_AIR * self._T) / self._V
            
        elif mode == ThermoMode.ADIABATIC:
            # Adiabatic: calculate new T and p
            V_old = self._V
            T_old = self._T
            
            # T_new = T_old * (V_old/V_new)^(gamma-1)
            volume_ratio = V_old / V_new
            self._T = T_old * (volume_ratio ** (GAMMA_AIR - 1.0))
            self._V = V_new
            
            # Recalculate pressure from ideal gas law
            self._p = (self._m * R_AIR * self._T) / self._V
        else:
            raise ValueError(f"Unknown thermo mode: {mode}")
    
    def add_mass(self, m_in: float, T_in: float):
        """Add mass with mixing
        
        Args:
            m_in: Incoming mass (kg)
            T_in: Temperature of incoming mass (K)
        """
        if m_in < 0:
            raise ValueError(f"Mass must be positive: {m_in}")
        if T_in <= 0:
            raise ValueError(f"Temperature must be positive: {T_in}")
        
        # Mass-weighted temperature mixing
        m_total = self._m + m_in
        self._T = (self._m * self._T + m_in * T_in) / m_total
        self._m = m_total
        
        # Recalculate pressure (volume stays same)
        self._p = (self._m * R_AIR * self._T) / self._V