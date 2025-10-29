# -*- coding: utf-8 -*-
"""
Road excitation tab for ModesPanel
Вкладка дорожного воздействия (амплитуда, частота, фазы)
"""

import logging

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QLabel,
    QSlider,
    QDoubleSpinBox,
    QSpinBox,
    QCheckBox,
    QComboBox,
)
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QFont

from .state_manager import ModesStateManager
from .defaults import PARAMETER_RANGES


SMOOTHING_EASING_OPTIONS = [
    ("OutCubic", "OutCubic"),
    ("OutQuad", "OutQuad"),
    ("Linear", "Linear"),
    ("InOutSine", "InOutSine"),
]


LOGGER = logging.getLogger(__name__)


class StandardSlider(QWidget):
    """Стандартный слайдер с полем ввода"""

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
        """Создать UI"""
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        # Title
        if title:
            title_label = QLabel(title)
            font = QFont()
            font.setPointSize(8)
            font.setBold(True)
            title_label.setFont(font)
            layout.addWidget(title_label)

        # Slider + spinbox row
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(4)

        # Slider
        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1000)
        self.slider.setMinimumWidth(80)
        controls_layout.addWidget(self.slider, stretch=2)

        # Spinbox
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

        # Units label
        if self._units:
            units_label = QLabel(self._units)
            font = QFont()
            font.setPointSize(8)
            units_label.setFont(font)
            controls_layout.addWidget(units_label)

        layout.addLayout(controls_layout)

        # Connect signals
        self.slider.valueChanged.connect(self._on_slider_changed)
        self.spinbox.valueChanged.connect(self._on_spinbox_changed)

    def setValue(self, value):
        """Установить значение"""
        value = max(self._minimum, min(self._maximum, value))

        self._updating = True
        self.spinbox.setValue(value)

        if self._maximum > self._minimum:
            ratio = (value - self._minimum) / (self._maximum - self._minimum)
            slider_pos = int(ratio * 1000)
            self.slider.setValue(slider_pos)

        self._updating = False

    def value(self):
        """Получить значение"""
        return self.spinbox.value()

    @Slot(int)
    def _on_slider_changed(self, slider_value):
        """Обработать изменение слайдера"""
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
        """Обработать изменение spinbox"""
        if self._updating:
            return

        if self._maximum > self._minimum:
            ratio = (value - self._minimum) / (self._maximum - self._minimum)
            slider_pos = int(ratio * 1000)

            self._updating = True
            self.slider.setValue(slider_pos)
            self._updating = False

        self.valueEdited.emit(value)


