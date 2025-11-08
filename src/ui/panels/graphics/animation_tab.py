"""Animation tab exposing animation smoothing and phase controls."""

from __future__ import annotations

from typing import Any

from PySide6.QtCore import Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

from src.ui.environment_schema import validate_animation_settings
from src.ui.panels.graphics.widgets import LabeledSlider
from src.ui.panels.modes.defaults import PARAMETER_RANGES


class AnimationTab(QWidget):
    """Widget tab providing controls for animation parameters."""

    animation_changed = Signal(dict)

    _EASING_OPTIONS: tuple[tuple[str, str], ...] = (
        ("OutCubic", "OutCubic"),
        ("OutQuad", "OutQuad"),
        ("Linear", "Linear"),
        ("InOutSine", "InOutSine"),
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._controls: dict[str, Any] = {}
        self._smoothing_widgets: list[Any] = []
        self._updating_ui = False
        self._setup_ui()

    # ------------------------------------------------------------------ UI helpers
    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(self._build_runtime_group())
        layout.addWidget(self._build_global_group())
        layout.addWidget(self._build_wheel_group())
        layout.addWidget(self._build_smoothing_group())

        layout.addStretch(1)

    def _build_runtime_group(self) -> QGroupBox:
        group = QGroupBox("Состояние анимации", self)
        form = QFormLayout(group)
        form.setContentsMargins(8, 8, 8, 8)
        form.setSpacing(8)

        running_check = QCheckBox("Анимация запущена", group)
        running_check.toggled.connect(
            lambda checked: self._on_bool_changed("is_running", checked)
        )
        self._controls["is_running"] = running_check
        form.addRow(running_check)

        time_spin = QDoubleSpinBox(group)
        time_spin.setDecimals(2)
        time_spin.setRange(0.0, 100000.0)
        time_spin.setSingleStep(0.1)
        time_spin.setSuffix(" с")
        time_spin.valueChanged.connect(
            lambda value: self._on_numeric_changed("animation_time", float(value))
        )
        self._controls["animation_time"] = time_spin
        form.addRow(QLabel("Базовое время"), time_spin)

        return group

    def _build_global_group(self) -> QGroupBox:
        group = QGroupBox("Глобальные параметры", self)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        amp_range = PARAMETER_RANGES["amplitude"]
        amplitude_slider = LabeledSlider(
            "Амплитуда",
            amp_range["min"],
            amp_range["max"],
            amp_range["step"],
            decimals=amp_range["decimals"],
            unit=amp_range["unit"],
        )
        amplitude_slider.valueChanged.connect(
            lambda value: self._on_numeric_changed("amplitude", float(value))
        )
        self._controls["amplitude"] = amplitude_slider
        layout.addWidget(amplitude_slider)

        freq_range = PARAMETER_RANGES["frequency"]
        frequency_slider = LabeledSlider(
            "Частота",
            freq_range["min"],
            freq_range["max"],
            freq_range["step"],
            decimals=freq_range["decimals"],
            unit=freq_range["unit"],
        )
        frequency_slider.valueChanged.connect(
            lambda value: self._on_numeric_changed("frequency", float(value))
        )
        self._controls["frequency"] = frequency_slider
        layout.addWidget(frequency_slider)

        phase_range = PARAMETER_RANGES["phase"]
        phase_slider = LabeledSlider(
            "Глобальная фаза",
            phase_range["min"],
            phase_range["max"],
            phase_range["step"],
            decimals=phase_range["decimals"],
            unit=phase_range["unit"],
        )
        phase_slider.valueChanged.connect(
            lambda value: self._on_numeric_changed("phase_global", float(value))
        )
        self._controls["phase_global"] = phase_slider
        layout.addWidget(phase_slider)

        return group

    def _build_wheel_group(self) -> QGroupBox:
        group = QGroupBox("Фазовые сдвиги", self)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        info = QLabel(
            "Настройте индивидуальные фазовые сдвиги для каждого колеса (в градусах)."
        )
        info.setWordWrap(True)
        layout.addWidget(info)

        wheel_layout = QHBoxLayout()
        wheel_layout.setSpacing(12)
        layout.addLayout(wheel_layout)

        phase_range = PARAMETER_RANGES["wheel_phase"]

        def _make_wheel_slider(title: str, key: str) -> LabeledSlider:
            slider = LabeledSlider(
                title,
                phase_range["min"],
                phase_range["max"],
                phase_range["step"],
                decimals=phase_range["decimals"],
                unit=phase_range["unit"],
            )
            slider.valueChanged.connect(
                lambda value: self._on_numeric_changed(key, float(value))
            )
            self._controls[key] = slider
            return slider

        left_column = QVBoxLayout()
        left_column.setSpacing(8)
        wheel_layout.addLayout(left_column)
        left_column.addWidget(_make_wheel_slider("Левое переднее", "phase_fl"))
        left_column.addWidget(_make_wheel_slider("Левое заднее", "phase_rl"))

        right_column = QVBoxLayout()
        right_column.setSpacing(8)
        wheel_layout.addLayout(right_column)
        right_column.addWidget(_make_wheel_slider("Правое переднее", "phase_fr"))
        right_column.addWidget(_make_wheel_slider("Правое заднее", "phase_rr"))

        return group

    def _build_smoothing_group(self) -> QGroupBox:
        group = QGroupBox("Сглаживание движения", self)
        layout = QVBoxLayout(group)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        smoothing_enabled = QCheckBox("Включить сглаживание", group)
        smoothing_enabled.toggled.connect(self._on_smoothing_toggled)
        self._controls["smoothing_enabled"] = smoothing_enabled
        layout.addWidget(smoothing_enabled)

        duration_range = PARAMETER_RANGES["smoothing_duration_ms"]
        duration_slider = LabeledSlider(
            "Длительность сглаживания",
            duration_range["min"],
            duration_range["max"],
            duration_range["step"],
            decimals=duration_range["decimals"],
            unit=duration_range["unit"],
        )
        duration_slider.valueChanged.connect(
            lambda value: self._on_numeric_changed(
                "smoothing_duration_ms", float(value)
            )
        )
        self._controls["smoothing_duration_ms"] = duration_slider
        layout.addWidget(duration_slider)
        self._smoothing_widgets.append(duration_slider)

        angle_range = PARAMETER_RANGES["smoothing_angle_snap_deg"]
        angle_slider = LabeledSlider(
            "Порог угла",
            angle_range["min"],
            angle_range["max"],
            angle_range["step"],
            decimals=angle_range["decimals"],
            unit=angle_range["unit"],
        )
        angle_slider.valueChanged.connect(
            lambda value: self._on_numeric_changed(
                "smoothing_angle_snap_deg", float(value)
            )
        )
        self._controls["smoothing_angle_snap_deg"] = angle_slider
        layout.addWidget(angle_slider)
        self._smoothing_widgets.append(angle_slider)

        piston_range = PARAMETER_RANGES["smoothing_piston_snap_m"]
        piston_slider = LabeledSlider(
            "Порог поршня",
            piston_range["min"],
            piston_range["max"],
            piston_range["step"],
            decimals=piston_range["decimals"],
            unit=piston_range["unit"],
        )
        piston_slider.valueChanged.connect(
            lambda value: self._on_numeric_changed(
                "smoothing_piston_snap_m", float(value)
            )
        )
        self._controls["smoothing_piston_snap_m"] = piston_slider
        layout.addWidget(piston_slider)
        self._smoothing_widgets.append(piston_slider)

        easing_row = QHBoxLayout()
        easing_row.setSpacing(6)
        easing_label = QLabel("Профиль easing", group)
        easing_row.addWidget(easing_label)

        easing_combo = QComboBox(group)
        for text, value in self._EASING_OPTIONS:
            easing_combo.addItem(text, value)
        easing_combo.currentIndexChanged.connect(
            lambda _: self._on_combo_changed("smoothing_easing")
        )
        self._controls["smoothing_easing"] = easing_combo
        easing_row.addWidget(easing_combo, 1)
        layout.addLayout(easing_row)
        self._smoothing_widgets.append(easing_combo)

        return group

    # ------------------------------------------------------------------ helpers
    def _on_numeric_changed(self, key: str, value: float) -> None:
        if self._updating_ui:
            return
        self.animation_changed.emit(self.get_state())

    def _on_bool_changed(self, key: str, value: bool) -> None:
        if key == "smoothing_enabled":
            self._update_smoothing_controls(value)
        if self._updating_ui:
            return
        self.animation_changed.emit(self.get_state())

    def _on_smoothing_toggled(self, checked: bool) -> None:
        self._on_bool_changed("smoothing_enabled", checked)

    def _on_combo_changed(self, key: str) -> None:
        if self._updating_ui:
            return
        self.animation_changed.emit(self.get_state())

    def _update_smoothing_controls(self, enabled: bool) -> None:
        for widget in self._smoothing_widgets:
            widget.setEnabled(enabled)

    def _require_control(self, key: str) -> Any:
        try:
            return self._controls[key]
        except KeyError as exc:  # pragma: no cover - defensive branch
            raise KeyError(f"Control '{key}' is not registered") from exc

    # ------------------------------------------------------------------ state API
    def get_state(self) -> dict[str, Any]:
        payload = {
            "is_running": bool(self._require_control("is_running").isChecked()),
            "animation_time": float(self._require_control("animation_time").value()),
            "amplitude": float(self._require_control("amplitude").value()),
            "frequency": float(self._require_control("frequency").value()),
            "phase_global": float(self._require_control("phase_global").value()),
            "phase_fl": float(self._require_control("phase_fl").value()),
            "phase_fr": float(self._require_control("phase_fr").value()),
            "phase_rl": float(self._require_control("phase_rl").value()),
            "phase_rr": float(self._require_control("phase_rr").value()),
            "smoothing_enabled": bool(
                self._require_control("smoothing_enabled").isChecked()
            ),
            "smoothing_duration_ms": float(
                self._require_control("smoothing_duration_ms").value()
            ),
            "smoothing_angle_snap_deg": float(
                self._require_control("smoothing_angle_snap_deg").value()
            ),
            "smoothing_piston_snap_m": float(
                self._require_control("smoothing_piston_snap_m").value()
            ),
            "smoothing_easing": str(
                self._require_control("smoothing_easing").currentData()  # type: ignore[attr-defined]
                or self._require_control("smoothing_easing").currentText()
            ),
        }
        return validate_animation_settings(payload)

    def set_state(self, state: dict[str, Any]) -> None:
        validated = validate_animation_settings(state)
        self._updating_ui = True
        try:
            self._require_control("is_running").setChecked(validated["is_running"])
            self._require_control("animation_time").setValue(
                validated["animation_time"]
            )
            self._require_control("amplitude").set_value(validated["amplitude"])
            self._require_control("frequency").set_value(validated["frequency"])
            self._require_control("phase_global").set_value(validated["phase_global"])
            self._require_control("phase_fl").set_value(validated["phase_fl"])
            self._require_control("phase_fr").set_value(validated["phase_fr"])
            self._require_control("phase_rl").set_value(validated["phase_rl"])
            self._require_control("phase_rr").set_value(validated["phase_rr"])
            self._require_control("smoothing_enabled").setChecked(
                validated["smoothing_enabled"]
            )
            self._update_smoothing_controls(validated["smoothing_enabled"])
            self._require_control("smoothing_duration_ms").set_value(
                validated["smoothing_duration_ms"]
            )
            self._require_control("smoothing_angle_snap_deg").set_value(
                validated["smoothing_angle_snap_deg"]
            )
            self._require_control("smoothing_piston_snap_m").set_value(
                validated["smoothing_piston_snap_m"]
            )

            easing_combo: QComboBox = self._require_control("smoothing_easing")
            target_value = validated["smoothing_easing"]
            index = easing_combo.findData(target_value)
            if index < 0:
                index = easing_combo.findText(target_value)
            easing_combo.setCurrentIndex(max(0, index))
        finally:
            self._updating_ui = False

        self.animation_changed.emit(self.get_state())


__all__ = ["AnimationTab"]
