# -*- coding: utf-8 -*-
"""
Environment Tab - вкладка настроек окружения (фон, IBL, туман)
Part of modular GraphicsPanel restructuring
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel, 
    QComboBox, QCheckBox, QPushButton, QFileDialog,
    QHBoxLayout, QLineEdit
)
from PySide6.QtCore import Signal, Slot
from pathlib import Path
from typing import Dict, Any, Optional

from .widgets import ColorButton, LabeledSlider


class EnvironmentTab(QWidget):
    """Вкладка настроек окружения: фон, IBL, туман
    
    Signals:
        environment_changed: Dict[str, Any] - параметры окружения изменились
    """
    
    environment_changed = Signal(dict)
    
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
        
        # Background group
        layout.addWidget(self._create_background_group())
        
        # IBL group
        layout.addWidget(self._create_ibl_group())
        
        # Fog group
        layout.addWidget(self._create_fog_group())
        
        layout.addStretch()
    
    def _create_background_group(self) -> QGroupBox:
        """Создать группу настроек фона"""
        group = QGroupBox("Фон")
        layout = QVBoxLayout(group)
        
        # Background mode
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Режим:"))
        self.background_mode_combo = QComboBox()
        self.background_mode_combo.addItems([
            "Цвет",
            "Skybox",
            "Прозрачный"
        ])
        mode_layout.addWidget(self.background_mode_combo)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        
        # Background color
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Цвет фона:"))
        self.bg_color_button = ColorButton("#1a1a2e")
        color_layout.addWidget(self.bg_color_button)
        color_layout.addStretch()
        layout.addLayout(color_layout)
        
        # Skybox enabled
        self.skybox_enabled_check = QCheckBox("Показывать Skybox")
        self.skybox_enabled_check.setChecked(True)
        layout.addWidget(self.skybox_enabled_check)
        
        # Skybox blur
        self.skybox_blur_slider = LabeledSlider(
            "Размытие Skybox:",
            minimum=0.0,
            maximum=1.0,
            value=0.0,
            step=0.01,
            suffix=""
        )
        layout.addWidget(self.skybox_blur_slider)
        
        return group
    
    def _create_ibl_group(self) -> QGroupBox:
        """Создать группу настроек IBL (Image-Based Lighting)"""
        group = QGroupBox("IBL (Image-Based Lighting)")
        layout = QVBoxLayout(group)
        
        # IBL enabled
        self.ibl_enabled_check = QCheckBox("Включить IBL")
        self.ibl_enabled_check.setChecked(True)
        layout.addWidget(self.ibl_enabled_check)
        
        # IBL source selection
        source_layout = QHBoxLayout()
        source_layout.addWidget(QLabel("HDR источник:"))
        self.ibl_source_line = QLineEdit()
        self.ibl_source_line.setPlaceholderText("assets/hdr/studio.hdr")
        self.ibl_source_line.setReadOnly(True)
        source_layout.addWidget(self.ibl_source_line)
        
        self.ibl_browse_button = QPushButton("Обзор...")
        self.ibl_browse_button.clicked.connect(self._browse_ibl_source)
        source_layout.addWidget(self.ibl_browse_button)
        layout.addLayout(source_layout)
        
        # IBL fallback
        fallback_layout = QHBoxLayout()
        fallback_layout.addWidget(QLabel("Fallback HDR:"))
        self.ibl_fallback_line = QLineEdit()
        self.ibl_fallback_line.setPlaceholderText("assets/hdr/default.hdr")
        self.ibl_fallback_line.setReadOnly(True)
        fallback_layout.addWidget(self.ibl_fallback_line)
        
        self.ibl_fallback_button = QPushButton("Обзор...")
        self.ibl_fallback_button.clicked.connect(self._browse_ibl_fallback)
        fallback_layout.addWidget(self.ibl_fallback_button)
        layout.addLayout(fallback_layout)
        
        # IBL intensity
        self.ibl_intensity_slider = LabeledSlider(
            "Интенсивность IBL:",
            minimum=0.0,
            maximum=5.0,
            value=1.0,
            step=0.1,
            suffix=""
        )
        layout.addWidget(self.ibl_intensity_slider)
        
        # IBL rotation
        self.ibl_rotation_slider = LabeledSlider(
            "Вращение IBL:",
            minimum=0.0,
            maximum=360.0,
            value=0.0,
            step=1.0,
            suffix="°"
        )
        layout.addWidget(self.ibl_rotation_slider)
        
        return group
    
    def _create_fog_group(self) -> QGroupBox:
        """Создать группу настроек тумана"""
        group = QGroupBox("Туман")
        layout = QVBoxLayout(group)
        
        # Fog enabled
        self.fog_enabled_check = QCheckBox("Включить туман")
        self.fog_enabled_check.setChecked(False)
        layout.addWidget(self.fog_enabled_check)
        
        # Fog color
        color_layout = QHBoxLayout()
        color_layout.addWidget(QLabel("Цвет тумана:"))
        self.fog_color_button = ColorButton("#808080")
        color_layout.addWidget(self.fog_color_button)
        color_layout.addStretch()
        layout.addLayout(color_layout)
        
        # Fog density
        self.fog_density_slider = LabeledSlider(
            "Плотность тумана:",
            minimum=0.0,
            maximum=1.0,
            value=0.1,
            step=0.01,
            suffix=""
        )
        layout.addWidget(self.fog_density_slider)
        
        return group
    
    def _connect_signals(self):
        """Подключить сигналы контролов"""
        # Background
        self.background_mode_combo.currentTextChanged.connect(self._emit_changes)
        self.bg_color_button.color_changed.connect(self._emit_changes)
        self.skybox_enabled_check.toggled.connect(self._emit_changes)
        self.skybox_blur_slider.value_changed.connect(self._emit_changes)
        
        # IBL
        self.ibl_enabled_check.toggled.connect(self._emit_changes)
        self.ibl_source_line.textChanged.connect(self._emit_changes)
        self.ibl_fallback_line.textChanged.connect(self._emit_changes)
        self.ibl_intensity_slider.value_changed.connect(self._emit_changes)
        self.ibl_rotation_slider.value_changed.connect(self._emit_changes)
        
        # Fog
        self.fog_enabled_check.toggled.connect(self._emit_changes)
        self.fog_color_button.color_changed.connect(self._emit_changes)
        self.fog_density_slider.value_changed.connect(self._emit_changes)
    
    @Slot()
    def _browse_ibl_source(self):
        """Обзор HDR файла для IBL"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выбрать HDR файл для IBL",
            "assets/hdr",
            "HDR Files (*.hdr *.exr);;All Files (*.*)"
        )
        
        if file_path:
            self.ibl_source_line.setText(file_path)
            self._emit_changes()
    
    @Slot()
    def _browse_ibl_fallback(self):
        """Обзор fallback HDR файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выбрать fallback HDR файл",
            "assets/hdr",
            "HDR Files (*.hdr *.exr);;All Files (*.*)"
        )
        
        if file_path:
            self.ibl_fallback_line.setText(file_path)
            self._emit_changes()
    
    def _emit_changes(self):
        """Собрать текущее состояние и испустить сигнал"""
        self._state = self.get_state()
        self.environment_changed.emit(self._state)
    
    def get_state(self) -> Dict[str, Any]:
        """Получить текущее состояние всех параметров
        
        Returns:
            Словарь с параметрами окружения
        """
        return {
            # Background
            'background_mode': self.background_mode_combo.currentText(),
            'background_color': self.bg_color_button.get_color(),
            'skybox_enabled': self.skybox_enabled_check.isChecked(),
            'skybox_blur': self.skybox_blur_slider.get_value(),
            
            # IBL
            'ibl_enabled': self.ibl_enabled_check.isChecked(),
            'ibl_source': self.ibl_source_line.text(),
            'ibl_fallback': self.ibl_fallback_line.text(),
            'ibl_intensity': self.ibl_intensity_slider.get_value(),
            'ibl_rotation': self.ibl_rotation_slider.get_value(),
            
            # Fog
            'fog_enabled': self.fog_enabled_check.isChecked(),
            'fog_color': self.fog_color_button.get_color(),
            'fog_density': self.fog_density_slider.get_value()
        }
    
    def set_state(self, state: Dict[str, Any]):
        """Установить состояние из словаря
        
        Args:
            state: Словарь с параметрами окружения
        """
        # Temporarily disconnect signals to avoid multiple emissions
        self._disconnect_signals_temp()
        
        try:
            # Background
            if 'background_mode' in state:
                index = self.background_mode_combo.findText(state['background_mode'])
                if index >= 0:
                    self.background_mode_combo.setCurrentIndex(index)
            
            if 'background_color' in state:
                self.bg_color_button.set_color(state['background_color'])
            
            if 'skybox_enabled' in state:
                self.skybox_enabled_check.setChecked(state['skybox_enabled'])
            
            if 'skybox_blur' in state:
                self.skybox_blur_slider.set_value(state['skybox_blur'])
            
            # IBL
            if 'ibl_enabled' in state:
                self.ibl_enabled_check.setChecked(state['ibl_enabled'])
            
            if 'ibl_source' in state:
                self.ibl_source_line.setText(state['ibl_source'])
            
            if 'ibl_fallback' in state:
                self.ibl_fallback_line.setText(state['ibl_fallback'])
            
            if 'ibl_intensity' in state:
                self.ibl_intensity_slider.set_value(state['ibl_intensity'])
            
            if 'ibl_rotation' in state:
                self.ibl_rotation_slider.set_value(state['ibl_rotation'])
            
            # Fog
            if 'fog_enabled' in state:
                self.fog_enabled_check.setChecked(state['fog_enabled'])
            
            if 'fog_color' in state:
                self.fog_color_button.set_color(state['fog_color'])
            
            if 'fog_density' in state:
                self.fog_density_slider.set_value(state['fog_density'])
        
        finally:
            # Reconnect signals
            self._connect_signals()
        
        # Update internal state
        self._state = self.get_state()
    
    def _disconnect_signals_temp(self):
        """Временно отключить сигналы (для batch update)"""
        try:
            self.background_mode_combo.currentTextChanged.disconnect()
            self.bg_color_button.color_changed.disconnect()
            self.skybox_enabled_check.toggled.disconnect()
            self.skybox_blur_slider.value_changed.disconnect()
            
            self.ibl_enabled_check.toggled.disconnect()
            self.ibl_source_line.textChanged.disconnect()
            self.ibl_fallback_line.textChanged.disconnect()
            self.ibl_intensity_slider.value_changed.disconnect()
            self.ibl_rotation_slider.value_changed.disconnect()
            
            self.fog_enabled_check.toggled.disconnect()
            self.fog_color_button.color_changed.disconnect()
            self.fog_density_slider.value_changed.disconnect()
        except:
            pass  # Signals may not be connected yet
