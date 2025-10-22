"""
Precise kinematics for P13 geometric engine

Implements:
- Lever kinematics (angle ? position)
- Cylinder kinematics (stroke ? volumes)
- Interference checking (capsule-capsule)

Coordinate system (per wheel plane):
- X: transverse from frame to wheel (+ outward)
- Y: vertical (+ up)
- ?: lever angle from X axis (CCW positive)

References:
- Inverse kinematics: https://www.cs.columbia.edu/~allen/F19/NOTES/stanfordinvkin.pdf
- numpy: https://numpy.org/doc/stable/
"""

from dataclasses import dataclass
from typing import Optional, Tuple
import numpy as np

from ..core.geometry import (
    Point2,
    Segment2,
    Capsule2,
    angle_from_x_axis,
    capsule_capsule_clearance,
)


@dataclass
class LeverState:
    """State of lever mechanism"""

    # Positions (Point2)
    pivot: Point2  # Pivot point (fixed)
    attach: Point2  # Rod attachment point on lever
    free_end: Point2  # Free end of lever

    # Kinematics
    angle: float  # Lever angle ? from X axis (rad)
    angular_velocity: float = 0.0  # d?/dt (rad/s)

    # Geometry
    arm_length: float = 0.0
    rod_attach_fraction: float = 0.0


@dataclass
class CylinderState:
    """State of pneumatic cylinder"""

    # Positions
    frame_hinge: Point2  # Hinge on frame (fixed)
    rod_hinge: Point2  # Hinge on lever (moving)

    # Stroke
    stroke: float  # Piston position s (m), 0 at center
    stroke_velocity: float = 0.0  # ds/dt (m/s)

    # Volumes
    volume_head: float = 0.0  # B���������� ������� (m?)
    volume_rod: float = 0.0  # �������� ������� (m?)

    # Geometry
    distance: float = 0.0  # Distance between hinges D (m)
    cylinder_axis_angle: float = 0.0  # Angle of cylinder axis (rad)

    # Areas
    area_head: float = 0.0  # Full piston area (m?)
    area_rod: float = 0.0  # Annular area (m?)


class LeverKinematics:
    """Lever kinematics solver"""

    def __init__(
        self,
        arm_length: float,
        pivot_position: Point2,
        pivot_offset_from_frame: float,
        rod_attach_fraction: float = 0.7,
    ):
        """Initialize lever kinematics

        Args:
            arm_length: Lever arm length L (m)
            pivot_position: Pivot point (usually at origin or offset)
            pivot_offset_from_frame: Horizontal offset b from frame (m)
            rod_attach_fraction: Rod attachment point as fraction ? of L
        """
        self.L = arm_length
        self.pivot = pivot_position
        self.b = pivot_offset_from_frame
        self.rho = rod_attach_fraction

    def solve_from_free_end_y(
        self, free_end_y: float, free_end_y_dot: float = 0.0
    ) -> LeverState:
        """Solve lever state from vertical position of free end

        Args:
            free_end_y: Vertical position of free end (m)
            free_end_y_dot: Vertical velocity d(free_end_y)/dt (m/s)

        Returns:
            LeverState with positions and velocities
        """
        # Check bounds
        if abs(free_end_y) > self.L:
            raise ValueError(
                f"Free end Y={free_end_y:.3f}m exceeds arm length {self.L:.3f}m"
            )

        # Solve for angle: sin(?) = y/L
        sin_theta = free_end_y / self.L
        sin_theta = np.clip(sin_theta, -1.0, 1.0)  # Numerical safety

        # Determine quadrant by requiring X > 0 (lever extends outward)
        # ? = arcsin(y/L) gives principal value
        # For X = b + L*cos(?) > 0, we need cos(?) > 0
        # So ? ? (-?/2, ?/2)
        theta = np.arcsin(sin_theta)

        # Compute cos(?) for position
        cos_theta = np.sqrt(1.0 - sin_theta**2)

        # Free end position
        free_end = Point2(
            x=self.pivot.x + self.L * cos_theta, y=self.pivot.y + free_end_y
        )

        # Attachment point (? * L along lever from pivot)
        attach = Point2(
            x=self.pivot.x + (self.rho * self.L) * cos_theta,
            y=self.pivot.y + (self.rho * self.L) * sin_theta,
        )

        # Angular velocity: d?/dt = (dy/dt) / (L * cos(?))
        if abs(cos_theta) > 1e-6:
            theta_dot = free_end_y_dot / (self.L * cos_theta)
        else:
            theta_dot = 0.0

        return LeverState(
            pivot=self.pivot,
            attach=attach,
            free_end=free_end,
            angle=theta,
            angular_velocity=theta_dot,
            arm_length=self.L,
            rod_attach_fraction=self.rho,
        )

    def solve_from_angle(self, theta: float, theta_dot: float = 0.0) -> LeverState:
        """Solve lever state from angle

        Args:
            theta: Lever angle from X axis (rad)
            theta_dot: Angular velocity d?/dt (rad/s)

        Returns:
            LeverState
        """
        # Free end position
        free_end = Point2(
            x=self.pivot.x + self.L * np.cos(theta),
            y=self.pivot.y + self.L * np.sin(theta),
        )

        # Attachment point
        attach = Point2(
            x=self.pivot.x + (self.rho * self.L) * np.cos(theta),
            y=self.pivot.y + (self.rho * self.L) * np.sin(theta),
        )

        return LeverState(
            pivot=self.pivot,
            attach=attach,
            free_end=free_end,
            angle=theta,
            angular_velocity=theta_dot,
            arm_length=self.L,
            rod_attach_fraction=self.rho,
        )


