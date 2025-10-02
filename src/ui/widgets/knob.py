"""
Universal knob widget for PySide6
Combines QDial with QDoubleSpinBox for precise value control
"""

from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                              QDial, QDoubleSpinBox, QSizePolicy)
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QFont
import math


class Knob(QWidget):
    """Universal rotary knob with value display and units
    
    Combines QDial for intuitive rotation with QDoubleSpinBox for precise input.
    Supports arbitrary float ranges with automatic scaling.
    """
    
    # Signals
    valueChanged = Signal(float)  # Emitted when value changes
    
    def __init__(self, 
                 minimum: float = 0.0,
                 maximum: float = 100.0,
                 value: float = 0.0,
                 step: float = 1.0,
                 decimals: int = 2,
                 units: str = "",
                 title: str = "",
                 parent=None):
        """Initialize knob widget
        
        Args:
            minimum: Minimum value
            maximum: Maximum value
            value: Initial value
            step: Step size for adjustments
            decimals: Number of decimal places to display
            units: Units string (e.g., "bar", "mm", "°")
            title: Title label above knob
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Parameters
        self._minimum = minimum
        self._maximum = maximum
        self._step = step
        self._decimals = decimals
        self._units = units
        self._dial_resolution = 1000  # Internal dial resolution
        
        # Create UI
        self._setup_ui(title)
        
        # Set initial value
        self.setValue(value)
        
        # Connect signals
        self._connect_signals()
        
        # Size policy
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
    
    def _setup_ui(self, title: str):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Title label
        if title:
            self.title_label = QLabel(title)
            self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            font = QFont()
            font.setPointSize(8)
            font.setBold(True)
            self.title_label.setFont(font)
            layout.addWidget(self.title_label)
        
        # Dial widget
        self.dial = QDial()
        self.dial.setMinimum(0)
        self.dial.setMaximum(self._dial_resolution)
        self.dial.setNotchesVisible(True)
        self.dial.setWrapping(False)
        self.dial.setMinimumSize(80, 80)
        self.dial.setMaximumSize(120, 120)
        layout.addWidget(self.dial)
        
        # Value display and input
        value_layout = QHBoxLayout()
        value_layout.setSpacing(2)
        
        self.spinbox = QDoubleSpinBox()
        self.spinbox.setMinimum(self._minimum)
        self.spinbox.setMaximum(self._maximum)
        self.spinbox.setSingleStep(self._step)
        self.spinbox.setDecimals(self._decimals)
        self.spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.spinbox.setMaximumWidth(80)
        
        value_layout.addWidget(self.spinbox)
        
        # Units label
        if self._units:
            self.units_label = QLabel(self._units)
            font = QFont()
            font.setPointSize(8)
            self.units_label.setFont(font)
            self.units_label.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            value_layout.addWidget(self.units_label)
        
        layout.addLayout(value_layout)
    
    def _connect_signals(self):
        """Connect internal signals"""
        self.dial.valueChanged.connect(self._on_dial_changed)
        self.spinbox.valueChanged.connect(self._on_spinbox_changed)
    
    def _value_to_dial(self, value: float) -> int:
        """Convert real value to dial position"""
        if self._maximum <= self._minimum:
            return 0
        
        # Clamp value
        value = max(self._minimum, min(self._maximum, value))
        
        # Scale to dial range
        ratio = (value - self._minimum) / (self._maximum - self._minimum)
        return int(ratio * self._dial_resolution)
    
    def _dial_to_value(self, dial_pos: int) -> float:
        """Convert dial position to real value"""
        # Scale from dial range
        ratio = dial_pos / self._dial_resolution
        value = self._minimum + ratio * (self._maximum - self._minimum)
        
        # Round to step if specified
        if self._step > 0:
            steps = round((value - self._minimum) / self._step)
            value = self._minimum + steps * self._step
        
        return max(self._minimum, min(self._maximum, value))
    
    @Slot(int)
    def _on_dial_changed(self, dial_value: int):
        """Handle dial value change"""
        real_value = self._dial_to_value(dial_value)
        
        # Update spinbox without triggering its signal
        self.spinbox.blockSignals(True)
        self.spinbox.setValue(real_value)
        self.spinbox.blockSignals(False)
        
        # Emit our signal
        self.valueChanged.emit(real_value)
    
    @Slot(float)
    def _on_spinbox_changed(self, spinbox_value: float):
        """Handle spinbox value change"""
        # Update dial without triggering its signal
        dial_pos = self._value_to_dial(spinbox_value)
        self.dial.blockSignals(True)
        self.dial.setValue(dial_pos)
        self.dial.blockSignals(False)
        
        # Emit our signal
        self.valueChanged.emit(spinbox_value)
    
    def setValue(self, value: float):
        """Set knob value
        
        Args:
            value: New value
        """
        value = max(self._minimum, min(self._maximum, value))
        
        # Update both widgets
        dial_pos = self._value_to_dial(value)
        
        self.dial.blockSignals(True)
        self.spinbox.blockSignals(True)
        
        self.dial.setValue(dial_pos)
        self.spinbox.setValue(value)
        
        self.dial.blockSignals(False)
        self.spinbox.blockSignals(False)
    
    def value(self) -> float:
        """Get current value
        
        Returns:
            Current value
        """
        return self.spinbox.value()
    
    def setRange(self, minimum: float, maximum: float, step: float = None):
        """Set value range
        
        Args:
            minimum: New minimum value
            maximum: New maximum value
            step: New step size (optional)
        """
        if maximum <= minimum:
            raise ValueError("Maximum must be greater than minimum")
        
        current_value = self.value()
        
        self._minimum = minimum
        self._maximum = maximum
        
        if step is not None:
            self._step = step
        
        # Update spinbox range
        self.spinbox.setMinimum(minimum)
        self.spinbox.setMaximum(maximum)
        if step is not None:
            self.spinbox.setSingleStep(step)
        
        # Restore value (clamped to new range)
        self.setValue(current_value)
    
    def setDecimals(self, decimals: int):
        """Set number of decimal places
        
        Args:
            decimals: Number of decimal places
        """
        self._decimals = decimals
        self.spinbox.setDecimals(decimals)
    
    def setUnits(self, units: str):
        """Set units label
        
        Args:
            units: Units string
        """
        self._units = units
        if hasattr(self, 'units_label'):
            self.units_label.setText(units)
    
    def setEnabled(self, enabled: bool):
        """Enable/disable the knob
        
        Args:
            enabled: True to enable, False to disable
        """
        super().setEnabled(enabled)
        self.dial.setEnabled(enabled)
        self.spinbox.setEnabled(enabled)
    
    def minimum(self) -> float:
        """Get minimum value"""
        return self._minimum
    
    def maximum(self) -> float:
        """Get maximum value"""
        return self._maximum
    
    def step(self) -> float:
        """Get step size"""
        return self._step