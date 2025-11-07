"""
Geometry and invariants for pneumatic system
All calculations in SI units (meters)
"""

import math
from dataclasses import dataclass
from src.common.units import MIN_VOLUME_FRACTION
from src.common.errors import GeometryError
from .types import ValidationResult


@dataclass
class FrameGeom:
    """Frame geometry with symmetry plane YZ at X=0

    Coordinate system:
    - Rear lower point of frame: (0, 0, 0)
    - Front lower point: (0, 0, L_wb)
    - Symmetry plane: YZ (X=0)
    """

    L_wb: float  # Wheelbase length (m)

    def __post_init__(self):
        if self.L_wb <= 0:
            raise GeometryError(f"Wheelbase L_wb must be positive, got {self.L_wb}")

    def validate_invariants(self) -> ValidationResult:
        """Validate frame geometry invariants"""
        errors = []
        warnings = []

        if self.L_wb <= 0:
            errors.append(f"Wheelbase L_wb must be positive, got {self.L_wb}")
        elif self.L_wb < 2.0:
            warnings.append(f"Wheelbase L_wb={self.L_wb}m seems too small for vehicle")
        elif self.L_wb > 10.0:
            warnings.append(f"Wheelbase L_wb={self.L_wb}m seems too large for vehicle")

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )


@dataclass
class LeverGeom:
    """Lever geometry with invariants

    Maintains consistency between lever length and frame-to-hinge distance
    """

    L_lever: float  # Lever length (m)
    rod_joint_frac: float  # Rod joint position as fraction of lever length (0.1..0.9)
    d_frame_to_lever_hinge: float  # Distance from symmetry plane to lever hinge (m)

    def __post_init__(self):
        self._validate_parameters()

    def _validate_parameters(self):
        """Validate lever parameters"""
        if self.L_lever <= 0:
            raise GeometryError(
                f"Lever length L_lever must be positive, got {self.L_lever}"
            )

        if not (0.1 <= self.rod_joint_frac <= 0.9):
            raise GeometryError(
                f"Rod joint fraction must be in [0.1, 0.9], got {self.rod_joint_frac}"
            )

        if self.d_frame_to_lever_hinge <= 0:
            raise GeometryError(
                f"Frame-to-hinge distance must be positive, got {self.d_frame_to_lever_hinge}"
            )

    def lever_tip_pos(self, angle: float) -> tuple[float, float]:
        """Calculate lever tip position in the axle plane

        Args:
            angle: Lever angle in radians from horizontal

        Returns:
            (x, y) position of lever tip
        """
        x = self.L_lever * math.cos(angle)
        y = self.L_lever * math.sin(angle)
        return (x, y)

    def rod_joint_pos(self, angle: float) -> tuple[float, float]:
        """Calculate rod joint position on lever

        Args:
            angle: Lever angle in radians from horizontal

        Returns:
            (x, y) position of rod joint
        """
        dist_from_hinge = self.rod_joint_frac * self.L_lever
        x = dist_from_hinge * math.cos(angle)
        y = dist_from_hinge * math.sin(angle)
        return (x, y)

    def validate_invariants(self) -> ValidationResult:
        """Validate lever geometry invariants"""
        errors = []
        warnings = []

        try:
            self._validate_parameters()
        except GeometryError as e:
            errors.append(str(e))

        # Check for reasonable dimensions
        if self.L_lever < 0.1:
            warnings.append(f"Lever length L_lever={self.L_lever}m seems too small")
        elif self.L_lever > 2.0:
            warnings.append(f"Lever length L_lever={self.L_lever}m seems too large")

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )


