"""
Simulation tab for ModesPanel
Вкладка выбора режима симуляции и пресетов
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QRadioButton,
    QButtonGroup,
    QLabel,
    QComboBox,
    QCheckBox,
    QDoubleSpinBox,
)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QFont

from .state_manager import ModesStateManager
from .defaults import MODE_PRESETS, PRESET_NAMES


class SimulationTab(QWidget):
    """Вкладка режима симуляции"""

    # Signals
    mode_changed = Signal(str, str)  # mode_type, new_mode
    preset_changed = Signal(int)  # preset_index

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
        title_label = QLabel("Режим симуляции")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Preset selector
        preset_group = self._create_preset_group()
        layout.addWidget(preset_group)

        # Simulation type (Kinematics/Dynamics)
        sim_type_group = self._create_sim_type_group()
        layout.addWidget(sim_type_group)

        # Thermodynamic mode
        thermo_group = self._create_thermo_group()
        layout.addWidget(thermo_group)

        safety_group = self._create_safety_group()
        layout.addWidget(safety_group)

        layout.addStretch()

    def _create_preset_group(self) -> QGroupBox:
        """Создать группу выбора пресета"""
        group = QGroupBox("Быстрые пресеты")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)

        # Preset selector
        preset_layout = QHBoxLayout()
        preset_label = QLabel("Пресет:")
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(PRESET_NAMES)
        self.preset_combo.setCurrentIndex(0)
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)

        preset_layout.addWidget(preset_label)
        preset_layout.addWidget(self.preset_combo, stretch=1)
        layout.addLayout(preset_layout)

        # Preset description
        self.preset_desc_label = QLabel()
        self.preset_desc_label.setWordWrap(True)
        self.preset_desc_label.setStyleSheet("color: #888888;")
        desc_font = QFont()
        desc_font.setPointSize(8)
        self.preset_desc_label.setFont(desc_font)
        layout.addWidget(self.preset_desc_label)

        # Update description
        self._update_preset_description(0)

        return group

    def _create_sim_type_group(self) -> QGroupBox:
        """Создать группу выбора типа симуляции"""
        group = QGroupBox("Тип расчёта")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        # Info label
        info_label = QLabel("Выберите метод расчёта физики:")
        info_label.setWordWrap(True)
        info_font = QFont()
        info_font.setPointSize(8)
        info_label.setFont(info_font)
        layout.addWidget(info_label)

        # Radio buttons
        self.sim_type_group = QButtonGroup()

        self.kinematics_radio = QRadioButton("Кинематика")
        self.kinematics_radio.setToolTip(
            "Упрощённый расчёт только геометрии.\nБыстро, но без учёта физических сил."
        )

        self.dynamics_radio = QRadioButton("Динамика")
        self.dynamics_radio.setToolTip(
            "Полный физический расчёт с силами.\nТочно, но требует больше ресурсов."
        )

        self.kinematics_radio.setChecked(True)

        self.sim_type_group.addButton(self.kinematics_radio, 0)
        self.sim_type_group.addButton(self.dynamics_radio, 1)

        # Connect signal
        self.sim_type_group.buttonToggled.connect(self._on_sim_type_changed)

        layout.addWidget(self.kinematics_radio)
        layout.addWidget(self.dynamics_radio)

        return group

    def _create_thermo_group(self) -> QGroupBox:
        """Создать группу термодинамического режима"""
        group = QGroupBox("Термодинамика пневматики")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        # Info label
        info_label = QLabel("Модель газового процесса:")
        info_label.setWordWrap(True)
        info_font = QFont()
        info_font.setPointSize(8)
        info_label.setFont(info_font)
        layout.addWidget(info_label)

        # Radio buttons
        self.thermo_group = QButtonGroup()

        self.isothermal_radio = QRadioButton("Изотермический")
        self.isothermal_radio.setToolTip(
            "Постоянная температура (T = const).\nМедленные процессы с теплообменом."
        )

        self.adiabatic_radio = QRadioButton("Адиабатический")
        self.adiabatic_radio.setToolTip(
            "Без теплообмена (Q = 0).\nБыстрые процессы, изменение температуры."
        )

        self.isothermal_radio.setChecked(True)

        self.thermo_group.addButton(self.isothermal_radio, 0)
        self.thermo_group.addButton(self.adiabatic_radio, 1)

        # Connect signal
        self.thermo_group.buttonToggled.connect(self._on_thermo_changed)

        layout.addWidget(self.isothermal_radio)
        layout.addWidget(self.adiabatic_radio)

        return group

    def _create_safety_group(self) -> QGroupBox:
        """Переключатели проверки пересечений и температуры среды"""

        group = QGroupBox("Проверки и среда")
        layout = QVBoxLayout(group)
        layout.setSpacing(8)

        self.interference_check = QCheckBox("🧱 Проверять пересечения")
        self.interference_check.setToolTip(
            "Включить проверку пересечений элементов подвески при расчёте."
        )
        self.interference_check.toggled.connect(self._on_interference_changed)
        layout.addWidget(self.interference_check)

        ambient_row = QHBoxLayout()
        ambient_label = QLabel("Температура среды, °C")
        ambient_row.addWidget(ambient_label)

        self.ambient_spin = QDoubleSpinBox()
        self.ambient_spin.setRange(-80.0, 150.0)
        self.ambient_spin.setDecimals(1)
        self.ambient_spin.setSuffix(" °C")
        self.ambient_spin.setSingleStep(0.5)
        self.ambient_spin.valueChanged.connect(self._on_ambient_changed)
        ambient_row.addWidget(self.ambient_spin, stretch=1)

        layout.addLayout(ambient_row)

        return group

    def _on_preset_changed(self, index: int):
        """Обработать изменение пресета"""
        print(f"📋 SimulationTab: Пресет изменён на '{PRESET_NAMES[index]}'")

        # Update description
        self._update_preset_description(index)

        # Apply preset to state
        updates = self.state_manager.apply_preset(index)

        # Update UI from state (don't emit signals during update)
        if updates and not updates.get("custom"):
            self._apply_current_state()

        # Emit signal
        self.preset_changed.emit(index)

    def _update_preset_description(self, preset_index: int):
        """Обновить описание пресета"""
        if preset_index in MODE_PRESETS:
            desc = MODE_PRESETS[preset_index].get("description", "")
            self.preset_desc_label.setText(desc)

    def _on_sim_type_changed(self):
        """Обработать изменение типа симуляции"""
        if self.kinematics_radio.isChecked():
            mode = "KINEMATICS"
        else:
            mode = "DYNAMICS"

        print(f"🔧 SimulationTab: Тип симуляции изменён на '{mode}'")

        # Update state
        self.state_manager.update_parameter("sim_type", mode)

        # Switch to custom preset if manual change
        if self.preset_combo.currentIndex() != 4:
            self.preset_combo.setCurrentIndex(4)

        # Emit signal
        self.mode_changed.emit("sim_type", mode)

    def _on_thermo_changed(self):
        """Обработать изменение термо-режима"""
        if self.isothermal_radio.isChecked():
            mode = "ISOTHERMAL"
        else:
            mode = "ADIABATIC"

        print(f"🌡️ SimulationTab: Термо-режим изменён на '{mode}'")

        # Update state
        self.state_manager.update_parameter("thermo_mode", mode)

        # Switch to custom preset if manual change
        if self.preset_combo.currentIndex() != 4:
            self.preset_combo.setCurrentIndex(4)

        # Emit signal
        self.mode_changed.emit("thermo_mode", mode)

    def _on_interference_changed(self, checked: bool):
        """Обработать переключение проверки пересечений"""

        self.state_manager.update_parameter("check_interference", bool(checked))
        if self.preset_combo.currentIndex() != 4:
            self.preset_combo.setCurrentIndex(4)
        self.mode_changed.emit("check_interference", "true" if checked else "false")

    def _on_ambient_changed(self, value: float):
        """Обработать изменение температуры среды"""

        self.state_manager.update_parameter("ambient_temperature_c", float(value))
        if self.preset_combo.currentIndex() != 4:
            self.preset_combo.setCurrentIndex(4)
        self.mode_changed.emit("ambient_temperature_c", f"{value:.1f}")

    def _apply_current_state(self):
        """Применить текущее состояние к UI"""
        params = self.state_manager.get_parameters()

        # Block signals during update
        self.sim_type_group.blockSignals(True)
        self.thermo_group.blockSignals(True)

        # Update sim type
        sim_type = params.get("sim_type", "KINEMATICS")
        if sim_type == "KINEMATICS":
            self.kinematics_radio.setChecked(True)
        else:
            self.dynamics_radio.setChecked(True)

        # Update thermo mode
        thermo_mode = params.get("thermo_mode", "ISOTHERMAL")
        if thermo_mode == "ISOTHERMAL":
            self.isothermal_radio.setChecked(True)
        else:
            self.adiabatic_radio.setChecked(True)

        self.interference_check.blockSignals(True)
        self.interference_check.setChecked(
            bool(params.get("check_interference", False))
        )
        self.interference_check.blockSignals(False)

        ambient = float(params.get("ambient_temperature_c", 20.0) or 0)
        self.ambient_spin.blockSignals(True)
        self.ambient_spin.setValue(ambient)
        self.ambient_spin.blockSignals(False)

        # Unblock signals
        self.sim_type_group.blockSignals(False)
        self.thermo_group.blockSignals(False)

    def set_enabled_for_running(self, running: bool):
        """Включить/выключить элементы при запущенной симуляции"""
        enabled = not running
        self.preset_combo.setEnabled(enabled)
        self.kinematics_radio.setEnabled(enabled)
        self.dynamics_radio.setEnabled(enabled)
        self.isothermal_radio.setEnabled(enabled)
        self.adiabatic_radio.setEnabled(enabled)
        self.interference_check.setEnabled(enabled)
        self.ambient_spin.setEnabled(enabled)
