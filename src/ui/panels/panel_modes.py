# -*- coding: utf-8 -*-
"""
Simulation modes configuration panel - РУССКИЙ ИНТЕРФЕЙС
Полная интеграция с SettingsManager: без дефолтов в коде, читаем при запуске,
записываем при выходе (централизованно в MainWindow), дефолты обновляем по кнопке.
"""
from __future__ import annotations

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QRadioButton,
    QCheckBox,
    QPushButton,
    QLabel,
    QButtonGroup,
    QSizePolicy,
    QComboBox,
    QSlider,
    QDoubleSpinBox,
    QSpinBox,
)
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QFont

from src.common.settings_manager import get_settings_manager


class StandardSlider(QWidget):
    """Стандартный слайдер Qt с полем ввода - компактная версия для ModesPanel"""

    valueEdited = Signal(float)

    def __init__(
        self,
        minimum=0.0,
        maximum=100.0,
        value=50.0,
        step=1.0,
        decimals=2,
        units="",
        title="",
        parent=None,
    ):
        super().__init__(parent)

        self._minimum = minimum
        self._maximum = maximum
        self._step = step
        self._decimals = decimals
        self._units = units
        self._updating = False

        self._setup_ui(title)
        self.setValue(value)

    def _setup_ui(self, title):
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        if title:
            title_label = QLabel(title)
            font = QFont()
            font.setPointSize(8)
            font.setBold(True)
            title_label.setFont(font)
            layout.addWidget(title_label)

        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(4)

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1000)
        self.slider.setMinimumWidth(80)
        controls_layout.addWidget(self.slider, stretch=2)

        if self._decimals == 0:
            self.spinbox = QSpinBox()
            self.spinbox.setMinimum(int(self._minimum))
            self.spinbox.setMaximum(int(self._maximum))
            self.spinbox.setSingleStep(int(self._step))
        else:
            self.spinbox = QDoubleSpinBox()
            self.spinbox.setDecimals(self._decimals)
            self.spinbox.setMinimum(self._minimum)
            self.spinbox.setMaximum(self._maximum)
            self.spinbox.setSingleStep(self._step)

        self.spinbox.setMinimumWidth(50)
        self.spinbox.setMaximumWidth(70)
        controls_layout.addWidget(self.spinbox)

        if self._units:
            units_label = QLabel(self._units)
            font = QFont()
            font.setPointSize(8)
            units_label.setFont(font)
            controls_layout.addWidget(units_label)

        layout.addLayout(controls_layout)

        self.slider.valueChanged.connect(self._on_slider_changed)
        self.spinbox.valueChanged.connect(self._on_spinbox_changed)

    def setValue(self, value):
        value = max(self._minimum, min(self._maximum, value))
        self._updating = True
        self.spinbox.setValue(value)
        if self._maximum > self._minimum:
            ratio = (value - self._minimum) / (self._maximum - self._minimum)
            self.slider.setValue(int(ratio * 1000))
        self._updating = False

    def value(self):
        return self.spinbox.value()

    @Slot(int)
    def _on_slider_changed(self, slider_value):
        if self._updating:
            return
        ratio = slider_value / 1000.0
        value = self._minimum + ratio * (self._maximum - self._minimum)
        if self._step > 0:
            steps = round((value - self._minimum) / self._step)
            value = self._minimum + steps * self._step
        value = max(self._minimum, min(self._maximum, value))
        self._updating = True
        self.spinbox.setValue(value)
        self._updating = False
        self.valueEdited.emit(value)

    @Slot()
    def _on_spinbox_changed(self, value):
        if self._updating:
            return
        if self._maximum > self._minimum:
            ratio = (value - self._minimum) / (self._maximum - self._minimum)
            self._updating = True
            self.slider.setValue(int(ratio * 1000))
            self._updating = False
        self.valueEdited.emit(value)


