"""Qt bridge exposing training presets to QML."""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional

from PySide6.QtCore import QObject, Property, Signal, Slot

from src.common.settings_manager import SettingsManager, get_settings_manager
from src.core.settings_orchestrator import SettingsOrchestrator
from src.simulation.presets import TrainingPresetLibrary, get_default_training_library
from src.simulation.service import TrainingPresetService


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
        simulation_service: Optional[TrainingPresetService] = None,
        orchestrator: Optional[SettingsOrchestrator] = None,
    ) -> None:
        super().__init__()
        self._settings_manager = settings_manager or get_settings_manager()
        self._library = library or get_default_training_library()
        self._orchestrator = orchestrator or SettingsOrchestrator(
            settings_manager=self._settings_manager
        )
        self._service = simulation_service or TrainingPresetService(
            orchestrator=self._orchestrator, library=self._library
        )
        self._presets_payload: List[Dict[str, Any]] = []
        self._active_preset_id: str = ""
        self._selected_payload: Dict[str, Any] = {}
        self._refresh_presets()
        self._refresh_active_preset()
        self._dispose_callbacks: List[Callable[[], None]] = []
        self._dispose_callbacks.append(
            self._service.register_active_observer(self._handle_active_change)
        )
        self.destroyed.connect(lambda _=None: self._cleanup())

    # ------------------------------------------------------------------ internals
    def _cleanup(self) -> None:
        for callback in self._dispose_callbacks:
            try:
                callback()
            except Exception:  # pragma: no cover - defensive cleanup
                pass
        self._dispose_callbacks.clear()
        if hasattr(self._service, "close"):
            try:
                self._service.close()
            except Exception:  # pragma: no cover - defensive cleanup
                pass
        if hasattr(self._orchestrator, "close"):
            try:
                self._orchestrator.close()
            except Exception:  # pragma: no cover - defensive cleanup
                pass

    def _handle_active_change(self, preset_id: str) -> None:
        if preset_id == self._active_preset_id:
            return
        self._active_preset_id = preset_id
        self.activePresetChanged.emit()
        if preset_id:
            self._set_selected_payload(preset_id)
        else:
            if self._selected_payload:
                self._selected_payload = {}
                self.selectedPresetChanged.emit()

    def _refresh_presets(self) -> None:
        self._presets_payload = [
            dict(payload) for payload in self._service.list_presets()
        ]
        self.presetsChanged.emit()

    def _resolve_active_id(self) -> str:
        return self._service.active_preset_id()

    def _describe(self, preset_id: str) -> Dict[str, Any]:
        payload = self._service.describe_preset(preset_id)
        return dict(payload)

    def _set_selected_payload(self, preset_id: str) -> None:
        self._selected_payload = self._describe(preset_id)
        self.selectedPresetChanged.emit()

    def _refresh_active_preset(self) -> None:
        self._handle_active_change(self._resolve_active_id())

    # ------------------------------------------------------------------ properties
    @Property("QVariantList", notify=presetsChanged)
    def presets(self) -> List[Dict[str, Any]]:  # pragma: no cover - Qt binding
        return [dict(item) for item in self._presets_payload]

    @Property(str, notify=activePresetChanged)
    def activePresetId(self) -> str:  # pragma: no cover - Qt binding
        return self._active_preset_id

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
        previous_active = self._active_preset_id
        try:
            self._service.apply_preset(preset_id, auto_save=True)
        except KeyError:
            return False
        self._set_selected_payload(preset_id)
        if self._active_preset_id == previous_active:
            # Ensure consumers receive a signal even when the same preset is re-applied.
            self._active_preset_id = self._service.active_preset_id()
            self.activePresetChanged.emit()
        return True

    @Slot(result=str)
    def defaultPresetId(self) -> str:
        if not self._presets_payload:
            return ""
        return str(self._presets_payload[0].get("id", ""))

    @Slot(result="QVariantMap")
    def selectedPreset(self) -> Dict[str, Any]:
        return dict(self._selected_payload)

    @Slot(result="QVariantList")
    def refreshPresets(self) -> List[Dict[str, Any]]:
        self._refresh_presets()
        self._refresh_active_preset()
        return self.listPresets()
