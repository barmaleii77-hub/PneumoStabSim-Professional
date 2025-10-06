# -*- coding: utf-8 -*-
"""
Simulation modes configuration panel - РУССКИЙ ИНТЕРФЕЙС
Controls for simulation type, physics options, and road excitation
Панель конфигурации режимов симуляции с управлением физикой и дорожным воздействием
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                              QRadioButton, QCheckBox, QPushButton, QLabel,
                              QButtonGroup, QSizePolicy, QComboBox)  # NEW: QComboBox
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QFont

from ..widgets import RangeSlider


class ModesPanel(QWidget):
    """Панель конфигурации режимов симуляции
    
    Panel for simulation mode configuration (Russian UI)
    
    Provides controls for / Управление:
    - Kinematic vs Dynamic simulation / Кинематическая vs Динамическая симуляция
    - Physics component toggles / Переключатели физических компонентов
    - Road excitation parameters / Параметры дорожного воздействия
    - Simulation control buttons / Кнопки управления симуляцией
    """
    
    # Signals
    simulation_control = Signal(str)        # "start", "stop", "reset", "pause"
    mode_changed = Signal(str, str)         # mode_type, new_mode
    parameter_changed = Signal(str, float)  # parameter_name, new_value
    physics_options_changed = Signal(dict)  # Physics option toggles
    animation_changed = Signal(dict)        # Animation parameters changed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Parameter storage
        self.parameters = {}
        self.physics_options = {}
        
        # Setup UI
        self._setup_ui()
        
        # Set default values
        self._set_default_values()
        
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
        title_label = QLabel("Режимы симуляции")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Mode preset selector (NEW!)
        preset_layout = QHBoxLayout()
        preset_label = QLabel("Пресет режима:")
        self.mode_preset_combo = QComboBox()
        self.mode_preset_combo.addItems([
            "Стандартный",
            "Только кинематика",
            "Полная динамика",
            "Тест пневматики",
            "Пользовательский"
        ])
        self.mode_preset_combo.setCurrentIndex(0)  # Default: Standard
        self.mode_preset_combo.currentIndexChanged.connect(self._on_mode_preset_changed)
        preset_layout.addWidget(preset_label)
        preset_layout.addWidget(self.mode_preset_combo, stretch=1)
        layout.addLayout(preset_layout)
        
        # Simulation control group
        control_group = self._create_control_group()
        layout.addWidget(control_group)
        
        # Simulation mode group
        mode_group = self._create_mode_group()
        layout.addWidget(mode_group)
        
        # Physics options group
        physics_group = self._create_physics_group()
        layout.addWidget(physics_group)
        
        # Road excitation group
        road_group = self._create_road_group()
        layout.addWidget(road_group)
        
        layout.addStretch()
    
    def _create_control_group(self) -> QGroupBox:
        """Создать группу управления симуляцией / Create simulation control buttons group"""
        group = QGroupBox("Управление симуляцией")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        
        # Main control buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        
        self.start_button = QPushButton("▶ Старт")
        self.stop_button = QPushButton("⏹ Стоп")
        self.pause_button = QPushButton("⏸ Пауза")
        self.reset_button = QPushButton("🔄 Сброс")
        
        # Style the buttons
        self.start_button.setMinimumHeight(30)
        self.stop_button.setMinimumHeight(30)
        self.pause_button.setMinimumHeight(30)
        self.reset_button.setMinimumHeight(30)
        
        # Tooltips
        self.start_button.setToolTip("Запустить симуляцию")
        self.stop_button.setToolTip("Остановить симуляцию")
        self.pause_button.setToolTip("Приостановить симуляцию")
        self.reset_button.setToolTip("Сбросить симуляцию к начальному состоянию")
        
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addWidget(self.pause_button)
        buttons_layout.addWidget(self.reset_button)
        
        layout.addLayout(buttons_layout)
        
        return group
    
    def _create_mode_group(self) -> QGroupBox:
        """Создать группу выбора режима симуляции / Create simulation mode selection group"""
        group = QGroupBox("Тип симуляции")
        layout = QHBoxLayout(group)
        layout.setSpacing(16)
        
        # Kinematics vs Dynamics (Кинематика vs Динамика)
        sim_type_widget = QWidget()
        sim_type_layout = QVBoxLayout(sim_type_widget)
        sim_type_layout.setSpacing(4)
        
        sim_type_label = QLabel("Режим физики")
        sim_type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        sim_type_label.setFont(font)
        sim_type_layout.addWidget(sim_type_label)
        
        self.sim_type_group = QButtonGroup()
        self.kinematics_radio = QRadioButton("Кинематика")
        self.dynamics_radio = QRadioButton("Динамика")
        
        self.kinematics_radio.setChecked(True)  # Default
        
        self.sim_type_group.addButton(self.kinematics_radio, 0)
        self.sim_type_group.addButton(self.dynamics_radio, 1)
        
        sim_type_layout.addWidget(self.kinematics_radio)
        sim_type_layout.addWidget(self.dynamics_radio)
        
        layout.addWidget(sim_type_widget)
        
        # Thermodynamic mode (Термодинамический режим)
        thermo_widget = QWidget()
        thermo_layout = QVBoxLayout(thermo_widget)
        thermo_layout.setSpacing(4)
        
        thermo_label = QLabel("Термо-режим")
        thermo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        thermo_label.setFont(font)
        thermo_layout.addWidget(thermo_label)
        
        self.thermo_group = QButtonGroup()
        self.isothermal_radio = QRadioButton("Изотермический")
        self.adiabatic_radio = QRadioButton("Адиабатический")
        
        self.isothermal_radio.setChecked(True)  # Default
        
        self.thermo_group.addButton(self.isothermal_radio, 0)
        self.thermo_group.addButton(self.adiabatic_radio, 1)
        
        thermo_layout.addWidget(self.isothermal_radio)
        thermo_layout.addWidget(self.adiabatic_radio)
        
        layout.addWidget(thermo_widget)
        
        return group
    
    def _create_physics_group(self) -> QGroupBox:
        """Создать группу опций физики / Create physics options group"""
        group = QGroupBox("Опции физики")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        
        # Component toggles (Переключатели компонентов)
        self.include_springs_check = QCheckBox("Включить пружины")
        self.include_dampers_check = QCheckBox("Включить демпферы")
        self.include_pneumatics_check = QCheckBox("Включить пневматику")
        
        # Set defaults
        self.include_springs_check.setChecked(True)
        self.include_dampers_check.setChecked(True)
        self.include_pneumatics_check.setChecked(True)
        
        # Tooltips
        self.include_springs_check.setToolTip("Учитывать упругость пружин")
        self.include_dampers_check.setToolTip("Учитывать демпфирование амортизаторов")
        self.include_pneumatics_check.setToolTip("Учитывать пневматическую систему")
        
        layout.addWidget(self.include_springs_check)
        layout.addWidget(self.include_dampers_check)
        layout.addWidget(self.include_pneumatics_check)
        
        return group
    
    def _create_road_group(self) -> QGroupBox:
        """Создать группу дорожного воздействия / Create road excitation parameters group"""
        group = QGroupBox("Дорожное воздействие")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        
        # Global excitation parameters (Глобальные параметры)
        self.amplitude_slider = RangeSlider(
            minimum=0.0, maximum=0.2, value=0.05, step=0.001,
            decimals=3, units="м", title="Глобальная амплитуда"
        )
        layout.addWidget(self.amplitude_slider)
        
        self.frequency_slider = RangeSlider(
            minimum=0.1, maximum=10.0, value=1.0, step=0.1,
            decimals=1, units="Гц", title="Глобальная частота"
        )
        layout.addWidget(self.frequency_slider)
        
        self.phase_slider = RangeSlider(
            minimum=0.0, maximum=360.0, value=0.0, step=15.0,
            decimals=0, units="°", title="Глобальная фаза"
        )
        layout.addWidget(self.phase_slider)
        
        # Per-wheel phase offsets (Фазовые сдвиги по колёсам)
        per_wheel_label = QLabel("Фазовые сдвиги по колёсам")
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        per_wheel_label.setFont(font)
        layout.addWidget(per_wheel_label)
        
        # Create compact sliders for each wheel
        wheel_layout = QHBoxLayout()
        wheel_layout.setSpacing(8)
        
        # Left Front (Левое переднее)
        lf_widget = QWidget()
        lf_layout = QVBoxLayout(lf_widget)
        lf_layout.setContentsMargins(2, 2, 2, 2)
        lf_layout.setSpacing(2)
        lf_label = QLabel("ЛП")
        lf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lf_layout.addWidget(lf_label)
        
        self.lf_phase_slider = RangeSlider(
            minimum=0.0, maximum=360.0, value=0.0, step=15.0,
            decimals=0, units="°", title=""
        )
        lf_layout.addWidget(self.lf_phase_slider)
        wheel_layout.addWidget(lf_widget)
        
        # Right Front (Правое переднее)
        rf_widget = QWidget()
        rf_layout = QVBoxLayout(rf_widget)
        rf_layout.setContentsMargins(2, 2, 2, 2)
        rf_layout.setSpacing(2)
        rf_label = QLabel("ПП")
        rf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rf_layout.addWidget(rf_label)
        
        self.rf_phase_slider = RangeSlider(
            minimum=0.0, maximum=360.0, value=0.0, step=15.0,
            decimals=0, units="°", title=""
        )
        rf_layout.addWidget(self.rf_phase_slider)
        wheel_layout.addWidget(rf_widget)
        
        # Left Rear (Левое заднее)
        lr_widget = QWidget()
        lr_layout = QVBoxLayout(lr_widget)
        lr_layout.setContentsMargins(2, 2, 2, 2)
        lr_layout.setSpacing(2)
        lr_label = QLabel("ЛЗ")
        lr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lr_layout.addWidget(lr_label)
        
        self.lr_phase_slider = RangeSlider(
            minimum=0.0, maximum=360.0, value=0.0, step=15.0,
            decimals=0, units="°", title=""
        )
        lr_layout.addWidget(self.lr_phase_slider)
        wheel_layout.addWidget(lr_widget)
        
        # Right Rear (Правое заднее)
        rr_widget = QWidget()
        rr_layout = QVBoxLayout(rr_widget)
        rr_layout.setContentsMargins(2, 2, 2, 2)
        rr_layout.setSpacing(2)
        rr_label = QLabel("ПЗ")
        rr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rr_layout.addWidget(rr_label)
        
        self.rr_phase_slider = RangeSlider(
            minimum=0.0, maximum=360.0, value=0.0, step=15.0,
            decimals=0, units="°", title=""
        )
        rr_layout.addWidget(self.rr_phase_slider)
        wheel_layout.addWidget(rr_widget)
        
        layout.addLayout(wheel_layout)
        
        return group
    
    def _set_default_values(self):
        """Set default parameter values"""
        defaults = {
            # Simulation modes
            'sim_type': 'KINEMATICS',
            'thermo_mode': 'ISOTHERMAL',
            'mode_preset': 'standard',
            
            # Road excitation
            'amplitude': 0.05,       # m
            'frequency': 1.0,        # Hz
            'phase': 0.0,           # degrees
            'lf_phase': 0.0,        # degrees
            'rf_phase': 0.0,        # degrees
            'lr_phase': 0.0,        # degrees
            'rr_phase': 0.0,        # degrees
        }
        
        physics_defaults = {
            'include_springs': True,
            'include_dampers': True,
            'include_pneumatics': True
        }
        
        self.parameters.update(defaults)
        self.physics_options.update(physics_defaults)
    
    def _connect_signals(self):
        """Connect widget signals"""
        # Control buttons
        self.start_button.clicked.connect(lambda: self.simulation_control.emit("start"))
        self.stop_button.clicked.connect(lambda: self.simulation_control.emit("stop"))
        self.pause_button.clicked.connect(lambda: self.simulation_control.emit("pause"))
        self.reset_button.clicked.connect(lambda: self.simulation_control.emit("reset"))
        
        # Mode radio buttons
        self.sim_type_group.buttonToggled.connect(self._on_sim_type_changed)
        self.thermo_group.buttonToggled.connect(self._on_thermo_mode_changed)
        
        # Physics options checkboxes
        self.include_springs_check.toggled.connect(
            lambda checked: self._on_physics_option_changed('include_springs', checked))
        self.include_dampers_check.toggled.connect(
            lambda checked: self._on_physics_option_changed('include_dampers', checked))
        self.include_pneumatics_check.toggled.connect(
            lambda checked: self._on_physics_option_changed('include_pneumatics', checked))
        
        # Road excitation sliders
        self.amplitude_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('amplitude', v))
        self.frequency_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('frequency', v))
        self.phase_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('phase', v))
        
        # Per-wheel phase sliders
        self.lf_phase_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('lf_phase', v))
        self.rf_phase_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('rf_phase', v))
        self.lr_phase_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('lr_phase', v))
        self.rr_phase_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('rr_phase', v))
    
    @Slot(int)
    def _on_mode_preset_changed(self, index: int):
        """Обработать изменение пресета режима / Handle mode preset change"""
        presets = {
            0: {  # Стандартный
                'sim_type': 'KINEMATICS',
                'thermo_mode': 'ISOTHERMAL',
                'include_springs': True,
                'include_dampers': True,
                'include_pneumatics': True
            },
            1: {  # Только кинематика
                'sim_type': 'KINEMATICS',
                'thermo_mode': 'ISOTHERMAL',
                'include_springs': False,
                'include_dampers': False,
                'include_pneumatics': False
            },
            2: {  # Полная динамика
                'sim_type': 'DYNAMICS',
                'thermo_mode': 'ADIABATIC',
                'include_springs': True,
                'include_dampers': True,
                'include_pneumatics': True
            },
            3: {  # Тест пневматики
                'sim_type': 'DYNAMICS',
                'thermo_mode': 'ISOTHERMAL',
                'include_springs': False,
                'include_dampers': False,
                'include_pneumatics': True
            },
            4: {  # Пользовательский (не изменяет настройки)
                'custom': True
            }
        }
        
        preset = presets.get(index, {})
        
        if 'custom' not in preset:
            # Apply preset
            if preset.get('sim_type') == 'KINEMATICS':
                self.kinematics_radio.setChecked(True)
            else:
                self.dynamics_radio.setChecked(True)
            
            if preset.get('thermo_mode') == 'ISOTHERMAL':
                self.isothermal_radio.setChecked(True)
            else:
                self.adiabatic_radio.setChecked(True)
            
            self.include_springs_check.setChecked(preset.get('include_springs', True))
            self.include_dampers_check.setChecked(preset.get('include_dampers', True))
            self.include_pneumatics_check.setChecked(preset.get('include_pneumatics', True))
            
            print(f"📋 ModesPanel: Пресет режима '{self.mode_preset_combo.currentText()}' применён")
        
        self.parameters['mode_preset'] = self.mode_preset_combo.currentText()
    
    @Slot()
    def _on_sim_type_changed(self):
        """Handle simulation type change"""
        if self.kinematics_radio.isChecked():
            mode = 'KINEMATICS'
        else:
            mode = 'DYNAMICS'
        
        self.parameters['sim_type'] = mode
        self.mode_changed.emit('sim_type', mode)
        
        # Switch to custom preset if manual change
        if self.mode_preset_combo.currentIndex() != 4:
            self.mode_preset_combo.setCurrentIndex(4)
    
    @Slot()
    def _on_thermo_mode_changed(self):
        """Handle thermodynamic mode change"""
        if self.isothermal_radio.isChecked():
            mode = 'ISOTHERMAL'
        else:
            mode = 'ADIABATIC'
        
        self.parameters['thermo_mode'] = mode
        self.mode_changed.emit('thermo_mode', mode)
        
        # Switch to custom preset if manual change
        if self.mode_preset_combo.currentIndex() != 4:
            self.mode_preset_combo.setCurrentIndex(4)
    
    @Slot(str, bool)
    def _on_physics_option_changed(self, option_name: str, checked: bool):
        """Handle physics option toggle
        
        Args:
            option_name: Name of physics option
            checked: New state
        """
        self.physics_options[option_name] = checked
        self.physics_options_changed.emit(self.physics_options.copy())
        
        # Switch to custom preset if manual change
        if self.mode_preset_combo.currentIndex() != 4:
            self.mode_preset_combo.setCurrentIndex(4)
    
    @Slot(str, float)
    def _on_parameter_changed(self, param_name: str, value: float):
        """Handle parameter change
        
        Args:
            param_name: Name of changed parameter
            value: New value
        """
        self.parameters[param_name] = value
        self.parameter_changed.emit(param_name, value)
        
        # Emit animation_changed for road excitation parameters
        if param_name in ['amplitude', 'frequency', 'phase', 'lf_phase', 'rf_phase', 'lr_phase', 'rr_phase']:
            animation_params = {
                'amplitude': self.parameters.get('amplitude', 0.05),
                'frequency': self.parameters.get('frequency', 1.0),
                'phase': self.parameters.get('phase', 0.0),
                'lf_phase': self.parameters.get('lf_phase', 0.0),
                'rf_phase': self.parameters.get('rf_phase', 0.0),
                'lr_phase': self.parameters.get('lr_phase', 0.0),
                'rr_phase': self.parameters.get('rr_phase', 0.0)
            }
            self.animation_changed.emit(animation_params)
            print(f"🔧 ModesPanel: Параметр анимации '{param_name}' изменён на {value}")
    
    def get_parameters(self) -> dict:
        """Get current parameter values
        
        Returns:
            Dictionary of current parameters
        """
        return self.parameters.copy()
    
    def get_physics_options(self) -> dict:
        """Get current physics options
        
        Returns:
            Dictionary of physics option states
        """
        return self.physics_options.copy()
    
    def set_simulation_running(self, running: bool):
        """Update UI state based on simulation status
        
        Args:
            running: True if simulation is running
        """
        self.start_button.setEnabled(not running)
        self.stop_button.setEnabled(running)
        self.pause_button.setEnabled(running)
        self.reset_button.setEnabled(not running)
        
        # Disable mode changes during simulation
        self.kinematics_radio.setEnabled(not running)
        self.dynamics_radio.setEnabled(not running)
        self.isothermal_radio.setEnabled(not running)
        self.adiabatic_radio.setEnabled(not running)