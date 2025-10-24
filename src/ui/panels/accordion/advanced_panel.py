"""Accordion panel module extracted from panels_accordion."""

from __future__ import annotations

from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Signal
from src.ui.parameter_slider import ParameterSlider


class AdvancedPanelAccordion(QWidget):
    """Advanced parameters panel"""

    parameter_changed = Signal(str, float)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # === SUSPENSION COMPONENTS ===

        susp_label = QLabel("Suspension:")
        susp_label.setStyleSheet("color: #aaaaaa; font-size: 9pt; font-weight: bold;")
        layout.addWidget(susp_label)

        # Spring stiffness
        self.spring_stiffness = ParameterSlider(
            name="Spring Stiffness (k)",
            initial_value=50000.0,
            min_value=10000.0,
            max_value=200000.0,
            step=1000.0,
            decimals=0,
            unit="N/m",
            allow_range_edit=True,
        )
        self.spring_stiffness.value_changed.connect(
            lambda v: self.parameter_changed.emit("spring_stiffness", v)
        )
        layout.addWidget(self.spring_stiffness)

        # Damper coefficient
        self.damper_coeff = ParameterSlider(
            name="Damper Coefficient (c)",
            initial_value=2000.0,
            min_value=500.0,
            max_value=10000.0,
            step=100.0,
            decimals=0,
            unit="N*s/m",
            allow_range_edit=True,
        )
        self.damper_coeff.value_changed.connect(
            lambda v: self.parameter_changed.emit("damper_coeff", v)
        )
        layout.addWidget(self.damper_coeff)

        # === DEAD ZONES ===

        dz_label = QLabel("Cylinder Dead Zones:")
        dz_label.setStyleSheet("color: #aaaaaa; font-size: 9pt; font-weight: bold;")
        layout.addWidget(dz_label)

        self.dead_zone = ParameterSlider(
            name="Dead Zone (both ends)",
            initial_value=5.0,
            min_value=0.0,
            max_value=20.0,
            step=0.5,
            decimals=1,
            unit="%",
            allow_range_edit=True,
        )
        self.dead_zone.value_changed.connect(
            lambda v: self.parameter_changed.emit("dead_zone", v)
        )
        layout.addWidget(self.dead_zone)

        # === GRAPHICS SETTINGS ===

        graphics_label = QLabel("Graphics:")
        graphics_label.setStyleSheet(
            "color: #aaaaaa; font-size: 9pt; font-weight: bold;"
        )
        layout.addWidget(graphics_label)

        # Target FPS
        self.target_fps = ParameterSlider(
            name="Target FPS",
            initial_value=60.0,
            min_value=30.0,
            max_value=120.0,
            step=10.0,
            decimals=0,
            unit="fps",
            allow_range_edit=False,
        )
        self.target_fps.value_changed.connect(
            lambda v: self.parameter_changed.emit("target_fps", v)
        )
        layout.addWidget(self.target_fps)

        # Anti-aliasing quality
        self.aa_quality = ParameterSlider(
            name="Anti-Aliasing Quality",
            initial_value=2.0,
            min_value=0.0,
            max_value=4.0,
            step=1.0,
            decimals=0,
            unit="",
            allow_range_edit=False,
        )
        self.aa_quality.value_changed.connect(
            lambda v: self.parameter_changed.emit("aa_quality", v)
        )
        layout.addWidget(self.aa_quality)

        # Shadow quality
        self.shadow_quality = ParameterSlider(
            name="Shadow Quality",
            initial_value=2.0,
            min_value=0.0,
            max_value=4.0,
            step=1.0,
            decimals=0,
            unit="",
            allow_range_edit=False,
        )
        self.shadow_quality.value_changed.connect(
            lambda v: self.parameter_changed.emit("shadow_quality", v)
        )
        layout.addWidget(self.shadow_quality)

        layout.addStretch()

    def get_parameters(self) -> dict:
        """Get all parameters"""
        return {
            "spring_stiffness": self.spring_stiffness.value(),
            "damper_coeff": self.damper_coeff.value(),
            "dead_zone": self.dead_zone.value(),
            "target_fps": self.target_fps.value(),
            "aa_quality": self.aa_quality.value(),
            "shadow_quality": self.shadow_quality.value(),
        }


# Export
__all__ = [
    "GeometryPanelAccordion",
    "PneumoPanelAccordion",
    "SimulationPanelAccordion",
    "RoadPanelAccordion",
    "AdvancedPanelAccordion",
]
