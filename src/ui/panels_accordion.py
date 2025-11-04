# -*- coding: utf-8 -*-
"""Reusable accordion panel primitives with undo/redo orchestration."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from functools import partial
from typing import Any, Callable, Dict, Iterable, Mapping, Optional

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
from src.ui.parameter_slider import ParameterSlider


def _build_logger(channel: str, *, panel: Optional[str] = None):
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
    settings_key: Optional[str] = None
    read_only: bool = False
    emit_signal: bool = True
    to_settings: Optional[Callable[[float], float]] = None
    from_settings: Optional[Callable[[float], float]] = None
    telemetry_key: Optional[str] = None
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
    telemetry_key: Optional[str] = None


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

    def __init__(self, parent: Optional[QObject] = None) -> None:
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
        parent: Optional[QWidget] = None,
        *,
        preset_settings_key: Optional[str] = None,
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
        self._field_specs: Dict[str, SliderFieldSpec] = {}
        self._field_widgets: Dict[str, ParameterSlider] = {}
        self._field_values: Dict[str, float] = {}
        self._preset_settings_key = preset_settings_key
        self._custom_preset_id = custom_preset_id
        self._presets: Dict[str, PanelPreset] = {}
        self._preset_model: list[Dict[str, str]] = []
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
    def presetModel(self) -> list[Dict[str, Any]]:  # pragma: no cover - Qt binding
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
        self, key: str, payload: tuple[float, Optional[str]], source: str
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

    def get_parameters(self) -> Dict[str, float]:
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
        telemetry_key: Optional[str] = None,
    ) -> None:
        """Register preset definitions available for the panel."""

        preset_map: Dict[str, PanelPreset] = {}
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
    def _prepare_preset_values(self, preset: PanelPreset) -> Dict[str, float]:
        values: Dict[str, float] = {}
        for field_key, spec in self._field_specs.items():
            candidate_keys = [spec.key]
            if spec.settings_key and spec.settings_key not in candidate_keys:
                candidate_keys.append(spec.settings_key)

            resolved: Optional[float] = None
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
        preset_from_settings: Optional[str] = None
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
        self, payload: tuple[Mapping[str, float], Optional[str]], reason: str
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

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(
            settings_section="geometry",
            parent=parent,
            preset_settings_key="active_preset",
        )

        field_specs = (
            (
                "wheelbase",
                SliderFieldSpec(
                    key="wheelbase",
                    label="Wheelbase (L)",
                    min_value=2.0,
                    max_value=5.0,
                    step=0.01,
                    decimals=3,
                    unit="m",
                    allow_range_edit=True,
                    default=3.0,
                    settings_key="wheelbase",
                    telemetry_key="geometry.wheelbase",
                ),
            ),
            (
                "track_width",
                SliderFieldSpec(
                    key="track_width",
                    label="Track Width (B)",
                    min_value=1.0,
                    max_value=2.5,
                    step=0.01,
                    decimals=3,
                    unit="m",
                    allow_range_edit=True,
                    default=1.8,
                    settings_key="track",
                    telemetry_key="geometry.track",
                ),
            ),
            (
                "lever_arm",
                SliderFieldSpec(
                    key="lever_arm",
                    label="Lever Arm (r)",
                    min_value=0.1,
                    max_value=0.6,
                    step=0.001,
                    decimals=3,
                    unit="m",
                    allow_range_edit=True,
                    default=0.3,
                    settings_key="lever_length",
                    telemetry_key="geometry.lever_length",
                ),
            ),
            (
                "lever_angle",
                SliderFieldSpec(
                    key="lever_angle",
                    label="Lever Angle (?)",
                    min_value=-30.0,
                    max_value=30.0,
                    step=0.1,
                    decimals=2,
                    unit="deg",
                    allow_range_edit=False,
                    default=0.0,
                    read_only=True,
                    emit_signal=False,
                    telemetry_key="geometry.lever_angle",
                ),
            ),
            (
                "cylinder_stroke",
                SliderFieldSpec(
                    key="cylinder_stroke",
                    label="Cylinder Stroke (s_max)",
                    min_value=0.05,
                    max_value=0.5,
                    step=0.001,
                    decimals=3,
                    unit="m",
                    allow_range_edit=True,
                    default=0.2,
                    settings_key="stroke_m",
                    telemetry_key="geometry.stroke",
                ),
            ),
            (
                "piston_diameter",
                SliderFieldSpec(
                    key="piston_diameter",
                    label="Piston Diameter (D_p)",
                    min_value=0.03,
                    max_value=0.15,
                    step=0.001,
                    decimals=3,
                    unit="m",
                    allow_range_edit=True,
                    default=0.08,
                    settings_key="cyl_diam_m",
                    telemetry_key="geometry.cyl_diameter",
                ),
            ),
            (
                "rod_diameter",
                SliderFieldSpec(
                    key="rod_diameter",
                    label="Rod Diameter (D_r)",
                    min_value=0.01,
                    max_value=0.10,
                    step=0.001,
                    decimals=3,
                    unit="m",
                    allow_range_edit=True,
                    default=0.04,
                    settings_key="rod_diameter_m",
                    telemetry_key="geometry.rod_diameter",
                ),
            ),
            (
                "frame_mass",
                SliderFieldSpec(
                    key="frame_mass",
                    label="Frame Mass (M_frame)",
                    min_value=500.0,
                    max_value=5000.0,
                    step=10.0,
                    decimals=1,
                    unit="kg",
                    allow_range_edit=True,
                    default=1500.0,
                    settings_key="frame_mass",
                    telemetry_key="geometry.frame_mass",
                ),
            ),
            (
                "wheel_mass",
                SliderFieldSpec(
                    key="wheel_mass",
                    label="Wheel Mass (M_wheel)",
                    min_value=10.0,
                    max_value=200.0,
                    step=1.0,
                    decimals=1,
                    unit="kg",
                    allow_range_edit=True,
                    default=50.0,
                    settings_key="wheel_mass",
                    telemetry_key="geometry.wheel_mass",
                ),
            ),
        )

        for attr, spec in field_specs:
            slider = self.add_slider_field(spec)
            setattr(self, attr, slider)

        self._initialise_geometry_presets()

        self.content_layout.addStretch()

    def on_field_value_changed(self, spec: SliderFieldSpec, value: float) -> None:
        self.parameter_changed.emit(spec.key, value)

    def update_calculated_values(self, lever_angle: float) -> None:
        """Update the derived lever angle without recording undo state."""

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


class SimulationPanelAccordion(QWidget):
    """Simulation mode and settings panel"""

    sim_mode_changed = Signal(str)  # 'kinematics' or 'dynamics'
    option_changed = Signal(str, bool)  # (option_name, enabled)
    parameter_changed = Signal(str, float)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # === SIMULATION MODE ===

        mode_label = QLabel("Simulation Mode:")
        mode_label.setStyleSheet("color: #aaaaaa; font-size: 9pt; font-weight: bold;")
        layout.addWidget(mode_label)

        self.sim_mode_combo = QComboBox()
        self.sim_mode_combo.addItems(["Kinematics", "Dynamics"])
        self.sim_mode_combo.setCurrentIndex(1)  # Default: Dynamics
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
        self.sim_mode_combo.currentTextChanged.connect(
            lambda text: self._on_mode_changed(text.lower())
        )
        layout.addWidget(self.sim_mode_combo)

        # === KINEMATIC MODE OPTIONS (only for kinematics) ===

        self.kinematic_options_label = QLabel("Kinematic Options:")
        self.kinematic_options_label.setStyleSheet(
            "color: #aaaaaa; font-size: 9pt; font-weight: bold;"
        )
        layout.addWidget(self.kinematic_options_label)

        self.include_springs_check = QCheckBox("Include Springs")
        self.include_springs_check.setStyleSheet("color: #ffffff; font-size: 9pt;")
        self.include_springs_check.setChecked(True)
        self.include_springs_check.stateChanged.connect(
            lambda state: self.option_changed.emit("include_springs", state == 2)
        )
        layout.addWidget(self.include_springs_check)

        self.include_dampers_check = QCheckBox("Include Dampers")
        self.include_dampers_check.setStyleSheet("color: #ffffff; font-size: 9pt;")
        self.include_dampers_check.setChecked(True)
        self.include_dampers_check.stateChanged.connect(
            lambda state: self.option_changed.emit("include_dampers", state == 2)
        )
        layout.addWidget(self.include_dampers_check)

        # Initially hide kinematic options (dynamics mode)
        self.kinematic_options_label.hide()
        self.include_springs_check.hide()
        self.include_dampers_check.hide()

        # === INTERFERENCE CHECK ===

        self.check_interference = QCheckBox("Check Lever-Cylinder Interference")
        self.check_interference.setStyleSheet("color: #ffffff; font-size: 9pt;")
        self.check_interference.setChecked(False)
        self.check_interference.stateChanged.connect(
            lambda state: self.option_changed.emit("check_interference", state == 2)
        )
        layout.addWidget(self.check_interference)

        # === TIMING PARAMETERS ===

        # Time step
        self.time_step = ParameterSlider(
            name="Time Step (dt)",
            initial_value=0.001,
            min_value=0.0001,
            max_value=0.01,
            step=0.0001,
            decimals=4,
            unit="s",
            allow_range_edit=True,
        )
        self.time_step.value_changed.connect(
            lambda v: self.parameter_changed.emit("time_step", v)
        )
        layout.addWidget(self.time_step)

        # Simulation speed
        self.sim_speed = ParameterSlider(
            name="Simulation Speed",
            initial_value=1.0,
            min_value=0.1,
            max_value=10.0,
            step=0.1,
            decimals=1,
            unit="x",
            allow_range_edit=True,
        )
        self.sim_speed.value_changed.connect(
            lambda v: self.parameter_changed.emit("sim_speed", v)
        )
        layout.addWidget(self.sim_speed)

        layout.addStretch()

    def _on_mode_changed(self, mode: str):
        """Handle simulation mode change"""
        is_kinematics = mode == "kinematics"

        # Show/hide kinematic options
        self.kinematic_options_label.setVisible(is_kinematics)
        self.include_springs_check.setVisible(is_kinematics)
        self.include_dampers_check.setVisible(is_kinematics)

        self.sim_mode_changed.emit(mode)

    def get_parameters(self) -> dict:
        """Get all parameters"""
        return {
            "sim_mode": self.sim_mode_combo.currentText().lower(),
            "include_springs": self.include_springs_check.isChecked(),
            "include_dampers": self.include_dampers_check.isChecked(),
            "check_interference": self.check_interference.isChecked(),
            "time_step": self.time_step.value(),
            "sim_speed": self.sim_speed.value(),
        }


class RoadPanelAccordion(QWidget):
    """Road input and excitation panel"""

    road_mode_changed = Signal(str)  # 'manual' or 'profile'
    parameter_changed = Signal(str, float)
    profile_type_changed = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # === ROAD MODE ===

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
        self.road_mode_combo.currentTextChanged.connect(self._on_mode_changed)
        layout.addWidget(self.road_mode_combo)

        # === MANUAL MODE PARAMETERS ===

        self.manual_label = QLabel("Manual Parameters:")
        self.manual_label.setStyleSheet(
            "color: #aaaaaa; font-size: 9pt; font-weight: bold;"
        )
        layout.addWidget(self.manual_label)

        # Amplitude (all wheels)
        self.amplitude = ParameterSlider(
            name="Amplitude (A)",
            initial_value=0.05,
            min_value=0.0,
            max_value=0.2,
            step=0.001,
            decimals=3,
            unit="m",
            allow_range_edit=True,
        )
        self.amplitude.value_changed.connect(
            lambda v: self.parameter_changed.emit("amplitude", v)
        )
        layout.addWidget(self.amplitude)

        # Frequency (all wheels)
        self.frequency = ParameterSlider(
            name="Frequency (f)",
            initial_value=1.0,
            min_value=0.1,
            max_value=10.0,
            step=0.1,
            decimals=2,
            unit="Hz",
            allow_range_edit=True,
        )
        self.frequency.value_changed.connect(
            lambda v: self.parameter_changed.emit("frequency", v)
        )
        layout.addWidget(self.frequency)

        # Phase offset (rear vs front)
        self.phase_offset = ParameterSlider(
            name="Phase Offset (rear)",
            initial_value=0.0,
            min_value=-180.0,
            max_value=180.0,
            step=1.0,
            decimals=1,
            unit="deg",
            allow_range_edit=True,
        )
        self.phase_offset.value_changed.connect(
            lambda v: self.parameter_changed.emit("phase_offset", v)
        )
        layout.addWidget(self.phase_offset)

        # === ROAD PROFILE PARAMETERS ===

        self.profile_label = QLabel("Road Profile:")
        self.profile_label.setStyleSheet(
            "color: #aaaaaa; font-size: 9pt; font-weight: bold;"
        )
        layout.addWidget(self.profile_label)

        self.profile_type_combo = QComboBox()
        profile_options = (
            "Smooth Highway",
            "City Streets",
            "Off-Road",
            "Mountain Serpentine",
            "Custom",
        )
        self.profile_type_combo.addItems(list(profile_options))
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
        self.profile_type_combo.currentTextChanged.connect(
            lambda text: self.profile_type_changed.emit(text.lower().replace(" ", "_"))
        )
        layout.addWidget(self.profile_type_combo)

        # Average speed
        self.avg_speed = ParameterSlider(
            name="Average Speed (v_avg)",
            initial_value=60.0,
            min_value=10.0,
            max_value=120.0,
            step=5.0,
            decimals=1,
            unit="km/h",
            allow_range_edit=True,
        )
        self.avg_speed.value_changed.connect(
            lambda v: self.parameter_changed.emit("avg_speed", v)
        )
        layout.addWidget(self.avg_speed)

        # Initially hide profile parameters
        self.profile_label.hide()
        self.profile_type_combo.hide()
        self.avg_speed.hide()

        layout.addStretch()

    def _on_mode_changed(self, mode_text: str):
        """Handle road mode change"""
        is_profile = "profile" in mode_text.lower()

        # Show/hide parameters
        self.manual_label.setVisible(not is_profile)
        self.amplitude.setVisible(not is_profile)
        self.frequency.setVisible(not is_profile)
        self.phase_offset.setVisible(not is_profile)

        self.profile_label.setVisible(is_profile)
        self.profile_type_combo.setVisible(is_profile)
        self.avg_speed.setVisible(is_profile)

        mode = "profile" if is_profile else "manual"
        self.road_mode_changed.emit(mode)

    def get_parameters(self) -> dict:
        """Get all parameters"""
        is_manual = "manual" in self.road_mode_combo.currentText().lower()

        if is_manual:
            return {
                "road_mode": "manual",
                "amplitude": self.amplitude.value(),
                "frequency": self.frequency.value(),
                "phase_offset": self.phase_offset.value(),
            }
        else:
            return {
                "road_mode": "profile",
                "profile_type": self.profile_type_combo.currentText()
                .lower()
                .replace(" ", "_"),
                "avg_speed": self.avg_speed.value(),
            }


class AdvancedPanelAccordion(QWidget):
    """Advanced parameters panel"""

    parameter_changed = Signal(str, float)

    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # === SUSPENSION COMPONENTS ===

        susp_label = QLabel("Suspension:")
        susp_label.setStyleSheet("color: #aaaaaa; font-size: 9pt; font-weight: bold;")
        layout.addWidget(susp_label)

        # Spring stiffness
        self.spring_stiffness = ParameterSlider(
            name="Spring Stiffness (k)",
            initial_value=50000.0,
            min_value=10000.0,
            max_value=200000.0,
            step=1000.0,
            decimals=0,
            unit="N/m",
            allow_range_edit=True,
        )
        self.spring_stiffness.value_changed.connect(
            lambda v: self.parameter_changed.emit("spring_stiffness", v)
        )
        layout.addWidget(self.spring_stiffness)

        # Damper coefficient
        self.damper_coeff = ParameterSlider(
            name="Damper Coefficient (c)",
            initial_value=2000.0,
            min_value=500.0,
            max_value=10000.0,
            step=100.0,
            decimals=0,
            unit="N*s/m",
            allow_range_edit=True,
        )
        self.damper_coeff.value_changed.connect(
            lambda v: self.parameter_changed.emit("damper_coeff", v)
        )
        layout.addWidget(self.damper_coeff)

        # === DEAD ZONES ===

        dz_label = QLabel("Cylinder Dead Zones:")
        dz_label.setStyleSheet("color: #aaaaaa; font-size: 9pt; font-weight: bold;")
        layout.addWidget(dz_label)

        self.dead_zone = ParameterSlider(
            name="Dead Zone (both ends)",
            initial_value=5.0,
            min_value=0.0,
            max_value=20.0,
            step=0.5,
            decimals=1,
            unit="%",
            allow_range_edit=True,
        )
        self.dead_zone.value_changed.connect(
            lambda v: self.parameter_changed.emit("dead_zone", v)
        )
        layout.addWidget(self.dead_zone)

        # === GRAPHICS SETTINGS ===

        graphics_label = QLabel("Graphics:")
        graphics_label.setStyleSheet(
            "color: #aaaaaa; font-size: 9pt; font-weight: bold;"
        )
        layout.addWidget(graphics_label)

        # Target FPS
        self.target_fps = ParameterSlider(
            name="Target FPS",
            initial_value=60.0,
            min_value=30.0,
            max_value=120.0,
            step=10.0,
            decimals=0,
            unit="fps",
            allow_range_edit=False,
        )
        self.target_fps.value_changed.connect(
            lambda v: self.parameter_changed.emit("target_fps", v)
        )
        layout.addWidget(self.target_fps)

        # Anti-aliasing quality
        self.aa_quality = ParameterSlider(
            name="Anti-Aliasing Quality",
            initial_value=2.0,
            min_value=0.0,
            max_value=4.0,
            step=1.0,
            decimals=0,
            unit="",
            allow_range_edit=False,
        )
        self.aa_quality.value_changed.connect(
            lambda v: self.parameter_changed.emit("aa_quality", v)
        )
        layout.addWidget(self.aa_quality)

        # Shadow quality
        self.shadow_quality = ParameterSlider(
            name="Shadow Quality",
            initial_value=2.0,
            min_value=0.0,
            max_value=4.0,
            step=1.0,
            decimals=0,
            unit="",
            allow_range_edit=False,
        )
        self.shadow_quality.value_changed.connect(
            lambda v: self.parameter_changed.emit("shadow_quality", v)
        )
        layout.addWidget(self.shadow_quality)

        layout.addStretch()

    def get_parameters(self) -> dict:
        """Get all parameters"""
        return {
            "spring_stiffness": self.spring_stiffness.value(),
            "damper_coeff": self.damper_coeff.value(),
            "dead_zone": self.dead_zone.value(),
            "target_fps": self.target_fps.value(),
            "aa_quality": self.aa_quality.value(),
            "shadow_quality": self.shadow_quality.value(),
        }


# Export
__all__ = [
    "GeometryPanelAccordion",
    "PneumoPanelAccordion",
    "SimulationPanelAccordion",
    "RoadPanelAccordion",
    "AdvancedPanelAccordion",
]
