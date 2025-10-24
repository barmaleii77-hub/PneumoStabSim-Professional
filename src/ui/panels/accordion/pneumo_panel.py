"""Accordion panel module extracted from panels_accordion."""

from __future__ import annotations

from PySide6.QtWidgets import QComboBox, QLabel, QVBoxLayout, QWidget
from PySide6.QtCore import Signal
from src.ui.parameter_slider import ParameterSlider


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