class RoadExcitationTab(QWidget):
    """Вкладка дорожного воздействия"""

    # Signals
    parameter_changed = Signal(str, float)  # parameter_name, value
    animation_changed = Signal(dict)  # All animation parameters

    def __init__(self, state_manager: ModesStateManager, parent=None):
        super().__init__(parent)
        self.state_manager = state_manager
        self._smoothing_controls = []
        self._setup_ui()
        self._apply_current_state()

    def _setup_ui(self):
        """Создать UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        # Title
        title_label = QLabel("Дорожное воздействие")
        title_font = QFont()
        title_font.setPointSize(11)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        # Global parameters
        global_group = self._create_global_group()
        layout.addWidget(global_group)

        # Per-wheel phases
        wheels_group = self._create_wheels_group()
        layout.addWidget(wheels_group)

        # Animation smoothing controls
        smoothing_group = self._create_smoothing_group()
        layout.addWidget(smoothing_group)

        layout.addStretch()

    def _create_global_group(self) -> QGroupBox:
        """Создать группу глобальных параметров"""
        group = QGroupBox("Глобальные параметры")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)

        # Amplitude
        amp_range = PARAMETER_RANGES["amplitude"]
        self.amplitude_slider = StandardSlider(
            minimum=amp_range["min"],
            maximum=amp_range["max"],
            value=amp_range["default"],
            step=amp_range["step"],
            decimals=amp_range["decimals"],
            units=amp_range["unit"],
            title="Амплитуда",
        )
        self.amplitude_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("amplitude", v)
        )
        layout.addWidget(self.amplitude_slider)

        # Frequency
        freq_range = PARAMETER_RANGES["frequency"]
        self.frequency_slider = StandardSlider(
            minimum=freq_range["min"],
            maximum=freq_range["max"],
            value=freq_range["default"],
            step=freq_range["step"],
            decimals=freq_range["decimals"],
            units=freq_range["unit"],
            title="Частота",
        )
        self.frequency_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("frequency", v)
        )
        layout.addWidget(self.frequency_slider)

        # Global phase
        phase_range = PARAMETER_RANGES["phase"]
        self.phase_slider = StandardSlider(
            minimum=phase_range["min"],
            maximum=phase_range["max"],
            value=phase_range["default"],
            step=phase_range["step"],
            decimals=phase_range["decimals"],
            units=phase_range["unit"],
            title="Глобальная фаза",
        )
        self.phase_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("phase", v)
        )
        layout.addWidget(self.phase_slider)

        return group

    def _create_wheels_group(self) -> QGroupBox:
        """Создать группу фазовых сдвигов по колёсам"""
        group = QGroupBox("Фазовые сдвиги по колёсам")
        layout = QVBoxLayout(group)
        layout.setSpacing(4)

        # Info
        info_label = QLabel("Индивидуальные фазовые сдвиги для каждого колеса:")
        info_label.setWordWrap(True)
        info_font = QFont()
        info_font.setPointSize(8)
        info_label.setFont(info_font)
        layout.addWidget(info_label)

        # Wheel sliders in 2x2 grid
        wheel_layout = QHBoxLayout()
        wheel_layout.setSpacing(8)

        phase_range = PARAMETER_RANGES["wheel_phase"]

        # Store sliders
        self.wheel_sliders = {}

        # Left column (FL, RL)
        left_column = QVBoxLayout()
        left_column.setSpacing(6)

        # Front Left
        lf_slider = self._create_wheel_slider(
            "ЛП (Left Front)", phase_range, "lf_phase"
        )
        self.wheel_sliders["lf"] = lf_slider
        left_column.addWidget(lf_slider)

        # Rear Left
        lr_slider = self._create_wheel_slider("ЛЗ (Left Rear)", phase_range, "lr_phase")
        self.wheel_sliders["lr"] = lr_slider
        left_column.addWidget(lr_slider)

        wheel_layout.addLayout(left_column)

        # Right column (FR, RR)
        right_column = QVBoxLayout()
        right_column.setSpacing(6)

        # Front Right
        rf_slider = self._create_wheel_slider(
            "ПП (Right Front)", phase_range, "rf_phase"
        )
        self.wheel_sliders["rf"] = rf_slider
        right_column.addWidget(rf_slider)

        # Rear Right
        rr_slider = self._create_wheel_slider(
            "ПЗ (Right Rear)", phase_range, "rr_phase"
        )
        self.wheel_sliders["rr"] = rr_slider
        right_column.addWidget(rr_slider)

        wheel_layout.addLayout(right_column)

        layout.addLayout(wheel_layout)

        return group

    def _create_wheel_slider(
        self, title: str, phase_range: dict, param_name: str
    ) -> StandardSlider:
        """Создать слайдер для конкретного колеса"""
        slider = StandardSlider(
            minimum=phase_range["min"],
            maximum=phase_range["max"],
            value=phase_range["default"],
            step=phase_range["step"],
            decimals=phase_range["decimals"],
            units=phase_range["unit"],
            title=title,
        )
        slider.valueEdited.connect(
            lambda v, p=param_name: self._on_parameter_changed(p, v)
        )
        return slider

    def _create_smoothing_group(self) -> QGroupBox:
        group = QGroupBox("Сглаживание анимации")
        layout = QVBoxLayout(group)
        layout.setSpacing(6)

        self.smoothing_checkbox = QCheckBox("Включить сглаживание")
        self.smoothing_checkbox.toggled.connect(self._on_smoothing_toggled)
        layout.addWidget(self.smoothing_checkbox)

        duration_range = PARAMETER_RANGES["smoothing_duration_ms"]
        self.smoothing_duration_slider = StandardSlider(
            minimum=duration_range["min"],
            maximum=duration_range["max"],
            value=duration_range["default"],
            step=duration_range["step"],
            decimals=duration_range["decimals"],
            units=duration_range["unit"],
            title="Время сглаживания",
        )
        self.smoothing_duration_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("smoothing_duration_ms", v)
        )
        layout.addWidget(self.smoothing_duration_slider)

        angle_range = PARAMETER_RANGES["smoothing_angle_snap_deg"]
        self.smoothing_angle_slider = StandardSlider(
            minimum=angle_range["min"],
            maximum=angle_range["max"],
            value=angle_range["default"],
            step=angle_range["step"],
            decimals=angle_range["decimals"],
            units=angle_range["unit"],
            title="Порог снапинга угла",
        )
        self.smoothing_angle_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("smoothing_angle_snap_deg", v)
        )
        layout.addWidget(self.smoothing_angle_slider)

        piston_range = PARAMETER_RANGES["smoothing_piston_snap_m"]
        self.smoothing_piston_slider = StandardSlider(
            minimum=piston_range["min"],
            maximum=piston_range["max"],
            value=piston_range["default"],
            step=piston_range["step"],
            decimals=piston_range["decimals"],
            units=piston_range["unit"],
            title="Порог снапинга поршня",
        )
        self.smoothing_piston_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("smoothing_piston_snap_m", v)
        )
        layout.addWidget(self.smoothing_piston_slider)

        self.smoothing_easing_combo = QComboBox()
        for label, key in SMOOTHING_EASING_OPTIONS:
            self.smoothing_easing_combo.addItem(label, key)
        self.smoothing_easing_combo.currentIndexChanged.connect(
            self._on_smoothing_easing_changed
        )
        layout.addWidget(self.smoothing_easing_combo)

        self._smoothing_controls.extend(
            [
                self.smoothing_duration_slider,
                self.smoothing_angle_slider,
                self.smoothing_piston_slider,
                self.smoothing_easing_combo,
            ]
        )

        return group

    def _on_parameter_changed(self, param_name: str, value: float):
        """Обработать изменение параметра"""
        LOGGER.debug(
            "RoadExcitationTab parameter changed",
            extra={"param": param_name, "value": value},
        )

        # Update state
        self.state_manager.update_parameter(param_name, value)

        # Emit individual parameter change
        self.parameter_changed.emit(param_name, value)

        # Emit animation update
        self._emit_animation_update()

    def _emit_animation_update(self):
        animation_params = self.state_manager.get_animation_parameters()
        self.animation_changed.emit(animation_params)

    def _set_smoothing_controls_enabled(self, enabled: bool):
        for widget in self._smoothing_controls:
            widget.setEnabled(enabled)

    def _on_smoothing_toggled(self, enabled: bool):
        LOGGER.debug(
            "RoadExcitationTab smoothing toggled", extra={"enabled": bool(enabled)}
        )
        self.state_manager.update_parameter("smoothing_enabled", bool(enabled))
        self._set_smoothing_controls_enabled(bool(enabled))
        self.parameter_changed.emit("smoothing_enabled", 1.0 if enabled else 0.0)
        self._emit_animation_update()

    def _on_smoothing_easing_changed(self, index: int):
        value = self.smoothing_easing_combo.itemData(index)
        if value is None:
            return
        self.state_manager.update_parameter("smoothing_easing", value)
        self.parameter_changed.emit("smoothing_easing", float(index))
        self._emit_animation_update()

    def _apply_current_state(self):
        """Применить текущее состояние к UI"""
        params = self.state_manager.get_parameters()

        # Block signals during update
        self.amplitude_slider.blockSignals(True)
        self.frequency_slider.blockSignals(True)
        self.phase_slider.blockSignals(True)
        for slider in self.wheel_sliders.values():
            slider.blockSignals(True)

        self.smoothing_checkbox.blockSignals(True)
        smoothing_enabled = bool(params.get("smoothing_enabled", True))
        self.smoothing_checkbox.setChecked(smoothing_enabled)
        self.smoothing_checkbox.blockSignals(False)
        self._set_smoothing_controls_enabled(smoothing_enabled)

        self.smoothing_duration_slider.blockSignals(True)
        self.smoothing_angle_slider.blockSignals(True)
        self.smoothing_piston_slider.blockSignals(True)
        self.smoothing_easing_combo.blockSignals(True)

        # Update sliders
        self.amplitude_slider.setValue(params.get("amplitude", 0.05))
        self.frequency_slider.setValue(params.get("frequency", 1.0))
        self.phase_slider.setValue(params.get("phase", 0.0))

        self.wheel_sliders["lf"].setValue(params.get("lf_phase", 0.0))
        self.wheel_sliders["rf"].setValue(params.get("rf_phase", 0.0))
        self.wheel_sliders["lr"].setValue(params.get("lr_phase", 0.0))
        self.wheel_sliders["rr"].setValue(params.get("rr_phase", 0.0))

        self.smoothing_duration_slider.setValue(
            params.get(
                "smoothing_duration_ms",
                PARAMETER_RANGES["smoothing_duration_ms"]["default"],
            )
        )
        self.smoothing_angle_slider.setValue(
            params.get(
                "smoothing_angle_snap_deg",
                PARAMETER_RANGES["smoothing_angle_snap_deg"]["default"],
            )
        )
        self.smoothing_piston_slider.setValue(
            params.get(
                "smoothing_piston_snap_m",
                PARAMETER_RANGES["smoothing_piston_snap_m"]["default"],
            )
        )

        easing_value = params.get("smoothing_easing", "OutCubic")
        easing_index = self.smoothing_easing_combo.findData(easing_value)
        if easing_index < 0:
            easing_index = 0
        self.smoothing_easing_combo.setCurrentIndex(easing_index)

        # Unblock signals
        self.amplitude_slider.blockSignals(False)
        self.frequency_slider.blockSignals(False)
        self.phase_slider.blockSignals(False)
        for slider in self.wheel_sliders.values():
            slider.blockSignals(False)
        self.smoothing_duration_slider.blockSignals(False)
        self.smoothing_angle_slider.blockSignals(False)
        self.smoothing_piston_slider.blockSignals(False)
        self.smoothing_easing_combo.blockSignals(False)
