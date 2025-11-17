"""Refactored pneumatic panel coordinator."""

from __future__ import annotations

import logging
from typing import Any
from collections.abc import Mapping

from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QTabWidget,
    QHBoxLayout,
    QPushButton,
    QMessageBox,
    QSizePolicy,
)
from PySide6.QtGui import QFont

from .state_manager import PneumoStateManager
from .thermo_tab import ThermoTab
from .pressures_tab import PressuresTab
from .valves_tab import ValvesTab
from .receiver_tab import ReceiverTab
from src.core.history import HistoryStack
from src.core.settings_sync_controller import SettingsSyncController
from src.ui.panels.preset_manager import PanelPresetManager

LOGGER = logging.getLogger(__name__)


class PneumoPanel(QWidget):
    """Thin coordinator delegating to modular tabs."""

    parameter_changed = Signal(str, float)
    mode_changed = Signal(str, str)
    pneumatic_updated = Signal(dict)
    receiver_volume_changed = Signal(float, str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        LOGGER.info("PneumoPanel (refactored) initializing...")

        self.state_manager = PneumoStateManager()
        self._history = HistoryStack()
        self._sync_controller = SettingsSyncController(
            initial_state=self.state_manager.get_state(), history=self._history
        )
        self._sync_controller.register_listener(self._on_state_synced)
        self.preset_manager = PanelPresetManager("pneumo", self._sync_controller)
        self._sync_guard = 0
        self._external_update_depth = 0
        self._setup_ui()
        self._connect_signals()

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        QTimer.singleShot(200, self._emit_initial_state)
        LOGGER.info("PneumoPanel initialized")

    # ------------------------------------------------------------------ setup
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        title = QLabel("Пневматическая система")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        title.setFont(font)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.tab_widget = QTabWidget()
        self.thermo_tab = ThermoTab(self.state_manager, self)
        self.pressures_tab = PressuresTab(self.state_manager, self)
        self.valves_tab = ValvesTab(self.state_manager, self)
        self.receiver_tab = ReceiverTab(self.state_manager, self)

        self.tab_widget.addTab(self.thermo_tab, "Термо")
        self.tab_widget.addTab(self.pressures_tab, "Давление")
        self.tab_widget.addTab(self.valves_tab, "Клапаны")
        self.tab_widget.addTab(self.receiver_tab, "Ресивер")

        tab_tip = self.preset_manager.get_tooltip(
            "tab_widget", "Выберите раздел для настройки пневмосистемы"
        )
        if tab_tip:
            self.tab_widget.setToolTip(tab_tip)

        layout.addWidget(self.tab_widget)

        buttons_row = QHBoxLayout()
        self.reset_button = QPushButton("↩︎ Сбросить (defaults)")
        reset_tip = self.preset_manager.get_tooltip(
            "reset_button", "Сбросить параметры пневмосистемы"
        )
        if reset_tip:
            self.reset_button.setToolTip(reset_tip)
        self.save_defaults_button = QPushButton("💾 Сохранить как дефолт")
        save_tip = self.preset_manager.get_tooltip(
            "save_defaults_button", "Сохранить текущие параметры как дефолты"
        )
        if save_tip:
            self.save_defaults_button.setToolTip(save_tip)
        self.validate_button = QPushButton("Проверить")
        validate_tip = self.preset_manager.get_tooltip(
            "validate_button", "Проверить корректность настроек"
        )
        if validate_tip:
            self.validate_button.setToolTip(validate_tip)
        buttons_row.addWidget(self.reset_button)
        buttons_row.addWidget(self.save_defaults_button)
        buttons_row.addWidget(self.validate_button)
        buttons_row.addStretch()
        layout.addLayout(buttons_row)
        layout.addStretch()

    # ----------------------------------------------------------------- signals
    def _connect_signals(self) -> None:
        self.thermo_tab.parameter_changed.connect(self._on_parameter_changed)
        self.thermo_tab.mode_changed.connect(self._on_mode_changed)

        self.pressures_tab.parameter_changed.connect(self._on_parameter_changed)

        self.valves_tab.parameter_changed.connect(self._on_parameter_changed)
        self.valves_tab.option_changed.connect(self._on_option_changed)

        self.receiver_tab.parameter_changed.connect(self._on_parameter_changed)
        self.receiver_tab.mode_changed.connect(self._on_mode_changed)
        self.receiver_tab.receiver_volume_changed.connect(
            self._on_receiver_volume_changed
        )

        self.reset_button.clicked.connect(self._on_reset_clicked)
        self.save_defaults_button.clicked.connect(self._on_save_defaults_clicked)
        self.validate_button.clicked.connect(self._on_validate_clicked)

    # ---------------------------------------------------------------- handlers
    def _emit_initial_state(self) -> None:
        self._emit_state_update()

    def _emit_state_update(self) -> None:
        if self._external_update_depth:
            return
        snapshot = self.state_manager.get_state()
        self.pneumatic_updated.emit(snapshot)

    def _on_parameter_changed(self, name: str, value: float) -> None:
        if self._external_update_depth:
            return
        LOGGER.debug("Parameter changed: %s=%s", name, value)
        self.parameter_changed.emit(name, float(value))
        self._emit_state_update()
        self._apply_sync_patch(
            {name: self.state_manager.get_state().get(name, value)},
            description=f"Update pneumatic parameter {name}",
        )

    def _on_mode_changed(self, name: str, mode: str) -> None:
        if self._external_update_depth:
            return
        LOGGER.debug("Mode changed: %s=%s", name, mode)
        self.mode_changed.emit(name, mode)
        self._emit_state_update()
        self._apply_sync_patch(
            {name: self.state_manager.get_state().get(name, mode)},
            description=f"Update pneumatic mode {name}",
        )

    def _on_option_changed(self, name: str, value: bool) -> None:
        if self._external_update_depth:
            return
        self.state_manager.set_option(name, value)
        LOGGER.debug("Option changed: %s=%s", name, value)
        self.mode_changed.emit(name, str(value))
        self._emit_state_update()
        self._apply_sync_patch(
            {name: self.state_manager.get_state().get(name, value)},
            description=f"Update pneumatic option {name}",
        )

    def _on_receiver_volume_changed(self, volume: float, mode: str) -> None:
        if self._external_update_depth:
            return
        LOGGER.debug("Receiver volume changed: %s (%s)", volume, mode)
        self.receiver_volume_changed.emit(volume, mode)
        self._emit_state_update()
        self._apply_sync_patch(
            {
                "receiver_volume": self.state_manager.get_state().get(
                    "receiver_volume", volume
                ),
                "volume_mode": mode,
            },
            description="Update pneumatic receiver",
        )

    def _on_reset_clicked(self) -> None:
        self.state_manager.reset_to_defaults()
        self._refresh_tabs()
        self.state_manager.save_state()
        self._emit_state_update()
        self._apply_sync_state(
            self.state_manager.get_state(),
            description="Reset pneumatic defaults",
            origin="preset",
        )

    def _on_save_defaults_clicked(self) -> None:
        self.state_manager.save_current_as_defaults()
        QMessageBox.information(
            self,
            "Сохранение",
            "Текущие параметры сохранены как дефолтные",
        )
        self._apply_sync_state(
            self.state_manager.get_state(),
            description="Save pneumatic defaults",
            origin="preset",
            metadata={"force_refresh": True},
        )

    def _on_validate_clicked(self) -> None:
        errors, warnings = self.state_manager.validate_pneumatic()
        if errors:
            QMessageBox.critical(self, "Ошибки пневмосистемы", "\n".join(errors))
        elif warnings:
            QMessageBox.warning(
                self, "Предупреждения пневмосистемы", "\n".join(warnings)
            )
        else:
            QMessageBox.information(
                self, "Проверка пневмосистемы", "Все параметры пневмосистемы корректны."
            )

    def _refresh_tabs(self) -> None:
        self.thermo_tab.update_from_state()
        self.pressures_tab.update_from_state()
        self.valves_tab.update_from_state()
        self.receiver_tab.update_from_state()

    def collect_state(self) -> dict[str, Any]:
        """Return parameters converted to storage (SI) units."""

        return self.state_manager.export_storage_payload()

    def get_parameters(self) -> dict[str, Any]:
        """Return the current pneumatic state in UI units."""

        return self.state_manager.get_state()

    def get_state(self) -> dict[str, Any]:
        return self._sync_controller.snapshot()

    def reset_to_defaults(self) -> None:
        """Public helper mirroring button action."""

        self._on_reset_clicked()

    def save_state(self) -> None:
        """Persist current parameters via the settings manager."""

        self.state_manager.save_state()

    def undo_last_change(self) -> bool:
        return self._sync_controller.undo() is not None

    def redo_last_change(self) -> bool:
        return self._sync_controller.redo() is not None

    def apply_registered_preset(self, preset_id: str) -> bool:
        return self.preset_manager.apply_registered_preset(preset_id) is not None

    # ----------------------------------------------------------------- syncing
    def set_parameters(
        self, updates: Mapping[str, Any], *, source: str = "external"
    ) -> None:
        """Применить внешние обновления состояния панели.

        Args:
            updates: Mapping с изменяемыми параметрами (ключи payload из SignalsRouter)
            source: Метка источника (для истории / диагностики)
        """
        if not updates:
            return
        self._external_update_depth += 1  # предотвращаем каскад сигналов
        try:
            sm = self.state_manager
            mode_before = sm.get_volume_mode()
            volume_mode_update = updates.get("volume_mode")
            if isinstance(volume_mode_update, str) and volume_mode_update:
                sm.set_volume_mode(volume_mode_update.upper())
            # Геометрия ресивера
            diameter_pending = updates.get("receiver_diameter")
            length_pending = updates.get("receiver_length")
            manual_volume_pending = updates.get("receiver_volume")

            if diameter_pending is not None:
                try:
                    sm.set_receiver_diameter(float(diameter_pending))
                except (TypeError, ValueError):
                    pass
            if length_pending is not None:
                try:
                    sm.set_receiver_length(float(length_pending))
                except (TypeError, ValueError):
                    pass

            if manual_volume_pending is not None and sm.get_volume_mode() == "MANUAL":
                try:
                    sm.set_manual_volume(float(manual_volume_pending))
                except (TypeError, ValueError):
                    pass
            if sm.get_volume_mode() == "GEOMETRIC":
                sm.refresh_geometric_volume()

            # Прочие параметры
            for key, value in updates.items():
                if key in {
                    "volume_mode",
                    "receiver_diameter",
                    "receiver_length",
                    "receiver_volume",
                }:
                    continue
                if isinstance(value, bool):
                    try:
                        sm.set_option(key, bool(value))
                    except AttributeError:
                        sm.set_parameter(key, bool(value))
                    continue
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    sm.set_parameter(key, float(value))

            # Синхронизация UI (только затронутых элементов)
            mode_after = sm.get_volume_mode()
            knob_block = (
                self.receiver_tab.manual_volume_knob,
                self.receiver_tab.receiver_diameter_knob,
                self.receiver_tab.receiver_length_knob,
            )
            for knob in knob_block:
                knob.blockSignals(True)
            try:
                if mode_after != mode_before or volume_mode_update is not None:
                    # Комбо режимов
                    self.receiver_tab.volume_mode_combo.setCurrentIndex(
                        0 if mode_after == "MANUAL" else 1
                    )
                    self.receiver_tab._apply_mode_visibility(mode_after)
                if diameter_pending is not None:
                    self.receiver_tab.receiver_diameter_knob.setValue(
                        sm.get_receiver_diameter()
                    )
                if length_pending is not None:
                    self.receiver_tab.receiver_length_knob.setValue(
                        sm.get_receiver_length()
                    )
                if (
                    manual_volume_pending is not None
                    and sm.get_volume_mode() == "MANUAL"
                ):
                    self.receiver_tab.manual_volume_knob.setValue(
                        sm.get_manual_volume()
                    )
            finally:
                for knob in knob_block:
                    knob.blockSignals(False)
            # Обновляем расчётный объём отображения при геометрическом режиме
            if sm.get_volume_mode() == "GEOMETRIC":
                self.receiver_tab._update_calculated_volume()

            # Эмиссия сигналов (минимально необходимая)
            if mode_after != mode_before:
                self.mode_changed.emit("volume_mode", mode_after)
            if diameter_pending is not None:
                self.parameter_changed.emit(
                    "receiver_diameter", sm.get_receiver_diameter()
                )
            if length_pending is not None:
                self.parameter_changed.emit("receiver_length", sm.get_receiver_length())
            # Всегда эмитим итоговый объём для согласованности тестов
            self.parameter_changed.emit(
                "receiver_volume",
                sm.get_manual_volume()
                if sm.get_volume_mode() == "MANUAL"
                else sm.get_parameter("receiver_volume"),
            )
            self.receiver_volume_changed.emit(
                sm.get_parameter("receiver_volume"), sm.get_volume_mode()
            )

            for key, value in updates.items():
                if key in {
                    "volume_mode",
                    "receiver_diameter",
                    "receiver_length",
                    "receiver_volume",
                }:
                    continue
                if isinstance(value, (int, float)) and not isinstance(value, bool):
                    self.parameter_changed.emit(key, float(sm.get_parameter(key)))
                elif isinstance(value, bool):
                    self.mode_changed.emit(key, str(bool(sm.get_parameter(key))))

            self._emit_state_update()
            self._apply_sync_patch(
                {k: sm.get_parameter(k) for k in updates.keys()},
                description=f"External pneumatic patch ({source})",
            )
        finally:
            self._external_update_depth -= 1

    def _apply_sync_patch(
        self,
        patch: Mapping[str, Any],
        *,
        description: str,
        origin: str = "local",
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        if self._sync_guard:
            return
        meta = {"panel": "pneumo"}
        if metadata:
            meta.update(dict(metadata))
        self._sync_controller.apply_patch(
            dict(patch),
            description=description,
            origin=origin,
            metadata=meta,
        )

    def _apply_sync_state(
        self,
        state: Mapping[str, Any],
        *,
        description: str,
        origin: str = "external",
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        if self._sync_guard:
            return
        meta = {"panel": "pneumo"}
        if metadata:
            meta.update(dict(metadata))
        self._sync_controller.apply_state(
            dict(state),
            description=description,
            origin=origin,
            metadata=meta,
        )

    def _on_state_synced(
        self, state: Mapping[str, Any], context: Mapping[str, Any]
    ) -> None:
        origin = str(context.get("origin", ""))
        if origin == "local" and not context.get("force_refresh"):
            return

        self._sync_guard += 1
        self._external_update_depth += 1
        try:
            self.state_manager.update_from(dict(state))
            self._refresh_tabs()
        finally:
            self._external_update_depth = max(0, self._external_update_depth - 1)
            self._sync_guard -= 1

        self._emit_state_update()
