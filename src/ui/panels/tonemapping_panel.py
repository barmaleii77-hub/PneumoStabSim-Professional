from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping
from collections.abc import Sequence

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.common.settings_manager import (
    SettingsEventBus,
    get_settings_event_bus,
    get_settings_manager,
)
from src.graphics.materials.baseline import TonemapPreset
from src.ui.panels.lighting.settings import LightingSettingsFacade


@dataclass(frozen=True)
class _PresetEntry:
    preset: TonemapPreset
    label: str
    description: str


class TonemappingPanel(QWidget):
    """Allow operators to pick calibrated HDR presets with live settings sync."""

    preset_applied = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._settings_manager = get_settings_manager()
        self._facade = LightingSettingsFacade()
        self._event_bus: SettingsEventBus = get_settings_event_bus()

        self._combo: QComboBox | None = None
        self._description_label: QLabel | None = None
        self._status_label: QLabel | None = None
        self._apply_button: QPushButton | None = None
        self._preset_by_id: dict[str, _PresetEntry] = {}
        self._active_preset: str = ""
        self._custom_label = self.tr("Пользовательская настройка")

        self._build_ui()
        self._load_presets()
        self._event_bus.settingChanged.connect(self._on_settings_event)
        self._event_bus.settingsBatchUpdated.connect(self._on_settings_event)

        current_effects = self._settings_manager.get("current.graphics.effects", {})
        self.sync_with_effects(current_effects)

    # ------------------------------------------------------------------ UI setup
    def _build_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        title = QLabel(self.tr("HDR пресеты"), self)
        title.setStyleSheet("font-weight: 600;")
        layout.addWidget(title)

        selector_row = QHBoxLayout()
        selector_row.setContentsMargins(0, 0, 0, 0)
        selector_row.setSpacing(8)

        combo = QComboBox(self)
        combo.currentIndexChanged.connect(self._on_selection_changed)
        selector_row.addWidget(combo, 1)
        self._combo = combo

        apply_btn = QPushButton(self.tr("Применить"), self)
        apply_btn.clicked.connect(self._on_apply_clicked)
        selector_row.addWidget(apply_btn)
        self._apply_button = apply_btn

        layout.addLayout(selector_row)

        description = QLabel("", self)
        description.setWordWrap(True)
        description.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        description.setStyleSheet("color: #6d737f;")
        layout.addWidget(description)
        self._description_label = description

        status = QLabel("", self)
        status.setWordWrap(True)
        status.setStyleSheet("color: #3a7a2a; font-size: 11px;")
        layout.addWidget(status)
        self._status_label = status

    # ----------------------------------------------------------------- data load
    def _load_presets(self) -> None:
        if self._combo is None:
            return
        self._combo.blockSignals(True)
        try:
            self._combo.clear()
            self._combo.addItem(self._custom_label, "")
            self._preset_by_id.clear()
            for preset in self._facade.iter_tonemap_presets():
                entry = _PresetEntry(
                    preset=preset,
                    label=self._format_label(preset),
                    description=self._format_description(preset),
                )
                self._preset_by_id[preset.id] = entry
                self._combo.addItem(entry.label, preset.id)
        finally:
            self._combo.blockSignals(False)
        self._update_description("")

    # ------------------------------------------------------------------ helpers
    def _format_label(self, preset: TonemapPreset) -> str:
        if "display_name" in preset.extras:
            return str(preset.extras["display_name"]).strip() or preset.id
        token = preset.label_key or preset.id
        return self._humanise_token(token)

    def _format_description(self, preset: TonemapPreset) -> str:
        segments: list[str] = []
        if preset.description_key:
            segments.append(self._humanise_token(preset.description_key))
        extras = [
            f"{self._humanise_token(key)} = {value}"
            for key, value in preset.extras.items()
            if key not in {"display_name"}
        ]
        if extras:
            segments.append(", ".join(extras))
        if not segments:
            return self.tr(
                "Настраивает экспозицию и белую точку под калиброванные значения."
            )
        return " — ".join(segments)

    def _humanise_token(self, token: str) -> str:
        fragment = token.split(".")[-1]
        text = fragment.replace("_", " ").strip()
        if not text:
            return token
        words = text.split()
        return " ".join(
            word.upper() if word.isupper() else word.capitalize() for word in words
        )

    def _build_preset_payload(self, preset: TonemapPreset) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "tonemap_mode": preset.mode,
            "tonemap_enabled": preset.tonemap_enabled,
            "tonemap_exposure": preset.exposure,
            "tonemap_white_point": preset.white_point,
        }
        for key, value in preset.extras.items():
            payload[key] = value
        return payload

    def _update_description(self, preset_id: str) -> None:
        if self._description_label is None:
            return
        if not preset_id:
            self._description_label.setText(
                self.tr(
                    "Пользовательские параметры активны; выберите пресет для восстановления эталона."
                )
            )
            return
        entry = self._preset_by_id.get(preset_id)
        if entry is None:
            self._description_label.setText("")
            return
        self._description_label.setText(entry.description)

    def _set_status(self, message: str) -> None:
        if self._status_label is None:
            return
        self._status_label.setText(message)

    def _set_selection(self, preset_id: str) -> None:
        if self._combo is None:
            return
        if preset_id == self._active_preset:
            return
        self._active_preset = preset_id
        self._combo.blockSignals(True)
        try:
            index = self._combo.findData(preset_id)
            if index < 0:
                index = 0
            self._combo.setCurrentIndex(index)
        finally:
            self._combo.blockSignals(False)
        self._update_description(preset_id)

    def _on_selection_changed(self, index: int) -> None:
        if self._combo is None:
            return
        preset_id = str(self._combo.itemData(index) or "")
        self._update_description(preset_id)
        self._set_status("")

    def _on_apply_clicked(self) -> None:
        if self._combo is None:
            return
        preset_id = str(self._combo.currentData() or "")
        if not preset_id:
            self._set_status(
                self.tr(
                    "Выберите один из пресетов, чтобы применить калиброванные значения."
                )
            )
            return
        entry = self._preset_by_id.get(preset_id)
        if entry is None:
            self._set_status(self.tr("Не удалось найти выбранный пресет."))
            return
        payload = self._build_preset_payload(entry.preset)
        self._facade.apply_tonemap_preset(preset_id, auto_save=False)
        self._set_selection(preset_id)
        self._set_status(self.tr("Пресет применён к текущим настройкам."))
        self.preset_applied.emit(payload)

    def _payload_targets_effects(self, payload: Mapping[str, Any]) -> bool:
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

    def _on_settings_event(self, payload: Mapping[str, Any]) -> None:
        if not self._payload_targets_effects(payload):
            return
        effects = self._settings_manager.get("current.graphics.effects", {})
        self.sync_with_effects(effects)

    # ----------------------------------------------------------------- public API
    def sync_with_effects(self, effects_state: Mapping[str, Any]) -> None:
        preset_id = ""
        for entry in self._preset_by_id.values():
            if entry.preset.matches(effects_state):
                preset_id = entry.preset.id
                break
        self._set_selection(preset_id)

    def get_parameters(self) -> dict[str, Any]:
        """Return the active preset and current effects snapshot."""

        effects = self._settings_manager.get("current.graphics.effects", {})
        if not isinstance(effects, Mapping):
            effects = {}

        selected_preset = ""
        if self._combo is not None:
            selected_preset = str(self._combo.currentData() or "")

        active_preset = (
            selected_preset
            or self._active_preset
            or self._facade.resolve_active_tonemap_preset()
            or ""
        )

        return {
            "active_preset": active_preset,
            "effects": dict(effects),
        }

    # ---------------------------------------------------------------- lifecycle
    def deleteLater(self) -> None:  # pragma: no cover - Qt lifecycle
        try:
            self._event_bus.settingChanged.disconnect(self._on_settings_event)
        except (RuntimeError, TypeError):
            pass
        try:
            self._event_bus.settingsBatchUpdated.disconnect(self._on_settings_event)
        except (RuntimeError, TypeError):
            pass
        super().deleteLater()
