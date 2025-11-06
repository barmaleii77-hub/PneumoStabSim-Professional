# -*- coding: utf-8 -*-
"""Thermal configuration tab."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QHBoxLayout,
    QRadioButton,
)
from PySide6.QtCore import Signal

from ...widgets import Knob
from .state_manager import PneumoStateManager
from .defaults import POLY_HEAT_TRANSFER_LIMITS, POLY_EXCHANGE_AREA_LIMITS


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
        self.polytropic_radio = QRadioButton("Политетропический")
        thermo_box.addWidget(self.isothermal_radio)
        thermo_box.addWidget(self.adiabatic_radio)
        thermo_box.addWidget(self.polytropic_radio)
        env_layout.addLayout(thermo_box)
        env_layout.addStretch()

        layout.addWidget(env_group)

        self.polytropic_group = QGroupBox("Параметры политетропики")
        poly_layout = QHBoxLayout(self.polytropic_group)
        poly_layout.setSpacing(12)
        self.polytropic_heat_knob = Knob(
            minimum=POLY_HEAT_TRANSFER_LIMITS["min"],
            maximum=POLY_HEAT_TRANSFER_LIMITS["max"],
            value=self.state_manager.get_polytropic_heat_transfer(),
            step=POLY_HEAT_TRANSFER_LIMITS["step"],
            decimals=POLY_HEAT_TRANSFER_LIMITS["decimals"],
            units="Вт/(м²·К)",
            title="Теплоотдача",
        )
        poly_layout.addWidget(self.polytropic_heat_knob)
        self.polytropic_area_knob = Knob(
            minimum=POLY_EXCHANGE_AREA_LIMITS["min"],
            maximum=POLY_EXCHANGE_AREA_LIMITS["max"],
            value=self.state_manager.get_polytropic_exchange_area(),
            step=POLY_EXCHANGE_AREA_LIMITS["step"],
            decimals=POLY_EXCHANGE_AREA_LIMITS["decimals"],
            units="м²",
            title="Площадь",
        )
        poly_layout.addWidget(self.polytropic_area_knob)
        layout.addWidget(self.polytropic_group)
        layout.addStretch()

    def _load_from_state(self) -> None:
        temp = self.state_manager.get_atmo_temp()
        self.atmo_temp_knob.setValue(temp)
        mode = self.state_manager.get_thermo_mode()
        self.isothermal_radio.setChecked(mode == "ISOTHERMAL")
        self.adiabatic_radio.setChecked(mode == "ADIABATIC")
        self.polytropic_radio.setChecked(mode == "POLYTROPIC")
        self.polytropic_heat_knob.setValue(
            self.state_manager.get_polytropic_heat_transfer()
        )
        self.polytropic_area_knob.setValue(
            self.state_manager.get_polytropic_exchange_area()
        )
        self.polytropic_group.setEnabled(self.polytropic_radio.isChecked())

    def update_from_state(self) -> None:
        self._load_from_state()

    def _connect_signals(self) -> None:
        self.atmo_temp_knob.valueChanged.connect(self._on_temp_changed)
        self.isothermal_radio.toggled.connect(self._on_mode_toggled)
        self.adiabatic_radio.toggled.connect(self._on_mode_toggled)
        self.polytropic_radio.toggled.connect(self._on_mode_toggled)
        self.polytropic_heat_knob.valueChanged.connect(self._on_polytropic_heat_changed)
        self.polytropic_area_knob.valueChanged.connect(self._on_polytropic_area_changed)

    def _on_temp_changed(self, value: float) -> None:
        self.state_manager.set_atmo_temp(value)
        self.parameter_changed.emit("atmo_temp", value)

    def _on_mode_toggled(self, checked: bool) -> None:
        self.polytropic_group.setEnabled(self.polytropic_radio.isChecked())
        if not checked:
            return
        if self.isothermal_radio.isChecked():
            mode = "ISOTHERMAL"
        elif self.adiabatic_radio.isChecked():
            mode = "ADIABATIC"
        else:
            mode = "POLYTROPIC"
        self.state_manager.set_thermo_mode(mode)
        self.mode_changed.emit("thermo_mode", mode)

    def _on_polytropic_heat_changed(self, value: float) -> None:
        self.state_manager.set_polytropic_heat_transfer(value)
        self.parameter_changed.emit(
            "polytropic_heat_transfer_coeff",
            self.state_manager.get_polytropic_heat_transfer(),
        )

    def _on_polytropic_area_changed(self, value: float) -> None:
        self.state_manager.set_polytropic_exchange_area(value)
        self.parameter_changed.emit(
            "polytropic_exchange_area",
            self.state_manager.get_polytropic_exchange_area(),
        )
