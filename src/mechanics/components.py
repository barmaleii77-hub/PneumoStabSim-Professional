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


@dataclass
class DetailedLever:
    """Detailed lever mechanics"""

    length: float = 0.8
    pivot_distance: float = 0.2
    angle: float = 0.0

    def apply_force(self, force_magnitude: float, force_angle: float):
        """Apply a force to the lever"""
        # TODO: Implement force application
        pass

    def compute_torque(self) -> float:
        """Compute torque around the pivot"""
        return self.angle_to_displacement(self.angle) * self.length

    def angle_to_displacement(self, angle: float) -> float:
        """Convert lever angle to linear displacement"""
        return self.pivot_distance * angle


@dataclass
class DetailedSpring:
    """Detailed spring mechanics"""

    k: float = 50000.0  # Spring constant (N/m)
    rest_length: float = 0.0  # Rest position
    damping_coefficient: float = 5.0  # Critical damping coefficient
    position: float = 0.0  # Current position
    velocity: float = 0.0  # Current velocity
    acceleration: float = 0.0  # Current acceleration

    def apply_force(self, force: float):
        """Apply a force to the spring-mass system"""
        # TODO: Implement force application
        pass

    def update(self, time_step: float):
        """Update the spring-mass system state"""
        # TODO: Implement system dynamics
        pass

    def force(self, position: float) -> float:
        """Compute spring force (compression only)"""
        compression = self.rest_length - position
        return self.k * max(0.0, compression)

    def damping_force(self) -> float:
        """Compute the damping force"""
        return -self.damping_coefficient * self.velocity


@dataclass
class DetailedDamper:
    """Detailed damper mechanics"""

    c: float = 2000.0  # Damping coefficient (N?s/m)
    threshold: float = 50.0  # Minimum force threshold
    extension: float = 0.0  # Current extension
    velocity: float = 0.0  # Current velocity

    def apply_force(self, force: float):
        """Apply a force to the damper"""
        # TODO: Implement force application
        pass

    def force(self, velocity: float) -> float:
        """Compute damper force"""
        F = self.c * velocity
        return F if abs(F) > self.threshold else 0.0


@dataclass
class DetailedPneumaticCylinder:
    """Detailed pneumatic cylinder mechanics"""

    area_head: float = 0.005  # Head area (m?)
    area_rod: float = 0.004  # Rod area (m?)
    damping_coefficient: float = 5.0  # Critical damping coefficient
    position: float = 0.0  # Current position
    velocity: float = 0.0  # Current velocity
    acceleration: float = 0.0  # Current acceleration

    def apply_force(self, force: float):
        """Apply a force to the cylinder"""
        # TODO: Implement force application
        pass

    def update(self, time_step: float):
        """Update the cylinder state"""
        # TODO: Implement state update
        pass

    def force(self, p_head: float, p_rod: float) -> float:
        """Compute net cylinder force"""
        return p_head * self.area_head - p_rod * self.area_rod

    def damping_force(self) -> float:
        """Compute the damping force"""
        return -self.damping_coefficient * self.velocity
