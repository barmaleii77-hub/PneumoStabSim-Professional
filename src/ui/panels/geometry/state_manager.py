# -*- coding: utf-8 -*-
"""
Geometry panel state manager
Управление состоянием и валидация геометрии
"""

import logging
from typing import Dict, List, Optional, Any

from src.common.settings_manager import SettingsManager

from .defaults import (
    DEFAULT_GEOMETRY,
    MAX_ROD_TO_CYLINDER_RATIO,
    WARNING_ROD_TO_CYLINDER_RATIO,
    MIN_FRAME_CLEARANCE,
)


class GeometryStateManager:
    """Управление состоянием панели геометрии

    Responsibilities:
    - Store current geometry parameters
    - Validate parameter changes
    - Check dependencies between parameters
    - Save/load settings
    """

    def __init__(
        self,
        settings_manager: Optional[SettingsManager] = None,
        *,
        settings_path: str = "current.geometry",
    ):
        """Initialize state manager bound to the JSON-backed settings service.

        Args:
            settings_manager: Shared :class:`SettingsManager` instance. When
                omitted the state manager operates in-memory only.
            settings_path: Dotted path in :mod:`config/app_settings.json` where
                geometry preferences should be stored.
        """
        self.logger = logging.getLogger(__name__)
        self.settings_manager = settings_manager
        self._settings_path = settings_path
        self._allowed_keys = frozenset(DEFAULT_GEOMETRY.keys())
        self._legacy_metadata_path = "metadata.legacy"

        # Current state (mutable)
        self.state: Dict[str, Any] = DEFAULT_GEOMETRY.copy()
        self._rod_link_snapshot: Optional[tuple[float, float]] = None

        # Load saved state if available
        if self.settings_manager:
            self.load_state()

    # =========================================================================
    # STATE MANAGEMENT
    # =========================================================================

    def get_parameter(self, param_name: str) -> Any:
        """Get parameter value

        Args:
            param_name: Parameter name

        Returns:
            Parameter value (or None if not found)
        """
        return self.state.get(param_name)

    def _ensure_known_parameter(self, param_name: str) -> None:
        if param_name not in self._allowed_keys:
            raise KeyError(f"Unknown geometry parameter: {param_name}")

    def _partition_parameters(
        self, payload: Dict[str, Any]
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """Split payload into known geometry keys and legacy values."""

        known: Dict[str, Any] = {}
        legacy: Dict[str, Any] = {}

        for key, value in payload.items():
            if key in self._allowed_keys:
                known[key] = value
            else:
                legacy[key] = value

        if legacy:
            self.logger.warning(
                "Dropping unknown geometry parameters: %s",
                ", ".join(sorted(legacy)),
            )

        return known, legacy

    def _record_legacy_parameters(self, path: str, legacy: Dict[str, Any]) -> None:
        """Persist legacy parameters under the metadata."""

        if not legacy or not self.settings_manager:
            return

        meta_path = f"{self._legacy_metadata_path}.{path}"

        try:
            existing = self.settings_manager.get(meta_path, default={}) or {}
            merged = {**existing, **legacy}
            self.settings_manager.set(meta_path, merged, auto_save=False)
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("Failed to record legacy geometry parameters: %s", exc)

    def _apply_sanitised_payload(self, path: str, payload: Dict[str, Any]) -> None:
        if not self.settings_manager:
            return

        try:
            self.settings_manager.set(path, payload, auto_save=False)
        except Exception as exc:  # pragma: no cover - defensive
            self.logger.error("Failed to persist sanitised geometry payload: %s", exc)

    def set_parameter(self, param_name: str, value: Any) -> None:
        """Set parameter value

        Args:
            param_name: Parameter name
            value: New value
        """
        self._ensure_known_parameter(param_name)

        if param_name in {"rod_diameter_m", "rod_diameter_rear_m"}:
            self._apply_rod_diameter_update(param_name, value)
            return

        if param_name == "link_rod_diameters":
            self._update_link_state(bool(value))
            return

        self.state[param_name] = value

    def _apply_rod_diameter_update(self, param_name: str, value: Any) -> None:
        """Update rod diameters respecting the link option."""

        try:
            numeric = float(value)
        except (TypeError, ValueError):
            numeric = float(DEFAULT_GEOMETRY["rod_diameter_m"])

        self.state[param_name] = numeric

        if bool(self.state.get("link_rod_diameters")):
            other_key = (
                "rod_diameter_rear_m"
                if param_name == "rod_diameter_m"
                else "rod_diameter_m"
            )
            self.state[other_key] = numeric

    def _update_link_state(self, enabled: bool) -> None:
        """Handle toggling of the rod diameter link option."""

        self.state["link_rod_diameters"] = enabled

        if enabled:
            front = float(self.state.get("rod_diameter_m", 0.035))
            rear = float(self.state.get("rod_diameter_rear_m", front))
            self._rod_link_snapshot = (front, rear)
            self.state["rod_diameter_m"] = front
            self.state["rod_diameter_rear_m"] = front
        else:
            self._rod_link_snapshot = None

    def get_all_parameters(self) -> Dict[str, Any]:
        """Get all parameters

        Returns:
            Copy of current state dictionary
        """
        return self.state.copy()

    def update_parameters(self, params: Dict[str, Any]) -> None:
        """Update multiple parameters

        Args:
            params: Dictionary of parameter updates
        """
        unknown = sorted(set(params) - self._allowed_keys)
        if unknown:
            raise KeyError("Unknown geometry parameters: " + ", ".join(unknown))
        self.state.update(params)

    def reset_to_defaults(self) -> None:
        """Reset all parameters to default values"""
        self.state = DEFAULT_GEOMETRY.copy()
        self.logger.info("State reset to defaults")

    # =========================================================================
    # VALIDATION
    # =========================================================================

    def validate_geometry(self) -> List[str]:
        """Validate current geometry configuration

        Returns:
            List of error messages (empty if valid)
        """
        errors = []

        # Geometric constraints
        geo_errors = self._validate_geometric_constraints()
        errors.extend(geo_errors)

        # Hydraulic constraints
        hyd_errors = self._validate_hydraulic_constraints()
        errors.extend(hyd_errors)

        return errors

    def get_warnings(self) -> List[str]:
        """Get warnings (non-critical issues)

        Returns:
            List of warning messages
        """
        warnings = []

        # Hydraulic warnings
        hyd_warnings = self._get_hydraulic_warnings()
        warnings.extend(hyd_warnings)

        return warnings

    def _validate_geometric_constraints(self) -> List[str]:
        """Validate geometric constraints

        Returns:
            List of error messages
        """
        errors = []

        wheelbase = self.state.get("wheelbase", 3.2)
        lever_length = self.state.get("lever_length", 0.8)
        frame_to_pivot = self.state.get("frame_to_pivot", 0.6)

        # Check lever reach
        max_lever_reach = wheelbase / 2.0 - MIN_FRAME_CLEARANCE

        if frame_to_pivot + lever_length > max_lever_reach:
            errors.append(
                f"Геометрия рычага превышает доступное пространство: "
                f"{frame_to_pivot + lever_length:.2f} > {max_lever_reach:.2f}м"
            )

        return errors

    def _validate_hydraulic_constraints(self) -> List[str]:
        """Validate hydraulic constraints

        Returns:
            List of error messages
        """
        errors = []

        front_rod = self.state.get("rod_diameter_m", 0.035)
        rear_rod = self.state.get("rod_diameter_rear_m", front_rod)
        cyl_diam_m = self.state.get("cyl_diam_m", 0.080)

        # Critical: Rod too large
        for label, rod_value in (
            ("переднего", front_rod),
            ("заднего", rear_rod),
        ):
            if rod_value >= cyl_diam_m * MAX_ROD_TO_CYLINDER_RATIO:
                errors.append(
                    "Диаметр {} штока слишком велик: {:.1f}мм >= {}% от {:.1f}мм цилиндра".format(
                        label,
                        rod_value * 1000,
                        int(MAX_ROD_TO_CYLINDER_RATIO * 100),
                        cyl_diam_m * 1000,
                    )
                )

        return errors

    def _get_hydraulic_warnings(self) -> List[str]:
        """Get hydraulic warnings (non-critical)

        Returns:
            List of warning messages
        """
        warnings = []

        cyl_diam_m = self.state.get("cyl_diam_m", 0.080)

        # Warning: Rod close to limit
        for label, rod_value in (
            ("переднего", self.state.get("rod_diameter_m", 0.035)),
            ("заднего", self.state.get("rod_diameter_rear_m", 0.035)),
        ):
            if (
                rod_value >= cyl_diam_m * WARNING_ROD_TO_CYLINDER_RATIO
                and rod_value < cyl_diam_m * MAX_ROD_TO_CYLINDER_RATIO
            ):
                warnings.append(
                    "Диаметр {} штока близок к пределу: {:.1f}мм vs {:.1f}мм цилиндра".format(
                        label, rod_value * 1000, cyl_diam_m * 1000
                    )
                )

        return warnings

    # =========================================================================
    # DEPENDENCY CHECKING
    # =========================================================================

    def check_dependencies(
        self, param_name: str, new_value: Any, old_value: Any
    ) -> Optional[Dict[str, Any]]:
        """Check parameter dependencies

        Args:
            param_name: Changed parameter name
            new_value: New value
            old_value: Old value

        Returns:
            Conflict info dictionary (or None if no conflict)
        """
        # Check hydraulic constraints
        if param_name in [
            "rod_diameter_m",
            "rod_diameter_rear_m",
            "cyl_diam_m",
        ]:
            return self._check_hydraulic_dependency(param_name, new_value)

        # Check geometric constraints
        if param_name in ["lever_length", "frame_to_pivot", "wheelbase"]:
            return self._check_geometric_dependency(param_name, new_value)

        return None

    def _check_hydraulic_dependency(
        self, param_name: str, new_value: float
    ) -> Optional[Dict[str, Any]]:
        """Check hydraulic parameter dependencies

        Args:
            param_name: Changed parameter
            new_value: New value

        Returns:
            Conflict info or None
        """
        # Temporarily update state for checking
        temp_state = self.state.copy()
        temp_state[param_name] = new_value

        front_rod = temp_state.get("rod_diameter_m", 0.035)
        rear_rod = temp_state.get("rod_diameter_rear_m", front_rod)
        cyl_diam_m = temp_state.get("cyl_diam_m", 0.080)

        # Critical conflict
        for key, rod_value in (
            ("rod_diameter_m", front_rod),
            ("rod_diameter_rear_m", rear_rod),
        ):
            if rod_value >= cyl_diam_m * MAX_ROD_TO_CYLINDER_RATIO:
                return {
                    "type": "hydraulic_constraint",
                    "critical": True,
                    "message": (
                        "Диаметр {} штока слишком велик относительно цилиндра.\n"
                        "Шток: {:.1f}мм\nЦилиндр: {:.1f}мм".format(
                            "переднего" if key == "rod_diameter_m" else "заднего",
                            rod_value * 1000,
                            cyl_diam_m * 1000,
                        )
                    ),
                    "options": [
                        (
                            "Уменьшить диаметр штока",
                            key,
                            cyl_diam_m * WARNING_ROD_TO_CYLINDER_RATIO,
                        ),
                        (
                            "Увеличить диаметр цилиндра",
                            "cyl_diam_m",
                            rod_value / WARNING_ROD_TO_CYLINDER_RATIO,
                        ),
                    ],
                    "changed_param": param_name,
                }

        return None

    def _check_geometric_dependency(
        self, param_name: str, new_value: float
    ) -> Optional[Dict[str, Any]]:
        """Check geometric parameter dependencies

        Args:
            param_name: Changed parameter
            new_value: New value

        Returns:
            Conflict info or None
        """
        # Temporarily update state
        temp_state = self.state.copy()
        temp_state[param_name] = new_value

        wheelbase = temp_state.get("wheelbase", 3.2)
        lever_length = temp_state.get("lever_length", 0.8)
        frame_to_pivot = temp_state.get("frame_to_pivot", 0.6)

        max_lever_reach = wheelbase / 2.0 - MIN_FRAME_CLEARANCE

        if frame_to_pivot + lever_length > max_lever_reach:
            return {
                "type": "geometric_constraint",
                "critical": True,
                "message": (
                    f"Геометрия рычага превышает доступное пространство.\n"
                    f"Требуется: {frame_to_pivot + lever_length:.2f}м\n"
                    f"Доступно: {max_lever_reach:.2f}м"
                ),
                "options": [
                    (
                        "Уменьшить длину рычага",
                        "lever_length",
                        max_lever_reach - frame_to_pivot,
                    ),
                    (
                        "Уменьшить расстояние до оси",
                        "frame_to_pivot",
                        max_lever_reach - lever_length,
                    ),
                    (
                        "Увеличить колёсную базу",
                        "wheelbase",
                        (frame_to_pivot + lever_length + MIN_FRAME_CLEARANCE) * 2,
                    ),
                ],
                "changed_param": param_name,
            }

        return None

    # =========================================================================
    # PERSISTENCE
    # =========================================================================

    def save_state(self) -> None:
        """Persist the current state using :class:`SettingsManager`."""
        if not self.settings_manager:
            self.logger.warning("No SettingsManager instance - cannot save")
            return

        try:
            persistable = {
                key: self.state.get(key, DEFAULT_GEOMETRY[key])
                for key in self._allowed_keys
            }
            self.settings_manager.set(self._settings_path, persistable, auto_save=True)
            self.logger.info("State saved to settings manager")
        except Exception as exc:
            self.logger.error("Failed to save geometry state: %s", exc)

    def load_state(self) -> None:
        """Load state from the JSON settings file if available."""
        if not self.settings_manager:
            self.logger.warning("No SettingsManager instance - cannot load")
            return

        needs_save = False

        def _load_section(path: str) -> Dict[str, Any]:
            nonlocal needs_save
            try:
                payload = self.settings_manager.get(path, default={})
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.error("Failed to access geometry section %s: %s", path, exc)
                return {}

            if isinstance(payload, dict):
                known, legacy = self._partition_parameters(payload)
                if legacy:
                    self._record_legacy_parameters(path, legacy)
                    self._apply_sanitised_payload(path, known)
                    needs_save = True
                elif len(known) != len(payload):
                    self._apply_sanitised_payload(path, known)
                    needs_save = True
                return known

            if payload not in (None, {}):
                self.logger.warning(
                    "Ignoring malformed geometry payload at %s (type=%s)",
                    path,
                    type(payload).__name__,
                )
                self._apply_sanitised_payload(path, {})
                needs_save = True
            return {}

        restored = DEFAULT_GEOMETRY.copy()

        defaults_path = self._settings_path.replace("current.", "defaults_snapshot.", 1)
        defaults_payload = _load_section(defaults_path)
        if defaults_payload:
            restored.update(defaults_payload)

        current_payload = _load_section(self._settings_path)
        if current_payload:
            restored.update(current_payload)
        else:
            self.logger.info(
                "Geometry settings missing in %s; falling back to defaults snapshot",
                self._settings_path,
            )

        self.state = restored
        self.logger.info("State loaded from settings manager")

        if needs_save and self.settings_manager:
            try:
                self.settings_manager.save()
            except Exception as exc:  # pragma: no cover - defensive
                self.logger.error("Failed to save geometry settings cleanup: %s", exc)

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def get_3d_geometry_update(self) -> Dict[str, float]:
        """Get geometry update for 3D scene.

        Returns:
            Dictionary with 3D geometry parameters expressed in meters.
        """

        def _value(name: str, default: float) -> float:
            try:
                return float(self.state.get(name, default))
            except (TypeError, ValueError):
                return float(default)

        frame_length = _value("wheelbase", 3.2)
        frame_height = _value("frame_height_m", 0.65)
        frame_beam_size = _value("frame_beam_size_m", 0.12)
        lever_length = _value("lever_length", 0.8)
        cylinder_body_length = _value("cylinder_length", 0.5)
        tail_rod_length = _value("tail_rod_length_m", 0.1)
        track_width = _value("track", 1.6)
        frame_to_pivot = _value("frame_to_pivot", 0.6)
        rod_position = _value("rod_position", 0.6)
        cyl_diameter = _value("cyl_diam_m", 0.080)
        stroke = _value("stroke_m", 0.300)
        dead_gap = _value("dead_gap_m", 0.005)
        rod_diameter_front = _value("rod_diameter_m", 0.035)
        rod_diameter_rear = _value("rod_diameter_rear_m", rod_diameter_front)
        piston_rod_length = _value("piston_rod_length_m", 0.200)
        piston_thickness = _value("piston_thickness_m", 0.025)

        payload = {
            # Основные размеры (м)
            "frameLength": frame_length,
            "frameHeight": frame_height,
            "frameBeamSize": frame_beam_size,
            "leverLength": lever_length,
            "cylinderBodyLength": cylinder_body_length,
            "tailRodLength": tail_rod_length,
            # Дополнительные параметры (м)
            "trackWidth": track_width,
            "frameToPivot": frame_to_pivot,
            "rodPosition": rod_position,
            # Параметры цилиндра и штока (м)
            "cylDiamM": cyl_diameter,
            "strokeM": stroke,
            "deadGapM": dead_gap,
            "rodDiameterFrontM": rod_diameter_front,
            "rodDiameterRearM": rod_diameter_rear,
            "pistonRodLengthM": piston_rod_length,
            "pistonThicknessM": piston_thickness,
            # Дублирующие ключи для обратной совместимости
            "boreHead": cyl_diameter,
            "rodDiameter": rod_diameter_front,
            "pistonRodLength": piston_rod_length,
            "pistonThickness": piston_thickness,
        }

        # Дополнительные значения в миллиметрах для устаревших потребителей
        mm_payload = {
            "frame_length_mm": frame_length * 1000.0,
            "frame_height_mm": frame_height * 1000.0,
            "frame_beam_size_mm": frame_beam_size * 1000.0,
            "lever_length_mm": lever_length * 1000.0,
            "cylinder_body_length_mm": cylinder_body_length * 1000.0,
            "tail_rod_length_mm": tail_rod_length * 1000.0,
            "track_width_mm": track_width * 1000.0,
            "frame_to_pivot_mm": frame_to_pivot * 1000.0,
            "cyl_diam_mm": cyl_diameter * 1000.0,
            "stroke_mm": stroke * 1000.0,
            "dead_gap_mm": dead_gap * 1000.0,
            "rod_diameter_front_mm": rod_diameter_front * 1000.0,
            "rod_diameter_rear_mm": rod_diameter_rear * 1000.0,
            "rod_diameter_mm": rod_diameter_front * 1000.0,
            "piston_rod_length_mm": piston_rod_length * 1000.0,
            "piston_thickness_mm": piston_thickness * 1000.0,
        }

        payload["rodDiameterM"] = rod_diameter_front
        payload["rodDiameterRear"] = rod_diameter_rear
        payload["rodDiameterFront"] = rod_diameter_front

        payload.update(mm_payload)
        return payload
