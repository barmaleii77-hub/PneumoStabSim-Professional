# -*- coding: utf-8 -*-
"""
Environment Tab - вкладка настроек окружения (фон, IBL, туман, AO)
Part of modular GraphicsPanel restructuring

СТРУКТУРА ТОЧНО ПОВТОРЯЕТ МОНОЛИТ panel_graphics.py:
- _build_background_group() → Фон и IBL (с HDR discovery)
- _build_fog_group() → Туман с near/far + высотный туман (Qt 6.10 Fog)
- _build_ao_group() → Ambient Occlusion (SSAO) расширенный
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel, 
    QComboBox, QCheckBox, QHBoxLayout, QGridLayout
)
from PySide6.QtCore import Signal
from pathlib import Path
from typing import Dict, Any, List, Tuple

from .widgets import ColorButton, LabeledSlider


class EnvironmentTab(QWidget):
    """Вкладка настроек окружения: фон, IBL, туман, AO
    
    Signals:
        environment_changed: Dict[str, Any] - параметры окружения изменились
    """
    
    environment_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Current state - храним ссылки на контролы
        self._controls: Dict[str, Any] = {}
        self._updating_ui = False
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Построить UI вкладки - РАСШИРЕННАЯ ВЕРСИЯ"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        layout.addWidget(self._build_background_group())
        layout.addWidget(self._build_fog_group())
        layout.addWidget(self._build_ao_group())
        
        layout.addStretch(1)
    
    def _build_background_group(self) -> QGroupBox:
        """Создать группу Фон и IBL - расширенная"""
        group = QGroupBox("Фон и IBL", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        row = 0
        
        # Background mode
        grid.addWidget(QLabel("Режим фона", self), row, 0)
        bg_mode = QComboBox(self)
        bg_mode.addItem("Skybox", "skybox")
        bg_mode.addItem("Сплошной цвет", "color")
        bg_mode.addItem("Прозрачный", "transparent")
        bg_mode.currentIndexChanged.connect(lambda _: self._on_control_changed("background_mode", bg_mode.currentData()))
        self._controls["background.mode"] = bg_mode
        grid.addWidget(bg_mode, row, 1)
        row += 1
        
        # Background color
        bg_row = QHBoxLayout()
        bg_row.addWidget(QLabel("Цвет", self))
        bg_button = ColorButton()
        bg_button.color_changed.connect(lambda c: self._on_control_changed("background_color", c))
        self._controls["background.color"] = bg_button
        bg_row.addWidget(bg_button)
        bg_row.addStretch(1)
        grid.addLayout(bg_row, row, 0, 1, 2)
        row += 1
        
        # Skybox enabled
        skybox_toggle = QCheckBox("Показывать Skybox (фон)", self)
        skybox_toggle.clicked.connect(lambda checked: self._on_skybox_enabled_clicked(checked))
        self._controls["background.skybox_enabled"] = skybox_toggle
        grid.addWidget(skybox_toggle, row, 0, 1, 2)
        row += 1
        
        # IBL enabled
        ibl_check = QCheckBox("Включить IBL", self)
        ibl_check.clicked.connect(lambda checked: self._on_ibl_enabled_clicked(checked))
        self._controls["ibl.enabled"] = ibl_check
        grid.addWidget(ibl_check, row, 0, 1, 2)
        row += 1
        
        # IBL intensity
        intensity = LabeledSlider("Интенсивность IBL", 0.0, 8.0, 0.05, decimals=2)
        intensity.valueChanged.connect(lambda v: self._on_control_changed("ibl_intensity", v))
        self._controls["ibl.intensity"] = intensity
        grid.addWidget(intensity, row, 0, 1, 2)
        row += 1
        
        # IBL extra: probe brightness (если поддерживается движком)
        probe_brightness = LabeledSlider("Яркость пробы (probeBrightness)", 0.0, 8.0, 0.05, decimals=2)
        probe_brightness.valueChanged.connect(lambda v: self._on_control_changed("probe_brightness", v))
        self._controls["ibl.probe_brightness"] = probe_brightness
        grid.addWidget(probe_brightness, row, 0, 1, 2)
        row += 1
        
        # IBL extra: probe horizon cutoff (-1..1)
        probe_horizon = LabeledSlider("Горизонт пробы (probeHorizon)", -1.0, 1.0, 0.01, decimals=2)
        probe_horizon.valueChanged.connect(lambda v: self._on_control_changed("probe_horizon", v))
        self._controls["ibl.probe_horizon"] = probe_horizon
        grid.addWidget(probe_horizon, row, 0, 1, 2)
        row += 1
        
        # Skybox blur
        blur = LabeledSlider("Размытие skybox", 0.0, 1.0, 0.01, decimals=2)
        blur.valueChanged.connect(lambda v: self._on_control_changed("skybox_blur", v))
        self._controls["skybox.blur"] = blur
        grid.addWidget(blur, row, 0, 1, 2)
        row += 1
        
        # HDR file
        hdr_combo = QComboBox(self)
        hdr_files = self._discover_hdr_files()
        for label, path in hdr_files:
            hdr_combo.addItem(label, path)
        hdr_combo.insertItem(0, "— не выбран —", "")
        hdr_combo.setCurrentIndex(0)
        def on_hdr_changed() -> None:
            data = hdr_combo.currentData()
            if not data:
                return
            try:
                p = str(data).replace('\\', '/')
            except Exception:
                p = data
            self._on_control_changed("ibl_source", p)
        hdr_combo.currentIndexChanged.connect(lambda _: on_hdr_changed())
        self._controls["ibl.file"] = hdr_combo
        grid.addWidget(QLabel("HDR файл", self), row, 0)
        grid.addWidget(hdr_combo, row, 1)
        row += 1
        
        # IBL rotation
        ibl_rot = LabeledSlider("Поворот IBL", -1080.0, 1080.0, 1.0, decimals=0, unit="°")
        ibl_rot.valueChanged.connect(lambda v: self._on_control_changed("ibl_rotation", v))
        self._controls["ibl.rotation"] = ibl_rot
        grid.addWidget(ibl_rot, row, 0, 1, 2)
        row += 1
        
        # IBL offsets
        env_off_x = LabeledSlider("Смещение окружения X", -180.0, 180.0, 1.0, decimals=0, unit="°")
        env_off_x.valueChanged.connect(lambda v: self._on_control_changed("ibl_offset_x", v))
        self._controls["ibl.offset_x"] = env_off_x
        grid.addWidget(env_off_x, row, 0, 1, 2)
        row += 1
        env_off_y = LabeledSlider("Смещение окружения Y", -180.0, 180.0, 1.0, decimals=0, unit="°")
        env_off_y.valueChanged.connect(lambda v: self._on_control_changed("ibl_offset_y", v))
        self._controls["ibl.offset_y"] = env_off_y
        grid.addWidget(env_off_y, row, 0, 1, 2)
        row += 1
        
        # IBL bind
        env_bind = QCheckBox("Привязать окружение к камере", self)
        env_bind.clicked.connect(lambda checked: self._on_control_changed("ibl_bind_to_camera", checked))
        self._controls["ibl.bind"] = env_bind
        grid.addWidget(env_bind, row, 0, 1, 2)
        
        return group
    
    def _discover_hdr_files(self) -> List[Tuple[str, str]]:
        results: List[Tuple[str, str]] = []
        search_dirs = [Path("assets/hdr"), Path("assets/hdri"), Path("assets/qml/assets")]
        qml_dir = Path("assets/qml").resolve()
        def to_qml_relative(p: Path) -> str:
            try:
                abs_p = p.resolve()
                rel = abs_p.relative_to(qml_dir)
                return rel.as_posix()
            except Exception:
                try:
                    import os
                    relpath = os.path.relpath(p.resolve(), start=qml_dir)
                    return Path(relpath).as_posix()
                except Exception:
                    return p.resolve().as_posix()
        seen: set[str] = set()
        for base in search_dirs:
            if not base.exists():
                continue
            for ext in ("*.hdr", "*.exr"):
                for p in sorted(base.glob(ext)):
                    key = p.name.lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    results.append((p.name, to_qml_relative(p)))
        return results
    
    def _build_fog_group(self) -> QGroupBox:
        """Создать группу Туман - расширенная (Fog Qt 6.10)"""
        group = QGroupBox("Туман", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        row = 0
        
        enabled = QCheckBox("Включить туман", self)
        enabled.clicked.connect(lambda checked: self._on_fog_enabled_clicked(checked))
        self._controls["fog.enabled"] = enabled
        grid.addWidget(enabled, row, 0, 1, 2); row += 1
        
        color_row = QHBoxLayout(); color_row.addWidget(QLabel("Цвет", self))
        fog_color = ColorButton(); fog_color.color_changed.connect(lambda c: self._on_control_changed("fog_color", c))
        self._controls["fog.color"] = fog_color; color_row.addWidget(fog_color); color_row.addStretch(1)
        grid.addLayout(color_row, row, 0, 1, 2); row += 1
        
        density = LabeledSlider("Плотность", 0.0, 1.0, 0.01, decimals=2)
        density.valueChanged.connect(lambda v: self._on_control_changed("fog_density", v))
        self._controls["fog.density"] = density
        grid.addWidget(density, row, 0, 1, 2); row += 1
        
        near_slider = LabeledSlider("Начало (Near)", 0.0, 200000.0, 50.0, decimals=0, unit="мм")
        near_slider.valueChanged.connect(lambda v: self._on_control_changed("fog_near", v))
        self._controls["fog.near"] = near_slider
        grid.addWidget(near_slider, row, 0, 1, 2); row += 1
        
        far_slider = LabeledSlider("Конец (Far)", 500.0, 400000.0, 100.0, decimals=0, unit="мм")
        far_slider.valueChanged.connect(lambda v: self._on_control_changed("fog_far", v))
        self._controls["fog.far"] = far_slider
        grid.addWidget(far_slider, row, 0, 1, 2); row += 1
        
        # Высотный туман
        h_enabled = QCheckBox("Высотный туман (height)", self)
        h_enabled.clicked.connect(lambda checked: self._on_control_changed("fog_height_enabled", checked))
        self._controls["fog.height_enabled"] = h_enabled
        grid.addWidget(h_enabled, row, 0, 1, 2); row += 1
        
        least_y = LabeledSlider("Наименее интенсивная высота Y", -100000.0, 100000.0, 50.0, decimals=0, unit="мм")
        least_y.valueChanged.connect(lambda v: self._on_control_changed("fog_least_intense_y", v))
        self._controls["fog.least_y"] = least_y
        grid.addWidget(least_y, row, 0, 1, 2); row += 1
        
        most_y = LabeledSlider("Наиболее интенсивная высота Y", -100000.0, 100000.0, 50.0, decimals=0, unit="мм")
        most_y.valueChanged.connect(lambda v: self._on_control_changed("fog_most_intense_y", v))
        self._controls["fog.most_y"] = most_y
        grid.addWidget(most_y, row, 0, 1, 2); row += 1
        
        h_curve = LabeledSlider("Кривая высоты", 0.0, 4.0, 0.05, decimals=2)
        h_curve.valueChanged.connect(lambda v: self._on_control_changed("fog_height_curve", v))
        self._controls["fog.height_curve"] = h_curve
        grid.addWidget(h_curve, row, 0, 1, 2); row += 1
        
        # Transmit
        t_enabled = QCheckBox("Учитывать передачу света (transmit)", self)
        t_enabled.clicked.connect(lambda checked: self._on_control_changed("fog_transmit_enabled", checked))
        self._controls["fog.transmit_enabled"] = t_enabled
        grid.addWidget(t_enabled, row, 0, 1, 2); row += 1
        
        t_curve = LabeledSlider("Кривая передачи", 0.0, 4.0, 0.05, decimals=2)
        t_curve.valueChanged.connect(lambda v: self._on_control_changed("fog_transmit_curve", v))
        self._controls["fog.transmit_curve"] = t_curve
        grid.addWidget(t_curve, row, 0, 1, 2)
        
        return group
    
    def _build_ao_group(self) -> QGroupBox:
        """Создать группу Ambient Occlusion - расширенная"""
        group = QGroupBox("Ambient Occlusion (SSAO)", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        row = 0
        
        enabled = QCheckBox("Включить SSAO", self)
        enabled.clicked.connect(lambda checked: self._on_control_changed("ao_enabled", checked))
        self._controls["ao.enabled"] = enabled
        grid.addWidget(enabled, row, 0, 1, 2); row += 1
        
        strength = LabeledSlider("Интенсивность", 0.0, 100.0, 1.0, decimals=0, unit="%")
        strength.valueChanged.connect(lambda v: self._on_control_changed("ao_strength", v))
        self._controls["ao.strength"] = strength
        grid.addWidget(strength, row, 0, 1, 2); row += 1
        
        radius = LabeledSlider("Радиус", 0.5, 50.0, 0.1, decimals=1, unit="мм")
        radius.valueChanged.connect(lambda v: self._on_control_changed("ao_radius", v))
        self._controls["ao.radius"] = radius
        grid.addWidget(radius, row, 0, 1, 2); row += 1
        
        softness = LabeledSlider("Мягкость", 0.0, 50.0, 1.0, decimals=0)
        softness.valueChanged.connect(lambda v: self._on_control_changed("ao_softness", v))
        self._controls["ao.softness"] = softness
        grid.addWidget(softness, row, 0, 1, 2); row += 1
        
        dither = QCheckBox("Dither для AO", self)
        dither.clicked.connect(lambda checked: self._on_control_changed("ao_dither", checked))
        self._controls["ao.dither"] = dither
        grid.addWidget(dither, row, 0, 1, 2); row += 1
        
        sample_rate = QComboBox(self)
        sample_rate.addItem("2x", 2)
        sample_rate.addItem("3x", 3)
        sample_rate.addItem("4x", 4)
        sample_rate.currentIndexChanged.connect(lambda _: self._on_control_changed("ao_sample_rate", sample_rate.currentData()))
        self._controls["ao.sample_rate"] = sample_rate
        grid.addWidget(QLabel("Сэмплов", self), row, 0)
        grid.addWidget(sample_rate, row, 1)
        
        return group
    
    # ========== ОБРАБОТЧИКИ ЧЕКБОКСОВ ==========
    
    def _on_ibl_enabled_clicked(self, checked: bool) -> None:
        if self._updating_ui:
            return
        self._on_control_changed("ibl_enabled", checked)
    
    def _on_skybox_enabled_clicked(self, checked: bool) -> None:
        if self._updating_ui:
            return
        self._on_control_changed("skybox_enabled", checked)
    
    def _on_fog_enabled_clicked(self, checked: bool) -> None:
        if self._updating_ui:
            return
        self._on_control_changed("fog_enabled", checked)
    
    # ========== ОБЩИЙ ОБРАБОТЧИК ==========
    
    def _on_control_changed(self, key: str, value: Any):
        if self._updating_ui:
            return
        state = self.get_state()
        self.environment_changed.emit(state)
    
    # ========== ГЕТТЕРЫ/СЕТТЕРЫ ==========
    
    def get_state(self) -> Dict[str, Any]:
        """Получить текущее состояние всех параметров окружения"""
        return {
            # Background
            'background_mode': self._controls["background.mode"].currentData() if self._controls.get("background.mode") else 'skybox',
            'background_color': self._controls["background.color"].color().name(),
            'skybox_enabled': self._controls["background.skybox_enabled"].isChecked(),
            
            # IBL
            'ibl_enabled': self._controls["ibl.enabled"].isChecked(),
            'ibl_intensity': self._controls["ibl.intensity"].value(),
            'probe_brightness': self._controls["ibl.probe_brightness"].value(),
            'probe_horizon': self._controls["ibl.probe_horizon"].value(),
            'ibl_rotation': self._controls["ibl.rotation"].value(),
            'ibl_source': self._controls["ibl.file"].currentData() or "",
            'ibl_fallback': "",
            'skybox_blur': self._controls["skybox.blur"].value(),
            'ibl_offset_x': self._controls["ibl.offset_x"].value(),
            'ibl_offset_y': self._controls["ibl.offset_y"].value(),
            'ibl_bind_to_camera': self._controls["ibl.bind"].isChecked(),
            
            # Fog
            'fog_enabled': self._controls["fog.enabled"].isChecked(),
            'fog_color': self._controls["fog.color"].color().name(),
            'fog_density': self._controls["fog.density"].value(),
            'fog_near': self._controls["fog.near"].value(),
            'fog_far': self._controls["fog.far"].value(),
            'fog_height_enabled': self._controls["fog.height_enabled"].isChecked(),
            'fog_least_intense_y': self._controls["fog.least_y"].value(),
            'fog_most_intense_y': self._controls["fog.most_y"].value(),
            'fog_height_curve': self._controls["fog.height_curve"].value(),
            'fog_transmit_enabled': self._controls["fog.transmit_enabled"].isChecked(),
            'fog_transmit_curve': self._controls["fog.transmit_curve"].value(),
            
            # Ambient Occlusion
            'ao_enabled': self._controls["ao.enabled"].isChecked(),
            'ao_strength': self._controls["ao.strength"].value(),
            'ao_radius': self._controls["ao.radius"].value(),
            'ao_softness': self._controls["ao.softness"].value(),
            'ao_dither': self._controls["ao.dither"].isChecked(),
            'ao_sample_rate': self._controls["ao.sample_rate"].currentData(),
        }
    
    def set_state(self, state: Dict[str, Any]):
        """Установить состояние из словаря"""
        self._updating_ui = True
        for control in self._controls.values():
            try:
                control.blockSignals(True)
            except:
                pass
        try:
            # Background
            if 'background_mode' in state:
                combo = self._controls.get("background.mode")
                if combo:
                    idx = combo.findData(state['background_mode'])
                    if idx >= 0:
                        combo.setCurrentIndex(idx)
            if 'background_color' in state:
                self._controls["background.color"].set_color(state['background_color'])
            if 'skybox_enabled' in state:
                self._controls["background.skybox_enabled"].setChecked(state['skybox_enabled'])
            
            # IBL
            if 'ibl_enabled' in state:
                self._controls["ibl.enabled"].setChecked(state['ibl_enabled'])
            if 'ibl_intensity' in state:
                self._controls["ibl.intensity"].set_value(state['ibl_intensity'])
            if 'probe_brightness' in state:
                self._controls["ibl.probe_brightness"].set_value(state['probe_brightness'])
            if 'probe_horizon' in state:
                self._controls["ibl.probe_horizon"].set_value(state['probe_horizon'])
            if 'ibl_rotation' in state:
                self._controls["ibl.rotation"].set_value(state['ibl_rotation'])
            if 'ibl_source' in state:
                combo = self._controls["ibl.file"]
                source_path = state['ibl_source']
                index = -1
                for i in range(combo.count()):
                    if combo.itemData(i) == source_path:
                        index = i
                        break
                if index >= 0:
                    combo.setCurrentIndex(index)
            if 'skybox_blur' in state:
                self._controls["skybox.blur"].set_value(state['skybox_blur'])
            if 'ibl_offset_x' in state:
                self._controls["ibl.offset_x"].set_value(state['ibl_offset_x'])
            if 'ibl_offset_y' in state:
                self._controls["ibl.offset_y"].set_value(state['ibl_offset_y'])
            if 'ibl_bind_to_camera' in state:
                self._controls["ibl.bind"].setChecked(state['ibl_bind_to_camera'])
            
            # Fog
            if 'fog_enabled' in state:
                self._controls["fog.enabled"].setChecked(state['fog_enabled'])
            if 'fog_color' in state:
                self._controls["fog.color"].set_color(state['fog_color'])
            if 'fog_density' in state:
                self._controls["fog.density"].set_value(state['fog_density'])
            if 'fog_near' in state:
                self._controls["fog.near"].set_value(state['fog_near'])
            if 'fog_far' in state:
                self._controls["fog.far"].set_value(state['fog_far'])
            if 'fog_height_enabled' in state:
                self._controls["fog.height_enabled"].setChecked(state['fog_height_enabled'])
            if 'fog_least_intense_y' in state:
                self._controls["fog.least_y"].set_value(state['fog_least_intense_y'])
            if 'fog_most_intense_y' in state:
                self._controls["fog.most_y"].set_value(state['fog_most_intense_y'])
            if 'fog_height_curve' in state:
                self._controls["fog.height_curve"].set_value(state['fog_height_curve'])
            if 'fog_transmit_enabled' in state:
                self._controls["fog.transmit_enabled"].setChecked(state['fog_transmit_enabled'])
            if 'fog_transmit_curve' in state:
                self._controls["fog.transmit_curve"].set_value(state['fog_transmit_curve'])
            
            # AO
            if 'ao_enabled' in state:
                self._controls["ao.enabled"].setChecked(state['ao_enabled'])
            if 'ao_strength' in state:
                self._controls["ao.strength"].set_value(state['ao_strength'])
            if 'ao_radius' in state:
                self._controls["ao.radius"].set_value(state['ao_radius'])
            if 'ao_softness' in state:
                self._controls["ao.softness"].set_value(state['ao_softness'])
            if 'ao_dither' in state:
                self._controls["ao.dither"].setChecked(state['ao_dither'])
            if 'ao_sample_rate' in state:
                combo = self._controls["ao.sample_rate"]
                idx = combo.findData(state['ao_sample_rate'])
                if idx >= 0:
                    combo.setCurrentIndex(idx)
        finally:
            for control in self._controls.values():
                try:
                    control.blockSignals(False)
                except:
                    pass
            self._updating_ui = False
    
    def get_controls(self) -> Dict[str, Any]:
        return self._controls
    
    def set_updating_ui(self, updating: bool) -> None:
        self._updating_ui = updating
