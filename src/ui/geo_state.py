"""
GeometryState: Centralized geometry management with kinematic constraints
"""

from dataclasses import dataclass, field
from typing import Dict, List, Tuple
import math

# Try to import kinematics modules
try:
    from ..mechanics.kinematics import LeverKinematics, CylinderKinematics
    from ..core.geometry import Point2

    KINEMATICS_AVAILABLE = True
except ImportError:
    KINEMATICS_AVAILABLE = False
    print("Warning: Kinematics modules not available, using simplified calculations")


@dataclass
class GeometryState:
    """Centralized geometry state with kinematic constraints"""

    # Frame dimensions
    wheelbase: float = 3.200
    track: float = 1.600

    # Suspension geometry
    frame_to_pivot: float = 0.600
    lever_length: float = 0.800
    rod_position: float = 0.600

    # Cylinder geometry (unified)
    cylinder_length: float = 0.500
    cyl_diam_m: float = 0.080
    rod_diam_m: float = 0.035
    stroke_m: float = 0.300
    piston_thickness_m: float = 0.020
    dead_gap_m: float = 0.005

    # Validation state
    _validation_errors: list[str] = field(default_factory=list)
    _validation_warnings: list[str] = field(default_factory=list)

    def __post_init__(self):
        """Initialize and validate after creation"""
        self.validate_all_constraints()

    def calculate_stroke_max_kinematic(self) -> float:
        """Calculate maximum stroke from kinematic constraints"""
        if not KINEMATICS_AVAILABLE:
            return self._calculate_stroke_max_geometric()

        try:
            # Create lever kinematics
            lever_kin = LeverKinematics(
                arm_length=self.lever_length,
                pivot_position=Point2(0.0, 0.0),
                pivot_offset_from_frame=self.frame_to_pivot,
                rod_attach_fraction=self.rod_position,
            )

            # Calculate maximum lever angle
            max_angle_rad = self._calculate_max_lever_angle()

            # Get lever states at extreme positions
            state_positive = lever_kin.solve_from_angle(max_angle_rad)
            state_negative = lever_kin.solve_from_angle(-max_angle_rad)

            # Create cylinder kinematics
            frame_hinge = Point2(-0.1, 0.0)
            cyl_kin = CylinderKinematics(
                frame_hinge=frame_hinge,
                inner_diameter=self.cyl_diam_m,
                rod_diameter=self.rod_diam_m,
                piston_thickness=self.piston_thickness_m,
                body_length=self.cylinder_length,
                dead_zone_rod=self.dead_gap_m * math.pi * (self.cyl_diam_m / 2) ** 2,
                dead_zone_head=self.dead_gap_m * math.pi * (self.cyl_diam_m / 2) ** 2,
            )

            # Calculate strokes at extreme positions
            cyl_state_pos = cyl_kin.solve_from_lever_state(state_positive)
            cyl_state_neg = cyl_kin.solve_from_lever_state(state_negative)

            # Maximum stroke is the range between extremes
            stroke_range = abs(cyl_state_pos.stroke - cyl_state_neg.stroke)

            return min(stroke_range, self._calculate_stroke_max_geometric())

        except Exception as e:
            print(f"Warning: Kinematic calculation failed: {e}")
            return self._calculate_stroke_max_geometric()

    def _calculate_stroke_max_geometric(self) -> float:
        """Fallback: geometric stroke limit from cylinder dimensions"""
        return self.cylinder_length - self.piston_thickness_m - 2 * self.dead_gap_m

    def _calculate_max_lever_angle(self) -> float:
        """Calculate maximum lever angle from wheelbase constraints"""
        clearance = 0.100  # 100mm safety clearance
        max_reach = self.wheelbase / 2.0 - clearance
        available_reach = max_reach - self.frame_to_pivot

        if available_reach >= self.lever_length:
            return math.pi / 2.0  # 90 degrees
        else:
            cos_theta_max = available_reach / self.lever_length
            cos_theta_max = min(cos_theta_max, 1.0)
            return math.acos(cos_theta_max)

    def validate_all_constraints(self) -> bool:
        """Validate all geometric and kinematic constraints"""
        self._validation_errors.clear()
        self._validation_warnings.clear()

        self._validate_wheelbase_geometry()
        self._validate_cylinder_constraints()
        self._validate_hydraulic_ratios()
        self._validate_kinematic_limits()

        return len(self._validation_errors) == 0

    def _validate_wheelbase_geometry(self):
        """Validate wheelbase vs lever geometry"""
        max_lever_reach = self.wheelbase / 2.0 - 0.100
        actual_reach = self.frame_to_pivot + self.lever_length

        if actual_reach > max_lever_reach:
            self._validation_errors.append(
                f"Lever geometry exceeds wheelbase: {actual_reach:.3f}m > {max_lever_reach:.3f}m"
            )
        elif actual_reach > max_lever_reach * 0.95:
            self._validation_warnings.append(
                f"Lever geometry close to wheelbase limit: {actual_reach:.3f}m vs {max_lever_reach:.3f}m"
            )

    def _validate_cylinder_constraints(self):
        """Validate cylinder geometric constraints"""
        min_cylinder_length = (
            self.stroke_m + self.piston_thickness_m + 2 * self.dead_gap_m
        )

        if self.cylinder_length < min_cylinder_length:
            self._validation_errors.append(
                f"Cylinder too short: {self.cylinder_length * 1000:.1f}mm < {min_cylinder_length * 1000:.1f}mm required"
            )
        elif self.cylinder_length < min_cylinder_length + 0.010:
            self._validation_warnings.append(
                f"Small cylinder clearance: {self.cylinder_length * 1000:.1f}mm vs {min_cylinder_length * 1000:.1f}mm required"
            )

    def _validate_hydraulic_ratios(self):
        """Validate hydraulic diameter ratios"""
        rod_to_cylinder_ratio = self.rod_diam_m / self.cyl_diam_m

        if rod_to_cylinder_ratio >= 0.8:
            self._validation_errors.append(
                f"Rod too large: {self.rod_diam_m * 1000:.1f}mm >= 80% of {self.cyl_diam_m * 1000:.1f}mm cylinder"
            )
        elif rod_to_cylinder_ratio >= 0.7:
            self._validation_warnings.append(
                f"Rod close to limit: {self.rod_diam_m * 1000:.1f}mm vs {self.cyl_diam_m * 1000:.1f}mm cylinder"
            )

    def _validate_kinematic_limits(self):
        """Validate kinematic constraints"""
        stroke_max_kinematic = self.calculate_stroke_max_kinematic()

        if self.stroke_m > stroke_max_kinematic:
            self._validation_errors.append(
                f"Stroke exceeds kinematic limit: {self.stroke_m * 1000:.1f}mm > {stroke_max_kinematic * 1000:.1f}mm"
            )
        elif self.stroke_m > stroke_max_kinematic * 0.95:
            self._validation_warnings.append(
                f"Stroke close to kinematic limit: {self.stroke_m * 1000:.1f}mm vs {stroke_max_kinematic * 1000:.1f}mm"
            )

    def normalize_parameter(
        self, param_name: str, value: float
    ) -> tuple[float, list[str]]:
        """Normalize parameter value and return corrections applied"""
        corrections = []
        normalized_value = value

        # Create temporary state for validation
        temp_state = GeometryState(**self.get_parameters())
        setattr(temp_state, param_name, value)

        if not temp_state.validate_all_constraints():
            # Apply corrections based on constraint violations
            if param_name == "stroke_m":
                stroke_max = self.calculate_stroke_max_kinematic()
                if value > stroke_max:
                    normalized_value = stroke_max
                    corrections.append(
                        f"Stroke limited to kinematic maximum: {stroke_max * 1000:.1f}mm"
                    )

            elif param_name == "rod_diam_m":
                max_rod = self.cyl_diam_m * 0.75  # Keep under 75% for safety
                if value > max_rod:
                    normalized_value = max_rod
                    corrections.append(
                        f"Rod diameter limited to 75% of cylinder: {max_rod * 1000:.1f}mm"
                    )

            elif param_name == "lever_length":
                max_lever_reach = self.wheelbase / 2.0 - 0.100
                max_lever = max_lever_reach - self.frame_to_pivot - 0.010  # 10mm safety
                if self.frame_to_pivot + value > max_lever_reach:
                    normalized_value = max_lever
                    corrections.append(
                        f"Lever length limited by wheelbase: {max_lever:.3f}m"
                    )

        return normalized_value, corrections

    def get_parameters(self) -> dict[str, float]:
        """Get all parameters as dictionary"""
        return {
            "wheelbase": self.wheelbase,
            "track": self.track,
            "frame_to_pivot": self.frame_to_pivot,
            "lever_length": self.lever_length,
            "rod_position": self.rod_position,
            "cylinder_length": self.cylinder_length,
            "cyl_diam_m": self.cyl_diam_m,
            "rod_diam_m": self.rod_diam_m,
            "stroke_m": self.stroke_m,
            "piston_thickness_m": self.piston_thickness_m,
            "dead_gap_m": self.dead_gap_m,
        }

    def set_parameters(self, params: dict[str, float]):
        """Set multiple parameters with validation"""
        for param_name, value in params.items():
            if hasattr(self, param_name):
                setattr(self, param_name, value)

        self.validate_all_constraints()

    def get_validation_results(self) -> tuple[list[str], list[str]]:
        """Get current validation errors and warnings"""
        return self._validation_errors.copy(), self._validation_warnings.copy()

    def get_computed_values(self) -> dict[str, float]:
        """Get computed/derived values"""
        area_head = math.pi * (self.cyl_diam_m / 2.0) ** 2
        area_rod = area_head - math.pi * (self.rod_diam_m / 2.0) ** 2

        return {
            "area_head": area_head,
            "area_rod": area_rod,
            "stroke_max_kinematic": self.calculate_stroke_max_kinematic(),
            "max_lever_angle_deg": math.degrees(self._calculate_max_lever_angle()),
        }

    def __str__(self) -> str:
        """String representation for debugging"""
        errors, warnings = self.get_validation_results()
        computed = self.get_computed_values()

        status = "VALID" if len(errors) == 0 else f"{len(errors)} ERRORS"
        if warnings:
            status += f" + {len(warnings)} WARNINGS"

        return (
            f"GeometryState [{status}]\n"
            f"  Wheelbase: {self.wheelbase:.3f}m, Track: {self.track:.3f}m\n"
            f"  Lever: {self.lever_length:.3f}m @ {self.frame_to_pivot:.3f}m offset\n"
            f"  Cylinder: {self.cyl_diam_m * 1000:.0f}mm x {self.cylinder_length * 1000:.0f}mm\n"
            f"  Stroke: {self.stroke_m * 1000:.0f}mm (max: {computed['stroke_max_kinematic'] * 1000:.0f}mm)\n"
            f"  Max lever angle: {computed['max_lever_angle_deg']:.1f} deg"
        )


def create_default_geometry() -> GeometryState:
    """Create geometry state with default truck parameters"""
    return GeometryState()


def create_light_commercial_geometry() -> GeometryState:
    """Create geometry state for light commercial vehicle"""
    return GeometryState(
        wheelbase=2.800,
        track=1.400,
        lever_length=0.700,
        frame_to_pivot=0.550,
        cyl_diam_m=0.065,
        rod_diam_m=0.028,
        stroke_m=0.250,
        cylinder_length=0.400,
        piston_thickness_m=0.015,
        dead_gap_m=0.003,
    )


def create_heavy_truck_geometry() -> GeometryState:
    """Create geometry state for heavy truck"""
    return GeometryState(
        wheelbase=3.800,
        track=1.900,
        lever_length=0.950,
        frame_to_pivot=0.700,
        rod_position=0.650,
        cyl_diam_m=0.100,
        rod_diam_m=0.045,
        stroke_m=0.400,
        cylinder_length=0.650,
        piston_thickness_m=0.025,
        dead_gap_m=0.007,
    )
