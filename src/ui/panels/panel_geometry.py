# -*- coding: utf-8 -*-
"""
Geometry configuration panel - Russian Interface
Controls for vehicle geometry parameters with dependency management
NOW INTEGRATES WITH GEOMETRYSTATE FOR KINEMATIC CONSTRAINTS (A-4.3)
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                              QCheckBox, QPushButton, QLabel, QMessageBox,
                              QSizePolicy, QComboBox)
from PySide6.QtCore import Signal, Slot, Qt, QSignalBlocker
from PySide6.QtGui import QFont

from ..widgets import RangeSlider

# A-4.3: Import GeometryState for kinematic constraints
try:
    from ..geo_state import GeometryState, create_default_geometry, create_light_commercial_geometry
    GEOMETRY_STATE_AVAILABLE = True
except ImportError:
    GEOMETRY_STATE_AVAILABLE = False
    print("Warning: GeometryState not available, using legacy validation")


class GeometryPanel(QWidget):
    """Panel for geometry parameter configuration (Russian UI)
    
    A-4.3: Now uses GeometryState for kinematic constraint validation
    
    Provides controls for:
    - Wheelbase and track dimensions
    - Lever geometry 
    - Cylinder dimensions
    - Dead zones and clearances
    - ? NEW: Kinematic constraints validation
    """
    
    # Signals for parameter changes
    parameter_changed = Signal(str, float)  # parameter_name, new_value
    geometry_updated = Signal(dict)         # Complete geometry dictionary
    geometry_changed = Signal(dict)         # 3D scene geometry update
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # A-4.3: Initialize GeometryState for kinematic constraints
        if GEOMETRY_STATE_AVAILABLE:
            self.geo_state = create_default_geometry()
            print("? A-4.3: GeometryState initialized with kinematic constraints")
        else:
            self.geo_state = None
            print("??  A-4.3: Using legacy parameter storage")
        
        # Parameter storage (legacy fallback)
        self.parameters = {}
        
        # Dependency resolution state
        self._resolving_conflict = False
        self._updating_from_state = False  # Prevent recursion during updates
        
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
        
        # Title with A-4.3 indicator
        title_text = "Geometry Panel"
        if GEOMETRY_STATE_AVAILABLE:
            title_text += " (A-4.3: Kinematic Constraints)"
        title_label = QLabel(title_text)
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
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
        
        # A-4.3: Kinematic info display
        if GEOMETRY_STATE_AVAILABLE:
            self.kinematic_info_label = QLabel("Kinematic limits: calculating...");
            self.kinematic_info_label.setStyleSheet("color: #666; font-size: 10px;")
            layout.addWidget(self.kinematic_info_label)
        
        # Frame dimensions group
        frame_group = self._create_frame_group()
        layout.addWidget(frame_group)
        
        # Suspension geometry group
        suspension_group = self._create_suspension_group()
        layout.addWidget(suspension_group)
        
        # Cylinder geometry group - A-4.3: Updated with kinematic limits
        cylinder_group = self._create_cylinder_group()
        layout.addWidget(cylinder_group)
        
        # Options group
        options_group = self._create_options_group()
        layout.addWidget(options_group)
        
        # Control buttons - A-4.3: Enhanced validation
        buttons_layout = self._create_buttons()
        layout.addLayout(buttons_layout)
        
        layout.addStretch()
        
        # A-4.3: Initial kinematic info update
        if GEOMETRY_STATE_AVAILABLE:
            self._update_kinematic_info()
    
    def _create_frame_group(self) -> QGroupBox:
        """Create frame dimensions group"""
        group = QGroupBox("Frame Dimensions")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        
        # Wheelbase - SI units: step 0.001m, decimals=3
        self.wheelbase_slider = RangeSlider(
            minimum=2.000, maximum=4.000, value=3.200, step=0.001,
            decimals=3, units="m", title="Wheelbase"
        )
        layout.addWidget(self.wheelbase_slider)
        
        # Track width - SI units: step 0.001m, decimals=3
        self.track_slider = RangeSlider(
            minimum=1.000, maximum=2.500, value=1.600, step=0.001,
            decimals=3, units="m", title="Track Width"
        )
        layout.addWidget(self.track_slider)
        
        return group
    
    def _create_suspension_group(self) -> QGroupBox:
        """Create suspension geometry group"""
        group = QGroupBox("Suspension Geometry")
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
            decimals=3, units="m", title="Lever Length"
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
        """Create cylinder geometry group - A-4.3: Enhanced with kinematic limits"""
        group = QGroupBox("Cylinder Dimensions")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        
        # Cylinder length - SI units: step 0.001m, decimals=3
        self.cylinder_length_slider = RangeSlider(
            minimum=0.300, maximum=0.800, value=0.500, step=0.001,
            decimals=3, units="m", title="Cylinder Length"
        )
        layout.addWidget(self.cylinder_length_slider)
        
        # Unified cylinder diameter - SI units: step 0.001m, decimals=3
        self.cyl_diam_slider = RangeSlider(
            minimum=0.030, maximum=0.150, value=0.080, step=0.001,
            decimals=3, units="m", title="Cylinder Diameter"
        )
        layout.addWidget(self.cyl_diam_slider)
        
        # Rod diameter - SI units: step 0.001m, decimals=3
        self.rod_diameter_slider = RangeSlider(
            minimum=0.010, maximum=0.060, value=0.035, step=0.001,
            decimals=3, units="m", title="Rod Diameter"
        )
        layout.addWidget(self.rod_diameter_slider)
        
        # Stroke - A-4.3: Enhanced with kinematic limits
        stroke_title = "Stroke"
        if GEOMETRY_STATE_AVAILABLE and hasattr(self, 'geo_state') and self.geo_state:
            computed = self.geo_state.get_computed_values()
            stroke_max_km = computed['stroke_max_kinematic']
            stroke_title += f" (max: {stroke_max_km*1000:.0f}mm kinematic)"
        
        self.stroke_slider = RangeSlider(
            minimum=0.100, maximum=0.500, value=0.300, step=0.001,
            decimals=3, units="m", title=stroke_title
        )
        layout.addWidget(self.stroke_slider)
        
        # Piston thickness - SI units: step 0.001m, decimals=3
        self.piston_thickness_slider = RangeSlider(
            minimum=0.005, maximum=0.030, value=0.020, step=0.001,
            decimals=3, units="m", title="Piston Thickness"
        )
        layout.addWidget(self.piston_thickness_slider)
        
        # Dead gap - SI units: step 0.001m, decimals=3
        self.dead_gap_slider = RangeSlider(
            minimum=0.000, maximum=0.020, value=0.005, step=0.001,
            decimals=3, units="m", title="Dead Gap"
        )
        layout.addWidget(self.dead_gap_slider)
        
        return group
    
    def _create_options_group(self) -> QGroupBox:
        """Create options group"""
        group = QGroupBox("Options")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        
        # Interference checking
        self.interference_check = QCheckBox("Check geometry interference")
        self.interference_check.setChecked(True)
        layout.addWidget(self.interference_check)
        
        # A-4.3: Kinematic constraints checkbox
        if GEOMETRY_STATE_AVAILABLE:
            self.kinematic_check = QCheckBox("Enable kinematic constraints (A-4.3)")
            self.kinematic_check.setChecked(True)
            self.kinematic_check.setToolTip("Use real suspension kinematics to limit stroke")
            layout.addWidget(self.kinematic_check)
        
        # Link rod diameters - deprecated but kept for compatibility
        self.link_rod_diameters = QCheckBox("Diameters unified automatically")
        self.link_rod_diameters.setChecked(True)
        self.link_rod_diameters.setEnabled(False)  # Disabled - always unified now
        self.link_rod_diameters.setToolTip("Cylinder diameter is now unified for both chambers")
        layout.addWidget(self.link_rod_diameters)
        
        return group
    
    def _create_buttons(self) -> QHBoxLayout:
        """Create control buttons - A-4.3: Enhanced validation"""
        layout = QHBoxLayout()
        layout.setSpacing(4)
        
        # Reset to defaults
        self.reset_button = QPushButton("Reset")
        self.reset_button.setToolTip("Reset to default values")
        self.reset_button.clicked.connect(self._reset_to_defaults)
        layout.addWidget(self.reset_button)
        
        # Validate geometry - A-4.3: Enhanced with kinematic validation
        validate_text = "Validate"
        if GEOMETRY_STATE_AVAILABLE:
            validate_text += " (A-4.3)"
        self.validate_button = QPushButton(validate_text)
        self.validate_button.setToolTip("Check geometry correctness including kinematic constraints")
        self.validate_button.clicked.connect(self._validate_geometry)
        layout.addWidget(self.validate_button)
        
        layout.addStretch()
        
        return layout
    
    def _update_kinematic_info(self):
        """A-4.3: Update kinematic information display"""
        if not GEOMETRY_STATE_AVAILABLE or not hasattr(self, 'kinematic_info_label'):
            return
        
        if self.geo_state:
            computed = self.geo_state.get_computed_values()
            stroke_max = computed['stroke_max_kinematic']
            max_angle = computed['max_lever_angle_deg']
            
            info_text = f"Kinematic limits: stroke ? {stroke_max*1000:.0f}mm, lever angle ? {max_angle:.1f}°"
            self.kinematic_info_label.setText(info_text)
        else:
            self.kinematic_info_label.setText("Kinematic limits: not available")

    @Slot(int)
    def _on_preset_changed(self, index: int):
        """Handle preset selection - A-4.3: Using GeometryState presets"""
        if GEOMETRY_STATE_AVAILABLE:
            # A-4.3: Use GeometryState presets
            if index == 0:  # Standard truck
                self.geo_state = create_default_geometry()
            elif index == 1:  # Light commercial
                self.geo_state = create_light_commercial_geometry()
            elif index == 2:  # Heavy truck - create on demand
                from ..geo_state import create_heavy_truck_geometry
                self.geo_state = create_heavy_truck_geometry()
            else:  # Custom - keep current
                pass
                
            if index < 3:  # Apply preset
                params = self.geo_state.get_parameters()
                self.set_parameters(params)
                self._update_kinematic_info()
                self.geometry_updated.emit(params)
        else:
            # Legacy preset handling
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
        """Set default parameter values - A-4.3: Using GeometryState defaults"""
        if GEOMETRY_STATE_AVAILABLE and self.geo_state:
            # A-4.3: Use GeometryState parameters
            self.parameters = self.geo_state.get_parameters()
        else:
            # Legacy defaults
            defaults = {
                'wheelbase': 3.200, 'track': 1.600, 'frame_to_pivot': 0.600,
                'lever_length': 0.800, 'rod_position': 0.600, 'cylinder_length': 0.500,
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
        
        # Cylinder dimensions - unified parameters only
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
        
        # Options
        self.link_rod_diameters.toggled.connect(self._on_link_rod_diameters_toggled)
    
    @Slot(str, float)
    def _on_parameter_changed(self, param_name: str, value: float):
        """Handle parameter change - A-4.3: Enhanced with GeometryState normalization"""
        if self._resolving_conflict or self._updating_from_state:
            return
        
        # Store old values for logging
        old_value = self.parameters.get(param_name, 0.0)
        
        print(f"A-4.3: Parameter changing: {param_name} from {old_value} to {value}")
        
        # A-4.3: Apply through GeometryState if available
        if GEOMETRY_STATE_AVAILABLE and self.geo_state:
            self._apply_ui_change_with_geometry_state(param_name, value)
        else:
            self._apply_ui_change_legacy(param_name, value)
    
    def _apply_ui_change_with_geometry_state(self, param_name: str, value: float):
        """A-4.3: Apply UI change using GeometryState for validation and normalization"""
        
        # Update GeometryState parameter
        if hasattr(self.geo_state, param_name):
            setattr(self.geo_state, param_name, value)
            
            # Validate constraints
            is_valid = self.geo_state.validate_all_constraints()
            errors, warnings = self.geo_state.get_validation_results()
            
            if errors:
                # Show kinematic constraint violations
                error_msg = "Kinematic constraint violations:\n" + "\n".join(errors)
                if warnings:
                    error_msg += "\n\nWarnings:\n" + "\n".join(warnings)
                
                reply = QMessageBox.question(
                    self, 'A-4.3: Kinematic Constraints',
                    error_msg + "\n\nAuto-correct these violations?",
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                
                if reply == QMessageBox.StandardButton.Yes:
                    # Apply auto-correction
                    normalized_value, corrections = self.geo_state.normalize_parameter(param_name, value)
                    if corrections:
                        correction_msg = "Applied corrections:\n" + "\n".join(corrections)
                        QMessageBox.information(self, 'A-4.3: Auto-correction', correction_msg)
                        setattr(self.geo_state, param_name, normalized_value)
                        self._set_parameter_value(param_name, normalized_value)
                        value = normalized_value
                else:
                    # Revert change
                    old_value = self.parameters.get(param_name, 0.0)
                    setattr(self.geo_state, param_name, old_value)
                    self._set_parameter_value(param_name, old_value)
                    return
            
            # Update internal parameters from GeometryState
            self.parameters = self.geo_state.get_parameters()
            
            # Update kinematic info display
            self._update_kinematic_info()
            
            # Emit signals
            self.parameter_changed.emit(param_name, value)
            self.geometry_updated.emit(self.parameters.copy())
            self._emit_3d_geometry_update()
            
        else:
            print(f"Warning: Parameter {param_name} not found in GeometryState")
            self._apply_ui_change_legacy(param_name, value)
    
    def _apply_ui_change_legacy(self, param_name: str, value: float):
        """Legacy path for UI changes (when GeometryState not available)"""
        # Store new value
        old_value = self.parameters.get(param_name, 0.0)
        self.parameters[param_name] = value
        
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
            # Unified cylinder parameters (convert from SI meters to mm for QML)
            'boreHead': self.parameters.get('cyl_diam_m', 0.080) * 1000,  # m -> mm
            'boreRod': self.parameters.get('cyl_diam_m', 0.080) * 1000,   # Same as boreHead now! 
            'rodDiameter': self.parameters.get('rod_diam_m', 0.035) * 1000,  # m -> mm
            'pistonThickness': self.parameters.get('piston_thickness_m', 0.020) * 1000,  # m -> mm
            # Additional parameters for 3D scene
            'strokeLength': self.parameters.get('stroke_m', 0.300) * 1000,  # m -> mm
            'deadGap': self.parameters.get('dead_gap_m', 0.005) * 1000,  # m -> mm
        }
        
        print(f"Emitting geometry_changed signal with {len(geometry_3d)} parameters")
        self.geometry_changed.emit(geometry_3d)
    
    def _check_dependencies(self, param_name: str, new_value: float, old_value: float) -> dict:
        """Check parameter dependencies (legacy)"""
        # A-4.3: Skip legacy checks if GeometryState is handling validation
        if GEOMETRY_STATE_AVAILABLE and self.geo_state:
            return None
            
        # Legacy dependency checking code...
        if param_name in ['wheelbase', 'lever_length', 'frame_to_pivot']:
            wheelbase = self.parameters['wheelbase']
            lever_length = self.parameters['lever_length']
            frame_to_pivot = self.parameters['frame_to_pivot']
            
            max_lever_reach = wheelbase / 2.0 - 0.100
            
            if frame_to_pivot + lever_length > max_lever_reach:
                return {
                    'type': 'geometric_constraint',
                    'message': f'Lever geometry exceeds available space.\nCurrent: {frame_to_pivot + lever_length:.3f}m\nMaximum: {max_lever_reach:.3f}m',
                    'options': [
                        ('Reduce lever length', 'lever_length', max_lever_reach - frame_to_pivot - 0.001),
                        ('Reduce distance to axis', 'frame_to_pivot', max_lever_reach - lever_length - 0.001),
                        ('Increase wheelbase', 'wheelbase', 2.0 * (frame_to_pivot + lever_length + 0.150))
                    ],
                    'changed_param': param_name
                }
        
        if param_name in ['rod_diam_m', 'cyl_diam_m']:
            rod_diameter = self.parameters['rod_diam_m']
            cyl_diameter = self.parameters['cyl_diam_m']
            
            if rod_diameter >= cyl_diameter * 0.8:
                return {
                    'type': 'hydraulic_constraint',
                    'message': f'Rod diameter too large relative to cylinder.\nRod: {rod_diameter*1000:.1f}mm\nCylinder: {cyl_diameter*1000:.1f}mm\nMax rod: {cyl_diameter*0.8*1000:.1f}mm',
                    'options': [
                        ('Reduce rod diameter', 'rod_diam_m', cyl_diameter * 0.700),
                        ('Increase cylinder diameter', 'cyl_diam_m', rod_diameter / 0.700),
                    },
                    'changed_param': param_name
                }
        
        return None
    
    def _resolve_conflict(self, conflict_info: dict):
        """Show conflict resolution dialog (legacy)"""
        self._resolving_conflict = True
        
        try:
            # Create message box with options
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle('Parameter Conflict')
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
            # A-4.3: Block signals during programmatic updates
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
        """Reset all parameters to defaults - A-4.3: Using GeometryState"""
        if GEOMETRY_STATE_AVAILABLE:
            # A-4.3: Create fresh GeometryState
            self.geo_state = create_default_geometry()
            self.parameters = self.geo_state.get_parameters()
            self._update_kinematic_info()
        else:
            # Legacy defaults
            self._set_default_values()
        
        # Update all widgets
        self.wheelbase_slider.setValue(self.parameters['wheelbase'])
        self.track_slider.setValue(self.parameters['track'])
        self.frame_to_pivot_slider.setValue(self.parameters['frame_to_pivot'])
        self.lever_length_slider.setValue(self.parameters['lever_length'])
        self.rod_position_slider.setValue(self.parameters['rod_position'])
        self.cylinder_length_slider.setValue(self.parameters['cylinder_length'])
        
        # Set values for unified parameters
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
        """Validate current geometry settings - A-4.3: Enhanced with kinematic validation"""
        if GEOMETRY_STATE_AVAILABLE and self.geo_state:
            # A-4.3: Use GeometryState validation
            is_valid = self.geo_state.validate_all_constraints()
            errors, warnings = self.geo_state.get_validation_results()
            computed = self.geo_state.get_computed_values() 
            
            # Create comprehensive validation message
            msg = "A-4.3: Kinematic Constraint Validation\n\n"
            
            # Show computed values
            msg += f"Computed values:\n"
            msg += f"• Max stroke (kinematic): {computed['stroke_max_kinematic']*1000:.1f}mm\n"
            msg += f"• Max lever angle: {computed['max_lever_angle_deg']:.1f}°\n"
            msg += f"• Current stroke: {self.geo_state.stroke_m*1000:.1f}mm\n\n"
            
            if errors:
                msg += f"? {len(errors)} ERRORS:\n"
                for error in errors:
                    msg += f"• {error}\n"
                msg += "\n"
            
            if warnings:
                msg += f"?? {len(warnings)} WARNINGS:\n"
                for warning in warnings:
                    msg += f"• {warning}\n"
                msg += "\n"
            
            if not errors and not warnings:
                msg += "? All constraints satisfied!\n"
                msg += "Geometry is kinematically valid."
            
            # Show appropriate message box
            if errors:
                QMessageBox.critical(self, 'A-4.3: Kinematic Validation', msg)
            elif warnings:
                QMessageBox.warning(self, 'A-4.3: Kinematic Validation', msg)
            else:
                QMessageBox.information(self, 'A-4.3: Kinematic Validation', msg)
                
        else:
            # Legacy validation
            self._validate_geometry_legacy()
    
    def _validate_geometry_legacy(self):
        """Legacy validation method"""
        errors = []
        warnings = []
        
        # Legacy validation code...
        wheelbase = self.parameters['wheelbase']
        lever_length = self.parameters['lever_length']
        frame_to_pivot = self.parameters['frame_to_pivot']
        
        max_lever_reach = wheelbase / 2.0 - 0.100
        if frame_to_pivot + lever_length > max_lever_reach:
            errors.append(f"Lever geometry exceeds space: {frame_to_pivot + lever_length:.3f} > {max_lever_reach:.3f}m")
        
        rod_diameter = self.parameters['rod_diam_m']
        cyl_diameter = self.parameters['cyl_diam_m']
        
        if rod_diameter >= cyl_diameter * 0.8:
            errors.append(f"Rod too large: {rod_diameter*1000:.1f}mm >= 80% of {cyl_diameter*1000:.1f}mm cylinder")
        elif rod_diameter >= cyl_diameter * 0.7:
            warnings.append(f"Rod close to limit: {rod_diameter*1000:.1f}mm vs {cyl_diameter*1000:.1f}mm cylinder")
        
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
            QMessageBox.critical(self, 'Geometry Errors', 
                               'Errors found:\n' + '\n'.join(errors))
        elif warnings:
            QMessageBox.warning(self, 'Geometry Warnings',
                              'Warnings:\n' + '\n'.join(warnings))
        else:
            QMessageBox.information(self, 'Geometry Check', 
                                  'All geometry parameters are correct.')
    
    def get_parameters(self) -> dict:
        """Get current parameter values"""
        return self.parameters.copy()
    
    def set_parameters(self, params: dict):
        """Set parameter values from dictionary"""
        self._resolving_conflict = True
        
        try:
            # A-4.3: Update GeometryState if available
            if GEOMETRY_STATE_AVAILABLE and self.geo_state:
                self.geo_state.set_parameters(params)
                self.parameters = self.geo_state.get_parameters()
                self._update_kinematic_info()
            else:
                # Update internal storage
                self.parameters.update(params)
            
            # Update widgets
            for param_name, value in params.items():
                self._set_parameter_value(param_name, value)
        
        finally:
            self._resolving_conflict = False
    
    @Slot(bool)
    def _on_link_rod_diameters_toggled(self, checked: bool):
        """Handle linking/unlinking of rod diameters"""
        # NOTE: With unified cylinder diameter (cyl_diam_m), this option is no longer relevant
        if checked:
            print("Rod diameters already unified (single cyl_diam_m parameter)")
        else:
            print("Rod diameters are always unified now (single cyl_diam_m parameter)")