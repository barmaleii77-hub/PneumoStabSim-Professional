# -*- coding: utf-8 -*-
"""
Graphics panel - lighting configuration tab
Вкладка настройки освещения
"""
import copy
from typing import Any, Dict

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


class LightingTab(QWidget):
    """Вкладка настройки освещения"""
    
    lighting_changed = Signal(dict)
    preset_applied = Signal(str)
    
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controls: Dict[str, Any] = {}
        self._updating_ui = False
        
        # ✅ НОВОЕ: State из SettingsManager
        settings_manager = get_settings_manager()
        graphics_settings = settings_manager.get_category("graphics")
        self._state = copy.deepcopy(graphics_settings.get("lighting", {}))
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Настроить интерфейс"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        layout.addWidget(self._build_key_light_group())
        layout.addWidget(self._build_fill_light_group())
        layout.addWidget(self._build_rim_light_group())
        layout.addWidget(self._build_point_light_group())
        layout.addWidget(self._build_lighting_preset_group())
        layout.addStretch(1)
    
    def _build_key_light_group(self) -> QGroupBox:
        """Создать группу ключевого света"""
        group = QGroupBox("Ключевой свет", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        
        brightness = LabeledSlider("Яркость", 0.0, 10.0, 0.05, decimals=2)
        brightness.valueChanged.connect(lambda v: self._update_lighting("key", "brightness", v))
        self._controls["key.brightness"] = brightness
        grid.addWidget(brightness, 0, 0, 1, 2)
        
        color_row = QHBoxLayout()
        color_row.setContentsMargins(0, 0, 0, 0)
        color_row.setSpacing(6)
        color_row.addWidget(QLabel("Цвет", self))
        color_button = ColorButton()
        color_button.color_changed.connect(lambda c: self._update_lighting("key", "color", c))
        self._controls["key.color"] = color_button
        color_row.addWidget(color_button)
        color_row.addStretch(1)
        grid.addLayout(color_row, 1, 0, 1, 2)
        
        angle_x = LabeledSlider("Наклон X", -90.0, 90.0, 1.0, decimals=1, unit="°")
        angle_x.valueChanged.connect(lambda v: self._update_lighting("key", "angle_x", v))
        self._controls["key.angle_x"] = angle_x
        grid.addWidget(angle_x, 2, 0, 1, 2)
        
        angle_y = LabeledSlider("Поворот Y", -180.0, 180.0, 1.0, decimals=1, unit="°")
        angle_y.valueChanged.connect(lambda v: self._update_lighting("key", "angle_y", v))
        self._controls["key.angle_y"] = angle_y
        grid.addWidget(angle_y, 3, 0, 1, 2)
        
        posx = LabeledSlider("Позиция X", -5000.0, 5000.0, 10.0, decimals=0, unit="мм")
        posx.valueChanged.connect(lambda v: self._update_lighting("key", "position_x", v))
        self._controls["key.position_x"] = posx
        grid.addWidget(posx, 4, 0, 1, 2)
        
        posy = LabeledSlider("Позиция Y", -5000.0, 5000.0, 10.0, decimals=0, unit="мм")
        posy.valueChanged.connect(lambda v: self._update_lighting("key", "position_y", v))
        self._controls["key.position_y"] = posy
        grid.addWidget(posy, 5, 0, 1, 2)
        
        key_shadow = QCheckBox("Тени от ключевого света", self)
        key_shadow.toggled.connect(lambda checked: self._update_lighting("key", "cast_shadow", checked))
        self._controls["key.cast_shadow"] = key_shadow
        grid.addWidget(key_shadow, 6, 0, 1, 2)
        
        key_bind = QCheckBox("Привязать к камере", self)
        key_bind.toggled.connect(lambda checked: self._update_lighting("key", "bind_to_camera", checked))
        self._controls["key.bind"] = key_bind
        grid.addWidget(key_bind, 7, 0, 1, 2)
        return group
    
    def _build_fill_light_group(self) -> QGroupBox:
        """Создать группу заполняющего света"""
        group = QGroupBox("Заполняющий свет", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        
        brightness = LabeledSlider("Яркость", 0.0, 5.0, 0.05, decimals=2)
        brightness.valueChanged.connect(lambda v: self._update_lighting("fill", "brightness", v))
        self._controls["fill.brightness"] = brightness
        grid.addWidget(brightness, 0, 0, 1, 2)
        
        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Цвет", self))
        color_button = ColorButton()
        color_button.color_changed.connect(lambda c: self._update_lighting("fill", "color", c))
        self._controls["fill.color"] = color_button
        color_row.addWidget(color_button)
        color_row.addStretch(1)
        grid.addLayout(color_row, 1, 0, 1, 2)
        
        posx = LabeledSlider("Позиция X", -5000.0, 5000.0, 10.0, decimals=0, unit="мм")
        posx.valueChanged.connect(lambda v: self._update_lighting("fill", "position_x", v))
        self._controls["fill.position_x"] = posx
        grid.addWidget(posx, 2, 0, 1, 2)
        
        posy = LabeledSlider("Позиция Y", -5000.0, 5000.0, 10.0, decimals=0, unit="мм")
        posy.valueChanged.connect(lambda v: self._update_lighting("fill", "position_y", v))
        self._controls["fill.position_y"] = posy
        grid.addWidget(posy, 3, 0, 1, 2)
        
        fill_shadow = QCheckBox("Тени от заполняющего света", self)
        fill_shadow.toggled.connect(lambda checked: self._update_lighting("fill", "cast_shadow", checked))
        self._controls["fill.cast_shadow"] = fill_shadow
        grid.addWidget(fill_shadow, 4, 0, 1, 2)
        
        fill_bind = QCheckBox("Привязать к камере", self)
        fill_bind.toggled.connect(lambda checked: self._update_lighting("fill", "bind_to_camera", checked))
        self._controls["fill.bind"] = fill_bind
        grid.addWidget(fill_bind, 5, 0, 1, 2)
        return group
    
    def _build_rim_light_group(self) -> QGroupBox:
        """Создать группу контрового света"""
        group = QGroupBox("Контровой свет", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        
        brightness = LabeledSlider("Яркость", 0.0, 5.0, 0.05, decimals=2)
        brightness.valueChanged.connect(lambda v: self._update_lighting("rim", "brightness", v))
        self._controls["rim.brightness"] = brightness
        grid.addWidget(brightness, 0, 0, 1, 2)
        
        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Цвет", self))
        color_button = ColorButton()
        color_button.color_changed.connect(lambda c: self._update_lighting("rim", "color", c))
        self._controls["rim.color"] = color_button
        color_row.addWidget(color_button)
        color_row.addStretch(1)
        grid.addLayout(color_row, 1, 0, 1, 2)
        
        posx = LabeledSlider("Позиция X", -5000.0, 5000.0, 10.0, decimals=0, unit="мм")
        posx.valueChanged.connect(lambda v: self._update_lighting("rim", "position_x", v))
        self._controls["rim.position_x"] = posx
        grid.addWidget(posx, 2, 0, 1, 2)
        
        posy = LabeledSlider("Позиция Y", -5000.0, 5000.0, 10.0, decimals=0, unit="мм")
        posy.valueChanged.connect(lambda v: self._update_lighting("rim", "position_y", v))
        self._controls["rim.position_y"] = posy
        grid.addWidget(posy, 3, 0, 1, 2)
        
        rim_shadow = QCheckBox("Тени от контрового света", self)
        rim_shadow.toggled.connect(lambda checked: self._update_lighting("rim", "cast_shadow", checked))
        self._controls["rim.cast_shadow"] = rim_shadow
        grid.addWidget(rim_shadow, 4, 0, 1, 2)
        
        rim_bind = QCheckBox("Привязать к камере", self)
        rim_bind.toggled.connect(lambda checked: self._update_lighting("rim", "bind_to_camera", checked))
        self._controls["rim.bind"] = rim_bind
        grid.addWidget(rim_bind, 5, 0, 1, 2)
        return group
    
    def _build_point_light_group(self) -> QGroupBox:
        """Создать группу точечного света"""
        group = QGroupBox("Точечный свет", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        
        intensity = LabeledSlider("Интенсивность", 0.0, 100000.0, 50.0, decimals=1)
        intensity.valueChanged.connect(lambda v: self._update_lighting("point", "brightness", v))
        self._controls["point.brightness"] = intensity
        grid.addWidget(intensity, 0, 0, 1, 2)
        
        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Цвет", self))
        color_button = ColorButton()
        color_button.color_changed.connect(lambda c: self._update_lighting("point", "color", c))
        self._controls["point.color"] = color_button
        color_row.addWidget(color_button)
        color_row.addStretch(1)
        grid.addLayout(color_row, 1, 0, 1, 2)
        
        posx = LabeledSlider("Позиция X", -5000.0, 5000.0, 10.0, decimals=0, unit="мм")
        posx.valueChanged.connect(lambda v: self._update_lighting("point", "position_x", v))
        self._controls["point.position_x"] = posx
        grid.addWidget(posx, 2, 0, 1, 2)
        
        posy = LabeledSlider("Позиция Y", 0.0, 5000.0, 10.0, decimals=1, unit="мм")
        posy.valueChanged.connect(lambda v: self._update_lighting("point", "position_y", v))
        self._controls["point.position_y"] = posy
        grid.addWidget(posy, 3, 0, 1, 2)
        
        range_slider = LabeledSlider("Радиус действия", 200.0, 5000.0, 10.0, decimals=1, unit="мм")
        range_slider.valueChanged.connect(lambda v: self._update_lighting("point", "range", v))
        self._controls["point.range"] = range_slider
        grid.addWidget(range_slider, 4, 0, 1, 2)
        
        point_shadows = QCheckBox("Тени от точечного света", self)
        point_shadows.toggled.connect(lambda checked: self._update_lighting("point", "cast_shadow", checked))
        self._controls["point.cast_shadow"] = point_shadows
        grid.addWidget(point_shadows, 5, 0, 1, 2)
        
        point_bind = QCheckBox("Привязать к камере", self)
        point_bind.toggled.connect(lambda checked: self._update_lighting("point", "bind_to_camera", checked))
        self._controls["point.bind"] = point_bind
        grid.addWidget(point_bind, 6, 0, 1, 2)
        return group
    
    def _build_lighting_preset_group(self) -> QGroupBox:
        """Создать группу пресетов освещения"""
        group = QGroupBox("Пресеты освещения", self)
        layout = QHBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)
        
        presets: Dict[str, Dict[str, Any]] = {
            "☀️ Дневной свет": {
                "key": {"brightness": 1.6, "color": "#ffffff", "angle_x": -45.0, "angle_y": -30.0},
                "fill": {"brightness": 0.9, "color": "#f1f4ff"},
                "rim": {"brightness": 1.1, "color": "#ffe1bd"},
                "point": {"brightness": 1800.0, "color": "#fff7e0", "height": 2600.0, "range": 3600.0},
            },
            "🌙 Ночной": {
                "key": {"brightness": 0.6, "color": "#a8c8ff", "angle_x": -20.0, "angle_y": -60.0},
                "fill": {"brightness": 0.4, "color": "#4d6a8f"},
                "rim": {"brightness": 0.8, "color": "#93c4ff"},
                "point": {"brightness": 950.0, "color": "#b8d6ff", "height": 2100.0, "range": 2800.0},
            },
            "🏭 Промышленный": {
                "key": {"brightness": 1.1, "color": "#f2f4ff", "angle_x": -25.0, "angle_y": -110.0},
                "fill": {"brightness": 0.8, "color": "#f0f0ff"},
                "rim": {"brightness": 1.2, "color": "#ffecc6"},
                "point": {"brightness": 2200.0, "color": "#ffd7a8", "height": 2400.0, "range": 3400.0},
            },
        }
        
        for name, preset in presets.items():
            button = QPushButton(name, self)
            button.clicked.connect(lambda _, p=preset, n=name: self._apply_lighting_preset(p, n))
            layout.addWidget(button)
        
        layout.addStretch(1)
        return group
    
    def _update_lighting(self, group: str, key: str, value: Any) -> None:
        """Обновить параметр освещения"""
        if self._updating_ui:
            return
        
        # Обновляем внутреннее состояние
        if group not in self._state:
            self._state[group] = {}
        self._state[group][key] = value
        
        # Эмитируем сигнал с обновлением
        update = {group: {key: value}}
        self.lighting_changed.emit(update)
    
    def _apply_lighting_preset(self, preset: Dict[str, Any], name: str) -> None:
        """Применить пресет освещения"""
        # Обновляем внутреннее состояние
        self._state = copy.deepcopy(preset)
        
        self.lighting_changed.emit(preset)
        self.preset_applied.emit(f"Освещение: {name}")
    
    # ✅ НОВЫЕ МЕТОДЫ: get_state() и set_state()
    def get_state(self) -> Dict[str, Any]:
        """Получить текущее состояние освещения
        
        Returns:
            Словарь с параметрами освещения (key, fill, rim, point)
        """
        return copy.deepcopy(self._state)
    
    def set_state(self, state: Dict[str, Any]) -> None:
        """Установить состояние освещения из словаря
        
        Args:
            state: Словарь с параметрами освещения
        """
        self._updating_ui = True
        try:
            # Обновляем внутреннее состояние
            self._state = copy.deepcopy(state)
            
            # Обновляем UI controls
            for group in ["key", "fill", "rim", "point"]:
                if group not in state:
                    continue
                
                group_state = state[group]
                
                for key, value in group_state.items():
                    control_key = f"{group}.{key}"
                    control = self._controls.get(control_key)
                    
                    if isinstance(control, ColorButton):
                        control.set_color(value)
                    elif isinstance(control, LabeledSlider):
                        control.set_value(value)
                    elif isinstance(control, QCheckBox):
                        control.setChecked(bool(value))
        
        finally:
            self._updating_ui = False
    
    def get_controls(self) -> Dict[str, Any]:
        """Получить словарь контролов для внешнего управления"""
        return self._controls
    
    def set_updating_ui(self, updating: bool) -> None:
        """Установить флаг обновления UI"""
        self._updating_ui = updating
