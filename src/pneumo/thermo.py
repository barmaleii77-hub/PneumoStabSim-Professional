"""
Thermodynamic formulas and constants
Function signatures for adiabatic and isothermal processes
"""

from dataclasses import dataclass
from enum import Enum
import math
from src.common.units import GAMMA_AIR, R_AIR, T_AMBIENT


class ThermoMode(Enum):
    """Thermodynamic calculation mode"""

    ISOTHERMAL = "isothermal"
    ADIABATIC = "adiabatic"
    POLYTROPIC = "polytropic"


@dataclass(frozen=True)
class PolytropicParameters:
    """Parameters controlling the polytropic heat exchange model."""

    heat_transfer_coeff: float
    exchange_area: float
    ambient_temperature: float = T_AMBIENT

    def effective_index(self, mass: float, gamma: float = GAMMA_AIR) -> float:
        """Return the polytropic exponent based on heat coupling strength."""

        if gamma <= 1.0:
            raise ValueError(f"Adiabatic gamma must be >1.0, got {gamma}")

        conduction = max(0.0, self.heat_transfer_coeff) * max(0.0, self.exchange_area)
        if mass <= 0.0 or conduction <= 0.0:
            return gamma

        cp = gamma * R_AIR / (gamma - 1.0)
        coupling = conduction / max(mass * cp, 1e-12)
        return 1.0 + (gamma - 1.0) / (1.0 + coupling)

    def relaxation_factor(self, mass: float, gamma: float = GAMMA_AIR) -> float:
        """Return the fractional temperature relaxation toward ambient."""

        if gamma <= 1.0:
            raise ValueError(f"Adiabatic gamma must be >1.0, got {gamma}")

        conduction = max(0.0, self.heat_transfer_coeff) * max(0.0, self.exchange_area)
        if mass <= 0.0 or conduction <= 0.0:
            return 0.0

        cp = gamma * R_AIR / (gamma - 1.0)
        coupling = conduction / max(mass * cp, 1e-12)
        return 1.0 - math.exp(-coupling)


def adiabatic_p(V: float, C: float) -> float:
    """Calculate pressure from adiabatic relation p*V^? = C

    Args:
        V: Volume (m³)
        C: Adiabatic constant p*V^? (Pa*m^(3?))

    Returns:
        Pressure (Pa)
    """
    if V <= 0:
        raise ValueError(f"Volume must be positive, got {V}")
    if C <= 0:
        raise ValueError(f"Adiabatic constant must be positive, got {C}")

    return C * (V ** (-GAMMA_AIR))


def adiabatic_T(V: float, C_T: float) -> float:
    """Calculate temperature from adiabatic relation T*V^(?-1) = C_T

    Args:
        V: Volume (m?)
        C_T: Temperature constant T*V^(?-1) (K*m^(3(?-1)))

    Returns:
        Temperature (K)
    """
    if V <= 0:
        raise ValueError(f"Volume must be positive, got {V}")
    if C_T <= 0:
        raise ValueError(f"Temperature constant must be positive, got {C_T}")

    return C_T * (V ** (-(GAMMA_AIR - 1.0)))


def isothermal_p(V: float, m: float, R: float, T_atm: float) -> float:
    """Calculate pressure from isothermal ideal gas law p = (m*R*T)/V

    Args:
        V: Volume (m?)
        m: Mass of gas (kg)
        R: Specific gas constant (J/(kg*K))
        T_atm: Atmospheric temperature (K)

    Returns:
        Pressure (Pa)
    """
    if V <= 0:
        raise ValueError(f"Volume must be positive, got {V}")
    if m <= 0:
        raise ValueError(f"Mass must be positive, got {m}")
    if R <= 0:
        raise ValueError(f"Gas constant must be positive, got {R}")
    if T_atm <= 0:
        raise ValueError(f"Temperature must be positive, got {T_atm}")

    return (m * R * T_atm) / V


def adiabatic_constant_pV(p: float, V: float) -> float:
    """Calculate adiabatic constant C = p*V^?

    Args:
        p: Pressure (Pa)
        V: Volume (m?)

    Returns:
        Adiabatic constant (Pa*m^(3?))
    """
    if p <= 0:
        raise ValueError(f"Pressure must be positive, got {p}")
    if V <= 0:
        raise ValueError(f"Volume must be positive, got {V}")

    return p * (V**GAMMA_AIR)


def adiabatic_constant_TV(T: float, V: float) -> float:
    """Calculate temperature adiabatic constant C_T = T*V^(?-1)

    Args:
        T: Temperature (K)
        V: Volume (m?)

    Returns:
        Temperature constant (K*m^(3(?-1)))
    """
    if T <= 0:
        raise ValueError(f"Temperature must be positive, got {T}")
    if V <= 0:
        raise ValueError(f"Volume must be positive, got {V}")

    return T * (V ** (GAMMA_AIR - 1.0))


def polytropic_constant_pV(p: float, V: float, n: float) -> float:
    """Calculate polytropic constant C = p*V^n."""

    if p <= 0:
        raise ValueError(f"Pressure must be positive, got {p}")
    if V <= 0:
        raise ValueError(f"Volume must be positive, got {V}")
    if n <= 0:
        raise ValueError(f"Polytropic exponent must be positive, got {n}")

    return p * (V**n)


def gas_mass_from_pVT(p: float, V: float, T: float, R: float = R_AIR) -> float:
    """Calculate gas mass from ideal gas law m = (p*V)/(R*T)

    Args:
        p: Pressure (Pa)
        V: Volume (m?)
        T: Temperature (K)
        R: Specific gas constant (J/(kg*K)), default for air

    Returns:
        Mass of gas (kg)
    """
    if p <= 0:
        raise ValueError(f"Pressure must be positive, got {p}")
    if V <= 0:
        raise ValueError(f"Volume must be positive, got {V}")
    if T <= 0:
        raise ValueError(f"Temperature must be positive, got {T}")
    if R <= 0:
        raise ValueError(f"Gas constant must be positive, got {R}")

    return (p * V) / (R * T)


# Re-export constants and classes for convenience
__all__ = [
    "ThermoMode",  # Enum for thermo mode
    "PolytropicParameters",
    "GAMMA_AIR",
    "R_AIR",
    "adiabatic_p",
    "adiabatic_T",
    "isothermal_p",
    "adiabatic_constant_pV",
    "adiabatic_constant_TV",
    "polytropic_constant_pV",
    "gas_mass_from_pVT",
]
