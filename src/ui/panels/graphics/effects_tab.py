# -*- coding: utf-8 -*-
"""
Effects Tab - вкладка настроек визуальных эффектов (Bloom, DoF, Vignette и т.д.)
Part of modular GraphicsPanel restructuring
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QCheckBox
)
from PySide6.QtCore import Signal
from typing import Dict, Any

from .widgets import LabeledSlider


class EffectsTab(QWidget):
    """Вкладка настроек эффектов: Bloom, SSAO, DoF, Vignette
    
    Signals:
        effects_changed: Dict[str, Any] - параметры эффектов изменились
    """
    
    effects_changed = Signal(dict)
    
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
        
        # Bloom group
        layout.addWidget(self._create_bloom_group())
        
        # SSAO group
        layout.addWidget(self._create_ssao_group())
        
        # Depth of Field group
        layout.addWidget(self._create_dof_group())
        
        # Vignette & Misc group
        layout.addWidget(self._create_misc_effects_group())
        
        layout.addStretch()
    
    def _create_bloom_group(self) -> QGroupBox:
        """Создать группу настроек Bloom (свечение)"""
        group = QGroupBox("Bloom (Свечение)")
        layout = QVBoxLayout(group)
        
        # Bloom enabled
        self.bloom_enabled_check = QCheckBox("Включить Bloom")
        self.bloom_enabled_check.setChecked(True)
        layout.addWidget(self.bloom_enabled_check)
        
        # Bloom intensity
        self.bloom_intensity_slider = LabeledSlider(
            "Интенсивность:",
            minimum=0.0,
            maximum=2.0,
            value=0.5,
            step=0.01,
            suffix=""
        )
        layout.addWidget(self.bloom_intensity_slider)
        
        # Bloom threshold
        self.bloom_threshold_slider = LabeledSlider(
            "Порог свечения:",
            minimum=0.0,
            maximum=2.0,
            value=1.0,
            step=0.01,
            suffix=""
        )
        layout.addWidget(self.bloom_threshold_slider)
        
        # Bloom blur passes
        self.bloom_blur_slider = LabeledSlider(
            "Размытие:",
            minimum=1.0,
            maximum=8.0,
            value=4.0,
            step=1.0,
            suffix=" проходов"
        )
        layout.addWidget(self.bloom_blur_slider)
        
        return group
    
    def _create_ssao_group(self) -> QGroupBox:
        """Создать группу настроек SSAO (Screen-Space Ambient Occlusion)"""
        group = QGroupBox("SSAO (Ambient Occlusion)")
        layout = QVBoxLayout(group)
        
        # SSAO enabled
        self.ssao_enabled_check = QCheckBox("Включить SSAO")
        self.ssao_enabled_check.setChecked(True)
        layout.addWidget(self.ssao_enabled_check)
        
        # SSAO strength
        self.ssao_strength_slider = LabeledSlider(
            "Сила SSAO:",
            minimum=0.0,
            maximum=100.0,
            value=50.0,
            step=1.0,
            suffix=""
        )
        layout.addWidget(self.ssao_strength_slider)
        
        # SSAO radius
        self.ssao_radius_slider = LabeledSlider(
            "Радиус SSAO:",
            minimum=0.1,
            maximum=10.0,
            value=1.0,
            step=0.1,
            suffix=" m"
        )
        layout.addWidget(self.ssao_radius_slider)
        
        # SSAO sample count
        self.ssao_samples_slider = LabeledSlider(
            "Количество сэмплов:",
            minimum=4.0,
            maximum=32.0,
            value=16.0,
            step=4.0,
            suffix=""
        )
        layout.addWidget(self.ssao_samples_slider)
        
        return group
    
    def _create_dof_group(self) -> QGroupBox:
        """Создать группу настроек Depth of Field (глубина резкости)"""
        group = QGroupBox("Depth of Field (Глубина резкости)")
        layout = QVBoxLayout(group)
        
        # DoF enabled
        self.dof_enabled_check = QCheckBox("Включить DoF")
        self.dof_enabled_check.setChecked(False)
        layout.addWidget(self.dof_enabled_check)
        
        # DoF focus distance
        self.dof_focus_slider = LabeledSlider(
            "Расстояние фокуса:",
            minimum=0.1,
            maximum=20.0,
            value=5.0,
            step=0.1,
            suffix=" m"
        )
        layout.addWidget(self.dof_focus_slider)
        
        # DoF focus range
        self.dof_range_slider = LabeledSlider(
            "Диапазон фокуса:",
            minimum=0.1,
            maximum=10.0,
            value=2.0,
            step=0.1,
            suffix=" m"
        )
        layout.addWidget(self.dof_range_slider)
        
        # DoF blur amount
        self.dof_blur_slider = LabeledSlider(
            "Сила размытия:",
            minimum=0.0,
            maximum=10.0,
            value=4.0,
            step=0.1,
            suffix=""
        )
        layout.addWidget(self.dof_blur_slider)
        
        return group
    
    def _create_misc_effects_group(self) -> QGroupBox:
        """Создать группу прочих эффектов (Vignette, Motion Blur и т.д.)"""
        group = QGroupBox("Прочие эффекты")
        layout = QVBoxLayout(group)
        
        # Vignette enabled
        self.vignette_enabled_check = QCheckBox("Включить виньетирование")
        self.vignette_enabled_check.setChecked(True)
        layout.addWidget(self.vignette_enabled_check)
        
        # Vignette strength
        self.vignette_strength_slider = LabeledSlider(
            "Сила виньетки:",
            minimum=0.0,
            maximum=1.0,
            value=0.45,
            step=0.01,
            suffix=""
        )
        layout.addWidget(self.vignette_strength_slider)
        
        # Motion blur enabled
        self.motion_blur_check = QCheckBox("Включить Motion Blur")
        self.motion_blur_check.setChecked(False)
        layout.addWidget(self.motion_blur_check)
        
        # Motion blur quality
        self.motion_blur_quality_slider = LabeledSlider(
            "Качество Motion Blur:",
            minimum=1.0,
            maximum=8.0,
            value=4.0,
            step=1.0,
            suffix=" сэмплов"
        )
        layout.addWidget(self.motion_blur_quality_slider)
        
        return group
    
    def _connect_signals(self):
        """Подключить сигналы контролов"""
        # Bloom
        self.bloom_enabled_check.toggled.connect(self._emit_changes)
        self.bloom_intensity_slider.value_changed.connect(self._emit_changes)
        self.bloom_threshold_slider.value_changed.connect(self._emit_changes)
        self.bloom_blur_slider.value_changed.connect(self._emit_changes)
        
        # SSAO
        self.ssao_enabled_check.toggled.connect(self._emit_changes)
        self.ssao_strength_slider.value_changed.connect(self._emit_changes)
        self.ssao_radius_slider.value_changed.connect(self._emit_changes)
        self.ssao_samples_slider.value_changed.connect(self._emit_changes)
        
        # DoF
        self.dof_enabled_check.toggled.connect(self._emit_changes)
        self.dof_focus_slider.value_changed.connect(self._emit_changes)
        self.dof_range_slider.value_changed.connect(self._emit_changes)
        self.dof_blur_slider.value_changed.connect(self._emit_changes)
        
        # Misc
        self.vignette_enabled_check.toggled.connect(self._emit_changes)
        self.vignette_strength_slider.value_changed.connect(self._emit_changes)
        self.motion_blur_check.toggled.connect(self._emit_changes)
        self.motion_blur_quality_slider.value_changed.connect(self._emit_changes)
    
    def _emit_changes(self):
        """Собрать текущее состояние и испустить сигнал"""
        self._state = self.get_state()
        self.effects_changed.emit(self._state)
    
    def get_state(self) -> Dict[str, Any]:
        """Получить текущее состояние всех параметров
        
        Returns:
            Словарь с параметрами эффектов
        """
        return {
            # Bloom
            'bloom_enabled': self.bloom_enabled_check.isChecked(),
            'bloom_intensity': self.bloom_intensity_slider.get_value(),
            'bloom_threshold': self.bloom_threshold_slider.get_value(),
            'bloom_blur_passes': int(self.bloom_blur_slider.get_value()),
            
            # SSAO
            'ssao_enabled': self.ssao_enabled_check.isChecked(),
            'ssao_strength': self.ssao_strength_slider.get_value(),
            'ssao_radius': self.ssao_radius_slider.get_value(),
            'ssao_sample_count': int(self.ssao_samples_slider.get_value()),
            
            # DoF
            'dof_enabled': self.dof_enabled_check.isChecked(),
            'dof_focus_distance': self.dof_focus_slider.get_value(),
            'dof_focus_range': self.dof_range_slider.get_value(),
            'dof_blur_amount': self.dof_blur_slider.get_value(),
            
            # Misc
            'vignette_enabled': self.vignette_enabled_check.isChecked(),
            'vignette_strength': self.vignette_strength_slider.get_value(),
            'motion_blur_enabled': self.motion_blur_check.isChecked(),
            'motion_blur_quality': int(self.motion_blur_quality_slider.get_value())
        }
    
    def set_state(self, state: Dict[str, Any]):
        """Установить состояние из словаря
        
        Args:
            state: Словарь с параметрами эффектов
        """
        # Temporarily disconnect signals
        self._disconnect_signals_temp()
        
        try:
            # Bloom
            if 'bloom_enabled' in state:
                self.bloom_enabled_check.setChecked(state['bloom_enabled'])
            if 'bloom_intensity' in state:
                self.bloom_intensity_slider.set_value(state['bloom_intensity'])
            if 'bloom_threshold' in state:
                self.bloom_threshold_slider.set_value(state['bloom_threshold'])
            if 'bloom_blur_passes' in state:
                self.bloom_blur_slider.set_value(float(state['bloom_blur_passes']))
            
            # SSAO
            if 'ssao_enabled' in state:
                self.ssao_enabled_check.setChecked(state['ssao_enabled'])
            if 'ssao_strength' in state:
                self.ssao_strength_slider.set_value(state['ssao_strength'])
            if 'ssao_radius' in state:
                self.ssao_radius_slider.set_value(state['ssao_radius'])
            if 'ssao_sample_count' in state:
                self.ssao_samples_slider.set_value(float(state['ssao_sample_count']))
            
            # DoF
            if 'dof_enabled' in state:
                self.dof_enabled_check.setChecked(state['dof_enabled'])
            if 'dof_focus_distance' in state:
                self.dof_focus_slider.set_value(state['dof_focus_distance'])
            if 'dof_focus_range' in state:
                self.dof_range_slider.set_value(state['dof_focus_range'])
            if 'dof_blur_amount' in state:
                self.dof_blur_slider.set_value(state['dof_blur_amount'])
            
            # Misc
            if 'vignette_enabled' in state:
                self.vignette_enabled_check.setChecked(state['vignette_enabled'])
            if 'vignette_strength' in state:
                self.vignette_strength_slider.set_value(state['vignette_strength'])
            if 'motion_blur_enabled' in state:
                self.motion_blur_check.setChecked(state['motion_blur_enabled'])
            if 'motion_blur_quality' in state:
                self.motion_blur_quality_slider.set_value(float(state['motion_blur_quality']))
        
        finally:
            # Reconnect signals
            self._connect_signals()
        
        # Update internal state
        self._state = self.get_state()
    
    def _disconnect_signals_temp(self):
        """Временно отключить сигналы (для batch update)"""
        try:
            # Bloom
            self.bloom_enabled_check.toggled.disconnect()
            self.bloom_intensity_slider.value_changed.disconnect()
            self.bloom_threshold_slider.value_changed.disconnect()
            self.bloom_blur_slider.value_changed.disconnect()
            
            # SSAO
            self.ssao_enabled_check.toggled.disconnect()
            self.ssao_strength_slider.value_changed.disconnect()
            self.ssao_radius_slider.value_changed.disconnect()
            self.ssao_samples_slider.value_changed.disconnect()
            
            # DoF
            self.dof_enabled_check.toggled.disconnect()
            self.dof_focus_slider.value_changed.disconnect()
            self.dof_range_slider.value_changed.disconnect()
            self.dof_blur_slider.value_changed.disconnect()
            
            # Misc
            self.vignette_enabled_check.toggled.disconnect()
            self.vignette_strength_slider.value_changed.disconnect()
            self.motion_blur_check.toggled.disconnect()
            self.motion_blur_quality_slider.value_changed.disconnect()
        except:
            pass  # Signals may not be connected yet
