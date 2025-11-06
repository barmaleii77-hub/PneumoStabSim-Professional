"""
Domain enumerations for pneumatic system
Strict terminology with docstrings
"""

from enum import Enum


class Wheel(Enum):
    """Wheel positions in the stabilizer system

    LP - Left Front
    PP - Right Front
    LZ - Left Rear
    PZ - Right Rear
    """

    LP = "LP"  # Left Front
    PP = "PP"  # Right Front
    LZ = "LZ"  # Left Rear
    PZ = "PZ"  # Right Rear


class Port(Enum):
    """Cylinder port types

    ROD - Rod side chamber
    HEAD - Head side chamber
    """

    ROD = "ROD"  # Rod chamber
    HEAD = "HEAD"  # Head chamber


class Line(Enum):
    """Pneumatic line identifiers

    Diagonal connection scheme:
    A1, B1, A2, B2 - four independent pneumatic lines
    """

    A1 = "A1"
    B1 = "B1"
    A2 = "A2"
    B2 = "B2"


class ThermoMode(Enum):
    """Thermodynamic process mode

    ADIABATIC - No heat exchange (fast processes)
    ISOTHERMAL - Constant temperature (slow processes)
    POLYTROPIC - Intermediate heat exchange with configurable coupling
    """

    ADIABATIC = "ADIABATIC"
    ISOTHERMAL = "ISOTHERMAL"
    POLYTROPIC = "POLYTROPIC"


class ReceiverVolumeMode(Enum):
    """Receiver volume recalculation mode

    NO_RECALC - Volume changes don't affect pressure/temperature
    ADIABATIC_RECALC - Recalculate p,T using adiabatic relations
    """

    NO_RECALC = "NO_RECALC"
    ADIABATIC_RECALC = "ADIABATIC_RECALC"


class CheckValveKind(Enum):
    """Check valve type by flow direction

    ATMO_TO_LINE - From atmosphere to pneumatic line
    LINE_TO_TANK - From pneumatic line to receiver tank
    """

    ATMO_TO_LINE = "ATMO_TO_LINE"
    LINE_TO_TANK = "LINE_TO_TANK"


class ReliefValveKind(Enum):
    """Relief valve type by function

    MIN_PRESS - Minimum pressure maintenance
    STIFFNESS - Stiffness control valve
    SAFETY - Safety relief valve (no throttling)
    """

    MIN_PRESS = "MIN_PRESS"
    STIFFNESS = "STIFFNESS"
    SAFETY = "SAFETY"
