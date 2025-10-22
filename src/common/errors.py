"""
Domain-specific error types for PneumoStabSim
"""


class PneumoStabSimError(Exception):
    """Base exception for all PneumoStabSim errors"""

    pass


class ModelConfigError(PneumoStabSimError):
    """Raised when configuration parameters are invalid or inconsistent"""

    pass


class InvariantViolation(PneumoStabSimError):
    """Raised when domain invariants are violated"""

    pass


class GeometryError(InvariantViolation):
    """Raised when geometric constraints are violated"""

    pass


class ConnectionError(PneumoStabSimError):
    """Raised when pneumatic connections are invalid"""

    pass


class VolumeError(InvariantViolation):
    """Raised when volume calculations result in invalid values"""

    pass


class ThermoError(PneumoStabSimError):
    """Raised when thermodynamic calculations fail"""

    pass
