"""
Range slider widget with editable min/max bounds
Combines QSlider with QDoubleSpinBox controls for precise range control
"""

from PySide6.QtWidgets import (QWidget, QHBoxLayout, QVBoxLayout, QLabel, 
                              QSlider, QDoubleSpinBox, QSizePolicy)
from PySide6.QtCore import Signal, Slot, QTimer, Qt
from PySide6.QtGui import QFont
import math


class RangeSlider(QWidget):
    """Slider with editable min/max range and precise value control
    
    Provides a horizontal slider with separate spinboxes for min, current value, and max.
    Includes debounced value change signals and automatic range validation.
    """
    
    # Signals
    valueEdited = Signal(float)  # Emitted after value stabilizes (debounced)
    valueChanged = Signal(float)  # Emitted on every change (immediate)
    rangeChanged = Signal(float, float)  # Emitted when min/max changes
    
    def __init__(self,
                 minimum: float = 0.0,
                 maximum: float = 100.0,
                 value: float = 50.0,
                 step: float = 1.0,
                 decimals: int = 2,
                 units: str = "",
                 title: str = "",
                 parent=None):
        """Initialize range slider
        
        Args:
            minimum: Initial minimum value
            maximum: Initial maximum value
            value: Initial value
            step: Step size for adjustments
            decimals: Number of decimal places
            units: Units string
            title: Title label
            parent: Parent widget
        """
        super().__init__(parent)
        
        # Parameters
        self._step = step
        self._decimals = decimals
        self._units = units
        self._slider_resolution = 10000  # High resolution for smooth sliding
        self._updating_internally = False
        
        # Debounce timer for valueEdited signal
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._emit_value_edited)
        self._debounce_delay = 200  # ms
        
        # Create UI
        self._setup_ui(title)
        
        # Set initial range and value
        self.setRange(minimum, maximum)
        self.setValue(value)
        
        # Connect signals
        self._connect_signals()
        
        # Size policy
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
    
    def _setup_ui(self, title: str):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(4)
        layout.setContentsMargins(4, 4, 4, 4)
        
        # Title label
        if title:
            self.title_label = QLabel(title)
            self.title_label.setAlignment(Qt.AlignmentFlag.AlignLeft)
            font = QFont()
            font.setPointSize(9)
            font.setBold(True)
            self.title_label.setFont(font)
            layout.addWidget(self.title_label)
        
        # Main slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(self._slider_resolution)
        self.slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.slider.setTickInterval(self._slider_resolution // 10)
        layout.addWidget(self.slider)
        
        # Controls layout
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(4)
        
        # Min spinbox
        min_layout = QVBoxLayout()
        min_layout.setSpacing(1)
        min_label = QLabel("Min")
        min_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(7)
        min_label.setFont(font)
        min_layout.addWidget(min_label)
        
        self.min_spinbox = QDoubleSpinBox()
        self.min_spinbox.setDecimals(self._decimals)
        self.min_spinbox.setMinimumWidth(80)
        self.min_spinbox.setMaximumWidth(100)
        self.min_spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        min_layout.addWidget(self.min_spinbox)
        
        controls_layout.addLayout(min_layout)
        
        # Current value spinbox
        value_layout = QVBoxLayout()
        value_layout.setSpacing(1)
        value_label = QLabel("Value")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(7)
        value_label.setFont(font)
        value_layout.addWidget(value_label)
        
        self.value_spinbox = QDoubleSpinBox()
        self.value_spinbox.setDecimals(self._decimals)
        self.value_spinbox.setMinimumWidth(80)
        self.value_spinbox.setMaximumWidth(100)
        self.value_spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_layout.addWidget(self.value_spinbox)
        
        controls_layout.addLayout(value_layout)
        
        # Max spinbox
        max_layout = QVBoxLayout()
        max_layout.setSpacing(1)
        max_label = QLabel("Max")
        max_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(7)
        max_label.setFont(font)
        max_layout.addWidget(max_label)
        
        self.max_spinbox = QDoubleSpinBox()
        self.max_spinbox.setDecimals(self._decimals)
        self.max_spinbox.setMinimumWidth(80)
        self.max_spinbox.setMaximumWidth(100)
        self.max_spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        max_layout.addWidget(self.max_spinbox)
        
        controls_layout.addLayout(max_layout)
        
        # Units label
        if self._units:
            self.units_label = QLabel(self._units)
            font = QFont()
            font.setPointSize(8)
            self.units_label.setFont(font)
            self.units_label.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignVCenter)
            controls_layout.addWidget(self.units_label)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
    
    def _connect_signals(self):
        """Connect internal signals"""
        self.slider.valueChanged.connect(self._on_slider_changed)
        self.value_spinbox.valueChanged.connect(self._on_value_spinbox_changed)
        self.min_spinbox.valueChanged.connect(self._on_min_changed)
        self.max_spinbox.valueChanged.connect(self._on_max_changed)
    
    def _value_to_slider(self, value: float) -> int:
        """Convert real value to slider position"""
        min_val = self.minimum()
        max_val = self.maximum()
        
        if max_val <= min_val:
            return 0
        
        # Clamp value
        value = max(min_val, min(max_val, value))
        
        # Scale to slider range
        ratio = (value - min_val) / (max_val - min_val)
        return int(ratio * self._slider_resolution)
    
    def _slider_to_value(self, slider_pos: int) -> float:
        """Convert slider position to real value"""
        min_val = self.minimum()
        max_val = self.maximum()
        
        # Scale from slider range
        ratio = slider_pos / self._slider_resolution
        value = min_val + ratio * (max_val - min_val)
        
        # Round to step if specified
        if self._step > 0:
            steps = round((value - min_val) / self._step)
            value = min_val + steps * self._step
        
        return max(min_val, min(max_val, value))
    
    @Slot(int)
    def _on_slider_changed(self, slider_value: int):
        """Handle slider value change"""
        if self._updating_internally:
            return
        
        real_value = self._slider_to_value(slider_value)
        
        # Update value spinbox
        self._updating_internally = True
        self.value_spinbox.setValue(real_value)
        self._updating_internally = False
        
        # Emit immediate signal
        self.valueChanged.emit(real_value)
        
        # Start/restart debounce timer for edited signal
        self._debounce_timer.start(self._debounce_delay)
    
    @Slot(float)
    def _on_value_spinbox_changed(self, spinbox_value: float):
        """Handle value spinbox change"""
        if self._updating_internally:
            return
        
        # Clamp to current range
        spinbox_value = max(self.minimum(), min(self.maximum(), spinbox_value))
        
        # Update slider
        slider_pos = self._value_to_slider(spinbox_value)
        self._updating_internally = True
        self.slider.setValue(slider_pos)
        self._updating_internally = False
        
        # Emit signals
        self.valueChanged.emit(spinbox_value)
        self._debounce_timer.start(self._debounce_delay)
    
    @Slot(float)
    def _on_min_changed(self, new_min: float):
        """Handle minimum value change"""
        if self._updating_internally:
            return
        
        current_max = self.maximum()
        current_value = self.value()
        
        # Validate range
        if new_min >= current_max:
            # Soft correction: adjust max to be slightly higher
            new_max = new_min + max(self._step, 0.01)
            self._updating_internally = True
            self.max_spinbox.setValue(new_max)
            self._updating_internally = False
            current_max = new_max
        
        # Update range
        self._update_spinbox_ranges()
        
        # Adjust current value if needed
        if current_value < new_min:
            self.setValue(new_min)
        else:
            # Update slider position for current value
            self._update_slider_position()
        
        # Emit range changed signal
        self.rangeChanged.emit(new_min, current_max)
    
    @Slot(float)
    def _on_max_changed(self, new_max: float):
        """Handle maximum value change"""
        if self._updating_internally:
            return
        
        current_min = self.minimum()
        current_value = self.value()
        
        # Validate range
        if new_max <= current_min:
            # Soft correction: adjust min to be slightly lower
            new_min = new_max - max(self._step, 0.01)
            self._updating_internally = True
            self.min_spinbox.setValue(new_min)
            self._updating_internally = False
            current_min = new_min
        
        # Update range
        self._update_spinbox_ranges()
        
        # Adjust current value if needed
        if current_value > new_max:
            self.setValue(new_max)
        else:
            # Update slider position for current value
            self._update_slider_position()
        
        # Emit range changed signal
        self.rangeChanged.emit(current_min, new_max)
    
    def _update_spinbox_ranges(self):
        """Update spinbox ranges based on current min/max"""
        min_val = self.min_spinbox.value()
        max_val = self.max_spinbox.value()
        
        # Set wide limits for min/max spinboxes themselves
        self.min_spinbox.setRange(-1e6, 1e6)
        self.max_spinbox.setRange(-1e6, 1e6)
        
        # Set constrained range for value spinbox
        self.value_spinbox.setMinimum(min_val)
        self.value_spinbox.setMaximum(max_val)
        self.value_spinbox.setSingleStep(self._step)
    
    def _update_slider_position(self):
        """Update slider position based on current value"""
        current_value = self.value_spinbox.value()
        slider_pos = self._value_to_slider(current_value)
        
        self._updating_internally = True
        self.slider.setValue(slider_pos)
        self._updating_internally = False
    
    @Slot()
    def _emit_value_edited(self):
        """Emit the debounced value edited signal"""
        self.valueEdited.emit(self.value())
    
    def setValue(self, value: float):
        """Set current value
        
        Args:
            value: New value
        """
        # Clamp to current range
        value = max(self.minimum(), min(self.maximum(), value))
        
        # Update both controls
        slider_pos = self._value_to_slider(value)
        
        self._updating_internally = True
        self.slider.setValue(slider_pos)
        self.value_spinbox.setValue(value)
        self._updating_internally = False
    
    def value(self) -> float:
        """Get current value
        
        Returns:
            Current value
        """
        return self.value_spinbox.value()
    
    def setRange(self, minimum: float, maximum: float):
        """Set range limits
        
        Args:
            minimum: New minimum value
            maximum: New maximum value
        """
        if maximum <= minimum:
            raise ValueError("Maximum must be greater than minimum")
        
        current_value = self.value_spinbox.value() if hasattr(self, 'value_spinbox') else minimum
        
        self._updating_internally = True
        
        # Set min/max spinboxes
        if hasattr(self, 'min_spinbox'):
            self.min_spinbox.setValue(minimum)
            self.max_spinbox.setValue(maximum)
        
        # Update ranges
        self._update_spinbox_ranges()
        
        self._updating_internally = False
        
        # Restore value (may be clamped)
        if hasattr(self, 'value_spinbox'):
            self.setValue(current_value)
    
    def minimum(self) -> float:
        """Get current minimum value"""
        return self.min_spinbox.value() if hasattr(self, 'min_spinbox') else 0.0
    
    def maximum(self) -> float:
        """Get current maximum value"""
        return self.max_spinbox.value() if hasattr(self, 'max_spinbox') else 100.0
    
    def setDecimals(self, decimals: int):
        """Set number of decimal places"""
        self._decimals = decimals
        if hasattr(self, 'min_spinbox'):
            self.min_spinbox.setDecimals(decimals)
            self.value_spinbox.setDecimals(decimals)
            self.max_spinbox.setDecimals(decimals)
    
    def setStep(self, step: float):
        """Set step size"""
        self._step = step
        if hasattr(self, 'value_spinbox'):
            self.value_spinbox.setSingleStep(step)
    
    def setEnabled(self, enabled: bool):
        """Enable/disable the widget"""
        super().setEnabled(enabled)
        if hasattr(self, 'slider'):
            self.slider.setEnabled(enabled)
            self.min_spinbox.setEnabled(enabled)
            self.value_spinbox.setEnabled(enabled)
            self.max_spinbox.setEnabled(enabled)