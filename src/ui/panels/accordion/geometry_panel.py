"""Accordion panel module extracted from panels_accordion."""

from __future__ import annotations

from PySide6.QtWidgets import QVBoxLayout, QWidget
from PySide6.QtCore import Signal
from src.ui.parameter_slider import ParameterSlider


class GeometryPanelAccordion(QWidget):
    """Geometry parameters panel with sliders and range controls"""

    parameter_changed = Signal(str, float)  # (parameter_name, value)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Main layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # === BASIC DIMENSIONS ===

        # Wheelbase
        self.wheelbase = ParameterSlider(
            name="Wheelbase (L)",
            initial_value=3.0,
            min_value=2.0,
            max_value=5.0,
            step=0.01,
            decimals=3,
            unit="m",
            allow_range_edit=True,
        )
        self.wheelbase.value_changed.connect(
            lambda v: self.parameter_changed.emit("wheelbase", v)
        )
        layout.addWidget(self.wheelbase)

        # Track width
        self.track_width = ParameterSlider(
            name="Track Width (B)",
            initial_value=1.8,
            min_value=1.0,
            max_value=2.5,
            step=0.01,
            decimals=3,
            unit="m",
            allow_range_edit=True,
        )
        self.track_width.value_changed.connect(
            lambda v: self.parameter_changed.emit("track_width", v)
        )
        layout.addWidget(self.track_width)

        # === LEVER GEOMETRY ===

        # Lever arm length
        self.lever_arm = ParameterSlider(
            name="Lever Arm (r)",
            initial_value=0.3,
            min_value=0.1,
            max_value=0.6,
            step=0.001,
            decimals=3,
            unit="m",
            allow_range_edit=True,
        )
        self.lever_arm.value_changed.connect(
            lambda v: self.parameter_changed.emit("lever_arm", v)
        )
        layout.addWidget(self.lever_arm)

        # Lever angle (alpha) - read-only, calculated
        self.lever_angle = ParameterSlider(
            name="Lever Angle (?)",
            initial_value=0.0,
            min_value=-30.0,
            max_value=30.0,
            step=0.1,
            decimals=2,
            unit="deg",
            allow_range_edit=False,
        )
        self.lever_angle.spinbox.setReadOnly(True)
        self.lever_angle.slider.setEnabled(False)
        layout.addWidget(self.lever_angle)

        # === CYLINDER GEOMETRY ===

        # Cylinder stroke (max)
        self.cylinder_stroke = ParameterSlider(
            name="Cylinder Stroke (s_max)",
            initial_value=0.2,
            min_value=0.05,
            max_value=0.5,
            step=0.001,
            decimals=3,
            unit="m",
            allow_range_edit=True,
        )
        self.cylinder_stroke.value_changed.connect(
            lambda v: self.parameter_changed.emit("cylinder_stroke", v)
        )
        layout.addWidget(self.cylinder_stroke)

        # Piston diameter
        self.piston_diameter = ParameterSlider(
            name="Piston Diameter (D_p)",
            initial_value=0.08,
            min_value=0.03,
            max_value=0.15,
            step=0.001,
            decimals=3,
            unit="m",
            allow_range_edit=True,
        )
        self.piston_diameter.value_changed.connect(
            lambda v: self.parameter_changed.emit("piston_diameter", v)
        )
        layout.addWidget(self.piston_diameter)

        # Rod diameter
        self.rod_diameter = ParameterSlider(
            name="Rod Diameter (D_r)",
            initial_value=0.04,
            min_value=0.01,
            max_value=0.10,
            step=0.001,
            decimals=3,
            unit="m",
            allow_range_edit=True,
        )
        self.rod_diameter.value_changed.connect(
            lambda v: self.parameter_changed.emit("rod_diameter", v)
        )
        layout.addWidget(self.rod_diameter)

        # === MASSES ===

        # Frame mass
        self.frame_mass = ParameterSlider(
            name="Frame Mass (M_frame)",
            initial_value=1500.0,
            min_value=500.0,
            max_value=5000.0,
            step=10.0,
            decimals=1,
            unit="kg",
            allow_range_edit=True,
        )
        self.frame_mass.value_changed.connect(
            lambda v: self.parameter_changed.emit("frame_mass", v)
        )
        layout.addWidget(self.frame_mass)

        # Wheel mass (each)
        self.wheel_mass = ParameterSlider(
            name="Wheel Mass (M_wheel)",
            initial_value=50.0,
            min_value=10.0,
            max_value=200.0,
            step=1.0,
            decimals=1,
            unit="kg",
            allow_range_edit=True,
        )
        self.wheel_mass.value_changed.connect(
            lambda v: self.parameter_changed.emit("wheel_mass", v)
        )
        layout.addWidget(self.wheel_mass)

        # Add stretch at bottom
        layout.addStretch()

    def get_parameters(self) -> dict:
        """Get all parameters as dict"""
        return {
            "wheelbase": self.wheelbase.value(),
            "track_width": self.track_width.value(),
            "lever_arm": self.lever_arm.value(),
            "lever_angle": self.lever_angle.value(),
            "cylinder_stroke": self.cylinder_stroke.value(),
            "piston_diameter": self.piston_diameter.value(),
            "rod_diameter": self.rod_diameter.value(),
            "frame_mass": self.frame_mass.value(),
            "wheel_mass": self.wheel_mass.value(),
        }

    def set_parameters(self, params: dict):
        """Set parameters from dict"""
        if "wheelbase" in params:
            self.wheelbase.set_value(params["wheelbase"])
        if "track_width" in params:
            self.track_width.set_value(params["track_width"])
        if "lever_arm" in params:
            self.lever_arm.set_value(params["lever_arm"])
        if "cylinder_stroke" in params:
            self.cylinder_stroke.set_value(params["cylinder_stroke"])
        if "piston_diameter" in params:
            self.piston_diameter.set_value(params["piston_diameter"])
        if "rod_diameter" in params:
            self.rod_diameter.set_value(params["rod_diameter"])
        if "frame_mass" in params:
            self.frame_mass.set_value(params["frame_mass"])
        if "wheel_mass" in params:
            self.wheel_mass.set_value(params["wheel_mass"])

    def update_calculated_values(self, lever_angle: float):
        """Update read-only calculated values (called from simulation)"""
        self.lever_angle.set_value(lever_angle)
