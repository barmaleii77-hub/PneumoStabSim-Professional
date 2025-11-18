"""Slider field specifications for the geometry accordion.

The accordion relies on :class:`~src.ui.panels_accordion.SliderFieldSpec`
instances so QML can bind to the same metadata and persistence rules as the
legacy Qt widgets.  Each specification pulls its defaults and ranges from the
canonical JSON settings snapshot to avoid diverging from the runtime config.
"""

from __future__ import annotations

from typing import Iterable

from src.ui.panels_accordion import SliderFieldSpec

from .cylinder_stroke_field import build_cylinder_stroke_spec
from .lever_arm_field import build_lever_arm_spec
from .piston_diameter_field import build_piston_diameter_spec
from .rod_diameter_field import build_rod_diameter_spec
from .track_width_field import build_track_width_spec
from .wheelbase_field import build_wheelbase_spec


def build_geometry_field_specs() -> Iterable[tuple[str, SliderFieldSpec]]:
    """Return ordered slider specs for the geometry accordion.

    The set follows the GeometryPanelAccordion checklist from ``ROADMAP``.
    """

    return (
        build_wheelbase_spec(),
        build_track_width_spec(),
        build_lever_arm_spec(),
        build_cylinder_stroke_spec(),
        build_piston_diameter_spec(),
        build_rod_diameter_spec(),
    )


__all__ = ["build_geometry_field_specs"]
