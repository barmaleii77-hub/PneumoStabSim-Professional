"""
Geometry Panel - Refactored Coordinator (v1.0.0)
Тонкий координатор с делегированием работы вкладкам
"""

import logging
from typing import Any, Mapping

from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel, QSizePolicy
from PySide6.QtCore import Signal, Slot, QTimer, Qt
from PySide6.QtGui import QCloseEvent, QFont

from .state_manager import GeometryStateManager
from .frame_tab import FrameTab
from .suspension_tab import SuspensionTab
from .cylinder_tab import CylinderTab
from .options_tab import OptionsTab
from .defaults import DEFAULT_GEOMETRY
from src.common.settings_manager import get_settings_manager
from src.core.history import HistoryStack
from src.core.settings_sync_controller import SettingsSyncController
from src.ui.panels.preset_manager import PanelPresetManager
from src.ui.geometry_schema import (
    GeometrySettings,
    GeometryValidationError,
    validate_geometry_settings,
)
from src.common.ui_dialogs import dialogs_allowed, message_question


try:
    _VALIDATED_FIELD_NAMES = frozenset(
        validate_geometry_settings(DEFAULT_GEOMETRY).to_config_dict().keys()
    )
except GeometryValidationError:  # pragma: no cover - defensive guardrail
    _VALIDATED_FIELD_NAMES = frozenset(DEFAULT_GEOMETRY.keys())


