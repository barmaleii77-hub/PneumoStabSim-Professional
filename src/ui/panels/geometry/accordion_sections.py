"""Reusable geometry accordion sections.

This module extracts the slider definitions for the geometry accordion into
discrete, testable building blocks.  Each section is focused on a single
parameter group (колёсная база, колея, рычаг, ход цилиндра, диаметры
поршня/штока) to mirror the roadmap checklist and keep signal routing simple.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

from src.ui.panels_accordion import SliderFieldSpec


@dataclass(frozen=True, slots=True)
class GeometryAccordionSection:
    """Container describing a set of geometry slider specs."""

    name: str
    specs: tuple[SliderFieldSpec, ...]

    def register(self, panel) -> tuple[object, ...]:
        """Register all specs on *panel* and return created widgets."""

        created: list[object] = []
        for spec in self.specs:
            created.append(panel.add_slider_field(spec))
        return tuple(created)


def build_geometry_sections() -> Iterable[GeometryAccordionSection]:
    """Yield geometry accordion sections in display order."""

    yield GeometryAccordionSection(
        name="wheelbase",
        specs=(
            SliderFieldSpec(
                key="wheelbase",
                label="Wheelbase (L)",
                min_value=2.0,
                max_value=5.0,
                step=0.01,
                decimals=3,
                unit="m",
                allow_range_edit=True,
                default=3.0,
                settings_key="wheelbase",
                telemetry_key="geometry.wheelbase",
            ),
        ),
    )

    yield GeometryAccordionSection(
        name="track_width",
        specs=(
            SliderFieldSpec(
                key="track_width",
                label="Track Width (B)",
                min_value=1.0,
                max_value=2.5,
                step=0.01,
                decimals=3,
                unit="m",
                allow_range_edit=True,
                default=1.8,
                settings_key="track",
                telemetry_key="geometry.track",
            ),
        ),
    )

    yield GeometryAccordionSection(
        name="lever",
        specs=(
            SliderFieldSpec(
                key="lever_arm",
                label="Lever Arm (r)",
                min_value=0.1,
                max_value=0.6,
                step=0.001,
                decimals=3,
                unit="m",
                allow_range_edit=True,
                default=0.3,
                settings_key="lever_length",
                telemetry_key="geometry.lever_length",
            ),
            SliderFieldSpec(
                key="lever_angle",
                label="Lever Angle (β)",
                min_value=-30.0,
                max_value=30.0,
                step=0.1,
                decimals=2,
                unit="deg",
                allow_range_edit=False,
                default=0.0,
                read_only=True,
                emit_signal=False,
                telemetry_key="geometry.lever_angle",
            ),
        ),
    )

    yield GeometryAccordionSection(
        name="cylinder_stroke",
        specs=(
            SliderFieldSpec(
                key="cylinder_stroke",
                label="Cylinder Stroke (s_max)",
                min_value=0.05,
                max_value=0.5,
                step=0.001,
                decimals=3,
                unit="m",
                allow_range_edit=True,
                default=0.2,
                settings_key="stroke_m",
                telemetry_key="geometry.stroke",
            ),
        ),
    )

    yield GeometryAccordionSection(
        name="piston_rod_diameters",
        specs=(
            SliderFieldSpec(
                key="piston_diameter",
                label="Piston Diameter (D_p)",
                min_value=0.03,
                max_value=0.15,
                step=0.001,
                decimals=3,
                unit="m",
                allow_range_edit=True,
                default=0.08,
                settings_key="cyl_diam_m",
                telemetry_key="geometry.cyl_diameter",
            ),
            SliderFieldSpec(
                key="rod_diameter",
                label="Rod Diameter (D_r)",
                min_value=0.01,
                max_value=0.10,
                step=0.001,
                decimals=3,
                unit="m",
                allow_range_edit=True,
                default=0.04,
                settings_key="rod_diameter_m",
                telemetry_key="geometry.rod_diameter",
            ),
        ),
    )

    yield GeometryAccordionSection(
        name="mass_properties",
        specs=(
            SliderFieldSpec(
                key="frame_mass",
                label="Frame Mass (M_frame)",
                min_value=500.0,
                max_value=5000.0,
                step=10.0,
                decimals=1,
                unit="kg",
                allow_range_edit=True,
                default=1500.0,
                settings_key="frame_mass",
                telemetry_key="geometry.frame_mass",
            ),
            SliderFieldSpec(
                key="wheel_mass",
                label="Wheel Mass (M_wheel)",
                min_value=10.0,
                max_value=200.0,
                step=1.0,
                decimals=1,
                unit="kg",
                allow_range_edit=True,
                default=50.0,
                settings_key="wheel_mass",
                telemetry_key="geometry.wheel_mass",
            ),
        ),
    )
