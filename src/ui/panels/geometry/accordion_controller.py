"""Signal router for the geometry accordion panel.

The controller keeps the :class:`~src.ui.panels.geometry.accordion_panel.GeometryAccordion`
in sync with :class:`~src.common.settings_manager.SettingsManager` and exposes
aggregated signals that mirror the pattern used by the graphics panel modules.
"""

from __future__ import annotations

import logging
from typing import Any

from PySide6.QtCore import QObject, Signal

from src.common.settings_manager import (
    SettingsEventBus,
    SettingsManager,
    get_settings_event_bus,
    get_settings_manager,
)

from .accordion_panel import GeometryAccordion


class GeometryAccordionController(QObject):
    """Bridge geometry accordion field changes to the settings service."""

    geometryChanged = Signal(dict)
    parameterChanged = Signal(str, float)

    def __init__(
        self,
        *,
        settings_manager: SettingsManager | None = None,
        event_bus: SettingsEventBus | None = None,
        parent: QObject | None = None,
    ) -> None:
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.settings = settings_manager or get_settings_manager()
        self._event_bus = event_bus or get_settings_event_bus()
        self.panel = GeometryAccordion()
        self.panel.parameter_changed.connect(self._on_parameter_changed)

        self._initialise_from_settings()

    # ------------------------------------------------------------------ helpers
    def _initialise_from_settings(self) -> None:
        try:
            current_geometry = self.settings.get("current.geometry", default={}) or {}
        except Exception as exc:  # pragma: no cover - defensive guard
            self.logger.warning("Failed to read geometry state from settings: %s", exc)
            current_geometry = {}

        if isinstance(current_geometry, dict) and current_geometry:
            try:
                self.panel.set_parameters(current_geometry, source="bootstrap")
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.warning(
                    "Unable to hydrate geometry accordion from settings: %s", exc
                )

    # ------------------------------------------------------------------ slots
    def _persist_geometry(self) -> dict[str, Any]:
        snapshot = self.panel.get_parameters()
        try:
            self.settings.set("current.geometry", snapshot, auto_save=False)
            self.settings.save()
            if self._event_bus is not None:
                self._event_bus.emit_settings_batch({"geometry": snapshot})
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("Failed to persist geometry snapshot: %s", exc)
        return snapshot

    def _on_parameter_changed(self, key: str, value: float) -> None:
        snapshot = self._persist_geometry()
        self.parameterChanged.emit(key, float(value))
        self.geometryChanged.emit(snapshot)

    # ----------------------------------------------------------------- public
    def apply_geometry_payload(self, payload: dict[str, Any]) -> None:
        """Apply incoming geometry updates without recording undo history."""

        if not isinstance(payload, dict):
            return
        try:
            self.panel.set_parameters(payload, source="external")
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.warning("Failed to apply geometry payload: %s", exc)


__all__ = ["GeometryAccordionController"]
