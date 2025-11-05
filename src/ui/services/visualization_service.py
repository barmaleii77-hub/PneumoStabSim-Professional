"""Service encapsulating the state management for :mod:`SceneBridge`."""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from typing import Any, Dict, Optional

from src.common.settings_manager import SettingsManager
from src.core.interfaces import VisualizationService as VisualizationServiceProtocol
from src.ui.hud import CameraHudTelemetry


class VisualizationService(VisualizationServiceProtocol):
    """Maintain a canonical snapshot of geometry and rendering categories."""

    _CATEGORIES: Sequence[str] = (
        "geometry",
        "camera",
        "lighting",
        "environment",
        "scene",
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
        *,
        settings_manager: Optional[SettingsManager] = None,
    ) -> None:
        self._state: Dict[str, Dict[str, Any]] = {key: {} for key in self._CATEGORIES}
        self._latest_updates: Dict[str, Dict[str, Any]] = {}
        self._settings_manager = settings_manager
        self._camera_telemetry = CameraHudTelemetry()

    # ----------------------------------------------------------------- protocol
    def categories(self) -> Sequence[str]:
        return self._CATEGORIES

    def state_for(self, category: str) -> Mapping[str, Any]:
        return dict(self._state.get(category, {}))

    def latest_updates(self) -> Mapping[str, Mapping[str, Any]]:
        return {key: dict(value) for key, value in self._latest_updates.items()}

    def dispatch_updates(
        self, updates: Mapping[str, Mapping[str, Any]]
    ) -> Mapping[str, Mapping[str, Any]]:
        sanitized: Dict[str, Dict[str, Any]] = {}
        for key, payload in updates.items():
            if key not in self._CATEGORIES:
                continue
            normalised = self._sanitize_payload(payload)
            if key == "camera":
                normalised = self.prepare_camera_payload(normalised)
            self._state[key] = normalised
            sanitized[key] = dict(normalised)

        if sanitized:
            self._latest_updates = sanitized
        else:
            self._latest_updates = {}

        return {key: dict(value) for key, value in sanitized.items()}

    def reset(self, categories: Iterable[str] | None = None) -> Iterable[str]:
        keys = list(categories) if categories is not None else list(self._CATEGORIES)
        cleared: list[str] = []
        for key in keys:
            if key not in self._CATEGORIES:
                continue
            self._state[key] = {}
            cleared.append(key)
        self._latest_updates = {}
        return tuple(cleared)

    def prepare_camera_payload(
        self, payload: Mapping[str, Any] | None = None
    ) -> Mapping[str, Any]:
        manager = self._resolve_settings_manager()
        base: Dict[str, Any] = {}
        if manager is not None:
            camera_defaults = manager.get("current.graphics.camera", {})
            if isinstance(camera_defaults, Mapping):
                base.update(self._sanitize_payload(camera_defaults))

        existing = self._state.get("camera")
        if isinstance(existing, Mapping):
            base.update(dict(existing))

        payload_mapping = payload if isinstance(payload, Mapping) else {}
        base.update(dict(payload_mapping))
        base.pop("hudTelemetry", None)

        if manager is not None:
            self._augment_with_orbit_metadata(base, manager)

        self._synchronise_vector_field(base, payload_mapping, key="orbit_target")
        self._synchronise_vector_field(base, payload_mapping, key="pan")

        telemetry = self._camera_telemetry.build(base)
        if telemetry:
            base["hudTelemetry"] = telemetry

        return dict(base)

    def refresh_orbit_presets(self) -> Mapping[str, Any]:
        manager = self._resolve_settings_manager()
        if manager is None:
            return {}
        manifest = manager.refresh_orbit_presets()
        payload = manager.get("current.graphics.camera", {})
        camera_payload = self.prepare_camera_payload(payload)
        if camera_payload:
            self.dispatch_updates({"camera": camera_payload})
        return manifest

    # ----------------------------------------------------------------- helpers
    def populate_camera_defaults(self) -> Mapping[str, Mapping[str, Any]]:
        manager = self._resolve_settings_manager()
        if manager is None:
            return {}
        payload = manager.get("current.graphics.camera", {})
        camera_payload = self.prepare_camera_payload(payload)
        if not camera_payload:
            return {}
        return self.dispatch_updates({"camera": camera_payload})

    def _resolve_settings_manager(self) -> Optional[SettingsManager]:
        if self._settings_manager is not None:
            return self._settings_manager
        try:
            self._settings_manager = SettingsManager()
        except Exception:  # pragma: no cover - defensive fall-back
            self._settings_manager = None
        return self._settings_manager

    @staticmethod
    def _sanitize_payload(payload: Mapping[str, Any] | None) -> Dict[str, Any]:
        if isinstance(payload, Mapping):
            return {key: deepcopy(value) for key, value in payload.items()}
        return {}

    def _augment_with_orbit_metadata(
        self, payload: Dict[str, Any], manager: SettingsManager
    ) -> None:
        try:
            presets = manager.get_orbit_presets()
        except Exception:  # pragma: no cover - defensive logging only
            return

        preset_list = presets.get("presets")
        if isinstance(preset_list, list) and preset_list:
            payload["orbitPresets"] = deepcopy(preset_list)
        version = presets.get("version")
        if isinstance(version, int):
            payload["orbitPresetVersion"] = version
        default_id = presets.get("default")
        if isinstance(default_id, str) and default_id:
            payload["orbitPresetDefault"] = default_id
            payload.setdefault("orbitPresetId", default_id)
        index = presets.get("index")
        if isinstance(index, Mapping):
            payload["orbitPresetIndex"] = {
                key: dict(value)
                for key, value in index.items()
                if isinstance(value, Mapping)
            }

        active_id = payload.get("orbitPresetId") or payload.get("orbitPresetDefault")
        if not active_id or not isinstance(preset_list, list):
            return
        for entry in preset_list:
            if not isinstance(entry, Mapping) or entry.get("id") != active_id:
                continue
            label = entry.get("label")
            if isinstance(label, Mapping):
                for preferred_key in ("en", "ru"):
                    value = label.get(preferred_key)
                    if isinstance(value, str) and value.strip():
                        payload["orbitPresetLabel"] = value
                        break
                if "orbitPresetLabel" not in payload:
                    for key, value in label.items():
                        if key in {"en", "ru"}:
                            continue
                        if isinstance(value, str) and value.strip():
                            payload["orbitPresetLabel"] = value
                            break
            elif isinstance(label, str) and label.strip():
                payload["orbitPresetLabel"] = label
            break

    def _synchronise_vector_field(
        self,
        base: Dict[str, Any],
        payload: Mapping[str, Any],
        *,
        key: str,
    ) -> None:
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


__all__ = ["VisualizationService"]
