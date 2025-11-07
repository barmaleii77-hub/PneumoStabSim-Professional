"""
Cylinder dimensions tab - Вкладка размеров цилиндра
Controls for pneumatic cylinder dimensions
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox
from PySide6.QtCore import Signal

from ...widgets import RangeSlider
from .state_manager import GeometryStateManager
from .defaults import get_parameter_limits, get_parameter_metadata


class CylinderTab(QWidget):
    """Вкладка размеров цилиндра

    Cylinder dimensions configuration tab

    Controls:
    - Cylinder body length (длина цилиндра)
    - Cylinder diameter (диаметр цилиндра)
    - Piston stroke (ход поршня)
    - Dead gap (мёртвый зазор)
    - Rod diameter (диаметр штока)
    - Piston rod length (длина штока поршня)
    - Piston thickness (толщина поршня)
    """

    # Signals
    parameter_changed = Signal(str, float)
    parameter_live_changed = Signal(str, float)

    def __init__(self, state_manager: GeometryStateManager, parent=None):
        """Initialize cylinder tab

        Args:
            state_manager: Shared state manager
            parent: Parent widget
        """
        super().__init__(parent)

        self.state_manager = state_manager

        self._setup_ui()
        self._load_from_state()
        self._connect_signals()
        self.update_link_state(
            bool(self.state_manager.get_parameter("link_rod_diameters"))
        )

    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        group = QGroupBox("Размеры цилиндра")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(4)

        # Cylinder length
        limits = get_parameter_limits("cylinder_length")
        metadata = get_parameter_metadata("cylinder_length")

        self.cylinder_length_slider = RangeSlider(
            minimum=limits["min"],
            maximum=limits["max"],
            value=self.state_manager.get_parameter("cylinder_length"),
            step=limits["step"],
            decimals=limits["decimals"],
            units=metadata["units"],
            title=metadata["title"],
        )
        self.cylinder_length_slider.setToolTip(metadata["description"])
        group_layout.addWidget(self.cylinder_length_slider)

        # Cylinder diameter
        limits = get_parameter_limits("cyl_diam_m")
        metadata = get_parameter_metadata("cyl_diam_m")

        self.cyl_diam_m_slider = RangeSlider(
            minimum=limits["min"],
            maximum=limits["max"],
            value=self.state_manager.get_parameter("cyl_diam_m"),
            step=limits["step"],
            decimals=limits["decimals"],
            units=metadata["units"],
            title=metadata["title"],
        )
        self.cyl_diam_m_slider.setToolTip(metadata["description"])
        group_layout.addWidget(self.cyl_diam_m_slider)

        # Piston stroke
        limits = get_parameter_limits("stroke_m")
        metadata = get_parameter_metadata("stroke_m")

        self.stroke_m_slider = RangeSlider(
            minimum=limits["min"],
            maximum=limits["max"],
            value=self.state_manager.get_parameter("stroke_m"),
            step=limits["step"],
            decimals=limits["decimals"],
            units=metadata["units"],
            title=metadata["title"],
        )
        self.stroke_m_slider.setToolTip(metadata["description"])
        group_layout.addWidget(self.stroke_m_slider)

        # Dead gap
        limits = get_parameter_limits("dead_gap_m")
        metadata = get_parameter_metadata("dead_gap_m")

        self.dead_gap_m_slider = RangeSlider(
            minimum=limits["min"],
            maximum=limits["max"],
            value=self.state_manager.get_parameter("dead_gap_m"),
            step=limits["step"],
            decimals=limits["decimals"],
            units=metadata["units"],
            title=metadata["title"],
        )
        self.dead_gap_m_slider.setToolTip(metadata["description"])
        group_layout.addWidget(self.dead_gap_m_slider)

        # Rod diameter
        limits = get_parameter_limits("rod_diameter_m")
        metadata = get_parameter_metadata("rod_diameter_m")

        self.rod_diameter_front_m_slider = RangeSlider(
            minimum=limits["min"],
            maximum=limits["max"],
            value=self.state_manager.get_parameter("rod_diameter_m"),
            step=limits["step"],
            decimals=limits["decimals"],
            units=metadata["units"],
            title=f"{metadata['title']} (передняя ось)",
        )
        self.rod_diameter_front_m_slider.setToolTip(metadata["description"])
        group_layout.addWidget(self.rod_diameter_front_m_slider)

        self.rod_diameter_rear_m_slider = RangeSlider(
            minimum=limits["min"],
            maximum=limits["max"],
            value=self.state_manager.get_parameter("rod_diameter_rear_m"),
            step=limits["step"],
            decimals=limits["decimals"],
            units=metadata["units"],
            title=f"{metadata['title']} (задняя ось)",
        )
        self.rod_diameter_rear_m_slider.setToolTip(metadata["description"])
        group_layout.addWidget(self.rod_diameter_rear_m_slider)

        # Piston rod length
        limits = get_parameter_limits("piston_rod_length_m")
        metadata = get_parameter_metadata("piston_rod_length_m")

        self.piston_rod_length_m_slider = RangeSlider(
            minimum=limits["min"],
            maximum=limits["max"],
            value=self.state_manager.get_parameter("piston_rod_length_m"),
            step=limits["step"],
            decimals=limits["decimals"],
            units=metadata["units"],
            title=metadata["title"],
        )
        self.piston_rod_length_m_slider.setToolTip(metadata["description"])
        group_layout.addWidget(self.piston_rod_length_m_slider)

        # Piston thickness
        limits = get_parameter_limits("piston_thickness_m")
        metadata = get_parameter_metadata("piston_thickness_m")

        self.piston_thickness_m_slider = RangeSlider(
            minimum=limits["min"],
            maximum=limits["max"],
            value=self.state_manager.get_parameter("piston_thickness_m"),
            step=limits["step"],
            decimals=limits["decimals"],
            units=metadata["units"],
            title=metadata["title"],
        )
        self.piston_thickness_m_slider.setToolTip(metadata["description"])
        group_layout.addWidget(self.piston_thickness_m_slider)

        layout.addWidget(group)
        layout.addStretch()

    def _connect_signals(self):
        """Connect widget signals"""
        # Cylinder length
        self.cylinder_length_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("cylinder_length", v)
        )
        self.cylinder_length_slider.valueChanged.connect(
            lambda v: self._on_parameter_live_changed("cylinder_length", v)
        )

        # Cylinder diameter
        self.cyl_diam_m_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("cyl_diam_m", v)
        )
        self.cyl_diam_m_slider.valueChanged.connect(
            lambda v: self._on_parameter_live_changed("cyl_diam_m", v)
        )

        # Stroke
        self.stroke_m_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("stroke_m", v)
        )
        self.stroke_m_slider.valueChanged.connect(
            lambda v: self._on_parameter_live_changed("stroke_m", v)
        )

        # Dead gap
        self.dead_gap_m_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("dead_gap_m", v)
        )
        self.dead_gap_m_slider.valueChanged.connect(
            lambda v: self._on_parameter_live_changed("dead_gap_m", v)
        )

        # Rod diameter
        self.rod_diameter_front_m_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("rod_diameter_m", v)
        )
        self.rod_diameter_front_m_slider.valueChanged.connect(
            lambda v: self._on_parameter_live_changed("rod_diameter_m", v)
        )
        self.rod_diameter_rear_m_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("rod_diameter_rear_m", v)
        )
        self.rod_diameter_rear_m_slider.valueChanged.connect(
            lambda v: self._on_parameter_live_changed("rod_diameter_rear_m", v)
        )

        # Piston rod length
        self.piston_rod_length_m_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("piston_rod_length_m", v)
        )
        self.piston_rod_length_m_slider.valueChanged.connect(
            lambda v: self._on_parameter_live_changed("piston_rod_length_m", v)
        )

        # Piston thickness
        self.piston_thickness_m_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("piston_thickness_m", v)
        )
        self.piston_thickness_m_slider.valueChanged.connect(
            lambda v: self._on_parameter_live_changed("piston_thickness_m", v)
        )

    def _on_parameter_changed(self, param_name: str, value: float):
        """Handle parameter change (final)"""
        self.state_manager.set_parameter(param_name, value)
        if param_name in {"rod_diameter_m", "rod_diameter_rear_m"}:
            self._sync_rod_sliders_from_state(param_name)
        self.parameter_changed.emit(param_name, value)

    def _on_parameter_live_changed(self, param_name: str, value: float):
        """Handle parameter change (real-time)"""
        self.state_manager.set_parameter(param_name, value)
        if param_name in {"rod_diameter_m", "rod_diameter_rear_m"}:
            self._sync_rod_sliders_from_state(param_name)
        self.parameter_live_changed.emit(param_name, value)

    def _load_from_state(self):
        """Load values from state manager"""
        params = [
            ("cylinder_length", self.cylinder_length_slider),
            ("cyl_diam_m", self.cyl_diam_m_slider),
            ("stroke_m", self.stroke_m_slider),
            ("dead_gap_m", self.dead_gap_m_slider),
            ("rod_diameter_m", self.rod_diameter_front_m_slider),
            ("rod_diameter_rear_m", self.rod_diameter_rear_m_slider),
            ("piston_rod_length_m", self.piston_rod_length_m_slider),
            ("piston_thickness_m", self.piston_thickness_m_slider),
        ]

        for param_name, slider in params:
            value = self.state_manager.get_parameter(param_name)
            if value is not None:
                slider.setValue(value)

    def update_from_state(self):
        """Update widgets from current state"""
        self._load_from_state()

    def update_link_state(self, linked: bool):
        """Enable or disable rear rod diameter editing based on link option."""

        self.rod_diameter_rear_m_slider.setEnabled(not linked)
        if linked:
            value = self.state_manager.get_parameter("rod_diameter_m")
            self.rod_diameter_rear_m_slider.blockSignals(True)
            try:
                self.rod_diameter_rear_m_slider.setValue(value)
            finally:
                self.rod_diameter_rear_m_slider.blockSignals(False)
        else:
            self._update_rod_sliders_from_state()

    def set_enabled(self, enabled: bool):
        """Enable/disable all controls"""
        self.cylinder_length_slider.setEnabled(enabled)
        self.cyl_diam_m_slider.setEnabled(enabled)
        self.stroke_m_slider.setEnabled(enabled)
        self.dead_gap_m_slider.setEnabled(enabled)
        self.rod_diameter_front_m_slider.setEnabled(enabled)
        self.rod_diameter_rear_m_slider.setEnabled(enabled)
        self.piston_rod_length_m_slider.setEnabled(enabled)
        self.piston_thickness_m_slider.setEnabled(enabled)

    def _sync_rod_sliders_from_state(self, source_param: str) -> None:
        """Mirror linked rod diameter values between sliders."""

        if not self.state_manager.get_parameter("link_rod_diameters"):
            return

        target_param = (
            "rod_diameter_rear_m"
            if source_param == "rod_diameter_m"
            else "rod_diameter_m"
        )
        target_slider = (
            self.rod_diameter_rear_m_slider
            if target_param == "rod_diameter_rear_m"
            else self.rod_diameter_front_m_slider
        )
        target_value = self.state_manager.get_parameter(target_param)
        if target_value is None:
            return

        target_slider.blockSignals(True)
        try:
            target_slider.setValue(target_value)
        finally:
            target_slider.blockSignals(False)

    def _update_rod_sliders_from_state(self) -> None:
        """Apply independent rod values from the state manager."""

        for param_name, slider in (
            ("rod_diameter_m", self.rod_diameter_front_m_slider),
            ("rod_diameter_rear_m", self.rod_diameter_rear_m_slider),
        ):
            value = self.state_manager.get_parameter(param_name)
            if value is None:
                continue

            slider.blockSignals(True)
            try:
                slider.setValue(value)
            finally:
                slider.blockSignals(False)


__all__ = ["CylinderTab"]
