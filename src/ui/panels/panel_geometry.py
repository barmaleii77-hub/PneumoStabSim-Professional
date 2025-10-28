# -*- coding: utf-8 -*-
"""
Geometry configuration panel - РУССКИЙ ИНТЕРФЕЙС
Полная интеграция с SettingsManager без дефолтов в коде.
Чтение при запуске, запись при выходе (централизованно в MainWindow).
"""

from __future__ import annotations

from typing import Optional

from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QGroupBox,
    QCheckBox,
    QPushButton,
    QLabel,
    QMessageBox,
    QSizePolicy,
    QComboBox,
)
from PySide6.QtCore import Signal, Slot, Qt
from PySide6.QtGui import QFont

from ..widgets import RangeSlider
from src.common.settings_manager import get_settings_manager


class GeometryPanel(QWidget):
    parameter_changed = Signal(str, float)
    geometry_updated = Signal(dict)
    geometry_changed = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._settings_manager = get_settings_manager()
        self.parameters: dict[str, float | bool] = {}
        self._resolving_conflict = False
        self._syncing_rods = False
        self._rod_link_snapshot: tuple[float, float] | None = None

        from src.common import get_category_logger

        self.logger = get_category_logger("GeometryPanel")

        # 1) Загружаем состояние из JSON СНАЧАЛА
        self._load_from_settings()

        # 2) Строим UI на основе загруженных значений (никаких дефолтов в коде)
        self._setup_ui()

        # 3) Подключаем сигналы
        self._connect_signals()

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        # 4) Отправляем начальные параметры
        from PySide6.QtCore import QTimer

        QTimer.singleShot(300, self._emit_initial)

    def _emit_initial(self):
        payload = self._get_fast_geometry_update("init", 0.0)
        self.geometry_changed.emit(payload)
        self.geometry_updated.emit(self.parameters.copy())

    # Чтение только из JSON
    def _load_from_settings(self) -> None:
        data = self._settings_manager.get_category("geometry") or {}
        self.parameters.update(data)
        if "rod_diameter_rear_m" not in self.parameters:
            self.parameters["rod_diameter_rear_m"] = float(
                self.parameters.get("rod_diameter_m", 0.035) or 0.035
            )
        self.logger.info("✅ Geometry loaded from app_settings.json (no code defaults)")

    # UI из параметров
    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(8)
        layout.setContentsMargins(8, 8, 8, 8)

        title_label = QLabel("Геометрия автомобиля")
        font = QFont()
        font.setPointSize(12)
        font.setBold(True)
        title_label.setFont(font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("Пресет:"))
        self.preset_combo = QComboBox()
        self.preset_combo.addItems(
            [
                "Стандартный грузовик",
                "Лёгкий коммерческий",
                "Тяжёлый грузовик",
                "Пользовательский",
            ]
        )
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_row.addWidget(self.preset_combo, 1)
        layout.addLayout(preset_row)

        layout.addWidget(self._create_frame_group())
        layout.addWidget(self._create_suspension_group())
        layout.addWidget(self._create_cylinder_group())
        layout.addWidget(self._create_options_group())

        self.rod_diameter_rear_slider.setEnabled(
            not self.link_rod_diameters.isChecked()
        )

        btns = QHBoxLayout()
        reset_btn = QPushButton("↩︎ Сбросить (defaults)")
        reset_btn.setToolTip(
            "Сбросить к значениям из defaults_snapshot в config/app_settings.json"
        )
        reset_btn.clicked.connect(self._reset_to_defaults)
        btns.addWidget(reset_btn)

        save_defaults_btn = QPushButton("💾 Сохранить как дефолт")
        save_defaults_btn.setToolTip(
            "Сохранить текущую геометрию как defaults_snapshot"
        )
        save_defaults_btn.clicked.connect(self._save_current_as_defaults)
        btns.addWidget(save_defaults_btn)

        validate_btn = QPushButton("Проверить")
        validate_btn.clicked.connect(self._validate_geometry)
        btns.addWidget(validate_btn)

        btns.addStretch()
        layout.addLayout(btns)
        layout.addStretch()

    def _create_frame_group(self) -> QGroupBox:
        group = QGroupBox("Размеры рамы")
        v = QVBoxLayout(group)
        self.wheelbase_slider = RangeSlider(
            minimum=2.0,
            maximum=4.0,
            value=float(self.parameters.get("wheelbase", 0) or 0),
            step=0.001,
            decimals=3,
            units="м",
            title="База (колёсная)",
        )
        self.wheelbase_slider.setToolTip(
            "Длина рамы по оси Z. Определяет положение передних/задних рогов."
        )
        v.addWidget(self.wheelbase_slider)
        self.track_slider = RangeSlider(
            minimum=1.0,
            maximum=2.5,
            value=float(self.parameters.get("track", 0) or 0),
            step=0.001,
            decimals=3,
            units="м",
            title="Колея",
        )
        self.track_slider.setToolTip(
            "Влияет ТОЛЬКО на позицию оси хвостовика цилиндра: X = ±колея/2. Не влияет на расстояние ‘Рама → ось рычага’."
        )
        v.addWidget(self.track_slider)
        return group

    def _create_suspension_group(self) -> QGroupBox:
        group = QGroupBox("Геометрия подвески")
        v = QVBoxLayout(group)
        self.frame_to_pivot_slider = RangeSlider(
            minimum=0.3,
            maximum=1.0,
            value=float(self.parameters.get("frame_to_pivot", 0) or 0),
            step=0.001,
            decimals=3,
            units="м",
            title="Рама → ось рычага",
        )
        self.frame_to_pivot_slider.setToolTip(
            "Абсолютное поперечное расстояние от центра рамы до оси рычага. НЕ зависит от ‘Колея’."
        )
        v.addWidget(self.frame_to_pivot_slider)
        self.lever_length_slider = RangeSlider(
            minimum=0.5,
            maximum=1.5,
            value=float(self.parameters.get("lever_length", 0) or 0),
            step=0.001,
            decimals=3,
            units="м",
            title="Длина рычага",
        )
        v.addWidget(self.lever_length_slider)
        self.rod_position_slider = RangeSlider(
            minimum=0.3,
            maximum=0.9,
            value=float(self.parameters.get("rod_position", 0) or 0),
            step=0.001,
            decimals=3,
            units="",
            title="Положение крепления штока (доля)",
        )
        v.addWidget(self.rod_position_slider)
        return group

    def _create_cylinder_group(self) -> QGroupBox:
        group = QGroupBox("Размеры цилиндра")
        v = QVBoxLayout(group)
        self.cylinder_length_slider = RangeSlider(
            minimum=0.3,
            maximum=0.8,
            value=float(self.parameters.get("cylinder_length", 0) or 0),
            step=0.001,
            decimals=3,
            units="м",
            title="Длина цилиндра",
        )
        v.addWidget(self.cylinder_length_slider)
        self.cyl_diam_m_slider = RangeSlider(
            minimum=0.030,
            maximum=0.150,
            value=float(self.parameters.get("cyl_diam_m", 0) or 0),
            step=0.001,
            decimals=3,
            units="м",
            title="Диаметр цилиндра",
        )
        v.addWidget(self.cyl_diam_m_slider)
        self.stroke_m_slider = RangeSlider(
            minimum=0.100,
            maximum=0.500,
            value=float(self.parameters.get("stroke_m", 0) or 0),
            step=0.001,
            decimals=3,
            units="м",
            title="Ход поршня",
        )
        v.addWidget(self.stroke_m_slider)
        self.dead_gap_m_slider = RangeSlider(
            minimum=0.000,
            maximum=0.020,
            value=float(self.parameters.get("dead_gap_m", 0) or 0),
            step=0.001,
            decimals=3,
            units="м",
            title="Мёртвый зазор",
        )
        v.addWidget(self.dead_gap_m_slider)
        self.rod_diameter_front_slider = RangeSlider(
            minimum=0.020,
            maximum=0.060,
            value=float(self.parameters.get("rod_diameter_m", 0) or 0),
            step=0.001,
            decimals=3,
            units="м",
            title="Диаметр штока (передняя ось)",
        )
        v.addWidget(self.rod_diameter_front_slider)
        self.rod_diameter_rear_slider = RangeSlider(
            minimum=0.020,
            maximum=0.060,
            value=float(self.parameters.get("rod_diameter_rear_m", 0) or 0),
            step=0.001,
            decimals=3,
            units="м",
            title="Диаметр штока (задняя ось)",
        )
        v.addWidget(self.rod_diameter_rear_slider)
        self.piston_rod_length_m_slider = RangeSlider(
            minimum=0.100,
            maximum=0.500,
            value=float(self.parameters.get("piston_rod_length_m", 0) or 0),
            step=0.001,
            decimals=3,
            units="м",
            title="Длина штока поршня",
        )
        v.addWidget(self.piston_rod_length_m_slider)
        self.piston_thickness_m_slider = RangeSlider(
            minimum=0.010,
            maximum=0.050,
            value=float(self.parameters.get("piston_thickness_m", 0) or 0),
            step=0.001,
            decimals=3,
            units="м",
            title="Толщина поршня",
        )
        v.addWidget(self.piston_thickness_m_slider)
        return group

    def _create_options_group(self) -> QGroupBox:
        group = QGroupBox("Опции")
        v = QVBoxLayout(group)
        self.interference_check = QCheckBox("Проверять пересечения геометрии")
        self.interference_check.setChecked(
            bool(self.parameters.get("interference_check", False))
        )
        v.addWidget(self.interference_check)
        self.link_rod_diameters = QCheckBox(
            "Связать диаметры штоков передних/задних колёс"
        )
        self.link_rod_diameters.setChecked(
            bool(self.parameters.get("link_rod_diameters", False))
        )
        v.addWidget(self.link_rod_diameters)
        return group

    def _connect_signals(self):
        self.wheelbase_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("wheelbase", v)
        )
        self.wheelbase_slider.valueChanged.connect(
            lambda v: self._on_parameter_live_change("wheelbase", v)
        )
        self.track_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("track", v)
        )
        self.track_slider.valueChanged.connect(
            lambda v: self._on_parameter_live_change("track", v)
        )
        self.frame_to_pivot_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("frame_to_pivot", v)
        )
        self.frame_to_pivot_slider.valueChanged.connect(
            lambda v: self._on_parameter_live_change("frame_to_pivot", v)
        )
        self.lever_length_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("lever_length", v)
        )
        self.lever_length_slider.valueChanged.connect(
            lambda v: self._on_parameter_live_change("lever_length", v)
        )
        self.rod_position_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("rod_position", v)
        )
        self.rod_position_slider.valueChanged.connect(
            lambda v: self._on_parameter_live_change("rod_position", v)
        )
        self.cylinder_length_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("cylinder_length", v)
        )
        self.cylinder_length_slider.valueChanged.connect(
            lambda v: self._on_parameter_live_change("cylinder_length", v)
        )
        self.cyl_diam_m_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("cyl_diam_m", v)
        )
        self.cyl_diam_m_slider.valueChanged.connect(
            lambda v: self._on_parameter_live_change("cyl_diam_m", v)
        )
        self.stroke_m_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("stroke_m", v)
        )
        self.stroke_m_slider.valueChanged.connect(
            lambda v: self._on_parameter_live_change("stroke_m", v)
        )
        self.dead_gap_m_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("dead_gap_m", v)
        )
        self.dead_gap_m_slider.valueChanged.connect(
            lambda v: self._on_parameter_live_change("dead_gap_m", v)
        )
        self.rod_diameter_front_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("rod_diameter_m", v)
        )
        self.rod_diameter_front_slider.valueChanged.connect(
            lambda v: self._on_parameter_live_change("rod_diameter_m", v)
        )
        self.rod_diameter_rear_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("rod_diameter_rear_m", v)
        )
        self.rod_diameter_rear_slider.valueChanged.connect(
            lambda v: self._on_parameter_live_change("rod_diameter_rear_m", v)
        )
        self.piston_rod_length_m_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("piston_rod_length_m", v)
        )
        self.piston_rod_length_m_slider.valueChanged.connect(
            lambda v: self._on_parameter_live_change("piston_rod_length_m", v)
        )
        self.piston_thickness_m_slider.valueEdited.connect(
            lambda v: self._on_parameter_changed("piston_thickness_m", v)
        )
        self.piston_thickness_m_slider.valueChanged.connect(
            lambda v: self._on_parameter_live_change("piston_thickness_m", v)
        )

        self.interference_check.toggled.connect(self._on_interference_check_toggled)
        self.link_rod_diameters.toggled.connect(self._on_link_rod_diameters_toggled)

    @Slot(bool)
    def _on_interference_check_toggled(self, checked: bool) -> None:
        """Изменение опции проверки пересечений геометрии"""
        if self._resolving_conflict:
            return
        self.parameters["interference_check"] = bool(checked)
        self.geometry_updated.emit(self.parameters.copy())
        self._show_interference_toggle_feedback(bool(checked))

    @Slot(bool)
    def _on_link_rod_diameters_toggled(self, checked: bool) -> None:
        """Изменение опции связывания диаметров штоков"""
        if self._resolving_conflict:
            return
        self.parameters["link_rod_diameters"] = bool(checked)

        if checked:
            front = float(self.parameters.get("rod_diameter_m", 0.035))
            rear = float(self.parameters.get("rod_diameter_rear_m", front))
            self._rod_link_snapshot = (front, rear)
            self.parameters["rod_diameter_rear_m"] = front
            self._syncing_rods = True
            try:
                self.rod_diameter_rear_slider.setValue(front)
            finally:
                self._syncing_rods = False
            self.rod_diameter_rear_slider.setEnabled(False)
        else:
            self.rod_diameter_rear_slider.setEnabled(True)
            if self._rod_link_snapshot:
                front, rear = self._rod_link_snapshot
                self._syncing_rods = True
                try:
                    self.rod_diameter_front_slider.setValue(front)
                    self.rod_diameter_rear_slider.setValue(rear)
                finally:
                    self._syncing_rods = False
                self.parameters["rod_diameter_m"] = front
                self.parameters["rod_diameter_rear_m"] = rear
            self._rod_link_snapshot = None

        self.geometry_updated.emit(self.parameters.copy())

    def _show_interference_toggle_feedback(self, enabled: bool) -> None:
        message = (
            "Проверка пересечений геометрии включена."
            if enabled
            else "Проверка пересечений геометрии отключена."
        )
        QMessageBox.information(self, "Проверка пересечений", message)
        if enabled:
            self._validate_geometry()

    @Slot(int)
    def _on_preset_changed(self, index: int):
        presets = {
            0: {
                "wheelbase": 3.2,
                "track": 1.6,
                "lever_length": 0.8,
                "cyl_diam_m": 0.080,
                "rod_diameter_m": 0.035,
            },
            1: {
                "wheelbase": 2.8,
                "track": 1.4,
                "lever_length": 0.7,
                "cyl_diam_m": 0.065,
                "rod_diameter_m": 0.028,
            },
            2: {
                "wheelbase": 3.8,
                "track": 1.9,
                "lever_length": 0.95,
                "cyl_diam_m": 0.100,
                "rod_diameter_m": 0.045,
            },
            3: {},
        }
        if index in (0, 1, 2):
            params = presets[index]
            self.set_parameters(params)
            self.geometry_updated.emit(self.parameters.copy())

    def set_parameters(self, params: dict) -> None:
        self._resolving_conflict = True
        try:
            self.parameters.update(params)
            for k, v in params.items():
                self._set_parameter_value(k, v)
        finally:
            self._resolving_conflict = False

    @Slot()
    def _reset_to_defaults(self):
        try:
            self._settings_manager.reset_to_defaults(category="geometry")
            self.parameters = self._settings_manager.get_category("geometry") or {}
            # Применяем к виджетам
            for k, v in self.parameters.items():
                self._set_parameter_value(k, v)
            self.geometry_updated.emit(self.parameters.copy())
        except Exception as e:
            self.logger.error(f"Reset to geometry defaults failed: {e}")

    @Slot()
    def _save_current_as_defaults(self):
        try:
            current = self.collect_state()
            self._settings_manager.set_category("geometry", current, auto_save=False)
            self._settings_manager.save_current_as_defaults(category="geometry")
        except Exception as e:
            self.logger.error(f"Save geometry as defaults failed: {e}")

    def collect_state(self) -> dict:
        return self.parameters.copy()

    @Slot(str, float)
    def _on_parameter_live_change(self, param_name: str, value: float):
        if self._resolving_conflict:
            return
        if param_name in ("rod_diameter_m", "rod_diameter_rear_m"):
            self._handle_rod_diameter_update(param_name, value, live=True)
            return
        self.parameters[param_name] = value
        geometry_3d = self._get_fast_geometry_update(param_name, value)
        self.geometry_changed.emit(geometry_3d)

    @Slot(str, float)
    def _on_parameter_changed(self, param_name: str, value: float):
        if self._resolving_conflict:
            return
        if param_name in ("rod_diameter_m", "rod_diameter_rear_m"):
            self._handle_rod_diameter_update(param_name, value, live=False)
            return
        self.parameters[param_name] = value
        self.parameter_changed.emit(param_name, value)
        self.geometry_updated.emit(self.parameters.copy())
        if param_name in [
            "wheelbase",
            "track",
            "lever_length",
            "cylinder_length",
            "frame_to_pivot",
            "rod_position",
            "cyl_diam_m",
            "stroke_m",
            "dead_gap_m",
            "rod_diameter_m",
            "piston_rod_length_m",
            "piston_thickness_m",
        ]:
            self.geometry_changed.emit(
                self._get_fast_geometry_update(param_name, value)
            )

    def _handle_rod_diameter_update(
        self, param_name: str, value: float, *, live: bool
    ) -> None:
        self.parameters[param_name] = value
        if self.link_rod_diameters.isChecked() and not self._syncing_rods:
            counterpart = (
                "rod_diameter_rear_m"
                if param_name == "rod_diameter_m"
                else "rod_diameter_m"
            )
            target_slider = (
                self.rod_diameter_rear_slider
                if counterpart == "rod_diameter_rear_m"
                else self.rod_diameter_front_slider
            )
            self.parameters[counterpart] = value
            self._syncing_rods = True
            try:
                target_slider.setValue(value)
            finally:
                self._syncing_rods = False

        if live:
            geometry_3d = self._get_fast_geometry_update(param_name, value)
            self.geometry_changed.emit(geometry_3d)
        else:
            self.parameter_changed.emit(param_name, value)
            self.geometry_updated.emit(self.parameters.copy())
            self.geometry_changed.emit(
                self._get_fast_geometry_update(param_name, value)
            )

    def _get_fast_geometry_update(self, param_name: str, value: float) -> dict:
        """Подготовить пакет обновления геометрии для QML.

        Все значения передаются в метрах. Ранее часть параметров пересчитывалась
        в миллиметры, что приводило к неверной интерпретации в QML для малых
        величин (например, зазоры порядка миллиметров). Теперь используем
        единый формат в метрах, соответствующий текущим настройкам.
        """

        geom_cfg = self._settings_manager.get_category("geometry") or {}
        rod_diameter_front = float(self.parameters.get("rod_diameter_m", 0) or 0.0)
        rod_diameter_rear = float(
            self.parameters.get("rod_diameter_rear_m", rod_diameter_front) or 0.0
        )

        payload: dict[str, float] = {
            "frameLength": float(self.parameters.get("wheelbase", 0) or 0.0),
            "leverLength": float(self.parameters.get("lever_length", 0) or 0.0),
            "cylinderBodyLength": float(
                self.parameters.get("cylinder_length", 0) or 0.0
            ),
            "trackWidth": float(self.parameters.get("track", 0) or 0.0),
            "frameToPivot": float(self.parameters.get("frame_to_pivot", 0) or 0.0),
            "rodPosition": float(self.parameters.get("rod_position", 0) or 0.0),
            "boreHead": float(self.parameters.get("cyl_diam_m", 0) or 0.0),
            "rodDiameter": rod_diameter_front,
            "rodDiameterRear": rod_diameter_rear,
            "pistonRodLength": float(
                self.parameters.get("piston_rod_length_m", 0) or 0.0
            ),
            "pistonThickness": float(
                self.parameters.get("piston_thickness_m", 0) or 0.0
            ),
        }

        def _cfg_value(key: str) -> Optional[float]:
            raw = geom_cfg.get(key)
            if isinstance(raw, (int, float)):
                return float(raw)
            return None

        if (frame_height := _cfg_value("frame_height_m")) is not None:
            payload["frameHeight"] = frame_height
        if (frame_beam := _cfg_value("frame_beam_size_m")) is not None:
            payload["frameBeamSize"] = frame_beam
        if (tail_rod := _cfg_value("tail_rod_length_m")) is not None:
            payload["tailRodLength"] = tail_rod

        payload["rodDiameterM"] = rod_diameter_front
        payload["rodDiameterFrontM"] = rod_diameter_front
        payload["rodDiameterRearM"] = rod_diameter_rear
        payload["rod_diameter_front_mm"] = rod_diameter_front * 1000.0
        payload["rod_diameter_rear_mm"] = rod_diameter_rear * 1000.0
        payload["rod_diameter_mm"] = rod_diameter_front * 1000.0

        return payload

    def _set_parameter_value(self, param_name: str, value: float) -> None:
        mapping = {
            "wheelbase": self.wheelbase_slider,
            "track": self.track_slider,
            "frame_to_pivot": self.frame_to_pivot_slider,
            "lever_length": self.lever_length_slider,
            "rod_position": self.rod_position_slider,
            "cylinder_length": self.cylinder_length_slider,
            "cyl_diam_m": self.cyl_diam_m_slider,
            "stroke_m": self.stroke_m_slider,
            "dead_gap_m": self.dead_gap_m_slider,
            "rod_diameter_m": self.rod_diameter_front_slider,
            "rod_diameter_rear_m": self.rod_diameter_rear_slider,
            "piston_rod_length_m": self.piston_rod_length_m_slider,
            "piston_thickness_m": self.piston_thickness_m_slider,
        }
        slider = mapping.get(param_name)
        if slider is None:
            self.parameters[param_name] = value
            return
        try:
            slider.setValue(float(value))
            self.parameters[param_name] = float(value)
        except Exception as e:
            self.logger.warning(f"Не удалось установить {param_name}={value}: {e}")

    def _validate_geometry(self):
        errors = []
        warnings = []

        wheelbase = float(self.parameters.get("wheelbase", 0) or 0)
        lever_length = float(self.parameters.get("lever_length", 0) or 0)
        frame_to_pivot = float(self.parameters.get("frame_to_pivot", 0) or 0)

        max_lever_reach = wheelbase / 2.0 - 0.1
        if frame_to_pivot + lever_length > max_lever_reach:
            errors.append(
                f"Геометрия рычага превышает доступное пространство: {frame_to_pivot + lever_length:.2f} > {max_lever_reach:.2f}м"
            )

        rod_diameter_front = float(self.parameters.get("rod_diameter_m", 0) or 0)
        rod_diameter_rear = float(
            self.parameters.get("rod_diameter_rear_m", rod_diameter_front) or 0
        )
        cyl_diam_m = float(self.parameters.get("cyl_diam_m", 0) or 0)
        if cyl_diam_m > 0:
            thresholds = {
                "переднего": rod_diameter_front,
                "заднего": rod_diameter_rear,
            }
            for label, rod_value in thresholds.items():
                if rod_value >= cyl_diam_m * 0.8:
                    errors.append(
                        f"Диаметр {label} штока слишком велик: {rod_value * 1000:.1f}мм >= 80% от {cyl_diam_m * 1000:.1f}мм цилиндра"
                    )
                elif rod_value >= cyl_diam_m * 0.7:
                    warnings.append(
                        f"Диаметр {label} штока близок к пределу: {rod_value * 1000:.1f}мм vs {cyl_diam_m * 1000:.1f}мм цилиндра"
                    )

        if errors:
            QMessageBox.critical(
                self, "Ошибки геометрии", "Обнаружены ошибки:\n" + "\n".join(errors)
            )
        elif warnings:
            QMessageBox.warning(
                self,
                "Предупреждения геометрии",
                "Предупреждения:\n" + "\n".join(warnings),
            )
        else:
            QMessageBox.information(
                self, "Проверка геометрии", "Все параметры геометрии корректны."
            )
