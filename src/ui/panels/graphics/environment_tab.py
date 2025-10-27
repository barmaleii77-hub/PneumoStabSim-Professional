# -*- coding: utf-8 -*-
"""
Environment Tab - вкладка настроек окружения (фон, IBL, туман, AO)
Part of modular GraphicsPanel restructuring

СТРУКТУРА ТОЧНО ПОВТОРЯЕТ МОНОЛИТ panel_graphics.py:
- _build_background_group() → Фон и IBL (с HDR discovery)
- _build_fog_group() → Туман с near/far + высотный туман (Qt 6.10 Fog)
- _build_ao_group() → Ambient Occlusion (SSAO) расширенный
"""

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QGroupBox,
    QLabel,
    QComboBox,
    QCheckBox,
    QHBoxLayout,
    QGridLayout,
)
from PySide6.QtCore import Signal
from pathlib import Path
from typing import Dict, Any, List, Tuple

from .widgets import ColorButton, LabeledSlider
from src.ui.environment_schema import validate_environment_settings


class EnvironmentTab(QWidget):
    """Вкладка настроек окружения: фон, IBL, туман, AO

    Signals:
        environment_changed: Dict[str, Any] - параметры окружения изменились
    """

    environment_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Current state - храним ссылки на контролы
        self._controls: Dict[str, Any] = {}
        self._updating_ui = False

        # Setup UI
        self._setup_ui()

    def _setup_ui(self):
        """Построить UI вкладки - РАСШИРЕННАЯ ВЕРСИЯ"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(self._build_background_group())
        layout.addWidget(self._build_reflection_group())
        layout.addWidget(self._build_fog_group())
        layout.addWidget(self._build_ao_group())

        layout.addStretch(1)

    def _build_background_group(self) -> QGroupBox:
        """Создать группу Фон и IBL - расширенная"""
        group = QGroupBox("Фон и IBL", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        row = 0

        # Background mode
        grid.addWidget(QLabel("Режим фона", self), row, 0)
        bg_mode = QComboBox(self)
        bg_mode.addItem("Skybox", "skybox")
        bg_mode.addItem("Сплошной цвет", "color")
        bg_mode.addItem("Прозрачный", "transparent")
        bg_mode.currentIndexChanged.connect(
            lambda _: self._on_control_changed("background_mode", bg_mode.currentData())
        )
        self._controls["background.mode"] = bg_mode
        grid.addWidget(bg_mode, row, 1)
        row += 1

        # Background color
        bg_row = QHBoxLayout()
        bg_row.addWidget(QLabel("Цвет", self))
        bg_button = ColorButton()
        bg_button.color_changed.connect(
            lambda c: self._on_control_changed("background_color", c)
        )
        self._controls["background.color"] = bg_button
        bg_row.addWidget(bg_button)
        bg_row.addStretch(1)
        grid.addLayout(bg_row, row, 0, 1, 2)
        row += 1

        # Skybox enabled
        skybox_toggle = LoggingCheckBox(
            "Показывать Skybox (фон)", "environment.skybox_enabled", self
        )
        skybox_toggle.clicked.connect(
            lambda checked: self._on_skybox_enabled_clicked(checked)
        )
        self._controls["background.skybox_enabled"] = skybox_toggle
        grid.addWidget(skybox_toggle, row, 0, 1, 2)
        row += 1

        # IBL enabled
        ibl_check = LoggingCheckBox("Включить IBL", "environment.ibl_enabled", self)
        ibl_check.clicked.connect(lambda checked: self._on_ibl_enabled_clicked(checked))
        self._controls["ibl.enabled"] = ibl_check
        grid.addWidget(ibl_check, row, 0, 1, 2)
        row += 1

        # IBL intensity
        intensity = LabeledSlider("Интенсивность IBL", 0.0, 8.0, 0.05, decimals=2)
        intensity.valueChanged.connect(
            lambda v: self._on_control_changed("ibl_intensity", v)
        )
        self._controls["ibl.intensity"] = intensity
        grid.addWidget(intensity, row, 0, 1, 2)
        row += 1

        # IBL extra: probe brightness (если поддерживается движком)
        probe_brightness = LabeledSlider(
            "Яркость пробы (probeBrightness)", 0.0, 8.0, 0.05, decimals=2
        )
        probe_brightness.valueChanged.connect(
            lambda v: self._on_control_changed("probe_brightness", v)
        )
        self._controls["ibl.probe_brightness"] = probe_brightness
        grid.addWidget(probe_brightness, row, 0, 1, 2)
        row += 1

        # IBL extra: probe horizon cutoff (-1..1)
        probe_horizon = LabeledSlider(
            "Горизонт пробы (probeHorizon)", -1.0, 1.0, 0.01, decimals=2
        )
        probe_horizon.valueChanged.connect(
            lambda v: self._on_control_changed("probe_horizon", v)
        )
        self._controls["ibl.probe_horizon"] = probe_horizon
        grid.addWidget(probe_horizon, row, 0, 1, 2)
        row += 1

        # Skybox blur
        blur = LabeledSlider("Размытие skybox", 0.0, 1.0, 0.01, decimals=2)
        blur.valueChanged.connect(lambda v: self._on_control_changed("skybox_blur", v))
        self._controls["skybox.blur"] = blur
        grid.addWidget(blur, row, 0, 1, 2)
        row += 1

        # HDR file (primary)
        hdr_combo = QComboBox(self)
        hdr_files = self._discover_hdr_files()
        for label, path in hdr_files:
            hdr_combo.addItem(label, path)
        hdr_combo.insertItem(0, "— не выбран —", "")
        hdr_combo.setCurrentIndex(0)

        def on_hdr_changed() -> None:
            data = hdr_combo.currentData()
            path = self._normalize_ibl_path(data)
            self._on_control_changed("ibl_source", path)

        hdr_combo.currentIndexChanged.connect(lambda _: on_hdr_changed())
        self._controls["ibl.file"] = hdr_combo
        grid.addWidget(QLabel("HDR файл (primary)", self), row, 0)
        grid.addWidget(hdr_combo, row, 1)
        row += 1

        # HDR fallback file
        fallback_combo = QComboBox(self)
        for label, path in hdr_files:
            fallback_combo.addItem(label, path)
        fallback_combo.insertItem(0, "— не выбран —", "")
        fallback_combo.setCurrentIndex(0)

        def on_fallback_changed() -> None:
            data = fallback_combo.currentData()
            path = self._normalize_ibl_path(data)
            self._on_control_changed("ibl_fallback", path)

        fallback_combo.currentIndexChanged.connect(lambda _: on_fallback_changed())
        self._controls["ibl.fallback"] = fallback_combo
        grid.addWidget(QLabel("HDR fallback", self), row, 0)
        grid.addWidget(fallback_combo, row, 1)
        row += 1

        # IBL rotation
        ibl_rot = LabeledSlider(
            "Поворот IBL", -1080.0, 1080.0, 1.0, decimals=0, unit="°"
        )
        ibl_rot.valueChanged.connect(
            lambda v: self._on_control_changed("ibl_rotation", v)
        )
        self._controls["ibl.rotation"] = ibl_rot
        grid.addWidget(ibl_rot, row, 0, 1, 2)
        row += 1

        # IBL offsets
        env_off_x = LabeledSlider(
            "Смещение окружения X", -180.0, 180.0, 1.0, decimals=0, unit="°"
        )
        env_off_x.valueChanged.connect(
            lambda v: self._on_control_changed("ibl_offset_x", v)
        )
        self._controls["ibl.offset_x"] = env_off_x
        grid.addWidget(env_off_x, row, 0, 1, 2)
        row += 1
        env_off_y = LabeledSlider(
            "Смещение окружения Y", -180.0, 180.0, 1.0, decimals=0, unit="°"
        )
        env_off_y.valueChanged.connect(
            lambda v: self._on_control_changed("ibl_offset_y", v)
        )
        self._controls["ibl.offset_y"] = env_off_y
        grid.addWidget(env_off_y, row, 0, 1, 2)
        row += 1

        # IBL bind
        env_bind = LoggingCheckBox(
            "Привязать окружение к камере",
            "environment.ibl_bind_to_camera",
            self,
        )
        env_bind.clicked.connect(
            lambda checked: self._on_control_changed("ibl_bind_to_camera", checked)
        )
        self._controls["ibl.bind"] = env_bind
        grid.addWidget(env_bind, row, 0, 1, 2)

        return group

    def _build_reflection_group(self) -> QGroupBox:
        """Создать группу настроек локальной Reflection Probe"""

        group = QGroupBox("Reflection Probe", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        row = 0

        enabled = LoggingCheckBox(
            "Включить локальную reflection probe",
            "environment.reflection_enabled",
            self,
        )
        enabled.clicked.connect(
            lambda checked: self._on_control_changed("reflection_enabled", checked)
        )
        self._controls["reflection.enabled"] = enabled
        grid.addWidget(enabled, row, 0, 1, 2)
        row += 1

        padding = LabeledSlider(
            "Отступ от геометрии", 0.0, 1.0, 0.01, decimals=2, unit="м"
        )
        padding.valueChanged.connect(
            lambda v: self._on_control_changed("reflection_padding_m", v)
        )
        padding.setToolTip(
            "Дополнительная оболочка вокруг подвески для захвата отражений"
        )
        self._controls["reflection.padding"] = padding
        grid.addWidget(padding, row, 0, 1, 2)
        row += 1

        quality_combo = QComboBox(self)
        quality_combo.addItem("Очень высокое", "veryhigh")
        quality_combo.addItem("Высокое", "high")
        quality_combo.addItem("Среднее", "medium")
        quality_combo.addItem("Низкое", "low")
        quality_combo.currentIndexChanged.connect(
            lambda _: self._on_control_changed(
                "reflection_quality", quality_combo.currentData()
            )
        )
        self._controls["reflection.quality"] = quality_combo
        grid.addWidget(QLabel("Качество", self), row, 0)
        grid.addWidget(quality_combo, row, 1)
        row += 1

        refresh_combo = QComboBox(self)
        refresh_combo.addItem("Каждый кадр", "everyframe")
        refresh_combo.addItem("Только первый кадр", "firstframe")
        refresh_combo.addItem("Отключено", "never")
        refresh_combo.currentIndexChanged.connect(
            lambda _: self._on_control_changed(
                "reflection_refresh_mode", refresh_combo.currentData()
            )
        )
        self._controls["reflection.refresh_mode"] = refresh_combo
        grid.addWidget(QLabel("Обновление карты", self), row, 0)
        grid.addWidget(refresh_combo, row, 1)
        row += 1

        slicing_combo = QComboBox(self)
        slicing_combo.addItem("Отдельно для каждой грани", "individualfaces")
        slicing_combo.addItem("Все грани одновременно", "allfacesatonce")
        slicing_combo.addItem("Без разделения по времени", "notimeslicing")
        slicing_combo.currentIndexChanged.connect(
            lambda _: self._on_control_changed(
                "reflection_time_slicing", slicing_combo.currentData()
            )
        )
        self._controls["reflection.time_slicing"] = slicing_combo
        grid.addWidget(QLabel("Распределение по кадрам", self), row, 0)
        grid.addWidget(slicing_combo, row, 1)

        return group

    def _discover_hdr_files(self) -> List[Tuple[str, str]]:
        results: List[Tuple[str, str]] = []
        search_dirs = [
            Path("assets/hdr"),
            Path("assets/hdri"),
            Path("assets/qml/assets"),
        ]
        qml_dir = Path("assets/qml").resolve()

        def to_qml_relative(p: Path) -> str:
            try:
                abs_p = p.resolve()
                rel = abs_p.relative_to(qml_dir)
                return rel.as_posix()
            except Exception:
                try:
                    import os

                    relpath = os.path.relpath(p.resolve(), start=qml_dir)
                    return Path(relpath).as_posix()
                except Exception:
                    return p.resolve().as_posix()

        seen: set[str] = set()
        for base in search_dirs:
            if not base.exists():
                continue
            for ext in ("*.hdr", "*.exr"):
                for p in sorted(base.glob(ext)):
                    key = p.name.lower()
                    if key in seen:
                        continue
                    seen.add(key)
                    results.append((p.name, to_qml_relative(p)))
        return results

    def _normalize_ibl_path(self, value: Any) -> str:
        """Нормализовать путь для IBL (привести к POSIX и убрать None)."""
        if value is None:
            return ""
        try:
            text = str(value)
        except Exception:
            return ""
        text = text.strip()
        if not text:
            return ""
        return text.replace("\\", "/")

    def _select_combo_path(self, combo: QComboBox, raw_path: Any) -> None:
        """Выбрать элемент в комбобоксе по пути, добавляя при необходимости."""
        if combo is None:
            return
        path = self._normalize_ibl_path(raw_path)
        if not path:
            combo.setCurrentIndex(0)
            return
        target_index = -1
        for i in range(combo.count()):
            data = combo.itemData(i)
            if self._normalize_ibl_path(data) == path:
                target_index = i
                break
        if target_index < 0:
            # Добавляем элемент, чтобы пользователь видел фактический путь из настроек
            label = f"{Path(path).name} (config)"
            combo.addItem(label, path)
            target_index = combo.count() - 1
        combo.setCurrentIndex(target_index if target_index >= 0 else 0)

    def _build_fog_group(self) -> QGroupBox:
        """Создать группу Туман - расширенная (Fog Qt 6.10)"""
        group = QGroupBox("Туман", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        row = 0

        enabled = LoggingCheckBox("Включить туман", "environment.fog_enabled", self)
        enabled.clicked.connect(lambda checked: self._on_fog_enabled_clicked(checked))
        self._controls["fog.enabled"] = enabled
        grid.addWidget(enabled, row, 0, 1, 2)
        row += 1

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Цвет", self))
        fog_color = ColorButton()
        fog_color.color_changed.connect(
            lambda c: self._on_control_changed("fog_color", c)
        )
        self._controls["fog.color"] = fog_color
        color_row.addWidget(fog_color)
        color_row.addStretch(1)
        grid.addLayout(color_row, row, 0, 1, 2)
        row += 1

        density = LabeledSlider("Плотность", 0.0, 1.0, 0.01, decimals=2)
        density.valueChanged.connect(
            lambda v: self._on_control_changed("fog_density", v)
        )
        self._controls["fog.density"] = density
        grid.addWidget(density, row, 0, 1, 2)
        row += 1

        near_slider = LabeledSlider(
            "Начало (Near)", 0.0, 200.0, 50.0, decimals=0, unit="мм"
        )
        near_slider.valueChanged.connect(
            lambda v: self._on_control_changed("fog_near", v)
        )
        self._controls["fog.near"] = near_slider
        grid.addWidget(near_slider, row, 0, 1, 2)
        row += 1

        far_slider = LabeledSlider(
            "Конец (Far)", 400.0, 5000.0, 100.0, decimals=0, unit="мм"
        )
        far_slider.valueChanged.connect(
            lambda v: self._on_control_changed("fog_far", v)
        )
        self._controls["fog.far"] = far_slider
        grid.addWidget(far_slider, row, 0, 1, 2)
        row += 1

        # Высотный туман
        h_enabled = LoggingCheckBox(
            "Высотный туман (height)", "environment.fog_height_enabled", self
        )
        h_enabled.clicked.connect(
            lambda checked: self._on_control_changed("fog_height_enabled", checked)
        )
        self._controls["fog.height_enabled"] = h_enabled
        grid.addWidget(h_enabled, row, 0, 1, 2)
        row += 1

        least_y = LabeledSlider(
            "Наименее интенсивная высота Y",
            -100000.0,
            100000.0,
            50.0,
            decimals=0,
            unit="мм",
        )
        least_y.valueChanged.connect(
            lambda v: self._on_control_changed("fog_least_intense_y", v)
        )
        self._controls["fog.least_y"] = least_y
        grid.addWidget(least_y, row, 0, 1, 2)
        row += 1

        most_y = LabeledSlider(
            "Наиболее интенсивная высота Y",
            -100000.0,
            100000.0,
            50.0,
            decimals=0,
            unit="мм",
        )
        most_y.valueChanged.connect(
            lambda v: self._on_control_changed("fog_most_intense_y", v)
        )
        self._controls["fog.most_y"] = most_y
        grid.addWidget(most_y, row, 0, 1, 2)
        row += 1

        h_curve = LabeledSlider("Кривая высоты", 0.0, 4.0, 0.05, decimals=2)
        h_curve.valueChanged.connect(
            lambda v: self._on_control_changed("fog_height_curve", v)
        )
        self._controls["fog.height_curve"] = h_curve
        grid.addWidget(h_curve, row, 0, 1, 2)
        row += 1

        # Transmit
        t_enabled = LoggingCheckBox(
            "Учитывать передачу света (transmit)",
            "environment.fog_transmit_enabled",
            self,
        )
        t_enabled.clicked.connect(
            lambda checked: self._on_control_changed("fog_transmit_enabled", checked)
        )
        self._controls["fog.transmit_enabled"] = t_enabled
        grid.addWidget(t_enabled, row, 0, 1, 2)
        row += 1

        t_curve = LabeledSlider("Кривая передачи", 0.0, 4.0, 0.05, decimals=2)
        t_curve.valueChanged.connect(
            lambda v: self._on_control_changed("fog_transmit_curve", v)
        )
        self._controls["fog.transmit_curve"] = t_curve
        grid.addWidget(t_curve, row, 0, 1, 2)

        return group

    def _build_ao_group(self) -> QGroupBox:
        """Создать группу Ambient Occlusion - расширенная"""
        group = QGroupBox("Ambient Occlusion (SSAO)", self)
        grid = QGridLayout(group)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setHorizontalSpacing(12)
        grid.setVerticalSpacing(8)
        row = 0

        enabled = LoggingCheckBox("Включить SSAO", "environment.ao_enabled", self)
        enabled.clicked.connect(
            lambda checked: self._on_control_changed("ao_enabled", checked)
        )
        self._controls["ao.enabled"] = enabled
        grid.addWidget(enabled, row, 0, 1, 2)
        row += 1

        strength = LabeledSlider("Интенсивность", 0.0, 100.0, 1.0, decimals=0, unit="%")
        strength.valueChanged.connect(
            lambda v: self._on_control_changed("ao_strength", v)
        )
        self._controls["ao.strength"] = strength
        grid.addWidget(strength, row, 0, 1, 2)
        row += 1

        radius = LabeledSlider("Радиус", 0.5, 50.0, 0.1, decimals=1, unit="мм")
        radius.valueChanged.connect(lambda v: self._on_control_changed("ao_radius", v))
        self._controls["ao.radius"] = radius
        grid.addWidget(radius, row, 0, 1, 2)
        row += 1

        softness = LabeledSlider("Мягкость", 0.0, 50.0, 1.0, decimals=0)
        softness.valueChanged.connect(
            lambda v: self._on_control_changed("ao_softness", v)
        )
        self._controls["ao.softness"] = softness
        grid.addWidget(softness, row, 0, 1, 2)
        row += 1

        dither = LoggingCheckBox("Dither для AO", "environment.ao_dither", self)
        dither.clicked.connect(
            lambda checked: self._on_control_changed("ao_dither", checked)
        )
        self._controls["ao.dither"] = dither
        grid.addWidget(dither, row, 0, 1, 2)
        row += 1

        sample_rate = QComboBox(self)
        sample_rate.addItem("2x", 2)
        sample_rate.addItem("3x", 3)
        sample_rate.addItem("4x", 4)
        sample_rate.addItem("6x", 6)
        sample_rate.addItem("8x", 8)
        sample_rate.currentIndexChanged.connect(
            lambda _: self._on_control_changed(
                "ao_sample_rate", sample_rate.currentData()
            )
        )
        self._controls["ao.sample_rate"] = sample_rate
        grid.addWidget(QLabel("Сэмплов", self), row, 0)
        grid.addWidget(sample_rate, row, 1)

        return group

    # ========== ОБРАБОТЧИКИ ЧЕКБОКСОВ ==========(

    def _on_ibl_enabled_clicked(self, checked: bool) -> None:
        if self._updating_ui:
            return
        self._on_control_changed("ibl_enabled", checked)

    def _on_skybox_enabled_clicked(self, checked: bool) -> None:
        if self._updating_ui:
            return
        self._on_control_changed("skybox_enabled", checked)

    def _on_fog_enabled_clicked(self, checked: bool) -> None:
        if self._updating_ui:
            return
        self._on_control_changed("fog_enabled", checked)

    # ========== ОБЩИЙ ОБРАБОТЧИК =========

    def _on_control_changed(self, key: str, value: Any):
        if self._updating_ui:
            return
        state = self.get_state()
        self.environment_changed.emit(state)

    # ========== ГЕТТЕРЫ/СЕТТЕРЫ ==========

    def _require_control(self, key: str):
        control = self._controls.get(key)
        if control is None:
            raise KeyError(f"Control '{key}' is not registered")
        return control

    def get_state(self) -> Dict[str, Any]:
        """Получить текущее состояние всех параметров окружения"""
        raw_state = {
            "background_mode": self._require_control("background.mode").currentData(),
            "background_color": self._require_control("background.color")
            .color()
            .name(),
            "skybox_enabled": self._require_control(
                "background.skybox_enabled"
            ).isChecked(),
            "ibl_enabled": self._require_control("ibl.enabled").isChecked(),
            "ibl_intensity": self._require_control("ibl.intensity").value(),
            "probe_brightness": self._require_control("ibl.probe_brightness").value(),
            "probe_horizon": self._require_control("ibl.probe_horizon").value(),
            "ibl_rotation": self._require_control("ibl.rotation").value(),
            "ibl_source": self._normalize_ibl_path(
                self._require_control("ibl.file").currentData()
            ),
            "ibl_fallback": self._normalize_ibl_path(
                self._require_control("ibl.fallback").currentData()
            ),
            "skybox_blur": self._require_control("skybox.blur").value(),
            "ibl_offset_x": self._require_control("ibl.offset_x").value(),
            "ibl_offset_y": self._require_control("ibl.offset_y").value(),
            "ibl_bind_to_camera": self._require_control("ibl.bind").isChecked(),
            "reflection_enabled": self._require_control(
                "reflection.enabled"
            ).isChecked(),
            "reflection_padding_m": self._require_control("reflection.padding").value(),
            "reflection_quality": self._require_control(
                "reflection.quality"
            ).currentData(),
            "reflection_refresh_mode": self._require_control(
                "reflection.refresh_mode"
            ).currentData(),
            "reflection_time_slicing": self._require_control(
                "reflection.time_slicing"
            ).currentData(),
            "fog_enabled": self._require_control("fog.enabled").isChecked(),
            "fog_color": self._require_control("fog.color").color().name(),
            "fog_density": self._require_control("fog.density").value(),
            "fog_near": self._require_control("fog.near").value(),
            "fog_far": self._require_control("fog.far").value(),
            "fog_height_enabled": self._require_control(
                "fog.height_enabled"
            ).isChecked(),
            "fog_least_intense_y": self._require_control("fog.least_y").value(),
            "fog_most_intense_y": self._require_control("fog.most_y").value(),
            "fog_height_curve": self._require_control("fog.height_curve").value(),
            "fog_transmit_enabled": self._require_control(
                "fog.transmit_enabled"
            ).isChecked(),
            "fog_transmit_curve": self._require_control("fog.transmit_curve").value(),
            "ao_enabled": self._require_control("ao.enabled").isChecked(),
            "ao_strength": self._require_control("ao.strength").value(),
            "ao_radius": self._require_control("ao.radius").value(),
            "ao_softness": self._require_control("ao.softness").value(),
            "ao_dither": self._require_control("ao.dither").isChecked(),
            "ao_sample_rate": self._require_control("ao.sample_rate").currentData(),
        }
        return validate_environment_settings(raw_state)

    def set_state(self, state: Dict[str, Any]):
        """Установить состояние из словаря"""
        validated = validate_environment_settings(state)
        self._updating_ui = True
        for control in self._controls.values():
            try:
                control.blockSignals(True)
            except Exception:
                pass
        try:
            combo = self._require_control("background.mode")
            idx = combo.findData(validated["background_mode"])
            if idx >= 0:
                combo.setCurrentIndex(idx)
            self._require_control("background.color").set_color(
                validated["background_color"]
            )
            self._require_control("background.skybox_enabled").setChecked(
                validated["skybox_enabled"]
            )

            self._require_control("ibl.enabled").setChecked(validated["ibl_enabled"])
            self._require_control("ibl.intensity").set_value(validated["ibl_intensity"])
            self._require_control("ibl.probe_brightness").set_value(
                validated["probe_brightness"]
            )
            self._require_control("ibl.probe_horizon").set_value(
                validated["probe_horizon"]
            )
            self._require_control("ibl.rotation").set_value(validated["ibl_rotation"])
            self._select_combo_path(
                self._require_control("ibl.file"), validated["ibl_source"]
            )
            self._select_combo_path(
                self._require_control("ibl.fallback"), validated["ibl_fallback"]
            )
            self._require_control("skybox.blur").set_value(validated["skybox_blur"])
            self._require_control("ibl.offset_x").set_value(validated["ibl_offset_x"])
            self._require_control("ibl.offset_y").set_value(validated["ibl_offset_y"])
            self._require_control("ibl.bind").setChecked(
                validated["ibl_bind_to_camera"]
            )

            self._require_control("reflection.enabled").setChecked(
                validated["reflection_enabled"]
            )
            self._require_control("reflection.padding").set_value(
                validated["reflection_padding_m"]
            )
            quality_combo = self._require_control("reflection.quality")
            idx_quality = quality_combo.findData(validated["reflection_quality"])
            if idx_quality >= 0:
                quality_combo.setCurrentIndex(idx_quality)

            refresh_combo = self._require_control("reflection.refresh_mode")
            idx_refresh = refresh_combo.findData(validated["reflection_refresh_mode"])
            if idx_refresh >= 0:
                refresh_combo.setCurrentIndex(idx_refresh)

            slicing_combo = self._require_control("reflection.time_slicing")
            idx_slicing = slicing_combo.findData(validated["reflection_time_slicing"])
            if idx_slicing >= 0:
                slicing_combo.setCurrentIndex(idx_slicing)

            self._require_control("fog.enabled").setChecked(validated["fog_enabled"])
            self._require_control("fog.color").set_color(validated["fog_color"])
            self._require_control("fog.density").set_value(validated["fog_density"])
            self._require_control("fog.near").set_value(validated["fog_near"])
            self._require_control("fog.far").set_value(validated["fog_far"])
            self._require_control("fog.height_enabled").setChecked(
                validated["fog_height_enabled"]
            )
            self._require_control("fog.least_y").set_value(
                validated["fog_least_intense_y"]
            )
            self._require_control("fog.most_y").set_value(
                validated["fog_most_intense_y"]
            )
            self._require_control("fog.height_curve").set_value(
                validated["fog_height_curve"]
            )
            self._require_control("fog.transmit_enabled").setChecked(
                validated["fog_transmit_enabled"]
            )
            self._require_control("fog.transmit_curve").set_value(
                validated["fog_transmit_curve"]
            )

            self._require_control("ao.enabled").setChecked(validated["ao_enabled"])
            self._require_control("ao.strength").set_value(validated["ao_strength"])
            self._require_control("ao.radius").set_value(validated["ao_radius"])
            self._require_control("ao.softness").set_value(validated["ao_softness"])
            self._require_control("ao.dither").setChecked(validated["ao_dither"])
            combo = self._require_control("ao.sample_rate")
            idx = combo.findData(validated["ao_sample_rate"])
            if idx >= 0:
                combo.setCurrentIndex(idx)
            elif combo.count():
                combo.setCurrentIndex(combo.count() - 1)
        finally:
            for control in self._controls.values():
                try:
                    control.blockSignals(False)
                except Exception:
                    pass
            self._updating_ui = False

    def get_controls(self) -> Dict[str, Any]:
        return self._controls

    def set_updating_ui(self, updating: bool) -> None:
        self._updating_ui = updating
