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
from .defaults import (
    DEFAULT_PNEUMATIC,
    PRESSURE_DROP_LIMITS,
    PRESSURE_UNITS,
    RELIEF_PRESSURE_LIMITS,
    convert_pressure_value,
)
from .state_manager import PneumoStateManager


class PressuresTab(QWidget):
    """Configure pressure-related parameters."""

    parameter_changed = Signal(str, float)

    def __init__(self, state_manager: PneumoStateManager, parent=None):
        super().__init__(parent)
        self.state_manager = state_manager

        self._setup_ui()
        self.update_from_state()
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

        # Check valves
        cv_group = QGroupBox("Обратные клапаны")
        cv_layout = QHBoxLayout(cv_group)
        cv_layout.setSpacing(12)
        self.cv_atmo_dp_knob = Knob(
            minimum=PRESSURE_DROP_LIMITS["min"],
            maximum=PRESSURE_DROP_LIMITS["max"],
            value=self.state_manager.get_pressure_drop("cv_atmo_dp"),
            step=PRESSURE_DROP_LIMITS["step"],
            decimals=PRESSURE_DROP_LIMITS["decimals"],
            units=DEFAULT_PNEUMATIC["pressure_units"],
            title="ΔP Атм→Линия",
        )
        cv_layout.addWidget(self.cv_atmo_dp_knob)
        self.cv_tank_dp_knob = Knob(
            minimum=PRESSURE_DROP_LIMITS["min"],
            maximum=PRESSURE_DROP_LIMITS["max"],
            value=self.state_manager.get_pressure_drop("cv_tank_dp"),
            step=PRESSURE_DROP_LIMITS["step"],
            decimals=PRESSURE_DROP_LIMITS["decimals"],
            units=DEFAULT_PNEUMATIC["pressure_units"],
            title="ΔP Линия→Ресивер",
        )
        cv_layout.addWidget(self.cv_tank_dp_knob)
        layout.addWidget(cv_group)

        # Relief valves
        relief_group = QGroupBox("Предохранительные клапаны")
        relief_layout = QHBoxLayout(relief_group)
        relief_layout.setSpacing(12)
        self.relief_min_knob = Knob(
            minimum=RELIEF_PRESSURE_LIMITS["min"],
            maximum=RELIEF_PRESSURE_LIMITS["max"],
            value=self.state_manager.get_relief_pressure("relief_min_pressure"),
            step=RELIEF_PRESSURE_LIMITS["step"],
            decimals=RELIEF_PRESSURE_LIMITS["decimals"],
            units=DEFAULT_PNEUMATIC["pressure_units"],
            title="Мин. сброс",
        )
        relief_layout.addWidget(self.relief_min_knob)
        self.relief_stiff_knob = Knob(
            minimum=RELIEF_PRESSURE_LIMITS["min"],
            maximum=RELIEF_PRESSURE_LIMITS["max"],
            value=self.state_manager.get_relief_pressure("relief_stiff_pressure"),
            step=RELIEF_PRESSURE_LIMITS["step"],
            decimals=RELIEF_PRESSURE_LIMITS["decimals"],
            units=DEFAULT_PNEUMATIC["pressure_units"],
            title="Сброс жёсткости",
        )
        relief_layout.addWidget(self.relief_stiff_knob)
        self.relief_safety_knob = Knob(
            minimum=RELIEF_PRESSURE_LIMITS["min"],
            maximum=RELIEF_PRESSURE_LIMITS["max"],
            value=self.state_manager.get_relief_pressure("relief_safety_pressure"),
            step=RELIEF_PRESSURE_LIMITS["step"],
            decimals=RELIEF_PRESSURE_LIMITS["decimals"],
            units=DEFAULT_PNEUMATIC["pressure_units"],
            title="Аварийный сброс",
        )
        relief_layout.addWidget(self.relief_safety_knob)
        layout.addWidget(relief_group)

        self.hint_label = QLabel()
        self.hint_label.setWordWrap(True)
        self.hint_label.setStyleSheet("color: #c54632; font-size: 11px;")
        self.hint_label.setVisible(False)
        layout.addWidget(self.hint_label)

        layout.addStretch()

    def _load_from_state(self) -> None:
        current_units = self.state_manager.get_pressure_units()
        idx = max(0, self.units_combo.findData(current_units))
        self.units_combo.setCurrentIndex(idx)
        self._apply_units_to_knobs(current_units)
        self._update_hint_label()

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
        self._update_hint_label()

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
        if units:
            self.state_manager.set_pressure_units(str(units))
            self.update_from_state()

    def _on_pressure_drop_changed(self, name: str, value: float) -> None:
        self.state_manager.set_pressure_drop(name, value)
        self.parameter_changed.emit(name, self.state_manager.get_pressure_drop(name))
        self._update_hint_label()

    def _on_relief_changed(self, name: str, value: float) -> None:
        self.state_manager.set_relief_pressure(name, value)
        self.parameter_changed.emit(name, self.state_manager.get_relief_pressure(name))
        self._update_hint_label()

    def _apply_units_to_knobs(self, units: str) -> None:
        base_units = DEFAULT_PNEUMATIC["pressure_units"]

        def _convert_limits(limits: dict[str, float]) -> tuple[float, float, float]:
            minimum = convert_pressure_value(limits["min"], base_units, units)
            maximum = convert_pressure_value(limits["max"], base_units, units)
            step = convert_pressure_value(limits["step"], base_units, units)
            return minimum, maximum, step

        drop_min, drop_max, drop_step = _convert_limits(PRESSURE_DROP_LIMITS)
        self.cv_atmo_dp_knob.setRange(drop_min, drop_max, drop_step)
        self.cv_tank_dp_knob.setRange(drop_min, drop_max, drop_step)

        relief_min, relief_max, relief_step = _convert_limits(RELIEF_PRESSURE_LIMITS)
        self.relief_min_knob.setRange(relief_min, relief_max, relief_step)
        self.relief_stiff_knob.setRange(relief_min, relief_max, relief_step)
        self.relief_safety_knob.setRange(relief_min, relief_max, relief_step)

        for knob in (
            self.cv_atmo_dp_knob,
            self.cv_tank_dp_knob,
            self.relief_min_knob,
            self.relief_stiff_knob,
            self.relief_safety_knob,
        ):
            knob.setUnits(units)
        self._update_hint_label()

    def _update_hint_label(self) -> None:
        keys = (
            "cv_atmo_dp",
            "cv_tank_dp",
            "relief_min_pressure",
            "relief_stiff_pressure",
            "relief_safety_pressure",
        )
        hints: list[str] = []
        for key in keys:
            hint = self.state_manager.get_hint(key)
            if hint:
                hints.append(hint)
        if hints:
            message = "\n".join(dict.fromkeys(hints))
            self.hint_label.setText(message)
            self.hint_label.setVisible(True)
        else:
            self.hint_label.clear()
            self.hint_label.setVisible(False)
