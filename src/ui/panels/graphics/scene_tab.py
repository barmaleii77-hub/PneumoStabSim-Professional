"""Scene Tab - управление базовыми параметрами сценического окружения."""

from __future__ import annotations

from typing import Any, Mapping

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
from src.common.settings_manager import get_settings_manager
from src.ui.environment_schema import (
    SCENE_PARAMETERS,
    SCENE_SUSPENSION_PARAMETERS,
    validate_scene_settings,
)


_DEFAULT_SCENE_STATE: dict[str, Any] = {
    "scale_factor": 1.0,
    "exposure": 1.0,
    "default_clear_color": "#1b1f27",
    "model_base_color": "#9da3aa",
    "model_roughness": 0.42,
    "model_metalness": 0.82,
    "suspension": {"rod_warning_threshold_m": 0.001},
}


class SceneTab(QWidget):
    """Вкладка управления параметрами сцены (масштаб, экспозиция, базовые цвета)."""

    scene_changed = Signal(dict)

    def __init__(
        self,
        parent: QWidget | None = None,
        metadata_defaults: Mapping[str, Any] | None = None,
    ) -> None:
        super().__init__(parent)
        self._controls: dict[str, Any] = {}
        self._updating_ui = False
        self._slider_ranges: dict[str, dict[str, float]] = self._load_slider_ranges()
        self._defaults = self._load_defaults(metadata_defaults)
        self._setup_ui()
        self._apply_defaults()

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

        scale_min, scale_max, scale_step, scale_decimals = self._slider_range(
            "scale_factor", 0.01, 5.0, 0.01, 2
        )
        scale_slider = LabeledSlider(
            "Масштаб модели",
            scale_min,
            scale_max,
            scale_step,
            decimals=scale_decimals,
        )
        scale_slider.valueChanged.connect(
            lambda value: self._on_control_changed("scale_factor", value)
        )
        self._controls["scale_factor"] = scale_slider
        grid.addWidget(scale_slider, row, 0, 1, 2)
        row += 1

        exposure_min, exposure_max, exposure_step, exposure_decimals = (
            self._slider_range("exposure", 0.0, 32.0, 0.1, 2)
        )
        exposure_slider = LabeledSlider(
            "Экспозиция",
            exposure_min,
            exposure_max,
            exposure_step,
            decimals=exposure_decimals,
        )
        exposure_slider.valueChanged.connect(
            lambda value: self._on_control_changed("exposure", value)
        )
        self._controls["exposure"] = exposure_slider
        grid.addWidget(exposure_slider, row, 0, 1, 2)
        row += 1

        clear_color_row = QHBoxLayout()
        clear_color_row.addWidget(QLabel("Цвет очистки", self))
        clear_button = ColorButton(self._defaults["default_clear_color"])
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
        base_button = ColorButton(self._defaults["model_base_color"])
        base_button.color_changed.connect(
            lambda color: self._on_control_changed("model_base_color", color)
        )
        self._controls["model_base_color"] = base_button
        base_color_row.addWidget(base_button)
        base_color_row.addStretch(1)
        grid.addLayout(base_color_row, row, 0, 1, 2)
        row += 1

        roughness_min, roughness_max, roughness_step, roughness_decimals = (
            self._slider_range("model_roughness", 0.0, 1.0, 0.01, 2)
        )
        roughness_slider = LabeledSlider(
            "Шероховатость модели",
            roughness_min,
            roughness_max,
            roughness_step,
            decimals=roughness_decimals,
        )
        roughness_slider.valueChanged.connect(
            lambda value: self._on_control_changed("model_roughness", value)
        )
        self._controls["model_roughness"] = roughness_slider
        grid.addWidget(roughness_slider, row, 0, 1, 2)
        row += 1

        metalness_min, metalness_max, metalness_step, metalness_decimals = (
            self._slider_range("model_metalness", 0.0, 1.0, 0.01, 2)
        )
        metalness_slider = LabeledSlider(
            "Металличность модели",
            metalness_min,
            metalness_max,
            metalness_step,
            decimals=metalness_decimals,
        )
        metalness_slider.valueChanged.connect(
            lambda value: self._on_control_changed("model_metalness", value)
        )
        self._controls["model_metalness"] = metalness_slider
        grid.addWidget(metalness_slider, row, 0, 1, 2)
        row += 1

        (
            suspension_min,
            suspension_max,
            suspension_step,
            suspension_decimals,
        ) = self._slider_range(
            "suspension.rod_warning_threshold_m", 0.0001, 0.02, 0.0001, 4
        )
        suspension_slider = LabeledSlider(
            "Порог предупреждения штока (м)",
            suspension_min,
            suspension_max,
            suspension_step,
            decimals=suspension_decimals,
        )
        suspension_slider.valueChanged.connect(
            lambda value: self._on_control_changed(
                "suspension.rod_warning_threshold_m", value
            )
        )
        self._controls["suspension.rod_warning_threshold_m"] = suspension_slider
        grid.addWidget(suspension_slider, row, 0, 1, 2)

        return group

    # ------------------------------------------------------------------ helpers
    def _apply_defaults(self) -> None:
        self.set_state(self._defaults, emit_signal=False)

    @staticmethod
    def _deep_merge_dicts(
        base: dict[str, Any], override: Mapping[str, Any]
    ) -> dict[str, Any]:
        merged: dict[str, Any] = dict(base)
        for key, value in override.items():
            existing = merged.get(key)
            if isinstance(existing, dict) and isinstance(value, Mapping):
                merged[key] = SceneTab._deep_merge_dicts(existing, value)
            else:
                merged[key] = value
        return merged

    def _load_defaults(
        self, metadata_defaults: Mapping[str, Any] | None
    ) -> dict[str, Any]:
        defaults = dict(_DEFAULT_SCENE_STATE)
        source: Mapping[str, Any] | None = metadata_defaults
        if source is None:
            try:
                manager = get_settings_manager()
                raw_defaults = manager.get("metadata.scene_defaults", {})
                if isinstance(raw_defaults, Mapping):
                    source = raw_defaults
            except Exception:
                source = None
        if isinstance(source, Mapping):
            defaults = self._deep_merge_dicts(defaults, source)
        try:
            return validate_scene_settings(defaults)
        except Exception:
            return validate_scene_settings(_DEFAULT_SCENE_STATE)

    def _load_slider_ranges(self) -> dict[str, dict[str, float]]:
        try:
            raw_ranges = get_settings_manager().get("metadata.scene_slider_ranges", {})
        except Exception:
            return {}
        if not isinstance(raw_ranges, Mapping):
            return {}

        ranges: dict[str, dict[str, float]] = {}
        for key, payload in raw_ranges.items():
            if key == "suspension" and isinstance(payload, Mapping):
                for nested_key, nested_payload in payload.items():
                    parsed = self._parse_slider_range(nested_payload)
                    if parsed:
                        ranges[f"suspension.{nested_key}"] = parsed
                continue
            parsed = self._parse_slider_range(payload)
            if parsed:
                ranges[key] = parsed
        return ranges

    @staticmethod
    def _parse_slider_range(payload: Any) -> dict[str, float] | None:
        if not isinstance(payload, Mapping):
            return None
        try:
            min_value = float(payload.get("min"))
            max_value = float(payload.get("max"))
            step = float(payload.get("step"))
        except (TypeError, ValueError):
            return None
        if step <= 0:
            return None
        decimals_raw = payload.get("decimals", 2)
        try:
            decimals = int(decimals_raw)
        except (TypeError, ValueError):
            decimals = 2
        return {"min": min_value, "max": max_value, "step": step, "decimals": decimals}

    def _slider_range(
        self,
        key: str,
        fallback_min: float,
        fallback_max: float,
        fallback_step: float,
        fallback_decimals: int,
    ) -> tuple[float, float, float, int]:
        configured = self._slider_ranges.get(key)
        if configured:
            min_value = float(configured.get("min", fallback_min))
            max_value = float(configured.get("max", fallback_max))
            step = float(configured.get("step", fallback_step)) or fallback_step
            decimals = int(configured.get("decimals", fallback_decimals))
            return min_value, max_value, step, max(decimals, 0)

        min_value, max_value = self._range_for(key, fallback_min, fallback_max)
        return min_value, max_value, fallback_step, fallback_decimals

    def _on_control_changed(self, key: str, value: Any) -> None:
        if self._updating_ui:
            return
        self.scene_changed.emit(self.get_state())

    def _require_control(self, key: str) -> Any:
        try:
            return self._controls[key]
        except KeyError as exc:  # pragma: no cover - defensive
            raise KeyError(f"Control '{key}' is not registered") from exc

    def _range_for(
        self, key: str, fallback_min: float, fallback_max: float
    ) -> tuple[float, float]:
        if key.startswith("suspension."):
            raw_key = key.split(".", maxsplit=1)[1]
            return self._range_from_definitions(
                raw_key, SCENE_SUSPENSION_PARAMETERS, fallback_min, fallback_max
            )

        return self._range_from_definitions(
            key, SCENE_PARAMETERS, fallback_min, fallback_max
        )

    @staticmethod
    def _range_from_definitions(
        key: str,
        definitions: tuple,
        fallback_min: float,
        fallback_max: float,
    ) -> tuple[float, float]:
        for definition in definitions:
            if getattr(definition, "key", None) != key:
                continue
            min_value = definition.min_value
            max_value = definition.max_value
            return (
                fallback_min if min_value is None else float(min_value),
                fallback_max if max_value is None else float(max_value),
            )
        return fallback_min, fallback_max

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

    def set_state(self, state: dict[str, Any], *, emit_signal: bool = True) -> None:
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
        if emit_signal:
            self.scene_changed.emit(self.get_state())


__all__ = ["SceneTab"]
