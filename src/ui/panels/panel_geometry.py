# -*- coding: utf-8 -*-
"""
Geometry configuration panel - MS-A-ACCEPT Implementation
Controls for vehicle geometry parameters with unified cylinder parameters
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                              QCheckBox, QPushButton, QLabel, QMessageBox,
                              QSizePolicy, QComboBox)
from PySide6.QtCore import Signal, Slot, Qt, QSignalBlocker
from PySide6.QtGui import QFont

from ..widgets import RangeSlider


class GeometryPanel(QWidget):
    """Panel for geometry parameter configuration (MS-A-ACCEPT)
    
    Provides controls for:
    - Wheelbase and track dimensions
    - Lever geometry 
    - Unified cylinder dimensions (MS-1 complete)
    - Dead zones and clearances
    - Unified parameters in SI units with step 0.001m
    """
    
    # Signals for parameter changes
    parameter_changed = Signal(str, float)  # parameter_name, new_value
    geometry_updated = Signal(dict)         # Complete geometry dictionary
    geometry_changed = Signal(dict)         # 3D scene geometry update
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Parameter storage
        self.parameters = {}
        
        # Dependency resolution state
        self._resolving_conflict = False
        
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
        title_label = QLabel("Geometry Panel (MS-A-ACCEPT)")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Status info - MS completion
        info_label = QLabel("✅ MS-1 to MS-4 Complete: Unified Cylinder Parameters in SI")
        info_label.setStyleSheet("color: #006600; font-size: 10px; font-weight: bold;")
        layout.addWidget(info_label)
        
        # Preset selector
        preset_layout = QHBoxLayout()
        preset_label = QLabel("Preset:")
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            "Standard Truck",
            "Light Commercial", 
            "Heavy Truck",
            "Custom"
        ])
        self.preset_combo.setCurrentIndex(0)
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_layout.addWidget(preset_label)
        preset_layout.addWidget(self.preset_combo, stretch=1)
        layout.addLayout(preset_layout)
        
        # Frame dimensions group
        frame_group = self._create_frame_group()
        layout.addWidget(frame_group)
        
        # Suspension geometry group
        suspension_group = self._create_suspension_group()
        layout.addWidget(suspension_group)
        
        # Cylinder geometry group - UNIFIED PARAMETERS (MS-1)
        cylinder_group = self._create_cylinder_group()
        layout.addWidget(cylinder_group)
        
        # Options group
        options_group = self._create_options_group()
        layout.addWidget(options_group)
        
        # Control buttons
        buttons_layout = self._create_buttons()
        layout.addLayout(buttons_layout)
        
        layout.addStretch()
    
    def _create_frame_group(self) -> QGroupBox:
        """Create frame dimensions group"""
        group = QGroupBox("Размеры рамы")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        
        # Wheelbase - SI units: step 0.001m, decimals=3
        self.wheelbase_slider = RangeSlider(
            minimum=2.000, maximum=4.000, value=3.200, step=0.001,
            decimals=3, units="m", title="Колесная база"
        )
        layout.addWidget(self.wheelbase_slider)
        
        # Track width - SI units: step 0.001m, decimals=3
        self.track_slider = RangeSlider(
            minimum=1.000, maximum=2.500, value=1.600, step=0.001,
            decimals=3, units="m", title="Ширина колеи"
        )
        layout.addWidget(self.track_slider)
        
        return group
    
    def _create_suspension_group(self) -> QGroupBox:
        """Create suspension geometry group"""
        group = QGroupBox("Геометрия подвески")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        
        # Distance from frame to lever pivot - SI units: step 0.001m, decimals=3
        self.frame_to_pivot_slider = RangeSlider(
            minimum=0.300, maximum=1.000, value=0.600, step=0.001,
            decimals=3, units="m", title="Frame to Pivot Distance"
        )
        layout.addWidget(self.frame_to_pivot_slider)
        
        # Lever length - SI units: step 0.001m, decimals=3
        self.lever_length_slider = RangeSlider(
            minimum=0.500, maximum=1.500, value=0.800, step=0.001,
            decimals=3, units="m", title="Длина рычага"
        )
        layout.addWidget(self.lever_length_slider)
        
        # Rod attachment position - fraction: step 0.001, decimals=3
        self.rod_position_slider = RangeSlider(
            minimum=0.300, maximum=0.900, value=0.600, step=0.001,
            decimals=3, units="", title="Rod Position (fraction)"
        )
        layout.addWidget(self.rod_position_slider)
        
        return group
    
    def _create_cylinder_group(self) -> QGroupBox:
        """Create cylinder geometry group - MS-1: UNIFIED PARAMETERS"""
        group = QGroupBox("Размеры цилиндра (MS-1: Унифицированные)")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        
        # Cylinder length - SI units: step 0.001m, decimals=3
        self.cylinder_length_slider = RangeSlider(
            minimum=0.300, maximum=0.800, value=0.500, step=0.001,
            decimals=3, units="m", title="Cylinder Length"
        )
        layout.addWidget(self.cylinder_length_slider)
        
        # MS-1: Unified cylinder diameter - SI units: step 0.001m, decimals=3
        self.cyl_diam_slider = RangeSlider(
            minimum=0.030, maximum=0.150, value=0.080, step=0.001,
            decimals=3, units="m", title="Cylinder Diameter (Unified)"
        )
        layout.addWidget(self.cyl_diam_slider)
        
        # Rod diameter - SI units: step 0.001m, decimals=3
        self.rod_diameter_slider = RangeSlider(
            minimum=0.010, maximum=0.060, value=0.035, step=0.001,
            decimals=3, units="m", title="Rod Diameter"
        )
        layout.addWidget(self.rod_diameter_slider)
        
        # MS-1: Stroke - SI units: step 0.001m, decimals=3
        self.stroke_slider = RangeSlider(
            minimum=0.100, maximum=0.500, value=0.300, step=0.001,
            decimals=3, units="m", title="Stroke"
        )
        layout.addWidget(self.stroke_slider)
        
        # MS-1: Piston thickness - SI units: step 0.001m, decimals=3
        self.piston_thickness_slider = RangeSlider(
            minimum=0.005, maximum=0.030, value=0.020, step=0.001,
            decimals=3, units="m", title="Piston Thickness"
        )
        layout.addWidget(self.piston_thickness_slider)
        
        # MS-1: Dead gap - SI units: step 0.001m, decimals=3
        self.dead_gap_slider = RangeSlider(
            minimum=0.000, maximum=0.020, value=0.005, step=0.001,
            decimals=3, units="m", title="Dead Gap"
        )
        layout.addWidget(self.dead_gap_slider)
        
        return group
    
    def _create_options_group(self) -> QGroupBox:
        """Create options group"""
        group = QGroupBox("Опции")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        
        # Interference checking
        self.interference_check = QCheckBox("Check geometry interference")
        self.interference_check.setChecked(True)
        layout.addWidget(self.interference_check)
        
        # MS-1: Unified diameters checkbox (disabled - always unified now)
        self.link_rod_diameters = QCheckBox("Diameters unified automatically (MS-1)")
        self.link_rod_diameters.setChecked(True)
        self.link_rod_diameters.setEnabled(False)  # Disabled - always unified now
        self.link_rod_diameters.setToolTip("Cylinder diameter is now unified for both chambers (MS-1 complete)")
        layout.addWidget(self.link_rod_diameters)
        
        return group
    
    def _create_buttons(self) -> QHBoxLayout:
        """Create control buttons"""
        layout = QHBoxLayout()
        layout.setSpacing(4)
        
        # Reset to defaults
        self.reset_button = QPushButton("Сбросить")
        self.reset_button.setToolTip("Сбросить к значениям по умолчанию")
        self.reset_button.clicked.connect(self._reset_to_defaults)
        layout.addWidget(self.reset_button)
        
        # Validate geometry
        self.validate_button = QPushButton("Проверить (MS-A)")
        self.validate_button.setToolTip("Проверить корректность геометрии для MS-A-ACCEPT")
        self.validate_button.clicked.connect(self._validate_geometry)
        layout.addWidget(self.validate_button)
        
        layout.addStretch()
        
        return layout

    @Slot(int)
    def _on_preset_changed(self, index: int):
        """Handle preset selection"""
        # MS-1: Updated presets with unified parameters
        presets = {
            0: {  # Standard truck  
                'wheelbase': 3.200, 'track': 1.600, 'lever_length': 0.800,
                'frame_to_pivot': 0.600, 'rod_position': 0.600,
                'cyl_diam_m': 0.080, 'rod_diam_m': 0.035, 'stroke_m': 0.300,
                'cylinder_length': 0.500, 'piston_thickness_m': 0.020, 'dead_gap_m': 0.005
            },
            1: {  # Light commercial
                'wheelbase': 2.800, 'track': 1.400, 'lever_length': 0.700,
                'frame_to_pivot': 0.550, 'rod_position': 0.600,
                'cyl_diam_m': 0.065, 'rod_diam_m': 0.028, 'stroke_m': 0.250,
                'cylinder_length': 0.400, 'piston_thickness_m': 0.015, 'dead_gap_m': 0.003
            },
            2: {  # Heavy truck
                'wheelbase': 3.800, 'track': 1.900, 'lever_length': 0.950,
                'frame_to_pivot': 0.700, 'rod_position': 0.650,  
                'cyl_diam_m': 0.100, 'rod_diam_m': 0.045, 'stroke_m': 0.400,
                'cylinder_length': 0.650, 'piston_thickness_m': 0.025, 'dead_gap_m': 0.007
            },
            3: {}  # Custom (no changes)
        }
        
        if index < 3:  # Don't change for "Custom"
            preset = presets.get(index, {})
            if preset:
                self.set_parameters(preset)
                self.geometry_updated.emit(self.parameters.copy())
    
    def _set_default_values(self):
        """Set default parameter values - MS-1: Unified parameters in SI"""
        defaults = {
            'wheelbase': 3.200, 'track': 1.600, 'frame_to_pivot': 0.600,
            'lever_length': 0.800, 'rod_position': 0.600, 'cylinder_length': 0.500,
            # MS-1: Unified cylinder parameters in SI
            'cyl_diam_m': 0.080, 'rod_diam_m': 0.035, 'stroke_m': 0.300,
            'piston_thickness_m': 0.020, 'dead_gap_m': 0.005,
        }
        self.parameters.update(defaults)
    
    def _connect_signals(self):
        """Connect widget signals"""
        # Frame dimensions
        self.wheelbase_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('wheelbase', v))
        self.track_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('track', v))
        
        # Suspension geometry
        self.frame_to_pivot_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('frame_to_pivot', v))
        self.lever_length_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('lever_length', v))
        self.rod_position_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('rod_position', v))
        
        # MS-1: Unified cylinder dimensions
        self.cylinder_length_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('cylinder_length', v))
        self.cyl_diam_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('cyl_diam_m', v))
        self.rod_diameter_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('rod_diam_m', v))
        self.stroke_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('stroke_m', v))
        self.piston_thickness_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('piston_thickness_m', v))
        self.dead_gap_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('dead_gap_m', v))
    
    @Slot(str, float)
    def _on_parameter_changed(self, param_name: str, value: float):
        """Handle parameter change"""
        if self._resolving_conflict:
            return
            
        # Store old values for logging
        old_value = self.parameters.get(param_name, 0.0)
        self.parameters[param_name] = value
        
        print(f"MS-A-ACCEPT: Parameter changing: {param_name} from {old_value} to {value}")
        
        # Check for dependencies and conflicts
        conflict_resolution = self._check_dependencies(param_name, value, old_value)
        
        if conflict_resolution:
            # Show conflict resolution dialog
            self._resolve_conflict(conflict_resolution)
        else:
            # No conflicts, emit signals
            self.parameter_changed.emit(param_name, value)
            self.geometry_updated.emit(self.parameters.copy())
            
            # Emit 3D scene geometry update
            self._emit_3d_geometry_update()
    
    def _emit_3d_geometry_update(self):
        """Emit geometry update for 3D scene"""
        # Convert parameters to 3D scene format (all from SI meters to mm)
        geometry_3d = {
            'frameLength': self.parameters.get('wheelbase', 3.200) * 1000,  # m -> mm
            'frameHeight': 650.0,  # Fixed for now (mm)
            'frameBeamSize': 120.0,  # Fixed for now (mm)
            'leverLength': self.parameters.get('lever_length', 0.800) * 1000,  # m -> mm
            'cylinderBodyLength': self.parameters.get('cylinder_length', 0.500) * 1000,  # m -> mm
            'tailRodLength': 100.0,  # Fixed for now (mm)
            # Updated parameters (converted from SI meters to mm)
            'trackWidth': self.parameters.get('track', 1.600) * 1000,  # m -> mm
            'frameToPivot': self.parameters.get('frame_to_pivot', 0.600) * 1000,  # m -> mm
            'rodPosition': self.parameters.get('rod_position', 0.600),  # fraction 0-1 (no conversion)
            # MS-1: Unified cylinder parameters (convert from SI meters to mm for QML)
            'boreHead': self.parameters.get('cyl_diam_m', 0.080) * 1000,  # m -> mm
            'boreRod': self.parameters.get('cyl_diam_m', 0.080) * 1000,   # Same as boreHead now! (MS-1)
            'rodDiameter': self.parameters.get('rod_diam_m', 0.035) * 1000,  # m -> mm
            'pistonThickness': self.parameters.get('piston_thickness_m', 0.020) * 1000,  # m -> mm
            # Additional parameters for 3D scene
            'strokeLength': self.parameters.get('stroke_m', 0.300) * 1000,  # m -> mm
            'deadGap': self.parameters.get('dead_gap_m', 0.005) * 1000,  # m -> mm
        }
        
        print(f"Emitting geometry_changed signal with {len(geometry_3d)} parameters")
        self.geometry_changed.emit(geometry_3d)
    
    def _check_dependencies(self, param_name: str, new_value: float, old_value: float) -> dict:
        """Check parameter dependencies (MS-A validation)"""
        
        # MS-1: Check hydraulic constraints with unified cylinder diameter
        if param_name in ['rod_diam_m', 'cyl_diam_m']:
            rod_diameter = self.parameters['rod_diam_m']
            cyl_diameter = self.parameters['cyl_diam_m']
            
            if rod_diameter >= cyl_diameter * 0.8:
                return {
                    'type': 'hydraulic_constraint',
                    'message': f'Rod diameter too large relative to cylinder (MS-A validation).\nRod: {rod_diameter*1000:.1f}mm\nCylinder: {cyl_diameter*1000:.1f}mm\nMax rod: {cyl_diameter*0.8*1000:.1f}mm',
                    'options': [
                        ('Reduce rod diameter', 'rod_diam_m', cyl_diameter * 0.700),
                        ('Increase cylinder diameter', 'cyl_diam_m', rod_diameter / 0.700),
                    ],
                    'changed_param': param_name
                }
        
        # MS-A: Check geometric constraints
        if param_name in ['wheelbase', 'lever_length', 'frame_to_pivot']:
            wheelbase = self.parameters['wheelbase']
            lever_length = self.parameters['lever_length']
            frame_to_pivot = self.parameters['frame_to_pivot']
            
            max_lever_reach = wheelbase / 2.0 - 0.100  # 100mm clearance
            
            if frame_to_pivot + lever_length > max_lever_reach:
                return {
                    'type': 'geometric_constraint',
                    'message': f'Lever geometry exceeds available space (MS-A validation).\nCurrent: {frame_to_pivot + lever_length:.3f}m\nMaximum: {max_lever_reach:.3f}m',
                    'options': [
                        ('Reduce lever length', 'lever_length', max_lever_reach - frame_to_pivot - 0.001),
                        ('Reduce distance to axis', 'frame_to_pivot', max_lever_reach - lever_length - 0.001),
                        ('Increase wheelbase', 'wheelbase', 2.0 * (frame_to_pivot + lever_length + 0.150))
                    ],
                    'changed_param': param_name
                }
        
        return None
    
    def _resolve_conflict(self, conflict_info: dict):
        """Show conflict resolution dialog"""
        self._resolving_conflict = True
        
        try:
            # Create message box with options
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle('MS-A Parameter Conflict')
            msg_box.setText(conflict_info['message'])
            msg_box.setInformativeText('How would you like to resolve this conflict?')
            
            # Add buttons for each resolution option
            buttons = []
            for option_text, param_name, suggested_value in conflict_info['options']:
                button = msg_box.addButton(option_text, QMessageBox.ButtonRole.ActionRole)
                buttons.append((button, param_name, suggested_value))
            
            # Add cancel button
            cancel_button = msg_box.addButton('Cancel', QMessageBox.ButtonRole.RejectRole)
            
            # Show dialog
            msg_box.exec()
            clicked_button = msg_box.clickedButton()
            
            if clicked_button == cancel_button:
                # Revert to old value
                changed_param = conflict_info['changed_param']
                old_value = self._get_widget_for_parameter(changed_param)
                self._set_parameter_value(changed_param, old_value)
            else:
                # Apply selected resolution
                for button, param_name, suggested_value in buttons:
                    if clicked_button == button:
                        self._set_parameter_value(param_name, suggested_value)
                        self.parameters[param_name] = suggested_value
                        break
                
                # Emit update signals
                self.geometry_updated.emit(self.parameters.copy())
        
        finally:
            self._resolving_conflict = False
    
    def _set_parameter_value(self, param_name: str, value: float):
        """Set parameter value on the appropriate widget"""
        widget_map = {
            'wheelbase': self.wheelbase_slider,
            'track': self.track_slider,
            'frame_to_pivot': self.frame_to_pivot_slider,
            'lever_length': self.lever_length_slider,
            'rod_position': self.rod_position_slider,
            'cylinder_length': self.cylinder_length_slider,
            'cyl_diam_m': self.cyl_diam_slider,
            'rod_diam_m': self.rod_diameter_slider,
            'stroke_m': self.stroke_slider,
            'piston_thickness_m': self.piston_thickness_slider,
            'dead_gap_m': self.dead_gap_slider,
        }
        
        widget = widget_map.get(param_name)
        if widget:
            # Block signals during programmatic updates
            blocker = QSignalBlocker(widget)
            widget.setValue(value)
            self.parameters[param_name] = value
        else:
            print(f"Warning: No widget found for parameter '{param_name}'")
    
    def _get_widget_for_parameter(self, param_name: str):
        """Get the current value from the widget for a parameter"""
        widget_map = {
            'wheelbase': self.wheelbase_slider,
            'track': self.track_slider,
            'frame_to_pivot': self.frame_to_pivot_slider,
            'lever_length': self.lever_length_slider,
            'rod_position': self.rod_position_slider,
            'cylinder_length': self.cylinder_length_slider,
            'cyl_diam_m': self.cyl_diam_slider,
            'rod_diam_m': self.rod_diameter_slider,
            'stroke_m': self.stroke_slider,
            'piston_thickness_m': self.piston_thickness_slider,
            'dead_gap_m': self.dead_gap_slider,
        }
        
        widget = widget_map.get(param_name)
        if widget:
            return widget.value()
        else:
            return self.parameters.get(param_name, 0.0)

    @Slot()
    def _reset_to_defaults(self):
        """Reset all parameters to defaults"""
        # Reset to MS-A defaults
        self._set_default_values()
        
        # Update all widgets
        self.wheelbase_slider.setValue(self.parameters['wheelbase'])
        self.track_slider.setValue(self.parameters['track'])
        self.frame_to_pivot_slider.setValue(self.parameters['frame_to_pivot'])
        self.lever_length_slider.setValue(self.parameters['lever_length'])
        self.rod_position_slider.setValue(self.parameters['rod_position'])
        self.cylinder_length_slider.setValue(self.parameters['cylinder_length'])
        
        # Set values for MS-1 unified parameters
        self.cyl_diam_slider.setValue(self.parameters['cyl_diam_m'])
        self.rod_diameter_slider.setValue(self.parameters['rod_diam_m'])
        self.stroke_slider.setValue(self.parameters['stroke_m'])
        self.piston_thickness_slider.setValue(self.parameters['piston_thickness_m'])
        self.dead_gap_slider.setValue(self.parameters['dead_gap_m'])
        
        # Reset checkboxes
        self.interference_check.setChecked(True)
        self.link_rod_diameters.setChecked(True)
        
        # Reset preset combo to "Standard Truck"
        self.preset_combo.setCurrentIndex(0)
        
        # Emit update
        self.geometry_updated.emit(self.parameters.copy())
    
    @Slot()
    def _validate_geometry(self):
        """Validate current geometry settings - MS-A validation"""
        errors = []
        warnings = []
        
        # MS-A: Validate wheelbase vs lever geometry
        wheelbase = self.parameters['wheelbase']
        lever_length = self.parameters['lever_length']
        frame_to_pivot = self.parameters['frame_to_pivot']
        
        max_lever_reach = wheelbase / 2.0 - 0.100
        if frame_to_pivot + lever_length > max_lever_reach:
            errors.append(f"Lever geometry exceeds space: {frame_to_pivot + lever_length:.3f} > {max_lever_reach:.3f}m")
        
        # MS-1: Validate unified cylinder parameters
        rod_diameter = self.parameters['rod_diam_m']
        cyl_diameter = self.parameters['cyl_diam_m']
        
        if rod_diameter >= cyl_diameter * 0.8:
            errors.append(f"Rod too large: {rod_diameter*1000:.1f}mm >= 80% of {cyl_diameter*1000:.1f}mm cylinder")
        elif rod_diameter >= cyl_diameter * 0.7:
            warnings.append(f"Rod close to limit: {rod_diameter*1000:.1f}mm vs {cyl_diameter*1000:.1f}mm cylinder")
        
        # MS-1: Validate stroke vs cylinder length
        stroke = self.parameters['stroke_m']
        cylinder_length = self.parameters['cylinder_length']
        piston_thickness = self.parameters['piston_thickness_m']
        dead_gap = self.parameters['dead_gap_m']
        
        min_cylinder_length = stroke + piston_thickness + 2 * dead_gap
        if cylinder_length < min_cylinder_length:
            errors.append(f"Cylinder too short: {cylinder_length*1000:.1f}mm < {min_cylinder_length*1000:.1f}mm (required)")
        elif cylinder_length < min_cylinder_length + 0.010:
            warnings.append(f"Small clearance: {cylinder_length*1000:.1f}mm vs {min_cylinder_length*1000:.1f}mm (required)")
        
        # Show results
        if errors:
            QMessageBox.critical(self, 'MS-A Geometry Errors', 
                               'Errors found:\n' + '\n'.join(errors))
        elif warnings:
            QMessageBox.warning(self, 'MS-A Geometry Warnings',
                              'Warnings:\n' + '\n'.join(warnings))
        else:
            QMessageBox.information(self, 'MS-A Geometry Check', 
                                  '✅ All geometry parameters are correct for MS-A-ACCEPT!')
    
    def get_parameters(self) -> dict:
        """Get current parameter values"""
        return self.parameters.copy()
    
    def set_parameters(self, params: dict):
        """Set parameter values from dictionary"""
        self._resolving_conflict = True
        
        try:
            # Update internal storage
            self.parameters.update(params)
            
            # Update widgets
            for param_name, value in params.items():
                self._set_parameter_value(param_name, value)
        
        finally:
            self._resolving_conflict = False
