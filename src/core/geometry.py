"""Core 2D geometry utilities used by the suspension kinematics.

Coordinate system (per wheel plane):
- X axis: transverse from frame to wheel (right for right side, mirrored for left)
- Y axis: vertical (up positive)

The helpers defined here provide 2D geometry primitives used throughout the
simulation when validating linkage lengths and rod clearances. They also serve
as a small math toolbox with projection and angle helpers that are frequently
consumed by the Python↔QML bridge.

Notes:
- Lever angle θ measured from X (horizontal) counterclockwise.

References:
- numpy.dot: https://numpy.org/doc/stable/reference/generated/numpy.dot.html
- Distance algorithms: https://www.geometrictools.com/Source/Distance2D.html
"""

from dataclasses import dataclass
import numpy as np
from typing import Any
from collections.abc import Mapping

from config.constants import (
    get_geometry_cylinder_constants,
    get_geometry_kinematics_constants,
    get_geometry_visual_constants,
)


def _require_value(payload: Mapping[str, Any], key: str, context: str) -> Any:
    if key not in payload:
        raise KeyError(f"Missing '{context}.{key}' in config/app_settings.json")
    return payload[key]


def _require_float(payload: Mapping[str, Any], key: str, context: str) -> float:
    value = _require_value(payload, key, context)
    try:
        return float(value)
    except (TypeError, ValueError) as exc:
        raise TypeError(
            f"'{context}.{key}' must be a number in config/app_settings.json"
        ) from exc


@dataclass(frozen=True)
class Vector3D:
    """Simple 3D vector helper used by geometry and bridge layers."""

    x: float
    y: float
    z: float

    def as_array(self) -> np.ndarray:
        """Return the vector as a numpy array with ``float`` dtype."""

        return np.array([self.x, self.y, self.z], dtype=float)

    def __add__(self, other: "Vector3D") -> "Vector3D":
        vec = self.as_array() + other.as_array()
        return Vector3D(float(vec[0]), float(vec[1]), float(vec[2]))

    def __sub__(self, other: "Vector3D") -> "Vector3D":
        vec = self.as_array() - other.as_array()
        return Vector3D(float(vec[0]), float(vec[1]), float(vec[2]))

    def __mul__(self, scalar: float) -> "Vector3D":
        vec = self.as_array() * float(scalar)
        return Vector3D(float(vec[0]), float(vec[1]), float(vec[2]))

    __rmul__ = __mul__

    def dot(self, other: "Vector3D") -> float:
        return float(np.dot(self.as_array(), other.as_array()))

    def cross(self, other: "Vector3D") -> "Vector3D":
        vec = np.cross(self.as_array(), other.as_array())
        return Vector3D(float(vec[0]), float(vec[1]), float(vec[2]))

    def magnitude(self) -> float:
        return float(np.linalg.norm(self.as_array()))

    def normalized(self) -> "Vector3D":
        norm = self.magnitude()
        if norm <= 1e-12:
            return Vector3D(0.0, 0.0, 0.0)
        return self * (1.0 / norm)

    def distance_to(self, other: "Vector3D") -> float:
        return float(np.linalg.norm(self.as_array() - other.as_array()))


@dataclass
class Point2:
    """2D point in plane"""

    x: float
    y: float

    def as_array(self) -> np.ndarray:
        """Convert to numpy array"""
        return np.array([self.x, self.y])

    def __sub__(self, other: "Point2") -> np.ndarray:
        """Vector from other to self"""
        return self.as_array() - other.as_array()

    def __add__(self, vec: np.ndarray) -> "Point2":
        """Add vector to point"""
        result = self.as_array() + vec
        return Point2(result[0], result[1])

    def distance_to(self, other: "Point2") -> float:
        """Euclidean distance to another point"""
        return np.linalg.norm(self - other)


@dataclass
class Segment2:
    """2D line segment"""

    p0: Point2  # Start point
    p1: Point2  # End point

    def length(self) -> float:
        """Segment length"""
        return self.p0.distance_to(self.p1)

    def direction(self) -> np.ndarray:
        """Unit direction vector"""
        vec = self.p1 - self.p0
        length = np.linalg.norm(vec)
        return vec / length if length > 1e-10 else np.array([1.0, 0.0])

    def point_at(self, t: float) -> Point2:
        """Point at parameter t ? [0,1]"""
        vec = self.p1 - self.p0
        result = self.p0.as_array() + t * vec
        return Point2(result[0], result[1])


