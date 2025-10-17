# -*- coding: utf-8 -*-
"""
Materials Tab - вкладка настроек PBR материалов всех компонентов
Part of modular GraphicsPanel restructuring
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel,
    QTabWidget, QHBoxLayout
)
from PySide6.QtCore import Signal
from typing import Dict, Any

from .widgets import ColorButton, LabeledSlider


class MaterialsTab(QWidget):
    """Вкладка настроек материалов: металл, стекло, рама, рычаг, цилиндр
    
    Signals:
        materials_changed: Dict[str, Any] - параметры материалов изменились
    """
    
    materials_changed = Signal(dict)
    
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
        
        # Tabs for different materials
        self.material_tabs = QTabWidget()
        
        # Add material groups as tabs
        self.material_tabs.addTab(self._create_metal_material(), "Металл")
        self.material_tabs.addTab(self._create_glass_material(), "Стекло")
        self.material_tabs.addTab(self._create_frame_material(), "Рама")
        self.material_tabs.addTab(self._create_cylinder_material(), "Цилиндр")
        
        layout.addWidget(self.material_tabs)
    
    def _create_metal_material(self) -> QWidget:
        """Создать настройки металлического материала"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Base color
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Базовый цвет:"))
        self.metal_color_button = ColorButton("#808080")
        color_layout.addWidget(self.metal_color_button)
        color_layout.addStretch()
        layout.addLayout(color_layout)
        
        # Metalness
        self.metal_metalness_slider = LabeledSlider(
            "Металличность:",
            minimum=0.0,
            maximum=1.0,
            value=1.0,
            step=0.01,
            suffix=""
        )
        layout.addWidget(self.metal_metalness_slider)
        
        # Roughness
        self.metal_roughness_slider = LabeledSlider(
            "Шероховатость:",
            minimum=0.0,
            maximum=1.0,
            value=0.3,
            step=0.01,
            suffix=""
        )
        layout.addWidget(self.metal_roughness_slider)
        
        # Clearcoat
        self.metal_clearcoat_slider = LabeledSlider(
            "Лаковое покрытие:",
            minimum=0.0,
            maximum=1.0,
            value=0.0,
            step=0.01,
            suffix=""
        )
        layout.addWidget(self.metal_clearcoat_slider)
        
        # Clearcoat roughness
        self.metal_clearcoat_roughness_slider = LabeledSlider(
            "Шероховатость лака:",
            minimum=0.0,
            maximum=1.0,
            value=0.01,
            step=0.01,
            suffix=""
        )
        layout.addWidget(self.metal_clearcoat_roughness_slider)
        
        layout.addStretch()
        return widget
    
    def _create_glass_material(self) -> QWidget:
        """Создать настройки стеклянного материала"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Base color
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Цвет стекла:"))
        self.glass_color_button = ColorButton("#aaaaaa")
        color_layout.addWidget(self.glass_color_button)
        color_layout.addStretch()
        layout.addLayout(color_layout)
        
        # Opacity
        self.glass_opacity_slider = LabeledSlider(
            "Непрозрачность:",
            minimum=0.0,
            maximum=1.0,
            value=0.3,
            step=0.01,
            suffix=""
        )
        layout.addWidget(self.glass_opacity_slider)
        
        # Roughness
        self.glass_roughness_slider = LabeledSlider(
            "Шероховатость:",
            minimum=0.0,
            maximum=1.0,
            value=0.0,
            step=0.01,
            suffix=""
        )
        layout.addWidget(self.glass_roughness_slider)
        
        # IOR (Index of Refraction)
        self.glass_ior_slider = LabeledSlider(
            "Коэффициент преломления:",
            minimum=1.0,
            maximum=2.5,
            value=1.52,
            step=0.01,
            suffix=""
        )
        layout.addWidget(self.glass_ior_slider)
        
        # Transmission
        self.glass_transmission_slider = LabeledSlider(
            "Пропускание:",
            minimum=0.0,
            maximum=1.0,
            value=0.95,
            step=0.01,
            suffix=""
        )
        layout.addWidget(self.glass_transmission_slider)
        
        layout.addStretch()
        return widget
    
    def _create_frame_material(self) -> QWidget:
        """Создать настройки материала рамы"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Base color
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Цвет рамы:"))
        self.frame_color_button = ColorButton("#2a2a3e")
        color_layout.addWidget(self.frame_color_button)
        color_layout.addStretch()
        layout.addLayout(color_layout)
        
        # Metalness
        self.frame_metalness_slider = LabeledSlider(
            "Металличность:",
            minimum=0.0,
            maximum=1.0,
            value=0.8,
            step=0.01,
            suffix=""
        )
        layout.addWidget(self.frame_metalness_slider)
        
        # Roughness
        self.frame_roughness_slider = LabeledSlider(
            "Шероховатость:",
            minimum=0.0,
            maximum=1.0,
            value=0.4,
            step=0.01,
            suffix=""
        )
        layout.addWidget(self.frame_roughness_slider)
        
        layout.addStretch()
        return widget
    
    def _create_cylinder_material(self) -> QWidget:
        """Создать настройки материала цилиндра"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Base color
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Цвет цилиндра:"))
        self.cylinder_color_button = ColorButton("#606060")
        color_layout.addWidget(self.cylinder_color_button)
        color_layout.addStretch()
        layout.addLayout(color_layout)
        
        # Metalness
        self.cylinder_metalness_slider = LabeledSlider(
            "Металличность:",
            minimum=0.0,
            maximum=1.0,
            value=0.9,
            step=0.01,
            suffix=""
        )
        layout.addWidget(self.cylinder_metalness_slider)
        
        # Roughness
        self.cylinder_roughness_slider = LabeledSlider(
            "Шероховатость:",
            minimum=0.0,
            maximum=1.0,
            value=0.5,
            step=0.01,
            suffix=""
        )
        layout.addWidget(self.cylinder_roughness_slider)
        
        layout.addStretch()
        return widget
    
    def _connect_signals(self):
        """Подключить сигналы контролов"""
        # Metal
        self.metal_color_button.color_changed.connect(self._emit_changes)
        self.metal_metalness_slider.value_changed.connect(self._emit_changes)
        self.metal_roughness_slider.value_changed.connect(self._emit_changes)
        self.metal_clearcoat_slider.value_changed.connect(self._emit_changes)
        self.metal_clearcoat_roughness_slider.value_changed.connect(self._emit_changes)
        
        # Glass
        self.glass_color_button.color_changed.connect(self._emit_changes)
        self.glass_opacity_slider.value_changed.connect(self._emit_changes)
        self.glass_roughness_slider.value_changed.connect(self._emit_changes)
        self.glass_ior_slider.value_changed.connect(self._emit_changes)
        self.glass_transmission_slider.value_changed.connect(self._emit_changes)
        
        # Frame
        self.frame_color_button.color_changed.connect(self._emit_changes)
        self.frame_metalness_slider.value_changed.connect(self._emit_changes)
        self.frame_roughness_slider.value_changed.connect(self._emit_changes)
        
        # Cylinder
        self.cylinder_color_button.color_changed.connect(self._emit_changes)
        self.cylinder_metalness_slider.value_changed.connect(self._emit_changes)
        self.cylinder_roughness_slider.value_changed.connect(self._emit_changes)
    
    def _emit_changes(self):
        """Собрать текущее состояние и испустить сигнал"""
        self._state = self.get_state()
        self.materials_changed.emit(self._state)
    
    def get_state(self) -> Dict[str, Any]:
        """Получить текущее состояние всех параметров
        
        Returns:
            Словарь с параметрами материалов
        """
        return {
            # Metal
            'metal': {
                'color': self.metal_color_button.get_color(),
                'metalness': self.metal_metalness_slider.get_value(),
                'roughness': self.metal_roughness_slider.get_value(),
                'clearcoat': self.metal_clearcoat_slider.get_value(),
                'clearcoat_roughness': self.metal_clearcoat_roughness_slider.get_value()
            },
            
            # Glass
            'glass': {
                'color': self.glass_color_button.get_color(),
                'opacity': self.glass_opacity_slider.get_value(),
                'roughness': self.glass_roughness_slider.get_value(),
                'ior': self.glass_ior_slider.get_value(),
                'transmission': self.glass_transmission_slider.get_value()
            },
            
            # Frame
            'frame': {
                'color': self.frame_color_button.get_color(),
                'metalness': self.frame_metalness_slider.get_value(),
                'roughness': self.frame_roughness_slider.get_value()
            },
            
            # Cylinder
            'cylinder': {
                'color': self.cylinder_color_button.get_color(),
                'metalness': self.cylinder_metalness_slider.get_value(),
                'roughness': self.cylinder_roughness_slider.get_value()
            }
        }
    
    def set_state(self, state: Dict[str, Any]):
        """Установить состояние из словаря
        
        Args:
            state: Словарь с параметрами материалов
        """
        # Temporarily disconnect signals
        self._disconnect_signals_temp()
        
        try:
            # Metal
            if 'metal' in state:
                metal = state['metal']
                if 'color' in metal:
                    self.metal_color_button.set_color(metal['color'])
                if 'metalness' in metal:
                    self.metal_metalness_slider.set_value(metal['metalness'])
                if 'roughness' in metal:
                    self.metal_roughness_slider.set_value(metal['roughness'])
                if 'clearcoat' in metal:
                    self.metal_clearcoat_slider.set_value(metal['clearcoat'])
                if 'clearcoat_roughness' in metal:
                    self.metal_clearcoat_roughness_slider.set_value(metal['clearcoat_roughness'])
            
            # Glass
            if 'glass' in state:
                glass = state['glass']
                if 'color' in glass:
                    self.glass_color_button.set_color(glass['color'])
                if 'opacity' in glass:
                    self.glass_opacity_slider.set_value(glass['opacity'])
                if 'roughness' in glass:
                    self.glass_roughness_slider.set_value(glass['roughness'])
                if 'ior' in glass:
                    self.glass_ior_slider.set_value(glass['ior'])
                if 'transmission' in glass:
                    self.glass_transmission_slider.set_value(glass['transmission'])
            
            # Frame
            if 'frame' in state:
                frame = state['frame']
                if 'color' in frame:
                    self.frame_color_button.set_color(frame['color'])
                if 'metalness' in frame:
                    self.frame_metalness_slider.set_value(frame['metalness'])
                if 'roughness' in frame:
                    self.frame_roughness_slider.set_value(frame['roughness'])
            
            # Cylinder
            if 'cylinder' in state:
                cylinder = state['cylinder']
                if 'color' in cylinder:
                    self.cylinder_color_button.set_color(cylinder['color'])
                if 'metalness' in cylinder:
                    self.cylinder_metalness_slider.set_value(cylinder['metalness'])
                if 'roughness' in cylinder:
                    self.cylinder_roughness_slider.set_value(cylinder['roughness'])
        
        finally:
            # Reconnect signals
            self._connect_signals()
        
        # Update internal state
        self._state = self.get_state()
    
    def _disconnect_signals_temp(self):
        """Временно отключить сигналы (для batch update)"""
        try:
            # Metal
            self.metal_color_button.color_changed.disconnect()
            self.metal_metalness_slider.value_changed.disconnect()
            self.metal_roughness_slider.value_changed.disconnect()
            self.metal_clearcoat_slider.value_changed.disconnect()
            self.metal_clearcoat_roughness_slider.value_changed.disconnect()
            
            # Glass
            self.glass_color_button.color_changed.disconnect()
            self.glass_opacity_slider.value_changed.disconnect()
            self.glass_roughness_slider.value_changed.disconnect()
            self.glass_ior_slider.value_changed.disconnect()
            self.glass_transmission_slider.value_changed.disconnect()
            
            # Frame
            self.frame_color_button.color_changed.disconnect()
            self.frame_metalness_slider.value_changed.disconnect()
            self.frame_roughness_slider.value_changed.disconnect()
            
            # Cylinder
            self.cylinder_color_button.color_changed.disconnect()
            self.cylinder_metalness_slider.value_changed.disconnect()
            self.cylinder_roughness_slider.value_changed.disconnect()
        except:
            pass  # Signals may not be connected yet
