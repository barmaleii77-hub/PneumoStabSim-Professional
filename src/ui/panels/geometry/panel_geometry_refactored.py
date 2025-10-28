# -*- coding: utf-8 -*-
"""
Geometry Panel - Refactored Coordinator (v1.0.0)
Тонкий координатор с делегированием работы вкладкам
"""

import logging
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel, QSizePolicy
from PySide6.QtCore import Signal, Slot, QTimer, Qt
from PySide6.QtGui import QFont

from .state_manager import GeometryStateManager
from .frame_tab import FrameTab
from .suspension_tab import SuspensionTab
from .cylinder_tab import CylinderTab
from .options_tab import OptionsTab
from src.common.settings_manager import get_settings_manager


class GeometryPanel(QWidget):
    """Панель конфигурации геометрии - Refactored Coordinator

    Geometry configuration panel (Russian UI)

    Architecture:
    - Thin coordinator pattern
    - Delegates work to specialized tabs
    - Aggregates signals from tabs
    - Manages shared state through StateManager
    """

    # Aggregated signals (for backward compatibility)
    parameter_changed = Signal(str, float)  # parameter_name, new_value
    geometry_updated = Signal(dict)  # Complete geometry dictionary
    geometry_changed = Signal(dict)  # 3D scene geometry update

    def __init__(self, parent=None):
        """Initialize geometry panel

        Args:
            parent: Parent widget
        """
        super().__init__(parent)

        # Logger
        self.logger = logging.getLogger(__name__)
        self.logger.info("GeometryPanel (refactored) initializing...")

        # Shared JSON settings manager
        self.settings_manager = get_settings_manager()

        # State manager (shared by all tabs)
        self.state_manager = GeometryStateManager(self.settings_manager)

        # Conflict resolution state
        self._resolving_conflict = False

        # Setup UI
        self._setup_ui()

        # Connect signals
        self._connect_signals()

        # Ensure widgets reflect persisted state before emitting updates
        self._apply_persisted_state()

        # Size policy
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        # Send initial geometry to QML (delayed)
        QTimer.singleShot(500, self._send_initial_geometry)

        self.logger.info("GeometryPanel initialized successfully")

    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # Title
        title_label = QLabel("Геометрия автомобиля")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Tab widget
        self.tab_widget = QTabWidget()

        # Create tabs (pass shared state manager)
        self.frame_tab = FrameTab(self.state_manager, self)
        self.suspension_tab = SuspensionTab(self.state_manager, self)
        self.cylinder_tab = CylinderTab(self.state_manager, self)
        self.options_tab = OptionsTab(self.state_manager, self)

        # Add tabs
        self.tab_widget.addTab(self.frame_tab, "Рама")
        self.tab_widget.addTab(self.suspension_tab, "Подвеска")
        self.tab_widget.addTab(self.cylinder_tab, "Цилиндры")
        self.tab_widget.addTab(self.options_tab, "Опции")

        layout.addWidget(self.tab_widget)

    def _connect_signals(self):
        """Connect signals from tabs"""
        self.logger.debug("Connecting tab signals...")

        # Frame tab
        self.frame_tab.parameter_changed.connect(self._on_tab_parameter_changed)
        self.frame_tab.parameter_live_changed.connect(
            self._on_tab_parameter_live_changed
        )

        # Suspension tab
        self.suspension_tab.parameter_changed.connect(self._on_tab_parameter_changed)
        self.suspension_tab.parameter_live_changed.connect(
            self._on_tab_parameter_live_changed
        )

        # Cylinder tab
        self.cylinder_tab.parameter_changed.connect(self._on_tab_parameter_changed)
        self.cylinder_tab.parameter_live_changed.connect(
            self._on_tab_parameter_live_changed
        )

        # Options tab
        self.options_tab.preset_applied.connect(self._on_preset_applied)
        self.options_tab.option_changed.connect(self._on_option_changed)
        self.options_tab.reset_requested.connect(self._on_reset_requested)
        self.options_tab.validate_requested.connect(self._on_validate_requested)

        self.logger.debug("Tab signals connected successfully")

    # =========================================================================
    # SIGNAL HANDLERS
    # =========================================================================

    @Slot(str, float)
    def _on_tab_parameter_changed(self, param_name: str, value: float):
        """Handle parameter change from tab (final)

        Args:
            param_name: Parameter name
            value: New value
        """
        if self._resolving_conflict:
            return

        old_value = self.state_manager.get_parameter(param_name)

        self.logger.debug(f"Parameter changed: {param_name} = {value}")

        # Check dependencies
        conflict = self.state_manager.check_dependencies(param_name, value, old_value)

        if conflict:
            self.logger.warning(f"Conflict detected: {conflict.get('type')}")
            conflict["previous_value"] = old_value
            self._resolve_conflict(conflict)
        else:
            # Emit signals
            self.parameter_changed.emit(param_name, value)
            self.geometry_updated.emit(self.state_manager.get_all_parameters())

            # Update 3D scene
            if param_name in self._get_3d_update_params():
                geometry_3d = self.state_manager.get_3d_geometry_update()
                self.geometry_changed.emit(geometry_3d)
                self.logger.debug(f"3D scene update sent for: {param_name}")

    @Slot(str, float)
    def _on_tab_parameter_live_changed(self, param_name: str, value: float):
        """Handle parameter change from tab (real-time)

        Args:
            param_name: Parameter name
            value: New value
        """
        if self._resolving_conflict:
            return

        # Update 3D scene in real-time
        if param_name in self._get_3d_update_params():
            geometry_3d = self.state_manager.get_3d_geometry_update()
            self.geometry_changed.emit(geometry_3d)

    @Slot(dict)
    def _on_preset_applied(self, preset_params: dict):
        """Handle preset application

        Args:
            preset_params: Preset parameters
        """
        self.logger.info(f"Applying preset: {preset_params.get('name', 'unknown')}")

        # Update all tabs from state
        self.frame_tab.update_from_state()
        self.suspension_tab.update_from_state()
        self.cylinder_tab.update_from_state()

        # Emit update signals
        self.geometry_updated.emit(self.state_manager.get_all_parameters())
        geometry_3d = self.state_manager.get_3d_geometry_update()
        self.geometry_changed.emit(geometry_3d)

    @Slot(str, bool)
    def _on_option_changed(self, option_name: str, value: bool):
        """Handle option change

        Args:
            option_name: Option name
            value: Option value
        """
        self.logger.info(f"Option changed: {option_name} = {value}")
        self.parameter_changed.emit(option_name, float(value))

    @Slot()
    def _on_reset_requested(self):
        """Handle reset request"""
        self.logger.info("Resetting to defaults")

        # Update all tabs from state
        self.frame_tab.update_from_state()
        self.suspension_tab.update_from_state()
        self.cylinder_tab.update_from_state()

        # Emit update signals
        self.geometry_updated.emit(self.state_manager.get_all_parameters())
        geometry_3d = self.state_manager.get_3d_geometry_update()
        self.geometry_changed.emit(geometry_3d)

    @Slot()
    def _on_validate_requested(self):
        """Handle validation request"""
        self.logger.info("Validation requested")
        # Validation result shown by OptionsTab dialog

    # =========================================================================
    # CONFLICT RESOLUTION
    # =========================================================================

    def _resolve_conflict(self, conflict_info: dict):
        """Resolve parameter conflict

        Args:
            conflict_info: Conflict information dictionary
        """
        from PySide6.QtWidgets import QMessageBox

        self._resolving_conflict = True

        try:
            # Create message box
            msg_box = QMessageBox(self)
            msg_box.setWindowTitle("Конфликт параметров")
            msg_box.setText(conflict_info["message"])
            msg_box.setInformativeText("Как вы хотите разрешить этот конфликт?")

            # Add resolution option buttons
            buttons = []
            for option_text, param_name, suggested_value in conflict_info["options"]:
                button = msg_box.addButton(
                    option_text, QMessageBox.ButtonRole.ActionRole
                )
                buttons.append((button, param_name, suggested_value))

            # Add cancel button
            cancel_button = msg_box.addButton(
                "Отмена", QMessageBox.ButtonRole.RejectRole
            )

            # Show dialog
            msg_box.exec()
            clicked_button = msg_box.clickedButton()

            if clicked_button == cancel_button:
                # Revert to previous value
                changed_param = conflict_info.get("changed_param")
                prev_value = conflict_info.get("previous_value")

                if changed_param and prev_value is not None:
                    self.state_manager.set_parameter(changed_param, prev_value)
                    self._update_tab_widget(changed_param, prev_value)
            else:
                # Apply selected resolution
                for button, param_name, suggested_value in buttons:
                    if clicked_button == button:
                        self.state_manager.set_parameter(param_name, suggested_value)
                        self._update_tab_widget(param_name, suggested_value)
                        break

                # Emit updates
                self.geometry_updated.emit(self.state_manager.get_all_parameters())
                geometry_3d = self.state_manager.get_3d_geometry_update()
                self.geometry_changed.emit(geometry_3d)

        finally:
            self._resolving_conflict = False

    def _update_tab_widget(self, param_name: str, value: float):
        """Update specific widget in tabs

        Args:
            param_name: Parameter name
            value: New value
        """
        # Update appropriate tab
        if param_name in ["wheelbase", "track"]:
            self.frame_tab.update_from_state()
        elif param_name in ["frame_to_pivot", "lever_length", "rod_position"]:
            self.suspension_tab.update_from_state()
        elif param_name in [
            "cylinder_length",
            "cyl_diam_m",
            "stroke_m",
            "dead_gap_m",
            "rod_diameter_m",
            "piston_rod_length_m",
            "piston_thickness_m",
        ]:
            self.cylinder_tab.update_from_state()

    # =========================================================================
    # PUBLIC API (backward compatibility)
    # =========================================================================

    def get_parameters(self) -> dict:
        """Get current geometry parameters

        Returns:
            Dictionary of current parameters
        """
        return self.state_manager.get_all_parameters()

    def set_parameters(self, params: dict):
        """Set geometry parameters

        Args:
            params: Dictionary of parameter values
        """
        self._resolving_conflict = True

        try:
            # Update state
            self.state_manager.update_parameters(params)

            # Update all tabs
            self.frame_tab.update_from_state()
            self.suspension_tab.update_from_state()
            self.cylinder_tab.update_from_state()

        finally:
            self._resolving_conflict = False

    # =========================================================================
    # HELPERS
    # =========================================================================

    def _send_initial_geometry(self):
        """Send initial geometry to QML"""
        self.logger.info("Sending initial geometry to QML...")

        geometry_3d = self.state_manager.get_3d_geometry_update()
        self.geometry_changed.emit(geometry_3d)
        self.geometry_updated.emit(self.state_manager.get_all_parameters())

        self.logger.info("Initial geometry sent successfully")

    @staticmethod
    def _get_3d_update_params() -> set:
        """Get parameters that trigger 3D scene updates

        Returns:
            Set of parameter names
        """
        return {
            "wheelbase",
            "track",
            "lever_length",
            "cylinder_length",
            "frame_to_pivot",
            "rod_position",
            "cyl_diam_m",
            "stroke_m",
            "dead_gap_m",
            "rod_diameter_m",
            "piston_rod_length_m",
            "piston_thickness_m",
        }

    def closeEvent(self, event):
        """Handle close event - save settings

        Args:
            event: Close event
        """
        self.state_manager.save_state()
        super().closeEvent(event)

    # =========================================================================
    # INTERNAL UTILITIES
    # =========================================================================

    def _apply_persisted_state(self) -> None:
        """Reload geometry from settings and refresh all tabs."""

        if self.settings_manager:
            try:
                self.state_manager.load_state()
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.warning("Failed to reload geometry state: %s", exc)

        self.frame_tab.update_from_state()
        self.suspension_tab.update_from_state()
        self.cylinder_tab.update_from_state()
