# -*- coding: utf-8 -*-
"""
Pneumatic system configuration panel
Controls for pneumatic parameters using knobs and radio buttons
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                              QRadioButton, QCheckBox, QPushButton, QLabel,
                              QButtonGroup, QSizePolicy)
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QFont

from ..widgets import Knob


class PneumoPanel(QWidget):
    """Panel for pneumatic system configuration
    
    Provides rotary knob controls for:
    - Check valve pressure differences
    - Relief valve trigger pressures  
    - Throttle diameters
    - Atmospheric temperature
    - Thermodynamic mode selection
    - Master isolation valve
    """
    
    # Signals for parameter changes
    parameter_changed = Signal(str, float)  # parameter_name, new_value
    mode_changed = Signal(str, str)         # mode_type, new_mode
    pneumatic_updated = Signal(dict)        # Complete pneumatic config
    geometry_changed = Signal(dict)         # Geometry parameters changed
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Parameter storage
        self.parameters = {}
        
        # Setup UI
        self._setup_ui()
        
        # Set default values
        self._set_default_values()
        
        # Connect signals
        self._connect_signals()
        
        # Size policy
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)
    
    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Title
        title_label = QLabel("Pneumatic System")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Check valves group
        check_valves_group = self._create_check_valves_group()
        layout.addWidget(check_valves_group)
        
        # Relief valves group
        relief_valves_group = self._create_relief_valves_group()
        layout.addWidget(relief_valves_group)
        
        # Environment group
        environment_group = self._create_environment_group()
        layout.addWidget(environment_group)
        
        # Geometry parameters group (NEW - for suspension dimensions)
        geometry_group = self._create_geometry_group()
        layout.addWidget(geometry_group)
        
        # System options group
        options_group = self._create_options_group()
        layout.addWidget(options_group)
        
        # Control buttons
        buttons_layout = self._create_buttons()
        layout.addLayout(buttons_layout)
        
        layout.addStretch()
    
    def _create_check_valves_group(self) -> QGroupBox:
        """Create check valves configuration group"""
        group = QGroupBox("Check Valves")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        
        # Create horizontal layout for knobs
        knobs_layout = QHBoxLayout()
        knobs_layout.setSpacing(12)
        
        # Atmosphere to line check valve ΔP
        self.cv_atmo_dp_knob = Knob(
            minimum=0.001, maximum=0.1, value=0.01, step=0.001,
            decimals=3, units="bar", title="Atmo→Line ΔP"
        )
        knobs_layout.addWidget(self.cv_atmo_dp_knob)
        
        # Line to tank check valve ΔP
        self.cv_tank_dp_knob = Knob(
            minimum=0.001, maximum=0.1, value=0.01, step=0.001,
            decimals=3, units="bar", title="Line→Tank ΔP"
        )
        knobs_layout.addWidget(self.cv_tank_dp_knob)
        
        layout.addLayout(knobs_layout)
        
        # Equivalent diameters row
        diameters_layout = QHBoxLayout()
        diameters_layout.setSpacing(12)
        
        # Atmosphere check valve equivalent diameter
        self.cv_atmo_dia_knob = Knob(
            minimum=1.0, maximum=10.0, value=3.0, step=0.1,
            decimals=1, units="mm", title="Atmo CV Dia"
        )
        diameters_layout.addWidget(self.cv_atmo_dia_knob)
        
        # Tank check valve equivalent diameter
        self.cv_tank_dia_knob = Knob(
            minimum=1.0, maximum=10.0, value=3.0, step=0.1,
            decimals=1, units="mm", title="Tank CV Dia"
        )
        diameters_layout.addWidget(self.cv_tank_dia_knob)
        
        layout.addLayout(diameters_layout)
        
        return group
    
    def _create_relief_valves_group(self) -> QGroupBox:
        """Create relief valves configuration group"""
        group = QGroupBox("Relief Valves")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        
        # Pressure settings row
        pressures_layout = QHBoxLayout()
        pressures_layout.setSpacing(12)
        
        # Minimum pressure relief
        self.relief_min_pressure_knob = Knob(
            minimum=1.0, maximum=10.0, value=2.5, step=0.1,
            decimals=1, units="bar", title="Min Relief"
        )
        pressures_layout.addWidget(self.relief_min_pressure_knob)
        
        # Stiffness relief pressure
        self.relief_stiff_pressure_knob = Knob(
            minimum=5.0, maximum=50.0, value=15.0, step=0.5,
            decimals=1, units="bar", title="Stiffness Relief"
        )
        pressures_layout.addWidget(self.relief_stiff_pressure_knob)
        
        # Safety relief pressure
        self.relief_safety_pressure_knob = Knob(
            minimum=20.0, maximum=100.0, value=50.0, step=1.0,
            decimals=0, units="bar", title="Safety Relief"
        )
        pressures_layout.addWidget(self.relief_safety_pressure_knob)
        
        layout.addLayout(pressures_layout)
        
        # Throttle diameters row
        throttles_layout = QHBoxLayout()
        throttles_layout.setSpacing(12)
        
        # Minimum relief throttle diameter
        self.throttle_min_dia_knob = Knob(
            minimum=0.5, maximum=3.0, value=1.0, step=0.1,
            decimals=1, units="mm", title="Min Throttle"
        )
        throttles_layout.addWidget(self.throttle_min_dia_knob)
        
        # Stiffness relief throttle diameter
        self.throttle_stiff_dia_knob = Knob(
            minimum=0.5, maximum=3.0, value=1.5, step=0.1,
            decimals=1, units="mm", title="Stiff Throttle"
        )
        throttles_layout.addWidget(self.throttle_stiff_dia_knob)
        
        # Add spacer to balance layout
        throttles_layout.addStretch()
        
        layout.addLayout(throttles_layout)
        
        return group
    
    def _create_environment_group(self) -> QGroupBox:
        """Create environment configuration group"""
        group = QGroupBox("Environment")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        
        # Temperature and thermo mode row
        env_layout = QHBoxLayout()
        env_layout.setSpacing(12)
        
        # Atmospheric temperature
        self.atmo_temp_knob = Knob(
            minimum=-20.0, maximum=50.0, value=20.0, step=1.0,
            decimals=0, units="°C", title="Atmosphere Temp"
        )
        env_layout.addWidget(self.atmo_temp_knob)
        
        # Thermodynamic mode selection
        thermo_group_widget = QWidget()
        thermo_layout = QVBoxLayout(thermo_group_widget)
        thermo_layout.setSpacing(4)
        thermo_layout.setContentsMargins(4, 4, 4, 4)
        
        thermo_title = QLabel("Thermo Mode")
        thermo_title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        thermo_title.setFont(font)
        thermo_layout.addWidget(thermo_title)
        
        # Radio button group
        self.thermo_button_group = QButtonGroup()
        
        self.isothermal_radio = QRadioButton("Isothermal")
        self.adiabatic_radio = QRadioButton("Adiabatic")
        
        self.isothermal_radio.setChecked(True)  # Default
        
        self.thermo_button_group.addButton(self.isothermal_radio, 0)
        self.thermo_button_group.addButton(self.adiabatic_radio, 1)
        
        thermo_layout.addWidget(self.isothermal_radio)
        thermo_layout.addWidget(self.adiabatic_radio)
        
        env_layout.addWidget(thermo_group_widget)
        env_layout.addStretch()
        
        layout.addLayout(env_layout)
        
        return group
    
    def _create_geometry_group(self) -> QGroupBox:
        """Create geometry parameters configuration group"""
        group = QGroupBox("Suspension Geometry")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)
        
        # Frame dimensions row
        frame_layout = QHBoxLayout()
        frame_layout.setSpacing(12)
        
        # Frame length
        self.frame_length_knob = Knob(
            minimum=1000.0, maximum=3000.0, value=2000.0, step=50.0,
            decimals=0, units="mm", title="Frame Length"
        )
        frame_layout.addWidget(self.frame_length_knob)
        
        # Frame height
        self.frame_height_knob = Knob(
            minimum=400.0, maximum=800.0, value=650.0, step=10.0,
            decimals=0, units="mm", title="Frame Height"
        )
        frame_layout.addWidget(self.frame_height_knob)
        
        # Frame beam size
        self.frame_beam_size_knob = Knob(
            minimum=80.0, maximum=200.0, value=120.0, step=5.0,
            decimals=0, units="mm", title="Beam Size"
        )
        frame_layout.addWidget(self.frame_beam_size_knob)
        
        layout.addLayout(frame_layout)
        
        # Suspension components row
        suspension_layout = QHBoxLayout()
        suspension_layout.setSpacing(12)
        
        # Lever length
        self.lever_length_knob = Knob(
            minimum=200.0, maximum=500.0, value=315.0, step=5.0,
            decimals=0, units="mm", title="Lever Length"
        )
        suspension_layout.addWidget(self.lever_length_knob)
        
        # Cylinder body length
        self.cylinder_length_knob = Knob(
            minimum=150.0, maximum=400.0, value=250.0, step=10.0,
            decimals=0, units="mm", title="Cylinder Length"
        )
        suspension_layout.addWidget(self.cylinder_length_knob)
        
        # Tail rod length
        self.tail_rod_length_knob = Knob(
            minimum=50.0, maximum=200.0, value=100.0, step=5.0,
            decimals=0, units="mm", title="Tail Rod Length"
        )
        suspension_layout.addWidget(self.tail_rod_length_knob)
        
        layout.addLayout(suspension_layout)
        
        return group
    
    def _create_options_group(self) -> QGroupBox:
        """Create system options group"""
        group = QGroupBox("System Options")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        
        # Master isolation valve
        self.master_isolation_check = QCheckBox("Master Isolation Open")
        self.master_isolation_check.setChecked(False)  # Closed by default
        layout.addWidget(self.master_isolation_check)
        
        # Link rod diameters front/rear
        self.link_rod_dia_check = QCheckBox("Link Front/Rear Rod Diameters")
        self.link_rod_dia_check.setChecked(False)
        layout.addWidget(self.link_rod_dia_check)
        
        return group
    
    def _create_buttons(self) -> QHBoxLayout:
        """Create control buttons"""
        layout = QHBoxLayout()
        layout.setSpacing(4)
        
        # Reset to defaults
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self._reset_to_defaults)
        layout.addWidget(self.reset_button)
        
        # Validate pneumatic system
        self.validate_button = QPushButton("Validate System")
        self.validate_button.clicked.connect(self._validate_system)
        layout.addWidget(self.validate_button)
        
        layout.addStretch()
        
        return layout
    
    def _set_default_values(self):
        """Set default parameter values"""
        defaults = {
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
            
            # Geometry parameters (NEW)
            'frame_length': 2000.0,        # mm
            'frame_height': 650.0,         # mm
            'frame_beam_size': 120.0,      # mm
            'lever_length': 315.0,         # mm
            'cylinder_length': 250.0,      # mm
            'tail_rod_length': 100.0       # mm
        }
        
        self.parameters.update(defaults)
    
    def _connect_signals(self):
        """Connect widget signals"""
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
        
        # Geometry knobs (NEW)
        self.frame_length_knob.valueChanged.connect(
            lambda v: self._on_geometry_changed('frame_length', v))
        self.frame_height_knob.valueChanged.connect(
            lambda v: self._on_geometry_changed('frame_height', v))
        self.frame_beam_size_knob.valueChanged.connect(
            lambda v: self._on_geometry_changed('frame_beam_size', v))
        self.lever_length_knob.valueChanged.connect(
            lambda v: self._on_geometry_changed('lever_length', v))
        self.cylinder_length_knob.valueChanged.connect(
            lambda v: self._on_geometry_changed('cylinder_length', v))
        self.tail_rod_length_knob.valueChanged.connect(
            lambda v: self._on_geometry_changed('tail_rod_length', v))
    
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
    
    def _validate_relief_pressures(self):
        """Validate that relief pressures are in correct order"""
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
        """Reset all parameters to default values"""
        self._set_default_values()
        
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
        
        # Reset geometry knobs (NEW)
        self.frame_length_knob.setValue(self.parameters['frame_length'])
        self.frame_height_knob.setValue(self.parameters['frame_height'])
        self.frame_beam_size_knob.setValue(self.parameters['frame_beam_size'])
        self.lever_length_knob.setValue(self.parameters['lever_length'])
        self.cylinder_length_knob.setValue(self.parameters['cylinder_length'])
        self.tail_rod_length_knob.setValue(self.parameters['tail_rod_length'])
        
        # Emit update
        self.pneumatic_updated.emit(self.parameters.copy())
    
    @Slot()
    def _validate_system(self):
        """Validate pneumatic system configuration"""
        warnings = []
        errors = []
        
        # Check relief valve pressure ordering
        min_p = self.parameters['relief_min_pressure']
        stiff_p = self.parameters['relief_stiff_pressure']
        safety_p = self.parameters['relief_safety_pressure']
        
        if not (min_p < stiff_p < safety_p):
            errors.append("Relief pressures must be ordered: Min < Stiffness < Safety")
        
        # Check temperature range
        temp = self.parameters['atmo_temp']
        if temp < -10.0:
            warnings.append(f"Low temperature ({temp} °C) may affect gas properties")
        elif temp > 40.0:
            warnings.append(f"High temperature ({temp} °C) may affect system performance")
        
        # Check throttle sizes
        min_throttle = self.parameters['throttle_min_dia']
        stiff_throttle = self.parameters['throttle_stiff_dia']
        
        if min_throttle >= stiff_throttle:
            warnings.append("Min throttle diameter should be smaller than stiffness throttle")
        
        # Show results
        from PySide6.QtWidgets import QMessageBox
        
        if errors:
            QMessageBox.critical(self, 'Pneumatic System Validation Failed',
                               'Errors found:\n' + '\n'.join(errors))
        elif warnings:
            QMessageBox.warning(self, 'Pneumatic System Validation Warnings',
                              'Warnings:\n' + '\n'.join(warnings))
        else:
            QMessageBox.information(self, 'Pneumatic System Validation',
                                  'All pneumatic parameters are valid.')
    
    def get_parameters(self) -> dict:
        """Get current parameter values
        
        Returns:
            Dictionary of current parameters
        """
        return self.parameters.copy()
    
    def set_parameters(self, params: dict):
        """Set parameter values from dictionary
        
        Args:
            params: Dictionary of parameter values
        """
        # Update internal storage
        self.parameters.update(params)
        
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
        
        # Update geometry knobs (NEW)
        if 'frame_length' in params:
            self.frame_length_knob.setValue(params['frame_length'])
        if 'frame_height' in params:
            self.frame_height_knob.setValue(params['frame_height'])
        if 'frame_beam_size' in params:
            self.frame_beam_size_knob.setValue(params['frame_beam_size'])
        if 'lever_length' in params:
            self.lever_length_knob.setValue(params['lever_length'])
        if 'cylinder_length' in params:
            self.cylinder_length_knob.setValue(params['cylinder_length'])
        if 'tail_rod_length' in params:
            self.tail_rod_length_knob.setValue(params['tail_rod_length'])
    
    @Slot(str, float)
    def _on_geometry_changed(self, param_name: str, value: float):
        """Handle geometry parameter change
        
        Args:
            param_name: Name of changed geometry parameter
            value: New value
        """
        # Store new value
        self.parameters[param_name] = value
        
        # Extract geometry parameters
        geometry_params = {
            'frameLength': self.parameters.get('frame_length', 2000.0),
            'frameHeight': self.parameters.get('frame_height', 650.0),
            'frameBeamSize': self.parameters.get('frame_beam_size', 120.0),
            'leverLength': self.parameters.get('lever_length', 315.0),
            'cylinderBodyLength': self.parameters.get('cylinder_length', 250.0),
            'tailRodLength': self.parameters.get('tail_rod_length', 100.0)
        }
        
        # Emit geometry change signal
        self.geometry_changed.emit(geometry_params)
        
        # Also emit general parameter change
        self.parameter_changed.emit(param_name, value)
        self.pneumatic_updated.emit(self.parameters.copy())
        
        print(f"🔧 PneumoPanel: Geometry parameter '{param_name}' changed to {value}")
    
    @Slot()