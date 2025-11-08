"""HUD diagnostics overlay binding helpers."""

from __future__ import annotations

from typing import Any
from collections.abc import Mapping

from PySide6.QtCore import QObject, Property, Signal, Slot

from .diagnostics_service import DiagnosticsService

__all__ = ["DiagnosticsOverlay"]


class DiagnosticsOverlay(QObject):
    """Expose :class:`DiagnosticsService` metrics to QML bindings."""

    metricsChanged = Signal("QVariantMap")
    visibilityChanged = Signal(bool)

    def __init__(
        self,
        parent: QObject | None = None,
        *,
        diagnostics_service: DiagnosticsService | None = None,
    ) -> None:
        super().__init__(parent)
        self._service = diagnostics_service or DiagnosticsService(parent)
        self._metrics: dict[str, Any] = self._coerce_mapping(self._service.metrics())
        self._visible: bool = self._service.is_visible()
        self._service.metricsChanged.connect(self._on_service_metrics)
        self._service.visibilityChanged.connect(self._on_service_visibility)

    @Property("QVariantMap", notify=metricsChanged)
    def metrics(self) -> dict[str, Any]:
        return dict(self._metrics)

    @Property(bool, notify=visibilityChanged)
    def visible(self) -> bool:
        return self._visible

    @Slot("QVariantMap")
    def updateMetrics(self, payload: Mapping[str, Any] | None) -> None:
        """Forward metric updates to the underlying service."""

        self._service.publish_metrics(payload)

    @Slot(bool)
    def setVisible(self, visible: bool) -> None:
        """Update visibility through the service."""

        self._service.set_visible(visible)

    def diagnostics_service(self) -> DiagnosticsService:
        """Return the bound diagnostics service."""

        return self._service

    def _on_service_metrics(self, payload: Mapping[str, Any] | None) -> None:
        self._metrics = self._coerce_mapping(payload)
        self.metricsChanged.emit(dict(self._metrics))

    def _on_service_visibility(self, visible: bool) -> None:
        visible_flag = bool(visible)
        if self._visible != visible_flag:
            self._visible = visible_flag
        self.visibilityChanged.emit(self._visible)

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
