"""Accordion panel module extracted from panels_accordion."""

from __future__ import annotations

from PySide6.QtWidgets import QCheckBox, QComboBox, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Signal
from src.ui.parameter_slider import ParameterSlider


class SimulationPanelAccordion(QWidget):
    """Simulation mode and settings panel"""

    sim_mode_changed = Signal(str)  # 'kinematics' or 'dynamics'
    option_changed = Signal(str, bool)  # (option_name, enabled)
    parameter_changed = Signal(str, float)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # === SIMULATION MODE ===

        mode_label = QLabel("Simulation Mode:")
        mode_label.setStyleSheet("color: #aaaaaa; font-size: 9pt; font-weight: bold;")
        layout.addWidget(mode_label)

        self.sim_mode_combo = QComboBox()
        self.sim_mode_combo.addItems(["Kinematics", "Dynamics"])
        self.sim_mode_combo.setCurrentIndex(1)  # Default: Dynamics
        self.sim_mode_combo.setStyleSheet(
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
        self.sim_mode_combo.currentTextChanged.connect(
            lambda text: self._on_mode_changed(text.lower())
        )
        layout.addWidget(self.sim_mode_combo)

        # === KINEMATIC MODE OPTIONS (only for kinematics) ===

        self.kinematic_options_label = QLabel("Kinematic Options:")
        self.kinematic_options_label.setStyleSheet(
            "color: #aaaaaa; font-size: 9pt; font-weight: bold;"
        )
        layout.addWidget(self.kinematic_options_label)

        self.include_springs_check = QCheckBox("Include Springs")
        self.include_springs_check.setStyleSheet("color: #ffffff; font-size: 9pt;")
        self.include_springs_check.setChecked(True)
        self.include_springs_check.stateChanged.connect(
            lambda state: self.option_changed.emit("include_springs", state == 2)
        )
        layout.addWidget(self.include_springs_check)

        self.include_dampers_check = QCheckBox("Include Dampers")
        self.include_dampers_check.setStyleSheet("color: #ffffff; font-size: 9pt;")
        self.include_dampers_check.setChecked(True)
        self.include_dampers_check.stateChanged.connect(
            lambda state: self.option_changed.emit("include_dampers", state == 2)
        )
        layout.addWidget(self.include_dampers_check)

        # Initially hide kinematic options (dynamics mode)
        self.kinematic_options_label.hide()
        self.include_springs_check.hide()
        self.include_dampers_check.hide()

        # === INTERFERENCE CHECK ===

        self.check_interference = QCheckBox("Check Lever-Cylinder Interference")
        self.check_interference.setStyleSheet("color: #ffffff; font-size: 9pt;")
        self.check_interference.setChecked(False)
        self.check_interference.stateChanged.connect(
            lambda state: self.option_changed.emit("check_interference", state == 2)
        )
        layout.addWidget(self.check_interference)

        # === TIMING PARAMETERS ===

        # Time step
        self.time_step = ParameterSlider(
            name="Time Step (dt)",
            initial_value=0.001,
            min_value=0.0001,
            max_value=0.01,
            step=0.0001,
            decimals=4,
            unit="s",
            allow_range_edit=True,
        )
        self.time_step.value_changed.connect(
            lambda v: self.parameter_changed.emit("time_step", v)
        )
        layout.addWidget(self.time_step)

        # Simulation speed
        self.sim_speed = ParameterSlider(
            name="Simulation Speed",
            initial_value=1.0,
            min_value=0.1,
            max_value=10.0,
            step=0.1,
            decimals=1,
            unit="x",
            allow_range_edit=True,
        )
        self.sim_speed.value_changed.connect(
            lambda v: self.parameter_changed.emit("sim_speed", v)
        )
        layout.addWidget(self.sim_speed)

        layout.addStretch()

    def _on_mode_changed(self, mode: str):
        """Handle simulation mode change"""
        is_kinematics = mode == "kinematics"

        # Show/hide kinematic options
        self.kinematic_options_label.setVisible(is_kinematics)
        self.include_springs_check.setVisible(is_kinematics)
        self.include_dampers_check.setVisible(is_kinematics)

        self.sim_mode_changed.emit(mode)

    def get_parameters(self) -> dict:
        """Get all parameters"""
        return {
            "sim_mode": self.sim_mode_combo.currentText().lower(),
            "include_springs": self.include_springs_check.isChecked(),
            "include_dampers": self.include_dampers_check.isChecked(),
            "check_interference": self.check_interference.isChecked(),
            "time_step": self.time_step.value(),
            "sim_speed": self.sim_speed.value(),
        }
