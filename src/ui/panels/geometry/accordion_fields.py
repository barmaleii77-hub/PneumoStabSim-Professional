"""Slider field specifications for the geometry accordion.

The accordion relies on :class:`~src.ui.panels_accordion.SliderFieldSpec`
instances so QML can bind to the same metadata and persistence rules as the
legacy Qt widgets.  Each specification pulls its defaults and ranges from the
canonical JSON settings snapshot to avoid diverging from the runtime config.
"""

from __future__ import annotations

from typing import Iterable

from src.ui.panels_accordion import SliderFieldSpec

from .defaults import DEFAULT_GEOMETRY, PARAMETER_LIMITS, PARAMETER_METADATA


def _spec_from_limits(
    key: str,
    *,
    label: str,
    unit: str,
    telemetry_key: str,
    settings_key: str | None = None,
) -> SliderFieldSpec:
    limits = PARAMETER_LIMITS.get(key, {})
    min_value = float(limits.get("min", 0.0))
    max_value = float(limits.get("max", 1.0))
    step = float(limits.get("step", 0.001))
    decimals = int(limits.get("decimals", 3))
    default = float(DEFAULT_GEOMETRY.get(settings_key or key, 0.0))

    return SliderFieldSpec(
        key=key,
        label=label,
        min_value=min_value,
        max_value=max_value,
        step=step,
        decimals=decimals,
        unit=unit,
        allow_range_edit=True,
        default=default,
        settings_key=settings_key or key,
        telemetry_key=telemetry_key,
    )


def build_geometry_field_specs() -> Iterable[tuple[str, SliderFieldSpec]]:
    """Return ordered slider specs for the geometry accordion.

    The set follows the GeometryPanelAccordion checklist from ``ROADMAP``.
    """

    wheelbase_meta = PARAMETER_METADATA.get("wheelbase", {})
    track_meta = PARAMETER_METADATA.get("track", {})
    lever_meta = PARAMETER_METADATA.get("lever_length", {})
    stroke_meta = PARAMETER_METADATA.get("stroke_m", {})
    piston_meta = PARAMETER_METADATA.get("cyl_diam_m", {})
    rod_meta = PARAMETER_METADATA.get("rod_diameter_m", {})

    return (
        (
            "wheelbase",
            _spec_from_limits(
                "wheelbase",
                label=wheelbase_meta.get("title", "Wheelbase (L)"),
                unit=wheelbase_meta.get("units", "м"),
                telemetry_key="geometry.wheelbase",
            ),
        ),
        (
            "track_width",
            _spec_from_limits(
                "track",
                label=track_meta.get("title", "Track Width (B)"),
                unit=track_meta.get("units", "м"),
                telemetry_key="geometry.track",
                settings_key="track",
            ),
        ),
        (
            "lever_arm",
            _spec_from_limits(
                "lever_length",
                label=lever_meta.get("title", "Lever Arm (r)"),
                unit=lever_meta.get("units", "м"),
                telemetry_key="geometry.lever_length",
            ),
        ),
        (
            "cylinder_stroke",
            _spec_from_limits(
                "stroke_m",
                label=stroke_meta.get("title", "Cylinder Stroke"),
                unit=stroke_meta.get("units", "м"),
                telemetry_key="geometry.stroke",
                settings_key="stroke_m",
            ),
        ),
        (
            "piston_diameter",
            _spec_from_limits(
                "cyl_diam_m",
                label=piston_meta.get("title", "Piston Diameter (D_p)"),
                unit=piston_meta.get("units", "м"),
                telemetry_key="geometry.cyl_diameter",
                settings_key="cyl_diam_m",
            ),
        ),
        (
            "rod_diameter",
            _spec_from_limits(
                "rod_diameter_m",
                label=rod_meta.get("title", "Rod Diameter (D_r)"),
                unit=rod_meta.get("units", "м"),
                telemetry_key="geometry.rod_diameter",
                settings_key="rod_diameter_m",
            ),
        ),
    )


__all__ = ["build_geometry_field_specs"]
