# -*- coding: utf-8 -*-
"""
Quality Tab - вкладка настроек качества рендеринга (тени, AA, производительность)
Part of modular GraphicsPanel restructuring
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QLabel,
    QComboBox, QCheckBox, QPushButton, QHBoxLayout
)
from PySide6.QtCore import Signal, Slot
from typing import Dict, Any

from .widgets import LabeledSlider


class QualityTab(QWidget):
    """Вкладка настроек качества рендеринга: тени, AA, производительность
    
    Signals:
        quality_changed: Dict[str, Any] - параметры качества изменились
    """
    
    quality_changed = Signal(dict)
    
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
        
        # Antialiasing group
        layout.addWidget(self._create_antialiasing_group())
        
        # Shadows group
        layout.addWidget(self._create_shadows_group())
        
        # Performance presets
        layout.addWidget(self._create_presets_group())
        
        layout.addStretch()
    
    def _create_antialiasing_group(self) -> QGroupBox:
        """Создать группу настроек сглаживания"""
        group = QGroupBox("Сглаживание (Anti-Aliasing)")
        layout = QVBoxLayout(group)
        
        # AA mode
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("Режим AA:"))
        self.aa_mode_combo = QComboBox()
        self.aa_mode_combo.addItems([
            "Нет",
            "MSAA",
            "SSAA",
            "Progressive AA"
        ])
        self.aa_mode_combo.setCurrentText("MSAA")
        mode_layout.addWidget(self.aa_mode_combo)
        mode_layout.addStretch()
        layout.addLayout(mode_layout)
        
        # AA quality (samples)
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Качество AA:"))
        self.aa_quality_combo = QComboBox()
        self.aa_quality_combo.addItems([
            "2x",
            "4x",
            "8x"
        ])
        self.aa_quality_combo.setCurrentText("4x")
        quality_layout.addWidget(self.aa_quality_combo)
        quality_layout.addStretch()
        layout.addLayout(quality_layout)
        
        return group
    
    def _create_shadows_group(self) -> QGroupBox:
        """Создать группу настроек теней"""
        group = QGroupBox("Тени")
        layout = QVBoxLayout(group)
        
        # Shadows enabled
        self.shadows_enabled_check = QCheckBox("Включить тени")
        self.shadows_enabled_check.setChecked(True)
        layout.addWidget(self.shadows_enabled_check)
        
        # Shadow quality
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Качество теней:"))
        self.shadow_quality_combo = QComboBox()
        self.shadow_quality_combo.addItems([
            "Низкое",
            "Среднее",
            "Высокое",
            "Ультра"
        ])
        self.shadow_quality_combo.setCurrentText("Высокое")
        quality_layout.addWidget(self.shadow_quality_combo)
        quality_layout.addStretch()
        layout.addLayout(quality_layout)
        
        # Shadow map size
        mapsize_layout = QHBoxLayout()
        mapsize_layout.addWidget(QLabel("Размер карты теней:"))
        self.shadow_mapsize_combo = QComboBox()
        self.shadow_mapsize_combo.addItems([
            "512",
            "1024",
            "2048",
            "4096"
        ])
        self.shadow_mapsize_combo.setCurrentText("2048")
        mapsize_layout.addWidget(self.shadow_mapsize_combo)
        mapsize_layout.addStretch()
        layout.addLayout(mapsize_layout)
        
        # Shadow softness
        self.shadow_softness_slider = LabeledSlider(
            "Мягкость теней:",
            minimum=0.0,
            maximum=1.0,
            value=0.5,
            step=0.01,
            suffix=""
        )
        layout.addWidget(self.shadow_softness_slider)
        
        # Shadow bias
        self.shadow_bias_slider = LabeledSlider(
            "Shadow Bias:",
            minimum=0.0,
            maximum=1.0,
            value=0.01,
            step=0.001,
            suffix=""
        )
        layout.addWidget(self.shadow_bias_slider)
        
        return group
    
    def _create_presets_group(self) -> QGroupBox:
        """Создать группу пресетов производительности"""
        group = QGroupBox("Пресеты производительности")
        layout = QVBoxLayout(group)
        
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Быстрый выбор:"))
        
        self.preset_low_button = QPushButton("Низкое")
        self.preset_low_button.clicked.connect(lambda: self._apply_preset('low'))
        preset_layout.addWidget(self.preset_low_button)
        
        self.preset_medium_button = QPushButton("Среднее")
        self.preset_medium_button.clicked.connect(lambda: self._apply_preset('medium'))
        preset_layout.addWidget(self.preset_medium_button)
        
        self.preset_high_button = QPushButton("Высокое")
        self.preset_high_button.clicked.connect(lambda: self._apply_preset('high'))
        preset_layout.addWidget(self.preset_high_button)
        
        self.preset_ultra_button = QPushButton("Ультра")
        self.preset_ultra_button.clicked.connect(lambda: self._apply_preset('ultra'))
        preset_layout.addWidget(self.preset_ultra_button)
        
        preset_layout.addStretch()
        layout.addLayout(preset_layout)
        
        return group
    
    def _connect_signals(self):
        """Подключить сигналы контролов"""
        # Antialiasing
        self.aa_mode_combo.currentTextChanged.connect(self._emit_changes)
        self.aa_quality_combo.currentTextChanged.connect(self._emit_changes)
        
        # Shadows
        self.shadows_enabled_check.toggled.connect(self._emit_changes)
        self.shadow_quality_combo.currentTextChanged.connect(self._emit_changes)
        self.shadow_mapsize_combo.currentTextChanged.connect(self._emit_changes)
        self.shadow_softness_slider.value_changed.connect(self._emit_changes)
        self.shadow_bias_slider.value_changed.connect(self._emit_changes)
    
    @Slot(str)
    def _apply_preset(self, preset_name: str):
        """Применить пресет качества
        
        Args:
            preset_name: Имя пресета ('low', 'medium', 'high', 'ultra')
        """
        presets = {
            'low': {
                'aa_mode': 'Нет',
                'aa_quality': '2x',
                'shadows_enabled': False,
                'shadow_quality': 'Низкое',
                'shadow_mapsize': '512',
                'shadow_softness': 0.2,
                'shadow_bias': 0.05
            },
            'medium': {
                'aa_mode': 'MSAA',
                'aa_quality': '2x',
                'shadows_enabled': True,
                'shadow_quality': 'Среднее',
                'shadow_mapsize': '1024',
                'shadow_softness': 0.4,
                'shadow_bias': 0.02
            },
            'high': {
                'aa_mode': 'MSAA',
                'aa_quality': '4x',
                'shadows_enabled': True,
                'shadow_quality': 'Высокое',
                'shadow_mapsize': '2048',
                'shadow_softness': 0.5,
                'shadow_bias': 0.01
            },
            'ultra': {
                'aa_mode': 'SSAA',
                'aa_quality': '8x',
                'shadows_enabled': True,
                'shadow_quality': 'Ультра',
                'shadow_mapsize': '4096',
                'shadow_softness': 0.7,
                'shadow_bias': 0.005
            }
        }
        
        if preset_name in presets:
            self.set_state(presets[preset_name])
            self._emit_changes()
    
    def _emit_changes(self):
        """Собрать текущее состояние и испустить сигнал"""
        self._state = self.get_state()
        self.quality_changed.emit(self._state)
    
    def get_state(self) -> Dict[str, Any]:
        """Получить текущее состояние всех параметров
        
        Returns:
            Словарь с параметрами качества
        """
        return {
            # Antialiasing
            'antialiasing': self._aa_mode_to_enum(self.aa_mode_combo.currentText()),
            'aa_quality': self._aa_quality_to_samples(self.aa_quality_combo.currentText()),
            
            # Shadows
            'shadows_enabled': self.shadows_enabled_check.isChecked(),
            'shadow_quality': self.shadow_quality_combo.currentText(),
            'shadow_mapsize': int(self.shadow_mapsize_combo.currentText()),
            'shadow_softness': self.shadow_softness_slider.get_value(),
            'shadow_bias': self.shadow_bias_slider.get_value()
        }
    
    def set_state(self, state: Dict[str, Any]):
        """Установить состояние из словаря
        
        Args:
            state: Словарь с параметрами качества
        """
        # Temporarily disconnect signals
        self._disconnect_signals_temp()
        
        try:
            # Antialiasing
            if 'aa_mode' in state:
                index = self.aa_mode_combo.findText(state['aa_mode'])
                if index >= 0:
                    self.aa_mode_combo.setCurrentIndex(index)
            
            if 'aa_quality' in state:
                index = self.aa_quality_combo.findText(state['aa_quality'])
                if index >= 0:
                    self.aa_quality_combo.setCurrentIndex(index)
            
            # Shadows
            if 'shadows_enabled' in state:
                self.shadows_enabled_check.setChecked(state['shadows_enabled'])
            
            if 'shadow_quality' in state:
                index = self.shadow_quality_combo.findText(state['shadow_quality'])
                if index >= 0:
                    self.shadow_quality_combo.setCurrentIndex(index)
            
            if 'shadow_mapsize' in state:
                index = self.shadow_mapsize_combo.findText(str(state['shadow_mapsize']))
                if index >= 0:
                    self.shadow_mapsize_combo.setCurrentIndex(index)
            
            if 'shadow_softness' in state:
                self.shadow_softness_slider.set_value(state['shadow_softness'])
            
            if 'shadow_bias' in state:
                self.shadow_bias_slider.set_value(state['shadow_bias'])
        
        finally:
            # Reconnect signals
            self._connect_signals()
        
        # Update internal state
        self._state = self.get_state()
    
    def _aa_mode_to_enum(self, mode_text: str) -> int:
        """Преобразовать текст режима AA в enum
        
        Args:
            mode_text: Текстовое название режима
            
        Returns:
            SceneEnvironment enum value (0=NoAA, 1=SSAA, 2=MSAA, 3=ProgressiveAA)
        """
        mapping = {
            'Нет': 0,
            'SSAA': 1,
            'MSAA': 2,
            'Progressive AA': 3
        }
        return mapping.get(mode_text, 2)  # Default: MSAA
    
    def _aa_quality_to_samples(self, quality_text: str) -> int:
        """Преобразовать текст качества AA в количество samples
        
        Args:
            quality_text: Текстовое качество ('2x', '4x', '8x')
            
        Returns:
            Количество samples
        """
        return int(quality_text.replace('x', ''))
    
    def _disconnect_signals_temp(self):
        """Временно отключить сигналы (для batch update)"""
        try:
            self.aa_mode_combo.currentTextChanged.disconnect()
            self.aa_quality_combo.currentTextChanged.disconnect()
            self.shadows_enabled_check.toggled.disconnect()
            self.shadow_quality_combo.currentTextChanged.disconnect()
            self.shadow_mapsize_combo.currentTextChanged.disconnect()
            self.shadow_softness_slider.value_changed.disconnect()
            self.shadow_bias_slider.value_changed.disconnect()
        except:
            pass  # Signals may not be connected yet
