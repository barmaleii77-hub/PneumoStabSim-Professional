"""Core geometry and data structures."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING

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


if TYPE_CHECKING:  # pragma: no cover - used for static analyzers only
    from .geometry import (  # noqa: F401 (re-exported via __getattr__)
        Capsule2,
        GeometryParams,
        Point2,
        Segment2,
        angle_between,
        angle_from_x_axis,
        capsule_capsule_clearance,
        capsule_capsule_intersect,
        closest_point_on_segment,
        dist_point_segment,
        dist_segment_segment,
        dot,
        norm,
        normalize,
        project,
    )


def __getattr__(name: str):
    if name in __all__:
        module = import_module("src.core.geometry")
        return getattr(module, name)
    raise AttributeError(f"module 'src.core' has no attribute '{name}'")
