# -*- coding: utf-8 -*-
"""
Accordion panels with ParameterSlider
Replaces old dock widget panels
"""
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QCheckBox,
)
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


class PneumoPanelAccordion(QWidget):
    """Pneumatics parameters panel"""

    parameter_changed = Signal(str, float)
    thermo_mode_changed = Signal(str)  # 'isothermal' or 'adiabatic'

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # === THERMO MODE ===

        thermo_label = QLabel("Thermodynamic Mode:")
        thermo_label.setStyleSheet("color: #aaaaaa; font-size: 9pt; font-weight: bold;")
        layout.addWidget(thermo_label)

        self.thermo_combo = QComboBox()
        self.thermo_combo.addItems(["Isothermal", "Adiabatic"])
        self.thermo_combo.setStyleSheet(
            """
            QComboBox {
                background-color: #2a2a3e;
                color: #ffffff;
                border: 1px solid #3a3a4e;
                border-radius: 3px;
                padding: 4px 6px;
                font-size: 9pt;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox:focus {
                border: 1px solid #5a9fd4;
            }
        """
        )
        self.thermo_combo.currentTextChanged.connect(
            lambda text: self.thermo_mode_changed.emit(text.lower())
        )
        layout.addWidget(self.thermo_combo)

        # === CYLINDER VOLUMES ===

        # Head volume (read-only, calculated from geometry)
        self.head_volume = ParameterSlider(
            name="Head Volume (V_h)",
            initial_value=500.0,
            min_value=100.0,
            max_value=2000.0,
            step=10.0,
            decimals=1,
            unit="cm?",
            allow_range_edit=False,
        )
        self.head_volume.spinbox.setReadOnly(True)
        self.head_volume.slider.setEnabled(False)
        layout.addWidget(self.head_volume)

        # Rod volume (read-only, calculated from geometry)
        self.rod_volume = ParameterSlider(
            name="Rod Volume (V_r)",
            initial_value=300.0,
            min_value=50.0,
            max_value=1500.0,
            step=10.0,
            decimals=1,
            unit="cm?",
            allow_range_edit=False,
        )
        self.rod_volume.spinbox.setReadOnly(True)
        self.rod_volume.slider.setEnabled(False)
        layout.addWidget(self.rod_volume)

        # === LINE PRESSURES ===

        # Line A1 pressure (initial)
        self.pressure_a1 = ParameterSlider(
            name="Line A1 Pressure (P_A1)",
            initial_value=150.0,
            min_value=50.0,
            max_value=500.0,
            step=5.0,
            decimals=1,
            unit="kPa",
            allow_range_edit=True,
        )
        self.pressure_a1.value_changed.connect(
            lambda v: self.parameter_changed.emit("pressure_a1", v)
        )
        layout.addWidget(self.pressure_a1)

        # Line B1 pressure (initial)
        self.pressure_b1 = ParameterSlider(
            name="Line B1 Pressure (P_B1)",
            initial_value=150.0,
            min_value=50.0,
            max_value=500.0,
            step=5.0,
            decimals=1,
            unit="kPa",
            allow_range_edit=True,
        )
        self.pressure_b1.value_changed.connect(
            lambda v: self.parameter_changed.emit("pressure_b1", v)
        )
        layout.addWidget(self.pressure_b1)

        # Line A2 pressure (initial)
        self.pressure_a2 = ParameterSlider(
            name="Line A2 Pressure (P_A2)",
            initial_value=150.0,
            min_value=50.0,
            max_value=500.0,
            step=5.0,
            decimals=1,
            unit="kPa",
            allow_range_edit=True,
        )
        self.pressure_a2.value_changed.connect(
            lambda v: self.parameter_changed.emit("pressure_a2", v)
        )
        layout.addWidget(self.pressure_a2)

        # Line B2 pressure (initial)
        self.pressure_b2 = ParameterSlider(
            name="Line B2 Pressure (P_B2)",
            initial_value=150.0,
            min_value=50.0,
            max_value=500.0,
            step=5.0,
            decimals=1,
            unit="kPa",
            allow_range_edit=True,
        )
        self.pressure_b2.value_changed.connect(
            lambda v: self.parameter_changed.emit("pressure_b2", v)
        )
        layout.addWidget(self.pressure_b2)

        # === TANK/RESERVOIR ===

        # Tank pressure
        self.tank_pressure = ParameterSlider(
            name="Tank Pressure (P_tank)",
            initial_value=200.0,
            min_value=100.0,
            max_value=600.0,
            step=10.0,
            decimals=1,
            unit="kPa",
            allow_range_edit=True,
        )
        self.tank_pressure.value_changed.connect(
            lambda v: self.parameter_changed.emit("tank_pressure", v)
        )
        layout.addWidget(self.tank_pressure)

        # Relief valve pressure
        self.relief_pressure = ParameterSlider(
            name="Relief Valve (P_relief)",
            initial_value=500.0,
            min_value=200.0,
            max_value=800.0,
            step=10.0,
            decimals=1,
            unit="kPa",
            allow_range_edit=True,
        )
        self.relief_pressure.value_changed.connect(
            lambda v: self.parameter_changed.emit("relief_pressure", v)
        )
        layout.addWidget(self.relief_pressure)

        # === TEMPERATURE ===

        # Atmospheric temperature
        self.temperature = ParameterSlider(
            name="Atmospheric Temp (T_atm)",
            initial_value=20.0,
            min_value=-20.0,
            max_value=50.0,
            step=1.0,
            decimals=1,
            unit="degC",  # Fixed: use ASCII instead of degree symbol
            allow_range_edit=True,
        )
        self.temperature.value_changed.connect(
            lambda v: self.parameter_changed.emit("temperature", v)
        )
        layout.addWidget(self.temperature)

        layout.addStretch()

    def get_parameters(self) -> dict:
        """Get all parameters"""
        return {
            "thermo_mode": self.thermo_combo.currentText().lower(),
            "head_volume": self.head_volume.value(),
            "rod_volume": self.rod_volume.value(),
            "pressure_a1": self.pressure_a1.value(),
            "pressure_b1": self.pressure_b1.value(),
            "pressure_a2": self.pressure_a2.value(),
            "pressure_b2": self.pressure_b2.value(),
            "tank_pressure": self.tank_pressure.value(),
            "relief_pressure": self.relief_pressure.value(),
            "temperature": self.temperature.value(),
        }

    def update_calculated_volumes(self, v_head: float, v_rod: float):
        """Update calculated volumes from geometry"""
        self.head_volume.set_value(v_head * 1e6)  # m? to cm?
        self.rod_volume.set_value(v_rod * 1e6)


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
