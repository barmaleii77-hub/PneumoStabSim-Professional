"""High-level facade used by lighting panels and tests."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Sequence

from src.common.settings_manager import SettingsManager, get_settings_manager

from .baseline import (
    MaterialsBaseline,
    SkyboxOrientation,
    load_materials_baseline,
)


class LightingSettingsFacade:
    """Expose baseline-driven lighting helpers for UI code."""

    def __init__(
        self,
        *,
        settings_manager: SettingsManager | None = None,
        baseline_path: Path | str | None = None,
    ) -> None:
        self._settings_manager = settings_manager or get_settings_manager()
        if baseline_path is None:
            self._baseline = load_materials_baseline()
        else:
            self._baseline = load_materials_baseline(Path(baseline_path))

    @property
    def baseline(self) -> MaterialsBaseline:
        return self._baseline

    # Tonemap presets -----------------------------------------------------
    def list_tonemap_presets(self) -> list[Dict[str, Any]]:
        """Return presets formatted for consumption by QML."""

        return [preset.to_qml_payload() for preset in self._baseline.tonemap_presets]

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
        for entry in self._baseline.skyboxes:
            if entry.status != "ok" or entry.orientation != "z-up":
                issues.append(
                    {
                        "id": entry.id,
                        "label": entry.label,
                        "orientation": entry.orientation,
                        "rotation": entry.rotation,
                        "status": entry.status,
                        "notes": entry.notes or "",
                    }
                )
        return issues
