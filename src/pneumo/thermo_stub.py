"""
Thermo module stubs for P12 tests
"""

from enum import Enum


class ThermoMode(Enum):
    """Thermodynamic calculation mode"""
    ISOTHERMAL = "isothermal"
    ADIABATIC = "adiabatic"
