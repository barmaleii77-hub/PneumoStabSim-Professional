"""
Core geometry and data structures
"""

from .geometry import (
    Point2,
    Segment2,
    Capsule2,
    GeometryParams,
    dot,
    norm,
    normalize,
    project,
    angle_between,
    angle_from_x_axis,
    dist_point_segment,
    closest_point_on_segment,
    dist_segment_segment,
    capsule_capsule_intersect,
    capsule_capsule_clearance,
)

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
