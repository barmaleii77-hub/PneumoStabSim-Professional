# -*- coding: utf-8 -*-
"""
Camera Tab - вкладка настроек камеры (FOV, clipping, auto-rotate)
Part of modular GraphicsPanel restructuring
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel,
    QCheckBox, QHBoxLayout
)
from PySide6.QtCore import Signal
from typing import Dict, Any

from .widgets import LabeledSlider


class CameraTab(QWidget):
    """Вкладка настроек камеры: FOV, clipping, auto-rotate
    
    Signals:
        camera_changed: Dict[str, Any] - параметры камеры изменились
    """
    
    camera_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Current state
        self._state = {}
        
        # Setup UI
        self._setup_ui()
        
        # Connect signals
        self._connect_signals()
    
    def _setup_ui(self):
        """Построить UI вкладки"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Field of view group
        layout.addWidget(self._create_fov_group())
        
        # Clipping planes group
        layout.addWidget(self._create_clipping_group())
        
        # Camera behavior group
        layout.addWidget(self._create_behavior_group())
        
        layout.addStretch()
    
    def _create_fov_group(self) -> QGroupBox:
        """Создать группу настроек поля зрения"""
        group = QGroupBox("Поле зрения (Field of View)")
        layout = QVBoxLayout(group)
        
        # FOV slider
        self.fov_slider = LabeledSlider(
            "FOV:",
            minimum=30.0,
            maximum=120.0,
            value=60.0,
            step=1.0,
            suffix="°"
        )
        layout.addWidget(self.fov_slider)
        
        return group
    
    def _create_clipping_group(self) -> QGroupBox:
        """Создать группу настроек clipping planes"""
        group = QGroupBox("Плоскости отсечения (Clipping Planes)")
        layout = QVBoxLayout(group)
        
        # Near clipping
        self.near_clip_slider = LabeledSlider(
            "Near Clip:",
            minimum=0.01,
            maximum=10.0,
            value=0.1,
            step=0.01,
            suffix=" m"
        )
        layout.addWidget(self.near_clip_slider)
        
        # Far clipping
        self.far_clip_slider = LabeledSlider(
            "Far Clip:",
            minimum=10.0,
            maximum=1000.0,
            value=100.0,
            step=10.0,
            suffix=" m"
        )
        layout.addWidget(self.far_clip_slider)
        
        return group
    
    def _create_behavior_group(self) -> QGroupBox:
        """Создать группу настроек поведения камеры"""
        group = QGroupBox("Поведение камеры")
        layout = QVBoxLayout(group)
        
        # Auto-rotate enabled
        self.auto_rotate_check = QCheckBox("Автоматическое вращение")
        self.auto_rotate_check.setChecked(False)
        layout.addWidget(self.auto_rotate_check)
        
        # Auto-rotate speed
        self.auto_rotate_speed_slider = LabeledSlider(
            "Скорость вращения:",
            minimum=0.1,
            maximum=5.0,
            value=1.0,
            step=0.1,
            suffix=" °/s"
        )
        layout.addWidget(self.auto_rotate_speed_slider)
        
        # Camera distance
        self.camera_distance_slider = LabeledSlider(
            "Расстояние камеры:",
            minimum=1.0,
            maximum=20.0,
            value=5.0,
            step=0.1,
            suffix=" m"
        )
        layout.addWidget(self.camera_distance_slider)
        
        # Camera speed (mouse control)
        self.camera_speed_slider = LabeledSlider(
            "Чувствительность мыши:",
            minimum=0.1,
            maximum=5.0,
            value=1.0,
            step=0.1,
            suffix=""
        )
        layout.addWidget(self.camera_speed_slider)
        
        return group
    
    def _connect_signals(self):
        """Подключить сигналы контролов"""
        # FOV
        self.fov_slider.value_changed.connect(self._emit_changes)
        
        # Clipping
        self.near_clip_slider.value_changed.connect(self._emit_changes)
        self.far_clip_slider.value_changed.connect(self._emit_changes)
        
        # Behavior
        self.auto_rotate_check.toggled.connect(self._emit_changes)
        self.auto_rotate_speed_slider.value_changed.connect(self._emit_changes)
        self.camera_distance_slider.value_changed.connect(self._emit_changes)
        self.camera_speed_slider.value_changed.connect(self._emit_changes)
    
    def _emit_changes(self):
        """Собрать текущее состояние и испустить сигнал"""
        self._state = self.get_state()
        self.camera_changed.emit(self._state)
    
    def get_state(self) -> Dict[str, Any]:
        """Получить текущее состояние всех параметров
        
        Returns:
            Словарь с параметрами камеры
        """
        return {
            # FOV
            'fov': self.fov_slider.get_value(),
            
            # Clipping
            'near_clip': self.near_clip_slider.get_value(),
            'far_clip': self.far_clip_slider.get_value(),
            
            # Behavior
            'auto_rotate': self.auto_rotate_check.isChecked(),
            'auto_rotate_speed': self.auto_rotate_speed_slider.get_value(),
            'camera_distance': self.camera_distance_slider.get_value(),
            'camera_speed': self.camera_speed_slider.get_value()
        }
    
    def set_state(self, state: Dict[str, Any]):
        """Установить состояние из словаря
        
        Args:
            state: Словарь с параметрами камеры
        """
        # Temporarily disconnect signals
        self._disconnect_signals_temp()
        
        try:
            # FOV
            if 'fov' in state:
                self.fov_slider.set_value(state['fov'])
            
            # Clipping
            if 'near_clip' in state:
                self.near_clip_slider.set_value(state['near_clip'])
            
            if 'far_clip' in state:
                self.far_clip_slider.set_value(state['far_clip'])
            
            # Behavior
            if 'auto_rotate' in state:
                self.auto_rotate_check.setChecked(state['auto_rotate'])
            
            if 'auto_rotate_speed' in state:
                self.auto_rotate_speed_slider.set_value(state['auto_rotate_speed'])
            
            if 'camera_distance' in state:
                self.camera_distance_slider.set_value(state['camera_distance'])
            
            if 'camera_speed' in state:
                self.camera_speed_slider.set_value(state['camera_speed'])
        
        finally:
            # Reconnect signals
            self._connect_signals()
        
        # Update internal state
        self._state = self.get_state()
    
    def _disconnect_signals_temp(self):
        """Временно отключить сигналы (для batch update)"""
        try:
            self.fov_slider.value_changed.disconnect()
            self.near_clip_slider.value_changed.disconnect()
            self.far_clip_slider.value_changed.disconnect()
            self.auto_rotate_check.toggled.disconnect()
            self.auto_rotate_speed_slider.value_changed.disconnect()
            self.camera_distance_slider.value_changed.disconnect()
            self.camera_speed_slider.value_changed.disconnect()
        except:
            pass  # Signals may not be connected yet