class CylinderKinematics:
    """Cylinder kinematics solver"""

    def __init__(
        self,
        frame_hinge: Point2,
        inner_diameter: float,
        rod_diameter: float,
        piston_thickness: float,
        body_length: float,
        dead_zone_rod: float,
        dead_zone_head: float,
    ):
        """Initialize cylinder kinematics

        Args:
            frame_hinge: Fixed hinge point on frame
            inner_diameter: Cylinder inner diameter D_in (m)
            rod_diameter: Rod diameter D_rod (m)
            piston_thickness: Piston thickness t_p (m)
            body_length: Cylinder body length L_body (m)
            dead_zone_rod: Rod side dead zone volume ?_rod (m?)
            dead_zone_head: Head side dead zone volume ?_head (m?)
        """
        self.frame_hinge = frame_hinge
        self.D_in = inner_diameter
        self.D_rod = rod_diameter
        self.t_p = piston_thickness
        self.L_body = body_length
        self.delta_rod = dead_zone_rod
        self.delta_head = dead_zone_head

        # Calculate areas
        self.A_head = np.pi * (self.D_in / 2.0) ** 2
        self.A_rod = self.A_head - np.pi * (self.D_rod / 2.0) ** 2

        # Maximum stroke
        self.S_max = self.L_body - self.t_p

    def solve_from_lever_state(
        self,
        lever_state: LeverState,
        lever_state_prev: Optional[LeverState] = None,
        dt: float = 0.001,
    ) -> CylinderState:
        """Solve cylinder state from lever attachment point

        Args:
            lever_state: Current lever state
            lever_state_prev: Previous lever state (for velocity)
            dt: Time step (s)

        Returns:
            CylinderState
        """
        rod_hinge = lever_state.attach

        # Distance between hinges
        D = self.frame_hinge.distance_to(rod_hinge)

        # Neutral distance D0 (piston at center, s=0)
        # D0 = L_body + some_offset
        # For simplicity: D0 = L_body (piston at mid-stroke)
        D0 = self.L_body

        # Stroke from distance: s = (D - D0)
        # This is simplified - more accurate would use projection
        s = D - D0

        # Clamp stroke to limits
        s = np.clip(s, -self.S_max / 2.0, self.S_max / 2.0)

        # Volumes (with dead zones)
        V_head = self.delta_head + self.A_head * (self.S_max / 2.0 + s)
        V_rod = self.delta_rod + self.A_rod * (self.S_max / 2.0 - s)

        # Stroke velocity (numerical differentiation)
        if lever_state_prev is not None:
            D_prev = self.frame_hinge.distance_to(lever_state_prev.attach)
            s_dot = (D - D_prev) / dt
        else:
            s_dot = 0.0

        # Cylinder axis angle
        vec = rod_hinge - self.frame_hinge
        axis_angle = angle_from_x_axis(vec)

        return CylinderState(
            frame_hinge=self.frame_hinge,
            rod_hinge=rod_hinge,
            stroke=s,
            stroke_velocity=s_dot,
            volume_head=V_head,
            volume_rod=V_rod,
            distance=D,
            cylinder_axis_angle=axis_angle,
            area_head=self.A_head,
            area_rod=self.A_rod,
        )


