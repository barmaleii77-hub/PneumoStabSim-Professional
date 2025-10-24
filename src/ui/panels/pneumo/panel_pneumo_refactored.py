# -*- coding: utf-8 -*-
"""Refactored pneumatic panel coordinator."""

from __future__ import annotations

import logging
from typing import Any, Dict

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

        layout.addWidget(self.tab_widget)

        buttons_row = QHBoxLayout()
        self.reset_button = QPushButton("↩︎ Сбросить (defaults)")
        self.save_defaults_button = QPushButton("💾 Сохранить как дефолт")
        self.validate_button = QPushButton("Проверить")
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
        snapshot = self.state_manager.get_state()
        self.pneumatic_updated.emit(snapshot)

    def _on_parameter_changed(self, name: str, value: float) -> None:
        LOGGER.debug("Parameter changed: %s=%s", name, value)
        self.parameter_changed.emit(name, float(value))
        self._emit_state_update()

    def _on_mode_changed(self, name: str, mode: str) -> None:
        LOGGER.debug("Mode changed: %s=%s", name, mode)
        self.mode_changed.emit(name, mode)
        self._emit_state_update()

    def _on_option_changed(self, name: str, value: bool) -> None:
        self.state_manager.set_option(name, value)
        LOGGER.debug("Option changed: %s=%s", name, value)
        self.mode_changed.emit(name, str(value))
        self._emit_state_update()

    def _on_receiver_volume_changed(self, volume: float, mode: str) -> None:
        LOGGER.debug("Receiver volume changed: %s (%s)", volume, mode)
        self.receiver_volume_changed.emit(volume, mode)
        self._emit_state_update()

    def _on_reset_clicked(self) -> None:
        self.state_manager.reset_to_defaults()
        self._refresh_tabs()
        self.state_manager.save_state()
        self._emit_state_update()

    def _on_save_defaults_clicked(self) -> None:
        self.state_manager.save_current_as_defaults()
        QMessageBox.information(
            self,
            "Сохранение",
            "Текущие параметры сохранены как defaults_snapshot",
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

    def collect_state(self) -> Dict[str, Any]:
        """Return a copy of the current pneumatic parameters."""

        return self.state_manager.get_state()

    def reset_to_defaults(self) -> None:
        """Public helper mirroring button action."""

        self._on_reset_clicked()

    def save_state(self) -> None:
        """Persist current parameters via the settings manager."""

        self.state_manager.save_state()
