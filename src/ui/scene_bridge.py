"""Qt bridge models exposed to QML.

The SceneBridge object is registered as a context property and provides
strongly typed properties and signals for all QML controllers.
"""

from __future__ import annotations

from typing import Any, Dict, Iterable

from PySide6.QtCore import QObject, Property, Signal


class SceneBridge(QObject):
    """Expose simulation state updates to QML via Qt properties/signals."""

    updatesDispatched = Signal("QVariantMap")
    geometryChanged = Signal("QVariantMap")
    cameraChanged = Signal("QVariantMap")
    lightingChanged = Signal("QVariantMap")
    environmentChanged = Signal("QVariantMap")
    qualityChanged = Signal("QVariantMap")
    materialsChanged = Signal("QVariantMap")
    effectsChanged = Signal("QVariantMap")
    animationChanged = Signal("QVariantMap")
    threeDChanged = Signal("QVariantMap")
    renderChanged = Signal("QVariantMap")
    simulationChanged = Signal("QVariantMap")

    _KEYS = (
        "geometry",
        "camera",
        "lighting",
        "environment",
        "quality",
        "materials",
        "effects",
        "animation",
        "threeD",
        "render",
        "simulation",
    )

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._state: Dict[str, Dict[str, Any]] = {key: {} for key in self._KEYS}
        self._latest_updates: Dict[str, Dict[str, Any]] = {}
        self._signal_map = {
            "geometry": self.geometryChanged,
            "camera": self.cameraChanged,
            "lighting": self.lightingChanged,
            "environment": self.environmentChanged,
            "quality": self.qualityChanged,
            "materials": self.materialsChanged,
            "effects": self.effectsChanged,
            "animation": self.animationChanged,
            "threeD": self.threeDChanged,
            "render": self.renderChanged,
            "simulation": self.simulationChanged,
        }

    # ------------------------------------------------------------------
    # Qt Properties
    # ------------------------------------------------------------------
    @Property("QVariantMap", notify=geometryChanged)
    def geometry(self) -> Dict[str, Any]:
        return self._state["geometry"]

    @Property("QVariantMap", notify=cameraChanged)
    def camera(self) -> Dict[str, Any]:
        return self._state["camera"]

    @Property("QVariantMap", notify=lightingChanged)
    def lighting(self) -> Dict[str, Any]:
        return self._state["lighting"]

    @Property("QVariantMap", notify=environmentChanged)
    def environment(self) -> Dict[str, Any]:
        return self._state["environment"]

    @Property("QVariantMap", notify=qualityChanged)
    def quality(self) -> Dict[str, Any]:
        return self._state["quality"]

    @Property("QVariantMap", notify=materialsChanged)
    def materials(self) -> Dict[str, Any]:
        return self._state["materials"]

    @Property("QVariantMap", notify=effectsChanged)
    def effects(self) -> Dict[str, Any]:
        return self._state["effects"]

    @Property("QVariantMap", notify=animationChanged)
    def animation(self) -> Dict[str, Any]:
        return self._state["animation"]

    @Property("QVariantMap", notify=threeDChanged)
    def threeD(self) -> Dict[str, Any]:
        return self._state["threeD"]

    @Property("QVariantMap", notify=renderChanged)
    def render(self) -> Dict[str, Any]:
        return self._state["render"]

    @Property("QVariantMap", notify=simulationChanged)
    def simulation(self) -> Dict[str, Any]:
        return self._state["simulation"]

    @Property("QVariantMap", notify=updatesDispatched)
    def latestUpdates(self) -> Dict[str, Any]:
        return self._latest_updates

    # ------------------------------------------------------------------
    # Update API
    # ------------------------------------------------------------------
    def dispatch_updates(self, updates: Dict[str, Any]) -> bool:
        """Push a batch of category updates and emit the relevant signals."""
        if not updates:
            return False

        sanitized_updates: Dict[str, Dict[str, Any]] = {}
        for key, payload in updates.items():
            if key not in self._signal_map:
                continue
            normalized = self._sanitize_payload(payload)
            self._state[key] = normalized
            sanitized_updates[key] = normalized
            self._signal_map[key].emit(normalized)

        if not sanitized_updates:
            return False

        self._latest_updates = sanitized_updates
        self.updatesDispatched.emit(sanitized_updates)
        return True

    def update_category(self, key: str, payload: Dict[str, Any]) -> bool:
        """Update a single category."""
        return self.dispatch_updates({key: payload})

    def reset(self, categories: Iterable[str] | None = None) -> None:
        """Reset stored payloads and notify QML listeners."""
        keys = list(categories) if categories is not None else list(self._KEYS)
        for key in keys:
            if key not in self._signal_map:
                continue
            self._state[key] = {}
            self._signal_map[key].emit({})
        self._latest_updates = {}
        self.updatesDispatched.emit({})

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _sanitize_payload(payload: Any) -> Dict[str, Any]:
        if isinstance(payload, dict):
            return dict(payload)
        return {}


__all__ = ["SceneBridge"]
