# -*- coding: utf-8 -*-
"""
Camera Tab - вкладка настроек камеры
Part of modular GraphicsPanel restructuring

СТРУКТУРА ТОЧНО ПОВТОРЯЕТ МОНОЛИТ panel_graphics.py (строки 1303-1370):
- Одна группа "Камера" со всеми параметрами
- FOV, near, far, speed, auto_rotate, auto_rotate_speed
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QCheckBox, QGridLayout, QPushButton
)
from PySide6.QtCore import Signal
from typing import Dict, Any

from .widgets import LabeledSlider


class CameraTab(QWidget):
    """Вкладка настроек камеры: FOV, clipping, auto-rotate, auto-fit
    
    Signals:
        camera_changed: Dict[str, Any] - параметры камеры изменились
    """
    
    camera_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Контролы UI
        self._controls: Dict[str, Any] = {}
        self._updating_ui = False
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Построить UI вкладки - ТОЧНО КАК В МОНОЛИТЕ + автофит"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # ✅ ТОЧНО КАК В МОНОЛИТЕ - одна группа "Камера"
        group = QGroupBox("Камера", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        
        # FOV slider (10-120°)
        fov = LabeledSlider("Поле зрения", 10.0, 120.0, 0.5, decimals=1, unit="°")
        fov.valueChanged.connect(lambda v: self._on_control_changed("fov", v))
        self._controls["fov"] = fov
        grid.addWidget(fov, 0, 0, 1, 2)
        
        # Near clipping plane (1-100 мм)
        near_clip = LabeledSlider("Ближняя плоскость", 1.0, 100.0, 1.0, decimals=1, unit="мм")
        near_clip.valueChanged.connect(lambda v: self._on_control_changed("near", v))
        self._controls["near"] = near_clip
        grid.addWidget(near_clip, 1, 0, 1, 2)
        
        # Far clipping plane (1000-100000 мм)
        far_clip = LabeledSlider("Дальняя плоскость", 1000.0, 100000.0, 500.0, decimals=0, unit="мм")
        far_clip.valueChanged.connect(lambda v: self._on_control_changed("far", v))
        self._controls["far"] = far_clip
        grid.addWidget(far_clip, 2, 0, 1, 2)
        
        # Camera speed (0.1-5.0)
        speed = LabeledSlider("Скорость камеры", 0.1, 5.0, 0.1, decimals=2)
        speed.valueChanged.connect(lambda v: self._on_control_changed("speed", v))
        self._controls["speed"] = speed
        grid.addWidget(speed, 3, 0, 1, 2)
        
        # Auto-rotate checkbox
        auto_rotate = QCheckBox("Автоповорот", self)
        auto_rotate.clicked.connect(lambda checked: self._on_control_changed("auto_rotate", checked))
        self._controls["auto_rotate"] = auto_rotate
        grid.addWidget(auto_rotate, 4, 0, 1, 2)
        
        # Auto-rotate speed (0.1-3.0)
        rotate_speed = LabeledSlider("Скорость автоповорота", 0.1, 3.0, 0.05, decimals=2)
        rotate_speed.valueChanged.connect(lambda v: self._on_control_changed("auto_rotate_speed", v))
        self._controls["auto_rotate_speed"] = rotate_speed
        grid.addWidget(rotate_speed, 5, 0, 1, 2)

        # Auto-fit checkbox
        auto_fit = QCheckBox("Автоподгон камеры при изменении геометрии", self)
        auto_fit.setToolTip("Если включено, камера автоматически центрируется и подгоняется при изменении геометрии. Также доступно двойным кликом по сцене.")
        auto_fit.clicked.connect(lambda checked: self._on_control_changed("auto_fit", checked))
        self._controls["auto_fit"] = auto_fit
        grid.addWidget(auto_fit, 6, 0, 1, 2)

        # Hint button (manual center)
        hint_btn = QPushButton("Двойной клик по сцене — автофит", self)
        hint_btn.setEnabled(False)
        grid.addWidget(hint_btn, 7, 0, 1, 2)
        
        layout.addWidget(group)
        layout.addStretch(1)
    
    # ========== ОБРАБОТЧИКИ ИЗМЕНЕНИЙ ========= =
    
    def _on_control_changed(self, key: str, value: Any) -> None:
        """Обработчик изменения любого контрола"""
        if self._updating_ui:
            return
        # Эмитим сигнал
        self.camera_changed.emit(self.get_state())
    
    # ========== ГЕТТЕРЫ/СЕТТЕРЫ СОСТОЯНИЯ ========= =
    
    def get_state(self) -> Dict[str, Any]:
        """Получить текущее состояние всех параметров камеры
        
        Returns:
            Словарь с параметрами - ТОЧНО КАК В МОНОЛИТЕ + auto_fit
        """
        return {
            'fov': self._controls["fov"].value(),
            'near': self._controls["near"].value(),
            'far': self._controls["far"].value(),
            'speed': self._controls["speed"].value(),
            'auto_rotate': self._controls["auto_rotate"].isChecked(),
            'auto_rotate_speed': self._controls["auto_rotate_speed"].value(),
            'auto_fit': self._controls["auto_fit"].isChecked(),
        }
    
    def set_state(self, state: Dict[str, Any]):
        """Установить состояние из словаря
        
        Args:
            state: Словарь с параметрами камеры
        """
        # Временно блокируем сигналы и UI updates
        self._updating_ui = True
        for control in self._controls.values():
            try:
                control.blockSignals(True)
            except:
                pass
        
        try:
            # FOV
            if 'fov' in state:
                self._controls["fov"].set_value(state['fov'])
            
            # Clipping planes
            if 'near' in state:
                self._controls["near"].set_value(state['near'])
            if 'far' in state:
                self._controls["far"].set_value(state['far'])
            
            # Speed
            if 'speed' in state:
                self._controls["speed"].set_value(state['speed'])
            
            # Auto-rotate
            if 'auto_rotate' in state:
                self._controls["auto_rotate"].setChecked(state['auto_rotate'])
            if 'auto_rotate_speed' in state:
                self._controls["auto_rotate_speed"].set_value(state['auto_rotate_speed'])

            # Auto-fit
            if 'auto_fit' in state:
                self._controls["auto_fit"].setChecked(state['auto_fit'])
        
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