def _build_geometry_settings(
    snapshot: Mapping[str, Any], logger: logging.Logger
) -> GeometrySettings:
    """Validate *snapshot* and convert it into :class:`GeometrySettings`.

    The geometry panel historically allowed callers to request the current
    parameters as a plain dictionary.  Modern unit tests expect that the
    snapshot is validated against :mod:`src.ui.geometry_schema` before being
    exposed to external consumers.  This helper keeps the coordinator lean
    while providing a single location for validation and fallbacks.
    """

    try:
        return validate_geometry_settings(snapshot)
    except GeometryValidationError as exc:
        logger.warning("Geometry settings validation failed, using fallback: %s", exc)
        fallback_payload = {
            key: snapshot.get(key, DEFAULT_GEOMETRY.get(key))
            for key in _VALIDATED_FIELD_NAMES
        }
        return GeometrySettings(fallback_payload)


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

        initial_state = self.state_manager.get_all_parameters()
        self._history = HistoryStack()
        self._sync_controller = SettingsSyncController(
            initial_state=initial_state, history=self._history
        )
        self._sync_controller.register_listener(self._on_state_synced)
        self.preset_manager = PanelPresetManager("geometry", self._sync_controller)
        self._sync_guard = 0

        # Conflict resolution state
        self._resolving_conflict = False

        # Setup UI
        self._setup_ui()

        # Connect signals
        self._connect_signals()

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
        tooltip = self.preset_manager.get_tooltip(
            "tab_widget",
            "Выберите вкладку для изменения параметров геометрии",
        )
        if tooltip:
            self.tab_widget.setToolTip(tooltip)

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

        reset_tip = self.preset_manager.get_tooltip(
            "options_reset", "Сбросить геометрию к значениям по умолчанию"
        )
        if reset_tip:
            self.options_tab.reset_button.setToolTip(reset_tip)
        validate_tip = self.preset_manager.get_tooltip(
            "options_validate", "Проверить корректность настроек геометрии"
        )
        if validate_tip:
            self.options_tab.validate_button.setToolTip(validate_tip)

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

            self._apply_sync_patch(
                {param_name: self.state_manager.get_parameter(param_name)},
                description=f"Update geometry.{param_name}",
            )

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
        self.cylinder_tab.update_link_state(
            bool(self.state_manager.get_parameter("link_rod_diameters"))
        )

        # Emit update signals
        self.geometry_updated.emit(self.state_manager.get_all_parameters())
        geometry_3d = self.state_manager.get_3d_geometry_update()
        self.geometry_changed.emit(geometry_3d)
        metadata = self.preset_manager.record_application(
            "geometry", preset_params.get("name")
        )
        self._apply_sync_state(
            self.state_manager.get_all_parameters(),
            description=metadata.get(
                "description", f"Apply geometry preset {preset_params.get('name')}"
            ),
            origin="preset",
        )

    @Slot(str, bool)
    def _on_option_changed(self, option_name: str, value: bool):
        """Handle option change

        Args:
            option_name: Option name
            value: Option value
        """
        self.logger.info(f"Option changed: {option_name} = {value}")
        self.parameter_changed.emit(option_name, float(value))
        self.geometry_updated.emit(self.state_manager.get_all_parameters())
        if option_name == "link_rod_diameters":
            self.cylinder_tab.update_from_state()
            self.cylinder_tab.update_link_state(value)
        self._apply_sync_patch(
            {option_name: self.state_manager.get_parameter(option_name)},
            description=f"Update geometry option {option_name}",
        )

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
        self._apply_sync_state(
            self.state_manager.get_all_parameters(),
            description="Reset geometry defaults",
            origin="preset",
        )

    @Slot()
    def _on_validate_requested(self):
        """Handle validation request"""
        self.logger.info("Validation requested")
        # Validation result shown by OptionsTab dialog

    def _apply_sync_patch(
        self,
        patch: Mapping[str, Any],
        *,
        description: str,
        origin: str = "local",
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        if self._sync_guard:
            return
        meta = {"panel": "geometry"}
        if metadata:
            meta.update(dict(metadata))
        self._sync_controller.apply_patch(
            dict(patch),
            description=description,
            origin=origin,
            metadata=meta,
        )

    def _apply_sync_state(
        self,
        state: Mapping[str, Any],
        *,
        description: str,
        origin: str = "external",
        metadata: Mapping[str, Any] | None = None,
    ) -> None:
        if self._sync_guard:
            return
        meta = {"panel": "geometry"}
        if metadata:
            meta.update(dict(metadata))
        self._sync_controller.apply_state(
            dict(state),
            description=description,
            origin=origin,
            metadata=meta,
        )

    def _on_state_synced(
        self, state: Mapping[str, Any], context: Mapping[str, Any]
    ) -> None:
        origin = str(context.get("origin", ""))
        if origin == "local" and not context.get("force_refresh"):
            return

        self._sync_guard += 1
        try:
            self.state_manager.update_parameters(dict(state))
            self.frame_tab.update_from_state()
            self.suspension_tab.update_from_state()
            self.cylinder_tab.update_from_state()
            self.cylinder_tab.update_link_state(
                bool(self.state_manager.get_parameter("link_rod_diameters"))
            )
            self.geometry_updated.emit(self.state_manager.get_all_parameters())
            geometry_3d = self.state_manager.get_3d_geometry_update()
            self.geometry_changed.emit(geometry_3d)
        finally:
            self._sync_guard -= 1

    # =========================================================================
    # CONFLICT RESOLUTION
    # =========================================================================

    def _resolve_conflict(self, conflict_info: dict):
        """Resolve parameter conflict

        В интерактивном режиме Asking the user; in headless/tests or
        when dialogs are suppressed - reverting to the previous value without blocking.
        """
        self._resolving_conflict = True
        try:
            changed_param = conflict_info.get("changed_param")
            prev_value = conflict_info.get("previous_value")
            options = list(conflict_info.get("options", ()))
            message = str(conflict_info.get("message", "Конфликт параметров"))

            if not dialogs_allowed():
                # Без модального окна: безопасный откат к предыдущему значению
                if changed_param is not None and prev_value is not None:
                    self.state_manager.set_parameter(changed_param, prev_value)
                    self._update_tab_widget(changed_param, prev_value)
                self.logger.warning("Conflict auto-resolved without dialog: %s", message)
                return

            # Интерактивный путь — короткий вопрос (Да/Нет) для принятия первого варианта
            if options:
                first_text, param_name, suggested_value = options[0]
                proceed = message_question(
                    self,
                    "Конфликт параметров",
                    f"{message}\n\nПрименить вариант: {first_text}?",
                    default_yes=False,
                )
                if proceed:
                    self.state_manager.set_parameter(param_name, suggested_value)
                    self._update_tab_widget(param_name, suggested_value)
                else:
                    if changed_param is not None and prev_value is not None:
                        self.state_manager.set_parameter(changed_param, prev_value)
                        self._update_tab_widget(changed_param, prev_value)
            else:
                # Нет вариантов — просто откатываемся
                if changed_param is not None and prev_value is not None:
                    self.state_manager.set_parameter(changed_param, prev_value)
                    self._update_tab_widget(changed_param, prev_value)

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

    def _collect_state_snapshot(self) -> dict[str, Any]:
        """Return a shallow copy of the current panel state."""
        return dict(self.state_manager.get_all_parameters())

    def get_geometry_settings(self) -> GeometrySettings:
        """Return the validated geometry configuration for the current state."""
        snapshot = self._collect_state_snapshot()
        return _build_geometry_settings(snapshot, self.logger)

    def get_parameters(self) -> dict[str, Any]:
        """Return a snapshot of the current geometry parameters as a mapping."""
        snapshot = self._collect_state_snapshot()
        settings = self.get_geometry_settings()
        snapshot.update(settings.to_config_dict())
        return snapshot

    def set_parameters(self, params: dict):
        """Set geometry parameters

        Args:
            params: Dictionary of parameter values
        """
        self._resolving_conflict = True
        try:
            self.state_manager.update_parameters(params)
            self.frame_tab.update_from_state()
            self.suspension_tab.update_from_state()
            self.cylinder_tab.update_from_state()
        finally:
            self._resolving_conflict = False

        self._apply_sync_state(
            self.state_manager.get_all_parameters(),
            description="External geometry set_parameters",
            origin="external",
        )

    def undo_last_change(self) -> bool:
        return self._sync_controller.undo() is not None

    def redo_last_change(self) -> bool:
        return self._sync_controller.redo() is not None

    def apply_registered_preset(self, preset_id: str) -> bool:
        return self.preset_manager.apply_registered_preset(preset_id) is not None

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

    def closeEvent(self, event: QCloseEvent) -> None:
        """Handle close event - save settings

        Args:
            event: Close event
        """
        self.state_manager.save_state()
        super().closeEvent(event)
