# -*- coding: utf-8 -*-
"""
Environment Tab - вкладка настроек окружения (фон, IBL, туман, AO)
Part of modular GraphicsPanel restructuring

СТРУКТУРА ТОЧНО ПОВТОРЯЕТ МОНОЛИТ panel_graphics.py:
- _build_background_group() → Фон и IBL (с HDR discovery)
- _build_fog_group() → Туман с near/far
- _build_ao_group() → Ambient Occlusion (SSAO)
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
        """Построить UI вкладки - ТОЧНО КАК В МОНОЛИТЕ"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # ✅ ТОЧНО КАК В МОНОЛИТЕ - 3 группы:
        layout.addWidget(self._build_background_group())
        layout.addWidget(self._build_fog_group())
        layout.addWidget(self._build_ao_group())
        
        layout.addStretch(1)
    
    def _build_background_group(self) -> QGroupBox:
        """Создать группу Фон и IBL - ТОЧНО КАК В МОНОЛИТЕ"""
        group = QGroupBox("Фон и IBL", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        row = 0
        
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
        
        # IBL enabled checkbox
        ibl_check = QCheckBox("Включить IBL", self)
        ibl_check.clicked.connect(lambda checked: self._on_ibl_enabled_clicked(checked))
        self._controls["ibl.enabled"] = ibl_check
        grid.addWidget(ibl_check, row, 0, 1, 2)
        row += 1
        
        # IBL intensity slider
        intensity = LabeledSlider("Интенсивность IBL", 0.0, 5.0, 0.05, decimals=2)
        intensity.valueChanged.connect(lambda v: self._on_control_changed("ibl_intensity", v))
        self._controls["ibl.intensity"] = intensity
        grid.addWidget(intensity, row, 0, 1, 2)
        row += 1
        
        # Skybox blur slider
        blur = LabeledSlider("Размытие skybox", 0.0, 1.0, 0.01, decimals=2)
        blur.valueChanged.connect(lambda v: self._on_control_changed("skybox_blur", v))
        self._controls["skybox.blur"] = blur
        grid.addWidget(blur, row, 0, 1, 2)
        row += 1
        
        # HDR file ComboBox (с discovery механизмом из монолита)
        hdr_combo = QComboBox(self)
        # Заполняем список HDR файлов при инициализации
        hdr_files = self._discover_hdr_files()
        for label, path in hdr_files:
            hdr_combo.addItem(label, path)
        # Добавляем плейсхолдер "не выбран"
        hdr_combo.insertItem(0, "— не выбран —", "")
        hdr_combo.setCurrentIndex(0)
        
        def on_hdr_changed() -> None:
            data = hdr_combo.currentData()
            if not data:
                # Не отправляем пустой путь
                return
            # Нормализуем слеши для Windows
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
        
        # IBL rotation slider
        ibl_rot = LabeledSlider("Поворот IBL", -1080.0, 1080.0, 1.0, decimals=0, unit="°")
        ibl_rot.valueChanged.connect(lambda v: self._on_control_changed("ibl_rotation", v))
        self._controls["ibl.rotation"] = ibl_rot
        grid.addWidget(ibl_rot, row, 0, 1, 2)
        row += 1
        
        # Skybox enabled checkbox (независимо от IBL)
        skybox_toggle = QCheckBox("Показывать Skybox (фон)", self)
        skybox_toggle.clicked.connect(lambda checked: self._on_skybox_enabled_clicked(checked))
        self._controls["background.skybox_enabled"] = skybox_toggle
        grid.addWidget(skybox_toggle, row, 0, 1, 2)
        row += 1
        
        # IBL offset X
        env_off_x = LabeledSlider("Смещение окружения X", -180.0, 180.0, 1.0, decimals=0, unit="°")
        env_off_x.valueChanged.connect(lambda v: self._on_control_changed("ibl_offset_x", v))
        self._controls["ibl.offset_x"] = env_off_x
        grid.addWidget(env_off_x, row, 0, 1, 2)
        row += 1
        
        # IBL offset Y
        env_off_y = LabeledSlider("Смещение окружения Y", -180.0, 180.0, 1.0, decimals=0, unit="°")
        env_off_y.valueChanged.connect(lambda v: self._on_control_changed("ibl_offset_y", v))
        self._controls["ibl.offset_y"] = env_off_y
        grid.addWidget(env_off_y, row, 0, 1, 2)
        row += 1
        
        # IBL bind to camera checkbox
        env_bind = QCheckBox("Привязать окружение к камере", self)
        env_bind.clicked.connect(lambda checked: self._on_control_changed("ibl_bind_to_camera", checked))
        self._controls["ibl.bind"] = env_bind
        grid.addWidget(env_bind, row, 0, 1, 2)
        
        return group
    
    def _discover_hdr_files(self) -> List[Tuple[str, str]]:
        """Ищет HDR/EXR файлы - ТОЧНО КАК В МОНОЛИТЕ
        
        Поиск ведётся в:
          - assets/hdr
          - assets/hdri
          - assets/qml/assets (исторически)
          
        Returns:
            Список пар (label, path)
        """
        results: List[Tuple[str, str]] = []
        
        search_dirs = [
            Path("assets/hdr"),
            Path("assets/hdri"),
            Path("assets/qml/assets"),
        ]
        
        # База для относительных путей: каталог main.qml
        qml_dir = Path("assets/qml").resolve()
        
        def to_qml_relative(p: Path) -> str:
            """Возвращает путь относительно main.qml"""
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
        """Создать группу Туман - ТОЧНО КАК В МОНОЛИТЕ"""
        group = QGroupBox("Туман", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        
        # Fog enabled checkbox
        enabled = QCheckBox("Включить туман", self)
        enabled.clicked.connect(lambda checked: self._on_fog_enabled_clicked(checked))
        self._controls["fog.enabled"] = enabled
        grid.addWidget(enabled, 0, 0, 1, 2)
        
        # Fog color
        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Цвет", self))
        fog_color = ColorButton()
        fog_color.color_changed.connect(lambda c: self._on_control_changed("fog_color", c))
        self._controls["fog.color"] = fog_color
        color_row.addWidget(fog_color)
        color_row.addStretch(1)
        grid.addLayout(color_row, 1, 0, 1, 2)
        
        # Fog density
        density = LabeledSlider("Плотность", 0.0, 1.0, 0.01, decimals=2)
        density.valueChanged.connect(lambda v: self._on_control_changed("fog_density", v))
        self._controls["fog.density"] = density
        grid.addWidget(density, 2, 0, 1, 2)
        
        # Fog near distance
        near_slider = LabeledSlider("Начало", 0.0, 20000.0, 50.0, decimals=0, unit="мм")
        near_slider.valueChanged.connect(lambda v: self._on_control_changed("fog_near", v))
        self._controls["fog.near"] = near_slider
        grid.addWidget(near_slider, 3, 0, 1, 2)
        
        # Fog far distance
        far_slider = LabeledSlider("Конец", 500.0, 60000.0, 100.0, decimals=0, unit="мм")
        far_slider.valueChanged.connect(lambda v: self._on_control_changed("fog_far", v))
        self._controls["fog.far"] = far_slider
        grid.addWidget(far_slider, 4, 0, 1, 2)
        
        return group
    
    def _build_ao_group(self) -> QGroupBox:
        """Создать группу Ambient Occlusion - ТОЧНО КАК В МОНОЛИТЕ"""
        group = QGroupBox("Ambient Occlusion", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        
        # AO enabled checkbox
        enabled = QCheckBox("Включить SSAO", self)
        enabled.clicked.connect(lambda checked: self._on_control_changed("ao_enabled", checked))
        self._controls["ao.enabled"] = enabled
        grid.addWidget(enabled, 0, 0, 1, 2)
        
        # AO strength
        strength = LabeledSlider("Интенсивность", 0.0, 2.0, 0.02, decimals=2)
        strength.valueChanged.connect(lambda v: self._on_control_changed("ao_strength", v))
        self._controls["ao.strength"] = strength
        grid.addWidget(strength, 1, 0, 1, 2)
        
        # AO radius
        radius = LabeledSlider("Радиус", 0.5, 20.0, 0.1, decimals=2)
        radius.valueChanged.connect(lambda v: self._on_control_changed("ao_radius", v))
        self._controls["ao.radius"] = radius
        grid.addWidget(radius, 2, 0, 1, 2)
        
        return group
    
    # ========== ОБРАБОТЧИКИ ЧЕКБОКСОВ (как в монолите) ==========
    
    def _on_ibl_enabled_clicked(self, checked: bool) -> None:
        """Обработчик клика на чекбокс IBL - как в монолите"""
        if self._updating_ui:
            return
        self._on_control_changed("ibl_enabled", checked)
    
    def _on_skybox_enabled_clicked(self, checked: bool) -> None:
        """Обработчик клика на чекбокс Skybox - как в монолите"""
        if self._updating_ui:
            return
        self._on_control_changed("skybox_enabled", checked)
    
    def _on_fog_enabled_clicked(self, checked: bool) -> None:
        """Обработчик клика на чекбокс тумана - как в монолите"""
        if self._updating_ui:
            return
        self._on_control_changed("fog_enabled", checked)
    
    # ========== ОБЩИЙ ОБРАБОТЧИК ИЗМЕНЕНИЙ ==========
    
    def _on_control_changed(self, key: str, value: Any):
        """Обработчик изменения любого контрола - испускаем сигнал"""
        if self._updating_ui:
            return
        # Собираем полное состояние
        state = self.get_state()
        self.environment_changed.emit(state)
    
    # ========== ГЕТТЕРЫ/СЕТТЕРЫ СОСТОЯНИЯ ==========
    
    def get_state(self) -> Dict[str, Any]:
        """Получить текущее состояние всех параметров окружения
        
        Returns:
            Словарь с параметрами - ТОЧНО КАК В МОНОЛИТЕ
        """
        return {
            # Background
            'background_mode': 'skybox',  # Фиксировано для совместимости
            'background_color': self._controls["background.color"].color().name(),
            'skybox_enabled': self._controls["background.skybox_enabled"].isChecked(),
            
            # IBL
            'ibl_enabled': self._controls["ibl.enabled"].isChecked(),
            'ibl_intensity': self._controls["ibl.intensity"].value(),
            'ibl_rotation': self._controls["ibl.rotation"].value(),
            'ibl_source': self._controls["ibl.file"].currentData() or "",
            'ibl_fallback': "",  # Не используется в UI, но нужно для совместимости
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
            
            # Ambient Occlusion
            'ao_enabled': self._controls["ao.enabled"].isChecked(),
            'ao_strength': self._controls["ao.strength"].value(),
            'ao_radius': self._controls["ao.radius"].value(),
        }
    
    def set_state(self, state: Dict[str, Any]):
        """Установить состояние из словаря
        
        Args:
            state: Словарь с параметрами окружения
        """
        # Временно блокируем сигналы и UI updates
        self._updating_ui = True
        for control in self._controls.values():
            try:
                control.blockSignals(True)
            except:
                pass
        
        try:
            # Background
            if 'background_color' in state:
                self._controls["background.color"].set_color(state['background_color'])
            if 'skybox_enabled' in state:
                self._controls["background.skybox_enabled"].setChecked(state['skybox_enabled'])
            
            # IBL
            if 'ibl_enabled' in state:
                self._controls["ibl.enabled"].setChecked(state['ibl_enabled'])
            if 'ibl_intensity' in state:
                self._controls["ibl.intensity"].set_value(state['ibl_intensity'])
            if 'ibl_rotation' in state:
                self._controls["ibl.rotation"].set_value(state['ibl_rotation'])
            if 'ibl_source' in state:
                # Ищем в ComboBox нужный путь
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
            
            # Ambient Occlusion
            if 'ao_enabled' in state:
                self._controls["ao.enabled"].setChecked(state['ao_enabled'])
            if 'ao_strength' in state:
                self._controls["ao.strength"].set_value(state['ao_strength'])
            if 'ao_radius' in state:
                self._controls["ao.radius"].set_value(state['ao_radius'])
        
        finally:
            # Разблокируем сигналы и UI
            for control in self._controls.values():
                try:
                    control.blockSignals(False)
                except:
                    pass
            self._updating_ui = False
    
    def get_controls(self) -> Dict[str, Any]:
        """Получить словарь контролов для внешнего управления"""
        return self._controls
    
    def set_updating_ui(self, updating: bool) -> None:
        """Установить флаг обновления UI"""
        self._updating_ui = updating
