"""
Pneumatic system assembly and validation
Manages 4 cylinders and 4 lines with diagonal connection scheme
"""

from dataclasses import dataclass
from typing import Dict, List
from .enums import Line, Wheel, Port
from .cylinder import CylinderState, CylinderSpec
from .line import PneumoLine
from .receiver import ReceiverState
from .types import ValidationResult
from src.common.errors import ConnectionError


@dataclass
class PneumaticSystem:
    """Complete pneumatic stabilizer system"""

    cylinders: Dict[Wheel, CylinderState]  # One cylinder per wheel
    lines: Dict[Line, PneumoLine]  # Four diagonal pneumatic lines
    receiver: ReceiverState  # Pressure tank
    master_isolation_open: bool = False  # Master isolation valve state

    def __post_init__(self):
        self._validate_system_configuration()

    def _validate_system_configuration(self):
        """Validate system-level configuration"""
        # Check we have all 4 wheels
        expected_wheels = {Wheel.LP, Wheel.PP, Wheel.LZ, Wheel.PZ}
        actual_wheels = set(self.cylinders.keys())
        if actual_wheels != expected_wheels:
            raise ConnectionError(
                f"Must have cylinders for all wheels. Expected {expected_wheels}, got {actual_wheels}"
            )

        # Check we have all 4 lines
        expected_lines = {Line.A1, Line.B1, Line.A2, Line.B2}
        actual_lines = set(self.lines.keys())
        if actual_lines != expected_lines:
            raise ConnectionError(
                f"Must have all 4 lines. Expected {expected_lines}, got {actual_lines}"
            )

        # Validate diagonal connection scheme
        self._validate_diagonal_connections()

    def _validate_diagonal_connections(self):
        """Validate the diagonal connection scheme

        Expected connections:
        A1: (LP,ROD) ? (PZ,HEAD) - Left Front Rod to Right Rear Head
        B1: (LP,HEAD) ? (PZ,ROD) - Left Front Head to Right Rear Rod
        A2: (PP,ROD) ? (LZ,HEAD) - Right Front Rod to Left Rear Head
        B2: (PP,HEAD) ? (LZ,ROD) - Right Front Head to Left Rear Rod
        """
        expected_connections = {
            Line.A1: {(Wheel.LP, Port.ROD), (Wheel.PZ, Port.HEAD)},
            Line.B1: {(Wheel.LP, Port.HEAD), (Wheel.PZ, Port.ROD)},
            Line.A2: {(Wheel.PP, Port.ROD), (Wheel.LZ, Port.HEAD)},
            Line.B2: {(Wheel.PP, Port.HEAD), (Wheel.LZ, Port.ROD)},
        }

        for line_name, expected_endpoints in expected_connections.items():
            if line_name not in self.lines:
                raise ConnectionError(f"Missing line {line_name.value}")

            line = self.lines[line_name]
            actual_endpoints = set(line.endpoints)

            if actual_endpoints != expected_endpoints:
                raise ConnectionError(
                    f"Line {line_name.value} has incorrect connections. "
                    f"Expected {expected_endpoints}, got {actual_endpoints}"
                )

    def get_cylinder_for_endpoint(self, wheel: Wheel, port: Port) -> CylinderState:
        """Get cylinder state for a specific wheel/port combination"""
        if wheel not in self.cylinders:
            raise ConnectionError(f"No cylinder found for wheel {wheel.value}")
        return self.cylinders[wheel]

    def get_connected_cylinders(self, line_name: Line) -> List[tuple]:
        """Get cylinders connected by a specific line

        Returns:
            List of (wheel, port, cylinder_state) tuples
        """
        if line_name not in self.lines:
            raise ConnectionError(f"Line {line_name.value} not found")

        line = self.lines[line_name]
        connected = []

        for wheel, port in line.endpoints:
            cylinder = self.get_cylinder_for_endpoint(wheel, port)
            connected.append((wheel, port, cylinder))

        return connected

    def update_system_from_lever_angles(self, angles: Dict[Wheel, float]):
        """Update all cylinder positions from lever angles

        Args:
            angles: Dictionary mapping Wheel to angle in radians
        """
        missing_angles = set(self.cylinders.keys()) - set(angles.keys())
        if missing_angles:
            raise ValueError(f"Missing lever angles for wheels: {missing_angles}")

        for wheel, angle in angles.items():
            if wheel in self.cylinders:
                self.cylinders[wheel].update_from_lever_angle(angle)

    def get_line_volumes(self) -> Dict[Line, Dict[str, float]]:
        """Calculate current volumes for all line connections

        Returns:
            Dictionary mapping line names to volume information
        """
        line_volumes = {}

        for line_name, line in self.lines.items():
            volumes = {"total_volume": 0.0, "endpoints": []}

            for wheel, port in line.endpoints:
                cylinder = self.cylinders[wheel]

                if port == Port.HEAD:
                    volume = cylinder.vol_head()
                else:  # Port.ROD
                    volume = cylinder.vol_rod()

                volumes["total_volume"] += volume
                endpoint = {
                    "wheel": wheel.value,
                    "port": port.value,
                    "volume": volume,
                }
                volumes["endpoints"].append(endpoint)

            line_volumes[line_name] = volumes

        return line_volumes

    def validate_invariants(self) -> ValidationResult:
        """Validate all system invariants"""
        errors = []
        warnings = []

        # Validate system configuration
        try:
            self._validate_system_configuration()
        except (ConnectionError, ValueError) as e:
            errors.append(str(e))
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        # Validate each cylinder
        for wheel, cylinder in self.cylinders.items():
            cyl_result = cylinder.validate_invariants()
            if not cyl_result["is_valid"]:
                cylinder_errors = [
                    f"Cylinder {wheel.value}: {err}" for err in cyl_result["errors"]
                ]
                errors.extend(cylinder_errors)
            cylinder_warnings = [
                f"Cylinder {wheel.value}: {warn}" for warn in cyl_result["warnings"]
            ]
            warnings.extend(cylinder_warnings)

        # Validate each line
        for line_name, line in self.lines.items():
            line_result = line.validate_invariants()
            if not line_result["is_valid"]:
                line_errors = [
                    f"Line {line_name.value}: {err}" for err in line_result["errors"]
                ]
                errors.extend(line_errors)
            line_warnings = [
                f"Line {line_name.value}: {warn}" for warn in line_result["warnings"]
            ]
            warnings.extend(line_warnings)

        # Validate receiver
        receiver_result = self.receiver.validate_invariants()
        if not receiver_result["is_valid"]:
            errors.extend([f"Receiver: {err}" for err in receiver_result["errors"]])
        warnings.extend([f"Receiver: {warn}" for warn in receiver_result["warnings"]])

        # System-level checks
        line_volumes = self.get_line_volumes()
        for line_name, volume_info in line_volumes.items():
            if volume_info["total_volume"] <= 0:
                errors.append(
                    f"Line {line_name.value} has zero or negative total volume"
                )

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )


