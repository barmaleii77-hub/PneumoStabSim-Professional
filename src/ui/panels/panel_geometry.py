"""
Geometry configuration panel - РУССКИЙ ИНТЕРФЕЙС
Полная интеграция с SettingsManager без дефолтов в коде.
Чтение при запуске, запись при выходе (централизованно в MainWindow).
"""

from __future__ import annotations

from dataclasses import dataclass
from collections.abc import Mapping
import logging
from typing import Any

try:  # pragma: no cover - optional structured logging
    import structlog
except ImportError:  # pragma: no cover - fallback when structlog is unavailable
    structlog = None  # type: ignore[assignment]

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
from PySide6.QtCore import QObject, QMetaMethod, Signal, Slot, Qt
from PySide6.QtGui import QFont

from ..widgets import RangeSlider
from config.constants import get_geometry_presets, get_geometry_ui_ranges
from src.common.settings_manager import get_settings_manager
from src.ui.geometry_schema import (
    GeometrySettings,
    GeometryValidationError,
    validate_geometry_settings,
)
from src.ui.panels.geometry.defaults import DEFAULT_GEOMETRY


@dataclass(frozen=True)
class _RangeSpec:
    minimum: float
    maximum: float
    step: float
    decimals: int
    units: str


@dataclass(frozen=True)
class GeometryPreset:
    key: str
    label: str
    values: dict[str, float]


try:
    _VALIDATED_FIELD_NAMES = frozenset(
        validate_geometry_settings(DEFAULT_GEOMETRY).to_config_dict().keys()
    )
except GeometryValidationError:  # pragma: no cover - defensive guardrail
    _VALIDATED_FIELD_NAMES = frozenset(DEFAULT_GEOMETRY.keys())


def _build_geometry_settings(snapshot: Mapping[str, Any], logger) -> GeometrySettings:
    """Validate the snapshot collected from the legacy widgets."""

    try:
        return validate_geometry_settings(snapshot)
    except GeometryValidationError as exc:
        logger.warning("Geometry settings validation failed, using fallback: %s", exc)
        fallback_payload = {
            key: snapshot.get(key, DEFAULT_GEOMETRY.get(key))
            for key in _VALIDATED_FIELD_NAMES
        }
        return GeometrySettings(fallback_payload)


def _log_no_subscribers(
    logger, description: str, *, panel: str, signal_name: str | None
) -> None:
    """Emit a structured log when a signal has no receivers."""

    event = "ui.signal.no_receivers"
    if structlog is not None:
        structlog.get_logger("ui.signal").info(
            event,
            panel=panel,
            signal=signal_name,
            description=description,
        )
        return

    logger.info("%s skipped: no subscribers", description)


