"""Geometry-to-3D bridge module.

This module converts 2D suspension geometry to 3D visualization coordinates and
is integrated with the Qt user interface layer. All dimensions are handled in
SI units (meters and radians).
"""

from __future__ import annotations

import logging
import math
from typing import Any, Optional
from collections.abc import Mapping

import numpy as np
from PySide6.QtCore import QObject, Property, Signal
from PySide6.QtGui import QVector3D

from config.constants import (
    get_geometry_cylinder_constants,
    get_geometry_initial_state_constants,
    get_geometry_visual_constants,
)
from ..common.settings_manager import get_settings_manager
from ..core.geometry import GeometryParams


class GeometryTo3DConverter(QObject):
    """Converts2D geometry parameters to3D visualization coordinates
    WITH USER INTERFACE INTEGRATION"""

    # Signals for parameter changes
    geometryChanged = Signal()
    frameChanged = Signal()

    def __init__(
        self,
        geometry: GeometryParams,
        *,
        settings_manager: Any | None = None,
    ) -> None:
        """Initialize geometry bridge converter."""
        super().__init__()
        self.geometry = geometry
        self._settings_manager = settings_manager or get_settings_manager()
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._visual_constants: dict[str, Any] = {}

        defaults = self._load_geometry_defaults()

        try:
            initial_state = get_geometry_initial_state_constants()
        except KeyError:
            initial_state = {}

        try:
            cylinder_constants = get_geometry_cylinder_constants()
        except KeyError:
            cylinder_constants = {}

        try:
            visual_raw: Mapping[str, Any] = get_geometry_visual_constants()
        except KeyError:
            self._logger.warning(
                "Секция constants.geometry.visualization отсутствует; будут использованы резервные значения."
            )
            visual_raw = {}
        self._visual_constants = dict(visual_raw)

        def _default(key: str, fallback: float) -> float:
            value = defaults.get(key, fallback)
            try:
                return float(value)
            except (TypeError, ValueError):
                return float(fallback)

        # VISUALIZATION PARAMETERS (from constants)
        self._pivot_offset_x = self._visual_value("pivot_offset_x_m")
        self._tail_offset_x = self._visual_value("tail_offset_x_m")
        self._piston_clip_min = self._visual_value("piston_clip_min_fraction")
        self._piston_clip_max = self._visual_value("piston_clip_max_fraction")
        self._max_stroke_fraction = self._visual_value("max_stroke_fraction")

        # USER-CONTROLLABLE PARAMETERS (connected to UI)
        # Fallbacks from constants
        fallback_frame_beam_size = float(initial_state.get("frame_beam_size_m", 0.12))
        fallback_frame_height = float(initial_state.get("frame_height_m", 0.65))
        fallback_frame_length = float(initial_state.get("frame_length_m", 3.4))
        fallback_lever_length = float(initial_state.get("lever_length_m", 0.75))
        fallback_cylinder_body_length = float(
            cylinder_constants.get("body_length_m", 0.46)
        )
        fallback_tail_rod_length = float(initial_state.get("tail_rod_length_m", 0.18))

        # Visualization constants
        self._frame_beam_size = _default("frame_beam_size_m", fallback_frame_beam_size)
        self._frame_height = _default("frame_height_m", fallback_frame_height)
        self._frame_length = _default("frame_length_m", fallback_frame_length)
        self._lever_length = _default("lever_length_m", fallback_lever_length)
        self._cylinder_body_length = _default(
            "cylinder_body_length_m", fallback_cylinder_body_length
        )
        self._tail_rod_length = _default("tail_rod_length_m", fallback_tail_rod_length)

        # Z coordinates for front/rear
        self._front_z = -self._frame_length / 2.0
        self._rear_z = self._frame_length / 2.0

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _load_geometry_defaults(self) -> dict[str, Any]:
        """Load geometry defaults from :class:`SettingsManager`."""
        if self._settings_manager is None:
            return {}
        try:
            return self._settings_manager.get_category("geometry")
        except Exception:
            return {}

    def _visual_value(self, key: str) -> float:
        fallback = _VISUAL_DEFAULTS.get(key, 0.0)
        raw = self._visual_constants.get(key)
        if raw is None:
            self._logger.warning(
                "Параметр визуализации '%s' отсутствует; используется %.3f",
                key,
                fallback,
            )
            return fallback
        try:
            return float(raw)
        except (TypeError, ValueError):
            self._logger.warning(
                "Параметр визуализации '%s' имеет некорректное значение (%r); используется %.3f",
                key,
                raw,
                fallback,
            )
            return fallback

    # USER-CONTROLLABLE PROPERTIES (connected to UI sliders/spinboxes)

    @Property(float, notify=frameChanged)
    def frameLength(self) -> float:
        return self._frame_length

    @frameLength.setter
    def frameLength(self, value: float) -> None:
        if self._frame_length != value:
            self._frame_length = value
            self._front_z = -value / 2.0
            self._rear_z = value / 2.0
            self.frameChanged.emit()
            self.geometryChanged.emit()

    @Property(float, notify=frameChanged)
    def frameHeight(self) -> float:
        return self._frame_height

    @frameHeight.setter
    def frameHeight(self, value: float) -> None:
        if self._frame_height != value:
            self._frame_height = value
            self.frameChanged.emit()
            self.geometryChanged.emit()

    @Property(float, notify=frameChanged)
    def frameBeamSize(self) -> float:
        return self._frame_beam_size

    @frameBeamSize.setter
    def frameBeamSize(self, value: float) -> None:
        if self._frame_beam_size != value:
            self._frame_beam_size = value
            self.frameChanged.emit()
            self.geometryChanged.emit()

    @Property(float, notify=geometryChanged)
    def leverLength(self) -> float:
        return self._lever_length

    @leverLength.setter
    def leverLength(self, value: float) -> None:
        if self._lever_length != value:
            self._lever_length = value
            self.geometryChanged.emit()

    @Property(float, notify=geometryChanged)
    def cylinderBodyLength(self) -> float:
        return self._cylinder_body_length

    @cylinderBodyLength.setter
    def cylinderBodyLength(self, value: float) -> None:
        if self._cylinder_body_length != value:
            self._cylinder_body_length = value
            self.geometryChanged.emit()

    @Property(float, notify=geometryChanged)
    def tailRodLength(self) -> float:
        return self._tail_rod_length

    @tailRodLength.setter
    def tailRodLength(self, value: float) -> None:
        if self._tail_rod_length != value:
            self._tail_rod_length = value
            self.geometryChanged.emit()

    def get_frame_params(self) -> dict[str, float]:
        """Get frame parameters for3D visualization in meters."""
        return {
            "beamSize": self._frame_beam_size,
            "frameHeight": self._frame_height,
            "frameLength": self._frame_length,
            "beamSizeM": self._frame_beam_size,
            "frameHeightM": self._frame_height,
            "frameLengthM": self._frame_length,
        }

    def convert_to_3d(
        self,
        corner: str,
        lever_angle_rad: float,
        cylinder_state: Any | None = None,
    ) -> dict[str, Any]:
        """Convert2D kinematics to3D coordinates for one corner."""
        # Determine side and position
        is_left = corner.endswith("l")
        is_front = corner.startswith("f")

        side_mult = -1.0 if is_left else 1.0
        z_plane = self._front_z if is_front else self._rear_z

        # Fixed frame joints
        pivot_offset_x = self._pivot_offset_x
        pivot_height = self._frame_beam_size / 2.0

        j_arm = QVector3D(pivot_offset_x * side_mult, pivot_height, z_plane)

        horn_height = self._frame_beam_size + self._frame_height
        tail_height = horn_height - self._frame_beam_size / 2.0
        tail_offset_x = self._tail_offset_x

        j_tail = QVector3D(tail_offset_x * side_mult, tail_height, z_plane)

        # Moving parts
        base_angle_rad = math.pi if is_left else 0.0
        total_angle_rad = base_angle_rad + lever_angle_rad
        total_angle_deg = float(np.rad2deg(total_angle_rad))

        rod_attach_x = j_arm.x() + self._lever_length * math.cos(total_angle_rad)
        rod_attach_y = j_arm.y() + self._lever_length * math.sin(total_angle_rad)
        j_rod = QVector3D(rod_attach_x, rod_attach_y, z_plane)

        # Piston position by geometry
        tail_to_rod_dist = float(
            np.sqrt((rod_attach_x - j_tail.x()) ** 2 + (rod_attach_y - j_tail.y()) ** 2)
        )

        base_rod_x = j_arm.x() + self._lever_length * math.cos(base_angle_rad)
        base_rod_y = j_arm.y() + self._lever_length * math.sin(base_angle_rad)
        base_dist = float(
            np.sqrt((base_rod_x - j_tail.x()) ** 2 + (base_rod_y - j_tail.y()) ** 2)
        )

        delta_dist = tail_to_rod_dist - base_dist
        piston_position = (self._cylinder_body_length / 2.0) + delta_dist
        piston_position = float(
            np.clip(
                piston_position,
                self._cylinder_body_length * self._piston_clip_min,
                self._cylinder_body_length * self._piston_clip_max,
            )
        )
        piston_ratio = float(piston_position / self._cylinder_body_length)

        # Override from physics if provided
        if cylinder_state is not None:
            stroke_m = cylinder_state.stroke
            max_stroke = self._cylinder_body_length * self._max_stroke_fraction
            piston_ratio_physics = 0.5 + (stroke_m / (2 * max_stroke))
            piston_ratio_physics = float(
                np.clip(
                    piston_ratio_physics,
                    self._piston_clip_min,
                    self._piston_clip_max,
                )
            )
            piston_position_physics = piston_ratio_physics * self._cylinder_body_length
            piston_position = float(piston_position_physics)
            piston_ratio = float(piston_ratio_physics)

        result = {
            "j_arm": j_arm,
            "j_tail": j_tail,
            "j_rod": j_rod,
            "leverAngle": float(np.rad2deg(lever_angle_rad)),
            "leverAngleRad": float(lever_angle_rad),
            "totalAngleRad": float(total_angle_rad),
            "leverLength": float(self._lever_length),
            "cylinderBodyLength": float(self._cylinder_body_length),
            "tailRodLength": float(self._tail_rod_length),
            "pistonPosition": float(piston_position),
            "pistonRatio": float(piston_ratio),
            "corner": corner,
            "totalAngle": float(total_angle_deg),
            "baseAngle": float(180.0 if is_left else 0.0),
            "side": "left" if is_left else "right",
            "position": "front" if is_front else "rear",
        }

        if cylinder_state is not None:
            result["cylinderPhysics"] = {
                "stroke": cylinder_state.stroke,
                "strokeVelocity": getattr(cylinder_state, "stroke_velocity", 0.0),
                "volumeHead": getattr(cylinder_state, "volume_head", 0.0),
                "volumeRod": getattr(cylinder_state, "volume_rod", 0.0),
                "distance": getattr(cylinder_state, "distance", 0.0),
                "axisAngle": getattr(cylinder_state, "cylinder_axis_angle", 0.0),
            }

        return result

    def get_all_corners_3d(
        self,
        lever_angles: dict[str, float] | None = None,
        cylinder_states: dict[str, Any] | None = None,
    ) -> dict[str, dict[str, Any]]:
        if lever_angles is None:
            lever_angles = {"fl": 0.0, "fr": 0.0, "rl": 0.0, "rr": 0.0}
        if cylinder_states is None:
            cylinder_states = {}
        corners: dict[str, dict[str, Any]] = {}
        for corner in ["fl", "fr", "rl", "rr"]:
            angle = lever_angles.get(corner, 0.0)
            cyl_state = cylinder_states.get(corner)
            corners[corner] = self.convert_to_3d(corner, angle, cyl_state)
        return corners

    # Backwards compatibility alias -------------------------------------------------

    def get_corner_3d_coords(
        self,
        corner: str,
        lever_angle_rad: float,
        cylinder_state: Any | None = None,
    ) -> dict[str, Any]:
        """Alias maintained for legacy callers expecting the old API name."""

        return self.convert_to_3d(corner, lever_angle_rad, cylinder_state)

    def update_from_simulation(self, sim_state: dict[str, Any]) -> dict[str, Any]:
        lever_angles = sim_state.get("lever_angles", {})
        if not lever_angles:
            lever_angles = {
                "fl": sim_state.get("fl_angle", 0.0),
                "fr": sim_state.get("fr_angle", 0.0),
                "rl": sim_state.get("rl_angle", 0.0),
                "rr": sim_state.get("rr_angle", 0.0),
            }
        for key, value in list(lever_angles.items()):
            if isinstance(value, (int, float)) and abs(value) > math.tau:
                lever_angles[key] = math.radians(value)

        cylinder_states = sim_state.get("cylinder_states", {})
        if not cylinder_states and "corners" in sim_state:
            for corner, data in sim_state.get("corners", {}).items():
                if "cylinder_state" in data:
                    cylinder_states[corner] = data["cylinder_state"]

        return {
            "frame": self.get_frame_params(),
            "corners": self.get_all_corners_3d(lever_angles, cylinder_states),
            "userParams": {
                "frameLength": self._frame_length,
                "frameHeight": self._frame_height,
                "frameBeamSize": self._frame_beam_size,
                "leverLength": self._lever_length,
                "cylinderBodyLength": self._cylinder_body_length,
                "tailRodLength": self._tail_rod_length,
            },
        }

    def update_user_parameters(
        self, params: dict[str, float], persist: bool = False
    ) -> None:
        if "frameLength" in params and params["frameLength"] != self._frame_length:
            self.frameLength = params["frameLength"]
        if "frameHeight" in params and params["frameHeight"] != self._frame_height:
            self.frameHeight = params["frameHeight"]
        if (
            "frameBeamSize" in params
            and params["frameBeamSize"] != self._frame_beam_size
        ):
            self.frameBeamSize = params["frameBeamSize"]
        if "leverLength" in params and params["leverLength"] != self._lever_length:
            self.leverLength = params["leverLength"]
        if (
            "cylinderBodyLength" in params
            and params["cylinderBodyLength"] != self._cylinder_body_length
        ):
            self.cylinderBodyLength = params["cylinderBodyLength"]
        if (
            "tailRodLength" in params
            and params["tailRodLength"] != self._tail_rod_length
        ):
            self.tailRodLength = params["tailRodLength"]
        if persist:
            self.save_to_settings()

    def save_to_settings(self) -> None:
        if self._settings_manager is None:
            return
        manager = self._settings_manager
        manager.set("geometry.frame_length_m", self._frame_length, auto_save=False)
        manager.set("geometry.frame_height_m", self._frame_height, auto_save=False)
        manager.set(
            "geometry.frame_beam_size_m", self._frame_beam_size, auto_save=False
        )
        manager.set("geometry.lever_length_m", self._lever_length, auto_save=False)
        manager.set(
            "geometry.cylinder_body_length_m",
            self._cylinder_body_length,
            auto_save=False,
        )
        manager.set(
            "geometry.tail_rod_length_m", self._tail_rod_length, auto_save=False
        )
        manager.save()

    def export_geometry_params(self) -> dict[str, Any]:
        return {
            "frameLength": self._frame_length,
            "frameHeight": self._frame_height,
            "frameBeamSize": self._frame_beam_size,
            "leverLength": self._lever_length,
            "cylinderBodyLength": self._cylinder_body_length,
            "tailRodLength": self._tail_rod_length,
        }


