"""
Graphics panel - lighting configuration tab
Вкладка настройки освещения
"""

import copy
import math
from collections.abc import Mapping
from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .widgets import ColorButton, LabeledSlider

# ✅ ИСПРАВЛЕНО: SettingsManager вместо defaults.py
from src.common.settings_manager import get_settings_manager
from src.common.logging_widgets import LoggingCheckBox


_POINT_ATTENUATION_MIN = 0.0
_POINT_ATTENUATION_MAX = 10.0
_POINT_ATTENUATION_STEP = 0.01

# Значения соответствуют движковым настройкам в assets/qml/lighting/PointLights.qml
_POINT_ATTENUATION_DEFAULTS: dict[str, float | None] = {
    "constant_fade": 1.0,
    "linear_fade": None,
    "quadratic_fade": 1.0,
}


def _quantize_attenuation(value: float) -> float:
    """Clamp attenuation to slider bounds and quantise to slider steps."""

    if not math.isfinite(value):
        value = _POINT_ATTENUATION_MIN

    clamped = max(_POINT_ATTENUATION_MIN, min(_POINT_ATTENUATION_MAX, value))
    steps = round((clamped - _POINT_ATTENUATION_MIN) / _POINT_ATTENUATION_STEP)
    quantised = _POINT_ATTENUATION_MIN + steps * _POINT_ATTENUATION_STEP
    # Round to a stable number of decimals to avoid floating point noise
    return round(quantised, 6)