@dataclass
class Capsule2:
    """2D capsule (segment with radius)"""

    segment: Segment2
    radius: float

    def contains_point(self, point: Point2) -> bool:
        """Check if point is inside capsule"""
        return dist_point_segment(point, self.segment) <= self.radius


class GeometryParams:
    """Geometry parameters for kinematics"""

    def __init__(self):
        kinematics = get_geometry_kinematics_constants()
        cylinder = get_geometry_cylinder_constants()
        visual = get_geometry_visual_constants()

        # Wheelbase and lever geometry
        context_kin = "constants.geometry.kinematics"
        self.track_width = _require_float(kinematics, "track_width_m", context_kin)
        self.lever_length = _require_float(kinematics, "lever_length_m", context_kin)
        self.pivot_offset_from_frame = _require_float(
            kinematics, "pivot_offset_from_frame_m", context_kin
        )

        # Cylinder geometry
        context_cyl = "constants.geometry.cylinder"
        self.cylinder_inner_diameter = _require_float(
            cylinder, "inner_diameter_m", context_cyl
        )
        self.rod_diameter = _require_float(cylinder, "rod_diameter_m", context_cyl)
        self.piston_thickness = _require_float(
            cylinder, "piston_thickness_m", context_cyl
        )
        self.cylinder_body_length = _require_float(
            cylinder, "body_length_m", context_cyl
        )

        # Dead zones (minimum pocket volumes)
        self.dead_zone_rod = _require_float(cylinder, "dead_zone_rod_m3", context_cyl)
        self.dead_zone_head = _require_float(cylinder, "dead_zone_head_m3", context_cyl)

        # Visualization radii
        context_vis = "constants.geometry.visualization"
        self.arm_vis_radius = _require_float(visual, "arm_radius_m", context_vis)
        self.cylinder_vis_radius = _require_float(
            visual, "cylinder_radius_m", context_vis
        )

        # Attachment point on lever (fraction of length)
        self.rod_attach_fraction = _require_float(
            kinematics, "rod_attach_fraction", context_kin
        )

    def validate_invariant_track(self) -> bool:
        """Validate track =2 * (arm_length + pivot_offset)"""
        expected_track = 2.0 * (self.lever_length + self.pivot_offset_from_frame)
        return abs(self.track_width - expected_track) < 1e-6

    def enforce_track_from_geometry(self):
        """Recalculate track from arm_length and pivot_offset"""
        self.track_width = 2.0 * (self.lever_length + self.pivot_offset_from_frame)

    def enforce_arm_length_from_track(self):
        """Recalculate arm_length from track (keeping pivot_offset fixed)"""
        self.lever_length = (self.track_width / 2.0) - self.pivot_offset_from_frame

    def enforce_pivot_offset_from_track(self):
        """Recalculate pivot_offset from track (keeping arm_length fixed)"""
        self.pivot_offset_from_frame = (self.track_width / 2.0) - self.lever_length


# =============================================================================
# Vector utilities
# ============================================================================


def dot(a: np.ndarray, b: np.ndarray) -> float:
    """Dot product (scalar product)

    References: https://numpy.org/doc/stable/reference/generated/numpy.dot.html
    """
    return np.dot(a, b)


def norm(v: np.ndarray) -> float:
    """Euclidean norm (length) of vector"""
    return np.linalg.norm(v)


def normalize(v: np.ndarray) -> np.ndarray:
    """Normalize vector to unit length"""
    length = norm(v)
    return v / length if length > 1e-10 else np.array([1.0, 0.0])


def project(v: np.ndarray, onto: np.ndarray) -> np.ndarray:
    """Project vector v onto vector 'onto'"""
    onto_norm = normalize(onto)
    return dot(v, onto_norm) * onto_norm


def angle_between(a: np.ndarray, b: np.ndarray) -> float:
    """Angle between two vectors (radians)"""
    cos_angle = dot(normalize(a), normalize(b))
    # Clamp to avoid numerical issues with arccos
    cos_angle = np.clip(cos_angle, -1.0, 1.0)
    return np.arccos(cos_angle)


def angle_from_x_axis(v: np.ndarray) -> float:
    """Angle from positive X axis (using atan2 for correct quadrant)"""
    return np.arctan2(v[1], v[0])


