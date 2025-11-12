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
)
from PySide6.QtCore import Signal, Slot

from .state_manager import GeometryStateManager
from .defaults import PRESET_NAMES, get_preset_by_index
from src.common.ui_dialogs import (
    dialogs_allowed,
    message_info,
    message_warning,
    message_critical,
    message_question,
)


class OptionsTab(QWidget):
    """Вкладка опций и пресетов

    Controls:
    - Geometry presets combo
    - Interference checking checkbox
    - Link rod diameters checkbox
    - Reset button
    - Validate button
    """

    preset_changed = Signal(int)  # preset_index
    preset_applied = Signal(dict)  # preset_parameters
    option_changed = Signal(str, bool)  # option_name, value
    reset_requested = Signal()
    validate_requested = Signal()

    def __init__(self, state_manager: GeometryStateManager, parent=None):
        super().__init__(parent)
        self.state_manager = state_manager
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

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

        options_group = QGroupBox("Опции")
        options_layout = QVBoxLayout(options_group)
        options_layout.setSpacing(4)

        self.interference_check = QCheckBox("Проверять пересечения геометрии")
        self.interference_check.setChecked(
            self.state_manager.get_parameter("interference_check")
        )
        self.interference_check.setToolTip(
            "Автоматически проверять геометрические конфликты"
        )
        options_layout.addWidget(self.interference_check)

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

        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(4)

        self.reset_button = QPushButton("Сбросить")
        self.reset_button.setToolTip("Сбросить к значениям по умолчанию")
        buttons_layout.addWidget(self.reset_button)

        self.validate_button = QPushButton("Проверить")
        self.validate_button.setToolTip("Проверить корректность геометрии")
        buttons_layout.addWidget(self.validate_button)
        buttons_layout.addStretch()
        layout.addLayout(buttons_layout)
        layout.addStretch()

    def _connect_signals(self):
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        self.interference_check.toggled.connect(
            lambda checked: self._on_option_changed("interference_check", checked)
        )
        self.link_rod_diameters.toggled.connect(
            lambda checked: self._on_option_changed("link_rod_diameters", checked)
        )
        self.reset_button.clicked.connect(self._on_reset_clicked)
        self.validate_button.clicked.connect(self._on_validate_clicked)

    @Slot(int)
    def _on_preset_changed(self, index: int):
        self.preset_changed.emit(index)
        if index == 3:  # "Custom"
            return
        preset = get_preset_by_index(index)
        if preset:
            self.state_manager.update_parameters(preset)
            self.preset_applied.emit(preset)

    @Slot(str, bool)
    def _on_option_changed(self, option_name: str, value: bool):
        self.state_manager.set_parameter(option_name, value)
        self.option_changed.emit(option_name, value)
        if option_name == "interference_check":
            self._show_interference_toggle_feedback(bool(value))

    @Slot()
    def _on_reset_clicked(self):
        # Если диалоги запрещены — автосброс без подтверждения
        proceed = message_question(
            self,
            "Сбросить параметры",
            "Сбросить все параметры к значениям по умолчанию?",
            default_yes=not dialogs_allowed(),
        )
        if not proceed:
            return
        self.state_manager.reset_to_defaults()
        self.preset_combo.setCurrentIndex(0)
        self.interference_check.setChecked(True)
        self.link_rod_diameters.setChecked(False)
        self.reset_requested.emit()

    @Slot()
    def _on_validate_clicked(self):
        errors = self.state_manager.validate_geometry()
        warnings = self.state_manager.get_warnings()
        self._present_validation_results(errors, warnings)
        self.validate_requested.emit()

    def _show_interference_toggle_feedback(self, enabled: bool) -> None:
        message = (
            "Проверка пересечений геометрии включена."
            if enabled
            else "Проверка пересечений геометрии отключена."
        )
        message_info(self, "Проверка пересечений", message)
        if enabled:
            errors = self.state_manager.validate_geometry()
            warnings = self.state_manager.get_warnings()
            self._present_validation_results(errors, warnings)

    def _present_validation_results(self, errors: list[str], warnings: list[str]) -> None:
        if errors:
            message_critical(
                self, "Ошибки геометрии", "Обнаружены ошибки:\n\n" + "\n".join(errors)
            )
        elif warnings:
            message_warning(
                self,
                "Предупреждения геометрии",
                "Предупреждения:\n\n" + "\n".join(warnings),
            )
        else:
            message_info(self, "Проверка геометрии", "Все параметры геометрии корректны.")

    def set_preset_index(self, index: int):
        if 0 <= index < self.preset_combo.count():
            self.preset_combo.setCurrentIndex(index)

    def get_preset_index(self) -> int:
        return self.preset_combo.currentIndex()
