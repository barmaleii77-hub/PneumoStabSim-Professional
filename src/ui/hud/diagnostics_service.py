"""Diagnostics service exposing HUD telemetry to Qt consumers."""

from __future__ import annotations

from typing import Any
from collections.abc import Mapping

from PySide6.QtCore import QObject, Signal

__all__ = ["DiagnosticsService"]


class DiagnosticsService(QObject):
    """Publish diagnostics metrics for the HUD overlay."""

    metricsChanged = Signal("QVariantMap")
    visibilityChanged = Signal(bool)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._metrics: dict[str, Any] = {}
        self._visible: bool = False

    @staticmethod
    def _coerce_mapping(payload: Mapping[str, Any] | None) -> dict[str, Any]:
        if not isinstance(payload, Mapping):
            return {}
        result: dict[str, Any] = {}
        for key, value in payload.items():
            if not isinstance(key, str) or not key:
                continue
            result[key] = value
        return result

    def publish_metrics(self, payload: Mapping[str, Any] | None) -> dict[str, Any]:
        """Sanitise ``payload`` and emit :pyattr:`metricsChanged`."""

        self._metrics = self._coerce_mapping(payload)
        snapshot = dict(self._metrics)
        self.metricsChanged.emit(snapshot)
        return snapshot

    def set_visible(self, visible: bool) -> bool:
        """Update the visibility flag and emit :pyattr:`visibilityChanged`."""

        visible_flag = bool(visible)
        if self._visible == visible_flag:
            return False
        self._visible = visible_flag
        self.visibilityChanged.emit(self._visible)
        return True

    def toggle_visible(self) -> bool:
        """Toggle the visibility flag."""

        return self.set_visible(not self._visible)

    def metrics(self) -> dict[str, Any]:
        """Return the last published metrics."""

        return dict(self._metrics)

    def is_visible(self) -> bool:
        """Return the last visibility flag."""

        return self._visible