def create_standard_diagonal_system(
    cylinder_specs: Dict[Wheel, CylinderSpec],
    line_configs: Dict[Line, dict],
    receiver: ReceiverState,
    master_isolation_open: bool = False,
) -> PneumaticSystem:
    """Factory function to create a standard diagonal pneumatic system

    Args:
        cylinder_specs: Cylinder specifications for each wheel
        line_configs: Line configuration (valves, initial pressure)
        receiver: Receiver state
        master_isolation_open: Initial isolation valve state

    Returns:
        Configured PneumaticSystem
    """
    # Create cylinder states
    cylinders = {
        wheel: CylinderState(spec=spec) for wheel, spec in cylinder_specs.items()
    }

    # Create lines with standard diagonal connections

    standard_connections = {
        Line.A1: ((Wheel.LP, Port.ROD), (Wheel.PZ, Port.HEAD)),
        Line.B1: ((Wheel.LP, Port.HEAD), (Wheel.PZ, Port.ROD)),
        Line.A2: ((Wheel.PP, Port.ROD), (Wheel.LZ, Port.HEAD)),
        Line.B2: ((Wheel.PP, Port.HEAD), (Wheel.LZ, Port.ROD)),
    }

    lines = {}
    for line_name, endpoints in standard_connections.items():
        config = line_configs[line_name]
        lines[line_name] = PneumoLine(
            name=line_name,
            endpoints=endpoints,
            cv_atmo=config["cv_atmo"],
            cv_tank=config["cv_tank"],
            p_line=config.get("p_line", 101325.0),  # Default to atmospheric
        )

    return PneumaticSystem(
        cylinders=cylinders,
        lines=lines,
        receiver=receiver,
        master_isolation_open=master_isolation_open,
    )
