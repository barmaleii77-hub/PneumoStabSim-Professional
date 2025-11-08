"""Orbit controller coordinating preset application and settings updates."""

from __future__ import annotations

from typing import Any
from collections.abc import Mapping

from PySide6.QtCore import QObject, Signal, Slot

from src.common.settings_manager import SettingsManager
from src.ui.services.visualization_service import VisualizationService

__all__ = ["OrbitController"]


class OrbitController(QObject):
    """Apply orbit presets through :class:`SettingsManager`."""

    manifestChanged = Signal("QVariantMap")
    presetApplied = Signal(str, "QVariantMap")

    def __init__(
        self,
        parent: QObject | None = None,
        *,
        settings_manager: SettingsManager | None = None,
        visualization_service: VisualizationService | None = None,
    ) -> None:
        super().__init__(parent)
        self._settings_manager = settings_manager
        self._visualization_service = visualization_service
        self._manifest: dict[str, Any] = {}
        self._active_preset: str | None = None
        self._load_manifest(initial=True)

    def manifest(self) -> dict[str, Any]:
        """Return the cached preset manifest."""

        return dict(self._manifest)

    def active_preset(self) -> str | None:
        """Return the last applied preset identifier."""

        return self._active_preset

    @Slot()
    def refresh_presets(self) -> dict[str, Any]:
        """Reload the preset manifest via :class:`SettingsManager`."""

        manager = self._resolve_settings_manager()
        manifest = manager.refresh_orbit_presets()
        return self._load_manifest(manifest=manifest)

    @Slot(str)
    def apply_preset(self, preset_id: str) -> dict[str, Any]:
        """Apply ``preset_id`` to the active settings profile."""

        if not preset_id:
            return {}

        manifest = self._manifest or self._load_manifest()
        preset_entry = self._resolve_preset_entry(manifest, preset_id)
        if not preset_entry:
            return {}

        values = preset_entry.get("values")
        if not isinstance(values, Mapping):
            return {}

        manager = self._resolve_settings_manager()
        current_payload = manager.get("current.graphics.camera", {})
        if not isinstance(current_payload, Mapping):
            current_payload = {}
        merged: dict[str, Any] = {key: value for key, value in current_payload.items()}
        for key, value in values.items():
            merged[str(key)] = value

        merged["orbitPresetId"] = preset_id
        version = manifest.get("version")
        if isinstance(version, int):
            merged["orbitPresetVersion"] = version

        manager.set("current.graphics.camera", merged)

        payload = self._prepare_payload(merged)
        self._active_preset = preset_id
        self.presetApplied.emit(preset_id, dict(payload))
        return payload

    def _load_manifest(
        self,
        manifest: Mapping[str, Any] | None = None,
        *,
        initial: bool = False,
    ) -> dict[str, Any]:
        manager = self._resolve_settings_manager()
        data = manifest if manifest is not None else manager.get_orbit_presets()
        if not isinstance(data, Mapping):
            data = {}
        manifest_payload = {key: value for key, value in data.items()}
        self._manifest = manifest_payload
        if initial or manifest is not None:
            self.manifestChanged.emit(dict(self._manifest))
        return dict(self._manifest)

    def _resolve_settings_manager(self) -> SettingsManager:
        if self._settings_manager is None:
            self._settings_manager = SettingsManager()
        return self._settings_manager

    def _resolve_visualization_service(self) -> VisualizationService | None:
        if self._visualization_service is None:
            try:
                self._visualization_service = VisualizationService(
                    settings_manager=self._settings_manager
                )
            except Exception:  # pragma: no cover - fallback in tests
                self._visualization_service = None
        return self._visualization_service

    def _resolve_preset_entry(
        self, manifest: Mapping[str, Any], preset_id: str
    ) -> Mapping[str, Any] | None:
        index = manifest.get("index")
        if isinstance(index, Mapping) and preset_id in index:
            entry = index[preset_id]
            if isinstance(entry, Mapping):
                return entry

        presets = manifest.get("presets")
        if isinstance(presets, list):
            for entry in presets:
                if isinstance(entry, Mapping) and entry.get("id") == preset_id:
                    return entry
        return None

    def _prepare_payload(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        service = self._resolve_visualization_service()
        if service is None:
            return {key: value for key, value in payload.items()}

        prepared = service.prepare_camera_payload(payload)
        if not isinstance(prepared, Mapping):
            prepared = payload

        updates = service.dispatch_updates({"camera": dict(prepared)})
        camera_payload = updates.get("camera") if isinstance(updates, Mapping) else None
        if isinstance(camera_payload, Mapping):
            return {key: value for key, value in camera_payload.items()}
        return {key: value for key, value in prepared.items()}
