"""Preset orchestration utilities shared between modular panels."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from src.core.settings_sync_controller import SettingsSyncController


@dataclass(slots=True)
class PresetDefinition:
    """Declarative description of a preset loaded from documentation."""

    preset_id: str
    label: str
    description: str
    patch: dict[str, Any]


class PanelPresetManager:
    """Load preset metadata, manage tooltips and apply registered presets."""

    def __init__(
        self,
        panel_id: str,
        sync_controller: SettingsSyncController,
        *,
        metadata_root: Path | str | None = None,
    ) -> None:
        self._panel_id = panel_id
        self._sync = sync_controller
        self._metadata_root = Path(metadata_root or "docs/help/panels")
        self._tooltips: dict[str, str] = {}
        self._presets: dict[str, PresetDefinition] = {}
        self._applied: list[dict[str, Any]] = []
        self._load_metadata()

    # ----------------------------------------------------------------- metadata
    def _load_metadata(self) -> None:
        path = self._metadata_root / f"{self._panel_id}.json"
        if not path.exists():
            return
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return
        tooltips = payload.get("tooltips", {})
        if isinstance(tooltips, Mapping):
            for key, value in tooltips.items():
                self._tooltips[str(key)] = str(value)
        presets = payload.get("presets", {})
        if not isinstance(presets, Mapping):
            return
        for preset_id, entry in presets.items():
            if not isinstance(entry, Mapping):
                continue
            label = str(entry.get("label", preset_id))
            description = str(entry.get("description", label))
            patch = entry.get("patch", {})
            if not isinstance(patch, Mapping):
                continue
            definition = PresetDefinition(
                preset_id=str(preset_id),
                label=label,
                description=description,
                patch={key: value for key, value in patch.items()},
            )
            self._presets[definition.preset_id] = definition

    # ------------------------------------------------------------------- tooltips
    def get_tooltip(self, key: str, default: str | None = None) -> str | None:
        """Return a contextual tooltip for *key* if present."""

        return self._tooltips.get(key, default)

    # -------------------------------------------------------------------- presets
    def available_presets(self) -> tuple[PresetDefinition, ...]:
        return tuple(self._presets.values())

    def _resolve_preset(
        self, category: str, label: str | None
    ) -> PresetDefinition | None:
        if not label:
            return None
        target = label.strip().casefold()
        for definition in self._presets.values():
            candidates = [
                definition.preset_id,
                definition.label,
                definition.preset_id.split(".")[-1],
            ]
            if category:
                candidates.append(f"{category}.{definition.preset_id}")
            for candidate in candidates:
                if candidate.strip().casefold() == target:
                    return definition
        return None

    def apply_registered_preset(self, preset_id: str) -> PresetDefinition | None:
        definition = self._presets.get(preset_id)
        if definition is None:
            return None
        context = {
            "origin": "preset",
            "preset_id": definition.preset_id,
            "preset_label": definition.label,
        }
        self._sync.apply_patch(
            definition.patch,
            description=definition.description,
            source=definition.preset_id,
            origin="preset",
            metadata=context,
        )
        self._applied.append(context)
        return definition

    def record_application(self, category: str, label: str | None) -> dict[str, Any]:
        definition = self._resolve_preset(category, label)
        metadata = {
            "category": category,
            "preset_label": label or "",
        }
        if definition is not None:
            metadata["preset_id"] = definition.preset_id
            metadata["description"] = definition.description
        else:
            metadata["description"] = f"Apply {category} preset '{label or 'custom'}'"
        self._applied.append(metadata)
        return metadata

    def last_applied(self) -> dict[str, Any] | None:
        return self._applied[-1] if self._applied else None


__all__ = ["PanelPresetManager", "PresetDefinition"]
