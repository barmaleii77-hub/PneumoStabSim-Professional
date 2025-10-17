# -*- coding: utf-8 -*-
"""
Suspension geometry tab - Вкладка геометрии подвески
Controls for lever geometry and suspension layout
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox
from PySide6.QtCore import Signal

from ...widgets import RangeSlider
from .state_manager import GeometryStateManager
from .defaults import get_parameter_limits, get_parameter_metadata


class SuspensionTab(QWidget):
    """Вкладка геометрии подвески
    
    Suspension geometry configuration tab
    
    Controls:
    - Frame to pivot distance (расстояние рама → ось рычага)
    - Lever length (длина рычага)
    - Rod position on lever (положение крепления штока)
    """
    
    # Signals
    parameter_changed = Signal(str, float)
    parameter_live_changed = Signal(str, float)
    
    def __init__(self, state_manager: GeometryStateManager, parent=None):
        """Initialize suspension tab
        
        Args:
            state_manager: Shared state manager
            parent: Parent widget
        """
        super().__init__(parent)
        
        self.state_manager = state_manager
        
        self._setup_ui()
        self._load_from_state()
        self._connect_signals()
    
    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)
        
        group = QGroupBox("Геометрия подвески")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(4)
        
        # Frame to pivot distance
        limits = get_parameter_limits('frame_to_pivot')
        metadata = get_parameter_metadata('frame_to_pivot')
        
        self.frame_to_pivot_slider = RangeSlider(
            minimum=limits['min'],
            maximum=limits['max'],
            value=self.state_manager.get_parameter('frame_to_pivot'),
            step=limits['step'],
            decimals=limits['decimals'],
            units=metadata['units'],
            title=metadata['title']
        )
        self.frame_to_pivot_slider.setToolTip(metadata['description'])
        group_layout.addWidget(self.frame_to_pivot_slider)
        
        # Lever length
        limits = get_parameter_limits('lever_length')
        metadata = get_parameter_metadata('lever_length')
        
        self.lever_length_slider = RangeSlider(
            minimum=limits['min'],
            maximum=limits['max'],
            value=self.state_manager.get_parameter('lever_length'),
            step=limits['step'],
            decimals=limits['decimals'],
            units=metadata['units'],
            title=metadata['title']
        )
        self.lever_length_slider.setToolTip(metadata['description'])
        group_layout.addWidget(self.lever_length_slider)
        
        # Rod position on lever
        limits = get_parameter_limits('rod_position')
        metadata = get_parameter_metadata('rod_position')
        
        self.rod_position_slider = RangeSlider(
            minimum=limits['min'],
            maximum=limits['max'],
            value=self.state_manager.get_parameter('rod_position'),
            step=limits['step'],
            decimals=limits['decimals'],
            units=metadata['units'],
            title=metadata['title']
        )
        self.rod_position_slider.setToolTip(metadata['description'])
        group_layout.addWidget(self.rod_position_slider)
        
        layout.addWidget(group)
        layout.addStretch()
    
    def _connect_signals(self):
        """Connect widget signals"""
        # Frame to pivot
        self.frame_to_pivot_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('frame_to_pivot', v)
        )
        self.frame_to_pivot_slider.valueChanged.connect(
            lambda v: self._on_parameter_live_changed('frame_to_pivot', v)
        )
        
        # Lever length
        self.lever_length_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('lever_length', v)
        )
        self.lever_length_slider.valueChanged.connect(
            lambda v: self._on_parameter_live_changed('lever_length', v)
        )
        
        # Rod position
        self.rod_position_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed('rod_position', v)
        )
        self.rod_position_slider.valueChanged.connect(
            lambda v: self._on_parameter_live_changed('rod_position', v)
        )
    
    def _on_parameter_changed(self, param_name: str, value: float):
        """Handle parameter change (final)"""
        self.state_manager.set_parameter(param_name, value)
        self.parameter_changed.emit(param_name, value)
    
    def _on_parameter_live_changed(self, param_name: str, value: float):
        """Handle parameter change (real-time)"""
        self.state_manager.set_parameter(param_name, value)
        self.parameter_live_changed.emit(param_name, value)
    
    def _load_from_state(self):
        """Load values from state manager"""
        frame_to_pivot = self.state_manager.get_parameter('frame_to_pivot')
        lever_length = self.state_manager.get_parameter('lever_length')
        rod_position = self.state_manager.get_parameter('rod_position')
        
        if frame_to_pivot is not None:
            self.frame_to_pivot_slider.setValue(frame_to_pivot)
        
        if lever_length is not None:
            self.lever_length_slider.setValue(lever_length)
        
        if rod_position is not None:
            self.rod_position_slider.setValue(rod_position)
    
    def update_from_state(self):
        """Update widgets from current state"""
        self._load_from_state()
    
    def set_enabled(self, enabled: bool):
        """Enable/disable all controls"""
        self.frame_to_pivot_slider.setEnabled(enabled)
        self.lever_length_slider.setEnabled(enabled)
        self.rod_position_slider.setEnabled(enabled)