class ModesPanel(QWidget):
    """Панель конфигурации режимов симуляции"""

    # Signals
    simulation_control = Signal(str)
    mode_changed = Signal(str, str)
    parameter_changed = Signal(str, float)
    physics_options_changed = Signal(dict)
    animation_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._settings_manager = get_settings_manager()
        self.parameters: dict[str, float | str] = {}
        self.physics_options: dict[str, bool] = {}

        # 1) Загружаем состояние до построения UI
        self._load_from_settings()

        # 2) UI
        self._setup_ui()
        self._apply_state_to_widgets()

        # 3) Signals
        self._connect_signals()

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

    def _load_from_settings(self) -> None:
        data = self._settings_manager.get_category("modes") or {}
        self.physics_options = dict(data.get("physics", {}))
        # копируем остальные поля кроме physics
        self.parameters = {k: v for k, v in data.items() if k != "physics"}

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        title_label = QLabel("Режимы симуляции")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        preset_layout = QHBoxLayout()
        preset_label = QLabel("Пресет режима:")
        self.mode_preset_combo = QComboBox()
        self.mode_preset_combo.addItems(
            [
                "Стандартный",
                "Только кинематика",
                "Полная динамика",
                "Тест пневматики",
                "Пользовательский",
            ]
        )
        self.mode_preset_combo.currentIndexChanged.connect(self._on_mode_preset_changed)
        preset_layout.addWidget(preset_label)
        preset_layout.addWidget(self.mode_preset_combo, stretch=1)
        layout.addLayout(preset_layout)

        control_group = self._create_control_group()
        layout.addWidget(control_group)

        mode_group = self._create_mode_group()
        layout.addWidget(mode_group)

        physics_group = self._create_physics_group()
        layout.addWidget(physics_group)

        road_group = self._create_road_group()
        layout.addWidget(road_group)

        # Кнопки сброса/дефолтов
        bottom = QHBoxLayout()
        self.reset_button = QPushButton("↩︎ Сбросить (defaults)")
        self.reset_button.clicked.connect(self._reset_to_defaults)
        bottom.addWidget(self.reset_button)
        self.save_defaults_button = QPushButton("💾 Сохранить как дефолт")
        self.save_defaults_button.clicked.connect(self._save_current_as_defaults)
        bottom.addWidget(self.save_defaults_button)
        bottom.addStretch()
        layout.addLayout(bottom)

        layout.addStretch()

    def _create_control_group(self) -> QGroupBox:
        group = QGroupBox("Управление симуляцией")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        buttons_layout = QHBoxLayout()
        buttons_layout.setSpacing(8)
        self.start_button = QPushButton("▶ Старт")
        self.stop_button = QPushButton("⏹ Стоп")
        self.pause_button = QPushButton("⏸ Пауза")
        self.reset_sim_button = QPushButton("🔄 Сброс")
        for b in (
            self.start_button,
            self.stop_button,
            self.pause_button,
            self.reset_sim_button,
        ):
            b.setMinimumHeight(30)
        self.start_button.setToolTip("Запустить симуляцию")
        self.stop_button.setToolTip("Остановить симуляцию")
        self.pause_button.setToolTip("Приостановить симуляцию")
        self.reset_sim_button.setToolTip("Сбросить симуляцию к начальному состоянию")
        buttons_layout.addWidget(self.start_button)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addWidget(self.pause_button)
        buttons_layout.addWidget(self.reset_sim_button)
        layout.addLayout(buttons_layout)
        return group

    def _create_mode_group(self) -> QGroupBox:
        group = QGroupBox("Тип симуляции")
        layout = QHBoxLayout(group)
        layout.setSpacing(16)

        sim_type_widget = QWidget()
        sim_type_layout = QVBoxLayout(sim_type_widget)
        sim_type_layout.setSpacing(4)
        sim_type_label = QLabel("Режим физики")
        sim_type_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        sim_type_label.setFont(font)
        sim_type_layout.addWidget(sim_type_label)
        self.sim_type_group = QButtonGroup()
        self.kinematics_radio = QRadioButton("Кинематика")
        self.dynamics_radio = QRadioButton("Динамика")
        self.sim_type_group.addButton(self.kinematics_radio, 0)
        self.sim_type_group.addButton(self.dynamics_radio, 1)
        sim_type_layout.addWidget(self.kinematics_radio)
        sim_type_layout.addWidget(self.dynamics_radio)
        layout.addWidget(sim_type_widget)

        thermo_widget = QWidget()
        thermo_layout = QVBoxLayout(thermo_widget)
        thermo_layout.setSpacing(4)
        thermo_label = QLabel("Термо-режим")
        thermo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        thermo_label.setFont(font)
        thermo_layout.addWidget(thermo_label)
        self.thermo_group = QButtonGroup()
        self.isothermal_radio = QRadioButton("Изотермический")
        self.adiabatic_radio = QRadioButton("Адиабатический")
        self.thermo_group.addButton(self.isothermal_radio, 0)
        self.thermo_group.addButton(self.adiabatic_radio, 1)
        thermo_layout.addWidget(self.isothermal_radio)
        thermo_layout.addWidget(self.adiabatic_radio)
        layout.addWidget(thermo_widget)

        return group

    def _create_physics_group(self) -> QGroupBox:
        group = QGroupBox("Опции физики")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        self.include_springs_check = QCheckBox("Включить пружины")
        self.include_dampers_check = QCheckBox("Включить демпферы")
        self.include_pneumatics_check = QCheckBox("Включить пневматику")
        self.include_springs_check.setToolTip("Учитывать упругость пружин")
        self.include_dampers_check.setToolTip("Учитывать демпфирование амортизаторов")
        self.include_pneumatics_check.setToolTip("Учитывать пневматическую систему")
        layout.addWidget(self.include_springs_check)
        layout.addWidget(self.include_dampers_check)
        layout.addWidget(self.include_pneumatics_check)
        return group

    def _create_road_group(self) -> QGroupBox:
        group = QGroupBox("Дорожное воздействие")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)
        # Значения берём из загруженных параметров
        self.amplitude_slider = StandardSlider(
            minimum=0.0,
            maximum=0.2,
            value=float(self.parameters.get("amplitude", 0) or 0),
            step=0.001,
            decimals=3,
            units="м",
            title="Глобальная амплитуда",
        )
        layout.addWidget(self.amplitude_slider)
        self.frequency_slider = StandardSlider(
            minimum=0.1,
            maximum=10.0,
            value=float(self.parameters.get("frequency", 0) or 0),
            step=0.1,
            decimals=1,
            units="Гц",
            title="Глобальная частота",
        )
        layout.addWidget(self.frequency_slider)
        self.phase_slider = StandardSlider(
            minimum=0.0,
            maximum=360.0,
            value=float(self.parameters.get("phase", 0) or 0),
            step=15.0,
            decimals=0,
            units="°",
            title="Глобальная фаза",
        )
        layout.addWidget(self.phase_slider)

        per_wheel_label = QLabel("Фазовые сдвиги по колёсам")
        font = QFont()
        font.setPointSize(9)
        font.setBold(True)
        per_wheel_label.setFont(font)
        layout.addWidget(per_wheel_label)

        wheel_layout = QHBoxLayout()
        wheel_layout.setSpacing(8)
        lf_widget = QWidget()
        lf_layout = QVBoxLayout(lf_widget)
        lf_layout.setContentsMargins(2, 2, 2, 2)
        lf_layout.setSpacing(2)
        lf_label = QLabel("ЛП")
        lf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lf_layout.addWidget(lf_label)
        self.lf_phase_slider = StandardSlider(
            minimum=0.0,
            maximum=360.0,
            value=float(self.parameters.get("lf_phase", 0) or 0),
            step=15.0,
            decimals=0,
            units="°",
            title="",
        )
        lf_layout.addWidget(self.lf_phase_slider)
        wheel_layout.addWidget(lf_widget)

        rf_widget = QWidget()
        rf_layout = QVBoxLayout(rf_widget)
        rf_layout.setContentsMargins(2, 2, 2, 2)
        rf_layout.setSpacing(2)
        rf_label = QLabel("ПП")
        rf_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rf_layout.addWidget(rf_label)
        self.rf_phase_slider = StandardSlider(
            minimum=0.0,
            maximum=360.0,
            value=float(self.parameters.get("rf_phase", 0) or 0),
            step=15.0,
            decimals=0,
            units="°",
            title="",
        )
        rf_layout.addWidget(self.rf_phase_slider)
        wheel_layout.addWidget(rf_widget)

        lr_widget = QWidget()
        lr_layout = QVBoxLayout(lr_widget)
        lr_layout.setContentsMargins(2, 2, 2, 2)
        lr_layout.setSpacing(2)
        lr_label = QLabel("ЛЗ")
        lr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        lr_layout.addWidget(lr_label)
        self.lr_phase_slider = StandardSlider(
            minimum=0.0,
            maximum=360.0,
            value=float(self.parameters.get("lr_phase", 0) or 0),
            step=15.0,
            decimals=0,
            units="°",
            title="",
        )
        lr_layout.addWidget(self.lr_phase_slider)
        wheel_layout.addWidget(lr_widget)

        rr_widget = QWidget()
        rr_layout = QVBoxLayout(rr_widget)
        rr_layout.setContentsMargins(2, 2, 2, 2)
        rr_layout.setSpacing(2)
        rr_label = QLabel("ПЗ")
        rr_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        rr_layout.addWidget(rr_label)
        self.rr_phase_slider = StandardSlider(
            minimum=0.0,
            maximum=360.0,
            value=float(self.parameters.get("rr_phase", 0) or 0),
            step=15.0,
            decimals=0,
            units="°",
            title="",
        )
        rr_layout.addWidget(self.rr_phase_slider)
        wheel_layout.addWidget(rr_widget)

        layout.addLayout(wheel_layout)
        return group

    def _apply_state_to_widgets(self) -> None:
        # Preset combo text
        preset = str(self.parameters.get("mode_preset", "Пользовательский"))
        if preset and preset != "Пользовательский":
            # Try to select matching preset name
            idx = (
                self.mode_preset_combo.findText(preset)
                if isinstance(preset, str)
                else -1
            )
            if idx >= 0:
                self.mode_preset_combo.setCurrentIndex(idx)

        # Simulation type
        sim_type = str(self.parameters.get("sim_type", ""))
        self.kinematics_radio.setChecked(sim_type == "KINEMATICS")
        self.dynamics_radio.setChecked(sim_type == "DYNAMICS")

        # Thermo mode
        thermo = str(self.parameters.get("thermo_mode", ""))
        self.isothermal_radio.setChecked(thermo == "ISOTHERMAL")
        self.adiabatic_radio.setChecked(thermo == "ADIABATIC")

        # Physics options
        self.include_springs_check.setChecked(
            bool(self.physics_options.get("include_springs", False))
        )
        self.include_dampers_check.setChecked(
            bool(self.physics_options.get("include_dampers", False))
        )
        self.include_pneumatics_check.setChecked(
            bool(self.physics_options.get("include_pneumatics", False))
        )

        # Sliders already init with values from parameters

    def _connect_signals(self):
        # Control buttons
        self.start_button.clicked.connect(lambda: self.simulation_control.emit("start"))
        self.stop_button.clicked.connect(lambda: self.simulation_control.emit("stop"))
        self.pause_button.clicked.connect(lambda: self.simulation_control.emit("pause"))
        self.reset_sim_button.clicked.connect(
            lambda: self.simulation_control.emit("reset")
        )

        # Mode radio buttons
        self.sim_type_group.buttonToggled.connect(self._on_sim_type_changed)
        self.thermo_group.buttonToggled.connect(self._on_thermo_mode_changed)

        # Physics options checkboxes
        self.include_springs_check.toggled.connect(
            lambda checked: self._on_physics_option_changed("include_springs", checked)
        )
        self.include_dampers_check.toggled.connect(
            lambda checked: self._on_physics_option_changed("include_dampers", checked)
        )
        self.include_pneumatics_check.toggled.connect(
            lambda checked: self._on_physics_option_changed(
                "include_pneumatics", checked
            )
        )

        # Road excitation sliders
        self.amplitude_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("amplitude", v)
        )
        self.frequency_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("frequency", v)
        )
        self.phase_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("phase", v)
        )
        self.lf_phase_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("lf_phase", v)
        )
        self.rf_phase_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("rf_phase", v)
        )
        self.lr_phase_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("lr_phase", v)
        )
        self.rr_phase_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("rr_phase", v)
        )

    @Slot(int)
    def _on_mode_preset_changed(self, index: int):
        presets = {
            0: {
                "sim_type": "KINEMATICS",
                "thermo_mode": "ISOTHERMAL",
                "include_springs": True,
                "include_dampers": True,
                "include_pneumatics": True,
            },
            1: {
                "sim_type": "KINEMATICS",
                "thermo_mode": "ISOTHERMAL",
                "include_springs": False,
                "include_dampers": False,
                "include_pneumatics": False,
            },
            2: {
                "sim_type": "DYNAMICS",
                "thermo_mode": "ADIABATIC",
                "include_springs": True,
                "include_dampers": True,
                "include_pneumatics": True,
            },
            3: {
                "sim_type": "DYNAMICS",
                "thermo_mode": "ISOTHERMAL",
                "include_springs": False,
                "include_dampers": False,
                "include_pneumatics": True,
            },
            4: {"custom": True},
        }
        preset = presets.get(index, {})
        if "custom" not in preset:
            self.kinematics_radio.setChecked(preset.get("sim_type") == "KINEMATICS")
            self.dynamics_radio.setChecked(preset.get("sim_type") == "DYNAMICS")
            self.isothermal_radio.setChecked(preset.get("thermo_mode") == "ISOTHERMAL")
            self.adiabatic_radio.setChecked(preset.get("thermo_mode") == "ADIABATIC")
            self.include_springs_check.setChecked(preset.get("include_springs", False))
            self.include_dampers_check.setChecked(preset.get("include_dampers", False))
            self.include_pneumatics_check.setChecked(
                preset.get("include_pneumatics", False)
            )
        self.parameters["mode_preset"] = self.mode_preset_combo.currentText()

    @Slot()
    def _on_sim_type_changed(self):
        mode = "KINEMATICS" if self.kinematics_radio.isChecked() else "DYNAMICS"
        self.parameters["sim_type"] = mode
        self.mode_changed.emit("sim_type", mode)
        if self.mode_preset_combo.currentIndex() != 4:
            self.mode_preset_combo.setCurrentIndex(4)

    @Slot()
    def _on_thermo_mode_changed(self):
        mode = "ISOTHERMAL" if self.isothermal_radio.isChecked() else "ADIABATIC"
        self.parameters["thermo_mode"] = mode
        self.mode_changed.emit("thermo_mode", mode)
        if self.mode_preset_combo.currentIndex() != 4:
            self.mode_preset_combo.setCurrentIndex(4)

    @Slot(str, bool)
    def _on_physics_option_changed(self, option_name: str, checked: bool):
        self.physics_options[option_name] = bool(checked)
        self.physics_options_changed.emit(self.physics_options.copy())
        if self.mode_preset_combo.currentIndex() != 4:
            self.mode_preset_combo.setCurrentIndex(4)

    @Slot(str, float)
    def _on_parameter_changed(self, param_name: str, value: float):
        self.parameters[param_name] = value
        self.parameter_changed.emit(param_name, value)
        if param_name in [
            "amplitude",
            "frequency",
            "phase",
            "lf_phase",
            "rf_phase",
            "lr_phase",
            "rr_phase",
        ]:
            animation_params = {
                "amplitude": float(self.parameters.get("amplitude", 0) or 0),
                "frequency": float(self.parameters.get("frequency", 0) or 0),
                "phase": float(self.parameters.get("phase", 0) or 0),
                "lf_phase": float(self.parameters.get("lf_phase", 0) or 0),
                "rf_phase": float(self.parameters.get("rf_phase", 0) or 0),
                "lr_phase": float(self.parameters.get("lr_phase", 0) or 0),
                "rr_phase": float(self.parameters.get("rr_phase", 0) or 0),
            }
            self.animation_changed.emit(animation_params)

    def collect_state(self) -> dict:
        data = dict(self.parameters)
        data["physics"] = dict(self.physics_options)
        return data

    @Slot()
    def _reset_to_defaults(self):
        self._settings_manager.reset_to_defaults(category="modes")
        self._load_from_settings()
        self._apply_state_to_widgets()

    @Slot()
    def _save_current_as_defaults(self):
        state = self.collect_state()
        self._settings_manager.set_category("modes", state, auto_save=False)
        self._settings_manager.save_current_as_defaults(category="modes")
