"""
Mechanical components: levers, springs, dampers
Minimal stubs for physics integration
"""

from dataclasses import dataclass

# TODO: Replace with real implementations


@dataclass
class Lever:
    """Lever mechanism stub"""

    length: float = 0.8
    pivot_distance: float = 0.2

    def angle_to_displacement(self, angle: float) -> float:
        """Convert lever angle to linear displacement"""
        return self.pivot_distance * angle


@dataclass
class Spring:
    """One-sided spring stub"""

    k: float = 50000.0  # Spring constant (N/m)
    rest_length: float = 0.0  # Rest position

    def force(self, position: float) -> float:
        """Compute spring force (compression only)"""
        compression = self.rest_length - position
        return self.k * max(0.0, compression)


@dataclass
class Damper:
    """Linear damper stub"""

    c: float = 2000.0  # Damping coefficient (N?s/m)
    threshold: float = 50.0  # Minimum force threshold

    def force(self, velocity: float) -> float:
        """Compute damper force"""
        F = self.c * velocity
        return F if abs(F) > self.threshold else 0.0


@dataclass
class PneumaticCylinder:
    """Pneumatic cylinder stub"""

    area_head: float = 0.005  # Head area (m?)
    area_rod: float = 0.004  # Rod area (m?)

    def force(self, p_head: float, p_rod: float) -> float:
        """Compute net cylinder force"""
        return p_head * self.area_head - p_rod * self.area_rod
