# -*- coding: utf-8 -*-
"""
Physics tab for ModesPanel
Вкладка опций физических компонентов
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QCheckBox, QLabel
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from .state_manager import ModesStateManager


class PhysicsTab(QWidget):
    """Вкладка опций физики"""

    # Signals
    physics_options_changed = Signal(dict)  # Physics option toggles

    def __init__(self, state_manager: ModesStateManager, parent=None):
        super().__init__(parent)
        self.state_manager = state_manager
        self._setup_ui()
        self._apply_current_state()

    def _setup_ui(self):
        """Создать UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Title
        title_label = QLabel("Физические компоненты")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Description
        desc_label = QLabel(
            "Выберите, какие компоненты учитывать при расчёте.\n"
            "Отключение компонентов ускоряет симуляцию."
        )
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #888888;")
        desc_font = QFont()
        desc_font.setPointSize(8)
        desc_label.setFont(desc_font)
        layout.addWidget(desc_label)

        # Components group
        components_group = self._create_components_group()
        layout.addWidget(components_group)

        layout.addStretch()

    def _create_components_group(self) -> QGroupBox:
        """Создать группу компонентов"""
        group = QGroupBox("Включённые компоненты")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        # Springs checkbox
        self.include_springs_check = QCheckBox("🌀 Включить пружины")
        self.include_springs_check.setToolTip(
            "Учитывать упругость механических пружин.\n"
            "Важно для реалистичного поведения подвески."
        )
        self.include_springs_check.setChecked(True)
        self.include_springs_check.toggled.connect(
            lambda checked: self._on_option_changed("include_springs", checked)
        )

        # Dampers checkbox
        self.include_dampers_check = QCheckBox("🔧 Включить демпферы")
        self.include_dampers_check.setToolTip(
            "Учитывать демпфирование амортизаторов.\n"
            "Гасит колебания и предотвращает резонанс."
        )
        self.include_dampers_check.setChecked(True)
        self.include_dampers_check.toggled.connect(
            lambda checked: self._on_option_changed("include_dampers", checked)
        )

        # Pneumatics checkbox
        self.include_pneumatics_check = QCheckBox("💨 Включить пневматику")
        self.include_pneumatics_check.setToolTip(
            "Учитывать пневматическую систему стабилизатора.\n"
            "Основной компонент активной подвески."
        )
        self.include_pneumatics_check.setChecked(True)
        self.include_pneumatics_check.toggled.connect(
            lambda checked: self._on_option_changed("include_pneumatics", checked)
        )

        layout.addWidget(self.include_springs_check)
        layout.addWidget(self.include_dampers_check)
        layout.addWidget(self.include_pneumatics_check)

        # Info about components
        info_layout = QVBoxLayout()
        info_layout.setContentsMargins(10, 10, 10, 10)

        info_label = QLabel(
            "<b>Влияние компонентов:</b><br>"
            "• <b>Пружины</b> — основная упругость (k)<br>"
            "• <b>Демпферы</b> — затухание колебаний (c)<br>"
            "• <b>Пневматика</b> — активная стабилизация"
        )
        info_label.setWordWrap(True)
        info_label.setStyleSheet(
            "color: #666666; background-color: #f5f5f5; padding: 8px; border-radius: 4px;"
        )
        info_font = QFont()
        info_font.setPointSize(8)
        info_label.setFont(info_font)
        info_layout.addWidget(info_label)

        layout.addLayout(info_layout)

        return group

    def _on_option_changed(self, option_name: str, checked: bool):
        """Обработать изменение опции"""
        print(f"⚙️ PhysicsTab: Опция '{option_name}' = {checked}")

        # Update state
        self.state_manager.update_physics_option(option_name, checked)

        # Emit signal with all options
        self.physics_options_changed.emit(self.state_manager.get_physics_options())

    def _apply_current_state(self):
        """Применить текущее состояние к UI"""
        options = self.state_manager.get_physics_options()

        # Block signals during update
        self.include_springs_check.blockSignals(True)
        self.include_dampers_check.blockSignals(True)
        self.include_pneumatics_check.blockSignals(True)

        # Update checkboxes
        self.include_springs_check.setChecked(options.get("include_springs", True))
        self.include_dampers_check.setChecked(options.get("include_dampers", True))
        self.include_pneumatics_check.setChecked(
            options.get("include_pneumatics", True)
        )

        # Unblock signals
        self.include_springs_check.blockSignals(False)
        self.include_dampers_check.blockSignals(False)
        self.include_pneumatics_check.blockSignals(False)

    def set_enabled_for_running(self, running: bool):
        """Включить/выключить элементы при запущенной симуляции"""
        enabled = not running
        self.include_springs_check.setEnabled(enabled)
        self.include_dampers_check.setEnabled(enabled)
        self.include_pneumatics_check.setEnabled(enabled)
