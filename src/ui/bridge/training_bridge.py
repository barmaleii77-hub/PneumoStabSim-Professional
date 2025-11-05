"""Qt bridge exposing training presets to QML."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from PySide6.QtCore import QObject, Property, Signal, Slot

from src.common.settings_manager import (
    SettingsManager,
    get_settings_event_bus,
    get_settings_manager,
)
from src.simulation.presets import TrainingPresetLibrary, get_default_training_library


class TrainingPresetBridge(QObject):
    """Expose training preset catalogue and application helpers to QML."""

    presetsChanged = Signal()
    activePresetChanged = Signal()
    selectedPresetChanged = Signal()

    def __init__(
        self,
        *,
        settings_manager: Optional[SettingsManager] = None,
        library: Optional[TrainingPresetLibrary] = None,
    ) -> None:
        super().__init__()
        self._settings_manager = settings_manager or get_settings_manager()
        self._library = library or get_default_training_library()
        self._event_bus = get_settings_event_bus()
        self._presets_payload: List[Dict[str, Any]] = []
        self._active_preset_id: str = ""
        self._selected_payload: Dict[str, Any] = {}
        self._refresh_presets()
        self._refresh_active_preset()
        self._event_bus.settingChanged.connect(self._handle_settings_event)
        self._event_bus.settingsBatchUpdated.connect(self._handle_settings_event)

    # ------------------------------------------------------------------ internals
    def _handle_settings_event(self, _payload: Dict[str, Any]) -> None:
        self._refresh_active_preset()

    def _refresh_presets(self) -> None:
        self._presets_payload = [
            dict(payload) for payload in self._library.describe_presets()
        ]
        self.presetsChanged.emit()

    def _resolve_active_id(self) -> str:
        snapshot = {
            "simulation": self._settings_manager.get("current.simulation", {}),
            "pneumatic": self._settings_manager.get("current.pneumatic", {}),
        }
        return self._library.resolve_active_id(snapshot)

    def _describe(self, preset_id: str) -> Dict[str, Any]:
        preset = self._library.get(preset_id)
        if preset is None:
            return {}
        payload = preset.to_qml_payload()
        return dict(payload)

    def _set_selected_payload(self, preset_id: str) -> None:
        self._selected_payload = self._describe(preset_id)
        self.selectedPresetChanged.emit()

    def _refresh_active_preset(self) -> None:
        active_id = self._resolve_active_id()
        if active_id == self._active_preset_id:
            return
        self._active_preset_id = active_id
        self.activePresetChanged.emit()
        if active_id:
            self._set_selected_payload(active_id)
        else:
            if self._selected_payload:
                self._selected_payload = {}
                self.selectedPresetChanged.emit()

    # ------------------------------------------------------------------ properties
    @Property("QVariantList", notify=presetsChanged)
    def presets(self) -> List[Dict[str, Any]]:  # pragma: no cover - Qt binding
        return [dict(item) for item in self._presets_payload]

    @Property(str, notify=activePresetChanged)
    def activePresetId(self) -> str:  # pragma: no cover - Qt binding
        return self._active_preset_id

    @Property("QVariantMap", notify=selectedPresetChanged)
    def selectedPreset(self) -> Dict[str, Any]:  # pragma: no cover - Qt binding
        return dict(self._selected_payload)

    # ---------------------------------------------------------------------- slots
    @Slot(result="QVariantList")
    def listPresets(self) -> List[Dict[str, Any]]:
        return [dict(item) for item in self._presets_payload]

    @Slot(str, result="QVariantMap")
    def describePreset(self, preset_id: str) -> Dict[str, Any]:
        return self._describe(preset_id)

    @Slot(str, result=bool)
    def applyPreset(self, preset_id: str) -> bool:
        if not preset_id:
            return False
        try:
            self._library.apply(self._settings_manager, preset_id, auto_save=True)
        except KeyError:
            return False
        self._refresh_active_preset()
        if preset_id:
            self._set_selected_payload(preset_id)
        return True

    @Slot(result=str)
    def defaultPresetId(self) -> str:
        if not self._presets_payload:
            return ""
        return str(self._presets_payload[0].get("id", ""))

    @Slot(result="QVariantList")
    def refreshPresets(self) -> List[Dict[str, Any]]:
        self._refresh_presets()
        self._refresh_active_preset()
        return self.listPresets()
