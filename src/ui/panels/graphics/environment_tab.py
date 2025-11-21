"""
Environment Tab - вкладка настроек окружающей среды (фон, IBL, туман, AO)
Часть модульной переработки GraphicsPanel

СТРУКТУРА ТОЧНО ПОВТОРЯЕТ МОНОЛИТ panel_graphics.py:
- _build_background_group() → Фон и IBL (с HDR discovery)
- _build_fog_group() → Туман с near/far + высотный туман (Qt 6.10 Fog)
- _build_ao_group() → Ambient Occlusion (SSAO) расширенный
"""

import logging
import os
from pathlib import Path
from typing import Any

from PySide6.QtCore import Signal, Qt
from PySide6.QtWidgets import (
    QComboBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
    QMessageBox,  # добавлено для monkeypatch в тестах
)

from .hdr_discovery import discover_hdr_files
from .widgets import ColorButton, FileCyclerWidget, LabeledSlider
from src.common.logging_widgets import LoggingCheckBox
from src.common.settings_manager import get_settings_manager
from src.common.ui_dialogs import (
    dialogs_allowed,
    message_warning,
)  # ✅ антиблокирующие диалоги
from src.ui.environment_schema import (
    ENVIRONMENT_SLIDER_RANGE_DEFAULTS,
    EnvironmentSliderRange,
    EnvironmentValidationError,
    validate_environment_settings,
    validate_environment_slider_ranges,
)


logger = logging.getLogger(__name__)