def create_geometry_converter(
    *,
    geometry: GeometryParams | None = None,
    settings_manager: Any | None = None,
    wheelbase: float | None = None,
    lever_length: float | None = None,
    cylinder_diameter: float | None = None,
) -> GeometryTo3DConverter:
    """Return a ready-to-use :class:`GeometryTo3DConverter` instance."""

    params = geometry or GeometryParams()

    if lever_length is not None:
        try:
            params.lever_length = float(lever_length)
        except Exception:
            pass

    if wheelbase is not None:
        if hasattr(params, "wheelbase"):
            try:
                params.wheelbase = float(wheelbase)
            except Exception:
                pass
        elif hasattr(params, "track_width"):
            try:
                params.track_width = float(wheelbase)
            except Exception:
                pass

    if cylinder_diameter is not None and hasattr(params, "cylinder_inner_diameter"):
        try:
            params.cylinder_inner_diameter = float(cylinder_diameter)
        except Exception:
            pass

    manager = settings_manager or get_settings_manager()
    return GeometryTo3DConverter(params, settings_manager=manager)


_VISUAL_DEFAULTS = {
    "pivot_offset_x_m": 0.0,
    "tail_offset_x_m": 0.0,
    "piston_clip_min_fraction": 0.05,
    "piston_clip_max_fraction": 0.95,
    "max_stroke_fraction": 0.9,
}
