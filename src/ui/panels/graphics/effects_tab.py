 # -*- coding: utf-8 -*-
"""
Effects Tab - вкладка настроек визуальных эффектов (Bloom, DoF, Vignette и т.д.)
Part of modular GraphicsPanel restructuring

СТРУКТУРА ТОЧНО ПОВТОРЯЕТ МОНОЛИТ panel_graphics.py:
- _build_bloom_group() → Bloom эффекты
- _build_tonemap_group() → Тонемаппинг
- _build_dof_group() → Depth of Field
- _build_misc_effects_group() → Дополнительные эффекты (Motion Blur, Lens Flare, Vignette)

✅ ДОПОЛНЕНО: Расширенные параметры из Qt 6.10 ExtendedSceneEnvironment
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QGroupBox, QCheckBox, QComboBox, QLabel, QGridLayout
)
from PySide6.QtCore import Signal
from typing import Dict, Any

from .widgets import LabeledSlider


class EffectsTab(QWidget):
    """Вкладка настроек эффектов: Bloom, Tonemap, DoF, Misc
    
    Signals:
        effects_changed: Dict[str, Any] - параметры эффектов изменились
    """
    
    effects_changed = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Current state - храним ссылки на контролы
        self._controls: Dict[str, Any] = {}
        
        # Setup UI
        self._setup_ui()
    
    def _setup_ui(self):
        """Построить UI вкладки - ТОЧНО КАК В МОНОЛИТЕ + расширенные параметры"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)
        
        # ✅ ТОЧНО КАК В МОНОЛИТЕ - 4 основные группы:
        layout.addWidget(self._build_bloom_group())
        layout.addWidget(self._build_tonemap_group())
        layout.addWidget(self._build_dof_group())
        layout.addWidget(self._build_misc_effects_group())
        
        # ✅ НОВОЕ: Color Adjustments (Qt 6.10+)
        layout.addWidget(self._build_color_adjustments_group())
        
        layout.addStretch(1)
    
    def _build_bloom_group(self) -> QGroupBox:
        """Создать группу Bloom - МОНОЛИТ + расширенные параметры Qt 6.10"""
        group = QGroupBox("Bloom (Свечение)", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        row = 0
        
        # ✅ ИЗ МОНОЛИТА: Checkbox enabled
        enabled = QCheckBox("Включить Bloom", self)
        enabled.clicked.connect(lambda checked: self._on_control_changed("bloom_enabled", checked))
        self._controls["bloom.enabled"] = enabled
        grid.addWidget(enabled, row, 0, 1, 2)
        row += 1

        # ✅ ИЗ МОНОЛИТА: Intensity slider
        intensity = LabeledSlider("Интенсивность (glowIntensity)", 0.0, 2.0, 0.02, decimals=2)
        intensity.valueChanged.connect(lambda v: self._on_control_changed("bloom_intensity", v))
        self._controls["bloom.intensity"] = intensity
        grid.addWidget(intensity, row, 0, 1, 2)
        row += 1

        # ✅ ИЗ МОНОЛИТА: Threshold slider
        threshold = LabeledSlider("Порог (glowHDRMinimumValue)", 0.0, 4.0, 0.05, decimals=2)
        threshold.valueChanged.connect(lambda v: self._on_control_changed("bloom_threshold", v))
        self._controls["bloom.threshold"] = threshold
        grid.addWidget(threshold, row, 0, 1, 2)
        row += 1

        # ✅ ИЗ МОНОЛИТЕ: Spread slider
        spread = LabeledSlider("Распространение (glowBloom)", 0.0, 1.0, 0.01, decimals=2)
        spread.valueChanged.connect(lambda v: self._on_control_changed("bloom_spread", v))
        self._controls["bloom.spread"] = spread
        grid.addWidget(spread, row, 0, 1, 2)
        row += 1
        
        # ✅ НОВОЕ Qt 6.10: Glow Strength
        glow_strength = LabeledSlider("Сила свечения (glowStrength)", 0.0, 2.0, 0.02, decimals=2)
        glow_strength.valueChanged.connect(lambda v: self._on_control_changed("bloom_glow_strength", v))
        self._controls["bloom.glow_strength"] = glow_strength
        grid.addWidget(glow_strength, row, 0, 1, 2)
        row += 1
        
        # ✅ ИСПРАВЛЕНО: Минимум 5.0 (должен быть > threshold), максимум 20.0 для HDR
        hdr_max = LabeledSlider("HDR Maximum (glowHDRMaximumValue)", 5.0, 20.0, 0.5, decimals=1)
        hdr_max.valueChanged.connect(lambda v: self._on_control_changed("bloom_hdr_max", v))
        self._controls["bloom.hdr_max"] = hdr_max
        grid.addWidget(hdr_max, row, 0, 1, 2)
        row += 1
        
        # ✅ НОВОЕ Qt 6.10: HDR Scale
        hdr_scale = LabeledSlider("HDR Scale (glowHDRScale)", 1.0, 5.0, 0.1, decimals=1)
        hdr_scale.valueChanged.connect(lambda v: self._on_control_changed("bloom_hdr_scale", v))
        self._controls["bloom.hdr_scale"] = hdr_scale
        grid.addWidget(hdr_scale, row, 0, 1, 2)
        row += 1
        
        # ✅ НОВОЕ Qt 6.10: Quality High checkbox
        quality_high = QCheckBox("Высокое качество (glowQualityHigh)", self)
        quality_high.clicked.connect(lambda checked: self._on_control_changed("bloom_quality_high", checked))
        self._controls["bloom.quality_high"] = quality_high
        grid.addWidget(quality_high, row, 0, 1, 2)
        row += 1
        
        # ✅ НОВОЕ Qt 6.10: Bicubic Upscale checkbox
        bicubic = QCheckBox("Бикубическое увеличение (glowUseBicubicUpscale)", self)
        bicubic.clicked.connect(lambda checked: self._on_control_changed("bloom_bicubic_upscale", checked))
        self._controls["bloom.bicubic_upscale"] = bicubic
        grid.addWidget(bicubic, row, 0, 1, 2)
        
        return group
    
    def _build_tonemap_group(self) -> QGroupBox:
        """Создать группу Тонемаппинг - МОНОЛИТ + расширенные параметры Qt 6.10"""
        group = QGroupBox("Тонемаппинг", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        row = 0
        
        # ✅ ИЗ МОНОЛИТА: Checkbox enabled
        enabled = QCheckBox("Включить тонемаппинг", self)
        enabled.clicked.connect(lambda checked: self._on_control_changed("tonemap_enabled", checked))
        self._controls["tonemap.enabled"] = enabled
        grid.addWidget(enabled, row, 0, 1, 2)
        row += 1

        # ✅ ИЗ МОНОЛИТА: Tonemap mode ComboBox
        combo = QComboBox(self)
        for label, value in [
            ("Filmic", "filmic"), 
            ("ACES", "aces"), 
            ("Reinhard", "reinhard"), 
            ("Gamma", "gamma"), 
            ("Linear", "linear")
        ]:
            combo.addItem(label, value)
        combo.currentIndexChanged.connect(lambda _: self._on_control_changed("tonemap_mode", combo.currentData()))
        self._controls["tonemap.mode"] = combo
        grid.addWidget(QLabel("Режим", self), row, 0)
        grid.addWidget(combo, row, 1)
        row += 1
        
        # ✅ НОВОЕ Qt 6.10: Exposure
        exposure = LabeledSlider("Экспозиция (tonemapExposure)", 0.1, 5.0, 0.05, decimals=2)
        exposure.valueChanged.connect(lambda v: self._on_control_changed("tonemap_exposure", v))
        self._controls["tonemap.exposure"] = exposure
        grid.addWidget(exposure, row, 0, 1, 2)
        row += 1
        
        # ✅ НОВОЕ Qt 6.10: White Point
        white_point = LabeledSlider("Белая точка (tonemapWhitePoint)", 0.5, 5.0, 0.1, decimals=1)
        white_point.valueChanged.connect(lambda v: self._on_control_changed("tonemap_white_point", v))
        self._controls["tonemap.white_point"] = white_point
        grid.addWidget(white_point, row, 0, 1, 2)

        return group
    
    def _build_dof_group(self) -> QGroupBox:
        """Создать группу Глубина резкости - ТОЧНО КАК В МОНОЛИТЕ"""
        group = QGroupBox("Depth of Field (Глубина резкости)", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        # Checkbox enabled
        enabled = QCheckBox("Включить DoF", self)
        enabled.clicked.connect(lambda checked: self._on_control_changed("depth_of_field", checked))
        self._controls["dof.enabled"] = enabled
        grid.addWidget(enabled, 0, 0, 1, 2)

        # Focus distance slider
        focus = LabeledSlider("Фокусное расстояние", 200.0, 20000.0, 50.0, decimals=0, unit="мм")
        focus.valueChanged.connect(lambda v: self._on_control_changed("dof_focus_distance", v))
        self._controls["dof.focus"] = focus
        grid.addWidget(focus, 1, 0, 1, 2)

        # Blur slider
        blur = LabeledSlider("Размытие", 0.0, 10.0, 0.1, decimals=2)
        blur.valueChanged.connect(lambda v: self._on_control_changed("dof_blur", v))
        self._controls["dof.blur"] = blur
        grid.addWidget(blur, 2, 0, 1, 2)

        return group
    
    def _build_misc_effects_group(self) -> QGroupBox:
        """Создать группу Дополнительные эффекты - МОНОЛИТ + расширенные параметры Qt 6.10"""
        group = QGroupBox("Дополнительные эффекты", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        row = 0
        
        # ========== MOTION BLUR (из монолита) ==========
        motion = QCheckBox("Размытие движения", self)
        motion.clicked.connect(lambda checked: self._on_control_changed("motion_blur", checked))
        self._controls["motion.enabled"] = motion
        grid.addWidget(motion, row, 0, 1, 2)
        row += 1

        motion_strength = LabeledSlider("Сила размытия", 0.0, 1.0, 0.02, decimals=2)
        motion_strength.valueChanged.connect(lambda v: self._on_control_changed("motion_blur_amount", v))
        self._controls["motion.amount"] = motion_strength
        grid.addWidget(motion_strength, row, 0, 1, 2)
        row += 1

        # ========== LENS FLARE (из монолита + расширенные) ==========
        lens_flare = QCheckBox("Линзовые блики", self)
        lens_flare.clicked.connect(lambda checked: self._on_control_changed("lens_flare", checked))
        self._controls["lens_flare.enabled"] = lens_flare
        grid.addWidget(lens_flare, row, 0, 1, 2)
        row += 1
        
        # ✅ НОВОЕ Qt 6.10: Lens Flare Ghost Count
        lf_ghost_count = LabeledSlider("Количество призраков", 1.0, 10.0, 1.0, decimals=0)
        lf_ghost_count.valueChanged.connect(lambda v: self._on_control_changed("lens_flare_ghost_count", int(v)))
        self._controls["lens_flare.ghost_count"] = lf_ghost_count
        grid.addWidget(lf_ghost_count, row, 0, 1, 2)
        row += 1
        
        # ✅ НОВОЕ Qt 6.10: Ghost Dispersal
        lf_dispersal = LabeledSlider("Распределение призраков", 0.0, 1.0, 0.01, decimals=2)
        lf_dispersal.valueChanged.connect(lambda v: self._on_control_changed("lens_flare_ghost_dispersal", v))
        self._controls["lens_flare.ghost_dispersal"] = lf_dispersal
        grid.addWidget(lf_dispersal, row, 0, 1, 2)
        row += 1
        
        # ✅ НОВОЕ Qt 6.10: Halo Width
        lf_halo = LabeledSlider("Ширина гало", 0.0, 1.0, 0.01, decimals=2)
        lf_halo.valueChanged.connect(lambda v: self._on_control_changed("lens_flare_halo_width", v))
        self._controls["lens_flare.halo_width"] = lf_halo
        grid.addWidget(lf_halo, row, 0, 1, 2)
        row += 1
        
        # ✅ НОВОЕ Qt 6.10: Bloom Bias
        lf_bloom_bias = LabeledSlider("Смещение bloom", 0.0, 1.0, 0.01, decimals=2)
        lf_bloom_bias.valueChanged.connect(lambda v: self._on_control_changed("lens_flare_bloom_bias", v))
        self._controls["lens_flare.bloom_bias"] = lf_bloom_bias
        grid.addWidget(lf_bloom_bias, row, 0, 1, 2)
        row += 1
        
        # ✅ НОВОЕ Qt 6.10: Stretch to Aspect checkbox
        lf_stretch = QCheckBox("Растяжение по пропорциям", self)
        lf_stretch.clicked.connect(lambda checked: self._on_control_changed("lens_flare_stretch_to_aspect", checked))
        self._controls["lens_flare.stretch"] = lf_stretch
        grid.addWidget(lf_stretch, row, 0, 1, 2)
        row += 1

        # ========== VIGNETTE (из монолита + расширенные) ==========
        vignette = QCheckBox("Виньетирование", self)
        vignette.clicked.connect(lambda checked: self._on_control_changed("vignette", checked))
        self._controls["vignette.enabled"] = vignette
        grid.addWidget(vignette, row, 0, 1, 2)
        row += 1

        vignette_strength = LabeledSlider("Сила виньетки", 0.0, 1.0, 0.02, decimals=2)
        vignette_strength.valueChanged.connect(lambda v: self._on_control_changed("vignette_strength", v))
        self._controls["vignette.strength"] = vignette_strength
        grid.addWidget(vignette_strength, row, 0, 1, 2)
        row += 1
        
        # ✅ НОВОЕ Qt 6.10: Vignette Radius
        vignette_radius = LabeledSlider("Радиус виньетки", 0.0, 1.0, 0.01, decimals=2)
        vignette_radius.valueChanged.connect(lambda v: self._on_control_changed("vignette_radius", v))
        self._controls["vignette.radius"] = vignette_radius
        grid.addWidget(vignette_radius, row, 0, 1, 2)
        
        return group
    
    def _build_color_adjustments_group(self) -> QGroupBox:
        """✅ НОВОЕ Qt 6.10: Color Adjustments группа"""
        group = QGroupBox("Цветокоррекция (Qt 6.10+)", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        
        row = 0
        
        # Brightness
        brightness = LabeledSlider("Яркость", -1.0, 1.0, 0.01, decimals=2)
        brightness.valueChanged.connect(lambda v: self._on_control_changed("adjustment_brightness", v))
        self._controls["color.brightness"] = brightness
        grid.addWidget(brightness, row, 0, 1, 2)
        row += 1
        
        # Contrast
        contrast = LabeledSlider("Контраст", -1.0, 1.0, 0.01, decimals=2)
        contrast.valueChanged.connect(lambda v: self._on_control_changed("adjustment_contrast", v))
        self._controls["color.contrast"] = contrast
        grid.addWidget(contrast, row, 0, 1, 2)
        row += 1
        
        # Saturation
        saturation = LabeledSlider("Насыщенность", -1.0, 1.0, 0.01, decimals=2)
        saturation.valueChanged.connect(lambda v: self._on_control_changed("adjustment_saturation", v))
        self._controls["color.saturation"] = saturation
        grid.addWidget(saturation, row, 0, 1, 2)
        
        return group
    
    def _on_control_changed(self, key: str, value: Any):
        """Обработчик изменения любого контрола - испускаем сигнал"""
        # Собираем полное состояние
        state = self.get_state()
        self.effects_changed.emit(state)
    
    def get_state(self) -> Dict[str, Any]:
        """Получить текущее состояние всех параметров эффектов
        
        Returns:
            Словарь с параметрами - МОНОЛИТ + расширенные Qt 6.10
        """
        return {
            # ========== BLOOM (монолит + расширенные) ==========
            'bloom_enabled': self._controls["bloom.enabled"].isChecked(),
            'bloom_intensity': self._controls["bloom.intensity"].value(),
            'bloom_threshold': self._controls["bloom.threshold"].value(),
            'bloom_spread': self._controls["bloom.spread"].value(),
            # Qt 6.10 расширенные
            'bloom_glow_strength': self._controls["bloom.glow_strength"].value(),
            'bloom_hdr_max': self._controls["bloom.hdr_max"].value(),
            'bloom_hdr_scale': self._controls["bloom.hdr_scale"].value(),
            'bloom_quality_high': self._controls["bloom.quality_high"].isChecked(),
            'bloom_bicubic_upscale': self._controls["bloom.bicubic_upscale"].isChecked(),
            
            # ========== TONEMAP (монолит + расширенные) ==========
            'tonemap_enabled': self._controls["tonemap.enabled"].isChecked(),
            'tonemap_mode': self._controls["tonemap.mode"].currentData(),
            # Qt 6.10 расширенные
            'tonemap_exposure': self._controls["tonemap.exposure"].value(),
            'tonemap_white_point': self._controls["tonemap.white_point"].value(),
            
            # ========== DOF (монолит без изменений) ==========
            'depth_of_field': self._controls["dof.enabled"].isChecked(),
            'dof_focus_distance': self._controls["dof.focus"].value(),
            'dof_blur': self._controls["dof.blur"].value(),
            
            # ========== MISC EFFECTS ==========
            # Motion Blur (монолит)
            'motion_blur': self._controls["motion.enabled"].isChecked(),
            'motion_blur_amount': self._controls["motion.amount"].value(),
            
            # Lens Flare (монолит + расширенные Qt 6.10)
            'lens_flare': self._controls["lens_flare.enabled"].isChecked(),
            'lens_flare_ghost_count': int(self._controls["lens_flare.ghost_count"].value()),
            'lens_flare_ghost_dispersal': self._controls["lens_flare.ghost_dispersal"].value(),
            'lens_flare_halo_width': self._controls["lens_flare.halo_width"].value(),
            'lens_flare_bloom_bias': self._controls["lens_flare.bloom_bias"].value(),
            'lens_flare_stretch_to_aspect': self._controls["lens_flare.stretch"].isChecked(),
            
            # Vignette (монолит + расширенные Qt 6.10)
            'vignette': self._controls["vignette.enabled"].isChecked(),
            'vignette_strength': self._controls["vignette.strength"].value(),
            'vignette_radius': self._controls["vignette.radius"].value(),
            
            # ========== COLOR ADJUSTMENTS (Qt 6.10+) ==========
            'adjustment_brightness': self._controls["color.brightness"].value(),
            'adjustment_contrast': self._controls["color.contrast"].value(),
            'adjustment_saturation': self._controls["color.saturation"].value(),
        }
    
    def set_state(self, state: Dict[str, Any]):
        """Установить состояние из словаря
        
        Args:
            state: Словарь с параметрами эффектов
        """
        # Временно блокируем сигналы чтобы избежать множественных emit
        for control in self._controls.values():
            control.blockSignals(True)
        
        try:
            # ========== BLOOM ==========
            if 'bloom_enabled' in state:
                self._controls["bloom.enabled"].setChecked(state['bloom_enabled'])
            if 'bloom_intensity' in state:
                self._controls["bloom.intensity"].set_value(state['bloom_intensity'])
            if 'bloom_threshold' in state:
                self._controls["bloom.threshold"].set_value(state['bloom_threshold'])
            if 'bloom_spread' in state:
                self._controls["bloom.spread"].set_value(state['bloom_spread'])
            # Qt 6.10 расширенные
            if 'bloom_glow_strength' in state:
                self._controls["bloom.glow_strength"].set_value(state['bloom_glow_strength'])
            if 'bloom_hdr_max' in state:
                self._controls["bloom.hdr_max"].set_value(state['bloom_hdr_max'])
            if 'bloom_hdr_scale' in state:
                self._controls["bloom.hdr_scale"].set_value(state['bloom_hdr_scale'])
            if 'bloom_quality_high' in state:
                self._controls["bloom.quality_high"].setChecked(state['bloom_quality_high'])
            if 'bloom_bicubic_upscale' in state:
                self._controls["bloom.bicubic_upscale"].setChecked(state['bloom_bicubic_upscale'])
            
            # ========== TONEMAP ==========
            if 'tonemap_enabled' in state:
                self._controls["tonemap.enabled"].setChecked(state['tonemap_enabled'])
            if 'tonemap_mode' in state:
                combo = self._controls["tonemap.mode"]
                index = combo.findData(state['tonemap_mode'])
                if index >= 0:
                    combo.setCurrentIndex(index)
            # Qt 6.10 расширенные
            if 'tonemap_exposure' in state:
                self._controls["tonemap.exposure"].set_value(state['tonemap_exposure'])
            if 'tonemap_white_point' in state:
                self._controls["tonemap.white_point"].set_value(state['tonemap_white_point'])
            
            # ========== DOF ==========
            if 'depth_of_field' in state:
                self._controls["dof.enabled"].setChecked(state['depth_of_field'])
            if 'dof_focus_distance' in state:
                self._controls["dof.focus"].set_value(state['dof_focus_distance'])
            if 'dof_blur' in state:
                self._controls["dof.blur"].set_value(state['dof_blur'])
            
            # ========== MISC EFFECTS ==========
            # Motion Blur
            if 'motion_blur' in state:
                self._controls["motion.enabled"].setChecked(state['motion_blur'])
            if 'motion_blur_amount' in state:
                self._controls["motion.amount"].set_value(state['motion_blur_amount'])
            
            # Lens Flare
            if 'lens_flare' in state:
                self._controls["lens_flare.enabled"].setChecked(state['lens_flare'])
            if 'lens_flare_ghost_count' in state:
                self._controls["lens_flare.ghost_count"].set_value(float(state['lens_flare_ghost_count']))
            if 'lens_flare_ghost_dispersal' in state:
                self._controls["lens_flare.ghost_dispersal"].set_value(state['lens_flare_ghost_dispersal'])
            if 'lens_flare_halo_width' in state:
                self._controls["lens_flare.halo_width"].set_value(state['lens_flare_halo_width'])
            if 'lens_flare_bloom_bias' in state:
                self._controls["lens_flare.bloom_bias"].set_value(state['lens_flare_bloom_bias'])
            if 'lens_flare_stretch_to_aspect' in state:
                self._controls["lens_flare.stretch"].setChecked(state['lens_flare_stretch_to_aspect'])
            
            # Vignette
            if 'vignette' in state:
                self._controls["vignette.enabled"].setChecked(state['vignette'])
            if 'vignette_strength' in state:
                self._controls["vignette.strength"].set_value(state['vignette_strength'])
            if 'vignette_radius' in state:
                self._controls["vignette.radius"].set_value(state['vignette_radius'])
            
            # ========== COLOR ADJUSTMENTS ==========
            if 'adjustment_brightness' in state:
                self._controls["color.brightness"].set_value(state['adjustment_brightness'])
            if 'adjustment_contrast' in state:
                self._controls["color.contrast"].set_value(state['adjustment_contrast'])
            if 'adjustment_saturation' in state:
                self._controls["color.saturation"].set_value(state['adjustment_saturation'])
        
        finally:
            # Разблокируем сигналы
            for control in self._controls.values():
                control.blockSignals(False)