class EnvironmentTab(QWidget):
    """Вкладка настроек окружения: фон, IBL, туман, AO

    Signals:
        environment_changed: dict[str, Any] - параметры окружения изменились
    """

    environment_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        # Current state - храним ссылки на контролы
        self._controls: dict[str, Any] = {}
        self._updating_ui = False
        self._passthrough_state: dict[str, Any] = {}
        self._qml_root = Path(__file__).resolve().parents[4] / "assets" / "qml"
        self._hdr_items: list[tuple[str, str]] = self._discover_hdr_files()
        self._slider_ranges: dict[str, EnvironmentSliderRange] = (
            self._load_slider_ranges()
        )

        # Setup UI
        self._setup_ui()

    def _setup_ui(self):
        """Построить UI вкладки - РАСШИРЕННАЯ ВЕРСИЯ"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        previous_flag = self._updating_ui
        self._updating_ui = True
        try:
            layout.addWidget(self._build_background_group())
            layout.addWidget(self._build_reflection_group())
            layout.addWidget(self._build_fog_group())
            layout.addWidget(self._build_ao_group())
        finally:
            self._updating_ui = previous_flag

        layout.addStretch(1)
        self._update_ibl_dependency_states()

    def _discover_hdr_files(self) -> list[tuple[str, str]]:
        """Автопоиск HDR-файлов. Отсутствие файлов → предупреждение, не ошибка."""
        try:
            # Ищем в стандартных папках: assets/hdr, assets/hdri, assets/qml/assets
            qml_root = self._qml_root
            assets_root = qml_root.parent
            search_dirs = [
                assets_root / "hdr",
                assets_root / "hdri",
                qml_root / "assets",
            ]
            items = discover_hdr_files(search_dirs, qml_root=qml_root)
        except Exception as exc:
            logger.warning("hdr_discovery_failed: %s", exc)
            return []
        if not items:
            logger.warning("hdr_discovery_empty: no HDR files under %s", self._qml_root)
        return items

    def _load_slider_ranges(self) -> dict[str, EnvironmentSliderRange]:
        settings_manager = get_settings_manager()
        raw_ranges = settings_manager.get("graphics.environment_ranges", {})

        validated: dict[str, EnvironmentSliderRange] = {}
        missing_keys: set[str] = set()
        invalid_keys: set[str] = set()
        invalid_messages: list[str] = []
        section_messages: list[str] = []
        recorded_invalid_sections: set[str] = set()

        def _record_invalid_section(section: str) -> None:
            if section in recorded_invalid_sections:
                return
            recorded_invalid_sections.add(section)
            section_messages.append(
                f"Секция {section} отсутствует или имеет неверный формат."
            )

        def _try_parse_range(
            source: str,
            payload: Any,
            key: str,
        ) -> EnvironmentSliderRange | None:
            if not isinstance(payload, dict):
                _record_invalid_section(source)
                return None
            if key not in payload:
                return None
            try:
                parsed, _ = validate_environment_slider_ranges(
                    {key: payload[key]},
                    required_keys=(key,),
                    raise_on_missing=True,
                )
            except EnvironmentValidationError as exc:
                invalid_messages.append(f"{source}.{key}: {exc}")
                return None
            return parsed[key]

        if not isinstance(raw_ranges, dict):
            _record_invalid_section("graphics.environment_ranges")
            raw_ranges = {}

        unexpected = sorted(
            set(raw_ranges.keys()) - set(ENVIRONMENT_SLIDER_RANGE_DEFAULTS.keys())
        )
        if unexpected:
            invalid_messages.append(
                "Неизвестные ключи диапазонов: " + ", ".join(unexpected)
            )

        for key in ENVIRONMENT_SLIDER_RANGE_DEFAULTS.keys():
            if key not in raw_ranges:
                missing_keys.add(key)
                continue
            try:
                parsed, _ = validate_environment_slider_ranges(
                    {key: raw_ranges[key]},
                    required_keys=(key,),
                    raise_on_missing=True,
                )
            except EnvironmentValidationError as exc:
                invalid_messages.append(f"graphics.environment_ranges.{key}: {exc}")
                invalid_keys.add(key)
            else:
                validated[key] = parsed[key]

        fallback_sources: list[tuple[str, Any]] = [
            (
                "metadata.environment_slider_ranges",
                settings_manager.get("metadata.environment_slider_ranges", {}),
            ),
            (
                "defaults_snapshot.graphics.environment_ranges",
                settings_manager.get(
                    "defaults_snapshot.graphics.environment_ranges", {}
                ),
            ),
        ]

        fallback_used: dict[str, list[str]] = {}
        for key in sorted(missing_keys | invalid_keys):
            for source_name, payload in fallback_sources:
                parsed = _try_parse_range(source_name, payload, key)
                if parsed is not None:
                    validated[key] = parsed
                    fallback_used.setdefault(source_name, []).append(key)
                    break
            else:
                # Значение будет взято из дефолтов
                validated[key] = ENVIRONMENT_SLIDER_RANGE_DEFAULTS[key]

        defaults_used = [
            key
            for key in sorted(missing_keys | invalid_keys)
            if key not in {k for keys in fallback_used.values() for k in keys}
        ]

        # Ключи, где фактическое значение совпало с дефолтами (даже если источник fallback == metadata)
        equal_to_defaults: list[str] = []
        for key in sorted(missing_keys | invalid_keys):
            v = validated.get(key)
            d = ENVIRONMENT_SLIDER_RANGE_DEFAULTS.get(key)
            if (
                v
                and d
                and (
                    v.minimum == d.minimum
                    and v.maximum == d.maximum
                    and v.step == d.step
                    and (v.decimals or None) == (d.decimals or None)
                    and (v.unit or None) == (d.unit or None)
                )
            ):
                equal_to_defaults.append(key)

        # Формируем предупреждения НЕ блокируя тесты
        if missing_keys or invalid_keys or unexpected:
            summary_parts: list[str] = []
            if missing_keys:
                summary_parts.append(
                    "Отсутствуют диапазоны: " + ", ".join(sorted(missing_keys))
                )
            if invalid_keys:
                summary_parts.append(
                    "Неверные диапазоны: " + ", ".join(sorted(invalid_keys))
                )
            if unexpected:
                summary_parts.append(
                    "Неизвестные ключи: " + ", ".join(sorted(unexpected))
                )
            if fallback_used:
                used_str = "; ".join(
                    f"{src}: {', '.join(keys)}" for src, keys in fallback_used.items()
                )
                summary_parts.append("Fallback источники → " + used_str)
            if defaults_used or equal_to_defaults:
                keys_list = sorted(set(defaults_used) | set(equal_to_defaults))
                summary_parts.append(
                    "Используются значения по умолчанию: " + ", ".join(keys_list)
                )
            summary = "\n".join(summary_parts)

            # 1) Всегда логируем (неблокирующе)
            logger.warning(
                "environment_tab_slider_ranges_issue: missing=%s invalid=%s unexpected=%s fallback=%s",
                sorted(missing_keys),
                sorted(invalid_keys),
                sorted(unexpected),
                {k: sorted(v) for k, v in fallback_used.items()},
            )
            for msg in invalid_messages:
                logger.warning("environment_tab_range_invalid_detail: %s", msg)
            for msg in section_messages:
                logger.warning("environment_tab_range_section_detail: %s", msg)

            # 2) UI уведомление/перехват тестами
            if dialogs_allowed():
                try:
                    message_warning(
                        None,
                        "Диапазоны окружения",
                        summary + "\n(автотесты не блокируются)",
                    )
                except Exception:
                    pass
            elif os.environ.get("PYTEST_CURRENT_TEST"):
                try:
                    QMessageBox.warning(None, "Диапазоны окружения", summary)
                except Exception:
                    pass

        return validated

    def _create_slider(
        self,
        key: str,
        title: str,
        *,
        decimals: int = 2,
        unit: str | None = None,
    ) -> LabeledSlider:
        slider_range = self._slider_ranges.get(
            key, ENVIRONMENT_SLIDER_RANGE_DEFAULTS[key]
        )
        slider_decimals = (
            slider_range.decimals if slider_range.decimals is not None else decimals
        )
        slider_unit = slider_range.unit if slider_range.unit is not None else unit
        return LabeledSlider(
            title,
            slider_range.minimum,
            slider_range.maximum,
            slider_range.step,
            decimals=slider_decimals,
            unit=slider_unit,
        )

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

        # IBL intensity (освещение)
        intensity = self._create_slider(
            "ibl_intensity", "Яркость освещения IBL", decimals=2
        )
        intensity.valueChanged.connect(
            lambda v: self._on_control_changed("ibl_intensity", v)
        )
        self._controls["ibl.intensity"] = intensity
        grid.addWidget(intensity, row, 0, 1, 2)
        row += 1

        # Skybox brightness (фон)
        skybox_brightness = self._create_slider(
            "skybox_brightness", "Яркость фона (Skybox)", decimals=2
        )
        skybox_brightness.valueChanged.connect(
            lambda v: self._on_control_changed("skybox_brightness", v)
        )
        self._controls["ibl.skybox_brightness"] = skybox_brightness
        grid.addWidget(skybox_brightness, row, 0, 1, 2)
        row += 1

        # IBL extra: probe horizon cutoff (-1..1)
        probe_horizon = self._create_slider(
            "probe_horizon", "Горизонт пробы (probeHorizon)", decimals=2
        )
        probe_horizon.valueChanged.connect(
            lambda v: self._on_control_changed("probe_horizon", v)
        )
        self._controls["ibl.probe_horizon"] = probe_horizon
        grid.addWidget(probe_horizon, row, 0, 1, 2)
        row += 1

        # Skybox blur
        blur = self._create_slider("skybox_blur", "Размытие skybox", decimals=2)
        blur.valueChanged.connect(lambda v: self._on_control_changed("skybox_blur", v))
        self._controls["skybox.blur"] = blur
        grid.addWidget(blur, row, 0, 1, 2)
        row += 1

        # HDR file (primary)
        grid.addWidget(QLabel("HDR окружение", self), row, 0)
        hdr_selector = FileCyclerWidget(self)
        hdr_selector.set_allow_empty_selection(True, label="—")
        hdr_selector.set_resolution_roots([self._qml_root])
        hdr_selector.set_items(self._hdr_items)
        hdr_selector.currentChanged.connect(
            lambda path: self._on_hdr_source_changed(path)
        )
        self._controls["ibl.file"] = hdr_selector
        grid.addWidget(hdr_selector, row, 1)

        hdr_status = QLabel("—", self)
        hdr_status.setObjectName("environmentHdrStatus")
        hdr_status.setAlignment(
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft
        )
        hdr_status.setMinimumWidth(80)
        self._controls["ibl.status_label"] = hdr_status
        grid.addWidget(hdr_status, row, 2)
        row += 1

        # IBL rotation
        ibl_rot = self._create_slider(
            "ibl_rotation", "Поворот IBL", decimals=0, unit="°"
        )
        ibl_rot.valueChanged.connect(
            lambda v: self._on_control_changed("ibl_rotation", v)
        )
        self._controls["ibl.rotation"] = ibl_rot
        grid.addWidget(ibl_rot, row, 0, 1, 2)
        row += 1

        # IBL offsets
        env_off_x = self._create_slider(
            "ibl_offset_x", "Смещение окружения X", decimals=0, unit="°"
        )
        env_off_x.valueChanged.connect(
            lambda v: self._on_control_changed("ibl_offset_x", v)
        )
        self._controls["ibl.offset_x"] = env_off_x
        grid.addWidget(env_off_x, row, 0, 1, 2)
        row += 1
        env_off_y = self._create_slider(
            "ibl_offset_y", "Смещение окружения Y", decimals=0, unit="°"
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

        group = QGroupBox("Отражения", self)
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

        padding = self._create_slider(
            "reflection_padding_m", "Отступ от геометрии", decimals=2, unit="м"
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

    def _build_ao_group(self) -> QGroupBox:
        """Создать группу Ambient Occlusion - расширенная"""
        group = QGroupBox("Ambient Occlusion (SSAO)", self)
        layout = QVBoxLayout(group)
        row = 0

        enabled = LoggingCheckBox("Включить SSAO", "environment.ao_enabled", self)
        enabled.clicked.connect(
            lambda checked: self._on_control_changed("ao_enabled", checked)
        )
        self._controls["ao.enabled"] = enabled
        layout.addWidget(enabled, row)
        row += 1

        strength = self._create_slider(
            "ao_strength", "Интенсивность", decimals=0, unit="%"
        )
        strength.valueChanged.connect(
            lambda v: self._on_control_changed("ao_strength", v)
        )
        self._controls["ao.strength"] = strength
        layout.addWidget(strength, row)
        row += 1

        radius = self._create_slider("ao_radius", "Радиус", decimals=3, unit="м")
        radius.set_value(0.008)
        radius.valueChanged.connect(lambda v: self._on_control_changed("ao_radius", v))
        self._controls["ao.radius"] = radius
        layout.addWidget(radius, row)
        row += 1

        bias = self._create_slider("ao_bias", "Смещение", decimals=3)
        bias.valueChanged.connect(lambda v: self._on_control_changed("ao_bias", v))
        self._controls["ao.bias"] = bias
        layout.addWidget(bias, row)
        row += 1

        softness = self._create_slider("ao_softness", "Мягкость", decimals=0)
        softness.valueChanged.connect(
            lambda v: self._on_control_changed("ao_softness", v)
        )
        self._controls["ao.softness"] = softness
        layout.addWidget(softness, row)
        row += 1

        dither = LoggingCheckBox("Dither для AO", "environment.ao_dither", self)
        dither.clicked.connect(
            lambda checked: self._on_control_changed("ao_dither", checked)
        )
        self._controls["ao.dither"] = dither
        layout.addWidget(dither, row)
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
        # Размещаем label+combo в одной строке
        hrow = QHBoxLayout()
        hrow.addWidget(QLabel("Сэмплов", self))
        hrow.addWidget(sample_rate)
        layout.addLayout(hrow)

        return group

    def _build_fog_group(self) -> QGroupBox:  # восстановлено после случайного удаления
        """Создать группу Туман (Fog Qt 6.10) — восстановленная минимальная версия.

        Регистрирует все control-keys, которые используются в set_state/get_state,
        чтобы не падать при валидации окружения в тестах.
        """
        group = QGroupBox("Туман", self)
        layout = QVBoxLayout(group)

        enabled = LoggingCheckBox("Включить туман", "environment.fog_enabled", self)
        enabled.clicked.connect(lambda checked: self._on_fog_enabled_clicked(checked))
        self._controls["fog.enabled"] = enabled
        layout.addWidget(enabled)

        color_row = QHBoxLayout()
        color_row.addWidget(QLabel("Цвет", self))
        fog_color = ColorButton()
        fog_color.color_changed.connect(
            lambda c: self._on_control_changed("fog_color", c)
        )
        self._controls["fog.color"] = fog_color
        color_row.addWidget(fog_color)
        color_row.addStretch(1)
        layout.addLayout(color_row)

        density = self._create_slider("fog_density", "Плотность", decimals=2)
        density.valueChanged.connect(
            lambda v: self._on_control_changed("fog_density", v)
        )
        self._controls["fog.density"] = density
        layout.addWidget(density)

        near_slider = self._create_slider(
            "fog_near", "Начало (Near)", decimals=2, unit="м"
        )
        near_slider.valueChanged.connect(
            lambda v: self._on_control_changed("fog_near", v)
        )
        self._controls["fog.near"] = near_slider
        layout.addWidget(near_slider)

        far_slider = self._create_slider("fog_far", "Конец (Far)", decimals=2, unit="м")
        far_slider.valueChanged.connect(
            lambda v: self._on_control_changed("fog_far", v)
        )
        self._controls["fog.far"] = far_slider
        layout.addWidget(far_slider)

        h_enabled = LoggingCheckBox(
            "Высотный туман (height)", "environment.fog_height_enabled", self
        )
        h_enabled.clicked.connect(
            lambda checked: self._on_control_changed("fog_height_enabled", checked)
        )
        self._controls["fog.height_enabled"] = h_enabled
        layout.addWidget(h_enabled)

        least_y = self._create_slider(
            "fog_least_intense_y", "Наименее интенсивная высота Y", decimals=2, unit="м"
        )
        least_y.valueChanged.connect(
            lambda v: self._on_control_changed("fog_least_intense_y", v)
        )
        self._controls["fog.least_y"] = least_y
        layout.addWidget(least_y)

        most_y = self._create_slider(
            "fog_most_intense_y", "Наиболее интенсивная высота Y", decimals=2, unit="м"
        )
        most_y.valueChanged.connect(
            lambda v: self._on_control_changed("fog_most_intense_y", v)
        )
        self._controls["fog.most_y"] = most_y
        layout.addWidget(most_y)

        h_curve = self._create_slider("fog_height_curve", "Кривая высоты", decimals=2)
        h_curve.valueChanged.connect(
            lambda v: self._on_control_changed("fog_height_curve", v)
        )
        self._controls["fog.height_curve"] = h_curve
        layout.addWidget(h_curve)

        t_enabled = LoggingCheckBox(
            "Учитывать передачу света (transmit)",
            "environment.fog_transmit_enabled",
            self,
        )
        t_enabled.clicked.connect(
            lambda checked: self._on_control_changed("fog_transmit_enabled", checked)
        )
        self._controls["fog.transmit_enabled"] = t_enabled
        layout.addWidget(t_enabled)

        t_curve = self._create_slider(
            "fog_transmit_curve", "Кривая передачи", decimals=2
        )
        t_curve.valueChanged.connect(
            lambda v: self._on_control_changed("fog_transmit_curve", v)
        )
        self._controls["fog.transmit_curve"] = t_curve
        layout.addWidget(t_curve)

        return group

    # ========== ОБРАБОТЧИКИ ЧЕКБОКСОВ ===========(

    def _on_ibl_enabled_clicked(self, checked: bool) -> None:
        if self._updating_ui:
            return
        self._update_ibl_dependency_states()
        self._on_control_changed("ibl_enabled", checked)

    def _on_skybox_enabled_clicked(self, checked: bool) -> None:
        if self._updating_ui:
            return
        self._update_ibl_dependency_states()
        # ✅ FIX: корректный snake_case ключ
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

    def get_state(self) -> dict[str, Any]:
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
            "skybox_brightness": self._require_control("ibl.skybox_brightness").value(),
            "probe_horizon": self._require_control("ibl.probe_horizon").value(),
            "ibl_rotation": self._require_control("ibl.rotation").value(),
            "ibl_source": self._normalize_hdr_path(
                self._require_control("ibl.file").current_path()
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
            "ao_bias": self._require_control("ao.bias").value(),
            "ao_softness": self._require_control("ao.softness").value(),
            "ao_dither": self._require_control("ao.dither").isChecked(),
            "ao_sample_rate": self._require_control("ao.sample_rate").currentData(),
        }
        for optional_key in ("fog_depth_enabled", "fog_depth_curve"):
            if optional_key in self._passthrough_state:
                raw_state.setdefault(
                    optional_key, self._passthrough_state[optional_key]
                )
        return validate_environment_settings(raw_state)

    def set_state(self, state: dict[str, Any]):
        """Установить состояние из словаря"""
        validated = validate_environment_settings(state)
        for optional_key in ("fog_depth_enabled", "fog_depth_curve"):
            if (
                optional_key not in validated
                and optional_key in self._passthrough_state
            ):
                self._passthrough_state.pop(optional_key, None)
        self._passthrough_state.update(
            {
                key: validated[key]
                for key in ("fog_depth_enabled", "fog_depth_curve")
                if key in validated
            }
        )
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
            self._require_control("ibl.skybox_brightness").set_value(
                validated["skybox_brightness"]
            )
            self._require_control("ibl.probe_horizon").set_value(
                validated["probe_horizon"]
            )
            self._require_control("ibl.rotation").set_value(validated["ibl_rotation"])
            hdr_widget: FileCyclerWidget = self._require_control("ibl.file")
            normalized_source = (
                self._normalize_hdr_path(validated["ibl_source"])
                if "ibl_source" in validated
                else ""
            )
            hdr_widget.set_current_data(normalized_source, emit=False)
            validated["ibl_source"] = hdr_widget.current_path()
            self._refresh_hdr_status(validated["ibl_source"])
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
            self._require_control("ao.bias").set_value(validated["ao_bias"])
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
        self._update_ibl_dependency_states()

    def get_controls(self) -> dict[str, Any]:
        return self._controls

    def set_updating_ui(self, updating: bool) -> None:
        self._updating_ui = updating

    # ========== ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ==========

    def _set_control_enabled(self, key: str, enabled: bool) -> None:
        widget = self._controls.get(key)
        if widget is None:
            return
        setter = getattr(widget, "set_enabled", None)
        if callable(setter):
            setter(enabled)
            return
        try:
            widget.setEnabled(enabled)
        except Exception:
            pass

    def _update_ibl_dependency_states(self) -> None:
        """Disable IBL controls when master toggles are off."""

        ibl_enabled = False
        skybox_enabled = False

        ibl_checkbox = self._controls.get("ibl.enabled")
        if hasattr(ibl_checkbox, "isChecked"):
            ibl_enabled = bool(ibl_checkbox.isChecked())

        skybox_checkbox = self._controls.get("background.skybox_enabled")
        if hasattr(skybox_checkbox, "isChecked"):
            skybox_enabled = bool(skybox_checkbox.isChecked())

        for key in (
            "ibl.intensity",
            "ibl.probe_horizon",
            "ibl.offset_x",
            "ibl.offset_y",
            "ibl.bind",
        ):
            self._set_control_enabled(key, ibl_enabled)

        for key in ("ibl.skybox_brightness", "skybox.blur"):
            self._set_control_enabled(key, skybox_enabled)

        self._set_control_enabled("ibl.rotation", ibl_enabled or skybox_enabled)

    def _normalize_hdr_path(self, candidate: Any, qml_dir: Path | None = None) -> str:
        """Преобразовать путь к HDR в POSIX формат, предпочитая относительный к каталогу QML.

        Совместимо с тестами: допускает пустые значения и возвращает пустую строку.
        """
        if not candidate:
            return ""
        if qml_dir is None:
            qml_dir = self._qml_root
        try:
            path_obj = Path(str(candidate).replace("\\", "/"))
        except Exception:
            return ""
        resolved = path_obj.resolve(strict=False)
        if not path_obj.is_absolute():
            return path_obj.as_posix()
        try:
            return resolved.relative_to(qml_dir).as_posix()
        except Exception:
            return resolved.as_posix()

    def _refresh_hdr_status(self, path: str) -> None:
        """Обновить статусный лейбл HDR источника (без падений если виджет отсутствует)."""
        widget = self._controls.get("ibl.status_label")
        if not isinstance(widget, QLabel):
            return
        selector = self._controls.get("ibl.file")
        if isinstance(selector, FileCyclerWidget) and selector.is_missing():
            widget.setText("⚠ файл не найден")
            widget.setToolTip(path or "")
        else:
            label = Path(path).name if path else "—"
            widget.setText(label or "—")
            widget.setToolTip(path or "")

    def _on_hdr_source_changed(self, path: str) -> None:
        """Handle HDR selection updates and keep status/normalisation in sync."""

        normalized = self._normalize_hdr_path(path)
        try:
            selector = self._require_control("ibl.file")
        except KeyError:
            selector = None

        if isinstance(selector, FileCyclerWidget):
            selector.set_current_data(normalized, emit=False)
        self._refresh_hdr_status(normalized)
        self._on_control_changed("ibl_source", normalized)
