# -*- coding: utf-8 -*-
"""
Options tab - Вкладка опций
Presets, validation, and options
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QComboBox,
    QCheckBox,
    QPushButton,
    QLabel,
    QMessageBox,
)
from PySide6.QtCore import Signal, Slot

from .state_manager import GeometryStateManager
from .defaults import PRESET_NAMES, get_preset_by_index


class OptionsTab(QWidget):
    """Вкладка опций и пресетов

    Options and presets configuration tab

    Controls:
    - Geometry presets combo
    - Interference checking checkbox
    - Link rod diameters checkbox
    - Reset button
    - Validate button
    """

    # Signals
    preset_changed = Signal(int)  # preset_index
    preset_applied = Signal(dict)  # preset_parameters
    option_changed = Signal(str, bool)  # option_name, value
    reset_requested = Signal()
    validate_requested = Signal()

    def __init__(self, state_manager: GeometryStateManager, parent=None):
        """Initialize options tab

        Args:
            state_manager: Shared state manager
            parent: Parent widget
        """
        super().__init__(parent)

        self.state_manager = state_manager

        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup user interface"""
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        # Preset selector
        preset_group = QGroupBox("Пресеты геометрии")
        preset_layout = QVBoxLayout(preset_group)
        preset_layout.setSpacing(4)

        preset_selector_layout = QHBoxLayout()
        preset_label = QLabel("Пресет:")

        self.preset_combo = QComboBox()
        self.preset_combo.addItems(PRESET_NAMES)
        self.preset_combo.setCurrentIndex(0)

        preset_selector_layout.addWidget(preset_label)
        preset_selector_layout.addWidget(self.preset_combo, stretch=1)
        preset_layout.addLayout(preset_selector_layout)

        layout.addWidget(preset_group)

        # Options group
        options_group = QGroupBox("Опции")
        options_layout = QVBoxLayout(options_group)
        options_layout.setSpacing(4)

        # Interference checking
        self.interference_check = QCheckBox("Проверять пересечения геометрии")
        self.interference_check.setChecked(
            self.state_manager.get_parameter("interference_check")
        )
        self.interference_check.setToolTip(
            "Автоматически проверять геометрические конфликты"
        )
        options_layout.addWidget(self.interference_check)

        # Link rod diameters
        self.link_rod_diameters = QCheckBox(
            "Связать диаметры штоков передних/задних колёс"
        )
        self.link_rod_diameters.setChecked(
            self.state_manager.get_parameter("link_rod_diameters")
        )
        self.link_rod_diameters.setToolTip(
            "Синхронизировать диаметры штоков всех колёс"
        )
        options_layout.addWidget(self.link_rod_diameters)

        layout.addWidget(options_group)

        # Control buttons
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(4)

        # Reset button
        self.reset_button = QPushButton("Сбросить")
        self.reset_button.setToolTip("Сбросить к значениям по умолчанию")
        buttons_layout.addWidget(self.reset_button)

        # Validate button
        self.validate_button = QPushButton("Проверить")
        self.validate_button.setToolTip("Проверить корректность геометрии")
        buttons_layout.addWidget(self.validate_button)

        buttons_layout.addStretch()

        layout.addLayout(buttons_layout)
        layout.addStretch()

    def _connect_signals(self):
        """Connect widget signals"""
        # Preset combo
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)

        # Options checkboxes
        self.interference_check.toggled.connect(
            lambda checked: self._on_option_changed("interference_check", checked)
        )
        self.link_rod_diameters.toggled.connect(
            lambda checked: self._on_option_changed("link_rod_diameters", checked)
        )

        # Buttons
        self.reset_button.clicked.connect(self._on_reset_clicked)
        self.validate_button.clicked.connect(self._on_validate_clicked)

    @Slot(int)
    def _on_preset_changed(self, index: int):
        """Handle preset selection

        Args:
            index: Combo box index
        """
        # Emit preset index change
        self.preset_changed.emit(index)

        # Don't apply for "Custom" preset
        if index == 3:
            return

        # Get preset parameters
        preset = get_preset_by_index(index)

        if preset:
            # Update state manager
            self.state_manager.update_parameters(preset)

            # Emit preset parameters
            self.preset_applied.emit(preset)

    @Slot(str, bool)
    def _on_option_changed(self, option_name: str, value: bool):
        """Handle option checkbox change

        Args:
            option_name: Option name
            value: Checkbox state
        """
        # Update state
        self.state_manager.set_parameter(option_name, value)

        # Emit signal
        self.option_changed.emit(option_name, value)

        if option_name == "interference_check":
            self._show_interference_toggle_feedback(bool(value))

    @Slot()
    def _on_reset_clicked(self):
        """Handle reset button click"""
        # Confirm with user
        reply = QMessageBox.question(
            self,
            "Сбросить параметры",
            "Сбросить все параметры к значениям по умолчанию?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            # Reset state manager
            self.state_manager.reset_to_defaults()

            # Reset preset combo
            self.preset_combo.setCurrentIndex(0)

            # Reset checkboxes
            self.interference_check.setChecked(True)
            self.link_rod_diameters.setChecked(False)

            # Emit reset signal
            self.reset_requested.emit()

    @Slot()
    def _on_validate_clicked(self):
        """Handle validate button click"""
        # Validate geometry
        errors = self.state_manager.validate_geometry()
        warnings = self.state_manager.get_warnings()

        # Show results
        self._present_validation_results(errors, warnings)

        # Emit validate signal
        self.validate_requested.emit()

    def _show_interference_toggle_feedback(self, enabled: bool) -> None:
        message = (
            "Проверка пересечений геометрии включена."
            if enabled
            else "Проверка пересечений геометрии отключена."
        )
        QMessageBox.information(self, "Проверка пересечений", message)
        if enabled:
            errors = self.state_manager.validate_geometry()
            warnings = self.state_manager.get_warnings()
            self._present_validation_results(errors, warnings)

    def _present_validation_results(
        self, errors: list[str], warnings: list[str]
    ) -> None:
        if errors:
            QMessageBox.critical(
                self, "Ошибки геометрии", "Обнаружены ошибки:\n\n" + "\n".join(errors)
            )
        elif warnings:
            QMessageBox.warning(
                self,
                "Предупреждения геометрии",
                "Предупреждения:\n\n" + "\n".join(warnings),
            )
        else:
            QMessageBox.information(
                self, "Проверка геометрии", "Все параметры геометрии корректны."
            )

    def set_preset_index(self, index: int):
        """Set preset combo index programmatically

        Args:
            index: Preset index
        """
        if 0 <= index < self.preset_combo.count():
            self.preset_combo.setCurrentIndex(index)

    def get_preset_index(self) -> int:
        """Get current preset index

        Returns:
            Current preset index
        """
        return self.preset_combo.currentIndex()
