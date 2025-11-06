# -*- coding: utf-8 -*-
"""Effects tab with full Qt 6.10 ExtendedSceneEnvironment coverage."""

from __future__ import annotations

from typing import Any, Dict

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGridLayout,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from .widgets import LabeledSlider
from src.common.logging_widgets import LoggingCheckBox


class EffectsTab(QWidget):
    """Вкладка настроек эффектов (Bloom, тонемаппинг, DoF, виньетирование)."""

    effects_changed = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._controls: Dict[str, Any] = {}
        self._state: Dict[str, Any] = {}
        self._updating_ui = False

        self._dependencies: Dict[str, tuple[str, ...]] = {
            "bloom.enabled": (
                "bloom.intensity",
                "bloom.threshold",
                "bloom.spread",
                "bloom.glow_strength",
                "bloom.hdr_max",
                "bloom.hdr_scale",
                "bloom.quality_high",
                "bloom.bicubic_upscale",
            ),
            "tonemap.enabled": (
                "tonemap.mode",
                "tonemap.exposure",
                "tonemap.white_point",
            ),
            "dof.enabled": ("dof.focus_distance", "dof.blur", "dof.auto_focus"),
            "motion.enabled": ("motion.amount",),
            "lens_flare.enabled": (
                "lens_flare.ghost_count",
                "lens_flare.ghost_dispersal",
                "lens_flare.halo_width",
                "lens_flare.bloom_bias",
                "lens_flare.stretch",
            ),
            "vignette.enabled": ("vignette.strength", "vignette.radius"),
            "color.enabled": (
                "color.brightness",
                "color.contrast",
                "color.saturation",
            ),
        }

        self._state_key_map: Dict[str, str] = {
            "bloom.enabled": "bloom_enabled",
            "bloom.intensity": "bloom_intensity",
            "bloom.threshold": "bloom_threshold",
            "bloom.spread": "bloom_spread",
            "bloom.glow_strength": "bloom_glow_strength",
            "bloom.hdr_max": "bloom_hdr_max",
            "bloom.hdr_scale": "bloom_hdr_scale",
            "bloom.quality_high": "bloom_quality_high",
            "bloom.bicubic_upscale": "bloom_bicubic_upscale",
            "tonemap.enabled": "tonemap_enabled",
            "tonemap.mode": "tonemap_mode",
            "tonemap.exposure": "tonemap_exposure",
            "tonemap.white_point": "tonemap_white_point",
            "dof.enabled": "depth_of_field",
            "dof.focus_distance": "dof_focus_distance",
            "dof.blur": "dof_blur",
            "dof.auto_focus": "dof_auto_focus",
            "motion.enabled": "motion_blur",
            "motion.amount": "motion_blur_amount",
            "lens_flare.enabled": "lens_flare",
            "lens_flare.ghost_count": "lens_flare_ghost_count",
            "lens_flare.ghost_dispersal": "lens_flare_ghost_dispersal",
            "lens_flare.halo_width": "lens_flare_halo_width",
            "lens_flare.bloom_bias": "lens_flare_bloom_bias",
            "lens_flare.stretch": "lens_flare_stretch_to_aspect",
            "vignette.enabled": "vignette",
            "vignette.strength": "vignette_strength",
            "vignette.radius": "vignette_radius",
            "color.enabled": "color_adjustments_enabled",
            "color.brightness": "adjustment_brightness",
            "color.contrast": "adjustment_contrast",
            "color.saturation": "adjustment_saturation",
        }

        self._integer_keys = {"lens_flare_ghost_count"}

        self._setup_ui()
        self._refresh_dependencies()

    # ------------------------------------------------------------------ UI
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(self._build_bloom_group())
        layout.addWidget(self._build_tonemap_group())
        layout.addWidget(self._build_dof_group())
        layout.addWidget(self._build_misc_effects_group())
        layout.addWidget(self._build_color_adjustments_group())
        layout.addStretch(1)

    def _build_bloom_group(self) -> QGroupBox:
        group = QGroupBox("Bloom", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(1, 1)

        row = 0
        row = self._add_checkbox(grid, row, "Включить Bloom", "bloom.enabled")
        row = self._add_slider(
            grid,
            row,
            "Интенсивность (glowIntensity)",
            "bloom.intensity",
            0.0,
            2.0,
            0.02,
        )
        row = self._add_slider(
            grid, row, "Порог (glowHDRMinimumValue)", "bloom.threshold", 0.0, 4.0, 0.05
        )
        row = self._add_slider(
            grid, row, "Распространение (glowBloom)", "bloom.spread", 0.0, 1.0, 0.01
        )
        row = self._add_slider(
            grid,
            row,
            "Сила свечения (glowStrength)",
            "bloom.glow_strength",
            0.0,
            2.0,
            0.02,
        )
        row = self._add_slider(
            grid, row, "HDR Maximum", "bloom.hdr_max", 0.0, 10.0, 0.1
        )
        row = self._add_slider(grid, row, "HDR Scale", "bloom.hdr_scale", 1.0, 5.0, 0.1)
        row = self._add_checkbox(
            grid, row, "Высокое качество (glowQualityHigh)", "bloom.quality_high"
        )
        self._controls["bloom.quality_high"].setToolTip(
            "Использует более качественное размытие, но требует больше ресурсов"
        )
        row = self._add_checkbox(
            grid,
            row,
            "Бикубическое увеличение (glowUseBicubicUpscale)",
            "bloom.bicubic_upscale",
        )
        return group

    def _build_tonemap_group(self) -> QGroupBox:
        group = QGroupBox("Тонемаппинг", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(1, 1)

        row = 0
        row = self._add_checkbox(grid, row, "Включить тонемаппинг", "tonemap.enabled")

        label = QLabel("Режим", self)
        grid.addWidget(label, row, 0)
        combo = QComboBox(self)
        combo.addItem("Filmic", "filmic")
        combo.addItem("ACES", "aces")
        combo.addItem("Reinhard", "reinhard")
        combo.addItem("Gamma", "gamma")
        combo.addItem("Linear (выкл.)", "linear")
        combo.currentIndexChanged.connect(
            lambda _: self._on_control_changed("tonemap.mode", combo.currentData())
        )
        self._controls["tonemap.mode"] = combo
        grid.addWidget(combo, row, 1)
        row += 1

        row = self._add_slider(
            grid, row, "Экспозиция", "tonemap.exposure", 0.1, 5.0, 0.05
        )
        row = self._add_slider(
            grid, row, "Белая точка", "tonemap.white_point", 0.5, 5.0, 0.1
        )
        return group

    def _build_dof_group(self) -> QGroupBox:
        group = QGroupBox("Depth of Field (Глубина резкости)", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(1, 1)

        row = 0
        row = self._add_checkbox(grid, row, "Включить DoF", "dof.enabled")
        auto_focus_row = self._add_checkbox(
            grid, row, "Автофокус (по дистанции камеры)", "dof.auto_focus"
        )
        self._controls["dof.auto_focus"].setToolTip(
            "При включении расстояние до объекта вычисляется автоматически на основе текущей дистанции камеры."
        )
        row = auto_focus_row
        row = self._add_slider(
            grid,
            row,
            "Фокусное расстояние",
            "dof.focus_distance",
            0.1,
            50.0,
            0.1,
            decimals=2,
        )
        row = self._add_slider(grid, row, "Размытие", "dof.blur", 0.0, 10.0, 0.1)
        return group

    def _build_misc_effects_group(self) -> QGroupBox:
        group = QGroupBox("Дополнительные эффекты", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(1, 1)

        row = 0
        row = self._add_section_label(grid, row, "Motion Blur")
        row = self._add_checkbox(grid, row, "Размытие движения", "motion.enabled")
        hint = QLabel(
            "Требует пользовательского эффекта; параметр сохраняется для совместимости.",
            self,
        )
        hint.setWordWrap(True)
        hint.setStyleSheet("color: #808080; font-size: 11px;")
        grid.addWidget(hint, row, 0, 1, 2)
        row += 1
        row = self._add_slider(
            grid, row, "Сила размытия", "motion.amount", 0.0, 1.0, 0.02
        )

        row = self._add_section_label(grid, row, "Lens Flare")
        row = self._add_checkbox(grid, row, "Линзовые блики", "lens_flare.enabled")
        row = self._add_slider(
            grid,
            row,
            "Количество призраков",
            "lens_flare.ghost_count",
            1,
            10,
            1,
            decimals=0,
        )
        row = self._add_slider(
            grid,
            row,
            "Распределение призраков",
            "lens_flare.ghost_dispersal",
            0.0,
            1.0,
            0.01,
        )
        row = self._add_slider(
            grid, row, "Ширина гало", "lens_flare.halo_width", 0.0, 1.0, 0.01
        )
        row = self._add_slider(
            grid,
            row,
            "Смещение bloom",
            "lens_flare.bloom_bias",
            0.0,
            1.0,
            0.01,
        )
        row = self._add_checkbox(
            grid, row, "Растяжение по пропорциям", "lens_flare.stretch"
        )

        row = self._add_section_label(grid, row, "Виньетирование")
        row = self._add_checkbox(grid, row, "Виньетирование", "vignette.enabled")
        row = self._add_slider(
            grid,
            row,
            "Сила виньетки",
            "vignette.strength",
            0.0,
            1.0,
            0.02,
        )
        row = self._add_slider(
            grid, row, "Радиус виньетки", "vignette.radius", 0.0, 1.0, 0.01
        )

        return group

    def _build_color_adjustments_group(self) -> QGroupBox:
        group = QGroupBox("Цветокоррекция", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        grid.setColumnStretch(1, 1)

        row = 0
        info = QLabel(
            "Параметры Qt 6.10 ExtendedSceneEnvironment: яркость, контраст, насыщенность.",
            self,
        )
        info.setWordWrap(True)
        info.setStyleSheet("color: #808080; font-size: 11px;")
        grid.addWidget(info, row, 0, 1, 2)
        row += 1

        row = self._add_checkbox(
            grid, row, "Активировать цветокоррекцию", "color.enabled"
        )

        row = self._add_slider(
            grid,
            row,
            "Яркость",
            "color.brightness",
            -1.0,
            1.0,
            0.01,
        )
        row = self._add_slider(grid, row, "Контраст", "color.contrast", -1.0, 1.0, 0.01)
        row = self._add_slider(
            grid, row, "Насыщенность", "color.saturation", -1.0, 1.0, 0.01
        )
        return group

    # ----------------------------------------------------------------- helpers
    def _add_checkbox(
        self, grid: QGridLayout, row: int, text: str, control_key: str
    ) -> int:
        state_key = self._state_key_map.get(control_key, control_key)
        widget_name = f"effects.{state_key}".replace("..", ".")
        checkbox = LoggingCheckBox(text, widget_name, self)
        checkbox.toggled.connect(
            lambda checked: self._on_control_changed(control_key, checked)
        )
        self._controls[control_key] = checkbox
        grid.addWidget(checkbox, row, 0, 1, 2)
        return row + 1

    def _add_slider(
        self,
        grid: QGridLayout,
        row: int,
        title: str,
        control_key: str,
        minimum: float,
        maximum: float,
        step: float,
        *,
        decimals: int = 2,
    ) -> int:
        slider = LabeledSlider(title, minimum, maximum, step, decimals=decimals)
        slider.valueChanged.connect(
            lambda value: self._on_control_changed(control_key, value)
        )
        self._controls[control_key] = slider
        grid.addWidget(slider, row, 0, 1, 2)
        return row + 1

    def _add_section_label(self, grid: QGridLayout, row: int, text: str) -> int:
        label = QLabel(text, self)
        label.setStyleSheet("font-weight: 600;")
        grid.addWidget(label, row, 0, 1, 2)
        return row + 1

    def _refresh_dependencies(self) -> None:
        for controller_key, dependent_keys in self._dependencies.items():
            controller = self._controls.get(controller_key)
            if isinstance(controller, QCheckBox):
                self._set_dependents_enabled(dependent_keys, controller.isChecked())
        self._update_dof_focus_enabled()

    def _set_dependents_enabled(self, keys: tuple[str, ...], enabled: bool) -> None:
        for key in keys:
            widget = self._controls.get(key)
            if widget is not None:
                widget.setEnabled(enabled)

    def _update_dof_focus_enabled(self) -> None:
        focus_control = self._controls.get("dof.focus_distance")
        auto_focus_control = self._controls.get("dof.auto_focus")
        if isinstance(focus_control, LabeledSlider):
            enabled = True
            if isinstance(auto_focus_control, QCheckBox):
                enabled = not auto_focus_control.isChecked()
            focus_control.setEnabled(enabled)

    def _normalise_value(self, state_key: str, value: Any) -> Any:
        if state_key in self._integer_keys:
            return int(round(float(value)))
        return value

    # ----------------------------------------------------------------- state api
    def _on_control_changed(self, key: str, value: Any) -> None:
        if self._updating_ui:
            return

        state_key = self._state_key_map.get(key)
        if state_key is not None:
            self._state[state_key] = self._normalise_value(state_key, value)

        if key in self._dependencies and isinstance(self._controls.get(key), QCheckBox):
            self._set_dependents_enabled(self._dependencies[key], bool(value))
        if key == "dof.auto_focus":
            self._update_dof_focus_enabled()

        payload = self.get_state()
        self._state = payload
        self.effects_changed.emit(payload)

    def get_state(self) -> Dict[str, Any]:
        state: Dict[str, Any] = {}
        for control_key, state_key in self._state_key_map.items():
            widget = self._controls.get(control_key)
            value: Any
            if isinstance(widget, QCheckBox):
                value = widget.isChecked()
            elif isinstance(widget, LabeledSlider):
                value = widget.value()
            elif isinstance(widget, QComboBox):
                value = widget.currentData()
            else:
                value = self._state.get(state_key)
            state[state_key] = self._normalise_value(state_key, value)
        if "color_adjustments_enabled" in state:
            active_value = bool(
                state.get(
                    "color_adjustments_active", state["color_adjustments_enabled"]
                )
            )
            state["color_adjustments_active"] = active_value
        return state

    def set_state(self, state: Dict[str, Any]) -> None:
        self._updating_ui = True
        for control in self._controls.values():
            try:
                control.blockSignals(True)
            except Exception:
                pass

        try:
            for control_key, state_key in self._state_key_map.items():
                if state_key not in state:
                    continue
                widget = self._controls.get(control_key)
                if (
                    control_key == "color.enabled"
                    and "color_adjustments_active" in state
                ):
                    value = state["color_adjustments_active"]
                else:
                    value = state[state_key]
                if isinstance(widget, QCheckBox):
                    widget.setChecked(bool(value))
                elif isinstance(widget, LabeledSlider):
                    widget.set_value(float(value))
                elif isinstance(widget, QComboBox):
                    index = widget.findData(value)
                    if index >= 0:
                        widget.setCurrentIndex(index)
        finally:
            for control in self._controls.values():
                try:
                    control.blockSignals(False)
                except Exception:
                    pass
            self._updating_ui = False
            self._refresh_dependencies()
            self._update_dof_focus_enabled()
            self._state = self.get_state()
