"""Geometry helpers for the lever-cylinder linkage.

The numbers in the engineering spreadsheet describe the neutral positions of
key suspension points (frame hinges, lever joints, pneumatic cylinder mounts)
for both the left and the right half of the chassis.  The right half is used
as the canonical plane and the left half can be obtained through symmetry.

This module converts those tabulated coordinates into derived quantities that
other subsystems require:

* Lever length and rod attachment fraction.
* Nominal cylinder length and minimum piston-rod length.
* Maximum vertical displacement (``amplitude``) that does not force the piston
  outside of the cylinder body.

All calculations are carried out in metres; a convenience constructor accepts
millimetres because the original specification is written in millimetres.
"""

from __future__ import annotations

from dataclasses import dataclass
import math

TwoVector = tuple[float, float]


def _ensure_pair(point: tuple[float, float], name: str) -> tuple[float, float]:
    if len(point) != 2:
        raise ValueError(f"{name} must contain two coordinates (x, y)")
    x, y = float(point[0]), float(point[1])
    return (x, y)


def _distance(a: TwoVector, b: TwoVector) -> float:
    return math.dist(a, b)


@dataclass(frozen=True)
class SuspensionLinkage:
    """Suspension linkage specification for a single side of the frame."""

    pivot: TwoVector
    free_end: TwoVector
    rod_joint: TwoVector
    cylinder_tail: TwoVector
    cylinder_body_length: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "pivot", _ensure_pair(self.pivot, "pivot"))
        object.__setattr__(self, "free_end", _ensure_pair(self.free_end, "free_end"))
        object.__setattr__(self, "rod_joint", _ensure_pair(self.rod_joint, "rod_joint"))
        object.__setattr__(
            self, "cylinder_tail", _ensure_pair(self.cylinder_tail, "cylinder_tail")
        )
        if self.cylinder_body_length <= 0.0:
            raise ValueError("cylinder_body_length must be positive")

    # ------------------------------------------------------------------
    # Convenience constructors
    # ------------------------------------------------------------------
    @classmethod
    def from_mm(
        cls,
        *,
        pivot: TwoVector,
        free_end: TwoVector,
        rod_joint: TwoVector,
        cylinder_tail: TwoVector,
        cylinder_body_length: float,
    ) -> SuspensionLinkage:
        """Create a specification from millimetre values."""

        factor = 1e-3
        return cls(
            pivot=(pivot[0] * factor, pivot[1] * factor),
            free_end=(free_end[0] * factor, free_end[1] * factor),
            rod_joint=(rod_joint[0] * factor, rod_joint[1] * factor),
            cylinder_tail=(cylinder_tail[0] * factor, cylinder_tail[1] * factor),
            cylinder_body_length=cylinder_body_length * factor,
        )

    # ------------------------------------------------------------------
    # Basic geometric relationships
    # ------------------------------------------------------------------
    @property
    def lever_length(self) -> float:
        return _distance(self.pivot, self.free_end)

    @property
    def rod_attach_distance(self) -> float:
        return _distance(self.pivot, self.rod_joint)

    @property
    def rod_joint_fraction(self) -> float:
        base = self.lever_length
        if base == 0.0:
            raise ValueError("lever length cannot be zero")
        return self.rod_attach_distance / base

    def rod_joint_is_on_lever(self, *, tolerance: float = 1e-9) -> bool:
        vec_lever = (self.free_end[0] - self.pivot[0], self.free_end[1] - self.pivot[1])
        vec_attach = (
            self.rod_joint[0] - self.pivot[0],
            self.rod_joint[1] - self.pivot[1],
        )
        cross = vec_lever[0] * vec_attach[1] - vec_lever[1] * vec_attach[0]
        return abs(cross) <= tolerance * self.lever_length * self.rod_attach_distance

    @property
    def nominal_cylinder_length(self) -> float:
        return _distance(self.cylinder_tail, self.rod_joint)

    @property
    def minimum_rod_length(self) -> float:
        return max(0.0, self.nominal_cylinder_length - self.cylinder_body_length)

    # ------------------------------------------------------------------
    # Cylinder displacement vs. lever angle
    # ------------------------------------------------------------------
    def cylinder_length_at_angle(self, angle: float) -> float:
        radius = self.rod_attach_distance
        rod_point = (
            self.pivot[0] + radius * math.cos(angle),
            self.pivot[1] + radius * math.sin(angle),
        )
        return _distance(self.cylinder_tail, rod_point)

    def max_angle_for_stroke_limit(self, direction: int) -> float:
        if direction not in (-1, 1):
            raise ValueError("direction must be +1 or -1")

        base_length = self.cylinder_length_at_angle(0.0)
        limit = self.cylinder_body_length
        end_angle = math.pi / 2 - 1e-6

        def displacement(theta: float) -> float:
            return abs(self.cylinder_length_at_angle(theta) - base_length)

        if displacement(direction * end_angle) <= limit:
            return direction * end_angle

        low = 0.0
        high = end_angle
        for _ in range(80):
            mid = 0.5 * (low + high)
            if displacement(direction * mid) <= limit:
                low = mid
            else:
                high = mid
        return direction * low

    # ------------------------------------------------------------------
    # Amplitude helpers
    # ------------------------------------------------------------------
    def free_end_amplitude(self, direction: int = 1) -> float:
        angle = self.max_angle_for_stroke_limit(direction)
        y_neutral = self.free_end[1]
        y_current = self.pivot[1] + self.lever_length * math.sin(angle)
        return y_current - y_neutral

    def free_end_amplitude_limits(self) -> tuple[float, float]:
        neg = self.free_end_amplitude(direction=-1)
        pos = self.free_end_amplitude(direction=1)
        return (neg, pos)
