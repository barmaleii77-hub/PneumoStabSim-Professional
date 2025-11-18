"""Accordion implementation for geometry parameters.

This module wraps :class:`~src.ui.panels_accordion.SettingsBackedAccordionPanel`
so the geometry controls share undo/redo, preset handling and settings
persistence with the newer graphics panel architecture.
"""

from __future__ import annotations

from typing import Mapping

from PySide6.QtCore import Signal
from PySide6.QtWidgets import QWidget

from config.constants import get_geometry_presets

from src.ui.panels_accordion import PanelPreset, SettingsBackedAccordionPanel

from .accordion_fields import build_geometry_field_specs


class GeometryAccordion(SettingsBackedAccordionPanel):
    """Accordion with sliders for the primary geometry parameters."""

    parameter_changed = Signal(str, float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            settings_section="geometry",
            parent=parent,
            preset_settings_key="active_preset",
        )

        for attr, spec in build_geometry_field_specs():
            slider = self.add_slider_field(spec)
            setattr(self, attr, slider)

        self._initialise_geometry_presets()
        self.content_layout.addStretch()

    def on_field_value_changed(self, spec, value: float) -> None:  # type: ignore[override]
        self.parameter_changed.emit(spec.key, value)

    def _initialise_geometry_presets(self) -> None:
        try:
            raw_presets = get_geometry_presets()
        except Exception:  # pragma: no cover - defensive
            return

        presets: list[PanelPreset] = []
        for entry in raw_presets:
            key = entry.get("key")
            values = entry.get("values")
            if not key or not isinstance(values, Mapping):
                continue
            label = entry.get("label") or str(key)
            description = entry.get("description", "")
            presets.append(
                PanelPreset(
                    preset_id=str(key),
                    label=str(label),
                    description=str(description),
                    values=values,
                    telemetry_key="geometry.preset",
                )
            )

        if presets:
            self.register_presets(presets, telemetry_key="geometry.preset")


__all__ = ["GeometryAccordion"]
