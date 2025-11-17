"""
Physics tab for ModesPanel
Вкладка опций физических компонентов
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QCheckBox,
    QLabel,
    QDoubleSpinBox,
    QFormLayout,
    QComboBox,
)
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

        self.include_springs_kinematics_check = QCheckBox("🌀 Пружины в кинематике")
        self.include_springs_kinematics_check.setToolTip(
            "Учитывать упругость в кинематических расчётах (предзагрузка, геометрия)."
        )
        self.include_springs_kinematics_check.toggled.connect(
            lambda checked: self._on_option_changed("include_springs_kinematics", checked)
        )

        self.include_dampers_kinematics_check = QCheckBox("🔧 Демпферы в кинематике")
        self.include_dampers_kinematics_check.setToolTip(
            "Учитывать демпферы при вычислении кинематических смещений."
        )
        self.include_dampers_kinematics_check.toggled.connect(
            lambda checked: self._on_option_changed("include_dampers_kinematics", checked)
        )

        layout.addWidget(self.include_springs_check)
        layout.addWidget(self.include_dampers_check)
        layout.addWidget(self.include_pneumatics_check)
        layout.addWidget(self.include_springs_kinematics_check)
        layout.addWidget(self.include_dampers_kinematics_check)

        tuning_form = QFormLayout()
        tuning_form.setContentsMargins(4, 8, 4, 8)
        tuning_form.setSpacing(6)

        self.spring_constant_spin = QDoubleSpinBox()
        self.spring_constant_spin.setRange(1_000.0, 200_000.0)
        self.spring_constant_spin.setSuffix(" Н/м")
        self.spring_constant_spin.setDecimals(0)
        self.spring_constant_spin.setSingleStep(500.0)
        self.spring_constant_spin.valueChanged.connect(
            lambda value: self._on_option_changed("spring_constant", value)
        )
        tuning_form.addRow("Жёсткость пружин", self.spring_constant_spin)

        self.damper_coefficient_spin = QDoubleSpinBox()
        self.damper_coefficient_spin.setRange(0.0, 20_000.0)
        self.damper_coefficient_spin.setSuffix(" Н·с/м")
        self.damper_coefficient_spin.setDecimals(0)
        self.damper_coefficient_spin.setSingleStep(200.0)
        self.damper_coefficient_spin.valueChanged.connect(
            lambda value: self._on_option_changed("damper_coefficient", value)
        )
        tuning_form.addRow("Коэф. демпфера", self.damper_coefficient_spin)

        self.damper_threshold_spin = QDoubleSpinBox()
        self.damper_threshold_spin.setRange(0.0, 10_000.0)
        self.damper_threshold_spin.setSuffix(" Н")
        self.damper_threshold_spin.setDecimals(0)
        self.damper_threshold_spin.setSingleStep(10.0)
        self.damper_threshold_spin.valueChanged.connect(
            lambda value: self._on_option_changed("damper_force_threshold_n", value)
        )
        tuning_form.addRow("Порог демпфера", self.damper_threshold_spin)

        self.spring_rest_position_spin = QDoubleSpinBox()
        self.spring_rest_position_spin.setRange(-0.2, 0.2)
        self.spring_rest_position_spin.setSuffix(" м")
        self.spring_rest_position_spin.setDecimals(3)
        self.spring_rest_position_spin.setSingleStep(0.001)
        self.spring_rest_position_spin.valueChanged.connect(
            lambda value: self._on_option_changed("spring_rest_position_m", value)
        )
        tuning_form.addRow("Смещение нуля", self.spring_rest_position_spin)

        self.inertia_multiplier_spin = QDoubleSpinBox()
        self.inertia_multiplier_spin.setRange(0.1, 5.0)
        self.inertia_multiplier_spin.setDecimals(2)
        self.inertia_multiplier_spin.setSingleStep(0.1)
        self.inertia_multiplier_spin.valueChanged.connect(
            lambda value: self._on_option_changed("lever_inertia_multiplier", value)
        )
        tuning_form.addRow("Множитель инерции", self.inertia_multiplier_spin)

        self.integrator_combo = QComboBox()
        self.integrator_combo.addItem("RK4 (устойчивый)", "rk4")
        self.integrator_combo.addItem("Эйлер (быстрый)", "euler")
        self.integrator_combo.currentIndexChanged.connect(self._on_integrator_changed)
        tuning_form.addRow("Интегратор рычага", self.integrator_combo)

        layout.addLayout(tuning_form)

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
        self.include_springs_kinematics_check.blockSignals(True)
        self.include_dampers_kinematics_check.blockSignals(True)
        self.spring_constant_spin.blockSignals(True)
        self.damper_coefficient_spin.blockSignals(True)
        self.inertia_multiplier_spin.blockSignals(True)
        self.damper_threshold_spin.blockSignals(True)
        self.spring_rest_position_spin.blockSignals(True)
        self.integrator_combo.blockSignals(True)

        # Update checkboxes
        self.include_springs_check.setChecked(options.get("include_springs", True))
        self.include_dampers_check.setChecked(options.get("include_dampers", True))
        self.include_pneumatics_check.setChecked(
            options.get("include_pneumatics", True)
        )
        self.include_springs_kinematics_check.setChecked(
            options.get("include_springs_kinematics", True)
        )
        self.include_dampers_kinematics_check.setChecked(
            options.get("include_dampers_kinematics", True)
        )
        self.spring_constant_spin.setValue(
            float(options.get("spring_constant", 50_000.0))
        )
        self.damper_coefficient_spin.setValue(
            float(options.get("damper_coefficient", 2_000.0))
        )
        self.damper_threshold_spin.setValue(
            float(options.get("damper_force_threshold_n", 50.0))
        )
        self.spring_rest_position_spin.setValue(
            float(options.get("spring_rest_position_m", 0.0))
        )
        self.inertia_multiplier_spin.setValue(
            float(options.get("lever_inertia_multiplier", 1.0))
        )
        method = str(options.get("integrator_method", "rk4")).strip().lower()
        if method not in {"rk4", "euler"}:
            method = "rk4"
        idx = self.integrator_combo.findData(method)
        if idx < 0:
            idx = 0
        self.integrator_combo.setCurrentIndex(idx)

        # Unblock signals
        self.include_springs_check.blockSignals(False)
        self.include_dampers_check.blockSignals(False)
        self.include_pneumatics_check.blockSignals(False)
        self.include_springs_kinematics_check.blockSignals(False)
        self.include_dampers_kinematics_check.blockSignals(False)
        self.spring_constant_spin.blockSignals(False)
        self.damper_coefficient_spin.blockSignals(False)
        self.inertia_multiplier_spin.blockSignals(False)
        self.damper_threshold_spin.blockSignals(False)
        self.spring_rest_position_spin.blockSignals(False)
        self.integrator_combo.blockSignals(False)

    def set_enabled_for_running(self, running: bool):
        """Включить/выключить элементы при запущенной симуляции"""
        enabled = not running
        self.include_springs_check.setEnabled(enabled)
        self.include_dampers_check.setEnabled(enabled)
        self.include_pneumatics_check.setEnabled(enabled)
        self.include_springs_kinematics_check.setEnabled(enabled)
        self.include_dampers_kinematics_check.setEnabled(enabled)
        self.spring_constant_spin.setEnabled(enabled)
        self.damper_coefficient_spin.setEnabled(enabled)
        self.inertia_multiplier_spin.setEnabled(enabled)
        self.damper_threshold_spin.setEnabled(enabled)
        self.spring_rest_position_spin.setEnabled(enabled)
        self.integrator_combo.setEnabled(enabled)

    def _on_integrator_changed(self, index: int) -> None:
        if index < 0:
            return
        method = self.integrator_combo.itemData(index)
        if not method:
            return
        self._on_option_changed("integrator_method", method)
