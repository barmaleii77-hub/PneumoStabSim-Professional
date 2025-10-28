"""Core geometry, data structures, and service wiring utilities."""

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
    "EventBus",
    "ServiceContainer",
    "ServiceRegistrationError",
    "ServiceResolutionError",
    "build_default_container",
]


if TYPE_CHECKING:  # pragma: no cover - used for static analyzers only
    from .container import (  # noqa: F401 (re-exported via __getattr__)
        EventBus,
        ServiceContainer,
        ServiceRegistrationError,
        ServiceResolutionError,
        build_default_container,
    )
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


_GEOMETRY_EXPORTS = {
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
}

_CONTAINER_EXPORTS = {
    "EventBus",
    "ServiceContainer",
    "ServiceRegistrationError",
    "ServiceResolutionError",
    "build_default_container",
}


def __getattr__(name: str):
    if name in _GEOMETRY_EXPORTS:
        module = import_module("src.core.geometry")
        return getattr(module, name)
    if name in _CONTAINER_EXPORTS:
        module = import_module("src.core.container")
        return getattr(module, name)
    raise AttributeError(f"module 'src.core' has no attribute '{name}'")