class InterferenceChecker:
    """Check for geometric interferences"""

    def __init__(
        self,
        arm_radius: float = 0.020,  # Reduced from 0.025
        cylinder_radius: float = 0.040,  # Reduced from 0.045
        enabled: bool = False,
    ):
        """Initialize interference checker

        Args:
            arm_radius: Lever arm visualization radius (m)
            cylinder_radius: Cylinder visualization radius (m)
            enabled: Enable interference checking
        """
        self.R_arm = arm_radius
        self.R_cyl = cylinder_radius
        self.enabled = enabled

    def check_lever_cylinder_interference(
        self, lever_state: LeverState, cylinder_state: CylinderState
    ) -> Tuple[bool, float]:
        """Check if lever and cylinder interfere

        Args:
            lever_state: Current lever state
            cylinder_state: Current cylinder state

        Returns:
            (is_interfering, clearance) - clearance negative if interfering
        """
        if not self.enabled:
            return False, float("inf")

        # Model FREE PART of lever as capsule (from attach to free_end)
        # This avoids false positives where cylinder connects to lever at attach point
        lever_seg = Segment2(lever_state.attach, lever_state.free_end)
        lever_capsule = Capsule2(lever_seg, self.R_arm)

        # Model cylinder as capsule
        cyl_seg = Segment2(cylinder_state.frame_hinge, cylinder_state.rod_hinge)
        cyl_capsule = Capsule2(cyl_seg, self.R_cyl)

        # Check intersection
        clearance = capsule_capsule_clearance(lever_capsule, cyl_capsule)
        is_interfering = clearance < 0.0

        return is_interfering, clearance


# ==============================================================================
# High-level solver
# ==============================================================================


def solve_axle_plane(
    side: str,  # "left" or "right"
    position: str,  # "front" or "rear"
    arm_length: float,
    pivot_offset: float,
    rod_attach_fraction: float,
    free_end_y: float,
    cylinder_params: dict,
    check_interference: bool = False,
) -> dict:
    """Solve complete state for one wheel plane

    Args:
        side: "left" or "right"
        position: "front" or "rear"
        arm_length: Lever arm length (m)
        pivot_offset: Pivot offset from frame (m)
        rod_attach_fraction: Rod attachment fraction
        free_end_y: Free end vertical position (m)
        cylinder_params: Dict with cylinder geometry
        check_interference: Enable interference checking

    Returns:
        Dict with lever_state, cylinder_state, interference info
    """
    # Create lever kinematics
    pivot = Point2(0.0, 0.0)  # Relative to wheel plane origin
    lever_kin = LeverKinematics(
        arm_length=arm_length,
        pivot_position=pivot,
        pivot_offset_from_frame=pivot_offset,
        rod_attach_fraction=rod_attach_fraction,
    )

    # Solve lever
    lever_state = lever_kin.solve_from_free_end_y(free_end_y)

    # Create cylinder kinematics
    frame_hinge = Point2(
        cylinder_params.get("frame_hinge_x", -0.1),
        cylinder_params.get("frame_hinge_y", 0.0),
    )

    cyl_kin = CylinderKinematics(
        frame_hinge=frame_hinge,
        inner_diameter=cylinder_params["inner_diameter"],
        rod_diameter=cylinder_params["rod_diameter"],
        piston_thickness=cylinder_params["piston_thickness"],
        body_length=cylinder_params["body_length"],
        dead_zone_rod=cylinder_params["dead_zone_rod"],
        dead_zone_head=cylinder_params["dead_zone_head"],
    )

    # Solve cylinder
    cylinder_state = cyl_kin.solve_from_lever_state(lever_state)

    # Check interference
    interference_checker = InterferenceChecker(enabled=check_interference)
    is_interfering, clearance = interference_checker.check_lever_cylinder_interference(
        lever_state, cylinder_state
    )

    return {
        "side": side,
        "position": position,
        "lever_state": lever_state,
        "cylinder_state": cylinder_state,
        "is_interfering": is_interfering,
        "clearance": clearance,
    }


__all__ = [
    "LeverState",
    "CylinderState",
    "LeverKinematics",
    "CylinderKinematics",
    "InterferenceChecker",
    "solve_axle_plane",
]
