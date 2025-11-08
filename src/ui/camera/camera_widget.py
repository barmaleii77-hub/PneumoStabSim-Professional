"""Widgets providing camera interaction affordances."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QMouseEvent
from PySide6.QtWidgets import QWidget

from .orbit_controller import OrbitController

__all__ = ["CameraWidget"]


class CameraWidget(QWidget):
    """Surface camera interactions such as auto-fit and preset selection."""

    autoFitRequested = Signal()
    presetApplied = Signal(str, "QVariantMap")

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        orbit_controller: OrbitController | None = None,
    ) -> None:
        super().__init__(parent)
        self._orbit_controller = orbit_controller
        if self._orbit_controller is not None:
            self._orbit_controller.presetApplied.connect(self._on_preset_applied)
        self.setMouseTracking(True)

    def set_orbit_controller(self, controller: OrbitController | None) -> None:
        """Attach ``controller`` and wire preset signals."""

        if self._orbit_controller is controller:
            return
        if self._orbit_controller is not None:
            try:
                self._orbit_controller.presetApplied.disconnect(self._on_preset_applied)
            except TypeError:  # pragma: no cover - signal already disconnected
                pass
        self._orbit_controller = controller
        if controller is not None:
            controller.presetApplied.connect(self._on_preset_applied)

    def orbit_controller(self) -> OrbitController | None:
        """Return the currently bound :class:`OrbitController`."""

        return self._orbit_controller

    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:  # noqa: N802 - Qt API
        if event.button() == Qt.LeftButton:
            self.autoFitRequested.emit()
            event.accept()
        super().mouseDoubleClickEvent(event)

    def mousePressEvent(self, event: QMouseEvent) -> None:  # noqa: N802 - Qt API
        super().mousePressEvent(event)

    @Slot(str, "QVariantMap")
    def _on_preset_applied(self, preset_id: str, payload: Any) -> None:
        self.presetApplied.emit(preset_id, payload)
