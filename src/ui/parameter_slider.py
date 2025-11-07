"""
Parameter Slider Widget - Slider with range controls
Combines slider, spinbox, and min/max range inputs
"""

from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QVBoxLayout,
    QSlider,
    QDoubleSpinBox,
    QLabel,
    QFrame,
)
from PySide6.QtCore import Qt, Signal
from collections.abc import Callable


class ParameterSlider(QWidget):
    """Parameter slider with adjustable range

    Features:
    - Slider for quick adjustment
    - SpinBox for precise input
    - Min/Max range controls
    - Value validation
    - Unit display
    """

    value_changed = Signal(float)  # Emitted when value changes
    range_changed = Signal(float, float)  # Emitted when min/max changes

    def __init__(
        self,
        name: str,
        initial_value: float = 0.0,
        min_value: float = 0.0,
        max_value: float = 100.0,
        step: float = 1.0,
        decimals: int = 2,
        unit: str = "",
        allow_range_edit: bool = True,
        validator: Callable[[float, float, float], bool] | None = None,
        parent=None,
    ):
        """
        Args:
            name: Parameter name (display label)
            initial_value: Starting value
            min_value: Minimum allowed value
            max_value: Maximum allowed value
            step: Step size for slider/spinbox
            decimals: Number of decimal places
            unit: Unit string (e.g., "mm", "kPa", "kg")
            allow_range_edit: Whether user can edit min/max
            validator: Optional function(value, min, max) -> bool for validation
        """
        super().__init__(parent)

        self._name = name
        self._min = min_value
        self._max = max_value
        self._step = step
        self._decimals = decimals
        self._unit = unit
        self._validator = validator
        self._allow_range_edit = allow_range_edit

        # Block signals during setup
        self._updating = False

        self._setup_ui()
        self.set_value(initial_value)

    def _setup_ui(self):
        """Setup UI layout"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 6)
        main_layout.setSpacing(4)

        # === ROW 1: Label and Value ===
        top_row = QHBoxLayout()
        top_row.setSpacing(8)

        # Parameter name label
        self.label = QLabel(self._name)
        self.label.setStyleSheet("color: #aaaaaa; font-size: 9pt;")
        top_row.addWidget(self.label)

        top_row.addStretch()

        # Value spinbox
        self.spinbox = QDoubleSpinBox()
        self.spinbox.setMinimum(self._min)
        self.spinbox.setMaximum(self._max)
        self.spinbox.setSingleStep(self._step)
        self.spinbox.setDecimals(self._decimals)
        self.spinbox.setSuffix(f" {self._unit}" if self._unit else "")
        self.spinbox.setMinimumWidth(100)
        self.spinbox.setStyleSheet(
            """
            QDoubleSpinBox {
                background-color: #2a2a3e;
                color: #ffffff;
                border: 1px solid #3a3a4e;
                border-radius: 3px;
                padding: 4px 6px;
                font-size: 9pt;
            }
            QDoubleSpinBox:focus {
                border: 1px solid #5a9fd4;
            }
        """
        )
        self.spinbox.valueChanged.connect(self._on_spinbox_changed)
        top_row.addWidget(self.spinbox)

        main_layout.addLayout(top_row)

        # === ROW 2: Slider ===
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1000)  # Internal resolution
        self.slider.setStyleSheet(
            """
            QSlider::groove:horizontal {
                background: #2a2a3e;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: #5a9fd4;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: #7ab9f4;
            }
            QSlider::sub-page:horizontal {
                background: #4a7fa4;
                border-radius: 3px;
            }
        """
        )
        self.slider.valueChanged.connect(self._on_slider_changed)
        main_layout.addWidget(self.slider)

        # === ROW 3: Min/Max Range (optional) ===
        if self._allow_range_edit:
            range_row = QHBoxLayout()
            range_row.setSpacing(4)

            # Min label
            min_label = QLabel("Min:")
            min_label.setStyleSheet("color: #888888; font-size: 8pt;")
            range_row.addWidget(min_label)

            # Min spinbox
            self.min_spinbox = QDoubleSpinBox()
            self.min_spinbox.setDecimals(self._decimals)
            self.min_spinbox.setSingleStep(self._step)
            self.min_spinbox.setValue(self._min)
            self.min_spinbox.setSuffix(f" {self._unit}" if self._unit else "")
            self.min_spinbox.setMaximumWidth(80)
            self.min_spinbox.setStyleSheet(
                """
                QDoubleSpinBox {
                    background-color: #2a2a3e;
                    color: #aaaaaa;
                    border: 1px solid #3a3a4e;
                    border-radius: 3px;
                    padding: 2px 4px;
                    font-size: 8pt;
                }
            """
            )
            self.min_spinbox.valueChanged.connect(self._on_min_changed)
            range_row.addWidget(self.min_spinbox)

            range_row.addStretch()

            # Max label
            max_label = QLabel("Max:")
            max_label.setStyleSheet("color: #888888; font-size: 8pt;")
            range_row.addWidget(max_label)

            # Max spinbox
            self.max_spinbox = QDoubleSpinBox()
            self.max_spinbox.setDecimals(self._decimals)
            self.max_spinbox.setSingleStep(self._step)
            self.max_spinbox.setValue(self._max)
            self.max_spinbox.setSuffix(f" {self._unit}" if self._unit else "")
            self.max_spinbox.setMaximumWidth(80)
            self.max_spinbox.setStyleSheet(
                """
                QDoubleSpinBox {
                    background-color: #2a2a3e;
                    color: #aaaaaa;
                    border: 1px solid #3a3a4e;
                    border-radius: 3px;
                    padding: 2px 4px;
                    font-size: 8pt;
                }
            """
            )
            self.max_spinbox.valueChanged.connect(self._on_max_changed)
            range_row.addWidget(self.max_spinbox)

            main_layout.addLayout(range_row)
        else:
            self.min_spinbox = None
            self.max_spinbox = None

        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setStyleSheet("background-color: #2a2a3e;")
        separator.setMaximumHeight(1)
        main_layout.addWidget(separator)

    def _value_to_slider(self, value: float) -> int:
        """Convert real value to slider position"""
        if self._max == self._min:
            return 0
        ratio = (value - self._min) / (self._max - self._min)
        return int(ratio * 1000)

    def _slider_to_value(self, pos: int) -> float:
        """Convert slider position to real value"""
        ratio = pos / 1000.0
        value = self._min + ratio * (self._max - self._min)
        # Round to step
        if self._step > 0:
            value = round(value / self._step) * self._step
        return value

    def _on_slider_changed(self, pos: int):
        """Handle slider movement"""
        if self._updating:
            return

        value = self._slider_to_value(pos)

        # Validate
        if self._validator and not self._validator(value, self._min, self._max):
            return

        self._updating = True
        self.spinbox.setValue(value)
        self._updating = False

        self.value_changed.emit(value)

    def _on_spinbox_changed(self, value: float):
        """Handle spinbox value change"""
        if self._updating:
            return

        # Validate
        if self._validator and not self._validator(value, self._min, self._max):
            return

        self._updating = True
        slider_pos = self._value_to_slider(value)
        self.slider.setValue(slider_pos)
        self._updating = False

        self.value_changed.emit(value)

    def _on_min_changed(self, new_min: float):
        """Handle min range change"""
        if self._updating:
            return

        # Validate: min < max
        if new_min >= self._max:
            self._updating = True
            self.min_spinbox.setValue(self._min)
            self._updating = False
            return

        self._min = new_min

        # Update spinbox limits
        self._updating = True
        self.spinbox.setMinimum(self._min)

        # Clamp current value
        current_value = self.spinbox.value()
        if current_value < self._min:
            self.spinbox.setValue(self._min)

        # Update slider
        slider_pos = self._value_to_slider(self.spinbox.value())
        self.slider.setValue(slider_pos)

        self._updating = False

        self.range_changed.emit(self._min, self._max)

    def _on_max_changed(self, new_max: float):
        """Handle max range change"""
        if self._updating:
            return

        # Validate: max > min
        if new_max <= self._min:
            self._updating = True
            self.max_spinbox.setValue(self._max)
            self._updating = False
            return

        self._max = new_max

        # Update spinbox limits
        self._updating = True
        self.spinbox.setMaximum(self._max)

        # Clamp current value
        current_value = self.spinbox.value()
        if current_value > self._max:
            self.spinbox.setValue(self._max)

        # Update slider
        slider_pos = self._value_to_slider(self.spinbox.value())
        self.slider.setValue(slider_pos)

        self._updating = False

        self.range_changed.emit(self._min, self._max)

    # === Public API ===

    def value(self) -> float:
        """Get current value"""
        return self.spinbox.value()

    def set_value(self, value: float):
        """Set value"""
        self._updating = True
        self.spinbox.setValue(value)
        slider_pos = self._value_to_slider(value)
        self.slider.setValue(slider_pos)
        self._updating = False

    def get_range(self) -> tuple[float, float]:
        """Get current min/max range"""
        return (self._min, self._max)

    def set_range(self, min_value: float, max_value: float):
        """Set min/max range"""
        if min_value >= max_value:
            raise ValueError("min_value must be less than max_value")

        self._updating = True

        self._min = min_value
        self._max = max_value

        self.spinbox.setMinimum(min_value)
        self.spinbox.setMaximum(max_value)

        if self._allow_range_edit:
            self.min_spinbox.setValue(min_value)
            self.max_spinbox.setValue(max_value)

        # Update slider
        slider_pos = self._value_to_slider(self.spinbox.value())
        self.slider.setValue(slider_pos)

        self._updating = False


# Export
__all__ = ["ParameterSlider"]
