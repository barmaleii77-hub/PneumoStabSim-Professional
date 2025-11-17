"""Service encapsulating the state management for :mod:`SceneBridge`."""

from __future__ import annotations

import logging
from collections.abc import Iterable, Mapping, Sequence
from copy import deepcopy
from typing import Any

from src.common.settings_manager import SettingsManager
from src.core.interfaces import VisualizationService as VisualizationServiceProtocol
from src.security.access_control import AccessControlService, get_access_control
from src.ui.hud import CameraHudTelemetry


logger = logging.getLogger(__name__)


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

    _CATEGORY_PERMISSION_MAP: Mapping[str, str] = {
        "geometry": "current.geometry",
        "camera": "current.graphics.camera",
        "lighting": "current.graphics.lighting",
        "environment": "current.graphics.environment",
        "scene": "current.graphics.scene",
        "quality": "current.graphics.quality",
        "materials": "current.graphics.materials",
        "effects": "current.graphics.effects",
        "animation": "current.animation",
        "threeD": "current.threeD",
        "render": "current.render",
        "simulation": "current.simulation",
    }

    _GRAPHICS_CATEGORY_PATHS: Mapping[str, str] = {
        "camera": "current.graphics.camera",
        "lighting": "current.graphics.lighting",
        "environment": "current.graphics.environment",
        "scene": "current.graphics.scene",
        "quality": "current.graphics.quality",
        "materials": "current.graphics.materials",
        "effects": "current.graphics.effects",
    }

    def __init__(
        self,
        *,
        settings_manager: SettingsManager | None = None,
        access_control: AccessControlService | None = None,
    ) -> None:
        self._state: dict[str, dict[str, Any]] = {key: {} for key in self._CATEGORIES}
        self._latest_updates: dict[str, dict[str, Any]] = {}
        self._settings_manager = settings_manager
        self._camera_telemetry = CameraHudTelemetry()
        self._access_control = access_control or get_access_control()

    # ----------------------------------------------------------------- startup
    def populate_initial_state(self) -> Mapping[str, Mapping[str, Any]]:
        """Load persisted graphics settings into the service state."""

        manager = self._resolve_settings_manager()
        if manager is None:
            logger.debug("VisualizationService.populate_initial_state: no manager")
            return self.populate_camera_defaults()

        payload: dict[str, Mapping[str, Any]] = {}
        loaded_categories: list[str] = []

        for category, path in self._GRAPHICS_CATEGORY_PATHS.items():
            try:
                raw = manager.get(path, {})
            except Exception as exc:  # pragma: no cover - defensive logging only
                logger.warning(
                    "Failed to read settings for %s (%s): %s",
                    category,
                    path,
                    exc,
                )
                continue

            if not isinstance(raw, Mapping) or not raw:
                if raw:
                    logger.warning(
                        "Settings payload for %s is not a mapping: %r",
                        path,
                        type(raw).__name__,
                    )
                continue

            payload[category] = dict(raw)
            loaded_categories.append(category)

        try:
            animation_payload = manager.get("current.animation", {})
        except Exception as exc:  # pragma: no cover - optional log path
            logger.warning("Failed to read settings for animation: %s", exc)
        else:
            if isinstance(animation_payload, Mapping) and animation_payload:
                payload["animation"] = dict(animation_payload)
                loaded_categories.append("animation")

        if not payload:
            logger.debug(
                "VisualizationService.populate_initial_state: no persisted payloads"
            )
            return self.populate_camera_defaults()

        logger.info(
            "Loaded graphics defaults for categories: %s",
            ", ".join(sorted(set(loaded_categories))),
        )

        return self.dispatch_updates(payload)

    # ----------------------------------------------------------------- protocol
    def categories(self) -> Sequence[str]:
        return self._CATEGORIES

    def state_for(self, category: str) -> Mapping[str, Any]:
        return dict(self._state.get(category, {}))

    def latest_updates(self) -> Mapping[str, Mapping[str, Any]]:
        return {key: dict(value) for key, value in self._latest_updates.items()}

    def access_profile(self) -> Mapping[str, Any]:
        return self._access_control.describe_access_profile()

    def dispatch_updates(
        self, updates: Mapping[str, Mapping[str, Any]]
    ) -> Mapping[str, Mapping[str, Any]]:
        sanitized: dict[str, dict[str, Any]] = {}
        for key, payload in updates.items():
            if key not in self._CATEGORIES:
                continue
            normalised = self._sanitize_payload(payload)
            if key == "camera":
                normalised = self.prepare_camera_payload(normalised)
            access_payload = self._build_access_payload(key)
            if access_payload:
                enriched = dict(normalised)
                enriched["_access"] = access_payload
            else:
                enriched = normalised
            self._state[key] = enriched
            sanitized[key] = dict(enriched)

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
        base: dict[str, Any] = {}
        if manager is not None:
            camera_defaults = manager.get("current.graphics.camera", {})
            if isinstance(camera_defaults, Mapping):
                base.update(self._sanitize_payload(camera_defaults))

        existing = self._state.get("camera")
        if isinstance(existing, Mapping):
            base.update(dict(existing))

        payload_mapping = payload if isinstance(payload, Mapping) else {}

        manager = self._resolve_settings_manager()
        camera_defaults: Mapping[str, Any] | None = None
        if manager is not None:
            defaults_payload = manager.get("current.graphics.camera", {})
            if isinstance(defaults_payload, Mapping):
                camera_defaults = defaults_payload
                base.update(dict(defaults_payload))
            self._augment_with_orbit_metadata(base, manager)

        base.update(dict(payload_mapping))
        base.pop("hudTelemetry", None)

        if isinstance(camera_defaults, Mapping):
            self._synchronise_vector_field(base, camera_defaults, key="orbit_target")
            self._synchronise_vector_field(base, camera_defaults, key="pan")

        self._synchronise_vector_field(base, payload_mapping, key="orbit_target")
        self._synchronise_vector_field(base, payload_mapping, key="pan")

        telemetry = self._camera_telemetry.build(base)
        if telemetry:
            # Нормализация HUD: pivot.z
            # - отрицательные значения → abs(z)
            # - почти ноль (|z| < 0.01) или нечисло → 0.5
            # - значения с «заглушками» из app_settings (|z| >= 99) → 0.5
            # - положительные значения остаются без изменений
            try:
                pivot = (
                    telemetry.get("pivot") if isinstance(telemetry, Mapping) else None
                )
                if isinstance(pivot, Mapping):
                    z_val = pivot.get("z")
                    new_z: float
                    try:
                        new_z = float(z_val)  # type: ignore[arg-type]
                    except Exception:
                        new_z = 0.5
                    if abs(new_z) < 0.01:
                        new_z = 0.5
                    elif abs(new_z) >= 99.0:
                        new_z = 0.5
                    elif new_z < 0.0:
                        new_z = abs(new_z)
                    # иначе положительное и значимое → оставить как есть
                    pivot = dict(pivot)
                    pivot["z"] = new_z
                    telemetry = dict(telemetry)
                    telemetry["pivot"] = pivot
            except Exception:
                pass
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

    def _resolve_settings_manager(self) -> SettingsManager | None:
        if self._settings_manager is not None:
            return self._settings_manager
        try:
            self._settings_manager = SettingsManager()
        except Exception:  # pragma: no cover - defensive fall-back
            self._settings_manager = None
        return self._settings_manager

    @staticmethod
    def _sanitize_payload(payload: Mapping[str, Any] | None) -> dict[str, Any]:
        if isinstance(payload, Mapping):
            return {key: deepcopy(value) for key, value in payload.items()}
        return {}

    def _build_access_payload(self, category: str) -> dict[str, Any] | None:
        target = self._CATEGORY_PERMISSION_MAP.get(category)
        if not target:
            return None
        can_edit = self._access_control.can_modify(target)
        profile = self._access_control.describe_access_profile()
        payload: dict[str, Any] = {
            "role": profile.get("role", "unknown"),
            "actor": profile.get("actor", "system"),
            "description": profile.get("description", ""),
            "uiFlags": dict(profile.get("uiFlags", {})),
            "simulationProfile": profile.get("simulationProfile", ""),
            "editablePrefixes": list(profile.get("editablePrefixes", [])),
            "targetPath": target,
            "canEdit": can_edit,
            "readOnly": not can_edit,
        }
        return payload

    def _augment_with_orbit_metadata(
        self, payload: dict[str, Any], manager: SettingsManager
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
        base: dict[str, Any],
        payload: Mapping[str, Any],
        *,
        key: str,
    ) -> None:
        axes: Sequence[str] = ("x", "y", "z")
        components: dict[str, Any] = {}

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
