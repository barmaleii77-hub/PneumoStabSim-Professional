"""
Cylinder specification and state
Handles volume calculations and lever angle integration
"""

from dataclasses import dataclass
from .geometry import CylinderGeom, LeverGeom
from .types import ValidationResult
from src.common.errors import GeometryError


@dataclass
class CylinderSpec:
    """Cylinder specification combining geometry with position info"""

    geometry: CylinderGeom
    is_front: bool  # True for front axle, False for rear axle
    lever_geom: LeverGeom  # Associated lever geometry

    def validate_invariants(self) -> ValidationResult:
        """Validate cylinder specification"""
        geom_result = self.geometry.validate_invariants()
        lever_result = self.lever_geom.validate_invariants()

        errors = geom_result["errors"] + lever_result["errors"]
        warnings = geom_result["warnings"] + lever_result["warnings"]

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )


@dataclass
class CylinderState:
    """Cylinder state with position-dependent volume calculations"""

    spec: CylinderSpec
    x: float = 0.0  # Piston position relative to center (m), x=0 means equal volumes
    penetration_head: float = 0.0  # Penetration beyond head stop (m)
    penetration_rod: float = 0.0  # Penetration beyond rod stop (m)

    def __post_init__(self):
        # Validate initial position is within travel limits
        max_travel = self.spec.geometry.L_travel_max
        half_travel = max_travel / 2.0
        if abs(self.x) > half_travel:
            raise GeometryError(
                f"Initial position x={self.x} exceeds travel limit +/-{half_travel}"
            )
        # Ensure contact state is consistent with the initial displacement
        self.apply_displacement(self.x)

    def vol_head(self, x: float = None) -> float:
        """Calculate head chamber volume at given position

        Args:
            x: Piston position (m), uses self.x if None

        Returns:
            Head chamber volume (m^3)
        """
        if x is None:
            x = self.x

        geom = self.spec.geometry
        area = geom.area_head(self.spec.is_front)

        # Volume = area * (distance from head to piston)
        # Center position has piston at L_inner/2, head dead zone reduces available length
        distance_from_head = geom.L_inner / 2.0 - x - geom.L_dead_head
        volume = area * distance_from_head

        # Ensure minimum volume
        min_vol = geom.min_volume_head(self.spec.is_front)
        return max(volume, min_vol)

    def vol_rod(self, x: float = None) -> float:
        """Calculate rod chamber volume at given position

        Args:
            x: Piston position (m), uses self.x if None

        Returns:
            Rod chamber volume (m^3)
        """
        if x is None:
            x = self.x

        geom = self.spec.geometry
        area = geom.area_rod(self.spec.is_front)

        # Volume = effective_area * (distance from rod end to piston)
        # Rod side has reduced area due to rod presence
        distance_from_rod = geom.L_inner / 2.0 + x - geom.L_dead_rod
        volume = area * distance_from_rod

        # Ensure minimum volume
        min_vol = geom.min_volume_rod(self.spec.is_front)
        return max(volume, min_vol)

    def apply_displacement(self, displacement: float) -> None:
        """Apply piston displacement while tracking stop penetrations."""

        geom = self.spec.geometry
        half_travel = geom.L_travel_max / 2.0

        # Calculate penetration beyond the mechanical stops
        penetration_head = max(0.0, displacement - half_travel)
        penetration_rod = max(0.0, -half_travel - displacement)

        # Numerical noise can produce both penetrations at ~0. Handle explicitly.
        if penetration_head > 0.0 and penetration_rod > 0.0:
            if penetration_head > penetration_rod:
                penetration_rod = 0.0
            else:
                penetration_head = 0.0

        self.penetration_head = penetration_head
        self.penetration_rod = penetration_rod

        # Clamp position to travel limits
        self.x = max(-half_travel, min(half_travel, displacement))

    def update_from_lever_angle(self, angle_rad: float):
        """Update piston position based on lever angle

        Args:
            angle_rad: Lever angle in radians from horizontal
        """
        lever = self.spec.lever_geom
        geom = self.spec.geometry

        # Get rod joint position on lever
        rod_x, rod_y = lever.rod_joint_pos(angle_rad)

        # Rod joint coordinates in 3D space (assuming lever rotates in YZ plane at X=0)
        rod_joint_3d = (0.0, rod_x, geom.Z_axle + rod_y)

        # Cylinder tail position
        tail_3d = (0.0, geom.Y_tail, geom.Z_axle)

        # Project to cylinder axis length
        cylinder_length = geom.project_to_cyl_axis(tail_3d, rod_joint_3d)

        # Convert to piston displacement from center
        # When lever is horizontal (angle=0), piston should be at center (x=0)
        nominal_length = geom.project_to_cyl_axis(
            tail_3d, (0.0, lever.rod_joint_frac * lever.L_lever, geom.Z_axle)
        )

        # Displacement from nominal position
        delta_length = cylinder_length - nominal_length

        # Apply displacement and track contact penetration
        self.apply_displacement(delta_length)

    def validate_invariants(self) -> ValidationResult:
        """Validate cylinder state invariants"""
        errors = []
        warnings = []

        # Validate specification first
        spec_result = self.spec.validate_invariants()
        errors.extend(spec_result["errors"])
        warnings.extend(spec_result["warnings"])

        # Check position limits
        max_travel = self.spec.geometry.L_travel_max
        if abs(self.x) > max_travel / 2.0:
            errors.append(
                f"Position x={self.x} exceeds travel limit +/-{max_travel / 2.0}"
            )

        # Check minimum volumes at current position
        vol_head = self.vol_head()
        vol_rod = self.vol_rod()
        min_vol_head = self.spec.geometry.min_volume_head(self.spec.is_front)
        min_vol_rod = self.spec.geometry.min_volume_rod(self.spec.is_front)

        if vol_head < min_vol_head * 0.999:  # Small tolerance for floating point
            errors.append(
                f"Head volume {vol_head:.6f} below minimum {min_vol_head:.6f}"
            )
        if vol_rod < min_vol_rod * 0.999:
            errors.append(f"Rod volume {vol_rod:.6f} below minimum {min_vol_rod:.6f}")

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )
