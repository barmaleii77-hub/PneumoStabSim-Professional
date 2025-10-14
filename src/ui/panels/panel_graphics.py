"""Graphics panel providing exhaustive Qt Quick 3D controls."""
from __future__ import annotations

import copy
import json
import logging
from typing import Any, Dict
from pathlib import Path

from PySide6.QtCore import QSettings, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QStandardItem
from PySide6 import QtWidgets  # ✅ ДОБАВЛЕНО: модуль QtWidgets для безопасного доступа к QSlider
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

# Импортируем логгер графических изменений
from .graphics_logger import get_graphics_logger

# ✅ НОВОЕ: Импорт EventLogger для отслеживания UI событий
from src.common.event_logger import get_event_logger, EventType


class ColorButton(QPushButton):
    """Small color preview button that streams changes from QColorDialog."""

    color_changed = Signal(str)

    def __init__(self, initial_color: str = "#ffffff", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(42, 28)
        self._color = QColor(initial_color)
        self._dialog = None
        self._user_triggered = False  # ✅ НОВОЕ: флаг пользовательского действия
        self._update_swatch()
        self.clicked.connect(self._open_dialog)

    def color(self) -> QColor:
        return self._color

    def set_color(self, color_str: str) -> None:
        """Программное изменение цвета (без логирования)"""
        self._color = QColor(color_str)
        self._update_swatch()

    def _update_swatch(self) -> None:
        self.setStyleSheet(
            "QPushButton {"
            f"background-color: {self._color.name()};"
            "border: 2px solid #5c5c5c;"
            "border-radius: 4px;"
            "}"
            "QPushButton:hover { border: 2px solid #9a9a9a; }"
        )

    @Slot()
    def _open_dialog(self) -> None:
        # ✅ Пользователь кликнул на кнопку - это пользовательское действие
        self._user_triggered = True
        
        if self._dialog:
            return

        dialog = QColorDialog(self._color, self)
        dialog.setOption(QColorDialog.DontUseNativeDialog, True)
        dialog.setOption(QColorDialog.ShowAlphaChannel, False)
        dialog.currentColorChanged.connect(self._on_color_changed)
        dialog.colorSelected.connect(self._on_color_changed)
        dialog.finished.connect(self._close_dialog)
        dialog.open()
        self._dialog = dialog

    @Slot(QColor)
    def _on_color_changed(self, color: QColor) -> None:
        if not color.isValid():
            return
        self._color = color
        self._update_swatch()
        
        # ✅ Испускаем сигнал ТОЛЬКО если это пользовательское действие
        if self._user_triggered:
            self.color_changed.emit(color.name())

    @Slot()
    def _close_dialog(self) -> None:
        if self._dialog:
            self._dialog.deleteLater()
        self._dialog = None
        self._user_triggered = False  # ✅ Сбрасываем флаг


class LabeledSlider(QWidget):
    """Slider + spin box pair with labelled feedback."""

    valueChanged = Signal(float)

    def __init__(
        self,
        title: str,
        minimum: float,
        maximum: float,
        step: float,
        *,
        decimals: int = 2,
        unit: str | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._title = title
        self._min = minimum
        self._max = maximum
        self._step = step
        self._decimals = decimals
        self._unit = unit or ""
        self._updating = False
        self._user_triggered = False  # ✅ НОВОЕ: флаг пользовательского действия

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._label = QLabel(self)
        layout.addWidget(self._label)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        layout.addLayout(row)

        # ✅ ИСПРАВЛЕНО: используем QtWidgets.QSlider, чтобы избежать NameError
        self._slider = QtWidgets.QSlider(Qt.Horizontal, self)
        steps = max(1, int(round((self._max - self._min) / self._step)))
        self._slider.setRange(0, steps)
        
        # ✅ КРИТИЧЕСКОЕ: Отслеживаем НАЧАЛО и КОНЕЦ пользовательского взаимодействия
        self._slider.sliderPressed.connect(self._on_slider_pressed)
        self._slider.sliderReleased.connect(self._on_slider_released)
        self._slider.valueChanged.connect(self._handle_slider)
        row.addWidget(self._slider, 1)

        self._spin = QDoubleSpinBox(self)
        self._spin.setDecimals(self._decimals)
        self._spin.setRange(self._min, self._max)
        self._spin.setSingleStep(self._step)
        
        # ✅ КРИТИЧЕСКОЕ: Отслеживаем фокус SpinBox (пользователь редактирует вручную)
        self._spin.installEventFilter(self)
        self._spin.valueChanged.connect(self._handle_spin)
        row.addWidget(self._spin)

        self.set_value(self._min)

    def eventFilter(self, obj, event) -> bool:
        """Отслеживаем фокус SpinBox для определения пользовательского ввода"""
        if obj == self._spin:
            if event.type() == event.Type.FocusIn:
                self._user_triggered = True
            elif event.type() == event.Type.FocusOut:
                self._user_triggered = False
        return super().eventFilter(obj, event)

    @Slot()
    def _on_slider_pressed(self) -> None:
        """Пользователь начал перетаскивать слайдер"""
        self._user_triggered = True

    @Slot()
    def _on_slider_released(self) -> None:
        """Пользователь отпустил слайдер"""
        self._user_triggered = False

    def set_enabled(self, enabled: bool) -> None:
        self.setEnabled(enabled)

    def value(self) -> float:
        return round(self._spin.value(), self._decimals)

    def set_value(self, value: float) -> None:
        """Программное изменение значения (без логирования)"""
        value = max(self._min, min(self._max, value))
        slider_value = int(round((value - self._min) / self._step))
        self._updating = True
        self._slider.setValue(slider_value)
        self._spin.setValue(value)
        self._update_label(value)
        self._updating = False

    def _update_label(self, value: float) -> None:
        formatted = f"{value:.{self._decimals}f}"
        if self._unit:
            formatted = f"{formatted} {self._unit}"
        self._label.setText(f"{self._title}: {formatted}")

    @Slot(int)
    def _handle_slider(self, slider_value: int) -> None:
        if self._updating:
            return
        value = self._min + slider_value * self._step
        value = max(self._min, min(self._max, value))
        self._updating = True
        self._spin.setValue(value)
        self._update_label(value)
        self._updating = False
        
        # ✅ Испускаем сигнал ТОЛЬКО если пользователь двигает слайдер
        if self._user_triggered:
            self.valueChanged.emit(round(value, self._decimals))

    @Slot(float)
    def _handle_spin(self, value: float) -> None:
        if self._updating:
            return
        slider_value = int(round((value - self._min) / self._step))
        self._updating = True
        self._slider.setValue(slider_value)
        self._update_label(value)
        self._updating = False
        
        # ✅ Испускаем сигнал ТОЛЬКО если пользователь редактирует SpinBox
        if self._user_triggered:
            self.valueChanged.emit(round(value, self._decimals))


class GraphicsPanel(QWidget):
    """Comprehensive graphics configuration panel for PneumoStabSim."""

    lighting_changed = Signal(dict)
    environment_changed = Signal(dict)
    material_changed = Signal(dict)
    quality_changed = Signal(dict)
    camera_changed = Signal(dict)
    effects_changed = Signal(dict)
    preset_applied = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        # ✅ CRITICAL FIX: Always pass parent to super().__init__(), even if None
        # Qt requires parent argument (None is valid) to properly initialize QWidget
        super().__init__(parent)
            
        self.logger = logging.getLogger(__name__)
        self.settings = QSettings("PneumoStabSim", "GraphicsPanel")
        self._updating_ui = False

        # Инициализируем логгер графических изменений
        self.graphics_logger = get_graphics_logger()
        self.logger.info("📊 Graphics logger initialized")
        
        # ✅ НОВОЕ: Инициализируем event logger для UI событий
        self.event_logger = get_event_logger()
        self.logger.info("🔗 Event logger initialized")

        self._defaults = self._build_defaults()
        self.state: Dict[str, Any] = copy.deepcopy(self._defaults)

        self._quality_presets = self._build_quality_presets()
        self._quality_preset_labels = {
            "ultra": "Ультра",
            "high": "Высокое",
            "medium": "Среднее",
            "low": "Низкое",
            "custom": "Пользовательский",
        }
        self._quality_preset_order = ["ultra", "high", "medium", "low", "custom"]
        self._suspend_preset_sync = False

        for material_key in list(self.state["materials"].keys()):
            self._ensure_material_defaults(material_key)

        self._create_ui()
        self.load_settings()
        self._apply_quality_constraints()
        self._apply_state_to_ui()

        QTimer.singleShot(0, self._emit_all)

    # ------------------------------------------------------------------
    # Defaults
    # ------------------------------------------------------------------
    def _build_defaults(self) -> Dict[str, Any]:
        return {
            "lighting": {
                # Добавлены: cast_shadow, bind_to_camera, position_x/position_y для каждого источника
                "key": {
                    "brightness": 1.2,
                    "color": "#ffffff",
                    "angle_x": -35.0,
                    "angle_y": -40.0,
                    "cast_shadow": True,
                    "bind_to_camera": False,
                    "position_x": 0.0,
                    "position_y": 0.0,
                },
                "fill": {
                    "brightness": 0.7,
                    "color": "#dfe7ff",
                    "cast_shadow": False,
                    "bind_to_camera": False,
                    "position_x": 0.0,
                    "position_y": 0.0,
                },
                "rim": {
                    "brightness": 1.0,
                    "color": "#ffe2b0",
                    "cast_shadow": False,
                    "bind_to_camera": False,
                    "position_x": 0.0,
                    "position_y": 0.0,
                },
                "point": {
                    "brightness": 1000.0,
                    "color": "#ffffff",
                    "position_x": 0.0,
                    "position_y": 2200.0,
                    "range": 3200.0,
                    "cast_shadow": False,
                    "bind_to_camera": False,
                },
            },
            "environment": {
                "background_mode": "skybox",  # 'color' | 'skybox'
                "background_color": "#1f242c",
                "ibl_enabled": True,
                "ibl_intensity": 1.3,
                "ibl_source": "../hdr/studio.hdr",
                "ibl_fallback": "../hdr/studio_small_09_2k.hdr",  # ✅ ИСПРАВЛЕНО: корректный относительный путь
                "skybox_blur": 0.08,
                "fog_enabled": True,
                "fog_color": "#b0c4d8",
                "fog_density": 0.12,
                "fog_near": 1200.0,
                "fog_far": 12000.0,
                "ao_enabled": True,
                "ao_strength": 1.0,
                "ao_radius": 8.0,
            },
            "quality": {
                "preset": "ultra",
                "shadows": {
                    "enabled": True,
                    "resolution": "4096",
                    "filter": 32,
                    "bias": 8.0,
                    "darkness": 80.0,
                },
                "antialiasing": {"primary": "ssaa", "quality": "high", "post": "taa"},
                "taa_enabled": True,
                "taa_strength": 0.4,
                "taa_motion_adaptive": True,
                "fxaa_enabled": False,
                "specular_aa": True,
                "dithering": True,
                "render_scale": 1.05,
                "render_policy": "always",
                "frame_rate_limit": 144.0,
                "oit": "weighted",
            },
            "camera": {
                "fov": 60.0,
                "near": 10.0,
                "far": 50000.0,
                "speed": 1.0,
                "auto_rotate": False,
                "auto_rotate_speed": 1.0,
            },
            "effects": {
                "bloom_enabled": True,
                "bloom_intensity": 0.5,
                "bloom_threshold": 1.0,
                "bloom_spread": 0.65,
                "ssao_enabled": True,
                "ssao_strength": 1.0,
                "ssao_radius": 8.0,
                "depth_of_field": False,
                "dof_focus_distance": 2200.0,
                "dof_blur": 4.0,
                "motion_blur": False,
                "motion_blur_amount": 0.2,
                "lens_flare": False,   # ✅ По умолчанию выкл
                "vignette": False,     # ✅ По умолчанию выкл
                "vignette_strength": 0.35,
                "tonemap_enabled": True,
                "tonemap_mode": "filmic",
            },
            "materials": {
                "frame": {
                    "base_color": "#c53030",
                    "metalness": 0.85,
                    "roughness": 0.35,
                    "specular": 1.0,
                    "specular_tint": 0.0,
                    "clearcoat": 0.22,
                    "clearcoat_roughness": 0.1,
                    "transmission": 0.0,
                    "opacity": 1.0,
                    "ior": 1.5,
                    "attenuation_distance": 10000.0,
                    "attenuation_color": "#ffffff",
                    "emissive_color": "#000000",
                    "emissive_intensity": 0.0,
                    "warning_color": "#ff5454",
                    "ok_color": "#00ff55",
                    "error_color": "#ff2a2a",
                },
                "lever": {
                    "base_color": "#9ea4ab",
                    "metalness": 1.0,
                    "roughness": 0.28,
                    "specular": 1.0,
                    "specular_tint": 0.0,
                    "clearcoat": 0.3,
                    "clearcoat_roughness": 0.08,
                    "transmission": 0.0,
                    "opacity": 1.0,
                    "ior": 1.5,
                    "attenuation_distance": 10000.0,
                    "attenuation_color": "#ffffff",
                    "emissive_color": "#000000",
                    "emissive_intensity": 0.0,
                    "warning_color": "#ff5454",
                    "ok_color": "#00ff55",
                    "error_color": "#ff2a2a",
                },
                "tail": {
                    "base_color": "#d5d9df",
                    "metalness": 1.0,
                    "roughness": 0.3,
                    "specular": 1.0,
                    "specular_tint": 0.0,
                    "clearcoat": 0.0,
                    "clearcoat_roughness": 0.0,
                    "transmission": 0.0,
                    "opacity": 1.0,
                    "ior": 1.5,
                    "attenuation_distance": 10000.0,
                    "attenuation_color": "#ffffff",
                    "emissive_color": "#000000",
                    "emissive_intensity": 0.0,
                    "warning_color": "#ffd24d",
                    "ok_color": "#00ff55",
                    "error_color": "#ff2a2a",
                },
                "cylinder": {
                    "base_color": "#e1f5ff",
                    "metalness": 0.0,
                    "roughness": 0.05,
                    "specular": 1.0,
                    "specular_tint": 0.0,
                    "clearcoat": 0.0,
                    "clearcoat_roughness": 0.0,
                    "transmission": 1.0,
                    "opacity": 1.0,
                    "ior": 1.52,
                    "attenuation_distance": 1800.0,
                    "attenuation_color": "#b7e7ff",
                    "emissive_color": "#000000",
                    "emissive_intensity": 0.0,
                    "warning_color": "#ff7070",
                    "ok_color": "#7dffd6",
                    "error_color": "#ff2a2a",
                },
                "piston_body": {
                    "base_color": "#ff3c6e",
                    "metalness": 1.0,
                    "roughness": 0.26,
                    "specular": 1.0,
                    "specular_tint": 0.0,
                    "clearcoat": 0.18,
                    "clearcoat_roughness": 0.06,
                    "transmission": 0.0,
                    "opacity": 1.0,
                    "ior": 1.5,
                    "attenuation_distance": 10000.0,
                    "attenuation_color": "#ffffff",
                    "emissive_color": "#000000",
                    "emissive_intensity": 0.0,
                    "warning_color": "#ff5454",
                    "ok_color": "#00ff55",
                    "error_color": "#ff2a2a",
                },
                "piston_rod": {
                    "base_color": "#ececec",
                    "metalness": 1.0,
                    "roughness": 0.18,
                    "specular": 1.0,
                    "specular_tint": 0.0,
                    "clearcoat": 0.12,
                    "clearcoat_roughness": 0.05,
                    "transmission": 0.0,
                    "opacity": 1.0,
                    "ior": 1.5,
                    "attenuation_distance": 10000.0,
                    "attenuation_color": "#ffffff",
                    "emissive_color": "#000000",
                    "emissive_intensity": 0.0,
                    "warning_color": "#ff5454",
                    "ok_color": "#00ff55",
                    "error_color": "#ff2a2a",
                },
                "joint_tail": {
                    "base_color": "#2a82ff",
                    "metalness": 0.9,
                    "roughness": 0.35,
                    "specular": 1.0,
                    "specular_tint": 0.0,
                    "clearcoat": 0.1,
                    "clearcoat_roughness": 0.08,
                    "transmission": 0.0,
                    "opacity": 1.0,
                    "ior": 1.5,
                    "attenuation_distance": 10000.0,
                    "attenuation_color": "#ffffff",
                    "emissive_color": "#000000",
                    "emissive_intensity": 0.0,
                    "warning_color": "#ffd24d",
                    "ok_color": "#00ff55",
                    "error_color": "#ff0000",
                },
                "joint_arm": {
                    "base_color": "#ff9c3a",
                    "metalness": 0.9,
                    "roughness": 0.32,
                    "specular": 1.0,
                    "specular_tint": 0.0,
                    "clearcoat": 0.12,
                    "clearcoat_roughness": 0.08,
                    "transmission": 0.0,
                    "opacity": 1.0,
                    "ior": 1.5,
                    "attenuation_distance": 10000.0,
                    "attenuation_color": "#ffffff",
                    "emissive_color": "#000000",
                    "emissive_intensity": 0.0,
                    "warning_color": "#ffd24d",
                    "ok_color": "#00ff55",
                    "error_color": "#ff2a2a",
                },
            },
        }

    def _build_quality_presets(self) -> Dict[str, Dict[str, Any]]:
        return {
            "ultra": {
                "shadows": {"enabled": True, "resolution": "4096", "filter": 32, "bias": 8.0, "darkness": 80.0},
                "antialiasing": {"primary": "ssaa", "quality": "high", "post": "taa"},
                "taa_enabled": True,
                "taa_strength": 0.4,
                "fxaa_enabled": False,
                "specular_aa": True,
                "dithering": True,
                "render_scale": 1.05,
                "render_policy": "always",
                "frame_rate_limit": 144.0,
                "oit": "weighted",
            },
            "high": {
                "shadows": {"enabled": True, "resolution": "2048", "filter": 16, "bias": 9.5, "darkness": 78.0},
                "antialiasing": {"primary": "msaa", "quality": "high", "post": "off"},
                "taa_enabled": False,
                "taa_strength": 0.3,
                "taa_motion_adaptive": True,
                "fxaa_enabled": False,
                "specular_aa": True,
                "dithering": True,
                "render_scale": 1.0,
                "render_policy": "always",
                "frame_rate_limit": 120.0,
                "oit": "weighted",
            },
            "medium": {
                "shadows": {"enabled": True, "resolution": "1024", "filter": 8, "bias": 10.0, "darkness": 75.0},
                "antialiasing": {"primary": "msaa", "quality": "medium", "post": "fxaa"},
                "taa_enabled": False,
                "taa_strength": 0.25,
                "taa_motion_adaptive": True,
                "fxaa_enabled": True,
                "specular_aa": True,
                "dithering": True,
                "render_scale": 0.9,
                "render_policy": "always",
                "frame_rate_limit": 90.0,
                "oit": "weighted",
            },
            "low": {
                "shadows": {"enabled": True, "resolution": "512", "filter": 4, "bias": 12.0, "darkness": 70.0},
                "antialiasing": {"primary": "off", "quality": "low", "post": "fxaa"},
                "taa_enabled": False,
                "taa_strength": 0.2,
                "taa_motion_adaptive": True,
                "fxaa_enabled": True,
                "specular_aa": False,
                "dithering": True,
                "render_scale": 0.8,
                "render_policy": "ondemand",
                "frame_rate_limit": 60.0,
                "oit": "none",
            },
        }
    # ------------------------------------------------------------------
    # UI creation
    # ------------------------------------------------------------------
    def _create_ui(self) -> None:
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(8, 8, 8, 8)
        main_layout.setSpacing(8)

        scroll = QScrollArea(self)
        scroll.setWidgetResizable(True)
        main_layout.addWidget(scroll, 1)

        container = QWidget()
        scroll.setWidget(container)
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(8)

        self._tabs = QTabWidget(container)
        container_layout.addWidget(self._tabs)

        self._lighting_controls: Dict[str, Any] = {}
        self._environment_controls: Dict[str, Any] = {}
        self._quality_controls: Dict[str, Any] = {}
        self._camera_controls: Dict[str, Any] = {}
        self._effects_controls: Dict[str, Any] = {}
        self._material_controls: Dict[str, Any] = {}
        self._material_rows: Dict[str, QWidget] = {}

        self._tabs.addTab(self._build_lighting_tab(), "Освещение")
        self._tabs.addTab(self._build_environment_tab(), "Окружение")
        self._tabs.addTab(self._build_quality_tab(), "Качество")
        self._tabs.addTab(self._build_camera_tab(), "Камера")
        self._tabs.addTab(self._build_materials_tab(), "Материалы")
        self._tabs.addTab(self._build_effects_tab(), "Эффекты")

        button_row = QHBoxLayout()
        button_row.setContentsMargins(0, 0, 0, 0)
        button_row.setSpacing(8)
        button_row.addStretch(1)

        reset_btn = QPushButton("↩︎ Сброс", self)
        reset_btn.clicked.connect(self.reset_to_defaults)
        button_row.addWidget(reset_btn)

        main_layout.addLayout(button_row)

    # --- Lighting -----------------------------------------------------
    def _build_lighting_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(self._build_key_light_group())
        layout.addWidget(self._build_fill_light_group())
        layout.addWidget(self._build_rim_light_group())
        layout.addWidget(self._build_point_light_group())
        layout.addWidget(self._build_lighting_preset_group())
        layout.addStretch(1)
        return tab

    def _build_key_light_group(self) -> QGroupBox:
        group = QGroupBox("Ключевой свет", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        brightness = LabeledSlider("Яркость", 0.0, 10.0, 0.05, decimals=2)
        brightness.valueChanged.connect(lambda v: self._update_lighting("key", "brightness", v))
        self._lighting_controls["key.brightness"] = brightness
        grid.addWidget(brightness, 0, 0, 1, 2)

        color_row = QHBoxLayout()
        color_row.setContentsMargins(0, 0, 0, 0)
        color_row.setSpacing(6)
        color_row.addWidget(QLabel("Цвет", self))
        color_button = ColorButton()
        color_button.color_changed.connect(lambda c: self._update_lighting("key", "color", c))
        self._lighting_controls["key.color"] = color_button
        color_row.addWidget(color_button)
        color_row.addStretch(1)
        grid.addLayout(color_row, 1, 0, 1, 2)

        angle_x = LabeledSlider("Наклон X", -90.0, 90.0, 1.0, decimals=1, unit="°")
        angle_x.valueChanged.connect(lambda v: self._update_lighting("key", "angle_x", v))
        self._lighting_controls["key.angle_x"] = angle_x
        grid.addWidget(angle_x, 2, 0, 1, 2)

        angle_y = LabeledSlider("Поворот Y", -180.0, 180.0, 1.0, decimals=1, unit="°")
        angle_y.valueChanged.connect(lambda v: self._update_lighting("key", "angle_y", v))
        self._lighting_controls["key.angle_y"] = angle_y
        grid.addWidget(angle_y, 3, 0, 1, 2)
+
+        # Позиция X/Y и флаги
+        posx = LabeledSlider("Позиция X", -5000.0, 5000.0, 10.0, decimals=0, unit="мм")
+        posx.valueChanged.connect(lambda v: self._update_lighting("key", "position_x", v))
+        self._lighting_controls["key.position_x"] = posx
+        grid.addWidget(posx, 4, 0, 1, 2)
+
+        posy = LabeledSlider("Позиция Y", -5000.0, 5000.0, 10.0, decimals=0, unit="мм")
+        posy.valueChanged.connect(lambda v: self._update_lighting("key", "position_y", v))
+        self._lighting_controls["key.position_y"] = posy
+        grid.addWidget(posy, 5, 0, 1, 2)
+
+        key_shadow = QCheckBox("Тени от ключевого света", self)
+        key_shadow.clicked.connect(lambda checked: self._update_lighting("key", "cast_shadow", checked))
+        self._lighting_controls["key.cast_shadow"] = key_shadow
+        grid.addWidget(key_shadow, 6, 0, 1, 2)
+
+        key_bind = QCheckBox("Привязать к камере", self)
+        key_bind.clicked.connect(lambda checked: self._update_lighting("key", "bind_to_camera", checked))
+        self._lighting_controls["key.bind"] = key_bind
+        grid.addWidget(key_bind, 7, 0, 1, 2)
         return group

    def _build_fill_light_group(self) -> QGroupBox:
        group = QGroupBox("Заполняющий свет", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        brightness = LabeledSlider("Яркость", 0.0, 5.0, 0.05, decimals=2)
        brightness.valueChanged.connect(lambda v: self._update_lighting("fill", "brightness", v))
        self._lighting_controls["fill.brightness"] = brightness
        grid.addWidget(brightness, 0, 0, 1, 2)

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Цвет", self))
        color_button = ColorButton()
        color_button.color_changed.connect(lambda c: self._update_lighting("fill", "color", c))
        self._lighting_controls["fill.color"] = color_button
        color_row.addWidget(color_button)
        color_row.addStretch(1)
        grid.addLayout(color_row, 1, 0, 1, 2)
+
+        # Позиция X/Y и флаги
+        posx = LabeledSlider("Позиция X", -5000.0, 5000.0, 10.0, decimals=0, unit="мм")
+        posx.valueChanged.connect(lambda v: self._update_lighting("fill", "position_x", v))
+        self._lighting_controls["fill.position_x"] = posx
+        grid.addWidget(posx, 2, 0, 1, 2)
+
+        posy = LabeledSlider("Позиция Y", -5000.0, 5000.0, 10.0, decimals=0, unit="мм")
+        posy.valueChanged.connect(lambda v: self._update_lighting("fill", "position_y", v))
+        self._lighting_controls["fill.position_y"] = posy
+        grid.addWidget(posy, 3, 0, 1, 2)
+
+        fill_shadow = QCheckBox("Тени от заполняющего света", self)
+        fill_shadow.clicked.connect(lambda checked: self._update_lighting("fill", "cast_shadow", checked))
+        self._lighting_controls["fill.cast_shadow"] = fill_shadow
+        grid.addWidget(fill_shadow, 4, 0, 1, 2)
+
+        fill_bind = QCheckBox("Привязать к камере", self)
+        fill_bind.clicked.connect(lambda checked: self._update_lighting("fill", "bind_to_camera", checked))
+        self._lighting_controls["fill.bind"] = fill_bind
+        grid.addWidget(fill_bind, 5, 0, 1, 2)
         return group

    def _build_rim_light_group(self) -> QGroupBox:
        group = QGroupBox("Контровой свет", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        brightness = LabeledSlider("Яркость", 0.0, 5.0, 0.05, decimals=2)
        brightness.valueChanged.connect(lambda v: self._update_lighting("rim", "brightness", v))
        self._lighting_controls["rim.brightness"] = brightness
        grid.addWidget(brightness, 0, 0, 1, 2)

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Цвет", self))
        color_button = ColorButton()
        color_button.color_changed.connect(lambda c: self._update_lighting("rim", "color", c))
        self._lighting_controls["rim.color"] = color_button
        color_row.addWidget(color_button)
        color_row.addStretch(1)
        grid.addLayout(color_row, 1, 0, 1, 2)
+
+        # Позиция X/Y и флаги
+        posx = LabeledSlider("Позиция X", -5000.0, 5000.0, 10.0, decimals=0, unit="мм")
+        posx.valueChanged.connect(lambda v: self._update_lighting("rim", "position_x", v))
+        self._lighting_controls["rim.position_x"] = posx
+        grid.addWidget(posx, 2, 0, 1, 2)
+
+        posy = LabeledSlider("Позиция Y", -5000.0, 5000.0, 10.0, decimals=0, unit="мм")
+        posy.valueChanged.connect(lambda v: self._update_lighting("rim", "position_y", v))
+        self._lighting_controls["rim.position_y"] = posy
+        grid.addWidget(posy, 3, 0, 1, 2)
+
+        rim_shadow = QCheckBox("Тени от контрового света", self)
+        rim_shadow.clicked.connect(lambda checked: self._update_lighting("rim", "cast_shadow", checked))
+        self._lighting_controls["rim.cast_shadow"] = rim_shadow
+        grid.addWidget(rim_shadow, 4, 0, 1, 2)
+
+        rim_bind = QCheckBox("Привязать к камере", self)
+        rim_bind.clicked.connect(lambda checked: self._update_lighting("rim", "bind_to_camera", checked))
+        self._lighting_controls["rim.bind"] = rim_bind
+        grid.addWidget(rim_bind, 5, 0, 1, 2)
         return group

    def _build_point_light_group(self) -> QGroupBox:
        group = QGroupBox("Точечный свет", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        intensity = LabeledSlider("Интенсивность", 0.0, 100000.0, 50.0, decimals=1)
        intensity.valueChanged.connect(lambda v: self._update_lighting("point", "brightness", v))
        self._lighting_controls["point.brightness"] = intensity
        grid.addWidget(intensity, 0, 0, 1, 2)

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Цвет", self))
        color_button = ColorButton()
        color_button.color_changed.connect(lambda c: self._update_lighting("point", "color", c))
        self._lighting_controls["point.color"] = color_button
        color_row.addWidget(color_button)
        color_row.addStretch(1)
        grid.addLayout(color_row, 1, 0, 1, 2)
 
-        height_slider = LabeledSlider("Высота", 0.0, 5000.0, 10.0, decimals=1, unit="мм")
-        height_slider.valueChanged.connect(lambda v: self._update_lighting("point", "height", v))
-        self._lighting_controls["point.height"] = height_slider
-        grid.addWidget(height_slider, 2, 0, 1, 2)
+        posx = LabeledSlider("Позиция X", -5000.0, 5000.0, 10.0, decimals=0, unit="мм")
+        posx.valueChanged.connect(lambda v: self._update_lighting("point", "position_x", v))
+        self._lighting_controls["point.position_x"] = posx
+        grid.addWidget(posx, 2, 0, 1, 2)
+
+        posy = LabeledSlider("Позиция Y", 0.0, 5000.0, 10.0, decimals=1, unit="мм")
+        posy.valueChanged.connect(lambda v: self._update_lighting("point", "position_y", v))
+        self._lighting_controls["point.position_y"] = posy
+        grid.addWidget(posy, 3, 0, 1, 2)
 
         range_slider = LabeledSlider("Радиус действия", 200.0, 5000.0, 10.0, decimals=1, unit="мм")
         range_slider.valueChanged.connect(lambda v: self._update_lighting("point", "range", v))
         self._lighting_controls["point.range"] = range_slider
         grid.addWidget(range_slider, 4, 0, 1, 2)
 
         # ✅ Новый переключатель: тени от точечного света
         point_shadows = QCheckBox("Тени от точечного света", self)
         point_shadows.clicked.connect(lambda checked: self._update_lighting("point", "cast_shadow", checked))
         self._lighting_controls["point.cast_shadow"] = point_shadows
-        grid.addWidget(point_shadows, 5, 0, 1, 2)
+        grid.addWidget(point_shadows, 5, 0, 1, 2)
+
+        point_bind = QCheckBox("Привязать к камере", self)
+        point_bind.clicked.connect(lambda checked: self._update_lighting("point", "bind_to_camera", checked))
+        self._lighting_controls["point.bind"] = point_bind
+        grid.addWidget(point_bind, 6, 0, 1, 2)
         return group

    def _build_lighting_preset_group(self) -> QGroupBox:
        group = QGroupBox("Пресеты освещения", self)
        layout = QHBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        presets = {
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

    # --- Environment --------------------------------------------------
    def _build_environment_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(self._build_background_group())
        layout.addWidget(self._build_fog_group())
        layout.addWidget(self._build_ao_group())
        layout.addStretch(1)
        return tab

    def _build_background_group(self) -> QGroupBox:
        group = QGroupBox("Фон и IBL", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
 
        # Комбинированный режим (4 опции)
        mode_combo = QComboBox(self)
        mode_combo.addItem("IBL + Skybox (HDR)", (True, "skybox"))
        mode_combo.addItem("IBL + Сплошной цвет", (True, "color"))
        mode_combo.addItem("Без IBL + Skybox (HDR)", (False, "skybox"))
        mode_combo.addItem("Без IBL + Сплошной цвет", (False, "color"))
        def on_mode_changed():
            ibl_on, bg_mode = mode_combo.currentData()
            self._update_environment("ibl_enabled", bool(ibl_on))
            self._update_environment("background_mode", bg_mode)
        mode_combo.currentIndexChanged.connect(lambda _: on_mode_changed())
        self._environment_controls["combined.mode"] = mode_combo
        grid.addWidget(QLabel("Режим", self), 0, 0)
        grid.addWidget(mode_combo, 0, 1)
 
         bg_row = QHBoxLayout()
         bg_row.addWidget(QLabel("Цвет", self))
         bg_button = ColorButton()
         bg_button.color_changed.connect(lambda c: self._update_environment("background_color", c))
         self._environment_controls["background.color"] = bg_button
         bg_row.addWidget(bg_button)
         bg_row.addStretch(1)
         grid.addLayout(bg_row, 1, 0, 1, 2)
 
         # Интенсивность IBL
         ibl_check = QCheckBox("Включить IBL", self)
         ibl_check.clicked.connect(lambda checked: self._on_ibl_enabled_clicked(checked))
         self._environment_controls["ibl.enabled"] = ibl_check
         grid.addWidget(ibl_check, 2, 0, 1, 2)
 
         intensity = LabeledSlider("Интенсивность IBL", 0.0, 5.0, 0.05, decimals=2)
         intensity.valueChanged.connect(lambda v: self._update_environment("ibl_intensity", v))
         self._environment_controls["ibl.intensity"] = intensity
         grid.addWidget(intensity, 3, 0, 1, 2)
 
         blur = LabeledSlider("Размытие skybox", 0.0, 1.0, 0.01, decimals=2)
         blur.valueChanged.connect(lambda v: self._update_environment("skybox_blur", v))
         self._environment_controls["skybox.blur"] = blur
         grid.addWidget(blur, 4, 0, 1, 2)
 
         # Выпадающий список HDR/EXR из папки
         hdr_combo = QComboBox(self)
         hdr_files = self._discover_hdr_files()
         for label, path in hdr_files:
             hdr_combo.addItem(label, path)
         def on_hdr_changed():
             self._update_environment("ibl_source", hdr_combo.currentData())
         hdr_combo.currentIndexChanged.connect(lambda _: on_hdr_changed())
         self._environment_controls["ibl.file"] = hdr_combo
         grid.addWidget(QLabel("HDR файл", self), 5, 0)
         grid.addWidget(hdr_combo, 5, 1)
+
+        # Размещение окружения относительно модели (X/Y) и привязка к камере
+        env_off_x = LabeledSlider("Смещение окружения X", -180.0, 180.0, 1.0, decimals=0, unit="°")
+        env_off_x.valueChanged.connect(lambda v: self._update_environment("ibl_offset_x", v))
+        self._environment_controls["ibl.offset_x"] = env_off_x
+        grid.addWidget(env_off_x, 6, 0, 1, 2)
+
+        env_off_y = LabeledSlider("Смещение окружения Y", -180.0, 180.0, 1.0, decimals=0, unit="°")
+        env_off_y.valueChanged.connect(lambda v: self._update_environment("ibl_offset_y", v))
+        self._environment_controls["ibl.offset_y"] = env_off_y
+        grid.addWidget(env_off_y, 7, 0, 1, 2)
+
+        env_bind = QCheckBox("Привязать окружение к камере", self)
+        env_bind.clicked.connect(lambda checked: self._update_environment("ibl_bind_to_camera", checked))
+        self._environment_controls["ibl.bind"] = env_bind
+        grid.addWidget(env_bind, 8, 0, 1, 2)
         return group

    def _build_fog_group(self) -> QGroupBox:
        group = QGroupBox("Туман", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        enabled = QCheckBox("Включить туман", self)
        # ✅ FIX: Логируем клик + вызываем обработчик
        enabled.clicked.connect(lambda checked: self._on_fog_enabled_clicked(checked))
        self._environment_controls["fog.enabled"] = enabled
        grid.addWidget(enabled, 0, 0, 1, 2)

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Цвет", self))
        fog_color = ColorButton()
        fog_color.color_changed.connect(lambda c: self._update_environment("fog_color", c))
        self._environment_controls["fog.color"] = fog_color
        color_row.addWidget(fog_color)
        color_row.addStretch(1)
        grid.addLayout(color_row, 1, 0, 1, 2)

        density = LabeledSlider("Плотность", 0.0, 1.0, 0.01, decimals=2)
        density.valueChanged.connect(lambda v: self._update_environment("fog_density", v))
        self._environment_controls["fog.density"] = density
        grid.addWidget(density, 2, 0, 1, 2)

        near_slider = LabeledSlider("Начало", 0.0, 20000.0, 50.0, decimals=0, unit="мм")
        near_slider.valueChanged.connect(lambda v: self._update_environment("fog_near", v))
        self._environment_controls["fog.near"] = near_slider
        grid.addWidget(near_slider, 3, 0, 1, 2)

        far_slider = LabeledSlider("Конец", 500.0, 60000.0, 100.0, decimals=0, unit="мм")
        far_slider.valueChanged.connect(lambda v: self._update_environment("fog_far", v))
        self._environment_controls["fog.far"] = far_slider
        grid.addWidget(far_slider, 4, 0, 1, 2)
        return group

    def _build_ao_group(self) -> QGroupBox:
        group = QGroupBox("Ambient Occlusion", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        enabled = QCheckBox("Включить SSAO", self)
        enabled.clicked.connect(lambda checked: self._update_environment("ao_enabled", checked))
        self._environment_controls["ao.enabled"] = enabled
        grid.addWidget(enabled, 0, 0, 1, 2)

        strength = LabeledSlider("Интенсивность", 0.0, 2.0, 0.02, decimals=2)
        strength.valueChanged.connect(lambda v: self._update_environment("ao_strength", v))
        self._environment_controls["ao.strength"] = strength  # ✅ ИСПРАВЛЕНО: snake_case
        grid.addWidget(strength, 1, 0, 1, 2)

        radius = LabeledSlider("Радиус", 0.5, 20.0, 0.1, decimals=2)
        radius.valueChanged.connect(lambda v: self._update_environment("ao_radius", v))
        self._environment_controls["ao.radius"] = radius
        grid.addWidget(radius, 2, 0, 1, 2)
        return group

    # --- Quality ------------------------------------------------------
    def _build_quality_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(self._build_quality_preset_group())
        layout.addWidget(self._build_shadow_group())
        layout.addWidget(self._build_antialiasing_group())
        layout.addWidget(self._build_render_group())
        layout.addStretch(1)
        return tab

    def _build_quality_preset_group(self) -> QGroupBox:
        group = QGroupBox("Предустановки качества", self)
        layout = QHBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(12)

        layout.addWidget(QLabel("Профиль", self))
        combo = QComboBox(self)
        for key in self._quality_preset_order:
            combo.addItem(self._quality_preset_labels[key], key)
        combo.currentIndexChanged.connect(lambda _: self._on_quality_preset_changed(combo.currentData()))
        self._quality_controls["quality.preset"] = combo
        layout.addWidget(combo, 1)

        hint = QLabel('Профиль "Пользовательский" активируется при ручных изменениях.', self)
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #8a8a8a;")
        layout.addWidget(hint, 2)
        layout.addStretch(1)
        return group

    def _build_shadow_group(self) -> QGroupBox:
        group = QGroupBox("Тени", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        enabled = QCheckBox("Включить тени", self)
        enabled.clicked.connect(lambda checked: self._update_quality("shadows.enabled", checked))
        self._quality_controls["shadows.enabled"] = enabled
        grid.addWidget(enabled, 0, 0, 1, 2)

        resolution = QComboBox(self)
        for label, value in [
            ("256 (Низкое)", "256"),
            ("512 (Среднее)", "512"),
            ("1024 (Высокое)", "1024"),
            ("2048 (Очень высокое)", "2048"),
            ("4096 (Ультра)", "4096"),
        ]:
            resolution.addItem(label, value)
        resolution.currentIndexChanged.connect(lambda _: self._update_quality("shadows.resolution", resolution.currentData()))
        self._quality_controls["shadows.resolution"] = resolution
        grid.addWidget(QLabel("Разрешение", self), 1, 0)
        grid.addWidget(resolution, 1, 1)

        shadow_filter = QComboBox(self)
        for label, value in [("Жёсткие", 1), ("PCF 4", 4), ("PCF 8", 8), ("PCF 16", 16), ("PCF 32", 32)]:
            shadow_filter.addItem(label, value)
        shadow_filter.currentIndexChanged.connect(lambda _: self._update_quality("shadows.filter", shadow_filter.currentData()))
        self._quality_controls["shadows.filter"] = shadow_filter
        grid.addWidget(QLabel("Фильтрация", self), 2, 0)
        grid.addWidget(shadow_filter, 2, 1)

        bias = LabeledSlider("Shadow Bias", 0.0, 50.0, 0.1, decimals=2)
        bias.valueChanged.connect(lambda v: self._update_quality("shadows.bias", v))
        self._quality_controls["shadows.bias"] = bias
        grid.addWidget(bias, 3, 0, 1, 2)

        darkness = LabeledSlider("Темнота", 0.0, 100.0, 1.0, decimals=0, unit="%")
        darkness.valueChanged.connect(lambda v: self._update_quality("shadows.darkness", v))
        self._quality_controls["shadows.darkness"] = darkness
        grid.addWidget(darkness, 4, 0, 1, 2)
        return group

    def _build_antialiasing_group(self) -> QGroupBox:
        group = QGroupBox("Сглаживание", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        primary_combo = QComboBox(self)
        for label, value in [("Выкл.", "off"), ("MSAA", "msaa"), ("SSAA", "ssaa")]:
            primary_combo.addItem(label, value)
        primary_combo.currentIndexChanged.connect(lambda _: self._on_primary_aa_changed(primary_combo.currentData()))
        self._quality_controls["aa.primary"] = primary_combo
        grid.addWidget(QLabel("Геометрическое AA", self), 0, 0)
        grid.addWidget(primary_combo, 0, 1)

        quality_combo = QComboBox(self)
        for label, value in [("Низкое", "low"), ("Среднее", "medium"), ("Высокое", "high")]:
            quality_combo.addItem(label, value)
        quality_combo.currentIndexChanged.connect(lambda _: self._update_quality("antialiasing.quality", quality_combo.currentData()))
        self._quality_controls["aa.quality"] = quality_combo
        grid.addWidget(QLabel("Качество", self), 1, 0)
        grid.addWidget(quality_combo, 1, 1)

        post_combo = QComboBox(self)
        for label, value in [("Выкл.", "off"), ("FXAA", "fxaa"), ("TAA", "taa")]:
            post_combo.addItem(label, value)
        post_combo.currentIndexChanged.connect(lambda _: self._update_quality("antialiasing.post", post_combo.currentData()))
        self._quality_controls["aa.post"] = post_combo
        grid.addWidget(QLabel("Постобработка", self), 2, 0)
        grid.addWidget(post_combo, 2, 1)

        taa_check = QCheckBox("Включить TAA", self)
        taa_check.clicked.connect(lambda checked: self._update_quality("taa.enabled", checked))
        self._quality_controls["taa.enabled"] = taa_check
        grid.addWidget(taa_check, 3, 0, 1, 2)

        taa_strength = LabeledSlider("Сила TAA", 0.0, 1.0, 0.01, decimals=2)
        taa_strength.valueChanged.connect(lambda v: self._update_quality("taa.strength", v))
        self._quality_controls["taa.strength"] = taa_strength
        grid.addWidget(taa_strength, 4, 0, 1, 2)

        taa_motion = QCheckBox("Отключать TAA при движении камеры", self)
        taa_motion.clicked.connect(lambda checked: self._update_quality("taa_motion_adaptive", checked))
        self._quality_controls["taa_motion_adaptive"] = taa_motion
        grid.addWidget(taa_motion, 5, 0, 1, 2)

        fxaa_check = QCheckBox("Включить FXAA", self)
        fxaa_check.clicked.connect(lambda checked: self._update_quality("fxaa.enabled", checked))
        self._quality_controls["fxaa.enabled"] = fxaa_check
        grid.addWidget(fxaa_check, 6, 0, 1, 2)

        specular_check = QCheckBox("Specular AA", self)
        specular_check.clicked.connect(lambda checked: self._update_quality("specular_aa", checked))
        self._quality_controls["specular.enabled"] = specular_check
        grid.addWidget(specular_check, 7, 0, 1, 2)

        return group

    def _build_render_group(self) -> QGroupBox:
        group = QGroupBox("Производительность", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        scale_slider = LabeledSlider("Масштаб рендера", 0.5, 1.5, 0.01, decimals=2)
        scale_slider.valueChanged.connect(lambda v: self._update_quality("render_scale", v))
        self._quality_controls["render.scale"] = scale_slider
        grid.addWidget(scale_slider, 0, 0, 1, 2)

        policy_combo = QComboBox(self)
        policy_combo.addItem("Максимальная частота", "always")
        policy_combo.addItem("По требованию", "ondemand")
        policy_combo.currentIndexChanged.connect(lambda _: self._update_quality("render_policy", policy_combo.currentData()))
        self._quality_controls["render.policy"] = policy_combo
        grid.addWidget(QLabel("Политика обновления", self), 1, 0)
        grid.addWidget(policy_combo, 1, 1)

        frame_slider = LabeledSlider("Лимит FPS", 24.0, 240.0, 1.0, decimals=0)
        frame_slider.valueChanged.connect(lambda v: self._update_quality("frame_rate_limit", v))
        self._quality_controls["frame_rate_limit"] = frame_slider
        grid.addWidget(frame_slider, 2, 0, 1, 2)

        oit_check = QCheckBox("Weighted OIT", self)
        oit_check.clicked.connect(lambda checked: self._update_quality("oit", "weighted" if checked else "none"))
        self._quality_controls["oit.enabled"] = oit_check
        grid.addWidget(oit_check, 3, 0, 1, 2)
        return group

    def _on_quality_preset_changed(self, preset_key: str | None) -> None:
        if self._updating_ui:
            return
        if not preset_key:
            return
        if preset_key == "custom":
            self.state["quality"]["preset"] = "custom"
            self._emit_quality()
            return
        self._apply_quality_preset(str(preset_key))

    def _apply_quality_preset(self, key: str) -> None:
        config = self._quality_presets.get(key)
        if not config:
            return
        self._suspend_preset_sync = True
        try:
            self.state["quality"]["preset"] = key
            self._deep_update(self.state["quality"], copy.deepcopy(config))
            self._apply_quality_constraints()
            previous = self._updating_ui
            self._updating_ui = True
            try:
                self._apply_quality_ui()
            finally:
                self._updating_ui = previous
        finally:
            self._suspend_preset_sync = False
        self._sync_quality_preset_ui()
        self._emit_quality()
        self.preset_applied.emit(f"Профиль качества: {self._quality_preset_labels.get(key, key)}")

    def _sync_quality_preset_ui(self) -> None:
        combo = self._quality_controls.get("quality.preset")
        if not isinstance(combo, QComboBox):
            return
        previous = self._updating_ui
        self._updating_ui = True
        try:
            preset_key = self.state["quality"].get("preset", "custom")
            index = combo.findData(preset_key)
            if index >= 0:
                combo.setCurrentIndex(index)
        finally:
            self._updating_ui = previous

    def _set_quality_custom(self) -> None:
        if self._suspend_preset_sync:
            return
        if self.state["quality"].get("preset") != "custom":
            self.state["quality"]["preset"] = "custom"
            self._sync_quality_preset_ui()

    def _ensure_material_defaults(self, key: str) -> None:
        base = self._defaults["materials"].get(key, {})
        target = self.state["materials"].setdefault(key, {})
        for prop, value in base.items():
            target.setdefault(prop, value)

    # --- Camera -------------------------------------------------------
    def _build_camera_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        group = QGroupBox("Камера", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        fov = LabeledSlider("Поле зрения", 10.0, 120.0, 0.5, decimals=1, unit="°")
        fov.valueChanged.connect(lambda v: self._update_camera("fov", v))
        self._camera_controls["fov"] = fov
        grid.addWidget(fov, 0, 0, 1, 2)

        near_clip = LabeledSlider("Ближняя плоскость", 1.0, 100.0, 1.0, decimals=1, unit="мм")
        near_clip.valueChanged.connect(lambda v: self._update_camera("near", v))
        self._camera_controls["near"] = near_clip
        grid.addWidget(near_clip, 1, 0, 1, 2)

        far_clip = LabeledSlider("Дальняя плоскость", 1000.0, 100000.0, 500.0, decimals=0, unit="мм")
        far_clip.valueChanged.connect(lambda v: self._update_camera("far", v))
        self._camera_controls["far"] = far_clip
        grid.addWidget(far_clip, 2, 0, 1, 2)

        speed = LabeledSlider("Скорость камеры", 0.1, 5.0, 0.1, decimals=2)
        speed.valueChanged.connect(lambda v: self._update_camera("speed", v))
        self._camera_controls["speed"] = speed
        grid.addWidget(speed, 3, 0, 1, 2)

        auto_rotate = QCheckBox("Автоповорот", self)
        
        # ✅ НОВОЕ: Обработчик с логированием пользовательского клика
        def on_auto_rotate_clicked(checked: bool):
            # Логируем КЛИК (перед обработчиком)
            self.event_logger.log_user_click(
                widget_name="auto_rotate",
                widget_type="QCheckBox",
                value=checked
            )
            
            # Вызываем обработчик
            self._update_camera("auto_rotate", checked)
        
        auto_rotate.clicked.connect(on_auto_rotate_clicked)
        self._camera_controls["auto_rotate"] = auto_rotate
        grid.addWidget(auto_rotate, 4, 0, 1, 2)

        rotate_speed = LabeledSlider("Скорость автоповорота", 0.1, 3.0, 0.05, decimals=2)
        rotate_speed.valueChanged.connect(lambda v: self._update_camera("auto_rotate_speed", v))
        self._camera_controls["auto_rotate_speed"] = rotate_speed
        grid.addWidget(rotate_speed, 5, 0, 1, 2)

        layout.addWidget(group)
        layout.addStretch(1)
        return tab

    # --- Materials ----------------------------------------------------
    def _build_materials_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        selector_row = QHBoxLayout()
        selector_row.addWidget(QLabel("Компонент", self))
        self._material_labels = {
            "frame": "Рама",
            "lever": "Рычаг",
            "tail": "Хвостовик",
            "cylinder": "Цилиндр (стекло)",
            "piston_body": "Корпус поршня",
            "piston_rod": "Шток",
            "joint_tail": "Шарнир хвостовика",
            "joint_arm": "Шарнир рычага",
        }
        self._material_selector = QComboBox(self)
        for key, label in self._material_labels.items():
            self._material_selector.addItem(label, key)
        self._material_selector.currentIndexChanged.connect(self._on_material_selection_changed)
        selector_row.addWidget(self._material_selector, 1)
        selector_row.addStretch(1)
        layout.addLayout(selector_row)

        group = QGroupBox("Параметры материала", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        row = 0
        row = self._add_material_color(grid, row, "Базовый цвет", "base_color")
        row = self._add_material_slider(grid, row, "Металличность", "metalness", 0.0, 1.0, 0.01)
        row = self._add_material_slider(grid, row, "Шероховатость", "roughness", 0.0, 1.0, 0.01)
        row = self._add_material_slider(grid, row, "Specular", "specular", 0.0, 1.0, 0.01)
        row = self._add_material_slider(grid, row, "Specular Tint", "specular_tint", 0.0, 1.0, 0.01)
        row = self._add_material_slider(grid, row, "Clearcoat", "clearcoat", 0.0, 1.0, 0.01)
        row = self._add_material_slider(grid, row, "Шероховатость лака", "clearcoat_roughness", 0.0, 1.0, 0.01)
        row = self._add_material_slider(grid, row, "Пропускание", "transmission", 0.0, 1.0, 0.01)
        row = self._add_material_slider(grid, row, "Непрозрачность", "opacity", 0.0, 1.0, 0.01)
        row = self._add_material_slider(grid, row, "Index of Refraction", "ior", 1.0, 3.0, 0.01)
        row = self._add_material_slider(grid, row, "Attenuation distance", "attenuation_distance", 0.0, 10000.0, 10.0, decimals=1)
        row = self._add_material_color(grid, row, "Attenuation color", "attenuation_color")
        row = self._add_material_color(grid, row, "Излучающий цвет", "emissive_color")
        row = self._add_material_slider(grid, row, "Яркость излучения", "emissive_intensity", 0.0, 5.0, 0.05)
        row = self._add_material_color(grid, row, "Цвет предупреждения", "warning_color")
        row = self._add_material_color(grid, row, "Цвет OK", "ok_color")
        row = self._add_material_color(grid, row, "Цвет ошибки", "error_color")

        layout.addWidget(group)
        layout.addStretch(1)

        self._on_material_selection_changed()
        return tab

    def _add_material_color(self, grid: QGridLayout, row: int, title: str, key: str) -> int:
        container = QWidget(self)
        hbox = QHBoxLayout(container)
        hbox.setContentsMargins(0, 0, 0, 0)
        hbox.setSpacing(6)
        hbox.addWidget(QLabel(title, self))
        button = ColorButton()
        button.color_changed.connect(lambda c, prop=key: self._on_material_color_changed(prop, c))
        self._material_controls[key] = button
        self._material_rows[key] = container
        hbox.addWidget(button)
        hbox.addStretch(1)
        grid.addWidget(container, row, 0, 1, 2)
        return row + 1

    def _add_material_slider(
        self,
        grid: QGridLayout,
        row: int,
        title: str,
        key: str,
        minimum: float,
        maximum: float,
        step: float,
        *,
        decimals: int = 2,
    ) -> int:
        slider = LabeledSlider(title, minimum, maximum, step, decimals=decimals)
        slider.valueChanged.connect(lambda v, prop=key: self._on_material_value_changed(prop, v))
        self._material_controls[key] = slider
        self._material_rows[key] = slider
        grid.addWidget(slider, row, 0, 1, 2)
        return row + 1

    def _on_material_selection_changed(self) -> None:
        if self._updating_ui:
            return
        self._updating_ui = True
        try:
            key = self._current_material_key()
            if not key:
                return
            self._ensure_material_defaults(key)
            data = self.state["materials"].get(key, {})
            defaults = self._defaults["materials"].get(key, {})
            for prop, widget in self._material_controls.items():
                value = data.get(prop, defaults.get(prop))
                if value is None:
                    continue
                if isinstance(widget, ColorButton):
                    widget.set_color(value)
                elif isinstance(widget, LabeledSlider):
                    widget.set_value(value)
        finally:
            self._updating_ui = False

    def _current_material_key(self) -> str:
        return self._material_selector.currentData()

    def _on_material_color_changed(self, prop: str, color: str) -> None:
        if self._updating_ui:
            return
        key = self._current_material_key()
        if not key or prop not in self.state["materials"].get(key, {}):
            return
        
        # Сохраняем старое значение для логирования
        old_value = self.state["materials"][key].get(prop)
        
        self.state["materials"][key][prop] = color
        
        # Логируем изменение
        self.graphics_logger.log_change(
            parameter_name=f"{key}.{prop}",
            old_value=old_value,
            new_value=color,
            category="material",
            panel_state=self.state
        )
        
        # ✅ НОВОЕ: Логируем отправку Python-сигнала
        try:
            self.event_logger.log_signal_emit("material_changed", self._prepare_materials_payload())
        except Exception:
            pass
        
        self._emit_material_update(key)

    def _on_material_value_changed(self, prop: str, value: float) -> None:
        if self._updating_ui:
            return
        key = self._current_material_key()
        if not key or prop not in self.state["materials"].get(key, {}):
            return
        
        # Сохраняем старое значение для логирования
        old_value = self.state["materials"][key].get(prop)
        
        self.state["materials"][key][prop] = value
        
        # Логируем изменение
        self.graphics_logger.log_change(
            parameter_name=f"{key}.{prop}",
            old_value=old_value,
            new_value=value,
            category="material",
            panel_state=self.state
        )
        
        # ✅ НОВОЕ: Логируем отправку Python-сигнала
        try:
            self.event_logger.log_signal_emit("material_changed", self._prepare_materials_payload())
        except Exception:
            pass
        
        self._emit_material_update(key)

    # --- Effects ------------------------------------------------------
    def _build_effects_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(self._build_bloom_group())
        layout.addWidget(self._build_tonemap_group())
        layout.addWidget(self._build_dof_group())
        layout.addWidget(self._build_misc_effects_group())
        layout.addStretch(1)
        return tab

    def _build_bloom_group(self) -> QGroupBox:
        group = QGroupBox("Bloom", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        enabled = QCheckBox("Включить Bloom", self)
        
        # ✅ FIX: Логируем клик + вызываем обработчик
        enabled.clicked.connect(lambda checked: self._on_bloom_enabled_clicked(checked))
        self._effects_controls["bloom.enabled"] = enabled
        grid.addWidget(enabled, 0, 0, 1, 2)

        intensity = LabeledSlider("Интенсивность", 0.0, 2.0, 0.02, decimals=2)
        intensity.valueChanged.connect(lambda v: self._update_effects("bloom_intensity", v))
        self._effects_controls["bloom.intensity"] = intensity
        grid.addWidget(intensity, 1, 0, 1, 2)

        threshold = LabeledSlider("Порог", 0.0, 4.0, 0.05, decimals=2)
        threshold.valueChanged.connect(lambda v: self._update_effects("bloom_threshold", v))
        self._effects_controls["bloom.threshold"] = threshold
        grid.addWidget(threshold, 2, 0, 1, 2)

        spread = LabeledSlider("Распространение", 0.2, 1.0, 0.02, decimals=2)
        spread.valueChanged.connect(lambda v: self._update_effects("bloom_spread", v))
        self._effects_controls["bloom.spread"] = spread
        grid.addWidget(spread, 3, 0, 1, 2)
        return group

    def _build_tonemap_group(self) -> QGroupBox:
        group = QGroupBox("Тонемаппинг", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        enabled = QCheckBox("Включить тонемаппинг", self)
        enabled.clicked.connect(lambda checked: self._update_effects("tonemap_enabled", checked))
        self._effects_controls["tonemap.enabled"] = enabled
        grid.addWidget(enabled, 0, 0, 1, 2)

        combo = QComboBox(self)
        for label, value in [
            ("Filmic", "filmic"),
            ("ACES", "aces"),
            ("Reinhard", "reinhard"),
            ("Gamma", "gamma"),
            ("Linear", "linear"),
        ]:
            combo.addItem(label, value)
        combo.currentIndexChanged.connect(lambda _: self._update_effects("tonemap_mode", combo.currentData()))
        self._effects_controls["tonemap.mode"] = combo
        grid.addWidget(QLabel("Режим", self), 1, 0)
        grid.addWidget(combo, 1, 1)

        return group

    def _build_dof_group(self) -> QGroupBox:
        group = QGroupBox("Глубина резкости", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        enabled = QCheckBox("Включить DoF", self)
        enabled.clicked.connect(lambda checked: self._update_effects("depth_of_field", checked))
        self._effects_controls["dof.enabled"] = enabled
        grid.addWidget(enabled, 0, 0, 1, 2)

        focus = LabeledSlider("Фокусное расстояние", 200.0, 20000.0, 50.0, decimals=0, unit="мм")
        focus.valueChanged.connect(lambda v: self._update_effects("dof_focus_distance", v))
        self._effects_controls["dof.focus"] = focus
        grid.addWidget(focus, 1, 0, 1, 2)

        blur = LabeledSlider("Размытие", 0.0, 10.0, 0.1, decimals=2)
        blur.valueChanged.connect(lambda v: self._update_effects("dof_blur", v))
        self._effects_controls["dof.blur"] = blur
        grid.addWidget(blur, 2, 0, 1, 2)
        return group

    def _build_misc_effects_group(self) -> QGroupBox:
        group = QGroupBox("Дополнительные эффекты", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        motion = QCheckBox("Размытие движения", self)
        motion.clicked.connect(lambda checked: self._update_effects("motion_blur", checked))
        self._effects_controls["motion.enabled"] = motion
        grid.addWidget(motion, 0, 0, 1, 2)

        motion_strength = LabeledSlider("Сила размытия", 0.0, 1.0, 0.02, decimals=2)
        motion_strength.valueChanged.connect(lambda v: self._update_effects("motion_blur_amount", v))
        self._effects_controls["motion.amount"] = motion_strength
        grid.addWidget(motion_strength, 1, 0, 1, 2)

        lens_flare = QCheckBox("Линзовые блики", self)
        lens_flare.clicked.connect(lambda checked: self._update_effects("lens_flare", checked))
        self._effects_controls["lens_flare.enabled"] = lens_flare
        grid.addWidget(lens_flare, 2, 0, 1, 2)

        vignette = QCheckBox("Виньетирование", self)
        vignette.clicked.connect(lambda checked: self._update_effects("vignette", checked))
        self._effects_controls["vignette.enabled"] = vignette
        grid.addWidget(vignette, 3, 0, 1, 2)

        vignette_strength = LabeledSlider("Сила виньетки", 0.0, 1.0, 0.02, decimals=2)
        vignette_strength.valueChanged.connect(lambda v: self._update_effects("vignette_strength", v))
        self._effects_controls["vignette.strength"] = vignette_strength
        grid.addWidget(vignette_strength, 4, 0, 1, 2)
        return group

    def _apply_quality_constraints(self) -> None:
        """Apply constraints between quality settings"""
        self._normalise_quality_state()
        self._sync_taa_controls()

    def _apply_lighting_preset(self, preset: Dict[str, Any], name: str) -> None:
        """Apply lighting preset"""
        self._updating_ui = True
        try:
            self.state["lighting"] = copy.deepcopy(preset)
            self._apply_lighting_ui()
        finally:
            self._updating_ui = False
        self._emit_lighting()
        self.preset_applied.emit(f"Освещение: {name}")

    def _on_primary_aa_changed(self, value: str) -> None:
        """Handle primary AA mode change"""
        if self._updating_ui:
            return
        self.state["quality"]["antialiasing"]["primary"] = value
        self._set_quality_custom()
        self._sync_taa_controls()
        self._emit_quality()

    # ------------------------------------------------------------------
    # Update methods for state changes
    # ------------------------------------------------------------------
    def _update_lighting(self, group: str, key: str, value: Any) -> None:
        """Update lighting parameter"""
        if self._updating_ui:
            return
        
        # Сохраняем старое значение для логирования
        old_value = self.state["lighting"].get(group, {}).get(key)
        
        if group not in self.state["lighting"]:
            self.state["lighting"][group] = {}
        self.state["lighting"][group][key] = value
        
        # Логируем изменение
        self.graphics_logger.log_change(
            parameter_name=f"{group}.{key}",
            old_value=old_value,
            new_value=value,
            category="lighting",
            panel_state=self.state
        )
        
        # ✅ ИСПРАВЛЕНО: Используем правильный API EventLogger
        if group == "key" and key in {"brightness", "color", "angle_x", "angle_y"}:
            self.event_logger.log_event(
                event_type=EventType.STATE_CHANGE,
                component=f"lighting.{group}",
                action=key,
                old_value=old_value,
                new_value=value
            )
        
        self._emit_lighting()

    def _update_environment(self, key: str, value: Any) -> None:
        """Update environment parameter"""
        if self._updating_ui:
            return 
        
        # Сохраняем старое значение для логирования
        old_value = self.state["environment"].get(key)
        
        self.state["environment"][key] = value
        
        # Логируем изменение
        self.graphics_logger.log_change(
            parameter_name=key,
            old_value=old_value,
            new_value=value,
            category="environment",
            panel_state=self.state
        )
        
        self._emit_environment()

    def _update_quality(self, key: str, value: Any) -> None:
        """Update quality parameter"""
        if self._updating_ui:
            return
        
        # Сохраняем старое значение для логирования
        old_value = None

        # ✅ Алиасы для плоских ключей качества (во избежание вложенных структур)
        if key == "fxaa.enabled":
            old_value = self.state["quality"].get("fxaa_enabled")
            self.state["quality"]["fxaa_enabled"] = value
        elif key == "taa.enabled":
            old_value = self.state["quality"].get("taa_enabled")
            self.state["quality"]["taa_enabled"] = value
        else:
            # Обычная обработка (включая вложенные shadows.*, antialiasing.*)
            if "." in key:
                parts = key.split(".")
                target = self.state["quality"]
                # Получаем старое значение, если возможно
                tmp = target
                for part in parts[:-1]:
                    if part in tmp and isinstance(tmp[part], dict):
                        tmp = tmp[part]
                    else:
                        tmp = None
                        break
                if isinstance(tmp, dict):
                    old_value = tmp.get(parts[-1])
                # Устанавливаем новое значение
                for part in parts[:-1]:
                    if part not in target or not isinstance(target[part], dict):
                        target[part] = {}
                    target = target[part]
                target[parts[-1]] = value
            else:
                old_value = self.state["quality"].get(key)
                self.state["quality"][key] = value
        
        # Логируем изменение
        self.graphics_logger.log_change(
            parameter_name=key,
            old_value=old_value,
            new_value=value,
            category="quality",
            panel_state=self.state
        )
        
        # ✅ ИСПРАВЛЕНО: Используем правильный API EventLogger
        self.event_logger.log_event(
            event_type=EventType.STATE_CHANGE,
            component="quality",
            action=key,
            old_value=old_value,
            new_value=value
        )
        
        self._set_quality_custom()
        self._emit_quality()

    def _update_camera(self, key: str, value: Any) -> None:
        if self._updating_ui:
            self.logger.debug(f"🔒 _update_camera blocked (updating_ui=True): {key}={value}")
            return
        
        # Сохраняем старое значение для логирования
        old_value = self.state["camera"].get(key)
        
        # ✅ КРИТИЧЕСКОЕ ЛОГИРОВАНИЕ для автовращения
        if key == "auto_rotate":
            self.logger.info(f"🔄 AUTO_ROTATE CHANGE DETECTED: {value}")
            self.logger.info(f"   Previous state: {self.state['camera'].get('auto_rotate', 'UNKNOWN')}")
        
        self.state["camera"][key] = value
        
        # Логируем изменение
        self.graphics_logger.log_change(
            parameter_name=key,
            old_value=old_value,
            new_value=value,
            category="camera",
            panel_state=self.state
        )
        
        self._emit_camera()
        
        if key == "auto_rotate":
            self.logger.info(f"   New state saved: {self.state['camera']['auto_rotate']}")
            self.logger.info(f"   About to emit camera_changed signal...")
        
        self._emit_camera()
        
        if key == "auto_rotate":
            self.logger.info(f"   ✅ camera_changed signal emitted!")

    def _update_effects(self, key: str, value: Any) -> None:
        """Update effects parameter"""
        if self._updating_ui:
            return
        
        # Сохраняем старое значение для логирования
        old_value = self.state["effects"].get(key)
        
        self.state["effects"][key] = value
        
        # Логируем изменение
        self.graphics_logger.log_change(
             parameter_name=key,
             old_value=old_value,
             new_value=value,
             category="effects",
             panel_state=self.state
         )
        
        self._emit_effects()

    # ✅ НОВОЕ: Метод обработки клика IBL Enabled с логированием
    def _on_ibl_enabled_clicked(self, checked: bool) -> None:
        """Обработчик клика IBL Enabled с логированием USER_CLICK"""
        # Логируем клик ПЕРЕД обработкой
        self.event_logger.log_user_click(
            widget_name="ibl_enabled",
            widget_type="QCheckBox",
            value=checked
        )
        # Дополнительно пишем в обычный лог
        self.logger.info(f"IBL checkbox clicked: {checked}")
        
        # Вызываем стандартный обработчик
        self._update_environment("ibl_enabled", checked)

    # ✅ НОВОЕ: Метод обработки клика Auto Rotate с логированием
    def _on_auto_rotate_clicked(self, checked: bool) -> None:
        """Обработчик клика Auto Rotate с логированием USER_CLICK"""
        # Логируем КЛИК (перед обработчиком)
        self.event_logger.log_user_click(
            widget_name="auto_rotate",
            widget_type="QCheckBox",
            value=checked
        )
        
        # Вызываем обработчик
        self._update_camera("auto_rotate", checked)

    # ✅ НОВОЕ: Метод обработки клика Fog Enabled с логированием
    def _on_fog_enabled_clicked(self, checked: bool) -> None:
        """Обработчик клика Fog Enabled с логированием USER_CLICK"""
        # Логируем клик ПЕРЕД обработкой
        self.event_logger.log_user_click(
            widget_name="fog_enabled",
            widget_type="QCheckBox",
            value=checked
        )
        self._update_environment("fog_enabled", checked)

    # ✅ НОВОЕ: Метод обработки клика Bloom Enabled с логированием
    def _on_bloom_enabled_clicked(self, checked: bool) -> None:
        """Обработчик клика Bloom Enabled с логированием USER_CLICK"""
        # Логируем клик ПЕРЕД обработкой
        self.event_logger.log_user_click(
            widget_name="bloom_enabled",
            widget_type="QCheckBox",
            value=checked
        )
        self._update_effects("bloom_enabled", checked)

    # ------------------------------------------------------------------
    # HDR file selection
    # ------------------------------------------------------------------
    def _discover_hdr_files(self) -> list[tuple[str, str]]:
        """Ищет HDR/EXR файлы в каталоге assets/qml/assets и формирует список для combo."""
        results: list[tuple[str, str]] = []
        base = Path("assets/qml/assets")
        if base.exists():
            for ext in ("*.hdr", "*.exr"):
                for p in sorted(base.glob(ext)):
                    results.append((p.name, str(p.as_posix())))
        # Добавляем текущий источник по умолчанию, если он вне папки
        current = self.state.get("environment", {}).get("ibl_source")
        if current and all(lbl != Path(current).name for lbl, _ in results):
            results.insert(0, (Path(current).name, current))
        return results

    # ------------------------------------------------------------------
    # Signal emission methods
    # ------------------------------------------------------------------
    def _emit_lighting(self) -> None:
        payload = self._prepare_lighting_payload()
        # ✅ Логируем факт отправки Python-сигнала
        try:
            self.event_logger.log_signal_emit("lighting_changed", payload)
        except Exception:
            pass
        self.lighting_changed.emit(payload)

    def _emit_environment(self) -> None:
        payload = self._prepare_environment_payload()
        # ✅ Логируем факт отправки Python-сигнала
        try:
            self.event_logger.log_signal_emit("environment_changed", payload)
        except Exception:
            pass
        self.environment_changed.emit(payload)

    def _emit_material_update(self, key: str) -> None:
        payload = self._prepare_materials_payload()
        # ✅ Логируем факт отправки Python-сигнала
        try:
            self.event_logger.log_signal_emit("material_changed", payload)
        except Exception:
            pass
        self.material_changed.emit(payload)

    def _emit_quality(self) -> None:
        payload = self._prepare_quality_payload()
        # ✅ Логируем факт отправки Python-сигнала
        try:
            self.event_logger.log_signal_emit("quality_changed", payload)
        except Exception:
            pass
        self.quality_changed.emit(payload)

    def _emit_camera(self) -> None:
        payload = self._prepare_camera_payload()
        # ✅ Логируем факт отправки Python-сигнала
        try:
            self.event_logger.log_signal_emit("camera_changed", payload)
        except Exception:
            pass
        self.camera_changed.emit(payload)

    def _emit_effects(self) -> None:
        payload = self._prepare_effects_payload()
        # ✅ Логируем факт отправки Python-сигнала
        try:
            self.event_logger.log_signal_emit("effects_changed", payload)
        except Exception:
            pass
        self.effects_changed.emit(payload)

    def _emit_all(self) -> None:
        """Emit all signals with current state"""
        self._emit_lighting()
        self._emit_environment()
        self._emit_quality()
        self._emit_camera()
        self._emit_effects()
        for key in self.state["materials"]:
            self._emit_material_update(key)

    # ------------------------------------------------------------------
    # Payload preparation
    # ------------------------------------------------------------------
    def _prepare_lighting_payload(self) -> Dict[str, Any]:
        """Prepare lighting payload mapped to QML expected keys.

        QML expects keys like `key_light`, `fill_light`, `rim_light`, `point_light`.
        Internal state uses `key`, `fill`, `rim`, `point` — map and rename fields
        (e.g. `height` -> `position_y`) to ensure QML applyLightingUpdates applies updates.
        """
        src = copy.deepcopy(self.state.get("lighting", {}))
        payload: Dict[str, Any] = {}

        # ✅ Map: key → key_light
        key = src.get("key") or {}
        if key:
            kl = {}
            if "brightness" in key:
                kl["brightness"] = key.get("brightness")
            if "color" in key:
                kl["color"] = key.get("color")
            if "angle_x" in key:
                kl["angle_x"] = key.get("angle_x")
            if "angle_y" in key:
                kl["angle_y"] = key.get("angle_y")
            if "cast_shadow" in key:
                kl["casts_shadow"] = bool(key.get("cast_shadow"))
            if "bind_to_camera" in key:
                kl["bind_to_camera"] = bool(key.get("bind_to_camera"))
            if "position_x" in key:
                kl["position_x"] = key.get("position_x")
            if "position_y" in key:
                kl["position_y"] = key.get("position_y")
            payload["key_light"] = kl

        # ✅ Map: fill → fill_light
        fill = src.get("fill") or {}
        if fill:
            fl = {}
            if "brightness" in fill:
                fl["brightness"] = fill.get("brightness")
            if "color" in fill:
                fl["color"] = fill.get("color")
            if "cast_shadow" in fill:
                fl["casts_shadow"] = bool(fill.get("cast_shadow"))
            if "bind_to_camera" in fill:
                fl["bind_to_camera"] = bool(fill.get("bind_to_camera"))
            if "position_x" in fill:
                fl["position_x"] = fill.get("position_x")
            if "position_y" in fill:
                fl["position_y"] = fill.get("position_y")
            payload["fill_light"] = fl

        # ✅ Map: rim → rim_light
        rim = src.get("rim") or {}
        if rim:
            rl = {}
            if "brightness" in rim:
                rl["brightness"] = rim.get("brightness")
            if "color" in rim:
                rl["color"] = rim.get("color")
            if "cast_shadow" in rim:
                rl["casts_shadow"] = bool(rim.get("cast_shadow"))
            if "bind_to_camera" in rim:
                rl["bind_to_camera"] = bool(rim.get("bind_to_camera"))
            if "position_x" in rim:
                rl["position_x"] = rim.get("position_x")
            if "position_y" in rim:
                rl["position_y"] = rim.get("position_y")
            payload["rim_light"] = rl

        # ✅ Map: point → point_light + position_x/position_y
        point = src.get("point") or {}
        if point:
            pl = {}
            if "brightness" in point:
                pl["brightness"] = point.get("brightness")
            if "color" in point:
                pl["color"] = point.get("color")
            if "position_x" in point:
                pl["position_x"] = point.get("position_x")
            if "position_y" in point:
                pl["position_y"] = point.get("position_y")
            if "range" in point:
                pl["range"] = point.get("range")
            # ✅ Новый ключ для QML: casts_shadow
            if "cast_shadow" in point:
                pl["casts_shadow"] = bool(point.get("cast_shadow"))
            if "bind_to_camera" in point:
                pl["bind_to_camera"] = bool(point.get("bind_to_camera"))
            payload["point_light"] = pl

        return payload

    def _prepare_environment_payload(self) -> Dict[str, Any]:
        """Собирает вложенный payload окружения в формате, ожидаемом QML applyEnvironmentUpdates()."""
        env = self.state.get("environment", {})
        payload: Dict[str, Any] = {}

        # background (НЕ зависит от ibl_enabled)
        bg: Dict[str, Any] = {}
        if "background_mode" in env:
            bg["mode"] = env.get("background_mode")
        if "background_color" in env:
            bg["color"] = env.get("background_color")
        if "ibl_enabled" in env:
            # Не связываем фон с IBL — только skybox_enabled по желанию
            pass
        if bg:
            payload["background"] = bg

        # IBL (независимо от background)
        ibl: Dict[str, Any] = {}
        if "ibl_enabled" in env:
            ibl["enabled"] = bool(env.get("ibl_enabled"))
            # По умолчанию зеркалим в lighting_enabled, а background_enabled не трогаем
            ibl["lighting_enabled"] = ibl["enabled"]
        if "ibl_intensity" in env:
            ibl["intensity"] = env.get("ibl_intensity")
        if "ibl_source" in env:
            ibl["source"] = env.get("ibl_source")
        if "ibl_fallback" in env:
            ibl["fallback"] = env.get("ibl_fallback")
        # Новые параметры позиционирования окружения
        if "ibl_offset_x" in env:
            ibl["offset_x"] = env.get("ibl_offset_x")
        if "ibl_offset_y" in env:
            ibl["offset_y"] = env.get("ibl_offset_y")
        if "ibl_bind_to_camera" in env:
            ibl["bind_to_camera"] = bool(env.get("ibl_bind_to_camera"))
        if ibl:
            payload["ibl"] = ibl

        # fog
        fog: Dict[str, Any] = {}
        if "fog_enabled" in env:
            fog["enabled"] = bool(env.get("fog_enabled"))
        if "fog_color" in env:
            fog["color"] = env.get("fog_color")
        if "fog_density" in env:
            fog["density"] = env.get("fog_density")
        if "fog_near" in env:
            fog["near"] = env.get("fog_near")
        if "fog_far" in env:
            fog["far"] = env.get("fog_far")
        if fog:
            payload["fog"] = fog

        # ambient occlusion
        ao: Dict[str, Any] = {}
        if "ao_enabled" in env:
            ao["enabled"] = bool(env.get("ao_enabled"))
        if "ao_strength" in env:
            ao["strength"] = env.get("ao_strength")
        if "ao_radius" in env:
            ao["radius"] = env.get("ao_radius")
        if ao:
            payload["ambient_occlusion"] = ao

        return payload

    def _update_environment(self, key: str, value: Any) -> None:
        """Update environment parameter"""
        if self._updating_ui:
            return 
        
        # Сохраняем старое значение для логирования
        old_value = self.state["environment"].get(key)
        
        self.state["environment"][key] = value
        
        # Логируем изменение
        self.graphics_logger.log_change(
            parameter_name=key,
            old_value=old_value,
            new_value=value,
            category="environment",
            panel_state=self.state
        )
        
        self._emit_environment()

    # ------------------------------------------------------------------
    # Settings persistence
    # ------------------------------------------------------------------
    @Slot()
    def save_settings(self) -> None:
        """Save current settings to QSettings"""
        try:
            for category, data in self.state.items():
                self.settings.setValue(f"state/{category}", json.dumps(data))
            self.settings.sync()
            self.logger.info("Graphics settings saved")
        except Exception as e:
            self.logger.error(f"Failed to save settings: {e}")

    @Slot()
    def load_settings(self) -> None:
        """Load settings from QSettings"""
        try:
            for category in self.state.keys():
                value = self.settings.value(f"state/{category}")
                if value:
                    try:
                        loaded = json.loads(value)
                        self._deep_update(self.state[category], loaded)
                    except json.JSONDecodeError as e:
                        self.logger.warning(f"Failed to parse {category} settings: {e}")
            self.logger.info("Graphics settings loaded")
        except Exception as e:
            self.logger.error(f"Failed to load settings: {e}")

    @Slot()
    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults"""
        self.logger.info("🔄 Resetting all graphics settings to defaults")
        
        # Логируем сброс
        self.graphics_logger.log_change(
            parameter_name="RESET_ALL",
            old_value=copy.deepcopy(self.state),
            new_value=copy.deepcopy(self._defaults),
            category="system",
            panel_state=self._defaults
        )
        
        self.state = copy.deepcopy(self._defaults)
        self._apply_state_to_ui()
        self._emit_all()
        self.preset_applied.emit("Сброс к значениям по умолчанию")

    # ------------------------------------------------------------------
    # UI state synchronization
    # ------------------------------------------------------------------
    def _apply_state_to_ui(self) -> None:
        """Apply current state to all UI controls"""
        # ✅ CRITICAL FIX: Блокируем все сигналы во время обновления UI
        # Это предотвращает множественные вызовы обработчиков
        self._updating_ui = True
        
        # Дополнительно блокируем сигналы на уровне Qt
        self.blockSignals(True)
        
        try:
            self._apply_lighting_ui()
            self._apply_environment_ui()
            self._apply_quality_ui()
            self._apply_camera_ui()
            self._apply_effects_ui()
            self._on_material_selection_changed()
        finally:
            # ✅ CRITICAL: Всегда разблокируем сигналы
            self.blockSignals(False)
            self._updating_ui = False

    def _apply_lighting_ui(self) -> None:
        for group, values in self.state["lighting"].items():
            for key, value in values.items():
                control = self._lighting_controls.get(f"{group}.{key}")
                if isinstance(control, ColorButton):
                    control.set_color(value)
                elif isinstance(control, LabeledSlider):
                    control.set_value(value)
                elif isinstance(control, QCheckBox):
                    control.setChecked(bool(value))

    def _apply_environment_ui(self) -> None:
        mode_combo = self._environment_controls.get("combined.mode")
        if isinstance(mode_combo, QComboBox):
            ibl_on = bool(self.state["environment"].get("ibl_enabled", True))
            bg_mode = self.state["environment"].get("background_mode", "skybox")
            target = (ibl_on, bg_mode)
            # Найти по кортежу
            for i in range(mode_combo.count()):
                if mode_combo.itemData(i) == target:
                    mode_combo.setCurrentIndex(i)
                    break

        bg_button = self._environment_controls.get("background.color")
        if isinstance(bg_button, ColorButton):
            bg_button.set_color(self.state["environment"]["background_color"])

        ibl_check = self._environment_controls.get("ibl.enabled")
        if isinstance(ibl_check, QCheckBox):
            ibl_check.setChecked(self.state["environment"]["ibl_enabled"])

        ibl_intensity = self._environment_controls.get("ibl.intensity")
        if isinstance(ibl_intensity, LabeledSlider):
            ibl_intensity.set_value(self.state["environment"]["ibl_intensity"])

        skybox_blur = self._environment_controls.get("skybox.blur")
        if isinstance(skybox_blur, LabeledSlider):
            skybox_blur.set_value(self.state["environment"]["skybox_blur"])

        fog_enabled = self._environment_controls.get("fog.enabled")
        if isinstance(fog_enabled, QCheckBox):
            fog_enabled.setChecked(self.state["environment"]["fog_enabled"])

        fog_color = self._environment_controls.get("fog.color")
        if isinstance(fog_color, ColorButton):
            fog_color.set_color(self.state["environment"]["fog_color"])

        fog_density = self._environment_controls.get("fog.density")
        if isinstance(fog_density, LabeledSlider):
            fog_density.set_value(self.state["environment"]["fog_density"])

        fog_near = self._environment_controls.get("fog.near")
        if isinstance(fog_near, LabeledSlider):
            fog_near.set_value(self.state["environment"]["fog_near"])

        fog_far = self._environment_controls.get("fog.far")
        if isinstance(fog_far, LabeledSlider):
            fog_far.set_value(self.state["environment"]["fog_far"])

        # ✅ FIXED: Заменено 'this' на 'self'
        ao_enabled = self._environment_controls.get("ao.enabled")
        if isinstance(ao_enabled, QCheckBox):
            ao_enabled.setChecked(self.state["environment"]["ao_enabled"])

        ao_strength = self._environment_controls.get("ao.strength")
        if isinstance(ao_strength, LabeledSlider):
            ao_strength.set_value(self.state["environment"]["ao_strength"])

        ao_radius = self._environment_controls.get("ao.radius")
        if isinstance(ao_radius, LabeledSlider):
            ao_radius.set_value(self.state["environment"]["ao_radius"])

        hdr_combo = self._environment_controls.get("ibl.file")
        if isinstance(hdr_combo, QComboBox):
            current = self.state["environment"].get("ibl_source")
            if current:
                for i in range(hdr_combo.count()):
                    if hdr_combo.itemData(i) == current:
                        hdr_combo.setCurrentIndex(i)
                        break

        off_x = self._environment_controls.get("ibl.offset_x")
        if isinstance(off_x, LabeledSlider):
            off_x.set_value(self.state["environment"].get("ibl_offset_x", 0.0))
        off_y = self._environment_controls.get("ibl.offset_y")
        if isinstance(off_y, LabeledSlider):
            off_y.set_value(self.state["environment"].get("ibl_offset_y", 0.0))
        bind = self._environment_controls.get("ibl.bind")
        if isinstance(bind, QCheckBox):
            bind.setChecked(bool(self.state["environment"].get("ibl_bind_to_camera", False)))

    def _apply_quality_ui(self) -> None:
        self._sync_quality_preset_ui()
        
        shadows_enabled = self._quality_controls.get("shadows.enabled")
        if isinstance(shadows_enabled, QCheckBox):
            shadows_enabled.setChecked(self.state["quality"]["shadows"]["enabled"])

        shadows_res = self._quality_controls.get("shadows.resolution")
        if isinstance(shadows_res, QComboBox):
            index = shadows_res.findData(self.state["quality"]["shadows"]["resolution"])
            if index >= 0:
                shadows_res.setCurrentIndex(index)

        shadows_filter = self._quality_controls.get("shadows.filter")
        if isinstance(shadows_filter, QComboBox):
            index = shadows_filter.findData(self.state["quality"]["shadows"]["filter"])
            if index >= 0:
                shadows_filter.setCurrentIndex(index)

        shadows_bias = self._quality_controls.get("shadows.bias")
        if isinstance(shadows_bias, LabeledSlider):
            shadows_bias.set_value(self.state["quality"]["shadows"]["bias"])

        shadows_darkness = self._quality_controls.get("shadows.darkness")
        if isinstance(shadows_darkness, LabeledSlider):
            shadows_darkness.set_value(self.state["quality"]["shadows"]["darkness"])

        aa_primary = self._quality_controls.get("aa.primary")
        if isinstance(aa_primary, QComboBox):
            index = aa_primary.findData(self.state["quality"]["antialiasing"]["primary"])
            if index >= 0:
                aa_primary.setCurrentIndex(index)

        aa_quality = self._quality_controls.get("aa.quality")
        if isinstance(aa_quality, QComboBox):
            index = aa_quality.findData(self.state["quality"]["antialiasing"]["quality"])
            if index >= 0:
                aa_quality.setCurrentIndex(index)

        aa_post = self._quality_controls.get("aa.post")
        if isinstance(aa_post, QComboBox):
            index = aa_post.findData(self.state["quality"]["antialiasing"]["post"])
            if index >= 0:
                aa_post.setCurrentIndex(index)

        taa_check = self._quality_controls.get("taa.enabled")
        if isinstance(taa_check, QCheckBox):
            taa_check.setChecked(self.state["quality"]["taa_enabled"])

        taa_strength = self._quality_controls.get("taa.strength")
        if isinstance(taa_strength, LabeledSlider):
            taa_strength.set_value(self.state["quality"]["taa_strength"])

        taa_motion = self._quality_controls.get("taa_motion_adaptive")
        if isinstance(taa_motion, QCheckBox):
            taa_motion.setChecked(self.state["quality"]["taa_motion_adaptive"])

        fxaa_check = self._quality_controls.get("fxaa.enabled")
        if isinstance(fxaa_check, QCheckBox):
            fxaa_check.setChecked(self.state["quality"]["fxaa_enabled"])

        specular_check = self._quality_controls.get("specular.enabled")
        if isinstance(specular_check, QCheckBox):
            specular_check.setChecked(self.state["quality"]["specular_aa"])

        dithering_check = self._quality_controls.get("dithering.enabled")
        if isinstance(dithering_check, QCheckBox):
            dithering_check.setChecked(self.state["quality"]["dithering"])

        render_scale = self._quality_controls.get("render.scale")
        if isinstance(render_scale, LabeledSlider):
            render_scale.set_value(self.state["quality"]["render_scale"])

        render_policy = self._quality_controls.get("render.policy")
        if isinstance(render_policy, QComboBox):
            index = render_policy.findData(self.state["quality"]["render_policy"])
            if index >= 0:
                render_policy.setCurrentIndex(index)

        frame_limit = self._quality_controls.get("frame_rate_limit")
        if isinstance(frame_limit, LabeledSlider):
            frame_limit.set_value(self.state["quality"]["frame_rate_limit"])

        oit_check = self._quality_controls.get("oit.enabled")
        if isinstance(oit_check, QCheckBox):
            oit_check.setChecked(self.state["quality"]["oit"] == "weighted")

    def _apply_camera_ui(self) -> None:
        fov = self._camera_controls.get("fov")
        if isinstance(fov, LabeledSlider):
            fov.set_value(self.state["camera"]["fov"])

        near = self._camera_controls.get("near")
        if isinstance(near, LabeledSlider):
            near.set_value(self.state["camera"]["near"])

        far = self._camera_controls.get("far")
        if isinstance(far, LabeledSlider):
            far.set_value(self.state["camera"]["far"])

        speed = self._camera_controls.get("speed")
        if isinstance(speed, LabeledSlider):
            speed.set_value(self.state["camera"]["speed"])

        auto_rotate = self._camera_controls.get("auto_rotate")
        if isinstance(auto_rotate, QCheckBox):
            auto_rotate.setChecked(self.state["camera"]["auto_rotate"])

        rotate_speed = self._camera_controls.get("auto_rotate_speed")
        if isinstance(rotate_speed, LabeledSlider):
            rotate_speed.set_value(self.state["camera"]["auto_rotate_speed"])

    def _apply_effects_ui(self) -> None:
        bloom_enabled = self._effects_controls.get("bloom.enabled")
        if isinstance(bloom_enabled, QCheckBox):
            bloom_enabled.setChecked(self.state["effects"]["bloom_enabled"])

        bloom_intensity = self._effects_controls.get("bloom.intensity")
        if isinstance(bloom_intensity, LabeledSlider):
            bloom_intensity.set_value(self.state["effects"]["bloom_intensity"])

        bloom_threshold = self._effects_controls.get("bloom.threshold")
        if isinstance(bloom_threshold, LabeledSlider):
            bloom_threshold.set_value(self.state["effects"]["bloom_threshold"])

        bloom_spread = self._effects_controls.get("bloom.spread")
        if isinstance(bloom_spread, LabeledSlider):
            bloom_spread.set_value(self.state["effects"]["bloom_spread"])

        tonemap_enabled = self._effects_controls.get("tonemap.enabled")
        if isinstance(tonemap_enabled, QCheckBox):
            tonemap_enabled.setChecked(self.state["effects"]["tonemap_enabled"])

        tonemap_mode = self._effects_controls.get("tonemap.mode")
        if isinstance(tonemap_mode, QComboBox):
            index = tonemap_mode.findData(self.state["effects"]["tonemap_mode"])
            if index >= 0:
                tonemap_mode.setCurrentIndex(index)

        dof_enabled = self._effects_controls.get("dof.enabled")
        if isinstance(dof_enabled, QCheckBox):
            dof_enabled.setChecked(self.state["effects"]["depth_of_field"])

        dof_focus = self._effects_controls.get("dof.focus")
        if isinstance(dof_focus, LabeledSlider):
            dof_focus.set_value(self.state["effects"]["dof_focus_distance"])

        dof_blur = self._effects_controls.get("dof.blur")
        if isinstance(dof_blur, LabeledSlider):
            dof_blur.set_value(self.state["effects"]["dof_blur"])

        motion_enabled = self._effects_controls.get("motion.enabled")
        if isinstance(motion_enabled, QCheckBox):
            motion_enabled.setChecked(self.state["effects"]["motion_blur"])

        motion_amount = self._effects_controls.get("motion.amount")
        if isinstance(motion_amount, LabeledSlider):
            motion_amount.set_value(self.state["effects"]["motion_blur_amount"])

        lens_flare = self._effects_controls.get("lens_flare.enabled")
        if isinstance(lens_flare, QCheckBox):
            lens_flare.setChecked(self.state["effects"]["lens_flare"])

        vignette = self._effects_controls.get("vignette.enabled")
        if isinstance(vignette, QCheckBox):
            vignette.setChecked(self.state["effects"]["vignette"])

        vignette_strength = self._effects_controls.get("vignette.strength")
        if isinstance(vignette_strength, LabeledSlider):
            vignette_strength.set_value(self.state["effects"]["vignette_strength"])

    # ------------------------------------------------------------------
    # Utility methods
    # ------------------------------------------------------------------
    def _sync_taa_controls(self) -> None:
        primary = self.state["quality"]["antialiasing"]["primary"]
        allow_taa = primary != "msaa"
        
        taa_check = self._quality_controls.get("taa.enabled")
        if isinstance(taa_check, QCheckBox):
            taa_check.setEnabled(allow_taa)
            
        taa_strength = self._quality_controls.get("taa.strength")
        if isinstance(taa_strength, LabeledSlider):
            taa_strength.set_enabled(allow_taa)
            
        taa_motion = self._quality_controls.get("taa_motion_adaptive")
        if isinstance(taa_motion, QCheckBox):
            taa_motion.setEnabled(allow_taa)

    def _normalise_quality_state(self) -> None:
        """Ensure quality state has all required keys"""
        if "shadows" not in self.state["quality"]:
            self.state["quality"]["shadows"] = {}
        if "antialiasing" not in self.state["quality"]:
            self.state["quality"]["antialiasing"] = {}

    @staticmethod
    def _deep_update(target: Dict[str, Any], source: Dict[str, Any]) -> None:
        """Deep update dictionary recursively"""
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                GraphicsPanel._deep_update(target[key], value)
            else:
                target[key] = value

    def closeEvent(self, event) -> None:
        """Обработка закрытия панели"""
        self.logger.info("🛑 GraphicsPanel closing, exporting analysis...")
        # Сохраняем настройки пользователя автоматически
        try:
            self.save_settings()
        except Exception as e:
            self.logger.error(f"Failed to auto-save settings on close: {e}")
         
         # Экспортируем финальный отчет
        try:
            report_path = self.graphics_logger.export_analysis_report()
            self.logger.info(f"   ✅ Analysis report saved: {report_path}")
        except Exception as e:
            self.logger.error(f"   ❌ Failed to export analysis: {e}")
        
        super().closeEvent(event)
    
    def export_sync_analysis(self) -> None:
        """Экспортировать анализ синхронизации Python-QML"""
        try:
            report_path = self.graphics_logger.export_analysis_report()
            self.logger.info(f"📄 Sync analysis exported: {report_path}")
            
            # Получаем анализ
            analysis = self.graphics_logger.analyze_qml_sync()
            
            # Выводим краткую статистику
            print("\n" + "="*60)
            print("📊 GRAPHICS SYNC ANALYSIS")
            print("="*60)
            print(f"Total changes: {analysis.get('total_events', 0)}")
            print(f"Successful QML updates: {analysis.get('successful_updates', 0)}")
            print(f"Failed QML updates: {analysis.get('failed_updates', 0)}")
            print(f"Sync rate: {analysis.get('sync_rate', 0):.1f}%")
            print("\nBy category:")
            for cat, stats in analysis.get('by_category', {}).items():
                print(f"  {cat}: {stats['total']} changes, {stats['successful']} synced")
            
            if analysis.get('errors_by_parameter'):
                print("\n⚠️ Parameters with errors:")
                for param, errors in analysis['errors_by_parameter'].items():
                    print(f"  {param}: {len(errors)} error(s)")
            
            print("="*60)
            print(f"Full report: {report_path}")
            print("="*60 + "\n")
            
        except Exception as e:
            self.logger.error(f"Failed to export sync analysis: {e}")
