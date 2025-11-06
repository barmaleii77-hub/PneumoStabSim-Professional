"""High-level facade used by lighting panels and tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

from PySide6.QtCore import QObject, Property, Signal, Slot

from src.common.settings_manager import (
    SettingsManager,
    get_settings_event_bus,
    get_settings_manager,
)
from src.graphics.materials import MATERIAL_CACHE_TOKEN, MaterialCache
from src.infrastructure.container import (
    ServiceResolutionError,
    get_default_container,
)

from .baseline import MaterialsBaseline, SkyboxOrientation


class LightingSettingsFacade:
    """Expose baseline-driven lighting helpers for UI code."""

    def __init__(
        self,
        *,
        settings_manager: SettingsManager | None = None,
        material_cache: MaterialCache | None = None,
        baseline_path: Path | str | None = None,
    ) -> None:
        self._settings_manager = settings_manager or get_settings_manager()
        if material_cache is not None:
            self._material_cache = material_cache
        elif baseline_path is not None:
            self._material_cache = MaterialCache(baseline_path=Path(baseline_path))
        else:
            container = get_default_container()
            try:
                self._material_cache = container.resolve(MATERIAL_CACHE_TOKEN)
            except ServiceResolutionError:
                self._material_cache = MaterialCache()
        self._baseline = self._material_cache.baseline()

    @property
    def baseline(self) -> MaterialsBaseline:
        return self._baseline

    # Tonemap presets -----------------------------------------------------
    def list_tonemap_presets(self) -> list[Dict[str, Any]]:
        """Return presets formatted for consumption by QML."""

        return [
            preset.to_qml_payload() for preset in self._baseline.list_tonemap_presets()
        ]

    def resolve_active_tonemap_preset(self) -> str | None:
        """Return the preset id matching the current settings, if any."""

        effects = self._settings_manager.get("current.graphics.effects", {})
        for preset in self._baseline.tonemap_presets:
            if preset.matches(effects):
                return preset.id
        return None

    def build_preset_payload(self, preset_id: str) -> Dict[str, Any]:
        """Return the effect values associated with a preset."""

        preset = self._baseline.find_tonemap_preset(preset_id)
        if preset is None:
            raise KeyError(f"Unknown tonemap preset '{preset_id}'")
        payload = {
            "tonemap_mode": preset.mode,
            "tonemap_enabled": preset.tonemap_enabled,
            "tonemap_exposure": preset.exposure,
            "tonemap_white_point": preset.white_point,
        }
        for key, value in preset.extras.items():
            payload[key] = value
        return payload

    def apply_tonemap_preset(
        self, preset_id: str, *, auto_save: bool = False
    ) -> Dict[str, Any]:
        """Update the settings manager with the preset values."""

        payload = self.build_preset_payload(preset_id)
        effects = self._settings_manager.get("current.graphics.effects", {})
        if not isinstance(effects, dict):
            effects = {}
        updated = dict(effects)
        updated.update(payload)
        self._settings_manager.set(
            "current.graphics.effects", updated, auto_save=auto_save
        )
        return updated

    # Skybox helpers ------------------------------------------------------
    def list_skybox_orientations(self) -> Sequence[SkyboxOrientation]:
        return self._baseline.skyboxes

    def list_orientation_issues(self) -> list[Dict[str, Any]]:
        """Return skybox orientation entries flagged for review."""

        issues: list[Dict[str, Any]] = []
        for issue in self._baseline.detect_orientation_issues():
            entry = issue.skybox
            issues.append(
                {
                    "id": entry.id,
                    "label": entry.label,
                    "orientation": entry.orientation,
                    "rotation": entry.rotation,
                    "status": entry.status,
                    "notes": entry.notes or "",
                    "kind": issue.kind,
                    "message": issue.message,
                }
            )
        return issues


class LightingSettingsBridge(QObject):
    """Qt-friendly adapter exposing lighting presets to QML."""

    tonemapPresetsChanged = Signal()
    activeTonemapPresetChanged = Signal()

    def __init__(self, facade: LightingSettingsFacade) -> None:
        super().__init__()
        self._facade = facade
        self._tonemap_presets: list[Dict[str, Any]] = []
        self._active_preset: str = ""
        self._event_bus = get_settings_event_bus()
        self._event_bus.settingChanged.connect(self._on_settings_changed)
        self._event_bus.settingsBatchUpdated.connect(self._on_settings_batch)
        self._refresh_presets()
        self._refresh_active_preset()

    # ------------------------------------------------------------------ helpers
    def _refresh_presets(self) -> None:
        presets = self._facade.list_tonemap_presets()
        self._tonemap_presets = [dict(preset) for preset in presets]
        self.tonemapPresetsChanged.emit()

    def _refresh_active_preset(self) -> None:
        active = self._facade.resolve_active_tonemap_preset() or ""
        if active == self._active_preset:
            return
        self._active_preset = active
        self.activeTonemapPresetChanged.emit()

    def _payload_targets_effects(self, payload: Dict[str, Any]) -> bool:
        path = payload.get("path")
        if isinstance(path, str) and path.startswith("current.graphics.effects"):
            return True
        changes = payload.get("changes")
        if isinstance(changes, Sequence):
            for item in changes:
                if not isinstance(item, Mapping):
                    continue
                nested_path = item.get("path")
                if isinstance(nested_path, str) and nested_path.startswith(
                    "current.graphics.effects"
                ):
                    return True
        return False

    def _on_settings_changed(self, payload: Dict[str, Any]) -> None:
        if self._payload_targets_effects(payload):
            self._refresh_active_preset()

    def _on_settings_batch(self, payload: Dict[str, Any]) -> None:
        if self._payload_targets_effects(payload):
            self._refresh_active_preset()

    # ----------------------------------------------------------------- properties
    @Property("QVariantList", notify=tonemapPresetsChanged)
    def tonemapPresets(self) -> list[Dict[str, Any]]:  # pragma: no cover - Qt binding
        return [dict(item) for item in self._tonemap_presets]

    @Property(str, notify=activeTonemapPresetChanged)
    def activeTonemapPreset(self) -> str:  # pragma: no cover - Qt binding
        return self._active_preset

    # --------------------------------------------------------------------- slots
    @Slot(result="QVariantList")
    def reloadTonemapPresets(self) -> list[Dict[str, Any]]:
        self._refresh_presets()
        return self.tonemapPresets

    @Slot(str, result="QVariantMap")
    def applyTonemapPreset(self, preset_id: str) -> Dict[str, Any]:
        updated = self._facade.apply_tonemap_preset(preset_id, auto_save=True)
        self._refresh_active_preset()
        return dict(updated)

    @Slot(result="QVariantList")
    def listOrientationIssues(self) -> list[Dict[str, Any]]:
        issues = self._facade.list_orientation_issues()
        return [dict(issue) for issue in issues]
