"""Scene Tab - управление базовыми параметрами сценического окружения."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from .widgets import ColorButton, LabeledSlider
from src.ui.environment_schema import validate_scene_settings


class SceneTab(QWidget):
    """Вкладка управления параметрами сцены (масштаб, экспозиция, базовые цвета)."""

    scene_changed = Signal(dict)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controls: dict[str, Any] = {}
        self._updating_ui = False
        self._setup_ui()

    # ------------------------------------------------------------------ UI helpers
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(self._build_scene_group())
        layout.addStretch(1)

    def _build_scene_group(self) -> QGroupBox:
        group = QGroupBox("Сцена и модель", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)

        row = 0

        scale_slider = LabeledSlider("Масштаб модели", 0.01, 5.0, 0.01, decimals=2)
        scale_slider.valueChanged.connect(
            lambda value: self._on_control_changed("scale_factor", value)
        )
        self._controls["scale_factor"] = scale_slider
        grid.addWidget(scale_slider, row, 0, 1, 2)
        row += 1

        exposure_slider = LabeledSlider("Экспозиция", 0.0, 32.0, 0.1, decimals=2)
        exposure_slider.valueChanged.connect(
            lambda value: self._on_control_changed("exposure", value)
        )
        self._controls["exposure"] = exposure_slider
        grid.addWidget(exposure_slider, row, 0, 1, 2)
        row += 1

        clear_color_row = QHBoxLayout()
        clear_color_row.addWidget(QLabel("Цвет очистки", self))
        clear_button = ColorButton("#1b1f27")
        clear_button.color_changed.connect(
            lambda color: self._on_control_changed("default_clear_color", color)
        )
        self._controls["default_clear_color"] = clear_button
        clear_color_row.addWidget(clear_button)
        clear_color_row.addStretch(1)
        grid.addLayout(clear_color_row, row, 0, 1, 2)
        row += 1

        base_color_row = QHBoxLayout()
        base_color_row.addWidget(QLabel("Базовый цвет модели", self))
        base_button = ColorButton("#9da3aa")
        base_button.color_changed.connect(
            lambda color: self._on_control_changed("model_base_color", color)
        )
        self._controls["model_base_color"] = base_button
        base_color_row.addWidget(base_button)
        base_color_row.addStretch(1)
        grid.addLayout(base_color_row, row, 0, 1, 2)
        row += 1

        roughness_slider = LabeledSlider(
            "Шероховатость модели", 0.0, 1.0, 0.01, decimals=2
        )
        roughness_slider.valueChanged.connect(
            lambda value: self._on_control_changed("model_roughness", value)
        )
        self._controls["model_roughness"] = roughness_slider
        grid.addWidget(roughness_slider, row, 0, 1, 2)
        row += 1

        metalness_slider = LabeledSlider(
            "Металличность модели", 0.0, 1.0, 0.01, decimals=2
        )
        metalness_slider.valueChanged.connect(
            lambda value: self._on_control_changed("model_metalness", value)
        )
        self._controls["model_metalness"] = metalness_slider
        grid.addWidget(metalness_slider, row, 0, 1, 2)
        row += 1

        suspension_slider = LabeledSlider(
            "Порог предупреждения штока (м)", 0.0001, 0.02, 0.0001, decimals=4
        )
        suspension_slider.set_value(0.001)
        suspension_slider.valueChanged.connect(
            lambda value: self._on_control_changed(
                "suspension.rod_warning_threshold_m", value
            )
        )
        self._controls["suspension.rod_warning_threshold_m"] = suspension_slider
        grid.addWidget(suspension_slider, row, 0, 1, 2)

        return group

    # ------------------------------------------------------------------ helpers
    def _on_control_changed(self, key: str, value: Any) -> None:
        if self._updating_ui:
            return
        self.scene_changed.emit(self.get_state())

    def _require_control(self, key: str) -> Any:
        try:
            return self._controls[key]
        except KeyError as exc:  # pragma: no cover - defensive
            raise KeyError(f"Control '{key}' is not registered") from exc

    # ------------------------------------------------------------------ state API
    def get_state(self) -> dict[str, Any]:
        return {
            "scale_factor": self._require_control("scale_factor").value(),
            "exposure": self._require_control("exposure").value(),
            "default_clear_color": self._require_control("default_clear_color")
            .color()
            .name(),
            "model_base_color": self._require_control("model_base_color")
            .color()
            .name(),
            "model_roughness": self._require_control("model_roughness").value(),
            "model_metalness": self._require_control("model_metalness").value(),
            "suspension": {
                "rod_warning_threshold_m": self._require_control(
                    "suspension.rod_warning_threshold_m"
                ).value()
            },
        }

    def set_state(self, state: dict[str, Any]) -> None:
        validated = validate_scene_settings(state)
        self._updating_ui = True
        try:
            self._require_control("scale_factor").set_value(validated["scale_factor"])
            self._require_control("exposure").set_value(validated["exposure"])
            self._require_control("default_clear_color").set_color(
                validated["default_clear_color"]
            )
            self._require_control("model_base_color").set_color(
                validated["model_base_color"]
            )
            self._require_control("model_roughness").set_value(
                validated["model_roughness"]
            )
            self._require_control("model_metalness").set_value(
                validated["model_metalness"]
            )
            self._require_control("suspension.rod_warning_threshold_m").set_value(
                validated["suspension"]["rod_warning_threshold_m"]
            )
        finally:
            self._updating_ui = False
        self.scene_changed.emit(self.get_state())


__all__ = ["SceneTab"]
