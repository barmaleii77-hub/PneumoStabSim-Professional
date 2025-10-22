# -*- coding: utf-8 -*-
"""
Frame dimensions tab - Вкладка размеров рамы
Controls for wheelbase and track width
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox
from PySide6.QtCore import Signal

from ...widgets import RangeSlider
from .state_manager import GeometryStateManager
from .defaults import get_parameter_limits, get_parameter_metadata


class FrameTab(QWidget):
    """Вкладка размеров рамы

    Frame dimensions configuration tab

    Controls:
    - Wheelbase (колёсная база)
    - Track width (колея)
    """

    # Signals
    parameter_changed = Signal(str, float)  # parameter_name, new_value
    parameter_live_changed = Signal(str, float)  # For real-time updates

    def __init__(self, state_manager: GeometryStateManager, parent=None):
        """Initialize frame tab

        Args:
            state_manager: Shared state manager
            parent: Parent widget
        """
        super().__init__(parent)

        self.state_manager = state_manager

        # Setup UI
        self._setup_ui()

        # Load initial values from state
        self._load_from_state()

        # Connect signals
        self._connect_signals()

    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # Frame dimensions group
        group = QGroupBox("Размеры рамы")
        group_layout = QVBoxLayout(group)
        group_layout.setSpacing(4)

        # Wheelbase slider
        limits = get_parameter_limits("wheelbase")
        metadata = get_parameter_metadata("wheelbase")

        self.wheelbase_slider = RangeSlider(
            minimum=limits["min"],
            maximum=limits["max"],
            value=self.state_manager.get_parameter("wheelbase"),
            step=limits["step"],
            decimals=limits["decimals"],
            units=metadata["units"],
            title=metadata["title"],
        )
        self.wheelbase_slider.setToolTip(metadata["description"])
        group_layout.addWidget(self.wheelbase_slider)

        # Track width slider
        limits = get_parameter_limits("track")
        metadata = get_parameter_metadata("track")

        self.track_slider = RangeSlider(
            minimum=limits["min"],
            maximum=limits["max"],
            value=self.state_manager.get_parameter("track"),
            step=limits["step"],
            decimals=limits["decimals"],
            units=metadata["units"],
            title=metadata["title"],
        )
        self.track_slider.setToolTip(metadata["description"])
        group_layout.addWidget(self.track_slider)

        layout.addWidget(group)
        layout.addStretch()

    def _connect_signals(self):
        """Connect widget signals"""
        # Wheelbase
        self.wheelbase_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("wheelbase", v)
        )
        self.wheelbase_slider.valueChanged.connect(
            lambda v: self._on_parameter_live_changed("wheelbase", v)
        )

        # Track
        self.track_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("track", v)
        )
        self.track_slider.valueChanged.connect(
            lambda v: self._on_parameter_live_changed("track", v)
        )

    def _on_parameter_changed(self, param_name: str, value: float):
        """Handle parameter change (final)

        Args:
            param_name: Parameter name
            value: New value
        """
        # Update state
        self.state_manager.set_parameter(param_name, value)

        # Emit signal
        self.parameter_changed.emit(param_name, value)

    def _on_parameter_live_changed(self, param_name: str, value: float):
        """Handle parameter change (real-time)

        Args:
            param_name: Parameter name
            value: New value
        """
        # Update state
        self.state_manager.set_parameter(param_name, value)

        # Emit signal
        self.parameter_live_changed.emit(param_name, value)

    def _load_from_state(self):
        """Load values from state manager"""
        wheelbase = self.state_manager.get_parameter("wheelbase")
        track = self.state_manager.get_parameter("track")

        if wheelbase is not None:
            self.wheelbase_slider.setValue(wheelbase)

        if track is not None:
            self.track_slider.setValue(track)

    def update_from_state(self):
        """Update widgets from current state (external change)"""
        self._load_from_state()

    def set_enabled(self, enabled: bool):
        """Enable/disable all controls

        Args:
            enabled: True to enable, False to disable
        """
        self.wheelbase_slider.setEnabled(enabled)
        self.track_slider.setEnabled(enabled)
