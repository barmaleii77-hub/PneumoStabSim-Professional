"""
Type definitions and protocols for pneumatic domain
"""

from typing import TypedDict, Protocol, Tuple
from .enums import Wheel, Port, Line


class ValidationResult(TypedDict):
    """Result of invariant validation"""

    is_valid: bool
    errors: list[str]
    warnings: list[str]


class GeometryValidationResult(ValidationResult):
    """Extended validation result for geometry"""

    computed_values: dict[str, float]


class ConnectionEndpoint(TypedDict):
    """Pneumatic connection endpoint"""

    wheel: Wheel
    port: Port


class LineConnection(TypedDict):
    """Complete line connection specification"""

    line: Line
    endpoints: tuple[ConnectionEndpoint, ConnectionEndpoint]


class Validatable(Protocol):
    """Protocol for objects that can validate their invariants"""

    def validate_invariants(self) -> ValidationResult:
        """Validate object invariants and return detailed results"""
        ...


class GeometryProvider(Protocol):
    """Protocol for objects that provide geometric calculations"""

    def compute_position(self, angle: float) -> tuple[float, float]:
        """Compute position based on angle"""
        ...

    def compute_length(self) -> float:
        """Compute current length"""
        ...
