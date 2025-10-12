"""Graphics panel providing exhaustive Qt Quick 3D controls."""
from __future__ import annotations

import copy
import json
import logging
from typing import Any, Dict

from PySide6.QtCore import QSettings, Qt, QTimer, Signal, Slot
from PySide6.QtGui import QColor, QStandardItem
from PySide6.QtWidgets import (
    QCheckBox,
    QColorDialog,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
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


class ColorButton(QPushButton):
    """Small color preview button that streams changes from QColorDialog."""

    color_changed = Signal(str)

    def __init__(self, initial_color: str = "#ffffff", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(42, 28)
        self._color = QColor(initial_color)
        self._dialog = None
        self._update_swatch()
        self.clicked.connect(self._open_dialog)

    def color(self) -> QColor:
        return self._color

    def set_color(self, color_str: str) -> None:
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
        self.color_changed.emit(color.name())

    @Slot()
    def _close_dialog(self) -> None:
        if self._dialog:
            self._dialog.deleteLater()
        self._dialog = None


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

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self._label = QLabel(self)
        layout.addWidget(self._label)

        row = QHBoxLayout()
        row.setContentsMargins(0, 0, 0, 0)
        row.setSpacing(6)
        layout.addLayout(row)

        self._slider = QSlider(Qt.Horizontal, self)
        steps = max(1, int(round((self._max - self._min) / self._step)))
        self._slider.setRange(0, steps)
        self._slider.valueChanged.connect(self._handle_slider)
        row.addWidget(self._slider, 1)

        self._spin = QDoubleSpinBox(self)
        self._spin.setDecimals(self._decimals)
        self._spin.setRange(self._min, self._max)
        self._spin.setSingleStep(self._step)
        self._spin.valueChanged.connect(self._handle_spin)
        row.addWidget(self._spin)

        self.set_value(self._min)

    def set_enabled(self, enabled: bool) -> None:
        self.setEnabled(enabled)

    def value(self) -> float:
        return round(self._spin.value(), self._decimals)

    def set_value(self, value: float) -> None:
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
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.settings = QSettings("PneumoStabSim", "GraphicsPanel")
        self._updating_ui = False

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
                "key": {"brightness": 1.2, "color": "#ffffff", "angle_x": -35.0, "angle_y": -40.0},
                "fill": {"brightness": 0.7, "color": "#dfe7ff"},
                "rim": {"brightness": 1.0, "color": "#ffe2b0"},
                "point": {"brightness": 1500.0, "color": "#ffffff", "height": 2200.0, "range": 3200.0},
            },
            "environment": {
                "background_mode": "skybox",
                "background_color": "#1f242c",
                "ibl_enabled": True,
                "ibl_intensity": 1.3,
                "ibl_source": "../hdr/studio.hdr",
                "ibl_fallback": "assets/studio_small_09_2k.hdr",
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
                "lens_flare": True,
                "vignette": True,
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

        save_btn = QPushButton("💾 Сохранить", self)
        save_btn.clicked.connect(self.save_settings)
        button_row.addWidget(save_btn)

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

        height_slider = LabeledSlider("Высота", 0.0, 5000.0, 10.0, decimals=1, unit="мм")
        height_slider.valueChanged.connect(lambda v: self._update_lighting("point", "height", v))
        self._lighting_controls["point.height"] = height_slider
        grid.addWidget(height_slider, 2, 0, 1, 2)

        range_slider = LabeledSlider("Радиус действия", 200.0, 5000.0, 10.0, decimals=1, unit="мм")
        range_slider.valueChanged.connect(lambda v: self._update_lighting("point", "range", v))
        self._lighting_controls["point.range"] = range_slider
        grid.addWidget(range_slider, 3, 0, 1, 2)
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
        group = QGroupBox("Фон и HDR", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        mode_combo = QComboBox(self)
        mode_combo.addItem("Сплошной цвет", "color")
        mode_combo.addItem("Skybox / HDR", "skybox")
        mode_combo.currentIndexChanged.connect(lambda _: self._update_environment("background_mode", mode_combo.currentData()))
        self._environment_controls["background.mode"] = mode_combo
        grid.addWidget(QLabel("Режим фона", self), 0, 0)
        grid.addWidget(mode_combo, 0, 1)

        bg_row = QHBoxLayout()
        bg_row.addWidget(QLabel("Цвет", self))
        bg_button = ColorButton()
        bg_button.color_changed.connect(lambda c: self._update_environment("background_color", c))
        self._environment_controls["background.color"] = bg_button
        bg_row.addWidget(bg_button)
        bg_row.addStretch(1)
        grid.addLayout(bg_row, 1, 0, 1, 2)

        ibl_check = QCheckBox("Включить HDR IBL", self)
        ibl_check.stateChanged.connect(lambda state: self._update_environment("ibl_enabled", state == Qt.Checked))
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

        choose_hdr = QPushButton("Загрузить HDR…", self)
        choose_hdr.clicked.connect(self._choose_hdr_file)
        grid.addWidget(choose_hdr, 5, 0)

        path_label = QLabel("", self)
        path_label.setWordWrap(True)
        self._environment_controls["ibl.path_label"] = path_label
        grid.addWidget(path_label, 5, 1)
        return group

    def _build_fog_group(self) -> QGroupBox:
        group = QGroupBox("Туман", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        enabled = QCheckBox("Включить туман", self)
        enabled.stateChanged.connect(lambda state: self._update_environment("fog_enabled", state == Qt.Checked))
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
        enabled.stateChanged.connect(lambda state: self._update_environment("ao_enabled", state == Qt.Checked))
        self._environment_controls["ao.enabled"] = enabled
        grid.addWidget(enabled, 0, 0, 1, 2)

        strength = LabeledSlider("Интенсивность", 0.0, 2.0, 0.02, decimals=2)
        strength.valueChanged.connect(lambda v: self._update_environment("ao_strength", v))
        self._environment_controls["ao.strength"] = strength
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
        enabled.stateChanged.connect(lambda state: self._update_quality("shadows.enabled", state == Qt.Checked))
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
        taa_check.stateChanged.connect(lambda state: self._update_quality("taa.enabled", state == Qt.Checked))
        self._quality_controls["taa.enabled"] = taa_check
        grid.addWidget(taa_check, 3, 0, 1, 2)

        taa_strength = LabeledSlider("Сила TAA", 0.0, 1.0, 0.01, decimals=2)
        taa_strength.valueChanged.connect(lambda v: self._update_quality("taa.strength", v))
        self._quality_controls["taa.strength"] = taa_strength
        grid.addWidget(taa_strength, 4, 0, 1, 2)

        fxaa_check = QCheckBox("Включить FXAA", self)
        fxaa_check.stateChanged.connect(lambda state: self._update_quality("fxaa_enabled", state == Qt.Checked))
        self._quality_controls["fxaa.enabled"] = fxaa_check
        grid.addWidget(fxaa_check, 5, 0, 1, 2)

        specular_check = QCheckBox("Specular AA", self)
        specular_check.stateChanged.connect(lambda state: self._update_quality("specular_aa", state == Qt.Checked))
        self._quality_controls["specular.enabled"] = specular_check
        grid.addWidget(specular_check, 6, 0, 1, 2)

        dithering_check = QCheckBox("Dithering", self)
        dithering_check.stateChanged.connect(lambda state: self._update_quality("dithering", state == Qt.Checked))
        self._quality_controls["dithering.enabled"] = dithering_check
        grid.addWidget(dithering_check, 7, 0, 1, 2)
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
        oit_check.stateChanged.connect(lambda state: self._update_quality("oit", "weighted" if state == Qt.Checked else "none"))
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
        auto_rotate.stateChanged.connect(lambda state: self._update_camera("auto_rotate", state == Qt.Checked))
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
        self.state["materials"][key][prop] = color
        self._emit_material_update(key)

    def _on_material_value_changed(self, prop: str, value: float) -> None:
        if self._updating_ui:
            return
        key = self._current_material_key()
        if not key or prop not in self.state["materials"].get(key, {}):
            return
        self.state["materials"][key][prop] = value
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
        enabled.stateChanged.connect(lambda state: self._update_effects("bloom_enabled", state == Qt.Checked))
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
        enabled.stateChanged.connect(lambda state: self._update_effects("tonemap_enabled", state == Qt.Checked))
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
        enabled.stateChanged.connect(lambda state: self._update_effects("depth_of_field", state == Qt.Checked))
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
        motion.stateChanged.connect(lambda state: self._update_effects("motion_blur", state == Qt.Checked))
        self._effects_controls["motion.enabled"] = motion
        grid.addWidget(motion, 0, 0, 1, 2)

        motion_strength = LabeledSlider("Сила размытия", 0.0, 1.0, 0.02, decimals=2)
        motion_strength.valueChanged.connect(lambda v: self._update_effects("motion_blur_amount", v))
        self._effects_controls["motion.amount"] = motion_strength
        grid.addWidget(motion_strength, 1, 0, 1, 2)

        lens_flare = QCheckBox("Линзовые блики", self)
        lens_flare.stateChanged.connect(lambda state: self._update_effects("lens_flare", state == Qt.Checked))
        self._effects_controls["lens_flare.enabled"] = lens_flare
        grid.addWidget(lens_flare, 2, 0, 1, 2)

        vignette = QCheckBox("Виньетирование", self)
        vignette.stateChanged.connect(lambda state: self._update_effects("vignette", state == Qt.Checked))
        self._effects_controls["vignette.enabled"] = vignette
        grid.addWidget(vignette, 3, 0, 1, 2)

        vignette_strength = LabeledSlider("Сила виньетки", 0.0, 1.0, 0.02, decimals=2)
        vignette_strength.valueChanged.connect(lambda v: self._update_effects("vignette_strength", v))
        self._effects_controls["vignette.strength"] = vignette_strength
        grid.addWidget(vignette_strength, 4, 0, 1, 2)
        return group

    # ------------------------------------------------------------------
    # State update helpers
    # ------------------------------------------------------------------
    def _update_lighting(self, group: str, key: str, value: Any) -> None:
        if self._updating_ui:
            return
        self.state["lighting"][group][key] = value
        self._emit_lighting()

    def _apply_lighting_preset(self, preset: Dict[str, Dict[str, Any]], name: str) -> None:
        self._updating_ui = True
        try:
            for group, values in preset.items():
                if group not in self.state["lighting"]:
                    continue
                for key, value in values.items():
                    self.state["lighting"][group][key] = value
                    control = self._lighting_controls.get(f"{group}.{key}")
                    if isinstance(control, ColorButton):
                        control.set_color(value)
                    elif isinstance(control, LabeledSlider):
                        control.set_value(value)
        finally:
            self._updating_ui = False
        self._emit_lighting()
        self.preset_applied.emit(name)

    def _update_environment(self, key: str, value: Any) -> None:
        if self._updating_ui:
            return
        self.state["environment"][key] = value
        if key in {"ibl_source", "ibl_fallback"}:
            label: QLabel = self._environment_controls.get("ibl.path_label")  # type: ignore[assignment]
            if isinstance(label, QLabel):
                label.setText(value)
        self._emit_environment()

    def _choose_hdr_file(self) -> None:
        filename, _ = QFileDialog.getOpenFileName(self, "Выбрать HDR", "", "HDR Images (*.hdr *.exr)")
        if filename:
            self._update_environment("ibl_source", filename)

    def _update_quality(self, path: str, value: Any) -> None:
        if self._updating_ui:
            return

        if path == "taa.enabled":
            self.state["quality"]["taa_enabled"] = bool(value)
        elif path == "taa.strength":
            self.state["quality"]["taa_strength"] = float(value)
        else:
            parts = path.split(".")
            target = self.state["quality"]
            for part in parts[:-1]:
                target = target.setdefault(part, {})  # type: ignore[assignment]
            target[parts[-1]] = value

        self._set_quality_custom()
        self._apply_quality_constraints()
        self._sync_quality_preset_ui()
        self._emit_quality()

    def _on_primary_aa_changed(self, mode: str) -> None:
        if self._updating_ui:
            return
        self.state["quality"]["antialiasing"]["primary"] = mode
        self._set_quality_custom()
        self._apply_quality_constraints()
        self._sync_quality_preset_ui()
        self._emit_quality()

    def _apply_quality_constraints(self) -> None:
        self._normalise_quality_state()

        primary = self.state["quality"]["antialiasing"]["primary"]
        post = self.state["quality"]["antialiasing"].get("post", "off")
        changed = False
        if primary == "msaa" and post == "taa":
            self.state["quality"]["antialiasing"]["post"] = "off"
            changed = True
        if primary == "msaa" and self.state["quality"].get("taa_enabled"):
            self.state["quality"]["taa_enabled"] = False
            changed = True
        if changed:
            self._set_quality_custom()

        self._update_post_aa_options()
        self._sync_taa_controls()

    def _update_post_aa_options(self) -> None:
        combo: QComboBox = self._quality_controls.get("aa.post")  # type: ignore[assignment]
        if not isinstance(combo, QComboBox):
            return
        allow_taa = self.state["quality"]["antialiasing"]["primary"] != "msaa"
        index = combo.findData("taa")
        if index >= 0 and hasattr(combo.model(), "item"):
            item = combo.model().item(index)  # type: ignore[assignment]
            if isinstance(item, QStandardItem):
                item.setEnabled(allow_taa)
        if not allow_taa and combo.currentData() == "taa":
            fallback = combo.findData("off")
            if fallback >= 0:
                combo.setCurrentIndex(fallback)
            self.state["quality"]["antialiasing"]["post"] = "off"
            self._set_quality_custom()
        self._sync_taa_controls()

    def _update_camera(self, key: str, value: Any) -> None:
        if self._updating_ui:
            return
        self.state["camera"][key] = value
        self._emit_camera()

    def _update_effects(self, key: str, value: Any) -> None:
        if self._updating_ui:
            return
        self.state["effects"][key] = value
        self._sync_effect_enablers()
        self._emit_effects()

    def _sync_effect_enablers(self) -> None:
        motion_slider = self._effects_controls.get("motion.amount")
        if isinstance(motion_slider, LabeledSlider):
            motion_slider.set_enabled(self.state["effects"].get("motion_blur", False))
        dof_focus = self._effects_controls.get("dof.focus")
        dof_blur = self._effects_controls.get("dof.blur")
        enabled = self.state["effects"].get("depth_of_field", False)
        if isinstance(dof_focus, LabeledSlider):
            dof_focus.set_enabled(enabled)
        if isinstance(dof_blur, LabeledSlider):
            dof_blur.set_enabled(enabled)

        tonemap_combo = self._effects_controls.get("tonemap.mode")
        if isinstance(tonemap_combo, QComboBox):
            tonemap_combo.setEnabled(self.state["effects"].get("tonemap_enabled", True))

    # ------------------------------------------------------------------
    # Emitters
    # ------------------------------------------------------------------
    def _emit_lighting(self) -> None:
        data = self.state["lighting"]
        payload = {
            "key_light": {
                "brightness": data["key"]["brightness"],
                "color": data["key"]["color"],
                "angle_x": data["key"]["angle_x"],
                "angle_y": data["key"]["angle_y"],
            },
            "fill_light": {
                "brightness": data["fill"]["brightness"],
                "color": data["fill"]["color"],
            },
            "rim_light": {
                "brightness": data["rim"]["brightness"],
                "color": data["rim"]["color"],
            },
            "point_light": {
                "brightness": data["point"]["brightness"],
                "color": data["point"]["color"],
                "position_y": data["point"]["height"],
                "range": data["point"]["range"],
            },
        }
        self.lighting_changed.emit(payload)

    def _emit_environment(self) -> None:
        env = self.state["environment"]
        payload = {
            "background": {
                "mode": env["background_mode"],
                "color": env["background_color"],
            },
            "ibl": {
                "enabled": env["ibl_enabled"],
                "intensity": env["ibl_intensity"],
                "source": env["ibl_source"],
                "fallback": env["ibl_fallback"],
                "blur": env["skybox_blur"],
            },
            "fog": {
                "enabled": env["fog_enabled"],
                "color": env["fog_color"],
                "density": env["fog_density"],
                "near": env["fog_near"],
                "far": env["fog_far"],
            },
            "ambient_occlusion": {
                "enabled": env["ao_enabled"],
                "strength": env["ao_strength"],
                "radius": env["ao_radius"],
            },
        }
        self.environment_changed.emit(payload)

    def _emit_quality(self) -> None:
        q = self.state["quality"]
        payload = {
            "shadows": copy.deepcopy(q["shadows"]),
            "antialiasing": copy.deepcopy(q["antialiasing"]),
            "taa_enabled": q["taa_enabled"],
            "taa_strength": q["taa_strength"],
            "fxaa_enabled": q["fxaa_enabled"],
            "specular_aa": q["specular_aa"],
            "dithering": q["dithering"],
            "render_scale": q["render_scale"],
            "render_policy": q["render_policy"],
            "frame_rate_limit": q["frame_rate_limit"],
            "oit": q["oit"],
            "preset": q.get("preset", "custom"),
        }
        self.quality_changed.emit(payload)

    def _emit_camera(self) -> None:
        self.camera_changed.emit(copy.deepcopy(self.state["camera"]))

    def _emit_effects(self) -> None:
        self.effects_changed.emit(copy.deepcopy(self.state["effects"]))

    def _emit_material_update(self, key: str) -> None:
        self.material_changed.emit({key: copy.deepcopy(self.state["materials"][key])})

    def _emit_all(self) -> None:
        self._emit_lighting()
        self._emit_environment()
        self._emit_quality()
        self._emit_camera()
        self._emit_effects()
        for key in self.state["materials"].keys():
            self._emit_material_update(key)

    # ------------------------------------------------------------------
    # UI synchronisation
    # ------------------------------------------------------------------
    def _apply_state_to_ui(self) -> None:
        self._updating_ui = True
        try:
            self._apply_lighting_ui()
            self._apply_environment_ui()
            self._apply_quality_ui()
            self._sync_quality_preset_ui()
            self._apply_camera_ui()
            self._apply_effects_ui()
            self._on_material_selection_changed()
        finally:
            self._updating_ui = False
        self._sync_effect_enablers()
        self._update_post_aa_options()
        self._sync_taa_controls()

    def _apply_lighting_ui(self) -> None:
        data = self.state["lighting"]
        for group, values in data.items():
            for key, value in values.items():
                control = self._lighting_controls.get(f"{group}.{key}")
                if isinstance(control, ColorButton):
                    control.set_color(value)
                elif isinstance(control, LabeledSlider):
                    control.set_value(value)

    def _apply_environment_ui(self) -> None:
        env = self.state["environment"]
        mode_combo: QComboBox = self._environment_controls["background.mode"]  # type: ignore[assignment]
        index = mode_combo.findData(env["background_mode"])
        if index >= 0:
            mode_combo.setCurrentIndex(index)
        bg_button: ColorButton = self._environment_controls["background.color"]  # type: ignore[assignment]
        bg_button.set_color(env["background_color"])
        ibl_check: QCheckBox = self._environment_controls["ibl.enabled"]  # type: ignore[assignment]
        ibl_check.setChecked(env["ibl_enabled"])
        self._environment_controls["ibl.intensity"].set_value(env["ibl_intensity"])  # type: ignore[index]
        self._environment_controls["skybox.blur"].set_value(env["skybox_blur"])  # type: ignore[index]
        label: QLabel = self._environment_controls["ibl.path_label"]  # type: ignore[assignment]
        label.setText(env["ibl_source"])

        fog_enabled: QCheckBox = self._environment_controls["fog.enabled"]  # type: ignore[assignment]
        fog_enabled.setChecked(env["fog_enabled"])
        self._environment_controls["fog.color"].set_color(env["fog_color"])  # type: ignore[index]
        self._environment_controls["fog.density"].set_value(env["fog_density"])  # type: ignore[index]
        self._environment_controls["fog.near"].set_value(env["fog_near"])  # type: ignore[index]
        self._environment_controls["fog.far"].set_value(env["fog_far"])  # type: ignore[index]

        ao_enabled: QCheckBox = self._environment_controls["ao.enabled"]  # type: ignore[assignment]
        ao_enabled.setChecked(env["ao_enabled"])
        self._environment_controls["ao.strength"].set_value(env["ao_strength"])  # type: ignore[index]
        self._environment_controls["ao.radius"].set_value(env["ao_radius"])  # type: ignore[index]

    def _apply_quality_ui(self) -> None:
        q = self.state["quality"]
        preset_combo: QComboBox = self._quality_controls["quality.preset"]  # type: ignore[assignment]
        index = preset_combo.findData(q.get("preset", "custom"))
        if index >= 0:
            preset_combo.setCurrentIndex(index)
        self._quality_controls["frame_rate_limit"].set_value(q["frame_rate_limit"])  # type: ignore[index]
        primary_combo: QComboBox = self._quality_controls["aa.primary"]  # type: ignore[assignment]
        index = primary_combo.findData(q["antialiasing"]["primary"])
        if index >= 0:
            primary_combo.setCurrentIndex(index)
        quality_combo: QComboBox = self._quality_controls["aa.quality"]  # type: ignore[assignment]
        index = quality_combo.findData(q["antialiasing"]["quality"])
        if index >= 0:
            quality_combo.setCurrentIndex(index)
        post_combo: QComboBox = self._quality_controls["aa.post"]  # type: ignore[assignment]
        index = post_combo.findData(q["antialiasing"].get("post", "off"))
        if index >= 0:
            post_combo.setCurrentIndex(index)

        self._quality_controls["shadows.enabled"].setChecked(q["shadows"]["enabled"])  # type: ignore[index]
        resolution_combo: QComboBox = self._quality_controls["shadows.resolution"]  # type: ignore[assignment]
        index = resolution_combo.findData(q["shadows"]["resolution"])
        if index >= 0:
            resolution_combo.setCurrentIndex(index)
        filter_combo: QComboBox = self._quality_controls["shadows.filter"]  # type: ignore[assignment]
        index = filter_combo.findData(q["shadows"]["filter"])
        if index >= 0:
            filter_combo.setCurrentIndex(index)
        self._quality_controls["shadows.bias"].set_value(q["shadows"]["bias"])  # type: ignore[index]
        self._quality_controls["shadows.darkness"].set_value(q["shadows"]["darkness"])  # type: ignore[index]

        self._quality_controls["taa.enabled"].setChecked(q["taa_enabled"])  # type: ignore[index]
        self._quality_controls["taa.strength"].set_value(q["taa_strength"])  # type: ignore[index]
        self._quality_controls["fxaa.enabled"].setChecked(q["fxaa_enabled"])  # type: ignore[index]
        self._quality_controls["specular.enabled"].setChecked(q["specular_aa"])  # type: ignore[index]
        self._quality_controls["dithering.enabled"].setChecked(q["dithering"])  # type: ignore[index]
        self._quality_controls["render.scale"].set_value(q["render_scale"])  # type: ignore[index]
        policy_combo: QComboBox = self._quality_controls["render.policy"]  # type: ignore[assignment]
        index = policy_combo.findData(q["render_policy"])
        if index >= 0:
            policy_combo.setCurrentIndex(index)
        oit_check: QCheckBox = self._quality_controls["oit.enabled"]  # type: ignore[assignment]
        oit_check.setChecked(q["oit"] == "weighted")

    def _apply_camera_ui(self) -> None:
        camera = self.state["camera"]
        self._camera_controls["fov"].set_value(camera["fov"])  # type: ignore[index]
        self._camera_controls["near"].set_value(camera["near"])  # type: ignore[index]
        self._camera_controls["far"].set_value(camera["far"])  # type: ignore[index]
        self._camera_controls["speed"].set_value(camera["speed"])  # type: ignore[index]
        auto_rotate: QCheckBox = self._camera_controls["auto_rotate"]  # type: ignore[assignment]
        auto_rotate.setChecked(camera["auto_rotate"])
        self._camera_controls["auto_rotate_speed"].set_value(camera["auto_rotate_speed"])  # type: ignore[index]

    def _apply_effects_ui(self) -> None:
        eff = self.state["effects"]
        self._effects_controls["bloom.enabled"].setChecked(eff["bloom_enabled"])  # type: ignore[index]
        self._effects_controls["bloom.intensity"].set_value(eff["bloom_intensity"])  # type: ignore[index]
        self._effects_controls["bloom.threshold"].set_value(eff["bloom_threshold"])  # type: ignore[index]
        self._effects_controls["bloom.spread"].set_value(eff["bloom_spread"])  # type: ignore[index]

        self._effects_controls["tonemap.enabled"].setChecked(eff["tonemap_enabled"])  # type: ignore[index]
        tonemap_combo: QComboBox = self._effects_controls["tonemap.mode"]  # type: ignore[assignment]
        index = tonemap_combo.findData(eff["tonemap_mode"])
        if index >= 0:
            tonemap_combo.setCurrentIndex(index)

        self._effects_controls["dof.enabled"].setChecked(eff["depth_of_field"])  # type: ignore[index]
        self._effects_controls["dof.focus"].set_value(eff["dof_focus_distance"])  # type: ignore[index]
        self._effects_controls["dof.blur"].set_value(eff["dof_blur"])  # type: ignore[index]

        self._effects_controls["motion.enabled"].setChecked(eff["motion_blur"])  # type: ignore[index]
        self._effects_controls["motion.amount"].set_value(eff["motion_blur_amount"])  # type: ignore[index]
        self._effects_controls["lens_flare.enabled"].setChecked(eff["lens_flare"])  # type: ignore[index]
        self._effects_controls["vignette.enabled"].setChecked(eff["vignette"])  # type: ignore[index]
        self._effects_controls["vignette.strength"].set_value(eff["vignette_strength"])  # type: ignore[index]

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def load_settings(self) -> None:
        raw = self.settings.value("state")
        if not raw:
            return
        try:
            data = json.loads(raw)
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.warning("Failed to parse saved graphics settings: %s", exc)
            return
        self._deep_update(self.state, data)
        for material_key in self.state["materials"].keys():
            self._ensure_material_defaults(material_key)

    def save_settings(self) -> None:
        self.settings.setValue("state", json.dumps(self.state))
        self.settings.sync()
        self.logger.info("Graphics settings saved")

    def reset_to_defaults(self) -> None:
        self.state = copy.deepcopy(self._defaults)
        for material_key in self.state["materials"].keys():
            self._ensure_material_defaults(material_key)
        self._apply_quality_constraints()
        self._apply_state_to_ui()
        self._emit_all()
        self.preset_applied.emit("Сброс")

    def _deep_update(self, target: Dict[str, Any], source: Dict[str, Any]) -> None:
        for key, value in source.items():
            if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                self._deep_update(target[key], value)  # type: ignore[arg-type]
            else:
                target[key] = value

    def _normalise_quality_state(self) -> None:
        """Collapse legacy TAA dictionaries into the flat quality structure."""

        q = self.state["quality"]
        legacy = q.pop("taa", None)
        if isinstance(legacy, dict):
            enabled = legacy.get("enabled")
            if isinstance(enabled, bool):
                q["taa_enabled"] = enabled
            strength = legacy.get("strength")
            if isinstance(strength, (int, float)):
                q["taa_strength"] = float(strength)

        defaults = self._defaults["quality"]
        for key, value in defaults.items():
            if key not in q:
                q[key] = copy.deepcopy(value) if isinstance(value, dict) else value

        if "antialiasing" not in q or not isinstance(q["antialiasing"], dict):
            q["antialiasing"] = copy.deepcopy(defaults["antialiasing"])
        else:
            q["antialiasing"].setdefault("primary", defaults["antialiasing"]["primary"])
            q["antialiasing"].setdefault("quality", defaults["antialiasing"]["quality"])
            q["antialiasing"].setdefault("post", defaults["antialiasing"]["post"])

        if "frame_rate_limit" in q:
            q["frame_rate_limit"] = max(24.0, min(240.0, float(q["frame_rate_limit"])))
        else:
            q["frame_rate_limit"] = defaults["frame_rate_limit"]

        if "preset" not in q:
            q["preset"] = "custom"
    def _sync_taa_controls(self) -> None:
        """Mirror the MSAA/TAA compatibility rules in the UI widgets."""

        allow_taa = self.state["quality"]["antialiasing"]["primary"] != "msaa"
        previous = self._updating_ui
        self._updating_ui = True
        try:
            taa_check = self._quality_controls.get("taa.enabled")
            if isinstance(taa_check, QCheckBox):
                if not allow_taa and taa_check.isChecked():
                    taa_check.setChecked(False)
                taa_check.setEnabled(allow_taa)

            taa_slider = self._quality_controls.get("taa.strength")
            if isinstance(taa_slider, LabeledSlider):
                taa_slider.set_enabled(allow_taa and self.state["quality"].get("taa_enabled", False))
        finally:
            self._updating_ui = previous
