# -*- coding: utf-8 -*-
"""Geometry-to-3D bridge module.

This module converts 2D suspension geometry to 3D visualization coordinates and
is integrated with the Qt user interface layer. All dimensions are handled in
SI units (meters and radians).
"""

from __future__ import annotations

import math
from typing import Any, Dict, Optional

import numpy as np
from PySide6.QtCore import QObject, Property, Signal
from PySide6.QtGui import QVector3D

from ..common.settings_manager import get_settings_manager
from ..core.geometry import GeometryParams


class GeometryTo3DConverter(QObject):
    """Converts 2D geometry parameters to 3D visualization coordinates
    WITH USER INTERFACE INTEGRATION"""

    # Signals for parameter changes
    geometryChanged = Signal()
    frameChanged = Signal()

    def __init__(
        self,
        geometry: GeometryParams,
        *,
        settings_manager: Optional[Any] = None,
    ):
        """Initialize geometry bridge converter."""
        super().__init__()
        self.geometry = geometry
        self._settings_manager = settings_manager or get_settings_manager()

        defaults = self._load_geometry_defaults()

        def _default(key: str, fallback: float) -> float:
            value = defaults.get(key, fallback)
            try:
                return float(value)
            except (TypeError, ValueError):
                return float(fallback)

        # USER-CONTROLLABLE PARAMETERS (will be connected to UI)
        self._frame_beam_size = _default("frame_beam_size_m", 0.12)
        self._frame_height = _default("frame_height_m", 0.65)
        self._frame_length = _default("frame_length_m", 2.0)
        self._lever_length = _default("lever_length_m", 0.315)
        self._cylinder_body_length = _default("cylinder_body_length_m", 0.25)
        self._tail_rod_length = _default("tail_rod_length_m", 0.1)

        # Z-coordinates for front/rear - calculated from frame length
        self._front_z = -self._frame_length / 2.0  # Front at -frame_length/2
        self._rear_z = self._frame_length / 2.0  # Rear at +frame_length/2

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _load_geometry_defaults(self) -> Dict[str, Any]:
        """Load geometry defaults from :class:`SettingsManager`."""

        if self._settings_manager is None:
            return {}

        try:
            return self._settings_manager.get_category("geometry")
        except Exception:
            # If the category is missing we keep the built-in fallbacks
            return {}

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

    def get_frame_params(self) -> Dict[str, float]:
        """Get frame parameters for 3D visualization in meters."""
        return {
            "beamSize": self._frame_beam_size,
            "frameHeight": self._frame_height,
            "frameLength": self._frame_length,
            "beamSizeM": self._frame_beam_size,
            "frameHeightM": self._frame_height,
            "frameLengthM": self._frame_length,
        }

    def get_corner_3d_coords(
        self,
        corner: str,
        lever_angle_rad: float = 0.0,
        cylinder_state: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Convert 2D kinematics to 3D coordinates for one corner
        USING CORRECTED SUSPENSION MECHANICS FROM test_2m_suspension.py

        Args:
            corner: 'fl', 'fr', 'rl', 'rr'
            lever_angle_rad: Current lever angle in radians
            cylinder_state: Optional CylinderState from physics simulation

        Returns:
            Dictionary with 3D coordinates for QML (compatible with CorrectedSuspensionCorner)
        """
        # Determine side and position
        is_left = corner.endswith("l")  # fl, rl = left side
        is_front = corner.startswith("f")  # fl, fr = front

        # Side multiplier for mirroring
        side_mult = -1.0 if is_left else 1.0

        # Z position (longitudinal)
        z_plane = self._front_z if is_front else self._rear_z

        # FIXED FRAME ATTACHMENT POINTS (never change)

        # Lever pivot (j_arm) - FIXED attachment to frame
        pivot_offset_x = 0.15  # m from center
        pivot_height = self._frame_beam_size / 2.0  # ON BEAM AXIS

        j_arm = QVector3D(
            pivot_offset_x * side_mult,  # ±150mm from center
            pivot_height,  # beam axis height
            z_plane,  # EXACTLY in plane
        )

        # Cylinder tail (j_tail) - FIXED attachment to frame
        horn_height = self._frame_beam_size + self._frame_height  # total horn height
        tail_height = horn_height - self._frame_beam_size / 2  # horn top minus offset
        tail_offset_x = 0.1  # m from center

        j_tail = QVector3D(
            tail_offset_x * side_mult,  # ±100mm from center
            tail_height,  # horn height
            z_plane,  # EXACTLY in plane
        )

        # MOVING PARTS (depend on lever angle)

        # Base angle: LEFT side points LEFT (180°), RIGHT side points RIGHT (0°)
        base_angle_deg = 180.0 if is_left else 0.0
        base_angle_rad = math.pi if is_left else 0.0
        total_angle_rad = base_angle_rad + lever_angle_rad
        total_angle_deg = float(np.rad2deg(total_angle_rad))

        # Rod attachment point on lever (at lever end)
        rod_attach_x = j_arm.x() + self._lever_length * math.cos(total_angle_rad)
        rod_attach_y = j_arm.y() + self._lever_length * math.sin(total_angle_rad)

        j_rod = QVector3D(rod_attach_x, rod_attach_y, z_plane)

        # PISTON POSITION CALCULATION
        # Calculate from GEOMETRY (correct kinematics!)
        # Distance from tail to rod attachment point
        tail_to_rod_dist = np.sqrt(
            (j_rod.x() - j_tail.x()) ** 2 + (j_rod.y() - j_tail.y()) ** 2
        )

        # Total assembly: tail_rod + cylinder_body + piston_rod
        # tail_rod = FIXED 100mm
        # cylinder_body = FIXED 250mm
        # piston_rod = VARIABLE (depends on lever angle!)

        # Calculate baseline distance (lever horizontal)
        base_angle_rad = math.pi if is_left else 0.0
        base_rod_x = j_arm.x() + self._lever_length * math.cos(base_angle_rad)
        base_rod_y = j_arm.y() + self._lever_length * math.sin(base_angle_rad)
        base_dist = np.sqrt(
            (base_rod_x - j_tail.x()) ** 2 + (base_rod_y - j_tail.y()) ** 2
        )

        # Change in distance from baseline
        delta_dist = tail_to_rod_dist - base_dist

        # Piston position inside cylinder:
        # When lever is horizontal (baseline), piston is centered
        # When lever rotates, distance changes ? piston moves
        # Piston moves IN SAME DIRECTION as rod extension
        # (if rod extends/distance increases, piston moves toward rod end/increases)
        # CORRECTED: Use PLUS (not minus) because piston follows rod extension
        piston_position = (self._cylinder_body_length / 2.0) + delta_dist

        # Clip to safe range (10% to 90% of cylinder length)
        piston_position = float(
            np.clip(
                piston_position,
                self._cylinder_body_length
                * 0.1,  # 10% minimum (25mm for 250mm cylinder)
                self._cylinder_body_length
                * 0.9,  # 90% maximum (225mm for 250mm cylinder)
            )
        )

        # Calculate ratio for QML
        piston_ratio = float(piston_position / self._cylinder_body_length)

        # If cylinder_state provided, OVERRIDE with physics data
        if cylinder_state is not None:
            # Use actual physics data from CylinderKinematics
            # Calculate piston position from stroke
            # Assuming stroke 0 = center of cylinder
            stroke_m = cylinder_state.stroke
            max_stroke = self._cylinder_body_length * 0.4  # ±40% stroke range
            piston_ratio_physics = 0.5 + (stroke_m / (2 * max_stroke))
            piston_ratio_physics = float(np.clip(piston_ratio_physics, 0.1, 0.9))
            piston_position_physics = (
                piston_ratio_physics * self._cylinder_body_length
            )

            # Use physics values
            piston_position = float(piston_position_physics)
            piston_ratio = float(piston_ratio_physics)

        # Return data compatible with CorrectedSuspensionCorner.qml
        result = {
            # FIXED joints
            "j_arm": j_arm,  # Lever pivot (orange joint)
            "j_tail": j_tail,  # Cylinder mount (blue joint)
            "j_rod": j_rod,  # Rod attachment (green joint)
            # Animation
            "leverAngle": float(np.rad2deg(lever_angle_rad)),
            "leverAngleRad": float(lever_angle_rad),
            "totalAngleRad": float(total_angle_rad),
            # Dimensions (for QML calculations)
            "leverLength": float(self._lever_length),
            "cylinderBodyLength": float(self._cylinder_body_length),
            "tailRodLength": float(self._tail_rod_length),
            # PISTON POSITION (ALWAYS float, never None or empty!)
            "pistonPosition": float(
                piston_position
            ),  # Absolute position in cylinder (m)
            "pistonRatio": float(piston_ratio),  # Ratio 0..1 inside cylinder
            # Additional data for UI
            "corner": corner,
            "totalAngle": float(total_angle_deg),
            "baseAngle": float(base_angle_deg),
            "side": "left" if is_left else "right",
            "position": "front" if is_front else "rear",
        }

        # If cylinder_state provided, add full physics data
        if cylinder_state is not None:
            result["cylinderPhysics"] = {
                "stroke": cylinder_state.stroke,
                "strokeVelocity": cylinder_state.stroke_velocity,
                "volumeHead": cylinder_state.volume_head,
                "volumeRod": cylinder_state.volume_rod,
                "distance": cylinder_state.distance,
                "axisAngle": cylinder_state.cylinder_axis_angle,
            }

        return result

    def get_all_corners_3d(
        self,
        lever_angles: Optional[Dict[str, float]] = None,
        cylinder_states: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Get 3D coordinates for all 4 corners

        Args:
            lever_angles: Optional dict with current lever angles {'fl': rad, 'fr': rad, 'rl': rad, 'rr': rad}
            cylinder_states: Optional dict with CylinderState objects for each corner

        Returns:
            Dictionary with all corner coordinates
        """
        if lever_angles is None:
            lever_angles = {"fl": 0.0, "fr": 0.0, "rl": 0.0, "rr": 0.0}

        if cylinder_states is None:
            cylinder_states = {}

        corners = {}
        for corner in ["fl", "fr", "rl", "rr"]:
            angle = lever_angles.get(corner, 0.0)
            cyl_state = cylinder_states.get(corner, None)
            corners[corner] = self.get_corner_3d_coords(corner, angle, cyl_state)

        return corners

    def update_from_simulation(self, sim_state: Dict[str, Any]) -> Dict[str, Any]:
        """Update 3D coordinates from simulation state

        Args:
            sim_state: Current simulation state with lever angles, cylinder states, etc.

        Returns:
            Complete geometry data for 3D scene update
        """
        # Extract lever angles from simulation
        lever_angles = {}

        if "lever_angles" in sim_state:
            lever_angles = sim_state["lever_angles"]
        else:
            # Extract from individual angle fields
            lever_angles = {
                "fl": sim_state.get("fl_angle", 0.0),
                "fr": sim_state.get("fr_angle", 0.0),
                "rl": sim_state.get("rl_angle", 0.0),
                "rr": sim_state.get("rr_angle", 0.0),
            }

        # Ensure angles are in radians (tolerate legacy degrees)
        for key, value in list(lever_angles.items()):
            if isinstance(value, (int, float)) and abs(value) > math.tau:
                lever_angles[key] = math.radians(value)

        # Extract cylinder states (if available)
        cylinder_states = {}
        if "cylinder_states" in sim_state:
            cylinder_states = sim_state["cylinder_states"]
        elif "corners" in sim_state:
            # Try to extract from corners structure
            for corner, data in sim_state.get("corners", {}).items():
                if "cylinder_state" in data:
                    cylinder_states[corner] = data["cylinder_state"]

        return {
            "frame": self.get_frame_params(),
            "corners": self.get_all_corners_3d(lever_angles, cylinder_states),
            # Add user-controllable parameters
            "userParams": {
                "frameLength": self._frame_length,
                "frameHeight": self._frame_height,
                "frameBeamSize": self._frame_beam_size,
                "leverLength": self._lever_length,
                "cylinderBodyLength": self._cylinder_body_length,
                "tailRodLength": self._tail_rod_length,
            },
        }

    def update_user_parameters(self, params: Dict[str, float], persist: bool = False):
        """Update multiple user parameters at once

        Args:
            params: Dictionary with parameter names and values
            persist: If True, persist changes to settings manager
        """
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

        # Persist changes to settings manager
        if persist:
            self.save_to_settings()

    def save_to_settings(self):
        """Save current geometry settings to persistent storage"""
        if self._settings_manager is None:
            return

        manager = self._settings_manager
        manager.set("geometry.frame_length_m", self._frame_length, auto_save=False)
        manager.set("geometry.frame_height_m", self._frame_height, auto_save=False)
        manager.set("geometry.frame_beam_size_m", self._frame_beam_size, auto_save=False)
        manager.set("geometry.lever_length_m", self._lever_length, auto_save=False)
        manager.set(
            "geometry.cylinder_body_length_m",
            self._cylinder_body_length,
            auto_save=False,
        )
        manager.set("geometry.tail_rod_length_m", self._tail_rod_length, auto_save=False)
        manager.save()

    def export_geometry_params(self) -> Dict[str, Any]:
        """Export current geometry parameters as dictionary

        Returns:
            Dictionary with geometry parameters for export
        """
        return {
            "frameLength": self._frame_length,
            "frameHeight": self._frame_height,
            "frameBeamSize": self._frame_beam_size,
            "leverLength": self._lever_length,
            "cylinderBodyLength": self._cylinder_body_length,
            "tailRodLength": self._tail_rod_length,
        }


# Convenience function for easy integration
def create_geometry_converter(
    wheelbase: float = 2.0,
    lever_length: float = 0.315,
    cylinder_diameter: float = 0.08,
    settings_manager: Optional[Any] = None,
) -> GeometryTo3DConverter:
    """Create geometry converter with common parameters

    Args:
        wheelbase: Vehicle track width in meters
        lever_length: Suspension lever length in meters
        cylinder_diameter: Cylinder bore diameter in meters
        settings_manager: Optional SettingsManager instance for persistent settings

    Returns:
        Configured GeometryTo3DConverter
    """
    geometry = GeometryParams()
    geometry.wheelbase = wheelbase
    geometry.lever_length = lever_length
    geometry.cylinder_inner_diameter = cylinder_diameter
    geometry.enforce_track_from_geometry()  # Ensure consistency

    converter = GeometryTo3DConverter(geometry, settings_manager=settings_manager)

    return converter
