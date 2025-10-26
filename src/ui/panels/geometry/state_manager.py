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

        # Current state (mutable)
        self.state: Dict[str, Any] = DEFAULT_GEOMETRY.copy()

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

    def set_parameter(self, param_name: str, value: Any) -> None:
        """Set parameter value

        Args:
            param_name: Parameter name
            value: New value
        """
        self.state[param_name] = value

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

        rod_diameter_m = self.state.get("rod_diameter_m", 0.035)
        cyl_diam_m = self.state.get("cyl_diam_m", 0.080)

        # Critical: Rod too large
        if rod_diameter_m >= cyl_diam_m * MAX_ROD_TO_CYLINDER_RATIO:
            errors.append(
                f"Диаметр штока слишком велик: "
                f"{rod_diameter_m * 1000:.1f}мм >= {MAX_ROD_TO_CYLINDER_RATIO * 100:.0f}% "
                f"от {cyl_diam_m * 1000:.1f}мм цилиндра"
            )

        return errors

    def _get_hydraulic_warnings(self) -> List[str]:
        """Get hydraulic warnings (non-critical)

        Returns:
            List of warning messages
        """
        warnings = []

        rod_diameter_m = self.state.get("rod_diameter_m", 0.035)
        cyl_diam_m = self.state.get("cyl_diam_m", 0.080)

        # Warning: Rod close to limit
        if (
            rod_diameter_m >= cyl_diam_m * WARNING_ROD_TO_CYLINDER_RATIO
            and rod_diameter_m < cyl_diam_m * MAX_ROD_TO_CYLINDER_RATIO
        ):
            warnings.append(
                f"Диаметр штока близок к пределу: "
                f"{rod_diameter_m * 1000:.1f}мм vs {cyl_diam_m * 1000:.1f}мм цилиндра"
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
        if param_name in ["rod_diameter_m", "cyl_diam_m"]:
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

        rod_diameter_m = temp_state.get("rod_diameter_m", 0.035)
        cyl_diam_m = temp_state.get("cyl_diam_m", 0.080)

        # Critical conflict
        if rod_diameter_m >= cyl_diam_m * MAX_ROD_TO_CYLINDER_RATIO:
            return {
                "type": "hydraulic_constraint",
                "critical": True,
                "message": (
                    f"Диаметр штока слишком велик относительно цилиндра.\n"
                    f"Шток: {rod_diameter_m * 1000:.1f}мм\n"
                    f"Цилиндр: {cyl_diam_m * 1000:.1f}мм"
                ),
                "options": [
                    (
                        "Уменьшить диаметр штока",
                        "rod_diameter_m",
                        cyl_diam_m * WARNING_ROD_TO_CYLINDER_RATIO,
                    ),
                    (
                        "Увеличить диаметр цилиндра",
                        "cyl_diam_m",
                        rod_diameter_m / WARNING_ROD_TO_CYLINDER_RATIO,
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
            self.settings_manager.set(self._settings_path, self.state, auto_save=True)
            self.logger.info("State saved to settings manager")
        except Exception as exc:
            self.logger.error("Failed to save geometry state: %s", exc)

    def load_state(self) -> None:
        """Load state from the JSON settings file if available."""
        if not self.settings_manager:
            self.logger.warning("No SettingsManager instance - cannot load")
            return

        try:
            stored = self.settings_manager.get(self._settings_path, default=None)
        except Exception as exc:
            self.logger.error("Failed to load geometry state: %s", exc)
            return

        if not isinstance(stored, dict):
            self.logger.info("No persisted geometry state found; using defaults")
            return

        restored = DEFAULT_GEOMETRY.copy()
        restored.update(stored)
        self.state = restored
        self.logger.info("State loaded from settings manager")

    # =========================================================================
    # HELPER METHODS
    # =========================================================================

    def get_3d_geometry_update(self) -> Dict[str, float]:
        """Get geometry update for 3D scene

        Returns:
            Dictionary with 3D geometry parameters (in mm)
        """
        return {
            # Основные размеры (м → мм)
            "frameLength": self.state.get("wheelbase", 3.2) * 1000,
            "frameHeight": 650.0,  # Fixed
            "frameBeamSize": 120.0,  # Fixed
            "leverLength": self.state.get("lever_length", 0.8) * 1000,
            "cylinderBodyLength": self.state.get("cylinder_length", 0.5) * 1000,
            "tailRodLength": 100.0,  # Fixed
            # Дополнительные параметры (м → мм)
            "trackWidth": self.state.get("track", 1.6) * 1000,
            "frameToPivot": self.state.get("frame_to_pivot", 0.6) * 1000,
            "rodPosition": self.state.get("rod_position", 0.6),
            # Параметры цилиндра и штока (м → мм)
            "cylDiamM": self.state.get("cyl_diam_m", 0.080) * 1000,
            "strokeM": self.state.get("stroke_m", 0.300) * 1000,
            "deadGapM": self.state.get("dead_gap_m", 0.005) * 1000,
            "rodDiameterM": self.state.get("rod_diameter_m", 0.035) * 1000,
            "pistonRodLengthM": self.state.get("piston_rod_length_m", 0.200) * 1000,
            "pistonThicknessM": self.state.get("piston_thickness_m", 0.025) * 1000,
            # Дублирующие ключи для обратной совместимости
            "boreHead": self.state.get("cyl_diam_m", 0.080) * 1000,
            "rodDiameter": self.state.get("rod_diameter_m", 0.035) * 1000,
            "pistonRodLength": self.state.get("piston_rod_length_m", 0.200) * 1000,
            "pistonThickness": self.state.get("piston_thickness_m", 0.025) * 1000,
        }
