"""
Pneumatic line components
Connects cylinders with valve control
"""

from dataclasses import dataclass
from typing import Tuple
from .enums import Line, Wheel, Port
from .valves import CheckValve
from .types import ValidationResult


@dataclass
class PneumoLine:
    """Pneumatic line connecting two cylinder ports"""

    name: Line
    endpoints: Tuple[
        Tuple[Wheel, Port], Tuple[Wheel, Port]
    ]  # ((wheel1, port1), (wheel2, port2))
    cv_atmo: CheckValve  # Check valve from atmosphere to line
    cv_tank: CheckValve  # Check valve from line to receiver tank
    p_line: float  # Current line pressure (Pa)

    def __post_init__(self):
        self._validate_configuration()

    def _validate_configuration(self):
        """Validate line configuration"""
        if len(self.endpoints) != 2:
            raise ValueError(
                f"Line must have exactly 2 endpoints, got {len(self.endpoints)}"
            )

        # Ensure endpoints are properly formed
        for i, endpoint in enumerate(self.endpoints):
            if len(endpoint) != 2:
                raise ValueError(
                    f"Endpoint {i} must be (Wheel, Port) tuple, got {endpoint}"
                )
            wheel, port = endpoint
            if not isinstance(wheel, Wheel):
                raise ValueError(
                    f"Endpoint {i} wheel must be Wheel enum, got {type(wheel)}"
                )
            if not isinstance(port, Port):
                raise ValueError(
                    f"Endpoint {i} port must be Port enum, got {type(port)}"
                )

        # Ensure endpoints are different
        if self.endpoints[0] == self.endpoints[1]:
            raise ValueError(f"Line endpoints cannot be identical: {self.endpoints[0]}")

        if self.p_line < 0:
            raise ValueError(f"Line pressure cannot be negative, got {self.p_line}")

    def get_connection_description(self) -> str:
        """Get human-readable connection description"""
        (wheel1, port1), (wheel2, port2) = self.endpoints
        return f"{wheel1.value}:{port1.value} <-> {wheel2.value}:{port2.value}"

    def is_diagonal_connection(self) -> bool:
        """Check if this line represents a diagonal connection

        Diagonal connections link opposite corners:
        - Front-left with rear-right
        - Front-right with rear-left
        """
        (wheel1, port1), (wheel2, port2) = self.endpoints

        # Get position indicators
        wheels = {wheel1, wheel2}

        # Check for front-rear pairing
        front_wheels = {Wheel.LP, Wheel.PP}  # Left/Right Front
        rear_wheels = {Wheel.LZ, Wheel.PZ}  # Left/Right Rear

        has_front = bool(wheels & front_wheels)
        has_rear = bool(wheels & rear_wheels)

        if not (has_front and has_rear):
            return False  # Not front-rear pairing

        # Check for left-right crossing
        left_wheels = {Wheel.LP, Wheel.LZ}  # Left Front/Rear
        right_wheels = {Wheel.PP, Wheel.PZ}  # Right Front/Rear

        has_left = bool(wheels & left_wheels)
        has_right = bool(wheels & right_wheels)

        return has_left and has_right  # Cross-diagonal

    def validate_invariants(self) -> ValidationResult:
        """Validate pneumatic line invariants"""
        errors = []
        warnings = []

        # Validate configuration
        try:
            self._validate_configuration()
        except ValueError as e:
            errors.append(str(e))
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        # Validate check valves
        cv_atmo_result = self.cv_atmo.validate_invariants()
        cv_tank_result = self.cv_tank.validate_invariants()

        errors.extend(cv_atmo_result["errors"])
        errors.extend(cv_tank_result["errors"])
        warnings.extend(cv_atmo_result["warnings"])
        warnings.extend(cv_tank_result["warnings"])

        # Validate line pressure
        if self.p_line > 1e7:  # > 100 bar
            warnings.append(f"Very high line pressure: {self.p_line} Pa")

        # Check for proper diagonal configuration (warning if not)
        if not self.is_diagonal_connection():
            warnings.append(
                f"Line {self.name.value} is not a diagonal connection: {self.get_connection_description()}"
            )

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )
