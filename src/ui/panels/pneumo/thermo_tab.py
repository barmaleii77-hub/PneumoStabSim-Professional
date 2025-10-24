# -*- coding: utf-8 -*-
"""Thermal configuration tab."""

from __future__ import annotations

from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QHBoxLayout, QRadioButton
from PySide6.QtCore import Signal

from ...widgets import Knob
from .state_manager import PneumoStateManager


class ThermoTab(QWidget):
    """Configure thermal mode and environment temperature."""

    parameter_changed = Signal(str, float)
    mode_changed = Signal(str, str)

    def __init__(self, state_manager: PneumoStateManager, parent=None):
        super().__init__(parent)
        self.state_manager = state_manager

        self._setup_ui()
        self._load_from_state()
        self._connect_signals()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # Environment
        env_group = QGroupBox("Окружающая среда")
        env_layout = QHBoxLayout(env_group)
        env_layout.setSpacing(12)
        self.atmo_temp_knob = Knob(
            minimum=-40.0,
            maximum=80.0,
            value=self.state_manager.get_atmo_temp(),
            step=1.0,
            decimals=0,
            units="°C",
            title="Температура",
        )
        env_layout.addWidget(self.atmo_temp_knob)

        thermo_box = QVBoxLayout()
        self.isothermal_radio = QRadioButton("Изотермический")
        self.adiabatic_radio = QRadioButton("Адиабатический")
        thermo_box.addWidget(self.isothermal_radio)
        thermo_box.addWidget(self.adiabatic_radio)
        env_layout.addLayout(thermo_box)
        env_layout.addStretch()

        layout.addWidget(env_group)
        layout.addStretch()

    def _load_from_state(self) -> None:
        temp = self.state_manager.get_atmo_temp()
        self.atmo_temp_knob.setValue(temp)
        mode = self.state_manager.get_thermo_mode()
        self.isothermal_radio.setChecked(mode == "ISOTHERMAL")
        self.adiabatic_radio.setChecked(mode == "ADIABATIC")

    def update_from_state(self) -> None:
        self._load_from_state()

    def _connect_signals(self) -> None:
        self.atmo_temp_knob.valueChanged.connect(self._on_temp_changed)
        self.isothermal_radio.toggled.connect(self._on_mode_toggled)
        self.adiabatic_radio.toggled.connect(self._on_mode_toggled)

    def _on_temp_changed(self, value: float) -> None:
        self.state_manager.set_atmo_temp(value)
        self.parameter_changed.emit("atmo_temp", value)

    def _on_mode_toggled(self, checked: bool) -> None:
        if not checked:
            return
        mode = "ISOTHERMAL" if self.isothermal_radio.isChecked() else "ADIABATIC"
        self.state_manager.set_thermo_mode(mode)
        self.mode_changed.emit("thermo_mode", mode)
