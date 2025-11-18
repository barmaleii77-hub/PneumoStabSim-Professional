"""Reusable accordion panel primitives with undo/redo orchestration."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from dataclasses import dataclass
from functools import partial
from typing import Any
from collections.abc import Callable
from collections.abc import Iterable, Mapping

try:  # pragma: no cover - structlog is optional at runtime
    import structlog
except ImportError:  # pragma: no cover - fallback for minimal environments
    structlog = None  # type: ignore[assignment]

from PySide6.QtCore import QObject, Property, Signal, Slot
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QLabel,
    QComboBox,
    QCheckBox,
)

from config.constants import get_geometry_presets

from src.common.settings_manager import get_settings_manager
from src.ui.accordion import AccordionWidget
from src.ui.parameter_slider import ParameterSlider


def _coerce_float(value: float | None, fallback: float) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return float(fallback)


def _normalize_setting(value: float | None, *, default: float, minimum: float, maximum: float) -> tuple[float, bool]:
    """Coerce a numeric setting and track validity without trusting the stored value.

    The returned tuple is ``(bounded_value, is_valid)`` where ``bounded_value`` is
    clamped to the provided range so that UI widgets can be initialised safely even
    when persisted settings are out of bounds.
    """

    candidate = _coerce_float(value, default)
    is_valid = math.isfinite(candidate) and minimum <= candidate <= maximum
    bounded = min(max(candidate, minimum), maximum)
    return bounded, is_valid


def _build_logger(channel: str, *, panel: str | None = None):
    """Return a logger compatible with structlog bindings."""

    if structlog is not None:
        base = structlog.get_logger(channel)
        return base.bind(panel=panel) if panel else base

    name = channel if panel is None else f"{channel}.{panel}"
    return logging.getLogger(name)


def _log_event(logger, level: str, event: str, **kwargs) -> None:
    """Emit a structured log event with graceful fallback."""

    if structlog is not None and hasattr(logger, level):
        getattr(logger, level)(event, **kwargs)
        return

    message = event
    if kwargs:
        extras = " ".join(f"{key}={value!r}" for key, value in sorted(kwargs.items()))
        message = f"{event} | {extras}"
    getattr(logger, level)(message)


@dataclass(frozen=True)
class SliderFieldSpec:
    """Declarative description of a slider field."""

    key: str
    label: str
    min_value: float
    max_value: float
    step: float
    decimals: int
    unit: str = ""
    allow_range_edit: bool = True
    default: float = 0.0
    settings_key: str | None = None
    read_only: bool = False
    emit_signal: bool = True
    to_settings: Callable[[float], float] | None = None
    from_settings: Callable[[float], float] | None = None
    telemetry_key: str | None = None
    resets_preset: bool = True

    def __post_init__(self) -> None:
        if self.settings_key is None and not self.read_only:
            object.__setattr__(self, "settings_key", self.key)


@dataclass(frozen=True)
class PanelPreset:
    """Declarative preset definition applied across registered sliders."""

    preset_id: str
    label: str
    values: Mapping[str, float]
    description: str = ""
    telemetry_key: str | None = None


@dataclass(slots=True)
class _UndoCommand:
    """Undo/redo command for field mutations."""

    field_key: str
    previous: Any
    new: Any
    apply: Callable[[Any, str], None]
    telemetry_key: str


class PanelUndoController(QObject):
    """Tracks slider changes and exposes undo/redo operations."""

    undoAvailabilityChanged = Signal(bool)
    redoAvailabilityChanged = Signal(bool)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._undo_stack: list[_UndoCommand] = []
        self._redo_stack: list[_UndoCommand] = []
        self._replaying = False
        self._logger = _build_logger("diagnostics.ui.panels.undo", panel=None)

    @Property(bool, notify=undoAvailabilityChanged)
    def canUndo(self) -> bool:  # pragma: no cover - trivial Qt binding
        return bool(self._undo_stack)

    @Property(bool, notify=redoAvailabilityChanged)
    def canRedo(self) -> bool:  # pragma: no cover - trivial Qt binding
        return bool(self._redo_stack)

    @property
    def is_replaying(self) -> bool:
        """Return ``True`` while an undo/redo command is being replayed."""

        return self._replaying

    def push(self, command: _UndoCommand) -> None:
        """Record a new undo command."""

        if math.isclose(command.previous, command.new, rel_tol=1e-9, abs_tol=1e-12):
            return

        self._undo_stack.append(command)
        self._redo_stack.clear()
        _log_event(
            self._logger,
            "info",
            "undo.push",
            field=command.telemetry_key,
            previous=command.previous,
            new=command.new,
        )
        self._emit_state()

    @Slot()
    def undo(self) -> None:
        if not self._undo_stack:
            return

        command = self._undo_stack.pop()
        self._replaying = True
        try:
            command.apply(command.previous, "undo")
        finally:
            self._replaying = False
        self._redo_stack.append(command)
        _log_event(
            self._logger,
            "info",
            "undo.invoke",
            field=command.telemetry_key,
            value=command.previous,
        )
        self._emit_state()

    @Slot()
    def redo(self) -> None:
        if not self._redo_stack:
            return

        command = self._redo_stack.pop()
        self._replaying = True
        try:
            command.apply(command.new, "redo")
        finally:
            self._replaying = False
        self._undo_stack.append(command)
        _log_event(
            self._logger,
            "info",
            "redo.invoke",
            field=command.telemetry_key,
            value=command.new,
        )
        self._emit_state()

    def reset(self) -> None:
        """Clear undo and redo stacks."""

        self._undo_stack.clear()
        self._redo_stack.clear()
        self._emit_state()

    def _emit_state(self) -> None:
        self.undoAvailabilityChanged.emit(self.canUndo)
        self.redoAvailabilityChanged.emit(self.canRedo)


class SettingsBackedAccordionPanel(QWidget):
    """Base class wiring sliders to :class:`SettingsManager` and undo support."""

    presetsChanged = Signal()
    activePresetChanged = Signal()

    def __init__(
        self,
        settings_section: str,
        parent: QWidget | None = None,
        *,
        preset_settings_key: str | None = None,
        custom_preset_id: str = "custom",
    ) -> None:
        super().__init__(parent)
        self._settings_section = settings_section
        self._settings = get_settings_manager()
        self._undo_controller = PanelUndoController(self)
        self.content_layout = QVBoxLayout(self)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(8)
        panel_name = self.objectName() or self.__class__.__name__
        self._logger = _build_logger(
            "diagnostics.ui.panels.accordion", panel=panel_name
        )
        self._field_specs: dict[str, SliderFieldSpec] = {}
        self._field_widgets: dict[str, ParameterSlider] = {}
        self._field_values: dict[str, float] = {}
        self._preset_settings_key = preset_settings_key
        self._custom_preset_id = custom_preset_id
        self._presets: dict[str, PanelPreset] = {}
        self._preset_model: list[dict[str, str]] = []
        self._preset_telemetry_key = f"{self._settings_section}.preset"
        self._active_preset_id: str = custom_preset_id
        self._applying_preset = False

        if preset_settings_key:
            stored = self._settings.get(
                f"current.{self._settings_section}.{preset_settings_key}",
                custom_preset_id,
            )
            if isinstance(stored, str) and stored:
                self._active_preset_id = stored

    # ----------------------------------------------------------------- bindings
    @Property(QObject, constant=True)
    def undoController(self) -> QObject:  # pragma: no cover - Qt binding
        return self._undo_controller

    @Property("QVariantList", notify=presetsChanged)
    def presetModel(self) -> list[dict[str, Any]]:  # pragma: no cover - Qt binding
        return [dict(item) for item in self._preset_model]

    @Property(str, notify=activePresetChanged)
    def activePresetId(self) -> str:  # pragma: no cover - Qt binding
        return self._active_preset_id

    @Slot(str)
    def applyPreset(self, preset_id: str) -> None:  # pragma: no cover - Qt binding
        self.apply_preset(preset_id)

    # ------------------------------------------------------------------ helpers
    def add_slider_field(self, spec: SliderFieldSpec) -> ParameterSlider:
        """Create a :class:`ParameterSlider` from ``spec`` and wire callbacks."""

        if spec.key in self._field_specs:
            raise ValueError(f"Field '{spec.key}' already registered")

        slider = ParameterSlider(
            name=spec.label,
            initial_value=spec.default,
            min_value=spec.min_value,
            max_value=spec.max_value,
            step=spec.step,
            decimals=spec.decimals,
            unit=spec.unit,
            allow_range_edit=spec.allow_range_edit,
        )

        if spec.read_only:
            slider.spinbox.setReadOnly(True)
            slider.slider.setEnabled(False)

        initial = self._resolve_initial_value(spec)
        self._field_specs[spec.key] = spec
        self._field_widgets[spec.key] = slider
        self._field_values[spec.key] = initial

        slider.set_value(initial)
        slider.value_changed.connect(partial(self._handle_slider_change, spec.key))
        self.content_layout.addWidget(slider)
        return slider

    def slider(self, key: str) -> ParameterSlider:
        """Return the slider widget associated with ``key``."""

        return self._field_widgets[key]

    def _resolve_initial_value(self, spec: SliderFieldSpec) -> float:
        value = spec.default
        if spec.settings_key:
            path = spec.settings_key
            if not path.startswith("current."):
                path = f"current.{self._settings_section}.{spec.settings_key}"
            stored = self._settings.get(path, spec.default)
            try:
                candidate = spec.from_settings(stored) if spec.from_settings else stored
                value = float(candidate)
            except (TypeError, ValueError):
                _log_event(
                    self._logger,
                    "warning",
                    "settings.invalid",
                    field=spec.key,
                    path=path,
                    value=stored,
                )
                value = spec.default
        return value

    def _handle_slider_change(self, key: str, value: float) -> None:
        spec = self._field_specs[key]
        previous = self._field_values.get(key, value)
        previous_preset = self._active_preset_id if spec.resets_preset else None
        if math.isclose(previous, value, rel_tol=1e-9, abs_tol=1e-12):
            return

        self._field_values[key] = value

        new_preset = previous_preset
        should_reset_preset = (
            spec.resets_preset
            and not self._applying_preset
            and previous_preset is not None
        )

        if should_reset_preset and previous_preset != self._custom_preset_id:
            self._set_active_preset(
                self._custom_preset_id,
                reason="field-change",
                persist=True,
                _from_command=False,
            )
            new_preset = self._active_preset_id

        if not self._undo_controller.is_replaying:
            command = _UndoCommand(
                field_key=key,
                previous=(previous, previous_preset),
                new=(value, new_preset),
                telemetry_key=spec.telemetry_key or spec.settings_key or spec.key,
                apply=lambda payload, reason: self._apply_value_from_command(
                    key, payload, reason
                ),
            )
            self._undo_controller.push(command)

        self._commit_value(spec, value, source="user")
        if spec.emit_signal:
            self.on_field_value_changed(spec, value)

    def _apply_value_from_command(
        self, key: str, payload: tuple[float, str | None], source: str
    ) -> None:
        value, preset_id = payload
        spec = self._field_specs[key]
        slider = self._field_widgets[key]
        self._field_values[key] = value
        slider.blockSignals(True)
        try:
            slider.set_value(value)
        finally:
            slider.blockSignals(False)
        self._commit_value(spec, value, source=source)
        if spec.emit_signal:
            self.on_field_value_changed(spec, value)
        if preset_id is not None:
            self._set_active_preset(
                preset_id, reason=f"{source}.replay", persist=True, _from_command=True
            )

    def _commit_value(
        self, spec: SliderFieldSpec, value: float, *, source: str
    ) -> None:
        if spec.settings_key:
            path = spec.settings_key
            if not path.startswith("current."):
                path = f"current.{self._settings_section}.{spec.settings_key}"
            payload = value
            if spec.to_settings:
                try:
                    payload = spec.to_settings(value)
                except Exception as exc:  # pragma: no cover - defensive
                    _log_event(
                        self._logger,
                        "warning",
                        "settings.transform_failed",
                        field=spec.key,
                        error=str(exc),
                    )
                    payload = value
            self._settings.set(path, payload)

        telemetry_key = spec.telemetry_key or spec.settings_key or spec.key
        _log_event(
            self._logger,
            "info",
            "field.changed",
            field=telemetry_key,
            value=value,
            source=source,
        )

    # ---------------------------------------------------------------- interface
    def on_field_value_changed(self, spec: SliderFieldSpec, value: float) -> None:
        """Hook for subclasses to respond to slider updates."""

    def get_parameters(self) -> dict[str, float]:
        """Return a snapshot of registered field values."""

        return dict(self._field_values)

    def set_parameters(
        self,
        params: Mapping[str, float],
        *,
        source: str = "external",
        mark_custom: bool = False,
    ) -> None:
        """Update registered fields without emitting undo commands."""

        for key, value in params.items():
            if key not in self._field_specs:
                continue
            spec = self._field_specs[key]
            numeric_value = float(value)
            self._field_values[key] = numeric_value
            slider = self._field_widgets[key]
            slider.blockSignals(True)
            try:
                slider.set_value(numeric_value)
            finally:
                slider.blockSignals(False)
            self._commit_value(spec, numeric_value, source=source)
            if spec.emit_signal:
                self.on_field_value_changed(spec, numeric_value)
            if mark_custom and spec.resets_preset and not self._applying_preset:
                self._set_active_preset(
                    self._custom_preset_id,
                    reason="external-update",
                    persist=True,
                    _from_command=False,
                )

    def set_read_only_value(self, key: str, value: float) -> None:
        """Update read-only slider values without persisting to settings."""

        if key not in self._field_specs:
            raise KeyError(f"Unknown field '{key}'")
        spec = self._field_specs[key]
        slider = self._field_widgets[key]
        self._field_values[key] = value
        slider.blockSignals(True)
        try:
            slider.set_value(value)
        finally:
            slider.blockSignals(False)
        telemetry_key = spec.telemetry_key or spec.settings_key or spec.key
        _log_event(
            self._logger,
            "info",
            "field.read_only_update",
            field=telemetry_key,
            value=value,
        )

    # ---------------------------------------------------------------- presets
    @property
    def active_preset_id(self) -> str:
        """Return the currently active preset identifier."""

        return self._active_preset_id

    def register_presets(
        self,
        presets: Iterable[PanelPreset],
        *,
        telemetry_key: str | None = None,
    ) -> None:
        """Register preset definitions available for the panel."""

        preset_map: dict[str, PanelPreset] = {}
        for preset in presets:
            preset_map[preset.preset_id] = preset
        self._presets = preset_map
        self._update_preset_model()
        if telemetry_key:
            self._preset_telemetry_key = telemetry_key

        self._resolve_initial_preset_state()

    def apply_preset(
        self, preset_id: str, *, source: str = "preset", push_undo: bool = True
    ) -> None:
        """Apply the preset identified by ``preset_id``."""

        preset = self._presets.get(preset_id)
        if preset is None:
            raise KeyError(f"Unknown preset '{preset_id}'")

        target_values = self._prepare_preset_values(preset)
        if not target_values:
            return

        previous_snapshot = {
            key: self._field_values.get(key, target)
            for key, target in target_values.items()
        }
        previous_payload = (previous_snapshot, self._active_preset_id)
        next_payload = (target_values, preset_id)

        should_push = True
        if self._snapshots_equal(previous_snapshot, target_values) and (
            self._active_preset_id == preset_id
        ):
            should_push = False

        telemetry_key = preset.telemetry_key or self._preset_telemetry_key
        if push_undo and should_push:
            command = _UndoCommand(
                field_key=f"preset:{preset_id}",
                previous=previous_payload,
                new=next_payload,
                telemetry_key=telemetry_key,
                apply=self._apply_preset_from_command,
            )
            self._undo_controller.push(command)

        self._apply_preset_from_command(next_payload, source)

    # ----------------------------------------------------------------- helpers
    def _prepare_preset_values(self, preset: PanelPreset) -> dict[str, float]:
        values: dict[str, float] = {}
        for field_key, spec in self._field_specs.items():
            candidate_keys = [spec.key]
            if spec.settings_key and spec.settings_key not in candidate_keys:
                candidate_keys.append(spec.settings_key)

            resolved: float | None = None
            for candidate in candidate_keys:
                if candidate not in preset.values:
                    continue
                try:
                    resolved = float(preset.values[candidate])
                except (TypeError, ValueError):
                    _log_event(
                        self._logger,
                        "warning",
                        "preset.invalid_value",
                        field=candidate,
                        preset=preset.preset_id,
                        value=preset.values[candidate],
                    )
                    resolved = None
                break

            if resolved is not None:
                values[field_key] = resolved
        return values

    def _resolve_initial_preset_state(self) -> None:
        preset_from_settings: str | None = None
        if self._preset_settings_key:
            path = f"current.{self._settings_section}.{self._preset_settings_key}"
            stored = self._settings.get(path, self._custom_preset_id)
            if isinstance(stored, str) and stored:
                preset_from_settings = stored

        if preset_from_settings and preset_from_settings in self._presets:
            resolved = preset_from_settings
        else:
            resolved = self._match_snapshot_to_preset()
        self._active_preset_id = resolved
        self._persist_active_preset()
        self.activePresetChanged.emit()

    def _match_snapshot_to_preset(self) -> str:
        current = self.get_parameters()
        for preset in self._presets.values():
            target = self._prepare_preset_values(preset)
            if not target:
                continue
            if self._snapshots_equal(target, current):
                return preset.preset_id
        return self._custom_preset_id

    def _snapshots_equal(
        self, first: Mapping[str, float], second: Mapping[str, float]
    ) -> bool:
        keys = set(first) | set(second)
        for key in keys:
            left = first.get(key)
            right = second.get(key)
            if left is None or right is None:
                if left != right:
                    return False
                continue
            if not math.isclose(left, right, rel_tol=1e-9, abs_tol=1e-12):
                return False
        return True

    def _apply_preset_from_command(
        self, payload: tuple[Mapping[str, float], str | None], reason: str
    ) -> None:
        values, preset_id = payload
        self._applying_preset = True
        try:
            self.set_parameters(values, source=reason)
        finally:
            self._applying_preset = False
        if preset_id is not None:
            self._set_active_preset(
                preset_id, reason=reason, persist=True, _from_command=True
            )
        _log_event(
            self._logger,
            "info",
            "preset.apply",
            preset=preset_id,
            source=reason,
        )

    def _set_active_preset(
        self,
        preset_id: str,
        *,
        reason: str,
        persist: bool,
        _from_command: bool,
    ) -> None:
        if preset_id == self._active_preset_id:
            return
        self._active_preset_id = preset_id
        if persist:
            self._persist_active_preset()
        _log_event(
            self._logger,
            "info",
            "preset.changed",
            field=self._preset_telemetry_key,
            value=preset_id,
            source=reason,
            replay=_from_command,
        )
        self.activePresetChanged.emit()

    def _persist_active_preset(self) -> None:
        if not self._preset_settings_key:
            return
        path = f"current.{self._settings_section}.{self._preset_settings_key}"
        self._settings.set(path, self._active_preset_id)

    def _update_preset_model(self) -> None:
        self._preset_model = [
            {
                "id": preset.preset_id,
                "label": preset.label,
                "description": preset.description,
            }
            for preset in self._presets.values()
        ]
        self.presetsChanged.emit()


class GeometryPanelAccordion(SettingsBackedAccordionPanel):
    """Geometry parameters panel with settings-backed sliders."""

    parameter_changed = Signal(str, float)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            settings_section="geometry",
            parent=parent,
            preset_settings_key="active_preset",
        )

        from src.ui.panels.geometry.accordion_fields import build_geometry_field_specs

        for attr, spec in build_geometry_field_specs():
            slider = self.add_slider_field(spec)
            setattr(self, attr, slider)

        self._initialise_geometry_presets()

        self.content_layout.addStretch()

    def on_field_value_changed(self, spec: SliderFieldSpec, value: float) -> None:
        self.parameter_changed.emit(spec.key, value)

    def update_calculated_values(self, lever_angle: float) -> None:
        """Update the derived lever angle without recording undo state."""
        if "lever_angle" in self._field_widgets:
            self.set_read_only_value("lever_angle", lever_angle)

    def _initialise_geometry_presets(self) -> None:
        try:
            raw_presets = get_geometry_presets()
        except Exception as exc:  # pragma: no cover - defensive guard
            _log_event(
                self._logger,
                "warning",
                "preset.load_failed",
                error=str(exc),
            )
            return

        presets: list[PanelPreset] = []
        for entry in raw_presets:
            key = entry.get("key")
            values = entry.get("values")
            if not key or not isinstance(values, Mapping):
                continue
            label = entry.get("label") or str(key)
            description = entry.get("description", "")
            presets.append(
                PanelPreset(
                    preset_id=str(key),
                    label=str(label),
                    description=str(description),
                    values=values,
                    telemetry_key="geometry.preset",
                )
            )

        if presets:
            self.register_presets(presets, telemetry_key="geometry.preset")


class PneumoPanelAccordion(QWidget):
    """Pneumatics parameters panel"""

    parameter_changed = Signal(str, float)
    thermo_mode_changed = Signal(str)  # 'isothermal' or 'adiabatic'

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # === THERMO MODE ===

        thermo_label = QLabel("Thermodynamic Mode:")
        thermo_label.setStyleSheet("color: #aaaaaa; font-size: 9pt; font-weight: bold;")
        layout.addWidget(thermo_label)

        self.thermo_combo = QComboBox()
        self.thermo_combo.addItems(["Isothermal", "Adiabatic"])
        self.thermo_combo.setStyleSheet(
            """
            QComboBox {
                background-color: #2a2a3e;
                color: #ffffff;
                border: 1px solid #3a3a4e;
                border-radius: 3px;
                padding: 4px 6px;
                font-size: 9pt;
            }
            QComboBox::drop-down {
                border: none;
            }
            QComboBox:focus {
                border: 1px solid #5a9fd4;
            }
        """
        )
        self.thermo_combo.currentTextChanged.connect(
            lambda text: self.thermo_mode_changed.emit(text.lower())
        )
        layout.addWidget(self.thermo_combo)

        # === CYLINDER VOLUMES ===

        # Head volume (read-only, calculated from geometry)
        self.head_volume = ParameterSlider(
            name="Head Volume (V_h)",
            initial_value=500.0,
            min_value=100.0,
            max_value=2000.0,
            step=10.0,
            decimals=1,
            unit="cm?",
            allow_range_edit=False,
        )
        self.head_volume.spinbox.setReadOnly(True)
        self.head_volume.slider.setEnabled(False)
        layout.addWidget(self.head_volume)

        # Rod volume (read-only, calculated from geometry)
        self.rod_volume = ParameterSlider(
            name="Rod Volume (V_r)",
            initial_value=300.0,
            min_value=50.0,
            max_value=1500.0,
            step=10.0,
            decimals=1,
            unit="cm?",
            allow_range_edit=False,
        )
        self.rod_volume.spinbox.setReadOnly(True)
        self.rod_volume.slider.setEnabled(False)
        layout.addWidget(self.rod_volume)

        # === LINE PRESSURES ===

        # Line A1 pressure (initial)
        self.pressure_a1 = ParameterSlider(
            name="Line A1 Pressure (P_A1)",
            initial_value=150.0,
            min_value=50.0,
            max_value=500.0,
            step=5.0,
            decimals=1,
            unit="kPa",
            allow_range_edit=True,
        )
        self.pressure_a1.value_changed.connect(
            lambda v: self.parameter_changed.emit("pressure_a1", v)
        )
        layout.addWidget(self.pressure_a1)

        # Line B1 pressure (initial)
        self.pressure_b1 = ParameterSlider(
            name="Line B1 Pressure (P_B1)",
            initial_value=150.0,
            min_value=50.0,
            max_value=500.0,
            step=5.0,
            decimals=1,
            unit="kPa",
            allow_range_edit=True,
        )
        self.pressure_b1.value_changed.connect(
            lambda v: self.parameter_changed.emit("pressure_b1", v)
        )
        layout.addWidget(self.pressure_b1)

        # Line A2 pressure (initial)
        self.pressure_a2 = ParameterSlider(
            name="Line A2 Pressure (P_A2)",
            initial_value=150.0,
            min_value=50.0,
            max_value=500.0,
            step=5.0,
            decimals=1,
            unit="kPa",
            allow_range_edit=True,
        )
        self.pressure_a2.value_changed.connect(
            lambda v: self.parameter_changed.emit("pressure_a2", v)
        )
        layout.addWidget(self.pressure_a2)

        # Line B2 pressure (initial)
        self.pressure_b2 = ParameterSlider(
            name="Line B2 Pressure (P_B2)",
            initial_value=150.0,
            min_value=50.0,
            max_value=500.0,
            step=5.0,
            decimals=1,
            unit="kPa",
            allow_range_edit=True,
        )
        self.pressure_b2.value_changed.connect(
            lambda v: self.parameter_changed.emit("pressure_b2", v)
        )
        layout.addWidget(self.pressure_b2)

        # === TANK/RESERVOIR ===

        # Tank pressure
        self.tank_pressure = ParameterSlider(
            name="Tank Pressure (P_tank)",
            initial_value=200.0,
            min_value=100.0,
            max_value=600.0,
            step=10.0,
            decimals=1,
            unit="kPa",
            allow_range_edit=True,
        )
        self.tank_pressure.value_changed.connect(
            lambda v: self.parameter_changed.emit("tank_pressure", v)
        )
        layout.addWidget(self.tank_pressure)

        # Relief valve pressure
        self.relief_pressure = ParameterSlider(
            name="Relief Valve (P_relief)",
            initial_value=500.0,
            min_value=200.0,
            max_value=800.0,
            step=10.0,
            decimals=1,
            unit="kPa",
            allow_range_edit=True,
        )
        self.relief_pressure.value_changed.connect(
            lambda v: self.parameter_changed.emit("relief_pressure", v)
        )
        layout.addWidget(self.relief_pressure)

        # === TEMPERATURE ===

        # Atmospheric temperature
        self.temperature = ParameterSlider(
            name="Atmospheric Temp (T_atm)",
            initial_value=20.0,
            min_value=-20.0,
            max_value=50.0,
            step=1.0,
            decimals=1,
            unit="degC",  # Fixed: use ASCII instead of degree symbol
            allow_range_edit=True,
        )
        self.temperature.value_changed.connect(
            lambda v: self.parameter_changed.emit("temperature", v)
        )
        layout.addWidget(self.temperature)

        layout.addStretch()

    def get_parameters(self) -> dict:
        """Get all parameters"""
        return {
            "thermo_mode": self.thermo_combo.currentText().lower(),
            "head_volume": self.head_volume.value(),
            "rod_volume": self.rod_volume.value(),
            "pressure_a1": self.pressure_a1.value(),
            "pressure_b1": self.pressure_b1.value(),
            "pressure_a2": self.pressure_a2.value(),
            "pressure_b2": self.pressure_b2.value(),
            "tank_pressure": self.tank_pressure.value(),
            "relief_pressure": self.relief_pressure.value(),
            "temperature": self.temperature.value(),
        }

    def update_calculated_volumes(self, v_head: float, v_rod: float):
        """Update calculated volumes from geometry"""
        self.head_volume.set_value(v_head * 1e6)  # m? to cm?
        self.rod_volume.set_value(v_rod * 1e6)


@dataclass
class _SimulationAccordionState:
    physics_dt: float
    sim_speed: float
    sim_mode: str
    thermo_mode: str
    include_springs: bool
    include_dampers: bool
    check_interference: bool
    validation: dict[str, bool] = field(default_factory=dict)


class SimulationPanelAccordion(QWidget):
    """Simulation mode and settings panel"""

    sim_mode_changed = Signal(str)  # 'kinematics' or 'dynamics'
    option_changed = Signal(str, bool)  # (option_name, enabled)
    parameter_changed = Signal(str, float)
    validationStateChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._settings = get_settings_manager()
        self._state: _SimulationAccordionState | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.accordion = AccordionWidget()
        layout.addWidget(self.accordion)

        self._mode_section = self.accordion.add_section(
            "mode",
            "Simulation Modes",
            self._build_mode_section(),
            expanded=True,
        )
        self._options_section = self.accordion.add_section(
            "options",
            "Physics & Safety",
            self._build_options_section(),
        )
        self._timing_section = self.accordion.add_section(
            "timing",
            "Timing",
            self._build_timing_section(),
        )

        self._on_mode_changed(self.sim_mode_combo.currentText())
        self._refresh_state(use_settings_snapshot=True)

    @Property("QVariantMap", notify=validationStateChanged)
    def validationState(self) -> dict:
        return dict(self._state.validation) if self._state else {}

    @Property("QVariantMap", constant=True)
    def bindingsSnapshot(self) -> dict:
        if not self._state:
            return {}
        return {
            "physics_dt": self._state.physics_dt,
            "sim_speed": self._state.sim_speed,
            "sim_mode": self._state.sim_mode,
            "thermo_mode": self._state.thermo_mode,
            "include_springs": self._state.include_springs,
            "include_dampers": self._state.include_dampers,
            "check_interference": self._state.check_interference,
        }

    def _build_mode_section(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        mode_label = QLabel("Simulation Mode:")
        mode_label.setStyleSheet("color: #aaaaaa; font-size: 9pt; font-weight: bold;")
        layout.addWidget(mode_label)

        self.sim_mode_combo = QComboBox()
        self.sim_mode_combo.addItems(["Kinematics", "Dynamics"])
        stored_mode = str(self._settings.get("current.modes.sim_type", "DYNAMICS"))
        self.sim_mode_combo.setCurrentIndex(
            0 if stored_mode.lower() == "kinematics" else 1
        )
        self.sim_mode_combo.setStyleSheet(
            """
            QComboBox {
                background-color: #2a2a3e;
                color: #ffffff;
                border: 1px solid #3a3a4e;
                border-radius: 3px;
                padding: 4px 6px;
                font-size: 9pt;
            }
        """
        )
        self.sim_mode_combo.currentTextChanged.connect(self._on_mode_changed)
        layout.addWidget(self.sim_mode_combo)

        thermo_label = QLabel("Thermodynamic Model:")
        thermo_label.setStyleSheet("color: #aaaaaa; font-size: 9pt; font-weight: bold;")
        layout.addWidget(thermo_label)

        self.thermo_combo = QComboBox()
        self.thermo_combo.addItems(["Isothermal", "Adiabatic"])
        stored_thermo = str(
            self._settings.get("current.pneumatic.thermo_mode", "ISOTHERMAL")
        )
        self.thermo_combo.setCurrentIndex(
            0 if stored_thermo.lower() == "isothermal" else 1
        )
        self.thermo_combo.currentTextChanged.connect(self._on_thermo_changed)
        self.thermo_combo.setStyleSheet(
            """
            QComboBox {
                background-color: #2a2a3e;
                color: #ffffff;
                border: 1px solid #3a3a4e;
                border-radius: 3px;
                padding: 4px 6px;
                font-size: 9pt;
            }
        """
        )
        layout.addWidget(self.thermo_combo)

        return container

    def _build_options_section(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.kinematic_options_label = QLabel("Kinematic Options:")
        self.kinematic_options_label.setStyleSheet(
            "color: #aaaaaa; font-size: 9pt; font-weight: bold;"
        )
        layout.addWidget(self.kinematic_options_label)

        self.include_springs_check = QCheckBox("Include Springs")
        self.include_springs_check.setStyleSheet("color: #ffffff; font-size: 9pt;")
        self.include_springs_check.setChecked(
            bool(self._settings.get("current.modes.physics.include_springs", True))
        )
        self.include_springs_check.stateChanged.connect(
            lambda state: self._on_option_changed("include_springs", state == 2)
        )
        layout.addWidget(self.include_springs_check)

        self.include_dampers_check = QCheckBox("Include Dampers")
        self.include_dampers_check.setStyleSheet("color: #ffffff; font-size: 9pt;")
        self.include_dampers_check.setChecked(
            bool(self._settings.get("current.modes.physics.include_dampers", True))
        )
        self.include_dampers_check.stateChanged.connect(
            lambda state: self._on_option_changed("include_dampers", state == 2)
        )
        layout.addWidget(self.include_dampers_check)

        self.check_interference = QCheckBox("Check Lever-Cylinder Interference")
        self.check_interference.setStyleSheet("color: #ffffff; font-size: 9pt;")
        self.check_interference.setChecked(
            bool(
                self._settings.get(
                    "current.physics.validation.enable_interference_checks", False
                )
            )
        )
        self.check_interference.stateChanged.connect(
            lambda state: self._on_option_changed("check_interference", state == 2)
        )
        layout.addWidget(self.check_interference)

        return container

    def _build_timing_section(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        sim_dt_raw = self._settings.get("current.simulation.physics_dt", 0.001)
        sim_dt, _ = _normalize_setting(
            sim_dt_raw, default=0.001, minimum=0.0001, maximum=0.01
        )
        self.time_step = ParameterSlider(
            name="Time Step (dt)",
            initial_value=sim_dt,
            min_value=0.0001,
            max_value=0.01,
            step=0.0001,
            decimals=4,
            unit="s",
            allow_range_edit=True,
        )
        self.time_step.value_changed.connect(self._on_time_step_changed)
        layout.addWidget(self.time_step)

        sim_speed_raw = self._settings.get("current.simulation.sim_speed", 1.0)
        sim_speed, _ = _normalize_setting(
            sim_speed_raw, default=1.0, minimum=0.1, maximum=10.0
        )
        self.sim_speed = ParameterSlider(
            name="Simulation Speed",
            initial_value=sim_speed,
            min_value=0.1,
            max_value=10.0,
            step=0.1,
            decimals=1,
            unit="x",
            allow_range_edit=True,
        )
        self.sim_speed.value_changed.connect(
            lambda v: self._on_slider_changed("sim_speed", v)
        )
        layout.addWidget(self.sim_speed)

        return container

    def _on_mode_changed(self, mode_text: str):
        """Handle simulation mode change"""
        mode = mode_text.lower()
        is_kinematics = mode == "kinematics"

        self.kinematic_options_label.setVisible(is_kinematics)
        self.include_springs_check.setVisible(is_kinematics)
        self.include_dampers_check.setVisible(is_kinematics)

        self._settings.set("current.modes.sim_type", mode.upper(), auto_save=False)
        self.sim_mode_changed.emit(mode)
        self._refresh_state()

    def _on_thermo_changed(self, mode_text: str) -> None:
        thermo_mode = mode_text.upper()
        self._settings.set(
            "current.pneumatic.thermo_mode", thermo_mode, auto_save=False
        )
        self.parameter_changed.emit(
            "thermo_mode", 1.0 if thermo_mode == "ADIABATIC" else 0.0
        )
        self._refresh_state()

    def _on_option_changed(self, name: str, enabled: bool) -> None:
        mapping = {
            "include_springs": "current.modes.physics.include_springs",
            "include_dampers": "current.modes.physics.include_dampers",
            "check_interference": "current.physics.validation.enable_interference_checks",
        }
        path = mapping.get(name)
        if path:
            self._settings.set(path, enabled, auto_save=False)
        self.option_changed.emit(name, enabled)
        self._refresh_state()

    def _on_time_step_changed(self, value: float) -> None:
        self._settings.set(
            "current.simulation.physics_dt", float(value), auto_save=False
        )
        self.parameter_changed.emit("physics_dt", value)
        self._refresh_state()

    def _on_slider_changed(self, name: str, value: float) -> None:
        self._settings.set(f"current.simulation.{name}", float(value), auto_save=False)
        self.parameter_changed.emit(name, value)
        self._refresh_state()

    def get_parameters(self) -> dict:
        """Get all parameters"""
        return {
            "sim_mode": self.sim_mode_combo.currentText().lower(),
            "thermo_mode": self.thermo_combo.currentText().lower(),
            "include_springs": self.include_springs_check.isChecked(),
            "include_dampers": self.include_dampers_check.isChecked(),
            "check_interference": self.check_interference.isChecked(),
            "time_step": self.time_step.value(),
            "sim_speed": self.sim_speed.value(),
        }

    def _refresh_state(self, *, use_settings_snapshot: bool = False) -> None:
        """Synchronise internal state mirrors for tests and validation."""

        def _validate_range(val: float, slider: ParameterSlider) -> bool:
            low, high = slider.get_range()
            return math.isfinite(val) and low <= val <= high

        source_dt = (
            self._settings.get("current.simulation.physics_dt")
            if use_settings_snapshot
            else self.time_step.value()
        )
        bounded_dt, dt_valid = _normalize_setting(
            source_dt, default=0.001, minimum=0.0001, maximum=0.01
        )
        if not use_settings_snapshot:
            self.time_step.set_value(bounded_dt)

        source_speed = (
            self._settings.get("current.simulation.sim_speed")
            if use_settings_snapshot
            else self.sim_speed.value()
        )
        bounded_speed, speed_valid = _normalize_setting(
            source_speed, default=1.0, minimum=0.1, maximum=10.0
        )
        if not use_settings_snapshot:
            self.sim_speed.set_value(bounded_speed)

        sim_mode = self.sim_mode_combo.currentText().lower()
        thermo_mode = self.thermo_combo.currentText().upper()
        validation = {
            "physics_dt": dt_valid and _validate_range(bounded_dt, self.time_step),
            "sim_speed": speed_valid and _validate_range(bounded_speed, self.sim_speed),
            "sim_mode": sim_mode in {"kinematics", "dynamics"},
            "thermo_mode": thermo_mode in {"ISOTHERMAL", "ADIABATIC"},
        }

        self._state = _SimulationAccordionState(
            physics_dt=bounded_dt,
            sim_speed=bounded_speed,
            sim_mode=sim_mode,
            thermo_mode=thermo_mode,
            include_springs=self.include_springs_check.isChecked(),
            include_dampers=self.include_dampers_check.isChecked(),
            check_interference=self.check_interference.isChecked(),
            validation=validation,
        )
        self.validationStateChanged.emit()


@dataclass
class _RoadAccordionState:
    road_mode: str
    amplitude: float
    frequency: float
    phase: float
    profile_type: str
    avg_speed: float
    validation: dict[str, bool] = field(default_factory=dict)


class RoadPanelAccordion(QWidget):
    """Road input and excitation panel"""

    road_mode_changed = Signal(str)  # 'manual' or 'profile'
    parameter_changed = Signal(str, float)
    profile_type_changed = Signal(str)
    validationStateChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._settings = get_settings_manager()
        self._state: _RoadAccordionState | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.accordion = AccordionWidget()
        layout.addWidget(self.accordion)

        self._mode_section = self.accordion.add_section(
            "mode",
            "Road Input",
            self._build_mode_section(),
            expanded=True,
        )
        self._manual_section = self.accordion.add_section(
            "manual",
            "Manual Sine",
            self._build_manual_section(),
        )
        self._profile_section = self.accordion.add_section(
            "profile",
            "Road Profile",
            self._build_profile_section(),
        )

        self._on_mode_changed(self.road_mode_combo.currentText())
        self._refresh_state(use_settings_snapshot=True)

    @Property("QVariantMap", notify=validationStateChanged)
    def validationState(self) -> dict:
        return dict(self._state.validation) if self._state else {}

    @Property("QVariantMap", constant=True)
    def bindingsSnapshot(self) -> dict:
        if not self._state:
            return {}
        return {
            "road_mode": self._state.road_mode,
            "amplitude": self._state.amplitude,
            "frequency": self._state.frequency,
            "phase": self._state.phase,
            "profile_type": self._state.profile_type,
            "avg_speed": self._state.avg_speed,
        }

    def _build_mode_section(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        mode_label = QLabel("Road Input Mode:")
        mode_label.setStyleSheet("color: #aaaaaa; font-size: 9pt; font-weight: bold;")
        layout.addWidget(mode_label)

        self.road_mode_combo = QComboBox()
        self.road_mode_combo.addItems(["Manual (Sine)", "Road Profile"])
        self.road_mode_combo.setStyleSheet(
            """
            QComboBox {
                background-color: #2a2a3e;
                color: #ffffff;
                border: 1px solid #3a3a4e;
                border-radius: 3px;
                padding: 4px 6px;
                font-size: 9pt;
            }
        """
        )
        initial_mode = str(self._settings.get("current.modes.road_mode", "manual"))
        if initial_mode == "profile":
            self.road_mode_combo.setCurrentIndex(1)
        self.road_mode_combo.currentTextChanged.connect(self._on_mode_changed)
        layout.addWidget(self.road_mode_combo)

        return container

    def _build_manual_section(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        amplitude_raw = self._settings.get("current.modes.amplitude", 0.05)
        amplitude, _ = _normalize_setting(
            amplitude_raw, default=0.05, minimum=0.0, maximum=0.2
        )
        self.amplitude = ParameterSlider(
            name="Amplitude (A)",
            initial_value=amplitude,
            min_value=0.0,
            max_value=0.2,
            step=0.001,
            decimals=3,
            unit="m",
            allow_range_edit=True,
        )
        self.amplitude.value_changed.connect(
            lambda v: self._on_parameter_changed("amplitude", v)
        )
        layout.addWidget(self.amplitude)

        frequency_raw = self._settings.get("current.modes.frequency", 1.0)
        frequency, _ = _normalize_setting(
            frequency_raw, default=1.0, minimum=0.1, maximum=10.0
        )
        self.frequency = ParameterSlider(
            name="Frequency (f)",
            initial_value=frequency,
            min_value=0.1,
            max_value=10.0,
            step=0.1,
            decimals=2,
            unit="Hz",
            allow_range_edit=True,
        )
        self.frequency.value_changed.connect(
            lambda v: self._on_parameter_changed("frequency", v)
        )
        layout.addWidget(self.frequency)

        phase_raw = self._settings.get("current.modes.phase", 0.0)
        phase, _ = _normalize_setting(
            phase_raw, default=0.0, minimum=-180.0, maximum=180.0
        )
        self.phase_offset = ParameterSlider(
            name="Phase Offset (rear)",
            initial_value=phase,
            min_value=-180.0,
            max_value=180.0,
            step=1.0,
            decimals=1,
            unit="deg",
            allow_range_edit=True,
        )
        self.phase_offset.value_changed.connect(
            lambda v: self._on_parameter_changed("phase", v)
        )
        layout.addWidget(self.phase_offset)

        return container

    def _build_profile_section(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        self.profile_type_combo = QComboBox()
        self._profile_map = {
            "smooth_highway": "Smooth Highway",
            "city_streets": "City Streets",
            "off_road": "Off-Road",
            "mountain_serpentine": "Mountain Serpentine",
            "custom": "Custom",
        }
        self.profile_type_combo.addItems(list(self._profile_map.values()))
        self.profile_type_combo.setStyleSheet(
            """
            QComboBox {
                background-color: #2a2a3e;
                color: #ffffff;
                border: 1px solid #3a3a4e;
                border-radius: 3px;
                padding: 4px 6px;
                font-size: 9pt;
            }
        """
        )
        self.profile_type_combo.currentTextChanged.connect(self._on_profile_changed)
        layout.addWidget(self.profile_type_combo)

        speed_raw = self._settings.get("current.modes.profile_avg_speed", 40.0)
        speed, _ = _normalize_setting(
            speed_raw, default=40.0, minimum=5.0, maximum=150.0
        )
        self.avg_speed = ParameterSlider(
            name="Average Speed",
            initial_value=speed,
            min_value=5.0,
            max_value=150.0,
            step=1.0,
            decimals=0,
            unit="km/h",
            allow_range_edit=True,
        )
        self.avg_speed.value_changed.connect(
            lambda v: self._on_parameter_changed("profile_avg_speed", v)
        )
        layout.addWidget(self.avg_speed)

        return container

    def _on_mode_changed(self, mode_text: str) -> None:
        is_profile = "profile" in mode_text.lower()

        self._manual_section.setVisible(not is_profile)
        self._profile_section.setVisible(is_profile)

        if is_profile:
            self._profile_section.expand()
        else:
            self._manual_section.expand()

        mode = "profile" if is_profile else "manual"
        self._settings.set("current.modes.road_mode", mode, auto_save=False)
        self.road_mode_changed.emit(mode)
        self._refresh_state()

    def _on_parameter_changed(self, name: str, value: float) -> None:
        self._settings.set(f"current.modes.{name}", float(value), auto_save=False)
        self.parameter_changed.emit(name, value)
        self._refresh_state()

    def _on_profile_changed(self, label: str) -> None:
        for key, text in self._profile_map.items():
            if text == label:
                self._settings.set("current.modes.mode_preset", key, auto_save=False)
                self.profile_type_changed.emit(key)
                self._refresh_state()
                return
        self.profile_type_changed.emit(label.lower())
        self._refresh_state()

    def get_parameters(self) -> dict:
        """Get all parameters"""
        is_manual = "manual" in self.road_mode_combo.currentText().lower()

        if is_manual:
            return {
                "road_mode": "manual",
                "amplitude": self.amplitude.value(),
                "frequency": self.frequency.value(),
                "phase": self.phase_offset.value(),
            }
            return {
                "road_mode": "profile",
                "profile_type": self.profile_type_combo.currentText()
                .lower()
                .replace(" ", "_"),
                "avg_speed": self.avg_speed.value(),
        }

    def _refresh_state(self, *, use_settings_snapshot: bool = False) -> None:
        """Synchronise state mirrors and validation flags."""

        def _validate_range(val: float, slider: ParameterSlider) -> bool:
            low, high = slider.get_range()
            return math.isfinite(val) and low <= val <= high

        mode = "profile" if "profile" in self.road_mode_combo.currentText().lower() else "manual"

        source_amp = (
            self._settings.get("current.modes.amplitude")
            if use_settings_snapshot
            else self.amplitude.value()
        )
        amplitude, amp_valid = _normalize_setting(
            source_amp, default=0.05, minimum=0.0, maximum=0.2
        )
        if not use_settings_snapshot:
            self.amplitude.set_value(amplitude)

        source_freq = (
            self._settings.get("current.modes.frequency")
            if use_settings_snapshot
            else self.frequency.value()
        )
        frequency, freq_valid = _normalize_setting(
            source_freq, default=1.0, minimum=0.1, maximum=10.0
        )
        if not use_settings_snapshot:
            self.frequency.set_value(frequency)

        source_phase = (
            self._settings.get("current.modes.phase")
            if use_settings_snapshot
            else self.phase_offset.value()
        )
        phase, phase_valid = _normalize_setting(
            source_phase, default=0.0, minimum=-180.0, maximum=180.0
        )
        if not use_settings_snapshot:
            self.phase_offset.set_value(phase)

        source_speed = (
            self._settings.get("current.modes.profile_avg_speed")
            if use_settings_snapshot
            else self.avg_speed.value()
        )
        avg_speed, speed_valid = _normalize_setting(
            source_speed, default=40.0, minimum=5.0, maximum=150.0
        )
        if not use_settings_snapshot:
            self.avg_speed.set_value(avg_speed)

        profile_key = ""
        for key, label in self._profile_map.items():
            if label == self.profile_type_combo.currentText():
                profile_key = key
                break

        validation = {
            "road_mode": mode in {"manual", "profile"},
            "amplitude": amp_valid and _validate_range(amplitude, self.amplitude),
            "frequency": freq_valid and _validate_range(frequency, self.frequency),
            "phase": phase_valid and _validate_range(phase, self.phase_offset),
            "profile_type": bool(profile_key),
            "avg_speed": speed_valid and _validate_range(avg_speed, self.avg_speed),
        }

        self._state = _RoadAccordionState(
            road_mode=mode,
            amplitude=amplitude,
            frequency=frequency,
            phase=phase,
            profile_type=profile_key,
            avg_speed=avg_speed,
            validation=validation,
        )
        self.validationStateChanged.emit()


@dataclass
class _AdvancedAccordionState:
    spring_stiffness: float
    damper_coeff: float
    dead_zone: float
    atmospheric_temp: float
    target_fps: float
    render_scale: float
    shadow_filter: float
    validation: dict[str, bool] = field(default_factory=dict)


class AdvancedPanelAccordion(QWidget):
    """Advanced parameters panel"""

    parameter_changed = Signal(str, float)
    validationStateChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._settings = get_settings_manager()
        self._state: _AdvancedAccordionState | None = None

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.accordion = AccordionWidget()
        layout.addWidget(self.accordion)

        self._suspension_section = self.accordion.add_section(
            "suspension",
            "Suspension",
            self._build_suspension_section(),
            expanded=True,
        )
        self._environment_section = self.accordion.add_section(
            "environment",
            "Dead Zones & Environment",
            self._build_environment_section(),
        )
        self._graphics_section = self.accordion.add_section(
            "graphics",
            "Graphics",
            self._build_graphics_section(),
        )

        self._refresh_state(use_settings_snapshot=True)

    @Property("QVariantMap", notify=validationStateChanged)
    def validationState(self) -> dict:
        return dict(self._state.validation) if self._state else {}

    @Property("QVariantMap", constant=True)
    def bindingsSnapshot(self) -> dict:
        if not self._state:
            return {}
        return {
            "spring_stiffness": self._state.spring_stiffness,
            "damper_coeff": self._state.damper_coeff,
            "dead_zone": self._state.dead_zone,
            "atmospheric_temp": self._state.atmospheric_temp,
            "target_fps": self._state.target_fps,
            "render_scale": self._state.render_scale,
            "shadow_filter": self._state.shadow_filter,
        }

    def _build_suspension_section(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        spring_raw = self._settings.get("current.physics.suspension.spring_constant", 50000.0)
        spring_constant, _ = _normalize_setting(
            spring_raw, default=50000.0, minimum=10000.0, maximum=200000.0
        )
        self.spring_stiffness = ParameterSlider(
            name="Spring Stiffness (k)",
            initial_value=spring_constant,
            min_value=10000.0,
            max_value=200000.0,
            step=1000.0,
            decimals=0,
            unit="N/m",
            allow_range_edit=True,
        )
        self.spring_stiffness.value_changed.connect(
            lambda v: self._on_parameter_changed(
                "physics.suspension.spring_constant", v
            )
        )
        layout.addWidget(self.spring_stiffness)

        damper_raw = self._settings.get(
            "current.physics.suspension.damper_coefficient", 2000.0
        )
        damper_coeff, _ = _normalize_setting(
            damper_raw, default=2000.0, minimum=500.0, maximum=10000.0
        )
        self.damper_coeff = ParameterSlider(
            name="Damper Coefficient (c)",
            initial_value=damper_coeff,
            min_value=500.0,
            max_value=10000.0,
            step=100.0,
            decimals=0,
            unit="N*s/m",
            allow_range_edit=True,
        )
        self.damper_coeff.value_changed.connect(
            lambda v: self._on_parameter_changed(
                "physics.suspension.damper_coefficient", v
            )
        )
        layout.addWidget(self.damper_coeff)

        return container

    def _build_environment_section(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        dead_zone_raw = self._settings.get(
            "current.physics.suspension.dead_zone_percent", 5.0
        )
        dead_zone, _ = _normalize_setting(
            dead_zone_raw, default=5.0, minimum=0.0, maximum=20.0
        )
        self.dead_zone = ParameterSlider(
            name="Dead Zone (both ends)",
            initial_value=dead_zone,
            min_value=0.0,
            max_value=20.0,
            step=0.5,
            decimals=1,
            unit="%",
            allow_range_edit=True,
        )
        self.dead_zone.value_changed.connect(
            lambda v: self._on_parameter_changed(
                "physics.suspension.dead_zone_percent", v
            )
        )
        layout.addWidget(self.dead_zone)

        atm_temp_raw = self._settings.get("current.pneumatic.atmo_temp", 20.0)
        atm_temp, _ = _normalize_setting(
            atm_temp_raw, default=20.0, minimum=-80.0, maximum=150.0
        )
        self.atmospheric_temp = ParameterSlider(
            name="Atmospheric Temp",
            initial_value=atm_temp,
            min_value=-80.0,
            max_value=150.0,
            step=1.0,
            decimals=1,
            unit="°C",
            allow_range_edit=True,
        )
        self.atmospheric_temp.value_changed.connect(
            lambda v: self._on_parameter_changed("pneumatic.atmo_temp", v)
        )
        layout.addWidget(self.atmospheric_temp)

        return container

    def _build_graphics_section(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(6)

        frame_limit_raw = self._settings.get(
            "current.graphics.quality.frame_rate_limit", 144.0
        )
        frame_limit, _ = _normalize_setting(
            frame_limit_raw, default=144.0, minimum=30.0, maximum=240.0
        )
        self.target_fps = ParameterSlider(
            name="Target FPS",
            initial_value=frame_limit,
            min_value=30.0,
            max_value=240.0,
            step=5.0,
            decimals=0,
            unit="fps",
            allow_range_edit=False,
        )
        self.target_fps.value_changed.connect(
            lambda v: self._on_parameter_changed("graphics.quality.frame_rate_limit", v)
        )
        layout.addWidget(self.target_fps)

        render_scale_raw = self._settings.get("current.graphics.quality.render_scale", 1.05)
        render_scale, _ = _normalize_setting(
            render_scale_raw, default=1.05, minimum=0.5, maximum=2.0
        )
        self.aa_quality = ParameterSlider(
            name="Render Scale",
            initial_value=render_scale,
            min_value=0.5,
            max_value=2.0,
            step=0.05,
            decimals=2,
            unit="x",
            allow_range_edit=True,
        )
        self.aa_quality.value_changed.connect(
            lambda v: self._on_parameter_changed("graphics.quality.render_scale", v)
        )
        layout.addWidget(self.aa_quality)

        shadow_filter_raw = self._settings.get(
            "current.graphics.quality.shadows.filter", 32.0
        )
        shadow_filter, _ = _normalize_setting(
            shadow_filter_raw, default=32.0, minimum=1.0, maximum=128.0
        )
        self.shadow_quality = ParameterSlider(
            name="Shadow Filter Size",
            initial_value=shadow_filter,
            min_value=1.0,
            max_value=128.0,
            step=1.0,
            decimals=0,
            unit="px",
            allow_range_edit=False,
        )
        self.shadow_quality.value_changed.connect(
            lambda v: self._on_parameter_changed("graphics.quality.shadows.filter", v)
        )
        layout.addWidget(self.shadow_quality)

        return container

    def get_parameters(self) -> dict:
        """Get all parameters"""
        return {
            "spring_stiffness": self.spring_stiffness.value(),
            "damper_coeff": self.damper_coeff.value(),
            "dead_zone": self.dead_zone.value(),
            "atmospheric_temp": self.atmospheric_temp.value(),
            "target_fps": self.target_fps.value(),
            "render_scale": self.aa_quality.value(),
            "shadow_filter": self.shadow_quality.value(),
        }

    def _refresh_state(self, *, use_settings_snapshot: bool = False) -> None:
        """Synchronise state mirrors and validation flags for tests."""

        def _validate_range(val: float, slider: ParameterSlider) -> bool:
            low, high = slider.get_range()
            return math.isfinite(val) and low <= val <= high

        source_spring = (
            self._settings.get("current.physics.suspension.spring_constant")
            if use_settings_snapshot
            else self.spring_stiffness.value()
        )
        spring, spring_valid = _normalize_setting(
            source_spring, default=50000.0, minimum=10000.0, maximum=200000.0
        )
        if not use_settings_snapshot:
            self.spring_stiffness.set_value(spring)

        source_damper = (
            self._settings.get("current.physics.suspension.damper_coefficient")
            if use_settings_snapshot
            else self.damper_coeff.value()
        )
        damper, damper_valid = _normalize_setting(
            source_damper, default=2000.0, minimum=500.0, maximum=10000.0
        )
        if not use_settings_snapshot:
            self.damper_coeff.set_value(damper)

        source_dead_zone = (
            self._settings.get("current.physics.suspension.dead_zone_percent")
            if use_settings_snapshot
            else self.dead_zone.value()
        )
        dead_zone, dead_zone_valid = _normalize_setting(
            source_dead_zone, default=5.0, minimum=0.0, maximum=20.0
        )
        if not use_settings_snapshot:
            self.dead_zone.set_value(dead_zone)

        source_temp = (
            self._settings.get("current.pneumatic.atmo_temp")
            if use_settings_snapshot
            else self.atmospheric_temp.value()
        )
        atmo_temp, temp_valid = _normalize_setting(
            source_temp, default=20.0, minimum=-80.0, maximum=150.0
        )
        if not use_settings_snapshot:
            self.atmospheric_temp.set_value(atmo_temp)

        source_fps = (
            self._settings.get("current.graphics.quality.frame_rate_limit")
            if use_settings_snapshot
            else self.target_fps.value()
        )
        target_fps, fps_valid = _normalize_setting(
            source_fps, default=144.0, minimum=30.0, maximum=240.0
        )
        if not use_settings_snapshot:
            self.target_fps.set_value(target_fps)

        source_render_scale = (
            self._settings.get("current.graphics.quality.render_scale")
            if use_settings_snapshot
            else self.aa_quality.value()
        )
        render_scale, render_valid = _normalize_setting(
            source_render_scale, default=1.05, minimum=0.5, maximum=2.0
        )
        if not use_settings_snapshot:
            self.aa_quality.set_value(render_scale)

        source_shadow = (
            self._settings.get("current.graphics.quality.shadows.filter")
            if use_settings_snapshot
            else self.shadow_quality.value()
        )
        shadow, shadow_valid = _normalize_setting(
            source_shadow, default=32.0, minimum=1.0, maximum=128.0
        )
        if not use_settings_snapshot:
            self.shadow_quality.set_value(shadow)

        validation = {
            "spring_stiffness": spring_valid and _validate_range(spring, self.spring_stiffness),
            "damper_coeff": damper_valid and _validate_range(damper, self.damper_coeff),
            "dead_zone": dead_zone_valid and _validate_range(dead_zone, self.dead_zone),
            "atmospheric_temp": temp_valid and _validate_range(atmo_temp, self.atmospheric_temp),
            "target_fps": fps_valid and _validate_range(target_fps, self.target_fps),
            "render_scale": render_valid and _validate_range(render_scale, self.aa_quality),
            "shadow_filter": shadow_valid and _validate_range(shadow, self.shadow_quality),
        }

        self._state = _AdvancedAccordionState(
            spring_stiffness=spring,
            damper_coeff=damper,
            dead_zone=dead_zone,
            atmospheric_temp=atmo_temp,
            target_fps=target_fps,
            render_scale=render_scale,
            shadow_filter=shadow,
            validation=validation,
        )
        self.validationStateChanged.emit()

    def _on_parameter_changed(self, dotted_key: str, value: float) -> None:
        self._settings.set(f"current.{dotted_key}", float(value), auto_save=False)
        short_key = dotted_key.split(".")[-1]
        self.parameter_changed.emit(short_key, value)
        self._refresh_state()


# Export
__all__ = [
    "GeometryPanelAccordion",
    "PneumoPanelAccordion",
    "SimulationPanelAccordion",
    "RoadPanelAccordion",
    "AdvancedPanelAccordion",
]
