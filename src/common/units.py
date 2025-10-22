"""
Common utilities and constants for PneumoStabSim
All values in SI units: meters, Pascals, Kelvin, kilograms, Newtons
"""

import math

# Atmospheric conditions
PA_ATM = 101325.0  # Pascal - atmospheric pressure at sea level
KELVIN_0C = 273.15  # Kelvin - 0°C in Kelvin

# Mathematical constants
DEG2RAD = math.pi / 180.0  # Degrees to radians conversion
RAD2DEG = 180.0 / math.pi  # Radians to degrees conversion

# Gas properties (for air)
# Use the canonical thermodynamic constant referenced by the
# legacy test-suite (rounded to 287.05). This matches historical
# calculations used by the pneumatic integration tests and avoids
# tiny rounding mismatches that previously caused assertion
# failures when comparing against analytical solutions.
R_AIR = 287.05  # Specific gas constant for air, J/(kg*K)
GAMMA_AIR = 1.4  # Adiabatic index for air

# Default environmental conditions
T_AMBIENT = 293.15  # K (20°C)
P_AMBIENT = PA_ATM  # Pa

# Numerical tolerances
EPSILON = 1e-9  # General floating point tolerance
MIN_VOLUME_FRACTION = 0.005  # Minimum residual volume as fraction of total
