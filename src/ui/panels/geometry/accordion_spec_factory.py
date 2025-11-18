"""Shared helpers for building geometry accordion field specs."""

from __future__ import annotations

from src.ui.panels_accordion import SliderFieldSpec

from .defaults import DEFAULT_GEOMETRY, PARAMETER_LIMITS, PARAMETER_METADATA


def spec_from_limits(
    key: str,
    *,
    label: str | None = None,
    unit: str | None = None,
    telemetry_key: str,
    settings_key: str | None = None,
) -> SliderFieldSpec:
    """Construct a :class:`SliderFieldSpec` using JSON-backed constraints."""

    limits = PARAMETER_LIMITS.get(key, {})
    min_value = float(limits.get("min", 0.0))
    max_value = float(limits.get("max", 1.0))
    step = float(limits.get("step", 0.001))
    decimals = int(limits.get("decimals", 3))
    meta = PARAMETER_METADATA.get(key, {})
    default = float(DEFAULT_GEOMETRY.get(settings_key or key, 0.0))

    return SliderFieldSpec(
        key=key,
        label=label or meta.get("title", key),
        min_value=min_value,
        max_value=max_value,
        step=step,
        decimals=decimals,
        unit=unit or meta.get("units", ""),
        allow_range_edit=True,
        default=default,
        settings_key=settings_key or key,
        telemetry_key=telemetry_key,
    )


__all__ = ["spec_from_limits"]