# ==============================================================================
# Distance calculations
# ==============================================================================


def dist_point_segment(point: Point2, segment: Segment2) -> float:
    """Distance from point to line segment

    Algorithm:
    1. Project point onto infinite line containing segment
    2. Clamp projection parameter t to [0,1]
    3. Compute distance to clamped point

    References: https://www.geometrictools.com/Source/Distance2D.html
    """
    p = point.as_array()
    a = segment.p0.as_array()
    b = segment.p1.as_array()

    # Vector from a to b
    ab = b - a
    length_sq = dot(ab, ab)

    # Degenerate segment (point)
    if length_sq < 1e-10:
        return norm(p - a)

    # Project point onto line: t = (p-a)·(b-a) / |b-a|?
    t = dot(p - a, ab) / length_sq

    # Clamp to segment
    t = np.clip(t, 0.0, 1.0)

    # Closest point on segment
    closest = a + t * ab

    return norm(p - closest)


def closest_point_on_segment(point: Point2, segment: Segment2) -> tuple[Point2, float]:
    """Find closest point on segment to given point

    Returns:
        (closest_point, parameter_t)
    """
    p = point.as_array()
    a = segment.p0.as_array()
    b = segment.p1.as_array()

    ab = b - a
    length_sq = dot(ab, ab)

    if length_sq < 1e-10:
        return segment.p0, 0.0

    t = dot(p - a, ab) / length_sq
    t = np.clip(t, 0.0, 1.0)

    closest = a + t * ab
    return Point2(closest[0], closest[1]), t


def dist_segment_segment(seg1: Segment2, seg2: Segment2) -> float:
    """Distance between two line segments

    Algorithm:
    - Check if segments are parallel/degenerate
    - Find closest points on infinite lines
    - Clamp to segment bounds
    - Return minimum distance

    References: https://www.geometrictools.com/Source/Distance2D.html
    """
    # Segment 1: p(s) = p0 + s*(p1-p0), s ? [0,1]
    # Segment 2: q(t) = q0 + t*(q1-q0), t ? [0,1]

    p0 = seg1.p0.as_array()
    p1 = seg1.p1.as_array()
    q0 = seg2.p0.as_array()
    q1 = seg2.p1.as_array()

    d1 = p1 - p0  # Direction of segment 1
    d2 = q1 - q0  # Direction of segment 2
    r = p0 - q0  # Vector from q0 to p0

    a = dot(d1, d1)
    b = dot(d1, d2)
    c = dot(d2, d2)
    d = dot(d1, r)
    e = dot(d2, r)

    # Parallel/degenerate check
    det = a * c - b * b

    if abs(det) < 1e-10:
        # Segments are parallel - use endpoint distances
        distances = [
            dist_point_segment(seg1.p0, seg2),
            dist_point_segment(seg1.p1, seg2),
            dist_point_segment(seg2.p0, seg1),
            dist_point_segment(seg2.p1, seg1),
        ]
        return min(distances)

    # Non-parallel case: solve for closest points
    s = (b * e - c * d) / det
    t = (a * e - b * d) / det

    # Clamp to [0,1] x [0,1]
    s = np.clip(s, 0.0, 1.0)
    t = np.clip(t, 0.0, 1.0)

    # Compute closest points
    closest1 = p0 + s * d1
    closest2 = q0 + t * d2

    return norm(closest1 - closest2)


def capsule_capsule_intersect(cap1: Capsule2, cap2: Capsule2) -> bool:
    """Check if two capsules intersect

    Capsules intersect if distance between segments < sum of radii
    """
    dist = dist_segment_segment(cap1.segment, cap2.segment)
    return dist < (cap1.radius + cap2.radius)


def capsule_capsule_clearance(cap1: Capsule2, cap2: Capsule2) -> float:
    """Clearance between two capsules (negative if intersecting)"""
    dist = dist_segment_segment(cap1.segment, cap2.segment)
    return dist - (cap1.radius + cap2.radius)


# =============================================================================
# Exports
# ==========================================================================

__all__ = [
    "Point2",
    "Segment2",
    "Capsule2",
    "GeometryParams",
    "dot",
    "norm",
    "normalize",
    "project",
    "angle_between",
    "angle_from_x_axis",
    "dist_point_segment",
    "closest_point_on_segment",
    "dist_segment_segment",
    "capsule_capsule_intersect",
    "capsule_capsule_clearance",
]
