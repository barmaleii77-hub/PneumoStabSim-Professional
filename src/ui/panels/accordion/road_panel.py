"""Accordion panel module extracted from panels_accordion."""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Signal
from src.ui.parameter_slider import ParameterSlider


class RoadPanelAccordion(QWidget):
    """Road input and excitation panel"""

    road_mode_changed = Signal(str)  # 'manual' or 'profile'
    parameter_changed = Signal(str, float)
    profile_type_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # === ROAD MODE ===

        mode_label = QLabel("Road Input Mode:")
        mode_label.setStyleSheet("color: #aaaaaa; font-size: 9pt; font-weight: bold;")
        layout.addWidget(mode_label)

        self.road_mode_combo = QComboBox()
        self.road_mode_combo.addItems(["Manual (Sine)", "Road Profile"])
        self.road_mode_combo.setStyleSheet(
            """
            QComboBox {
                background-color: #2a2a3e;
                color: #ffffff;
                border: 1px solid #3a3a4e;
                border-radius: 3px;
                padding: 4px 6px;
                font-size: 9pt;
            }
        """
        )
        self.road_mode_combo.currentTextChanged.connect(self._on_mode_changed)
        layout.addWidget(self.road_mode_combo)

        # === MANUAL MODE PARAMETERS ===

        self.manual_label = QLabel("Manual Parameters:")
        self.manual_label.setStyleSheet(
            "color: #aaaaaa; font-size: 9pt; font-weight: bold;"
        )
        layout.addWidget(self.manual_label)

        # Amplitude (all wheels)
        self.amplitude = ParameterSlider(
            name="Amplitude (A)",
            initial_value=0.05,
            min_value=0.0,
            max_value=0.2,
            step=0.001,
            decimals=3,
            unit="m",
            allow_range_edit=True,
        )
        self.amplitude.value_changed.connect(
            lambda v: self.parameter_changed.emit("amplitude", v)
        )
        layout.addWidget(self.amplitude)

        # Frequency (all wheels)
        self.frequency = ParameterSlider(
            name="Frequency (f)",
            initial_value=1.0,
            min_value=0.1,
            max_value=10.0,
            step=0.1,
            decimals=2,
            unit="Hz",
            allow_range_edit=True,
        )
        self.frequency.value_changed.connect(
            lambda v: self.parameter_changed.emit("frequency", v)
        )
        layout.addWidget(self.frequency)

        # Phase offset (rear vs front)
        self.phase_offset = ParameterSlider(
            name="Phase Offset (rear)",
            initial_value=0.0,
            min_value=-180.0,
            max_value=180.0,
            step=1.0,
            decimals=1,
            unit="deg",
            allow_range_edit=True,
        )
        self.phase_offset.value_changed.connect(
            lambda v: self.parameter_changed.emit("phase_offset", v)
        )
        layout.addWidget(self.phase_offset)

        # === ROAD PROFILE PARAMETERS ===

        self.profile_label = QLabel("Road Profile:")
        self.profile_label.setStyleSheet(
            "color: #aaaaaa; font-size: 9pt; font-weight: bold;"
        )
        layout.addWidget(self.profile_label)

        self.profile_type_combo = QComboBox()
        self.profile_type_combo.addItems(
            [
                "Smooth Highway",
                "City Streets",
                "Off-Road",
                "Mountain Serpentine",
                "Custom",
            ]
        )
        self.profile_type_combo.setStyleSheet(
            """
            QComboBox {
                background-color: #2a2a3e;
                color: #ffffff;
                border: 1px solid #3a3a4e;
                border-radius: 3px;
                padding: 4px 6px;
                font-size: 9pt;
            }
        """
        )
        self.profile_type_combo.currentTextChanged.connect(
            lambda text: self.profile_type_changed.emit(text.lower().replace(" ", "_"))
        )
        layout.addWidget(self.profile_type_combo)

        # Average speed
        self.avg_speed = ParameterSlider(
            name="Average Speed (v_avg)",
            initial_value=60.0,
            min_value=10.0,
            max_value=120.0,
            step=5.0,
            decimals=1,
            unit="km/h",
            allow_range_edit=True,
        )
        self.avg_speed.value_changed.connect(
            lambda v: self.parameter_changed.emit("avg_speed", v)
        )
        layout.addWidget(self.avg_speed)

        # Initially hide profile parameters
        self.profile_label.hide()
        self.profile_type_combo.hide()
        self.avg_speed.hide()

        layout.addStretch()

    def _on_mode_changed(self, mode_text: str):
        """Handle road mode change"""
        is_profile = "profile" in mode_text.lower()

        # Show/hide parameters
        self.manual_label.setVisible(not is_profile)
        self.amplitude.setVisible(not is_profile)
        self.frequency.setVisible(not is_profile)
        self.phase_offset.setVisible(not is_profile)

        self.profile_label.setVisible(is_profile)
        self.profile_type_combo.setVisible(is_profile)
        self.avg_speed.setVisible(is_profile)

        mode = "profile" if is_profile else "manual"
        self.road_mode_changed.emit(mode)

    def get_parameters(self) -> dict:
        """Get all parameters"""
        is_manual = "manual" in self.road_mode_combo.currentText().lower()

        if is_manual:
            return {
                "road_mode": "manual",
                "amplitude": self.amplitude.value(),
                "frequency": self.frequency.value(),
                "phase_offset": self.phase_offset.value(),
            }
        else:
            return {
                "road_mode": "profile",
                "profile_type": self.profile_type_combo.currentText()
                .lower()
                .replace(" ", "_"),
                "avg_speed": self.avg_speed.value(),
            }
