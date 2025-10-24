# -*- coding: utf-8 -*-
"""Valve configuration tab."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QCheckBox,
)
from PySide6.QtCore import Signal

from ...widgets import Knob
from .defaults import THROTTLE_DIAMETER_LIMITS, VALVE_DIAMETER_LIMITS
from .state_manager import PneumoStateManager


class ValvesTab(QWidget):
    """Configure valve diameters and system options."""

    parameter_changed = Signal(str, float)
    option_changed = Signal(str, bool)

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

        # Valve diameters
        valve_group = QGroupBox("Обратные клапаны")
        valve_layout = QHBoxLayout(valve_group)
        valve_layout.setSpacing(12)
        self.cv_atmo_dia_knob = Knob(
            minimum=VALVE_DIAMETER_LIMITS["min"],
            maximum=VALVE_DIAMETER_LIMITS["max"],
            value=self.state_manager.get_valve_diameter("cv_atmo_dia"),
            step=VALVE_DIAMETER_LIMITS["step"],
            decimals=VALVE_DIAMETER_LIMITS["decimals"],
            units="мм",
            title="Диаметр (Атм)",
        )
        valve_layout.addWidget(self.cv_atmo_dia_knob)
        self.cv_tank_dia_knob = Knob(
            minimum=VALVE_DIAMETER_LIMITS["min"],
            maximum=VALVE_DIAMETER_LIMITS["max"],
            value=self.state_manager.get_valve_diameter("cv_tank_dia"),
            step=VALVE_DIAMETER_LIMITS["step"],
            decimals=VALVE_DIAMETER_LIMITS["decimals"],
            units="мм",
            title="Диаметр (Ресивер)",
        )
        valve_layout.addWidget(self.cv_tank_dia_knob)
        layout.addWidget(valve_group)

        # Throttle diameters
        throttle_group = QGroupBox("Дроссели")
        throttle_layout = QHBoxLayout(throttle_group)
        throttle_layout.setSpacing(12)
        self.throttle_min_knob = Knob(
            minimum=THROTTLE_DIAMETER_LIMITS["min"],
            maximum=THROTTLE_DIAMETER_LIMITS["max"],
            value=self.state_manager.get_valve_diameter("throttle_min_dia"),
            step=THROTTLE_DIAMETER_LIMITS["step"],
            decimals=THROTTLE_DIAMETER_LIMITS["decimals"],
            units="мм",
            title="Мин. дроссель",
        )
        throttle_layout.addWidget(self.throttle_min_knob)
        self.throttle_stiff_knob = Knob(
            minimum=THROTTLE_DIAMETER_LIMITS["min"],
            maximum=THROTTLE_DIAMETER_LIMITS["max"],
            value=self.state_manager.get_valve_diameter("throttle_stiff_dia"),
            step=THROTTLE_DIAMETER_LIMITS["step"],
            decimals=THROTTLE_DIAMETER_LIMITS["decimals"],
            units="мм",
            title="Дроссель жёстк.",
        )
        throttle_layout.addWidget(self.throttle_stiff_knob)
        layout.addWidget(throttle_group)

        # Options
        options_group = QGroupBox("Системные опции")
        options_layout = QVBoxLayout(options_group)
        options_layout.setSpacing(4)
        self.master_isolation_check = QCheckBox("Главная изоляция открыта")
        options_layout.addWidget(self.master_isolation_check)
        self.link_rod_dia_check = QCheckBox("Связать диаметры штоков")
        options_layout.addWidget(self.link_rod_dia_check)
        layout.addWidget(options_group)

        layout.addStretch()

    def _load_from_state(self) -> None:
        self.master_isolation_check.setChecked(
            self.state_manager.get_option("master_isolation_open")
        )
        self.link_rod_dia_check.setChecked(
            self.state_manager.get_option("link_rod_dia")
        )

    def update_from_state(self) -> None:
        self._load_from_state()
        self.cv_atmo_dia_knob.setValue(
            self.state_manager.get_valve_diameter("cv_atmo_dia")
        )
        self.cv_tank_dia_knob.setValue(
            self.state_manager.get_valve_diameter("cv_tank_dia")
        )
        self.throttle_min_knob.setValue(
            self.state_manager.get_valve_diameter("throttle_min_dia")
        )
        self.throttle_stiff_knob.setValue(
            self.state_manager.get_valve_diameter("throttle_stiff_dia")
        )

    def _connect_signals(self) -> None:
        self.cv_atmo_dia_knob.valueChanged.connect(
            lambda value: self._on_valve_changed("cv_atmo_dia", value)
        )
        self.cv_tank_dia_knob.valueChanged.connect(
            lambda value: self._on_valve_changed("cv_tank_dia", value)
        )
        self.throttle_min_knob.valueChanged.connect(
            lambda value: self._on_throttle_changed("throttle_min_dia", value)
        )
        self.throttle_stiff_knob.valueChanged.connect(
            lambda value: self._on_throttle_changed("throttle_stiff_dia", value)
        )
        self.master_isolation_check.toggled.connect(
            lambda checked: self._on_option_changed("master_isolation_open", checked)
        )
        self.link_rod_dia_check.toggled.connect(
            lambda checked: self._on_option_changed("link_rod_dia", checked)
        )

    def _on_valve_changed(self, name: str, value: float) -> None:
        self.state_manager.set_valve_diameter(name, value)
        self.parameter_changed.emit(name, self.state_manager.get_valve_diameter(name))

    def _on_throttle_changed(self, name: str, value: float) -> None:
        self.state_manager.set_throttle_diameter(name, value)
        self.parameter_changed.emit(name, self.state_manager.get_valve_diameter(name))

    def _on_option_changed(self, name: str, value: bool) -> None:
        self.state_manager.set_option(name, value)
        self.option_changed.emit(name, value)