@dataclass
class CylinderGeom:
    """Cylinder geometry with full invariant validation

    Separate specifications for front and rear cylinders
    """

    # Cylinder dimensions
    D_in_front: float  # Front cylinder inner diameter (m)
    D_in_rear: float  # Rear cylinder inner diameter (m)
    D_out_front: float  # Front cylinder outer diameter (m)
    D_out_rear: float  # Rear cylinder outer diameter (m)
    L_inner: float  # Internal chamber length (m)
    t_piston: float  # Piston thickness (m)

    # Rod specifications
    D_rod: float  # Rod diameter (m)
    link_rod_diameters_front_rear: bool  # If True, both cylinders use same rod diameter

    # Dead zones
    L_dead_head: float  # Head side dead zone length (m)
    L_dead_rod: float  # Rod side dead zone length (m)

    # Safety parameters
    residual_frac_min: float = MIN_VOLUME_FRACTION  # Minimum residual volume fraction

    # Position coordinates
    Y_tail: float = 0.0  # Tail Y coordinate (m)
    Z_axle: float = 0.0  # Axle height (m)

    def __post_init__(self):
        self._validate_parameters()

    def _validate_parameters(self):
        """Validate all cylinder parameters"""
        # Positive dimensions
        params_positive = [
            (self.D_in_front, "D_in_front"),
            (self.D_in_rear, "D_in_rear"),
            (self.D_out_front, "D_out_front"),
            (self.D_out_rear, "D_out_rear"),
            (self.L_inner, "L_inner"),
            (self.t_piston, "t_piston"),
            (self.D_rod, "D_rod"),
            (self.L_dead_head, "L_dead_head"),
            (self.L_dead_rod, "L_dead_rod"),
        ]

        for value, name in params_positive:
            if value <= 0:
                raise GeometryError(f"{name} must be positive, got {value}")

        # Diameter constraints
        if self.D_in_front >= self.D_out_front:
            raise GeometryError("Front inner diameter must be less than outer diameter")
        if self.D_in_rear >= self.D_out_rear:
            raise GeometryError("Rear inner diameter must be less than outer diameter")

        # Rod diameter constraint
        max_rod_diameter = (
            min(self.D_in_front, self.D_in_rear) * 0.8
        )  # Leave 20% margin
        if self.D_rod >= max_rod_diameter:
            raise GeometryError(
                f"Rod diameter {self.D_rod} too large for cylinder bores"
            )

        # Residual fraction
        if not (0.001 <= self.residual_frac_min <= 0.1):
            raise GeometryError(
                f"Residual fraction must be in [0.001, 0.1], got {self.residual_frac_min}"
            )

        # Travel validation
        L_travel_max = self.L_inner - (
            self.L_dead_head + self.L_dead_rod + self.t_piston
        )
        if L_travel_max <= 0:
            raise GeometryError(
                f"No travel available: L_inner={self.L_inner}, dead zones + piston={self.L_dead_head + self.L_dead_rod + self.t_piston}"
            )

    @property
    def L_travel_max(self) -> float:
        """Maximum piston travel distance"""
        return self.L_inner - (self.L_dead_head + self.L_dead_rod + self.t_piston)

    def area_head(self, is_front: bool) -> float:
        """Calculate head chamber area"""
        diameter = self.D_in_front if is_front else self.D_in_rear
        return math.pi * (diameter / 2.0) ** 2

    def area_rod(self, is_front: bool) -> float:
        """Calculate rod chamber effective area (head area minus rod area)"""
        area_head = self.area_head(is_front)
        area_rod_steel = math.pi * (self.D_rod / 2.0) ** 2
        return area_head - area_rod_steel

    def min_volume_head(self, is_front: bool) -> float:
        """Minimum allowable head chamber volume"""
        return self.residual_frac_min * (self.area_head(is_front) * self.L_inner)

    def min_volume_rod(self, is_front: bool) -> float:
        """Minimum allowable rod chamber volume"""
        return self.residual_frac_min * (self.area_rod(is_front) * self.L_inner)

    def project_to_cyl_axis(
        self,
        tail_point: tuple[float, float, float],
        joint_point: tuple[float, float, float],
    ) -> float:
        """Project geometry change to cylinder axis displacement

        Args:
            tail_point: Cylinder tail attachment point (x, y, z)
            joint_point: Rod joint point (x, y, z)

        Returns:
            Cylinder length along axis
        """
        dx = joint_point[0] - tail_point[0]
        dy = joint_point[1] - tail_point[1]
        dz = joint_point[2] - tail_point[2]
        return math.sqrt(dx * dx + dy * dy + dz * dz)

    def validate_invariants(self) -> ValidationResult:
        """Validate cylinder geometry invariants"""
        errors = []
        warnings = []

        try:
            self._validate_parameters()
        except GeometryError as e:
            errors.append(str(e))
            return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

        # Check travel constraints at extremes
        half_travel = self.L_travel_max / 2.0

        for is_front in [True, False]:
            label = "front" if is_front else "rear"

            # Volume at maximum extension (x = +half_travel)
            vol_head_max = self.area_head(is_front) * (
                self.L_inner / 2.0 - half_travel - self.L_dead_head
            )
            vol_rod_max = self.area_rod(is_front) * (
                self.L_inner / 2.0 + half_travel - self.L_dead_rod
            )

            # Volume at maximum compression (x = -half_travel)
            vol_head_min = self.area_head(is_front) * (
                self.L_inner / 2.0 + half_travel - self.L_dead_head
            )
            vol_rod_min = self.area_rod(is_front) * (
                self.L_inner / 2.0 - half_travel - self.L_dead_rod
            )

            min_vol_head = self.min_volume_head(is_front)
            min_vol_rod = self.min_volume_rod(is_front)

            if vol_head_max < min_vol_head:
                errors.append(
                    f"{label} head volume at max extension below minimum: {vol_head_max:.6f} < {min_vol_head:.6f}"
                )
            if vol_head_min < min_vol_head:
                errors.append(
                    f"{label} head volume at max compression below minimum: {vol_head_min:.6f} < {min_vol_head:.6f}"
                )
            if vol_rod_max < min_vol_rod:
                errors.append(
                    f"{label} rod volume at max extension below minimum: {vol_rod_max:.6f} < {min_vol_rod:.6f}"
                )
            if vol_rod_min < min_vol_rod:
                errors.append(
                    f"{label} rod volume at max compression below minimum: {vol_rod_min:.6f} < {min_vol_rod:.6f}"
                )

        return ValidationResult(
            is_valid=len(errors) == 0, errors=errors, warnings=warnings
        )
