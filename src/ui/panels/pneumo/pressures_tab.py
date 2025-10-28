# -*- coding: utf-8 -*-
"""Pressure configuration tab."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QComboBox,
)
from PySide6.QtCore import Signal

from ...widgets import Knob
from .defaults import PRESSURE_UNITS
from .state_manager import PneumoStateManager


class PressuresTab(QWidget):
    """Configure pressure-related parameters."""

    parameter_changed = Signal(str, float)

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

        units_row = QHBoxLayout()
        units_row.addWidget(QLabel("Единицы давления:"))
        self.units_combo = QComboBox()
        for label, value in PRESSURE_UNITS:
            self.units_combo.addItem(label, userData=value)
        units_row.addWidget(self.units_combo, 1)
        layout.addLayout(units_row)

        current_units = self.state_manager.get_pressure_units()
        drop_limits = self.state_manager.get_pressure_drop_limits()
        relief_limits = self.state_manager.get_relief_pressure_limits()

        # Check valves
        cv_group = QGroupBox("Обратные клапаны")
        cv_layout = QHBoxLayout(cv_group)
        cv_layout.setSpacing(12)
        self.cv_atmo_dp_knob = Knob(
            minimum=drop_limits["min"],
            maximum=drop_limits["max"],
            value=self.state_manager.get_pressure_drop("cv_atmo_dp"),
            step=drop_limits["step"],
            decimals=drop_limits["decimals"],
            units=current_units,
            title="ΔP Атм→Линия",
        )
        cv_layout.addWidget(self.cv_atmo_dp_knob)
        self.cv_tank_dp_knob = Knob(
            minimum=drop_limits["min"],
            maximum=drop_limits["max"],
            value=self.state_manager.get_pressure_drop("cv_tank_dp"),
            step=drop_limits["step"],
            decimals=drop_limits["decimals"],
            units=current_units,
            title="ΔP Линия→Ресивер",
        )
        cv_layout.addWidget(self.cv_tank_dp_knob)
        layout.addWidget(cv_group)

        # Relief valves
        relief_group = QGroupBox("Предохранительные клапаны")
        relief_layout = QHBoxLayout(relief_group)
        relief_layout.setSpacing(12)
        self.relief_min_knob = Knob(
            minimum=relief_limits["min"],
            maximum=relief_limits["max"],
            value=self.state_manager.get_relief_pressure("relief_min_pressure"),
            step=relief_limits["step"],
            decimals=relief_limits["decimals"],
            units=current_units,
            title="Мин. сброс",
        )
        relief_layout.addWidget(self.relief_min_knob)
        self.relief_stiff_knob = Knob(
            minimum=relief_limits["min"],
            maximum=relief_limits["max"],
            value=self.state_manager.get_relief_pressure("relief_stiff_pressure"),
            step=relief_limits["step"],
            decimals=relief_limits["decimals"],
            units=current_units,
            title="Сброс жёсткости",
        )
        relief_layout.addWidget(self.relief_stiff_knob)
        self.relief_safety_knob = Knob(
            minimum=relief_limits["min"],
            maximum=relief_limits["max"],
            value=self.state_manager.get_relief_pressure("relief_safety_pressure"),
            step=relief_limits["step"],
            decimals=relief_limits["decimals"],
            units=current_units,
            title="Аварийный сброс",
        )
        relief_layout.addWidget(self.relief_safety_knob)
        layout.addWidget(relief_group)

        layout.addStretch()

    def _load_from_state(self) -> None:
        current_units = self.state_manager.get_pressure_units()
        idx = max(0, self.units_combo.findData(current_units))
        self.units_combo.blockSignals(True)
        self.units_combo.setCurrentIndex(idx)
        self.units_combo.blockSignals(False)
        self._reconfigure_knobs_for_units(current_units)

    def update_from_state(self) -> None:
        self._load_from_state()
        self.cv_atmo_dp_knob.setValue(
            self.state_manager.get_pressure_drop("cv_atmo_dp")
        )
        self.cv_tank_dp_knob.setValue(
            self.state_manager.get_pressure_drop("cv_tank_dp")
        )
        self.relief_min_knob.setValue(
            self.state_manager.get_relief_pressure("relief_min_pressure")
        )
        self.relief_stiff_knob.setValue(
            self.state_manager.get_relief_pressure("relief_stiff_pressure")
        )
        self.relief_safety_knob.setValue(
            self.state_manager.get_relief_pressure("relief_safety_pressure")
        )

    def _connect_signals(self) -> None:
        self.units_combo.currentIndexChanged.connect(self._on_units_changed)
        self.cv_atmo_dp_knob.valueChanged.connect(
            lambda value: self._on_pressure_drop_changed("cv_atmo_dp", value)
        )
        self.cv_tank_dp_knob.valueChanged.connect(
            lambda value: self._on_pressure_drop_changed("cv_tank_dp", value)
        )
        self.relief_min_knob.valueChanged.connect(
            lambda value: self._on_relief_changed("relief_min_pressure", value)
        )
        self.relief_stiff_knob.valueChanged.connect(
            lambda value: self._on_relief_changed("relief_stiff_pressure", value)
        )
        self.relief_safety_knob.valueChanged.connect(
            lambda value: self._on_relief_changed("relief_safety_pressure", value)
        )

    def _on_units_changed(self, index: int) -> None:
        units = self.units_combo.itemData(index)
        if not units:
            return

        units = str(units)
        if units == self.state_manager.get_pressure_units():
            return

        self.state_manager.set_pressure_units(units)
        self._reconfigure_knobs_for_units(units)
        self.update_from_state()

    def _on_pressure_drop_changed(self, name: str, value: float) -> None:
        self.state_manager.set_pressure_drop(name, value)
        self.parameter_changed.emit(name, self.state_manager.get_pressure_drop(name))

    def _on_relief_changed(self, name: str, value: float) -> None:
        self.state_manager.set_relief_pressure(name, value)
        self.parameter_changed.emit(name, self.state_manager.get_relief_pressure(name))

    def _reconfigure_knobs_for_units(self, units: str) -> None:
        drop_limits = self.state_manager.get_pressure_drop_limits()
        relief_limits = self.state_manager.get_relief_pressure_limits()

        for knob in (self.cv_atmo_dp_knob, self.cv_tank_dp_knob):
            knob.setUnits(units)
            knob.setRange(drop_limits["min"], drop_limits["max"], drop_limits["step"])
            knob.setDecimals(drop_limits["decimals"])

        for knob in (
            self.relief_min_knob,
            self.relief_stiff_knob,
            self.relief_safety_knob,
        ):
            knob.setUnits(units)
            knob.setRange(
                relief_limits["min"], relief_limits["max"], relief_limits["step"]
            )
            knob.setDecimals(relief_limits["decimals"])
