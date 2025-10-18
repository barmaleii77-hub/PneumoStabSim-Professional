# -*- coding: utf-8 -*-
"""
Pneumatic system configuration panel - РУССКИЙ ИНТЕРФЕЙС
Controls for pneumatic parameters using knobs and radio buttons
Панель конфигурации пневмосистемы с крутилками и переключателями
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                              QRadioButton, QCheckBox, QPushButton, QLabel,
                              QButtonGroup, QSizePolicy, QComboBox, QMessageBox)
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QFont

from ..widgets import Knob
# ✅ НОВОЕ: Импортируем SettingsManager
from src.common.settings_manager import SettingsManager


class PneumoPanel(QWidget):
    """Панель конфигурации пневматической системы
    
    Panel for pneumatic system configuration (Russian UI)
    
    Provides rotary knob controls for / Управление крутилками:
    - Check valve pressure differences / Обратные клапаны (перепады давления)
    - Relief valve trigger pressures / Предохранительные клапаны
    - Throttle diameters / Диаметры дросселей
    - Atmospheric temperature / Температура окружающей среды
    - Thermodynamic mode selection / Выбор термодинамического режима
    - Master isolation valve / Главный изолирующий клапан
    """
    
    # Signals for parameter changes
    parameter_changed = Signal(str, float)  # parameter_name, new_value
    mode_changed = Signal(str, str)         # mode_type, new_mode
    pneumatic_updated = Signal(dict)        # Complete pneumatic config
    receiver_volume_changed = Signal(float, str)  # NEW: volume (m³), mode ('MANUAL'/'GEOMETRIC')
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # ✅ НОВОЕ: Используем SettingsManager
        self._settings_manager = SettingsManager()
        
        # Parameter storage
        self.parameters = {}
        self.physics_options = {}
        
        # Setup UI
        self._setup_ui()
        
        # ✅ ИЗМЕНЕНО: Загружаем defaults из SettingsManager
        self._load_defaults_from_settings()
        
        # Connect signals
        self._connect_signals()
        
        # Size policy
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
    
    def _setup_ui(self):
        """Настроить интерфейс / Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Title (Russian)
        title_label = QLabel("Пневматическая система")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Units selector (NEW!)
        units_layout = QHBoxLayout()
        units_label = QLabel("Единицы давления:")
        self.pressure_units_combo = QComboBox()
        self.pressure_units_combo.addItems(["бар (bar)", "Па (Pa)", "кПа (kPa)", "МПа (MPa)"])
        self.pressure_units_combo.setCurrentIndex(0)  # Default: bar
        self.pressure_units_combo.currentIndexChanged.connect(self._on_pressure_units_changed)
        units_layout.addWidget(units_label)
        units_layout.addWidget(self.pressure_units_combo, stretch=1)
        layout.addLayout(units_layout)
        
        # NEW: Receiver group
        receiver_group = self._create_receiver_group()
        layout.addWidget(receiver_group)
        
        # Check valves group
        check_valves_group = self._create_check_valves_group()
        layout.addWidget(check_valves_group)
        
        # Relief valves group
        relief_valves_group = self._create_relief_valves_group()
        layout.addWidget(relief_valves_group)
        
        # Environment group
        environment_group = self._create_environment_group()
        layout.addWidget(environment_group)
        
        # System options group
        options_group = self._create_options_group()
        layout.addWidget(options_group)
        
        # Control buttons
        buttons_layout = self._create_buttons()
        layout.addLayout(buttons_layout)
        
        layout.addStretch()
    
    def _create_receiver_group(self) -> QGroupBox:
        """Создать группу ресивера / Create receiver tank configuration group"""
        group = QGroupBox("Ресивер")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        
        # Volume mode selector (Режим задания объёма)
        mode_layout = QHBoxLayout()
        mode_label = QLabel("Режим объёма:")
        self.volume_mode_combo = QComboBox()
        self.volume_mode_combo.addItems([
            "Ручной объём",
            "Геометрический расчёт"
        ])
        self.volume_mode_combo.setCurrentIndex(0)  # Default: manual volume
        self.volume_mode_combo.currentIndexChanged.connect(self._on_volume_mode_changed)
        mode_layout.addWidget(mode_label)
        mode_layout.addWidget(self.volume_mode_combo, stretch=1)
        layout.addLayout(mode_layout)
        
        # Manual volume controls (Режим 1: Ручной объём)
        self.manual_volume_widget = QWidget()
        manual_layout = QHBoxLayout(self.manual_volume_widget)
        manual_layout.setContentsMargins(0, 0, 0, 0)
        manual_layout.setSpacing(12)
        
        self.manual_volume_knob = Knob(
            minimum=0.001, maximum=0.100, value=0.020, step=0.001,
            decimals=3, units="м³", title="Объём ресивера"
        )
        manual_layout.addWidget(self.manual_volume_knob)
        manual_layout.addStretch()
        
        layout.addWidget(self.manual_volume_widget)
        
        # Geometric calculation controls (Режим 2: Геометрический расчёт)
        self.geometric_volume_widget = QWidget()
        geometric_layout = QHBoxLayout(self.geometric_volume_widget)
        geometric_layout.setContentsMargins(0, 0, 0, 0)
        geometric_layout.setSpacing(12)
        
        self.receiver_diameter_knob = Knob(
            minimum=0.050, maximum=0.500, value=0.200, step=0.001,
            decimals=3, units="м", title="Диаметр ресивера"
        )
        geometric_layout.addWidget(self.receiver_diameter_knob)
        
        self.receiver_length_knob = Knob(
            minimum=0.100, maximum=2.000, value=0.500, step=0.001,
            decimals=3, units="м", title="Длина ресивера"
        )
        geometric_layout.addWidget(self.receiver_length_knob)
        
        layout.addWidget(self.geometric_volume_widget)
        
        # Volume display label (Отображение расчётного объёма)
        self.calculated_volume_label = QLabel("Расчётный объём: 0.016 м³")
        self.calculated_volume_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        self.calculated_volume_label.setFont(font)
        layout.addWidget(self.calculated_volume_label)
        
        # Initially show manual volume mode
        self.geometric_volume_widget.setVisible(False)
        
        return group
    
    def _create_check_valves_group(self) -> QGroupBox:
        """Создать группу обратных клапанов / Create check valves configuration group"""
        group = QGroupBox("Обратные клапаны")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        
        # Create horizontal layout for knobs
        knobs_layout = QHBoxLayout()
        knobs_layout.setSpacing(12)
        
        # Atmosphere to line check valve ΔP (Атмосфера → Линия)
        self.cv_atmo_dp_knob = Knob(
            minimum=0.001, maximum=0.1, value=0.01, step=0.001,
            decimals=3, units="бар", title="ΔP Атм→Линия"
        )
        knobs_layout.addWidget(self.cv_atmo_dp_knob)
        
        # Line to tank check valve ΔP (Линия → Ресивер)
        self.cv_tank_dp_knob = Knob(
            minimum=0.001, maximum=0.1, value=0.01, step=0.001,
            decimals=3, units="бар", title="ΔP Линия→Ресивер"
        )
        knobs_layout.addWidget(self.cv_tank_dp_knob)
        
        layout.addLayout(knobs_layout)
        
        # Equivalent diameters row (Эквивалентные диаметры)
        diameters_layout = QHBoxLayout()
        diameters_layout.setSpacing(12)
        
        # Atmosphere check valve equivalent diameter
        self.cv_atmo_dia_knob = Knob(
            minimum=1.0, maximum=10.0, value=3.0, step=0.1,
            decimals=1, units="мм", title="Диаметр (Атм)"
        )
        diameters_layout.addWidget(self.cv_atmo_dia_knob)
        
        # Tank check valve equivalent diameter
        self.cv_tank_dia_knob = Knob(
            minimum=1.0, maximum=10.0, value=3.0, step=0.1,
            decimals=1, units="мм", title="Диаметр (Ресивер)"
        )
        diameters_layout.addWidget(self.cv_tank_dia_knob)
        
        layout.addLayout(diameters_layout)
        
        return group
    
    def _create_relief_valves_group(self) -> QGroupBox:
        """Создать группу предохранительных клапанов / Create relief valves configuration group"""
        group = QGroupBox("Предохранительные клапаны")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        
        # Pressure settings row (Настройки давления)
        pressures_layout = QHBoxLayout()
        pressures_layout.setSpacing(12)
        
        # Minimum pressure relief (Минимальное сброса)
        self.relief_min_pressure_knob = Knob(
            minimum=1.0, maximum=10.0, value=2.5, step=0.1,
            decimals=1, units="бар", title="Мин. сброс"
        )
        pressures_layout.addWidget(self.relief_min_pressure_knob)
        
        # Stiffness relief pressure (Сброс жёсткости)
        self.relief_stiff_pressure_knob = Knob(
            minimum=5.0, maximum=50.0, value=15.0, step=0.5,
            decimals=1, units="бар", title="Сброс жёсткости"
        )
        pressures_layout.addWidget(self.relief_stiff_pressure_knob)
        
        # Safety relief pressure (Аварийный сброс)
        self.relief_safety_pressure_knob = Knob(
            minimum=20.0, maximum=100.0, value=50.0, step=1.0,
            decimals=0, units="бар", title="Аварийный сброс"
        )
        pressures_layout.addWidget(self.relief_safety_pressure_knob)
        
        layout.addLayout(pressures_layout)
        
        # Throttle diameters row (Диаметры дросселей)
        throttles_layout = QHBoxLayout()
        throttles_layout.setSpacing(12)
        
        # Minimum relief throttle diameter
        self.throttle_min_dia_knob = Knob(
            minimum=0.5, maximum=3.0, value=1.0, step=0.1,
            decimals=1, units="мм", title="Дроссель мин."
        )
        throttles_layout.addWidget(self.throttle_min_dia_knob)
        
        # Stiffness relief throttle diameter
        self.throttle_stiff_dia_knob = Knob(
            minimum=0.5, maximum=3.0, value=1.5, step=0.1,
            decimals=1, units="мм", title="Дроссель жёстк."
        )
        throttles_layout.addWidget(self.throttle_stiff_dia_knob)
        
        # Add spacer to balance layout
        throttles_layout.addStretch()
        
        layout.addLayout(throttles_layout)
        
        return group
    
    def _create_environment_group(self) -> QGroupBox:
        """Создать группу параметров окружающей среды / Create environment configuration group"""
        group = QGroupBox("Окружающая среда")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        
        # Temperature and thermo mode row
        env_layout = QHBoxLayout()
        env_layout.setSpacing(12)
        
        # Atmospheric temperature (Температура атмосферы)
        self.atmo_temp_knob = Knob(
            minimum=-20.0, maximum=50.0, value=20.0, step=1.0,
            decimals=0, units="°C", title="Температура атм."
        )
        env_layout.addWidget(self.atmo_temp_knob)
        
        # Thermodynamic mode selection (Термодинамический режим)
        thermo_group_widget = QWidget()
        thermo_layout = QVBoxLayout(thermo_group_widget)
        thermo_layout.setSpacing(4)
        thermo_layout.setContentsMargins(4, 4, 4, 4)
        
        thermo_title = QLabel("Термо-режим")
        thermo_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        thermo_title.setFont(font)
        thermo_layout.addWidget(thermo_title)
        
        # Radio button group
        self.thermo_button_group = QButtonGroup()
        
        self.isothermal_radio = QRadioButton("Изотермический")
        self.adiabatic_radio = QRadioButton("Адиабатический")
        
        self.isothermal_radio.setChecked(True)  # Default
        
        self.thermo_button_group.addButton(self.isothermal_radio, 0)
        self.thermo_button_group.addButton(self.adiabatic_radio, 1)
        
        thermo_layout.addWidget(self.isothermal_radio)
        thermo_layout.addWidget(self.adiabatic_radio)
        
        env_layout.addWidget(thermo_group_widget)
        env_layout.addStretch()
        
        layout.addLayout(env_layout)
        
        return group
    
    def _create_options_group(self) -> QGroupBox:
        """Создать группу системных опций / Create system options group"""
        group = QGroupBox("Системные опции")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        
        # Master isolation valve (Главная изоляция)
        self.master_isolation_check = QCheckBox("Главная изоляция открыта")
        self.master_isolation_check.setChecked(False)  # Closed by default
        layout.addWidget(self.master_isolation_check)
        
        # Link rod diameters front/rear
        self.link_rod_dia_check = QCheckBox("Связать диаметры штоков передних/задних колёс")
        self.link_rod_dia_check.setChecked(False)
        layout.addWidget(self.link_rod_dia_check)
        
        return group
    
    def _create_buttons(self) -> QHBoxLayout:
        """Создать кнопки управления / Create control buttons"""
        layout = QHBoxLayout()
        layout.setSpacing(4)
        
        # Reset to defaults (Сбросить)
        self.reset_button = QPushButton("Сбросить")
        self.reset_button.setToolTip("Сбросить к значениям по умолчанию")
        self.reset_button.clicked.connect(self._reset_to_defaults)
        layout.addWidget(self.reset_button)
        
        # Validate pneumatic system (Проверить)
        self.validate_button = QPushButton("Проверить")
        self.validate_button.setToolTip("Проверить корректность настроек пневмосистемы")
        self.validate_button.clicked.connect(self._validate_system)
        layout.addWidget(self.validate_button)
        
        layout.addStretch()
        
        return layout
    
    def _load_defaults_from_settings(self):
        """Загрузить defaults из SettingsManager"""
        defaults = self._settings_manager.get("pneumatic", {
            # Receiver parameters
            'volume_mode': 'MANUAL',
            'receiver_volume': 0.020,
            'receiver_diameter': 0.200,
            'receiver_length': 0.500,
            
            # Check valves
            'cv_atmo_dp': 0.01,
            'cv_tank_dp': 0.01,
            'cv_atmo_dia': 3.0,
            'cv_tank_dia': 3.0,
            
            # Relief valves
            'relief_min_pressure': 2.5,
            'relief_stiff_pressure': 15.0,
            'relief_safety_pressure': 50.0,
            'throttle_min_dia': 1.0,
            'throttle_stiff_dia': 1.5,
            
            # Environment
            'atmo_temp': 20.0,
            'thermo_mode': 'ISOTHERMAL',
            
            # Options
            'master_isolation_open': False,
            'link_rod_dia': False,
        })
        
        self.parameters.update(defaults)
    
    def _set_default_values(self):
        """Set default parameter values"""
        defaults = {
            # Receiver parameters (NEW!)
            'volume_mode': 'MANUAL',           # MANUAL or GEOMETRIC
            'receiver_volume': 0.020,          # m³ (20 liters)
            'receiver_diameter': 0.200,        # m (200mm diameter)
            'receiver_length': 0.500,          # m (500mm length)
            
            # Check valves
            'cv_atmo_dp': 0.01,      # bar
            'cv_tank_dp': 0.01,      # bar
            'cv_atmo_dia': 3.0,      # mm
            'cv_tank_dia': 3.0,      # mm
            
            # Relief valves
            'relief_min_pressure': 2.5,    # bar
            'relief_stiff_pressure': 15.0, # bar
            'relief_safety_pressure': 50.0, # bar
            'throttle_min_dia': 1.0,       # mm
            'throttle_stiff_dia': 1.5,     # mm
            
            # Environment
            'atmo_temp': 20.0,       # degC
            'thermo_mode': 'ISOTHERMAL',
            
            # Options
            'master_isolation_open': False,
            'link_rod_dia': False,
        }
        
        self.parameters.update(defaults)
    
    def _connect_signals(self):
        """Connect widget signals"""
        # Receiver controls (NEW!)
        self.manual_volume_knob.valueChanged.connect(
            lambda v: self._on_manual_volume_changed(v))
        self.receiver_diameter_knob.valueChanged.connect(
            lambda v: self._on_receiver_geometry_changed())
        self.receiver_length_knob.valueChanged.connect(
            lambda v: self._on_receiver_geometry_changed())
        
        # Check valve knobs
        self.cv_atmo_dp_knob.valueChanged.connect(
            lambda v: self._on_parameter_changed('cv_atmo_dp', v))
        self.cv_tank_dp_knob.valueChanged.connect(
            lambda v: self._on_parameter_changed('cv_tank_dp', v))
        self.cv_atmo_dia_knob.valueChanged.connect(
            lambda v: self._on_parameter_changed('cv_atmo_dia', v))
        self.cv_tank_dia_knob.valueChanged.connect(
            lambda v: self._on_parameter_changed('cv_tank_dia', v))
        
        # Relief valve knobs
        self.relief_min_pressure_knob.valueChanged.connect(
            lambda v: self._on_parameter_changed('relief_min_pressure', v))
        self.relief_stiff_pressure_knob.valueChanged.connect(
            lambda v: self._on_parameter_changed('relief_stiff_pressure', v))
        self.relief_safety_pressure_knob.valueChanged.connect(
            lambda v: self._on_parameter_changed('relief_safety_pressure', v))
        self.throttle_min_dia_knob.valueChanged.connect(
            lambda v: self._on_parameter_changed('throttle_min_dia', v))
        self.throttle_stiff_dia_knob.valueChanged.connect(
            lambda v: self._on_parameter_changed('throttle_stiff_dia', v))
        
        # Environment knobs
        self.atmo_temp_knob.valueChanged.connect(
            lambda v: self._on_parameter_changed('atmo_temp', v))
        
        # Radio buttons
        self.thermo_button_group.buttonToggled.connect(self._on_thermo_mode_changed)
        
        # Checkboxes
        self.master_isolation_check.toggled.connect(
            lambda checked: self._on_parameter_changed('master_isolation_open', checked))
        self.link_rod_dia_check.toggled.connect(
            lambda checked: self._on_parameter_changed('link_rod_dia', checked))
    
    @Slot(float)
    def _on_manual_volume_changed(self, volume: float):
        """Обработать изменение ручного объёма / Handle manual volume change"""
        if self.parameters.get('volume_mode') == 'MANUAL':
            self.parameters['receiver_volume'] = volume
            
            # Emit signals
            self.parameter_changed.emit('receiver_volume', volume)
            self.receiver_volume_changed.emit(volume, 'MANUAL')  # NEW!
            self.pneumatic_updated.emit(self.parameters.copy())
            
            print(f"🔧 Ручной объём изменён: {volume:.3f} м³")
    
    @Slot()
    def _on_receiver_geometry_changed(self):
        """Обработать изменение геометрии ресивера / Handle receiver geometry change"""
        if self.parameters.get('volume_mode') == 'GEOMETRIC':
            self._update_calculated_volume()
            
            # Emit update signals
            self.parameter_changed.emit('receiver_volume', self.parameters['receiver_volume'])
            self.receiver_volume_changed.emit(self.parameters['receiver_volume'], 'GEOMETRIC')  # NEW!
            self.pneumatic_updated.emit(self.parameters.copy())
    
    @Slot(str, float)
    def _on_parameter_changed(self, param_name: str, value):
        """Handle parameter change
        
        Args:
            param_name: Name of changed parameter
            value: New value (float or bool)
        """
        # Store new value
        self.parameters[param_name] = value
        
        # Validate relief valve pressures ordering
        if param_name in ['relief_min_pressure', 'relief_stiff_pressure', 'relief_safety_pressure']:
            self._validate_relief_pressures()
        
        # Emit signals
        if isinstance(value, bool):
            self.mode_changed.emit(param_name, str(value))
        else:
            self.parameter_changed.emit(param_name, float(value))
        
        self.pneumatic_updated.emit(self.parameters.copy())
    
    @Slot()
    def _on_thermo_mode_changed(self):
        """Handle thermodynamic mode change"""
        if self.isothermal_radio.isChecked():
            mode = 'ISOTHERMAL'
        else:
            mode = 'ADIABATIC'
        
        self.parameters['thermo_mode'] = mode
        self.mode_changed.emit('thermo_mode', mode)
        self.pneumatic_updated.emit(self.parameters.copy())
    
    @Slot(int)
    def _on_pressure_units_changed(self, index: int):
        """Обработать изменение единиц давления / Handle pressure units change"""
        units_map = {
            0: ("бар", 1.0),           # bar (base unit)
            1: ("Па", 100000.0),       # Pa (1 bar = 100000 Pa)
            2: ("кПа", 100.0),         # kPa (1 bar = 100 kPa)
            3: ("МПа", 0.1)            # MPa (1 bar = 0.1 MPa)
        }
        
        unit_name, conversion = units_map.get(index, ("бар", 1.0))
        
        # Update knob units (for display only - internal storage remains in bar)
        # Note: This would require updating Knob widget to support dynamic units
        # For now, just log the change
        print(f"📊 PneumoPanel: Единицы давления изменены на {unit_name}")
        self.parameters['pressure_units'] = unit_name
    
    def _validate_relief_pressures(self):
        """Проверить порядок давлений предохранительных клапанов / Validate relief pressures ordering"""
        min_p = self.parameters['relief_min_pressure']
        stiff_p = self.parameters['relief_stiff_pressure']
        safety_p = self.parameters['relief_safety_pressure']
        
        # Ensure proper ordering: min < stiffness < safety
        if stiff_p <= min_p:
            # Adjust stiffness to be higher than min
            new_stiff = min_p + 1.0
            self.relief_stiff_pressure_knob.setValue(new_stiff)
            self.parameters['relief_stiff_pressure'] = new_stiff
        
        if safety_p <= stiff_p:
            # Adjust safety to be higher than stiffness
            new_safety = self.parameters['relief_stiff_pressure'] + 5.0
            self.relief_safety_pressure_knob.setValue(new_safety)
            self.parameters['relief_safety_pressure'] = new_safety
    
    @Slot()
    def _reset_to_defaults(self):
        """Сбросить все параметры к значениям по умолчанию из JSON"""
        self._settings_manager.reset_to_defaults(category="pneumatic")
        self.parameters = self._settings_manager.get("pneumatic")
        
        # Update receiver controls
        self.volume_mode_combo.setCurrentIndex(0)
        self.manual_volume_knob.setValue(self.parameters['receiver_volume'])
        self.receiver_diameter_knob.setValue(self.parameters['receiver_diameter'])
        self.receiver_length_knob.setValue(self.parameters['receiver_length'])
        
        # Update all knobs
        self.cv_atmo_dp_knob.setValue(self.parameters['cv_atmo_dp'])
        self.cv_tank_dp_knob.setValue(self.parameters['cv_tank_dp'])
        self.cv_atmo_dia_knob.setValue(self.parameters['cv_atmo_dia'])
        self.cv_tank_dia_knob.setValue(self.parameters['cv_tank_dia'])
        
        self.relief_min_pressure_knob.setValue(self.parameters['relief_min_pressure'])
        self.relief_stiff_pressure_knob.setValue(self.parameters['relief_stiff_pressure'])
        self.relief_safety_pressure_knob.setValue(self.parameters['relief_safety_pressure'])
        self.throttle_min_dia_knob.setValue(self.parameters['throttle_min_dia'])
        self.throttle_stiff_dia_knob.setValue(self.parameters['throttle_stiff_dia'])
        
        self.atmo_temp_knob.setValue(self.parameters['atmo_temp'])
        
        # Reset radio buttons and checkboxes
        self.isothermal_radio.setChecked(True)
        self.master_isolation_check.setChecked(False)
        self.link_rod_dia_check.setChecked(False)
        
        # Reset units selector
        self.pressure_units_combo.setCurrentIndex(0)
        
        # Emit update
        self.pneumatic_updated.emit(self.parameters.copy())
    
    def get_parameters(self) -> dict:
        """Get current parameter values
        
        Returns:
            Dictionary of current parameters
        """
        return self.parameters.copy()
    
    def set_parameters(self, params: dict):
        """Set parameter values and save to SettingsManager
        
        Args:
            params: Dictionary of parameter values
        """
        # Update internal storage
        self.parameters.update(params)
        
        # ✅ НОВОЕ: Сохраняем через SettingsManager
        self._settings_manager.set("pneumatic", self.parameters, auto_save=True)
        
        # Update receiver controls (NEW!)
        if 'volume_mode' in params:
            if params['volume_mode'] == 'MANUAL':
                self.volume_mode_combo.setCurrentIndex(0)
            else:
                self.volume_mode_combo.setCurrentIndex(1)
        
        if 'receiver_volume' in params and self.parameters.get('volume_mode') == 'MANUAL':
            self.manual_volume_knob.setValue(params['receiver_volume'])
        
        if 'receiver_diameter' in params:
            self.receiver_diameter_knob.setValue(params['receiver_diameter'])
        
        if 'receiver_length' in params:
            self.receiver_length_knob.setValue(params['receiver_length'])
        
        # Update knobs
        if 'cv_atmo_dp' in params:
            self.cv_atmo_dp_knob.setValue(params['cv_atmo_dp'])
        if 'cv_tank_dp' in params:
            self.cv_tank_dp_knob.setValue(params['cv_tank_dp'])
        if 'cv_atmo_dia' in params:
            self.cv_atmo_dia_knob.setValue(params['cv_atmo_dia'])
        if 'cv_tank_dia' in params:
            self.cv_tank_dia_knob.setValue(params['cv_tank_dia'])
        
        if 'relief_min_pressure' in params:
            self.relief_min_pressure_knob.setValue(params['relief_min_pressure'])
        if 'relief_stiff_pressure' in params:
            self.relief_stiff_pressure_knob.setValue(params['relief_stiff_pressure'])
        if 'relief_safety_pressure' in params:
            self.relief_safety_pressure_knob.setValue(params['relief_safety_pressure'])
        if 'throttle_min_dia' in params:
            self.throttle_min_dia_knob.setValue(params['throttle_min_dia'])
        if 'throttle_stiff_dia' in params:
            self.throttle_stiff_dia_knob.setValue(params['throttle_stiff_dia'])
        
        if 'atmo_temp' in params:
            self.atmo_temp_knob.setValue(params['atmo_temp'])
        
        # Update radio buttons and checkboxes
        if 'thermo_mode' in params:
            if params['thermo_mode'] == 'ISOTHERMAL':
                self.isothermal_radio.setChecked(True)
            else:
                self.adiabatic_radio.setChecked(True)
        
        if 'master_isolation_open' in params:
            self.master_isolation_check.setChecked(params['master_isolation_open'])
        
        if 'link_rod_dia' in params:
            self.link_rod_dia_check.setChecked(params['link_rod_dia'])
    
    @Slot(int)
    def _on_volume_mode_changed(self, index: int):
        """Обработать переключение режима объёма / Handle volume mode change"""
        if index == 0:  # Manual volume mode
            self.manual_volume_widget.setVisible(True)
            self.geometric_volume_widget.setVisible(False)
            self.calculated_volume_label.setVisible(False)
            
            # Update parameters
            self.parameters['volume_mode'] = 'MANUAL'
            self.parameters['receiver_volume'] = self.manual_volume_knob.value()
            
            print(f"📊 Режим объёма: Ручной ({self.parameters['receiver_volume']:.3f} м³)")
            
            # Emit volume change signal with current volume and mode
            self.receiver_volume_changed.emit(self.parameters['receiver_volume'], 'MANUAL')
            
        else:  # Geometric calculation mode
            self.manual_volume_widget.setVisible(False)
            self.geometric_volume_widget.setVisible(True)
            self.calculated_volume_label.setVisible(True)
            
            # Update parameters and calculate volume
            self.parameters['volume_mode'] = 'GEOMETRIC'
            self._update_calculated_volume()
            
            print(f"📊 Режим объёма: Геометрический ({self.parameters['receiver_volume']:.3f} м³)")
            
            # Emit volume change signal with calculated volume and mode
            self.receiver_volume_changed.emit(self.parameters['receiver_volume'], 'GEOMETRIC')
        
        # Emit mode change signal
        self.mode_changed.emit('volume_mode', self.parameters['volume_mode'])
        self.pneumatic_updated.emit(self.parameters.copy())
    
    def _update_calculated_volume(self):
        """Обновить расчётный объём / Update calculated volume from geometry"""
        diameter = self.receiver_diameter_knob.value()
        length = self.receiver_length_knob.value()
        
        # Calculate volume: V = π × (D/2)² × L
        import math
        radius = diameter / 2.0
        volume = math.pi * radius * radius * length
        
        # Update parameters
        self.parameters['receiver_diameter'] = diameter
        self.parameters['receiver_length'] = length
        self.parameters['receiver_volume'] = volume
        
        # Update display label
        self.calculated_volume_label.setText(f"Расчётный объём: {volume:.3f} м³")
        
        print(f"🧮 Геометрический расчёт: D={diameter:.3f}м, L={length:.3f}м → V={volume:.3f}м³")
    
    @Slot()
    def _validate_system(self):
        """Проверить корректность настроек пневмосистемы / Validate pneumatic system settings"""
        issues = []
        warnings = []
        
        # Проверка 1: Порядок давлений предохранительных клапанов
        min_p = self.parameters.get('relief_min_pressure', 0)
        stiff_p = self.parameters.get('relief_stiff_pressure', 0)
        safety_p = self.parameters.get('relief_safety_pressure', 0)
        
        if not (min_p < stiff_p < safety_p):
            issues.append(
                f"❌ Некорректный порядок давлений клапанов:\n"
                f"   Мин: {min_p:.1f} бар, Жёстк: {stiff_p:.1f} бар, Аварийн: {safety_p:.1f} бар\n"
                f"   Требуется: Мин < Жёстк < Аварийн"
            )
        
        # Проверка 2: Объём ресивера
        volume = self.parameters.get('receiver_volume', 0)
        if volume < 0.001:
            issues.append("❌ Слишком малый объём ресивера (< 1 литр)")
        elif volume < 0.005:
            warnings.append("⚠️ Малый объём ресивера (< 5 литров) - возможны проблемы с давлением")
        
        if volume > 0.100:
            warnings.append("⚠️ Большой объём ресивера (> 100 литров) - медленная реакция системы")
        
        # Проверка 3: Диаметры дросселей
        throttle_min = self.parameters.get('throttle_min_dia', 0)
        throttle_stiff = self.parameters.get('throttle_stiff_dia', 0)
        
        if throttle_min >= throttle_stiff:
            issues.append(
                f"❌ Диаметр минимального дросселя ({throttle_min:.1f} мм) "
                f"должен быть меньше жёсткости ({throttle_stiff:.1f} мм)"
            )
        
        if throttle_min < 0.3:
            warnings.append("⚠️ Слишком малый диаметр минимального дросселя (< 0.3 мм)")
        
        # Проверка 4: Температура
        temp = self.parameters.get('atmo_temp', 20)
        if temp < -40 or temp > 60:
            warnings.append(f"⚠️ Экстремальная температура ({temp}°C) - проверьте корректность")
        
        # Проверка 5: Перепады давления обратных клапанов
        cv_atmo_dp = self.parameters.get('cv_atmo_dp', 0)
        cv_tank_dp = self.parameters.get('cv_tank_dp', 0)
        
        if cv_atmo_dp > 0.05:
            warnings.append(f"⚠️ Большой перепад обратного клапана атмосферы ({cv_atmo_dp:.3f} бар)")
        
        if cv_tank_dp > 0.05:
            warnings.append(f"⚠️ Большой перепад обратного клапана ресивера ({cv_tank_dp:.3f} бар)")
        
        # Формирование сообщения
        if issues:
            # Критические ошибки
            message = "🔴 ОБНАРУЖЕНЫ КРИТИЧЕСКИЕ ОШИБКИ:\n\n" + "\n\n".join(issues)
            if warnings:
                message += "\n\n⚠️ ПРЕДУПРЕЖДЕНИЯ:\n\n" + "\n\n".join(warnings)
            
            QMessageBox.critical(self, "Ошибки конфигурации", message)
            print("❌ Проверка пневмосистемы: ОШИБКИ")
            
        elif warnings:
            # Только предупреждения
            message = "⚠️ ПРЕДУПРЕЖДЕНИЯ:\n\n" + "\n\n".join(warnings)
            message += "\n\nСистема работоспособна, но рекомендуется проверить параметры."
            
            QMessageBox.warning(self, "Предупреждения", message)
            print("⚠️ Проверка пневмосистемы: ПРЕДУПРЕЖДЕНИЯ")
            
        else:
            # Всё в порядке
            message = (
                "✅ Конфигурация пневмосистемы корректна!\n\n"
                f"Параметры:\n"
                f"  • Объём ресивера: {volume:.3f} м³ ({volume*1000:.1f} л)\n"
                f"  • Давления клапанов: {min_p:.1f} / {stiff_p:.1f} / {safety_p:.1f} бар\n"
                f"  • Температура: {temp:.0f}°C\n"
                f"  • Режим: {self.parameters.get('thermo_mode', 'N/A')}\n"
                f"  • Главная изоляция: {'Открыта' if self.parameters.get('master_isolation_open') else 'Закрыта'}"
            )
            
            QMessageBox.information(self, "Проверка успешна", message)
            print("✅ Проверка пневмосистемы: ВСЁ В ПОРЯДКЕ")
