"""Qt bridge models exposed to QML.

The SceneBridge object is registered as a context property and provides
strongly typed properties and signals for all QML controllers.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, Iterable, Mapping, Sequence

from PySide6.QtCore import QObject, Property, Signal

from src.common.settings_manager import SettingsManager
from src.ui.hud import CameraHudTelemetry


_LOGGER = logging.getLogger(__name__)


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

    def __init__(
        self,
        parent: QObject | None = None,
        *,
        settings_manager: SettingsManager | None = None,
    ) -> None:
        super().__init__(parent)
        self._state: Dict[str, Dict[str, Any]] = {key: {} for key in self._KEYS}
        self._latest_updates: Dict[str, Dict[str, Any]] = {}
        self._settings_manager: SettingsManager | None = settings_manager
        self._camera_telemetry = CameraHudTelemetry()
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
        self._populate_camera_defaults()

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
            if key == "camera":
                normalized = self._prepare_camera_payload(normalized)
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

    # ------------------------------------------------------------------
    # Settings integration
    # ------------------------------------------------------------------

    def _resolve_settings_manager(self) -> SettingsManager | None:
        if self._settings_manager is not None:
            return self._settings_manager
        try:
            self._settings_manager = SettingsManager()
        except FileNotFoundError as exc:
            _LOGGER.warning("Settings file not found: %s", exc)
            self._settings_manager = None
        except Exception as exc:  # pragma: no cover - defensive
            _LOGGER.warning("Unable to initialise settings manager: %s", exc)
            self._settings_manager = None
        return self._settings_manager

    def _camera_payload_from_settings(self, manager: SettingsManager) -> Dict[str, Any]:
        raw = manager.get("current.graphics.camera", {})
        return self._prepare_camera_payload(raw, manager=manager)

    def _populate_camera_defaults(self) -> None:
        manager = self._resolve_settings_manager()
        if manager is None:
            return

        payload = self._camera_payload_from_settings(manager)
        if not payload:
            return

        self.dispatch_updates({"camera": payload})

    def refresh_orbit_presets(self) -> Dict[str, Any]:
        """Reload orbit presets via the settings manager and broadcast updates."""

        manager = self._resolve_settings_manager()
        if manager is None:
            return {}

        try:
            manifest = manager.refresh_orbit_presets()
        except Exception as exc:  # pragma: no cover - defensive logging only
            _LOGGER.debug("Unable to refresh orbit presets: %s", exc)
            manifest = {}

        payload = self._camera_payload_from_settings(manager)
        if payload:
            self.dispatch_updates({"camera": payload})

        return manifest

    def _prepare_camera_payload(
        self,
        payload: Any,
        *,
        manager: SettingsManager | None = None,
    ) -> Dict[str, Any]:
        """Normalise camera updates with presets and HUD telemetry."""

        base: Dict[str, Any] = {}
        existing = self._state.get("camera")
        if isinstance(existing, Mapping):
            base.update(dict(existing))

        payload_mapping: Mapping[str, Any] | None = None
        if isinstance(payload, Mapping):
            payload_mapping = payload
            base.update(dict(payload))
        else:
            base = dict(base)

        base.pop("hudTelemetry", None)

        manager_instance = manager or self._resolve_settings_manager()
        if manager_instance is not None:
            try:
                presets = manager_instance.get_orbit_presets()
            except Exception as exc:  # pragma: no cover - defensive logging only
                _LOGGER.debug("Unable to fetch orbit presets: %s", exc)
            else:
                preset_list = presets.get("presets")
                if isinstance(preset_list, list) and preset_list:
                    base["orbitPresets"] = preset_list
                version = presets.get("version")
                if isinstance(version, int):
                    base["orbitPresetVersion"] = version
                default_id = presets.get("default")
                if isinstance(default_id, str) and default_id:
                    base["orbitPresetDefault"] = default_id
                    base.setdefault("orbitPresetId", default_id)
                index = presets.get("index")
                if isinstance(index, Mapping):
                    base["orbitPresetIndex"] = dict(index)

                active_id = base.get("orbitPresetId") or base.get("orbitPresetDefault")
                if active_id and isinstance(preset_list, list):
                    for entry in preset_list:
                        if not isinstance(entry, Mapping):
                            continue
                        if entry.get("id") != active_id:
                            continue
                        label = entry.get("label")
                        if isinstance(label, Mapping):
                            for preferred_key in ("en", "ru"):
                                value = label.get(preferred_key)
                                if isinstance(value, str) and value.strip():
                                    base["orbitPresetLabel"] = value
                                    break
                            if "orbitPresetLabel" not in base:
                                for key, value in label.items():
                                    if key in {"en", "ru"}:
                                        continue
                                    if isinstance(value, str) and value.strip():
                                        base["orbitPresetLabel"] = value
                                        break
                        elif isinstance(label, str) and label.strip():
                            base["orbitPresetLabel"] = label
                        break

        if payload_mapping is None and isinstance(payload, Mapping):
            payload_mapping = payload

        if payload_mapping is not None:
            self._synchronise_vector_field(base, payload_mapping, key="orbit_target")
            self._synchronise_vector_field(base, payload_mapping, key="pan")

        telemetry = self._camera_telemetry.build(base)
        if telemetry:
            base["hudTelemetry"] = telemetry

        return dict(base)

    def _synchronise_vector_field(
        self,
        base: Dict[str, Any],
        payload: Mapping[str, Any],
        *,
        key: str,
    ) -> None:
        """Keep compound vector keys (e.g. orbit_target) and axis aliases in sync."""

        axes: Sequence[str] = ("x", "y", "z")
        components: Dict[str, Any] = {}

        vector_value = payload.get(key)
        if isinstance(vector_value, Mapping):
            for axis in axes:
                if axis in vector_value:
                    components[axis] = vector_value[axis]
                elif axis.upper() in vector_value:
                    components[axis] = vector_value[axis.upper()]
        elif isinstance(vector_value, Sequence) and not isinstance(
            vector_value, (str, bytes, bytearray)
        ):
            for idx, axis in enumerate(axes):
                if len(vector_value) > idx:
                    components[axis] = vector_value[idx]

        for axis in axes:
            explicit_key = f"{key}_{axis}"
            if explicit_key in payload:
                components[axis] = payload[explicit_key]

        existing = base.get(key)
        if isinstance(existing, Mapping):
            for axis in axes:
                components.setdefault(axis, existing.get(axis))
        elif isinstance(existing, Sequence) and not isinstance(
            existing, (str, bytes, bytearray)
        ):
            for idx, axis in enumerate(axes):
                if len(existing) > idx and axis not in components:
                    components[axis] = existing[idx]

        for axis in axes:
            explicit_key = f"{key}_{axis}"
            if explicit_key in base and axis not in components:
                components[axis] = base[explicit_key]

        if not components:
            return

        base[key] = {axis: components[axis] for axis in axes if axis in components}
        for axis in axes:
            explicit_key = f"{key}_{axis}"
            if axis in components:
                base[explicit_key] = components[axis]


__all__ = ["SceneBridge"]
