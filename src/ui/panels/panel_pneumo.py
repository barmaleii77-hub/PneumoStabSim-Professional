# -*- coding: utf-8 -*-
"""
Pneumatic system configuration panel - РУССКИЙ ИНТЕРФЕЙС
Полная интеграция с SettingsManager без дефолтов в коде.
Чтение при запуске, запись при выходе (централизованно в MainWindow).
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox,
    QRadioButton, QCheckBox, QPushButton, QLabel,
    QButtonGroup, QSizePolicy, QComboBox, QMessageBox
)
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QFont

from ..widgets import Knob
from src.common.settings_manager import get_settings_manager


class PneumoPanel(QWidget):
    """Панель конфигурации пневматической системы"""

    parameter_changed = Signal(str, float)
    mode_changed = Signal(str, str)
    pneumatic_updated = Signal(dict)
    receiver_volume_changed = Signal(float, str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._settings_manager = get_settings_manager()
        self.parameters: dict[str, float | bool | str] = {}

        # Сначала загрузим состояние, затем строим UI без хардкода значений
        self._load_from_settings()
        self._setup_ui()
        self._connect_signals()

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        title_label = QLabel("Пневматическая система")
        title_font = QFont(); title_font.setPointSize(12); title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Units selector
        units_layout = QHBoxLayout()
        units_layout.addWidget(QLabel("Единицы давления:"))
        self.pressure_units_combo = QComboBox()
        self.pressure_units_combo.addItems(["бар (bar)", "Па (Pa)", "кПа (kPa)", "МПа (MPa)"])
        # Индекс из параметров (если есть)
        units_index = {"бар": 0, "Па": 1, "кПа": 2, "МПа": 3}.get(str(self.parameters.get('pressure_units', 'бар')).split()[0], 0)
        self.pressure_units_combo.setCurrentIndex(units_index)
        self.pressure_units_combo.currentIndexChanged.connect(self._on_pressure_units_changed)
        units_layout.addWidget(self.pressure_units_combo, 1)
        layout.addLayout(units_layout)

        layout.addWidget(self._create_receiver_group())
        layout.addWidget(self._create_check_valves_group())
        layout.addWidget(self._create_relief_valves_group())
        layout.addWidget(self._create_environment_group())
        layout.addWidget(self._create_options_group())

        # Controls
        buttons_layout = QHBoxLayout()
        self.reset_button = QPushButton("↩︎ Сбросить (defaults)")
        self.reset_button.clicked.connect(self._reset_to_defaults)
        buttons_layout.addWidget(self.reset_button)

        self.save_defaults_button = QPushButton("💾 Сохранить как дефолт")
        self.save_defaults_button.clicked.connect(self._save_current_as_defaults)
        buttons_layout.addWidget(self.save_defaults_button)

        self.validate_button = QPushButton("Проверить")
        self.validate_button.clicked.connect(self._validate_system)
        buttons_layout.addWidget(self.validate_button)

        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        layout.addStretch()

    def _load_from_settings(self) -> None:
        data = self._settings_manager.get_category("pneumatic") or {}
        self.parameters.update(data)

    # --- Connections ---
    def _connect_knob(self, knob: Knob, handler):
        """Безопасно подключить сигнал ручки (valueEdited или valueChanged)."""
        if hasattr(knob, "valueEdited"):
            try:
                knob.valueEdited.connect(handler)  # type: ignore[attr-defined]
                return
            except Exception:
                pass
        if hasattr(knob, "valueChanged"):
            try:
                knob.valueChanged.connect(handler)  # type: ignore[attr-defined]
            except Exception:
                pass

    def _connect_signals(self) -> None:
        # Receiver volume
        self._connect_knob(self.manual_volume_knob, self._on_manual_volume_changed)
        # Geometry-based receiver volume
        self._connect_knob(self.receiver_diameter_knob, lambda _v: self._on_receiver_geometry_changed())
        self._connect_knob(self.receiver_length_knob, lambda _v: self._on_receiver_geometry_changed())

        # Check valves
        self._connect_knob(self.cv_atmo_dp_knob, lambda v: self._on_parameter_changed('cv_atmo_dp', float(v)))
        self._connect_knob(self.cv_tank_dp_knob, lambda v: self._on_parameter_changed('cv_tank_dp', float(v)))
        self._connect_knob(self.cv_atmo_dia_knob, lambda v: self._on_parameter_changed('cv_atmo_dia', float(v)))
        self._connect_knob(self.cv_tank_dia_knob, lambda v: self._on_parameter_changed('cv_tank_dia', float(v)))

        # Relief valves
        self._connect_knob(self.relief_min_pressure_knob, lambda v: self._on_parameter_changed('relief_min_pressure', float(v)))
        self._connect_knob(self.relief_stiff_pressure_knob, lambda v: self._on_parameter_changed('relief_stiff_pressure', float(v)))
        self._connect_knob(self.relief_safety_pressure_knob, lambda v: self._on_parameter_changed('relief_safety_pressure', float(v)))
        self._connect_knob(self.throttle_min_dia_knob, lambda v: self._on_parameter_changed('throttle_min_dia', float(v)))
        self._connect_knob(self.throttle_stiff_dia_knob, lambda v: self._on_parameter_changed('throttle_stiff_dia', float(v)))

        # Environment
        self._connect_knob(self.atmo_temp_knob, lambda v: self._on_parameter_changed('atmo_temp', float(v)))

        # Thermo mode
        try:
            self.isothermal_radio.toggled.connect(self._on_thermo_mode_changed)
            self.adiabatic_radio.toggled.connect(self._on_thermo_mode_changed)
        except Exception:
            pass

        # Options
        self.master_isolation_check.toggled.connect(lambda checked: self._on_parameter_changed('master_isolation_open', bool(checked)))
        self.link_rod_dia_check.toggled.connect(lambda checked: self._on_parameter_changed('link_rod_dia', bool(checked)))

    # --- UI helpers ---
    def _apply_volume_mode_widgets(self, mode: str) -> None:
        is_manual = (mode == 'MANUAL')
        self.manual_volume_widget.setVisible(is_manual)
        self.geometric_volume_widget.setVisible(not is_manual)
        self.calculated_volume_label.setVisible(not is_manual)

    def _create_receiver_group(self) -> QGroupBox:
        group = QGroupBox("Ресивер")
        layout = QVBoxLayout(group); layout.setSpacing(8)

        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Режим объёма:"))
        self.volume_mode_combo = QComboBox()
        self.volume_mode_combo.addItems(["Ручной объём", "Геометрический расчёт"])
        current_mode = str(self.parameters.get('volume_mode', 'MANUAL'))
        self.volume_mode_combo.setCurrentIndex(0 if current_mode == 'MANUAL' else 1)
        self.volume_mode_combo.currentIndexChanged.connect(self._on_volume_mode_changed)
        mode_layout.addWidget(self.volume_mode_combo, 1)
        layout.addLayout(mode_layout)

        self.manual_volume_widget = QWidget()
        manual_layout = QHBoxLayout(self.manual_volume_widget)
        manual_layout.setContentsMargins(0, 0, 0, 0); manual_layout.setSpacing(12)
        self.manual_volume_knob = Knob(minimum=0.001, maximum=0.100, value=float(self.parameters.get('receiver_volume', 0) or 0), step=0.001, decimals=3, units="м³", title="Объём ресивера")
        manual_layout.addWidget(self.manual_volume_knob)
        manual_layout.addStretch()
        layout.addWidget(self.manual_volume_widget)

        self.geometric_volume_widget = QWidget()
        geometric_layout = QHBoxLayout(self.geometric_volume_widget)
        geometric_layout.setContentsMargins(0, 0, 0, 0); geometric_layout.setSpacing(12)
        self.receiver_diameter_knob = Knob(minimum=0.050, maximum=0.500, value=float(self.parameters.get('receiver_diameter', 0) or 0), step=0.001, decimals=3, units="м", title="Диаметр ресивера")
        geometric_layout.addWidget(self.receiver_diameter_knob)
        self.receiver_length_knob = Knob(minimum=0.100, maximum=2.000, value=float(self.parameters.get('receiver_length', 0) or 0), step=0.001, decimals=3, units="м", title="Длина ресивера")
        geometric_layout.addWidget(self.receiver_length_knob)
        layout.addWidget(self.geometric_volume_widget)

        self.calculated_volume_label = QLabel("Расчётный объём: 0.000 м³")
        self.calculated_volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont(); font.setPointSize(9); font.setBold(True)
        self.calculated_volume_label.setFont(font)
        layout.addWidget(self.calculated_volume_label)

        # Применить видимость по режиму
        self._apply_volume_mode_widgets(current_mode)
        if current_mode == 'GEOMETRIC':
            self._update_calculated_volume()
        return group

    def _create_check_valves_group(self) -> QGroupBox:
        group = QGroupBox("Обратные клапаны")
        layout = QVBoxLayout(group)
        knobs_layout = QHBoxLayout(); knobs_layout.setSpacing(12)
        self.cv_atmo_dp_knob = Knob(minimum=0.001, maximum=0.1, value=float(self.parameters.get('cv_atmo_dp', 0) or 0), step=0.001, decimals=3, units="бар", title="ΔP Атм→Линия")
        knobs_layout.addWidget(self.cv_atmo_dp_knob)
        self.cv_tank_dp_knob = Knob(minimum=0.001, maximum=0.1, value=float(self.parameters.get('cv_tank_dp', 0) or 0), step=0.001, decimals=3, units="бар", title="ΔP Линия→Ресивер")
        knobs_layout.addWidget(self.cv_tank_dp_knob)
        layout.addLayout(knobs_layout)

        diameters_layout = QHBoxLayout(); diameters_layout.setSpacing(12)
        self.cv_atmo_dia_knob = Knob(minimum=1.0, maximum=10.0, value=float(self.parameters.get('cv_atmo_dia', 0) or 0), step=0.1, decimals=1, units="мм", title="Диаметр (Атм)")
        diameters_layout.addWidget(self.cv_atmo_dia_knob)
        self.cv_tank_dia_knob = Knob(minimum=1.0, maximum=10.0, value=float(self.parameters.get('cv_tank_dia', 0) or 0), step=0.1, decimals=1, units="мм", title="Диаметр (Ресивер)")
        diameters_layout.addWidget(self.cv_tank_dia_knob)
        layout.addLayout(diameters_layout)
        return group

    def _create_relief_valves_group(self) -> QGroupBox:
        group = QGroupBox("Предохранительные клапаны")
        layout = QVBoxLayout(group)
        pressures_layout = QHBoxLayout(); pressures_layout.setSpacing(12)
        self.relief_min_pressure_knob = Knob(minimum=1.0, maximum=10.0, value=float(self.parameters.get('relief_min_pressure', 0) or 0), step=0.1, decimals=1, units="бар", title="Мин. сброс")
        pressures_layout.addWidget(self.relief_min_pressure_knob)
        self.relief_stiff_pressure_knob = Knob(minimum=5.0, maximum=50.0, value=float(self.parameters.get('relief_stiff_pressure', 0) or 0), step=0.5, decimals=1, units="бар", title="Сброс жёсткости")
        pressures_layout.addWidget(self.relief_stiff_pressure_knob)
        self.relief_safety_pressure_knob = Knob(minimum=20.0, maximum=100.0, value=float(self.parameters.get('relief_safety_pressure', 0) or 0), step=1.0, decimals=0, units="бар", title="Аварийный сброс")
        pressures_layout.addWidget(self.relief_safety_pressure_knob)
        layout.addLayout(pressures_layout)

        throttles_layout = QHBoxLayout(); throttles_layout.setSpacing(12)
        self.throttle_min_dia_knob = Knob(minimum=0.5, maximum=3.0, value=float(self.parameters.get('throttle_min_dia', 0) or 0), step=0.1, decimals=1, units="мм", title="Дроссель мин.")
        throttles_layout.addWidget(self.throttle_min_dia_knob)
        self.throttle_stiff_dia_knob = Knob(minimum=0.5, maximum=3.0, value=float(self.parameters.get('throttle_stiff_dia', 0) or 0), step=0.1, decimals=1, units="мм", title="Дроссель жёстк.")
        throttles_layout.addWidget(self.throttle_stiff_dia_knob)
        throttles_layout.addStretch()
        layout.addLayout(throttles_layout)
        return group

    def _create_environment_group(self) -> QGroupBox:
        group = QGroupBox("Окружающая среда")
        layout = QVBoxLayout(group)
        env_layout = QHBoxLayout(); env_layout.setSpacing(12)
        self.atmo_temp_knob = Knob(minimum=-20.0, maximum=50.0, value=float(self.parameters.get('atmo_temp', 0) or 0), step=1.0, decimals=0, units="°C", title="Температура атм.")
        env_layout.addWidget(self.atmo_temp_knob)
        thermo_group_widget = QWidget(); thermo_layout = QVBoxLayout(thermo_group_widget)
        thermo_layout.setSpacing(4); thermo_layout.setContentsMargins(4, 4, 4, 4)
        thermo_title = QLabel("Термо-режим"); thermo_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont(); font.setPointSize(9); font.setBold(True); thermo_title.setFont(font)
        thermo_layout.addWidget(thermo_title)
        self.thermo_button_group = QButtonGroup()
        self.isothermal_radio = QRadioButton("Изотермический")
        self.adiabatic_radio = QRadioButton("Адиабатический")
        current_thermo = str(self.parameters.get('thermo_mode', 'ISOTHERMAL'))
        self.isothermal_radio.setChecked(current_thermo == 'ISOTHERMAL')
        self.adiabatic_radio.setChecked(current_thermo == 'ADIABATIC')
        self.thermo_button_group.addButton(self.isothermal_radio, 0)
        self.thermo_button_group.addButton(self.adiabatic_radio, 1)
        thermo_layout.addWidget(self.isothermal_radio)
        thermo_layout.addWidget(self.adiabatic_radio)
        env_layout.addWidget(thermo_group_widget); env_layout.addStretch()
        layout.addLayout(env_layout)
        return group

    def _create_options_group(self) -> QGroupBox:
        group = QGroupBox("Системные опции")
        layout = QVBoxLayout(group)
        self.master_isolation_check = QCheckBox("Главная изоляция открыта")
        self.master_isolation_check.setChecked(bool(self.parameters.get('master_isolation_open', False)))
        layout.addWidget(self.master_isolation_check)
        self.link_rod_dia_check = QCheckBox("Связать диаметры штоков передних/задних колёс")
        self.link_rod_dia_check.setChecked(bool(self.parameters.get('link_rod_dia', False)))
        layout.addWidget(self.link_rod_dia_check)
        return group

    # --- Logic ---
    @Slot(float)
    def _on_manual_volume_changed(self, volume: float):
        if self.parameters.get('volume_mode') == 'MANUAL':
            self.parameters['receiver_volume'] = float(volume)
            self.parameter_changed.emit('receiver_volume', float(volume))
            self.receiver_volume_changed.emit(float(volume), 'MANUAL')
            self.pneumatic_updated.emit(self.parameters.copy())

    @Slot()
    def _on_receiver_geometry_changed(self):
        if self.parameters.get('volume_mode') == 'GEOMETRIC':
            self._update_calculated_volume()
            self.parameter_changed.emit('receiver_volume', float(self.parameters['receiver_volume']))
            self.receiver_volume_changed.emit(float(self.parameters['receiver_volume']), 'GEOMETRIC')
            self.pneumatic_updated.emit(self.parameters.copy())

    @Slot(str, float)
    def _on_parameter_changed(self, param_name: str, value):
        self.parameters[param_name] = value
        if isinstance(value, bool):
            self.mode_changed.emit(param_name, str(value))
        else:
            self.parameter_changed.emit(param_name, float(value))
        self.pneumatic_updated.emit(self.parameters.copy())

    @Slot()
    def _on_thermo_mode_changed(self):
        mode = 'ISOTHERMAL' if self.isothermal_radio.isChecked() else 'ADIABATIC'
        self.parameters['thermo_mode'] = mode
        self.mode_changed.emit('thermo_mode', mode)
        self.pneumatic_updated.emit(self.parameters.copy())

    @Slot(int)
    def _on_pressure_units_changed(self, index: int):
        units_map = {0: ("бар", 1.0), 1: ("Па", 100000.0), 2: ("кПа", 100.0), 3: ("МПа", 0.1)}
        unit_name, _ = units_map.get(index, ("бар", 1.0))
        self.parameters['pressure_units'] = unit_name

    @Slot(int)
    def _on_volume_mode_changed(self, index: int):
        if index == 0:
            self._apply_volume_mode_widgets('MANUAL')
            self.parameters['volume_mode'] = 'MANUAL'
            self.parameters['receiver_volume'] = float(self.manual_volume_knob.value())
            self.receiver_volume_changed.emit(float(self.parameters['receiver_volume']), 'MANUAL')
        else:
            self._apply_volume_mode_widgets('GEOMETRIC')
            self.parameters['volume_mode'] = 'GEOMETRIC'
            self._update_calculated_volume()
            self.receiver_volume_changed.emit(float(self.parameters['receiver_volume']), 'GEOMETRIC')
        self.mode_changed.emit('volume_mode', self.parameters['volume_mode'])
        self.pneumatic_updated.emit(self.parameters.copy())

    def _update_calculated_volume(self):
        import math
        diameter = float(self.receiver_diameter_knob.value())
        length = float(self.receiver_length_knob.value())
        radius = diameter / 2.0
        volume = math.pi * radius * radius * length
        self.parameters['receiver_diameter'] = diameter
        self.parameters['receiver_length'] = length
        self.parameters['receiver_volume'] = volume
        self.calculated_volume_label.setText(f"Расчётный объём: {volume:.3f} м³")

    @Slot()
    def _reset_to_defaults(self):
        self._settings_manager.reset_to_defaults(category="pneumatic")
        self.parameters = self._settings_manager.get_category("pneumatic") or {}
        # Отразить в UI
        self.volume_mode_combo.setCurrentIndex(0 if self.parameters.get('volume_mode') == 'MANUAL' else 1)
        self.manual_volume_knob.setValue(float(self.parameters.get('receiver_volume', 0) or 0))
        self.receiver_diameter_knob.setValue(float(self.parameters.get('receiver_diameter', 0) or 0))
        self.receiver_length_knob.setValue(float(self.parameters.get('receiver_length', 0) or 0))
        self._apply_volume_mode_widgets(str(self.parameters.get('volume_mode', 'MANUAL')))
        self.cv_atmo_dp_knob.setValue(float(self.parameters.get('cv_atmo_dp', 0) or 0))
        self.cv_tank_dp_knob.setValue(float(self.parameters.get('cv_tank_dp', 0) or 0))
        self.cv_atmo_dia_knob.setValue(float(self.parameters.get('cv_atmo_dia', 0) or 0))
        self.cv_tank_dia_knob.setValue(float(self.parameters.get('cv_tank_dia', 0) or 0))
        self.relief_min_pressure_knob.setValue(float(self.parameters.get('relief_min_pressure', 0) or 0))
        self.relief_stiff_pressure_knob.setValue(float(self.parameters.get('relief_stiff_pressure', 0) or 0))
        self.relief_safety_pressure_knob.setValue(float(self.parameters.get('relief_safety_pressure', 0) or 0))
        self.throttle_min_dia_knob.setValue(float(self.parameters.get('throttle_min_dia', 0) or 0))
        self.throttle_stiff_dia_knob.setValue(float(self.parameters.get('throttle_stiff_dia', 0) or 0))
        self.atmo_temp_knob.setValue(float(self.parameters.get('atmo_temp', 0) or 0))
        self.isothermal_radio.setChecked(str(self.parameters.get('thermo_mode', 'ISOTHERMAL')) == 'ISOTHERMAL')
        self.adiabatic_radio.setChecked(str(self.parameters.get('thermo_mode', 'ISOTHERMAL')) == 'ADIABATIC')
        self.master_isolation_check.setChecked(bool(self.parameters.get('master_isolation_open', False)))
        self.link_rod_dia_check.setChecked(bool(self.parameters.get('link_rod_dia', False)))
        units_index = {"бар": 0, "Па": 1, "кПа": 2, "МПа": 3}.get(str(self.parameters.get('pressure_units', 'бар')).split()[0], 0)
        self.pressure_units_combo.setCurrentIndex(units_index)
        self.pneumatic_updated.emit(self.parameters.copy())

    @Slot()
    def _save_current_as_defaults(self):
        current = self.collect_state()
        self._settings_manager.set_category("pneumatic", current, auto_save=False)
        self._settings_manager.save_current_as_defaults(category="pneumatic")

    def collect_state(self) -> dict:
        return self.parameters.copy()

    # --- Validation ---
    @Slot()
    def _validate_system(self) -> None:
        """Проверить корректность параметров пневмосистемы и показать результат."""
        errors: list[str] = []
        warnings: list[str] = []

        # Ресивер
        vol = float(self.parameters.get('receiver_volume', 0) or 0)
        mode = str(self.parameters.get('volume_mode', 'MANUAL'))
        if mode == 'MANUAL' and (vol <= 0 or vol > 1.0):
            errors.append("Объём ресивера (ручной) должен быть > 0 и ≤ 1.0 м³")
        if mode == 'GEOMETRIC':
            d = float(self.parameters.get('receiver_diameter', 0) or 0)
            L = float(self.parameters.get('receiver_length', 0) or 0)
            if d <= 0 or L <= 0:
                errors.append("Параметры геометрии ресивера должны быть > 0")

        # Предохранительные давления
        p_min = float(self.parameters.get('relief_min_pressure', 0) or 0)
        p_stiff = float(self.parameters.get('relief_stiff_pressure', 0) or 0)
        p_safe = float(self.parameters.get('relief_safety_pressure', 0) or 0)
        if p_min and p_stiff and p_min >= p_stiff:
            errors.append("Мин. сброс должен быть меньше давления сброса жёсткости")
        if p_stiff and p_safe and p_stiff >= p_safe:
            errors.append("Давление сброса жёсткости должно быть меньше аварийного сброса")

        # Дамберы/дросселя
        th_min = float(self.parameters.get('throttle_min_dia', 0) or 0)
        th_stiff = float(self.parameters.get('throttle_stiff_dia', 0) or 0)
        if th_min and (th_min < 0.2 or th_min > 10):
            warnings.append("Диаметр минимального дросселя вне типового диапазона (0.2..10 мм)")
        if th_stiff and (th_stiff < 0.2 or th_stiff > 10):
            warnings.append("Диаметр дросселя жёсткости вне типового диапазона (0.2..10 мм)")

        # Клапаны
        dp_atmo = float(self.parameters.get('cv_atmo_dp', 0) or 0)
        dp_tank = float(self.parameters.get('cv_tank_dp', 0) or 0)
        if dp_atmo < 0 or dp_tank < 0:
            errors.append("ΔP для обратных клапанов не может быть отрицательной")

        if errors:
            QMessageBox.critical(self, "Ошибки пневмосистемы", "\n".join(errors))
        elif warnings:
            QMessageBox.warning(self, "Предупреждения пневмосистемы", "\n".join(warnings))
        else:
            QMessageBox.information(self, "Проверка пневмосистемы", "Все параметры пневмосистемы корректны.")
