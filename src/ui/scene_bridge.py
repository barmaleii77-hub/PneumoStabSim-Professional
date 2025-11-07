"""Qt bridge exposing :class:`VisualizationService` state to QML."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Optional

from PySide6.QtCore import QObject, Property, Signal

from src.common.settings_manager import SettingsManager
from src.common.signal_trace import SignalTraceService, get_signal_trace_service
from src.ui.services.visualization_service import VisualizationService


class SceneBridge(QObject):
    """Expose simulation and graphics state updates to QML listeners."""

    updatesDispatched = Signal("QVariantMap")
    geometryChanged = Signal("QVariantMap")
    cameraChanged = Signal("QVariantMap")
    lightingChanged = Signal("QVariantMap")
    environmentChanged = Signal("QVariantMap")
    sceneChanged = Signal("QVariantMap")
    qualityChanged = Signal("QVariantMap")
    materialsChanged = Signal("QVariantMap")
    effectsChanged = Signal("QVariantMap")
    animationChanged = Signal("QVariantMap")
    threeDChanged = Signal("QVariantMap")
    renderChanged = Signal("QVariantMap")
    simulationChanged = Signal("QVariantMap")

    def __init__(
        self,
        parent: Optional[QObject] = None,
        *,
        visualization_service: VisualizationService | None = None,
        settings_manager: Optional[SettingsManager] = None,
        signal_trace_service: SignalTraceService | None = None,
    ) -> None:
        super().__init__(parent)
        if visualization_service is not None:
            self._service = visualization_service
        else:
            self._service = VisualizationService(settings_manager=settings_manager)
        if signal_trace_service is not None:
            self._signal_trace = signal_trace_service
        else:
            try:
                self._signal_trace = get_signal_trace_service()
            except Exception:  # pragma: no cover - optional diagnostics dependency
                self._signal_trace = None
        self._signal_map = {
            "geometry": self.geometryChanged,
            "camera": self.cameraChanged,
            "lighting": self.lightingChanged,
            "environment": self.environmentChanged,
            "scene": self.sceneChanged,
            "quality": self.qualityChanged,
            "materials": self.materialsChanged,
            "effects": self.effectsChanged,
            "animation": self.animationChanged,
            "threeD": self.threeDChanged,
            "render": self.renderChanged,
            "simulation": self.simulationChanged,
        }

        initial = self._service.populate_initial_state()
        if initial:
            self._emit_updates(initial)

    # ------------------------------------------------------------------
    # Qt Properties
    # ------------------------------------------------------------------
    @Property("QVariantMap", notify=geometryChanged)
    def geometry(self) -> Dict[str, Any]:
        return dict(self._service.state_for("geometry"))

    @Property("QVariantMap", notify=cameraChanged)
    def camera(self) -> Dict[str, Any]:
        return dict(self._service.state_for("camera"))

    @Property("QVariantMap", notify=lightingChanged)
    def lighting(self) -> Dict[str, Any]:
        return dict(self._service.state_for("lighting"))

    @Property("QVariantMap", notify=environmentChanged)
    def environment(self) -> Dict[str, Any]:
        return dict(self._service.state_for("environment"))

    @Property("QVariantMap", notify=qualityChanged)
    def quality(self) -> Dict[str, Any]:
        return dict(self._service.state_for("quality"))

    @Property("QVariantMap", notify=sceneChanged)
    def scene(self) -> Dict[str, Any]:
        return dict(self._service.state_for("scene"))

    @Property("QVariantMap", notify=materialsChanged)
    def materials(self) -> Dict[str, Any]:
        return dict(self._service.state_for("materials"))

    @Property("QVariantMap", notify=effectsChanged)
    def effects(self) -> Dict[str, Any]:
        return dict(self._service.state_for("effects"))

    @Property("QVariantMap", notify=animationChanged)
    def animation(self) -> Dict[str, Any]:
        return dict(self._service.state_for("animation"))

    @Property("QVariantMap", notify=threeDChanged)
    def threeD(self) -> Dict[str, Any]:
        return dict(self._service.state_for("threeD"))

    @Property("QVariantMap", notify=renderChanged)
    def render(self) -> Dict[str, Any]:
        return dict(self._service.state_for("render"))

    @Property("QVariantMap", notify=simulationChanged)
    def simulation(self) -> Dict[str, Any]:
        return dict(self._service.state_for("simulation"))

    @Property(QObject, constant=True)
    def signalTrace(self) -> SignalTraceService | None:
        return self._signal_trace

    @Property("QVariantMap", notify=updatesDispatched)
    def latestUpdates(self) -> Dict[str, Any]:
        return {
            key: dict(value) for key, value in self._service.latest_updates().items()
        }

    # ------------------------------------------------------------------
    # Update API
    # ------------------------------------------------------------------
    def dispatch_updates(self, updates: Dict[str, Any]) -> bool:
        """Push a batch of category updates and emit the relevant signals."""

        sanitized = self._service.dispatch_updates(updates)
        if not sanitized:
            return False
        self._emit_updates(sanitized)
        return True

    def update_category(self, key: str, payload: Dict[str, Any]) -> bool:
        """Update a single category."""

        return self.dispatch_updates({key: payload})

    def reset(self, categories: Iterable[str] | None = None) -> None:
        """Reset stored payloads and notify QML listeners."""

        cleared = self._service.reset(categories)
        for key in cleared:
            signal = self._signal_map.get(key)
            if signal is not None:
                signal.emit({})
        self.updatesDispatched.emit({})

    def refresh_orbit_presets(self) -> Dict[str, Any]:
        """Reload orbit presets via the service and broadcast camera updates."""

        manifest = self._service.refresh_orbit_presets()
        updates = {
            key: dict(value)
            for key, value in self._service.latest_updates().items()
            if isinstance(value, dict)
        }
        if updates:
            self._emit_updates(updates)
        return dict(manifest)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _emit_updates(self, updates: Dict[str, Dict[str, Any]]) -> None:
        payload = {}
        for key, value in updates.items():
            signal = self._signal_map.get(key)
            if signal is not None:
                signal.emit(dict(value))
                payload[key] = dict(value)
        if payload:
            self.updatesDispatched.emit(payload)


__all__ = ["SceneBridge"]
