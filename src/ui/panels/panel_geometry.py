"""
Geometry configuration panel
Controls for vehicle geometry parameters with dependency management
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, 
                              QCheckBox, QPushButton, QLabel, QMessageBox,
                              QSizePolicy)
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QFont

from ..widgets import RangeSlider


class GeometryPanel(QWidget):
    """Panel for geometry parameter configuration
    
    Provides controls for:
    - Wheelbase and track dimensions
    - Lever geometry (length, pivot distances)
    - Cylinder dimensions (bore, stroke, rod diameter)
    - Dead zones and clearances
    
    Includes automatic dependency resolution for conflicting parameters.
    """
    
    # Signals for parameter changes
    parameter_changed = Signal(str, float)  # parameter_name, new_value
    geometry_updated = Signal(dict)         # Complete geometry dictionary
    geometry_changed = Signal(dict)         # 3D scene geometry update (NEW!)
    
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
        title_label = QLabel("Vehicle Geometry")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)
        
        # Frame dimensions group
        frame_group = self._create_frame_group()
        layout.addWidget(frame_group)
        
        # Suspension geometry group
        suspension_group = self._create_suspension_group()
        layout.addWidget(suspension_group)
        
        # Cylinder geometry group
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
        group = QGroupBox("Frame Dimensions")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        
        # Wheelbase
        self.wheelbase_slider = RangeSlider(
            minimum=2.0, maximum=4.0, value=3.2, step=0.1,
            decimals=1, units="m", title="Wheelbase"
        )
        layout.addWidget(self.wheelbase_slider)
        
        # Track width
        self.track_slider = RangeSlider(
            minimum=1.0, maximum=2.5, value=1.6, step=0.1,
            decimals=1, units="m", title="Track Width"
        )
        layout.addWidget(self.track_slider)
        
        return group
    
    def _create_suspension_group(self) -> QGroupBox:
        """Create suspension geometry group"""
        group = QGroupBox("Suspension Geometry")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        
        # Distance from frame to lever pivot
        self.frame_to_pivot_slider = RangeSlider(
            minimum=0.3, maximum=1.0, value=0.6, step=0.05,
            decimals=2, units="m", title="Frame to Pivot Distance"
        )
        layout.addWidget(self.frame_to_pivot_slider)
        
        # Lever length
        self.lever_length_slider = RangeSlider(
            minimum=0.5, maximum=1.5, value=0.8, step=0.05,
            decimals=2, units="m", title="Lever Length"
        )
        layout.addWidget(self.lever_length_slider)
        
        # Rod attachment position (fraction of lever length)
        self.rod_position_slider = RangeSlider(
            minimum=0.3, maximum=0.9, value=0.6, step=0.05,
            decimals=2, units="", title="Rod Attachment Position (fraction)"
        )
        layout.addWidget(self.rod_position_slider)
        
        return group
    
    def _create_cylinder_group(self) -> QGroupBox:
        """Create cylinder geometry group"""
        group = QGroupBox("Cylinder Dimensions")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        
        # Cylinder length
        self.cylinder_length_slider = RangeSlider(
            minimum=0.3, maximum=0.8, value=0.5, step=0.01,
            decimals=2, units="m", title="Cylinder Length"
        )
        layout.addWidget(self.cylinder_length_slider)
        
        # Bore diameter (head side)
        self.bore_head_slider = RangeSlider(
            minimum=50.0, maximum=150.0, value=80.0, step=5.0,
            decimals=0, units="mm", title="Head Side Bore Diameter"
        )
        layout.addWidget(self.bore_head_slider)
        
        # Bore diameter (rod side) 
        self.bore_rod_slider = RangeSlider(
            minimum=50.0, maximum=150.0, value=80.0, step=5.0,
            decimals=0, units="mm", title="Rod Side Bore Diameter"
        )
        layout.addWidget(self.bore_rod_slider)
        
        # Rod diameter
        self.rod_diameter_slider = RangeSlider(
            minimum=20.0, maximum=60.0, value=35.0, step=2.5,
            decimals=1, units="mm", title="Rod Diameter"
        )
        layout.addWidget(self.rod_diameter_slider)
        
        # Piston rod length (NEW!)
        self.piston_rod_length_slider = RangeSlider(
            minimum=100.0, maximum=500.0, value=200.0, step=10.0,
            decimals=0, units="mm", title="Piston Rod Length"
        )
        layout.addWidget(self.piston_rod_length_slider)
        
        # Piston thickness
        self.piston_thickness_slider = RangeSlider(
            minimum=10.0, maximum=50.0, value=25.0, step=2.5,
            decimals=1, units="mm", title="Piston Thickness"
        )
        layout.addWidget(self.piston_thickness_slider)
        
        return group
    
    def _create_options_group(self) -> QGroupBox:
        """Create options group"""
        group = QGroupBox("Options")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        
        # Interference checking
        self.interference_check = QCheckBox("Enable Interference Checking")
        self.interference_check.setChecked(True)
        layout.addWidget(self.interference_check)
        
        # Link rod diameters
        self.link_rod_diameters = QCheckBox("Link Front/Rear Rod Diameters")
        self.link_rod_diameters.setChecked(False)
        layout.addWidget(self.link_rod_diameters)
        
        return group
    
    def _create_buttons(self) -> QHBoxLayout:
        """Create control buttons"""
        layout = QHBoxLayout()
        layout.setSpacing(4)
        
        # Reset to defaults
        self.reset_button = QPushButton("Reset to Defaults")
        self.reset_button.clicked.connect(self._reset_to_defaults)
        layout.addWidget(self.reset_button)
        
        # Validate geometry
        self.validate_button = QPushButton("Validate Geometry")
        self.validate_button.clicked.connect(self._validate_geometry)
        layout.addWidget(self.validate_button)
        
        layout.addStretch()
        
        return layout
    
    def _set_default_values(self):
        """Set default parameter values"""
        defaults = {
            'wheelbase': 3.2,
            'track': 1.6,
            'frame_to_pivot': 0.6,
            'lever_length': 0.8,
            'rod_position': 0.6,
            'cylinder_length': 0.5,
            'bore_head': 80.0,
            'bore_rod': 80.0,
            'rod_diameter': 35.0,
            'piston_rod_length': 200.0,  # NEW: Default 200mm rod length
            'piston_thickness': 25.0
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
        
        # Cylinder dimensions
        self.cylinder_length_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('cylinder_length', v))
        self.bore_head_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('bore_head', v))
        self.bore_rod_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('bore_rod', v))
        self.rod_diameter_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('rod_diameter', v))
        self.piston_rod_length_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('piston_rod_length', v))
        self.piston_thickness_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('piston_thickness', v))
        
        # Options
        self.link_rod_diameters.toggled.connect(self._on_link_rod_diameters_toggled)
    
    @Slot(str, float)
    def _on_parameter_changed(self, param_name: str, value: float):
        """Handle parameter change with dependency resolution
        
        Args:
            param_name: Name of changed parameter
            value: New value
        """
        if self._resolving_conflict:
            return
        
        # Store new value
        old_value = self.parameters.get(param_name, 0.0)
        self.parameters[param_name] = value
        
        print(f"???????????????????????????????????????????????")
        print(f"?? GeometryPanel: Parameter changed")
        print(f"   Name: {param_name}")
        print(f"   Old value: {old_value}")
        print(f"   New value: {value}")
        print(f"   All parameters: {self.parameters}")
        print(f"???????????????????????????????????????????????")
        
        # Check for dependencies and conflicts
        conflict_resolution = self._check_dependencies(param_name, value, old_value)
        
        if conflict_resolution:
            # Show conflict resolution dialog
            self._resolve_conflict(conflict_resolution)
        else:
            # No conflicts, emit signals
            self.parameter_changed.emit(param_name, value)
            self.geometry_updated.emit(self.parameters.copy())
            
            # NEW: Emit 3D scene geometry update for frame dimensions
            if param_name in ['wheelbase', 'track', 'lever_length', 'cylinder_length', 'frame_to_pivot', 'rod_position', 
                             'bore_head', 'bore_rod', 'rod_diameter', 'piston_rod_length', 'piston_thickness']:
                # Convert parameters to 3D scene format
                geometry_3d = {
                    'frameLength': self.parameters.get('wheelbase', 3.2) * 1000,  # m -> mm
                    'frameHeight': 650.0,  # Fixed for now
                    'frameBeamSize': 120.0,  # Fixed for now
                    'leverLength': self.parameters.get('lever_length', 0.8) * 1000,  # m -> mm
                    'cylinderBodyLength': self.parameters.get('cylinder_length', 0.5) * 1000,  # m -> mm
                    'tailRodLength': 100.0,  # Fixed for now
                    # NEW: Additional parameters
                    'trackWidth': self.parameters.get('track', 1.6) * 1000,  # m -> mm
                    'frameToPivot': self.parameters.get('frame_to_pivot', 0.6) * 1000,  # m -> mm
                    'rodPosition': self.parameters.get('rod_position', 0.6),  # fraction 0-1
                    'boreHead': self.parameters.get('bore_head', 80.0),  # mm
                    'boreRod': self.parameters.get('bore_rod', 80.0),  # mm
                    'rodDiameter': self.parameters.get('rod_diameter', 35.0),  # mm
                    'pistonRodLength': self.parameters.get('piston_rod_length', 200.0),  # mm - NEW!
                    'pistonThickness': self.parameters.get('piston_thickness', 25.0)  # mm
                }
                
                print(f"???????????????????????????????????????????????")
                print(f"?? GeometryPanel: Emitting geometry_changed signal")
                print(f"   Converted to 3D format:")
                for key, val in geometry_3d.items():
                    print(f"      {key}: {val}")
                print(f"???????????????????????????????????????????????")
                
                self.geometry_changed.emit(geometry_3d)
    
    def _check_dependencies(self, param_name: str, new_value: float, old_value: float) -> dict:
        """Check for parameter dependencies and conflicts
        
        Args:
            param_name: Name of changed parameter
            new_value: New value
            old_value: Previous value
            
        Returns:
            Dictionary with conflict information, or None if no conflicts
        """
        # Geometric constraints that may cause conflicts
        
        # Example: wheelbase vs lever geometry
        if param_name in ['wheelbase', 'lever_length', 'frame_to_pivot']:
            wheelbase = self.parameters['wheelbase']
            lever_length = self.parameters['lever_length']
            frame_to_pivot = self.parameters['frame_to_pivot']
            
            # Check if lever can physically fit
            max_lever_reach = wheelbase / 2.0 - 0.1  # Leave some clearance
            
            if frame_to_pivot + lever_length > max_lever_reach:
                return {
                    'type': 'geometric_constraint',
                    'message': f'Lever geometry exceeds available space.\n'
                              f'Current: {frame_to_pivot + lever_length:.2f}m\n'
                              f'Maximum: {max_lever_reach:.2f}m',
                    'options': [
                        ('Reduce lever length', 'lever_length', max_lever_reach - frame_to_pivot),
                        ('Reduce frame-to-pivot distance', 'frame_to_pivot', max_lever_reach - lever_length),
                        ('Increase wheelbase', 'wheelbase', 2.0 * (frame_to_pivot + lever_length + 0.1))
                    ],
                    'changed_param': param_name
                }
        
        # Rod diameter vs bore diameter constraint
        if param_name in ['rod_diameter', 'bore_head', 'bore_rod']:
            rod_diameter = self.parameters['rod_diameter']
            min_bore = min(self.parameters['bore_head'], self.parameters['bore_rod'])
            
            if rod_diameter >= min_bore * 0.8:  # Rod should be < 80% of bore
                return {
                    'type': 'hydraulic_constraint',
                    'message': f'Rod diameter too large relative to bore.\n'
                              f'Rod: {rod_diameter:.1f}mm\n'
                              f'Min bore: {min_bore:.1f}mm',
                    'options': [
                        ('Reduce rod diameter', 'rod_diameter', min_bore * 0.7),
                        ('Increase bore diameters', 'bore_head', rod_diameter / 0.7),
                    ],
                    'changed_param': param_name
                }
        
        return None
    
    def _resolve_conflict(self, conflict_info: dict):
        """Show conflict resolution dialog
        
        Args:
            conflict_info: Conflict information dictionary
        """
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
    
    def _get_widget_for_parameter(self, param_name: str) -> RangeSlider:
        """Get widget for parameter name"""
        widget_map = {
            'wheelbase': self.wheelbase_slider,
            'track': self.track_slider,
            'frame_to_pivot': self.frame_to_pivot_slider,
            'lever_length': self.lever_length_slider,
            'rod_position': self.rod_position_slider,
            'cylinder_length': self.cylinder_length_slider,
            'bore_head': self.bore_head_slider,
            'bore_rod': self.bore_rod_slider,
            'rod_diameter': self.rod_diameter_slider,
            'piston_rod_length': self.piston_rod_length_slider,
            'piston_thickness': self.piston_thickness_slider
        }
        return widget_map.get(param_name)
    
    def _set_parameter_value(self, param_name: str, value: float):
        """Set parameter value in appropriate widget"""
        widget = self._get_widget_for_parameter(param_name)
        if widget:
            widget.setValue(value)
    
    @Slot(bool)
    def _on_link_rod_diameters_toggled(self, checked: bool):
        """Handle rod diameter linking toggle"""
        if checked:
            # Link rod diameters - set rear to match front
            front_diameter = self.rod_diameter_slider.value()
            # For now, we only have one rod diameter control
            # In a full implementation, we'd have separate front/rear controls
            pass
    
    @Slot()
    def _reset_to_defaults(self):
        """Reset all parameters to default values"""
        self._set_default_values()
        
        # Update all widgets
        self.wheelbase_slider.setValue(self.parameters['wheelbase'])
        self.track_slider.setValue(self.parameters['track'])
        self.frame_to_pivot_slider.setValue(self.parameters['frame_to_pivot'])
        self.lever_length_slider.setValue(self.parameters['lever_length'])
        self.rod_position_slider.setValue(self.parameters['rod_position'])
        self.cylinder_length_slider.setValue(self.parameters['cylinder_length'])
        self.bore_head_slider.setValue(self.parameters['bore_head'])
        self.bore_rod_slider.setValue(self.parameters['bore_rod'])
        self.rod_diameter_slider.setValue(self.parameters['rod_diameter'])
        self.piston_rod_length_slider.setValue(self.parameters['piston_rod_length'])
        self.piston_thickness_slider.setValue(self.parameters['piston_thickness'])
        
        # Reset checkboxes
        self.interference_check.setChecked(True)
        self.link_rod_diameters.setChecked(False)
        
        # Emit update
        self.geometry_updated.emit(self.parameters.copy())
    
    @Slot()
    def _validate_geometry(self):
        """Validate current geometry settings"""
        errors = []
        warnings = []
        
        # Check geometric constraints
        wheelbase = self.parameters['wheelbase']
        lever_length = self.parameters['lever_length']
        frame_to_pivot = self.parameters['frame_to_pivot']
        
        max_lever_reach = wheelbase / 2.0 - 0.1
        if frame_to_pivot + lever_length > max_lever_reach:
            errors.append(f"Lever geometry exceeds available space: {frame_to_pivot + lever_length:.2f} > {max_lever_reach:.2f}m")
        
        # Check hydraulic constraints
        rod_diameter = self.parameters['rod_diameter']
        min_bore = min(self.parameters['bore_head'], self.parameters['bore_rod'])
        
        if rod_diameter >= min_bore * 0.8:
            errors.append(f"Rod diameter too large: {rod_diameter:.1f}mm >= 80% of {min_bore:.1f}mm bore")
        elif rod_diameter >= min_bore * 0.7:
            warnings.append(f"Rod diameter approaching limit: {rod_diameter:.1f}mm vs {min_bore:.1f}mm bore")
        
        # Show results
        if errors:
            QMessageBox.critical(self, 'Geometry Validation Failed', 
                               'Errors found:\n' + '\n'.join(errors))
        elif warnings:
            QMessageBox.warning(self, 'Geometry Validation Warnings',
                              'Warnings:\n' + '\n'.join(warnings))
        else:
            QMessageBox.information(self, 'Geometry Validation', 
                                  'All geometry parameters are valid.')
    
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
        self._resolving_conflict = True
        
        try:
            # Update internal storage
            self.parameters.update(params)
            
            # Update widgets
            for param_name, value in params.items():
                self._set_parameter_value(param_name, value)
        
        finally:
            self._resolving_conflict = False