def _resolve_signal_name(
    meta_method: QMetaMethod | None, signal_obj: Any
) -> str | None:
    if meta_method is not None and meta_method.isValid():
        try:
            return meta_method.name()
        except Exception:  # pragma: no cover - Qt internals
            return None

    return getattr(signal_obj, "__name__", signal_obj.__class__.__name__)


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
        self._ui_ranges: dict[str, _RangeSpec] = {}
        self._preset_map: dict[str, GeometryPreset] = {}
        self._active_preset: str = "custom"
        self._block_preset_signal = False
        self._applying_preset = False
        self._geometry_changed_meta: QMetaMethod | None = None

        from src.common import get_category_logger

        self.logger = get_category_logger("GeometryPanel")

        # 1) Загружаем состояние из JSON СНАЧАЛА
        self._load_from_settings()
        self._load_ui_ranges()
        self._load_presets()

        # 2) Строим UI на основе загруженных значений (никаких дефолтов в коде)
        self._setup_ui()

        # 3) Подключаем сигналы
        self._connect_signals()

        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        # 4) Отправляем начальные параметры
        from PySide6.QtCore import QTimer

        QTimer.singleShot(300, self._emit_initial)

    def _emit_initial(self):
        meta_method = self._get_geometry_meta_method()
        geometry_connected = self._verify_geometry_subscribers(meta_method)

        payload = self._get_fast_geometry_update("init", 0.0)
        if geometry_connected is not False:
            self._emit_if_connected(
                self.geometry_changed,
                payload,
                "GeometryPanel: initial geometry_changed",
                meta_method,
            )

        updated_meta = self._get_meta_method(getattr(self, "geometry_updated", None))
        if self._is_signal_connected(self.geometry_updated, updated_meta) is not False:
            self._emit_if_connected(
                self.geometry_updated,
                self.parameters.copy(),
                "GeometryPanel: initial geometry_updated",
                updated_meta,
            )

    def _get_meta_method(self, signal_obj: Any) -> QMetaMethod | None:
        try:
            meta_method = QMetaMethod.fromSignal(signal_obj)
        except (TypeError, AttributeError):  # pragma: no cover - Qt internals
            meta_method = None

        if meta_method is not None and meta_method.isValid():
            return meta_method

        # PySide6 exposes ``SignalInstance.signal`` for string-based signatures;
        # use it to resolve a meta method without touching private attributes
        # like ``SignalInstance.receivers`` that are not available on all
        # versions.
        signature = getattr(signal_obj, "signal", None)
        if signature:
            meta_object = self.metaObject()
            try:
                index = meta_object.indexOfSignal(signature)
            except TypeError:
                try:
                    index = meta_object.indexOfSignal(bytes(signature))
                except Exception:  # pragma: no cover - defensive fallback
                    index = -1
            if index >= 0:
                candidate = meta_object.method(index)
                if candidate.isValid():
                    return candidate

        return None

    def _get_geometry_meta_method(self) -> QMetaMethod | None:
        if self._geometry_changed_meta is None:
            self._geometry_changed_meta = self._get_meta_method(self.geometry_changed)
        return self._geometry_changed_meta

    def _is_signal_connected(
        self, signal_obj: QObject | Any, meta_method: QMetaMethod | None = None
    ) -> bool | None:
        """Attempt to detect whether QML subscribers are attached.

        Qt 6 APIs differ across releases: ``QObject.isSignalConnected`` was
        introduced in Qt 6.5 while some bindings expose ``SignalInstance``
        helpers instead.  This helper feature-detects supported variants and
        swallows any Qt-specific errors so initial emissions never crash.

        Returns:
            ``True`` when a supported API reports at least one receiver,
            ``False`` when the signal has no receivers, ``None`` when
            detection is unsupported.
        """

        emit_fn = getattr(signal_obj, "emit", None)
        if not callable(emit_fn) and not callable(signal_obj):
            return None

        if meta_method is None:
            meta_method = self._get_meta_method(signal_obj)

        if meta_method is None or not meta_method.isValid():
            return None

        try:
            signal_connected = getattr(signal_obj, "isSignalConnected", None)
            if callable(signal_connected):
                try:
                    return bool(signal_connected())
                except TypeError:
                    if meta_method is not None:
                        try:
                            return bool(signal_connected(meta_method))
                        except TypeError:
                            self.logger.debug(
                                "GeometryPanel: isSignalConnected signature mismatch",
                                exc_info=True,
                            )

            is_connected = getattr(self, "isSignalConnected", None)
            if callable(is_connected) and meta_method is not None:
                try:
                    return bool(is_connected(meta_method))
                except TypeError:
                    self.logger.debug(
                        "GeometryPanel: QWidget.isSignalConnected signature mismatch",
                        exc_info=True,
                    )

            if meta_method is not None and hasattr(self, "isSignalConnected"):
                try:
                    return bool(self.isSignalConnected(meta_method))
                except Exception:  # pragma: no cover - Qt internals are fickle
                    self.logger.debug(
                        "GeometryPanel: QWidget.isSignalConnected probe failed",
                        exc_info=True,
                    )
        except Exception:  # pragma: no cover - defensive Qt fallback
            self.logger.debug(
                "GeometryPanel: subscriber verification failed; proceeding without check",
                exc_info=True,
            )

        return None

    def _verify_geometry_subscribers(
        self, meta_method: QMetaMethod | None = None
    ) -> bool | None:
        signal_obj = getattr(self, "geometry_changed", None)
        if signal_obj is None:
            return None

        return self._is_signal_connected(signal_obj, meta_method)

    def _emit_if_connected(
        self,
        signal_obj: Any,
        payload: Any,
        description: str,
        meta_method: QMetaMethod | None = None,
    ) -> None:
        if signal_obj is None:
            self.logger.warning("%s skipped: signal is not available", description)
            return

        try:
            connected = self._is_signal_connected(signal_obj, meta_method)
        except Exception:  # pragma: no cover - defensive Qt fallback
            self.logger.debug(
                "geometry_emit_connection_probe_failed",
                extra={"description": description},
                exc_info=True,
            )
            connected = None

        if connected is False:
            signature = None
            if meta_method is not None:
                try:
                    raw_signature = meta_method.methodSignature()
                    signature = (
                        raw_signature.decode(errors="ignore")
                        if isinstance(raw_signature, (bytes, bytearray))
                        else str(raw_signature)
                    )
                except Exception:  # pragma: no cover - defensive Qt fallback
                    self.logger.debug(
                        "geometry_emit_signature_resolution_failed",
                        description=description,
                        exc_info=True,
                    )

            self._log_geometry_emit_skipped(description, signature)
            return

        try:
            signal_obj.emit(payload)
        except RuntimeError as exc:
            self.logger.warning("%s failed: %s", description, exc)

    def _logger_has_live_handlers(self) -> bool:
        logger = getattr(self, "logger", None)
        if not isinstance(logger, logging.Logger):
            return False

        visited: set[int] = set()
        current: logging.Logger | None = logger
        found_handler = False
        while isinstance(current, logging.Logger) and id(current) not in visited:
            visited.add(id(current))
            for handler in current.handlers:
                found_handler = True
                stream = getattr(handler, "stream", None)
                if stream is not None and getattr(stream, "closed", False):
                    return False
            if not current.propagate:
                break
            parent = getattr(current, "parent", None)
            current = parent if isinstance(parent, logging.Logger) else None

        return found_handler

    def _log_geometry_emit_skipped(
        self, description: str, signature: str | None
    ) -> None:
        if not self._logger_has_live_handlers():
            return

        try:
            self.logger.info(
                "geometry_emit_skipped",
                extra={
                    "description": description,
                    "reason": "no_subscribers",
                    "signal_signature": signature,
                },
            )
        except ValueError:
            # Logging streams can be closed during pytest teardown; avoid
            # surfacing spurious errors when emitting diagnostic messages.
            return

    # Чтение только из JSON
    def _load_from_settings(self) -> None:
        data = self._settings_manager.get_category("geometry") or {}
        self._apply_settings_payload(data)
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
        for preset in self._preset_map.values():
            self.preset_combo.addItem(preset.label, preset.key)
        self.preset_combo.addItem("Пользовательский", "custom")
        self.preset_combo.currentIndexChanged.connect(self._on_preset_changed)
        preset_row.addWidget(self.preset_combo, 1)
        layout.addLayout(preset_row)
        self._select_preset(self._active_preset)

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
        wheelbase_spec = self._get_range("wheelbase", 2.0, 4.0, 0.001, 3, "м")
        self.wheelbase_slider = RangeSlider(
            minimum=wheelbase_spec.minimum,
            maximum=wheelbase_spec.maximum,
            value=self._clamp_value("wheelbase", wheelbase_spec),
            step=wheelbase_spec.step,
            decimals=wheelbase_spec.decimals,
            units=wheelbase_spec.units,
            title="База (колёсная)",
        )
        self.wheelbase_slider.setToolTip(
            "Длина рамы по оси Z. Определяет положение передних/задних рогов."
        )
        v.addWidget(self.wheelbase_slider)
        track_spec = self._get_range("track", 1.0, 2.5, 0.001, 3, "м")
        self.track_slider = RangeSlider(
            minimum=track_spec.minimum,
            maximum=track_spec.maximum,
            value=self._clamp_value("track", track_spec),
            step=track_spec.step,
            decimals=track_spec.decimals,
            units=track_spec.units,
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
        frame_to_pivot_spec = self._get_range("frame_to_pivot", 0.3, 1.0, 0.001, 3, "м")
        self.frame_to_pivot_slider = RangeSlider(
            minimum=frame_to_pivot_spec.minimum,
            maximum=frame_to_pivot_spec.maximum,
            value=self._clamp_value("frame_to_pivot", frame_to_pivot_spec),
            step=frame_to_pivot_spec.step,
            decimals=frame_to_pivot_spec.decimals,
            units=frame_to_pivot_spec.units,
            title="Рама → ось рычага",
        )
        self.frame_to_pivot_slider.setToolTip(
            "Абсолютное поперечное расстояние от центра рамы до оси рычага. НЕ зависит от ‘Колея’."
        )
        v.addWidget(self.frame_to_pivot_slider)
        lever_length_spec = self._get_range("lever_length", 0.5, 1.5, 0.001, 3, "м")
        self.lever_length_slider = RangeSlider(
            minimum=lever_length_spec.minimum,
            maximum=lever_length_spec.maximum,
            value=self._clamp_value("lever_length", lever_length_spec),
            step=lever_length_spec.step,
            decimals=lever_length_spec.decimals,
            units=lever_length_spec.units,
            title="Длина рычага",
        )
        v.addWidget(self.lever_length_slider)
        rod_position_spec = self._get_range("rod_position", 0.3, 0.9, 0.001, 3, "")
        self.rod_position_slider = RangeSlider(
            minimum=rod_position_spec.minimum,
            maximum=rod_position_spec.maximum,
            value=self._clamp_value("rod_position", rod_position_spec),
            step=rod_position_spec.step,
            decimals=rod_position_spec.decimals,
            units=rod_position_spec.units,
            title="Положение крепления штока (доля)",
        )
        v.addWidget(self.rod_position_slider)
        return group

    def _create_cylinder_group(self) -> QGroupBox:
        group = QGroupBox("Размеры цилиндра")
        v = QVBoxLayout(group)
        cylinder_length_spec = self._get_range(
            "cylinder_length", 0.3, 0.8, 0.001, 3, "м"
        )
        self.cylinder_length_slider = RangeSlider(
            minimum=cylinder_length_spec.minimum,
            maximum=cylinder_length_spec.maximum,
            value=self._clamp_value("cylinder_length", cylinder_length_spec),
            step=cylinder_length_spec.step,
            decimals=cylinder_length_spec.decimals,
            units=cylinder_length_spec.units,
            title="Длина цилиндра",
        )
        v.addWidget(self.cylinder_length_slider)
        cyl_diam_spec = self._get_range("cyl_diam_m", 0.03, 0.15, 0.001, 3, "м")
        self.cyl_diam_m_slider = RangeSlider(
            minimum=cyl_diam_spec.minimum,
            maximum=cyl_diam_spec.maximum,
            value=self._clamp_value("cyl_diam_m", cyl_diam_spec),
            step=cyl_diam_spec.step,
            decimals=cyl_diam_spec.decimals,
            units=cyl_diam_spec.units,
            title="Диаметр цилиндра",
        )
        v.addWidget(self.cyl_diam_m_slider)
        stroke_spec = self._get_range("stroke_m", 0.1, 0.5, 0.001, 3, "м")
        self.stroke_m_slider = RangeSlider(
            minimum=stroke_spec.minimum,
            maximum=stroke_spec.maximum,
            value=self._clamp_value("stroke_m", stroke_spec),
            step=stroke_spec.step,
            decimals=stroke_spec.decimals,
            units=stroke_spec.units,
            title="Ход поршня",
        )
        v.addWidget(self.stroke_m_slider)
        dead_gap_spec = self._get_range("dead_gap_m", 0.0, 0.02, 0.001, 3, "м")
        self.dead_gap_m_slider = RangeSlider(
            minimum=dead_gap_spec.minimum,
            maximum=dead_gap_spec.maximum,
            value=self._clamp_value("dead_gap_m", dead_gap_spec),
            step=dead_gap_spec.step,
            decimals=dead_gap_spec.decimals,
            units=dead_gap_spec.units,
            title="Мёртвый зазор",
        )
        v.addWidget(self.dead_gap_m_slider)
        rod_front_spec = self._get_range("rod_diameter_m", 0.02, 0.06, 0.001, 3, "м")
        self.rod_diameter_front_slider = RangeSlider(
            minimum=rod_front_spec.minimum,
            maximum=rod_front_spec.maximum,
            value=self._clamp_value("rod_diameter_m", rod_front_spec),
            step=rod_front_spec.step,
            decimals=rod_front_spec.decimals,
            units=rod_front_spec.units,
            title="Диаметр штока (передняя ось)",
        )
        v.addWidget(self.rod_diameter_front_slider)
        rod_rear_spec = self._get_range(
            "rod_diameter_rear_m", 0.02, 0.06, 0.001, 3, "м"
        )
        self.rod_diameter_rear_slider = RangeSlider(
            minimum=rod_rear_spec.minimum,
            maximum=rod_rear_spec.maximum,
            value=self._clamp_value("rod_diameter_rear_m", rod_rear_spec),
            step=rod_rear_spec.step,
            decimals=rod_rear_spec.decimals,
            units=rod_rear_spec.units,
            title="Диаметр штока (задняя ось)",
        )
        v.addWidget(self.rod_diameter_rear_slider)
        piston_rod_spec = self._get_range(
            "piston_rod_length_m", 0.1, 0.5, 0.001, 3, "м"
        )
        self.piston_rod_length_m_slider = RangeSlider(
            minimum=piston_rod_spec.minimum,
            maximum=piston_rod_spec.maximum,
            value=self._clamp_value("piston_rod_length_m", piston_rod_spec),
            step=piston_rod_spec.step,
            decimals=piston_rod_spec.decimals,
            units=piston_rod_spec.units,
            title="Длина штока поршня",
        )
        v.addWidget(self.piston_rod_length_m_slider)
        piston_thickness_spec = self._get_range(
            "piston_thickness_m", 0.01, 0.05, 0.001, 3, "м"
        )
        self.piston_thickness_m_slider = RangeSlider(
            minimum=piston_thickness_spec.minimum,
            maximum=piston_thickness_spec.maximum,
            value=self._clamp_value("piston_thickness_m", piston_thickness_spec),
            step=piston_thickness_spec.step,
            decimals=piston_thickness_spec.decimals,
            units=piston_thickness_spec.units,
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

        # Метапараметры (шаг/точность/единицы) для каждого слайдера
        meta_map = {
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
        for key, slider in meta_map.items():
            slider.stepChanged.connect(
                lambda v, k=key: self._on_slider_step_changed(k, v)
            )
            slider.decimalsChanged.connect(
                lambda v, k=key: self._on_slider_decimals_changed(k, v)
            )
            slider.unitsChanged.connect(
                lambda v, k=key: self._on_slider_units_changed(k, v)
            )

    @Slot(bool)
    def _on_interference_check_toggled(self, checked: bool) -> None:
        """Изменение опции проверки пересечений геометрии"""
        if self._resolving_conflict:
            return
        self.parameters["interference_check"] = bool(checked)
        self._persist_parameter(
            "interference_check", self.parameters["interference_check"]
        )
        self._emit_if_connected(
            self.geometry_updated,
            self.parameters.copy(),
            "GeometryPanel: interference_check toggled",
        )
        self._mark_custom_on_user_change()
        self._show_interference_toggle_feedback(bool(checked))

    @Slot(bool)
    def _on_link_rod_diameters_toggled(self, checked: bool) -> None:
        """Изменение опции связывания диаметров штоков"""
        if self._resolving_conflict:
            return
        self.parameters["link_rod_diameters"] = bool(checked)
        self._persist_parameter(
            "link_rod_diameters", self.parameters["link_rod_diameters"]
        )
        if checked:
            front = float(self.parameters.get("rod_diameter_m", 0.035))
            rear = float(self.parameters.get("rod_diameter_rear_m", front))
            self._rod_link_snapshot = (front, rear)
            self.parameters["rod_diameter_m"] = front
            self.parameters["rod_diameter_rear_m"] = front
            self._syncing_rods = True
            try:
                self.rod_diameter_rear_slider.setValue(front)
            finally:
                self._syncing_rods = False
            self.rod_diameter_rear_slider.setEnabled(False)
            self._persist_parameter("rod_diameter_m", front)
            self._persist_parameter("rod_diameter_rear_m", front)
        else:
            self.rod_diameter_rear_slider.setEnabled(True)
            # Preserve the current synced values; users can now adjust sliders independently.
            self._rod_link_snapshot = None

        self._emit_if_connected(
            self.geometry_updated,
            self.parameters.copy(),
            "GeometryPanel: link_rod_diameters toggled",
        )
        self._mark_custom_on_user_change()

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
        if self._block_preset_signal:
            return
        key = self.preset_combo.itemData(index)
        if not isinstance(key, str):
            return
        if key == "custom":
            self._update_active_preset("custom", update_combo=False)
            return
        preset = self._preset_map.get(key)
        if preset is None:
            self.logger.warning("Неизвестный ключ пресета геометрии: %s", key)
            self._update_active_preset("custom", update_combo=True)
            return
        self._applying_preset = True
        try:
            self.set_parameters(preset.values, from_preset=True)
            self._update_active_preset(key, update_combo=False)
        finally:
            self._applying_preset = False
        self._emit_if_connected(
            self.geometry_updated,
            self.parameters.copy(),
            "GeometryPanel: preset applied",
        )

    def set_parameters(
        self, params: Mapping[str, float], *, from_preset: bool = False
    ) -> None:
        self._resolving_conflict = True
        previous_applying_state = self._applying_preset
        self._applying_preset = self._applying_preset or from_preset
        try:
            for k, v in params.items():
                numeric = float(v)
                self.parameters[k] = numeric
                self._set_parameter_value(k, numeric)
                self._persist_parameter(k, numeric)
        finally:
            self._resolving_conflict = False
            self._applying_preset = previous_applying_state

    @Slot()
    def _reset_to_defaults(self):
        try:
            self._settings_manager.reset_to_defaults(category="geometry")
            self._settings_manager.save()
            payload = self._settings_manager.get_category("geometry") or {}
            self._apply_settings_payload(payload)
            # Применяем к виджетам
            for k, v in self.parameters.items():
                self._set_parameter_value(k, v)
            self._select_preset(self._active_preset)
            self._emit_if_connected(
                self.geometry_updated,
                self.parameters.copy(),
                "GeometryPanel: reset to defaults",
            )
        except Exception as e:
            self.logger.error(f"Reset to geometry defaults failed: {e}")

    @Slot()
    def _save_current_as_defaults(self):
        try:
            current = self.collect_state()
            self._settings_manager.set_category("geometry", current, auto_save=False)
            self._settings_manager.save_current_as_defaults(category="geometry")
            self._settings_manager.save()
        except Exception as e:
            self.logger.error(f"Save geometry as defaults failed: {e}")

    def _collect_ui_snapshot(self) -> dict[str, Any]:
        snapshot: dict[str, Any] = dict(self.parameters)
        slider_map = {
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
        for key, slider in slider_map.items():
            snapshot[key] = float(slider.value_spinbox.value())
        # Добавляем раздел meta из настроек, если он присутствует
        try:
            meta_payload = self._settings_manager.get("current.geometry.meta")
            if isinstance(meta_payload, dict):
                snapshot["meta"] = meta_payload
        except Exception:
            pass
        snapshot["interference_check"] = bool(self.interference_check.isChecked())
        snapshot["link_rod_diameters"] = bool(self.link_rod_diameters.isChecked())
        snapshot["active_preset"] = self._active_preset
        return snapshot

    def collect_state(self) -> dict:
        return self._collect_ui_snapshot()

    def get_geometry_settings(self) -> GeometrySettings:
        """Return the validated geometry snapshot for legacy panels."""

        snapshot = self._collect_ui_snapshot()
        return _build_geometry_settings(snapshot, self.logger)

    def get_parameters(self) -> dict[str, Any]:
        """Return the current geometry configuration as reflected by the UI."""

        snapshot = self._collect_ui_snapshot()
        settings = self.get_geometry_settings().to_config_dict()
        merged = dict(snapshot)
        merged.update(settings)
        return merged

    @Slot(str, float)
    def _on_parameter_live_change(self, param_name: str, value: float):
        if self._resolving_conflict:
            return
        if param_name in ("rod_diameter_m", "rod_diameter_rear_m"):
            self._handle_rod_diameter_update(param_name, value, live=True)
            return
        self.parameters[param_name] = value
        geometry_3d = self._get_fast_geometry_update(param_name, value)
        self._emit_if_connected(
            self.geometry_changed,
            geometry_3d,
            f"GeometryPanel: live change {param_name}",
            self._get_geometry_meta_method(),
        )

    @Slot(str, float)
    def _on_parameter_changed(self, param_name: str, value: float):
        if self._resolving_conflict:
            return
        if param_name in ("rod_diameter_m", "rod_diameter_rear_m"):
            self._handle_rod_diameter_update(param_name, value, live=False)
            return
        self.parameters[param_name] = value
        self._persist_parameter(param_name, value)
        self.parameter_changed.emit(param_name, value)
        self._emit_if_connected(
            self.geometry_updated,
            self.parameters.copy(),
            f"GeometryPanel: parameter {param_name} changed",
        )
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
            "rod_diameter_rear_m",
            "piston_rod_length_m",
            "piston_thickness_m",
        ]:
            self._emit_if_connected(
                self.geometry_changed,
                self._get_fast_geometry_update(param_name, value),
                f"GeometryPanel: geometry change {param_name}",
                self._get_geometry_meta_method(),
            )
        self._mark_custom_on_user_change()

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
            self._persist_parameter(counterpart, value)

        if live:
            geometry_3d = self._get_fast_geometry_update(param_name, value)
            self._emit_if_connected(
                self.geometry_changed,
                geometry_3d,
                f"GeometryPanel: rod diameter live change {param_name}",
                self._get_geometry_meta_method(),
            )
        else:
            self._persist_parameter(param_name, value)
            self.parameter_changed.emit(param_name, value)
            self._emit_if_connected(
                self.geometry_updated,
                self.parameters.copy(),
                f"GeometryPanel: rod diameter change {param_name}",
            )
            self._emit_if_connected(
                self.geometry_changed,
                self._get_fast_geometry_update(param_name, value),
                f"GeometryPanel: rod diameter geometry change {param_name}",
                self._get_geometry_meta_method(),
            )
            self._mark_custom_on_user_change()

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

        def _cfg_value(key: str) -> float | None:
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

    def _apply_settings_payload(self, payload: Mapping[str, object]) -> None:
        self.parameters.clear()
        active = payload.get("active_preset") if isinstance(payload, Mapping) else None
        if isinstance(active, str) and active.strip():
            self._active_preset = active.strip()
        else:
            self._active_preset = "custom"
        for key, value in payload.items():
            if key == "active_preset":
                continue
            self.parameters[key] = value  # type: ignore[assignment]

    def _load_ui_ranges(self) -> None:
        specs: dict[str, _RangeSpec] = {}
        try:
            raw_ranges = get_geometry_ui_ranges()
        except Exception as exc:
            self.logger.warning(
                "Не удалось загрузить диапазоны геометрии из настроек: %s", exc
            )
            self._ui_ranges = {}
            return
        if not isinstance(raw_ranges, Mapping):
            self.logger.warning(
                "Диапазоны геометрии имеют некорректный тип: %s",
                type(raw_ranges).__name__,
            )
            self._ui_ranges = {}
            return
        for key, entry in raw_ranges.items():
            if not isinstance(entry, Mapping):
                self.logger.warning(
                    "Диапазон параметра '%s' должен быть объектом, получено %s",
                    key,
                    type(entry).__name__,
                )
                continue
            try:
                minimum = float(entry["min"])
                maximum = float(entry["max"])
            except (KeyError, TypeError, ValueError) as exc:
                self.logger.warning(
                    "Диапазон параметра '%s' некорректен (min/max): %s", key, exc
                )
                continue
            if minimum >= maximum:
                self.logger.warning(
                    "Диапазон параметра '%s' имеет min >= max (%.3f >= %.3f)",
                    key,
                    minimum,
                    maximum,
                )
                continue
            try:
                step = float(entry.get("step", 0.001))
            except (TypeError, ValueError):
                step = 0.001
            if step <= 0:
                self.logger.warning(
                    "Шаг для параметра '%s' <= 0 (%.4f), используем 0.001",
                    key,
                    step,
                )
                step = 0.001
            try:
                decimals = int(entry.get("decimals", 3))
            except (TypeError, ValueError):
                decimals = 3
            units_value = entry.get("units")
            units = str(units_value) if units_value is not None else ""
            specs[key] = _RangeSpec(minimum, maximum, step, decimals, units)
        self._ui_ranges = specs

    def _load_presets(self) -> None:
        presets: dict[str, GeometryPreset] = {}
        try:
            raw_presets = get_geometry_presets()
        except Exception as exc:
            self.logger.warning(
                "Не удалось загрузить пресеты геометрии из настроек: %s", exc
            )
            self._preset_map = {}
            if self._active_preset != "custom":
                self._active_preset = "custom"
            return
        for item in raw_presets:
            if not isinstance(item, Mapping):
                self.logger.warning(
                    "Пропускаем некорректный пресет геометрии: %s",
                    type(item).__name__,
                )
                continue
            key = item.get("key")
            label = item.get("label")
            values = item.get("values")
            if not isinstance(key, str) or not key.strip():
                self.logger.warning("Пресет без корректного ключа пропущен")
                continue
            if not isinstance(label, str) or not label.strip():
                label = key
            if not isinstance(values, Mapping):
                self.logger.warning(
                    "Пресет '%s' имеет некорректное поле 'values' (%s)",
                    key,
                    type(values).__name__,
                )
                continue
            numeric_values: dict[str, float] = {}
            for param, raw_value in values.items():
                try:
                    numeric_values[param] = float(raw_value)
                except (TypeError, ValueError):
                    self.logger.warning(
                        "Пресет '%s': параметр '%s' не является числом (%r)",
                        key,
                        param,
                        raw_value,
                    )
            presets[key] = GeometryPreset(
                key=key, label=label.strip(), values=numeric_values
            )
        self._preset_map = presets
        if self._active_preset not in self._preset_map:
            if self._active_preset != "custom":
                self.logger.warning(
                    "Активный пресет '%s' отсутствует в конфигурации, переключаемся на 'custom'",
                    self._active_preset,
                )
            self._active_preset = "custom"

    def _get_range(
        self,
        key: str,
        fallback_min: float,
        fallback_max: float,
        fallback_step: float,
        fallback_decimals: int,
        fallback_units: str,
    ) -> _RangeSpec:
        spec = self._ui_ranges.get(key)
        if spec is None:
            self.logger.warning(
                "Диапазон для параметра '%s' отсутствует в конфигурации; используем запасной диапазон",  # noqa: E501
                key,
            )
            return _RangeSpec(
                fallback_min,
                fallback_max,
                fallback_step,
                fallback_decimals,
                fallback_units,
            )
        return spec

    def _clamp_value(self, key: str, spec: _RangeSpec) -> float:
        raw = self.parameters.get(key)
        try:
            value = float(raw)
        except (TypeError, ValueError):
            value = spec.minimum
        if value < spec.minimum:
            self.logger.debug(
                "Параметр '%s' ниже минимума (%.3f < %.3f); выполняем клэмп",
                key,
                value,
                spec.minimum,
            )
            value = spec.minimum
        elif value > spec.maximum:
            self.logger.debug(
                "Параметр '%s' выше максимума (%.3f > %.3f); выполняем клэмп",
                key,
                value,
                spec.maximum,
            )
            value = spec.maximum
        self.parameters[key] = value
        return value

    def _select_preset(self, key: str) -> None:
        target = key if key in self._preset_map else "custom"
        index = self.preset_combo.findData(target)
        if index < 0:
            index = self.preset_combo.findData("custom")
        if index < 0:
            return
        if self.preset_combo.currentIndex() == index:
            return
        self._block_preset_signal = True
        try:
            self.preset_combo.setCurrentIndex(index)
        finally:
            self._block_preset_signal = False

    def _update_active_preset(self, key: str, *, update_combo: bool = True) -> None:
        if self._active_preset == key:
            return
        self._active_preset = key
        if update_combo:
            self._select_preset(key)
        try:
            self._settings_manager.set(
                "current.geometry.active_preset", key, auto_save=False
            )
        except Exception as exc:
            self.logger.error("Не удалось сохранить активный пресет '%s': %s", key, exc)

    def _persist_parameter(self, param_name: str, value: float | bool) -> None:
        try:
            self._settings_manager.set(
                f"current.geometry.{param_name}", value, auto_save=False
            )
        except Exception as exc:
            self.logger.error(
                "Не удалось сохранить параметр '%s' (%s): %s",
                param_name,
                value,
                exc,
            )

    def _mark_custom_on_user_change(self) -> None:
        if self._applying_preset:
            return
        if self._active_preset != "custom":
            self._update_active_preset("custom", update_combo=True)

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

    def _on_slider_step_changed(self, param: str, value: float) -> None:
        try:
            self._settings_manager.set(
                f"current.geometry.meta.{param}.step", float(value), auto_save=False
            )
        except Exception:
            pass

    def _on_slider_decimals_changed(self, param: str, value: int) -> None:
        try:
            self._settings_manager.set(
                f"current.geometry.meta.{param}.decimals", int(value), auto_save=False
            )
        except Exception:
            pass

    def _on_slider_units_changed(self, param: str, units: str) -> None:
        try:
            self._settings_manager.set(
                f"current.geometry.meta.{param}.units", str(units), auto_save=False
            )
        except Exception:
            pass