class LightingTab(QWidget):
    """Вкладка настройки освещения"""

    lighting_changed = Signal(dict)
    preset_applied = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controls: dict[str, Any] = {}
        self._updating_ui = False

        # ✅ НОВОЕ: State из SettingsManager
        settings_manager = get_settings_manager()
        graphics_settings = settings_manager.get_category("graphics")
        lighting_settings = graphics_settings.get("lighting", {})
        if isinstance(lighting_settings, Mapping):
            self._defaults: dict[str, Any] = copy.deepcopy(lighting_settings)
        else:
            self._defaults = {}
        self._state = copy.deepcopy(self._defaults)

        self._setup_ui()
        # Применяем состояние сразу, чтобы слайдеры отображали корректные
        # значения по умолчанию вместо минимальных порогов (например, 0.0).
        self.set_state(self._state)

    def _setup_ui(self) -> None:
        """Настроить интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(self._build_key_light_group())
        layout.addWidget(self._build_fill_light_group())
        layout.addWidget(self._build_rim_light_group())
        layout.addWidget(self._build_point_light_group())
        layout.addWidget(self._build_spot_light_group())  # ✅ новый прожектор
        layout.addWidget(self._build_lighting_preset_group())
        layout.addStretch(1)

    def _build_key_light_group(self) -> QGroupBox:
        """Создать группу ключевого света"""
        group = QGroupBox("Ключевой свет", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        row = 0
        brightness = LabeledSlider("Яркость", 0.0, 10.0, 0.05, decimals=2)
        brightness.valueChanged.connect(
            lambda v: self._update_lighting("key", "brightness", v)
        )
        self._controls["key.brightness"] = brightness
        grid.addWidget(brightness, row, 0, 1, 2)
        row += 1

        color_row = QHBoxLayout()
        color_row.setContentsMargins(0, 0, 0, 0)
        color_row.setSpacing(6)
        color_row.addWidget(QLabel("Цвет", self))
        color_button = ColorButton()
        color_button.color_changed.connect(
            lambda c: self._update_lighting("key", "color", c)
        )
        self._controls["key.color"] = color_button
        color_row.addWidget(color_button)
        color_row.addStretch(1)
        grid.addLayout(color_row, row, 0, 1, 2)
        row += 1

        angle_x = LabeledSlider("Наклон X", -180.0, 180.0, 0.5, decimals=1, unit="°")
        angle_x.valueChanged.connect(
            lambda v: self._update_lighting("key", "angle_x", v)
        )
        self._controls["key.angle_x"] = angle_x
        grid.addWidget(angle_x, row, 0, 1, 2)
        row += 1

        angle_y = LabeledSlider("Поворот Y", -180.0, 180.0, 0.5, decimals=1, unit="°")
        angle_y.valueChanged.connect(
            lambda v: self._update_lighting("key", "angle_y", v)
        )
        self._controls["key.angle_y"] = angle_y
        grid.addWidget(angle_y, row, 0, 1, 2)
        row += 1

        angle_z = LabeledSlider("Крен Z", -180.0, 180.0, 0.5, decimals=1, unit="°")
        angle_z.valueChanged.connect(
            lambda v: self._update_lighting("key", "angle_z", v)
        )
        self._controls["key.angle_z"] = angle_z
        grid.addWidget(angle_z, row, 0, 1, 2)
        row += 1

        posx = LabeledSlider("Позиция X", -100.0, 100.0, 0.1, decimals=1, unit="м")
        posx.valueChanged.connect(
            lambda v: self._update_lighting("key", "position_x", v)
        )
        self._controls["key.position_x"] = posx
        grid.addWidget(posx, row, 0, 1, 2)
        row += 1

        posy = LabeledSlider("Позиция Y", -100.0, 100.0, 0.1, decimals=1, unit="м")
        posy.valueChanged.connect(
            lambda v: self._update_lighting("key", "position_y", v)
        )
        self._controls["key.position_y"] = posy
        grid.addWidget(posy, row, 0, 1, 2)
        row += 1

        posz = LabeledSlider("Позиция Z", -100.0, 100.0, 0.1, decimals=1, unit="м")
        posz.valueChanged.connect(
            lambda v: self._update_lighting("key", "position_z", v)
        )
        self._controls["key.position_z"] = posz
        grid.addWidget(posz, row, 0, 1, 2)
        row += 1

        key_shadow = LoggingCheckBox(
            "Тени от ключевого света", "lighting.key.cast_shadow", self
        )
        key_shadow.clicked.connect(
            lambda checked: self._update_lighting("key", "cast_shadow", checked)
        )
        self._controls["key.cast_shadow"] = key_shadow
        grid.addWidget(key_shadow, row, 0, 1, 2)
        row += 1

        key_bind = LoggingCheckBox(
            "Привязать к камере", "lighting.key.bind_to_camera", self
        )
        key_bind.clicked.connect(
            lambda checked: self._update_lighting("key", "bind_to_camera", checked)
        )
        self._controls["key.bind_to_camera"] = key_bind
        grid.addWidget(key_bind, row, 0, 1, 2)
        return group

    def _build_fill_light_group(self) -> QGroupBox:
        """Создать группу заполняющего света"""
        group = QGroupBox("Заполняющий свет", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        row = 0

        brightness = LabeledSlider("Яркость", 0.0, 10.0, 0.05, decimals=2)
        brightness.valueChanged.connect(
            lambda v: self._update_lighting("fill", "brightness", v)
        )
        self._controls["fill.brightness"] = brightness
        grid.addWidget(brightness, row, 0, 1, 2)
        row += 1

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Цвет", self))
        color_button = ColorButton()
        color_button.color_changed.connect(
            lambda c: self._update_lighting("fill", "color", c)
        )
        self._controls["fill.color"] = color_button
        color_row.addWidget(color_button)
        color_row.addStretch(1)
        grid.addLayout(color_row, row, 0, 1, 2)
        row += 1

        angle_x = LabeledSlider("Наклон X", -180.0, 180.0, 0.5, decimals=1, unit="°")
        angle_x.valueChanged.connect(
            lambda v: self._update_lighting("fill", "angle_x", v)
        )
        self._controls["fill.angle_x"] = angle_x
        grid.addWidget(angle_x, row, 0, 1, 2)
        row += 1
        angle_y = LabeledSlider("Поворот Y", -180.0, 180.0, 0.5, decimals=1, unit="°")
        angle_y.valueChanged.connect(
            lambda v: self._update_lighting("fill", "angle_y", v)
        )
        self._controls["fill.angle_y"] = angle_y
        grid.addWidget(angle_y, row, 0, 1, 2)
        row += 1
        angle_z = LabeledSlider("Крен Z", -180.0, 180.0, 0.5, decimals=1, unit="°")
        angle_z.valueChanged.connect(
            lambda v: self._update_lighting("fill", "angle_z", v)
        )
        self._controls["fill.angle_z"] = angle_z
        grid.addWidget(angle_z, row, 0, 1, 2)
        row += 1

        posx = LabeledSlider("Позиция X", -100.0, 100.0, 0.1, decimals=1, unit="м")
        posx.valueChanged.connect(
            lambda v: self._update_lighting("fill", "position_x", v)
        )
        self._controls["fill.position_x"] = posx
        grid.addWidget(posx, row, 0, 1, 2)
        row += 1
        posy = LabeledSlider("Позиция Y", -100.0, 100.0, 0.1, decimals=1, unit="м")
        posy.valueChanged.connect(
            lambda v: self._update_lighting("fill", "position_y", v)
        )
        self._controls["fill.position_y"] = posy
        grid.addWidget(posy, row, 0, 1, 2)
        row += 1
        posz = LabeledSlider("Позиция Z", -100.0, 100.0, 0.1, decimals=1, unit="м")
        posz.valueChanged.connect(
            lambda v: self._update_lighting("fill", "position_z", v)
        )
        self._controls["fill.position_z"] = posz
        grid.addWidget(posz, row, 0, 1, 2)
        row += 1

        fill_shadow = LoggingCheckBox(
            "Тени от заполняющего света", "lighting.fill.cast_shadow", self
        )
        fill_shadow.clicked.connect(
            lambda checked: self._update_lighting("fill", "cast_shadow", checked)
        )
        self._controls["fill.cast_shadow"] = fill_shadow
        grid.addWidget(fill_shadow, row, 0, 1, 2)
        row += 1

        fill_bind = LoggingCheckBox(
            "Привязать к камере", "lighting.fill.bind_to_camera", self
        )
        fill_bind.clicked.connect(
            lambda checked: self._update_lighting("fill", "bind_to_camera", checked)
        )
        self._controls["fill.bind_to_camera"] = fill_bind
        grid.addWidget(fill_bind, row, 0, 1, 2)
        return group

    def _build_rim_light_group(self) -> QGroupBox:
        """Создать группу контрового света"""
        group = QGroupBox("Контровой свет", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        row = 0

        brightness = LabeledSlider("Яркость", 0.0, 10.0, 0.05, decimals=2)
        brightness.valueChanged.connect(
            lambda v: self._update_lighting("rim", "brightness", v)
        )
        self._controls["rim.brightness"] = brightness
        grid.addWidget(brightness, row, 0, 1, 2)
        row += 1

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Цвет", self))
        color_button = ColorButton()
        color_button.color_changed.connect(
            lambda c: self._update_lighting("rim", "color", c)
        )
        self._controls["rim.color"] = color_button
        color_row.addWidget(color_button)
        color_row.addStretch(1)
        grid.addLayout(color_row, row, 0, 1, 2)
        row += 1

        angle_x = LabeledSlider("Наклон X", -180.0, 180.0, 0.5, decimals=1, unit="°")
        angle_x.valueChanged.connect(
            lambda v: self._update_lighting("rim", "angle_x", v)
        )
        self._controls["rim.angle_x"] = angle_x
        grid.addWidget(angle_x, row, 0, 1, 2)
        row += 1
        angle_y = LabeledSlider("Поворот Y", -180.0, 180.0, 0.5, decimals=1, unit="°")
        angle_y.valueChanged.connect(
            lambda v: self._update_lighting("rim", "angle_y", v)
        )
        self._controls["rim.angle_y"] = angle_y
        grid.addWidget(angle_y, row, 0, 1, 2)
        row += 1
        angle_z = LabeledSlider("Крен Z", -180.0, 180.0, 0.5, decimals=1, unit="°")
        angle_z.valueChanged.connect(
            lambda v: self._update_lighting("rim", "angle_z", v)
        )
        self._controls["rim.angle_z"] = angle_z
        grid.addWidget(angle_z, row, 0, 1, 2)
        row += 1

        posx = LabeledSlider("Позиция X", -100.0, 100.0, 0.1, decimals=1, unit="м")
        posx.valueChanged.connect(
            lambda v: self._update_lighting("rim", "position_x", v)
        )
        self._controls["rim.position_x"] = posx
        grid.addWidget(posx, row, 0, 1, 2)
        row += 1
        posy = LabeledSlider("Позиция Y", -100.0, 100.0, 0.1, decimals=1, unit="м")
        posy.valueChanged.connect(
            lambda v: self._update_lighting("rim", "position_y", v)
        )
        self._controls["rim.position_y"] = posy
        grid.addWidget(posy, row, 0, 1, 2)
        row += 1
        posz = LabeledSlider("Позиция Z", -100.0, 100.0, 0.1, decimals=1, unit="м")
        posz.valueChanged.connect(
            lambda v: self._update_lighting("rim", "position_z", v)
        )
        self._controls["rim.position_z"] = posz
        grid.addWidget(posz, row, 0, 1, 2)
        row += 1

        rim_shadow = LoggingCheckBox(
            "Тени от контрового света", "lighting.rim.cast_shadow", self
        )
        rim_shadow.clicked.connect(
            lambda checked: self._update_lighting("rim", "cast_shadow", checked)
        )
        self._controls["rim.cast_shadow"] = rim_shadow
        grid.addWidget(rim_shadow, row, 0, 1, 2)
        row += 1

        rim_bind = LoggingCheckBox(
            "Привязать к камере", "lighting.rim.bind_to_camera", self
        )
        rim_bind.clicked.connect(
            lambda checked: self._update_lighting("rim", "bind_to_camera", checked)
        )
        self._controls["rim.bind_to_camera"] = rim_bind
        grid.addWidget(rim_bind, row, 0, 1, 2)
        return group

    def _build_point_light_group(self) -> QGroupBox:
        """Создать группу точечного света"""
        group = QGroupBox("Точечный свет", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        row = 0

        intensity = LabeledSlider("Интенсивность", 0.0, 200000.0, 50.0, decimals=1)
        intensity.valueChanged.connect(
            lambda v: self._update_lighting("point", "brightness", v)
        )
        self._controls["point.brightness"] = intensity
        grid.addWidget(intensity, row, 0, 1, 2)
        row += 1

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Цвет", self))
        color_button = ColorButton()
        color_button.color_changed.connect(
            lambda c: self._update_lighting("point", "color", c)
        )
        self._controls["point.color"] = color_button
        color_row.addWidget(color_button)
        color_row.addStretch(1)
        grid.addLayout(color_row, row, 0, 1, 2)
        row += 1

        posx = LabeledSlider("Позиция X", -100.0, 100.0, 0.1, decimals=1, unit="м")
        posx.valueChanged.connect(
            lambda v: self._update_lighting("point", "position_x", v)
        )
        self._controls["point.position_x"] = posx
        grid.addWidget(posx, row, 0, 1, 2)
        row += 1
        posy = LabeledSlider("Позиция Y", -100.0, 100.0, 0.1, decimals=1, unit="м")
        posy.valueChanged.connect(
            lambda v: self._update_lighting("point", "position_y", v)
        )
        self._controls["point.position_y"] = posy
        grid.addWidget(posy, row, 0, 1, 2)
        row += 1
        posz = LabeledSlider("Позиция Z", -100.0, 100.0, 0.1, decimals=1, unit="м")
        posz.valueChanged.connect(
            lambda v: self._update_lighting("point", "position_z", v)
        )
        self._controls["point.position_z"] = posz
        grid.addWidget(posz, row, 0, 1, 2)
        row += 1

        range_slider = LabeledSlider(
            "Радиус действия", 0.1, 200.0, 0.1, decimals=2, unit="м"
        )
        range_slider.valueChanged.connect(
            lambda v: self._update_lighting("point", "range", v)
        )
        self._controls["point.range"] = range_slider
        grid.addWidget(range_slider, row, 0, 1, 2)
        row += 1

        cfade = LabeledSlider(
            "Constant Fade",
            _POINT_ATTENUATION_MIN,
            _POINT_ATTENUATION_MAX,
            _POINT_ATTENUATION_STEP,
            decimals=2,
        )
        cfade.valueChanged.connect(
            lambda v: self._update_lighting("point", "constant_fade", v)
        )
        self._controls["point.constant_fade"] = cfade
        grid.addWidget(cfade, row, 0, 1, 2)
        row += 1

        lfade = LabeledSlider(
            "Linear Fade",
            _POINT_ATTENUATION_MIN,
            _POINT_ATTENUATION_MAX,
            _POINT_ATTENUATION_STEP,
            decimals=2,
        )
        lfade.valueChanged.connect(
            lambda v: self._update_lighting("point", "linear_fade", v)
        )
        self._controls["point.linear_fade"] = lfade
        grid.addWidget(lfade, row, 0, 1, 2)
        row += 1

        qfade = LabeledSlider(
            "Quadratic Fade",
            _POINT_ATTENUATION_MIN,
            _POINT_ATTENUATION_MAX,
            _POINT_ATTENUATION_STEP,
            decimals=2,
        )
        qfade.valueChanged.connect(
            lambda v: self._update_lighting("point", "quadratic_fade", v)
        )
        self._controls["point.quadratic_fade"] = qfade
        grid.addWidget(qfade, row, 0, 1, 2)
        row += 1

        point_shadows = LoggingCheckBox(
            "Тени от точечного света", "lighting.point.cast_shadow", self
        )
        point_shadows.clicked.connect(
            lambda checked: self._update_lighting("point", "cast_shadow", checked)
        )
        self._controls["point.cast_shadow"] = point_shadows
        grid.addWidget(point_shadows, row, 0, 1, 2)
        row += 1

        point_bind = LoggingCheckBox(
            "Привязать к камере", "lighting.point.bind_to_camera", self
        )
        point_bind.clicked.connect(
            lambda checked: self._update_lighting("point", "bind_to_camera", checked)
        )
        self._controls["point.bind_to_camera"] = point_bind
        grid.addWidget(point_bind, row, 0, 1, 2)
        return group

    def _build_spot_light_group(self) -> QGroupBox:
        """Создать группу прожектор (SpotLight)"""
        group = QGroupBox("Прожектор (Spot)", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        row = 0

        intensity = LabeledSlider("Интенсивность", 0.0, 200000.0, 50.0, decimals=1)
        intensity.valueChanged.connect(
            lambda v: self._update_lighting("spot", "brightness", v)
        )
        self._controls["spot.brightness"] = intensity
        grid.addWidget(intensity, row, 0, 1, 2)
        row += 1

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Цвет", self))
        color_button = ColorButton()
        color_button.color_changed.connect(
            lambda c: self._update_lighting("spot", "color", c)
        )
        self._controls["spot.color"] = color_button
        color_row.addWidget(color_button)
        color_row.addStretch(1)
        grid.addLayout(color_row, row, 0, 1, 2)
        row += 1

        # Позиция
        posx = LabeledSlider("Позиция X", -100.0, 100.0, 0.1, decimals=1, unit="м")
        posx.valueChanged.connect(
            lambda v: self._update_lighting("spot", "position_x", v)
        )
        self._controls["spot.position_x"] = posx
        grid.addWidget(posx, row, 0, 1, 2)
        row += 1
        posy = LabeledSlider("Позиция Y", -100.0, 100.0, 0.1, decimals=1, unit="м")
        posy.valueChanged.connect(
            lambda v: self._update_lighting("spot", "position_y", v)
        )
        self._controls["spot.position_y"] = posy
        grid.addWidget(posy, row, 0, 1, 2)
        row += 1
        posz = LabeledSlider("Позиция Z", -100.0, 100.0, 0.1, decimals=1, unit="м")
        posz.valueChanged.connect(
            lambda v: self._update_lighting("spot", "position_z", v)
        )
        self._controls["spot.position_z"] = posz
        grid.addWidget(posz, row, 0, 1, 2)
        row += 1

        # Ориентация
        angle_x = LabeledSlider("Наклон X", -180.0, 180.0, 0.5, decimals=1, unit="°")
        angle_x.valueChanged.connect(
            lambda v: self._update_lighting("spot", "angle_x", v)
        )
        self._controls["spot.angle_x"] = angle_x
        grid.addWidget(angle_x, row, 0, 1, 2)
        row += 1
        angle_y = LabeledSlider("Поворот Y", -180.0, 180.0, 0.5, decimals=1, unit="°")
        angle_y.valueChanged.connect(
            lambda v: self._update_lighting("spot", "angle_y", v)
        )
        self._controls["spot.angle_y"] = angle_y
        grid.addWidget(angle_y, row, 0, 1, 2)
        row += 1
        angle_z = LabeledSlider("Крен Z", -180.0, 180.0, 0.5, decimals=1, unit="°")
        angle_z.valueChanged.connect(
            lambda v: self._update_lighting("spot", "angle_z", v)
        )
        self._controls["spot.angle_z"] = angle_z
        grid.addWidget(angle_z, row, 0, 1, 2)
        row += 1

        # Диапазон и конусы
        range_slider = LabeledSlider(
            "Радиус действия", 0.05, 50.0, 0.05, decimals=2, unit="м"
        )
        range_slider.valueChanged.connect(
            lambda v: self._update_lighting("spot", "range", v)
        )
        self._controls["spot.range"] = range_slider
        grid.addWidget(range_slider, row, 0, 1, 2)
        row += 1

        cone = LabeledSlider("Угол конуса", 1.0, 179.0, 1.0, decimals=0, unit="°")
        cone.valueChanged.connect(
            lambda v: self._update_lighting("spot", "cone_angle", v)
        )
        self._controls["spot.cone_angle"] = cone
        grid.addWidget(cone, row, 0, 1, 2)
        row += 1

        inner = LabeledSlider("Внутренний конус", 0.0, 178.0, 1.0, decimals=0, unit="°")
        inner.valueChanged.connect(
            lambda v: self._update_lighting("spot", "inner_cone_angle", v)
        )
        self._controls["spot.inner_cone_angle"] = inner
        grid.addWidget(inner, row, 0, 1, 2)
        row += 1

        spot_shadows = LoggingCheckBox(
            "Тени от прожектора", "lighting.spot.cast_shadow", self
        )
        spot_shadows.clicked.connect(
            lambda checked: self._update_lighting("spot", "cast_shadow", checked)
        )
        self._controls["spot.cast_shadow"] = spot_shadows
        grid.addWidget(spot_shadows, row, 0, 1, 2)
        row += 1

        spot_bind = LoggingCheckBox(
            "Привязать к камере", "lighting.spot.bind_to_camera", self
        )
        spot_bind.clicked.connect(
            lambda checked: self._update_lighting("spot", "bind_to_camera", checked)
        )
        self._controls["spot.bind_to_camera"] = spot_bind
        grid.addWidget(spot_bind, row, 0, 1, 2)

        return group

    def _build_lighting_preset_group(self) -> QGroupBox:
        """Создать группу пресетов освещения"""
        group = QGroupBox("Пресеты освещения", self)
        layout = QHBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        presets: dict[str, dict[str, Any]] = {
            "☀️ Дневной свет": {
                "key": {
                    "brightness": 1.6,
                    "color": "#ffffff",
                    "angle_x": -45.0,
                    "angle_y": -30.0,
                    "angle_z": 0.0,
                },
                "fill": {
                    "brightness": 0.9,
                    "color": "#f1f4ff",
                    "angle_x": -60.0,
                    "angle_y": 135.0,
                    "angle_z": 0.0,
                },
                "rim": {
                    "brightness": 1.1,
                    "color": "#ffe1bd",
                    "angle_x": 30.0,
                    "angle_y": -135.0,
                    "angle_z": 0.0,
                },
                "point": {
                    "brightness": 1800.0,
                    "color": "#fff7e0",
                    "position_y": 2.6,
                    "range": 3.6,
                    "constant_fade": 1.0,
                    "linear_fade": 0.01,
                    "quadratic_fade": 1.0,
                },
                "spot": {
                    "brightness": 0.0,
                    "color": "#ffffff",
                    "position_x": 0.0,
                    "position_y": 2.5,
                    "position_z": 0.0,
                    "range": 3.0,
                    "cone_angle": 45.0,
                    "inner_cone_angle": 25.0,
                    "angle_x": 0.0,
                    "angle_y": 0.0,
                    "angle_z": 0.0,
                },
            },
            "🌙 Ночной": {
                "key": {
                    "brightness": 0.6,
                    "color": "#a8c8ff",
                    "angle_x": -20.0,
                    "angle_y": -60.0,
                    "angle_z": 0.0,
                },
                "fill": {
                    "brightness": 0.4,
                    "color": "#4d6a8f",
                    "angle_x": -60.0,
                    "angle_y": 135.0,
                    "angle_z": 0.0,
                },
                "rim": {
                    "brightness": 0.8,
                    "color": "#93c4ff",
                    "angle_x": 30.0,
                    "angle_y": -135.0,
                    "angle_z": 0.0,
                },
                "point": {
                    "brightness": 950.0,
                    "color": "#b8d6ff",
                    "position_y": 2.1,
                    "range": 2.8,
                    "constant_fade": 1.0,
                    "linear_fade": 0.01,
                    "quadratic_fade": 1.0,
                },
                "spot": {
                    "brightness": 0.0,
                    "color": "#93c4ff",
                    "position_x": 0.0,
                    "position_y": 2.3,
                    "position_z": 0.0,
                    "range": 2.6,
                    "cone_angle": 40.0,
                    "inner_cone_angle": 20.0,
                    "angle_x": 0.0,
                    "angle_y": 0.0,
                    "angle_z": 0.0,
                },
            },
            "🏭 Промышленный": {
                "key": {
                    "brightness": 1.1,
                    "color": "#f2f4ff",
                    "angle_x": -25.0,
                    "angle_y": -110.0,
                    "angle_z": 0.0,
                },
                "fill": {
                    "brightness": 0.8,
                    "color": "#f0f0ff",
                    "angle_x": -60.0,
                    "angle_y": 135.0,
                    "angle_z": 0.0,
                },
                "rim": {
                    "brightness": 1.2,
                    "color": "#ffecc6",
                    "angle_x": 30.0,
                    "angle_y": -135.0,
                    "angle_z": 0.0,
                },
                "point": {
                    "brightness": 2200.0,
                    "color": "#ffd7a8",
                    "position_y": 2.4,
                    "range": 3.4,
                    "constant_fade": 1.0,
                    "linear_fade": 0.01,
                    "quadratic_fade": 1.0,
                },
                "spot": {
                    "brightness": 0.0,
                    "color": "#ffd7a8",
                    "position_x": 0.0,
                    "position_y": 2.4,
                    "position_z": 0.0,
                    "range": 3.2,
                    "cone_angle": 50.0,
                    "inner_cone_angle": 28.0,
                    "angle_x": 0.0,
                    "angle_y": 0.0,
                    "angle_z": 0.0,
                },
            },
        }

        for name, preset in presets.items():
            button = QPushButton(name, self)
            button.clicked.connect(
                lambda _, p=preset, n=name: self._apply_lighting_preset(p, n)
            )
            layout.addWidget(button)

        layout.addStretch(1)
        return group

    def _update_lighting(self, group: str, key: str, value: Any) -> None:
        """Обновить параметр освещения"""
        if self._updating_ui:
            return

        if group not in self._state:
            self._state[group] = {}
        self._state[group][key] = value

        update = {group: {key: value}}
        self.lighting_changed.emit(update)

    def _apply_lighting_preset(self, preset: dict[str, Any], name: str) -> None:
        self._state = copy.deepcopy(preset)
        self.lighting_changed.emit(preset)
        self.preset_applied.emit(f"Освещение: {name}")

    def get_state(self) -> dict[str, Any]:
        return copy.deepcopy(self._state)

    def _merge_with_defaults(self, state: Mapping[str, Any] | None) -> dict[str, Any]:
        """Return a defensive copy of *state* with engine defaults applied."""

        merged: dict[str, Any] = {}
        if isinstance(state, Mapping):
            merged = copy.deepcopy(state)

        point = merged.get("point")
        if not isinstance(point, Mapping):
            point = {}

        # Гарантируем наличие положительного range в состоянии
        resolved_range = self._resolve_point_range(point)
        if resolved_range is None or resolved_range <= 0.0:
            resolved_range = 3.0  # движковый дефолт для стабильных тестов
        # Пробрасываем range назад в состояние, чтобы потребители видели значение
        point_with_core: dict[str, float] = {"range": float(resolved_range)}

        # Аттенюации с учётом дефолтов
        point_with_defaults: dict[str, float] = {}
        linear_default = _quantize_attenuation(2.0 / resolved_range)
        for key, default in _POINT_ATTENUATION_DEFAULTS.items():
            effective_default = (
                linear_default if key == "linear_fade" else float(default or 0.0)
            )
            point_with_defaults[key] = self._coerce_attenuation_value(
                point.get(key) if isinstance(point, Mapping) else None,
                effective_default,
            )

        # Сборка итогового блока point
        existing_point = dict(point) if isinstance(point, Mapping) else {}
        existing_point.update(point_with_core)
        existing_point.update(point_with_defaults)
        merged["point"] = existing_point

        return merged

    def _coerce_attenuation_value(self, raw_value: Any, default: float) -> float:
        """Coerce UI-bound attenuation values to sane numeric defaults."""

        numeric = default
        if raw_value is not None:
            try:
                numeric = float(raw_value)
            except (TypeError, ValueError):
                numeric = default

        if numeric <= 0.0:
            numeric = default if default > 0.0 else _POINT_ATTENUATION_MIN

        return _quantize_attenuation(numeric)

    def _compute_point_linear_default(
        self, point_state: Mapping[str, Any] | None
    ) -> float:
        """Calculate the engine's linear attenuation fallback based on range."""

        range_value = self._resolve_point_range(point_state)
        if range_value is None or range_value <= 0.0:
            return _quantize_attenuation(_POINT_ATTENUATION_MIN)

        return _quantize_attenuation(2.0 / range_value)

    def _resolve_point_range(
        self, point_state: Mapping[str, Any] | None
    ) -> float | None:
        """Return a positive range value from *point_state* or defaults."""

        candidates: list[Any] = []
        if isinstance(point_state, Mapping):
            candidates.append(point_state.get("range"))

        defaults_point = (
            self._defaults.get("point") if isinstance(self._defaults, Mapping) else None
        )
        if isinstance(defaults_point, Mapping):
            candidates.append(defaults_point.get("range"))

        for candidate in candidates:
            try:
                numeric = float(candidate)
            except (TypeError, ValueError):
                continue
            if numeric > 0.0:
                return numeric

        return None

    def set_state(self, state: Mapping[str, Any] | None) -> None:
        merged_state = self._merge_with_defaults(state)
        self._updating_ui = True
        try:
            self._state = copy.deepcopy(merged_state)
            for group in ["key", "fill", "rim", "point", "spot"]:
                group_state = merged_state.get(group)
                if not isinstance(group_state, Mapping):
                    continue
                for key, value in group_state.items():
                    control_key = f"{group}.{key}"
                    control = self._controls.get(control_key)
                    if isinstance(control, ColorButton):
                        control.set_color(value)
                    elif isinstance(control, LabeledSlider):
                        try:
                            numeric_value = float(value)
                        except (TypeError, ValueError):
                            continue
                        control.set_value(numeric_value)
                    elif isinstance(control, QCheckBox):
                        control.setChecked(bool(value))
        finally:
            self._updating_ui = False

    def get_controls(self) -> dict[str, Any]:
        return self._controls

    def set_updating_ui(self, updating: bool) -> None:
        self._updating_ui = updating
