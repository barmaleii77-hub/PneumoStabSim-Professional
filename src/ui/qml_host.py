# -*- coding: utf-8 -*-
"""
QML Host for full suspension 3D visualization
Embeds UFrameScene.qml with all 4 corners (FL/FR/RL/RR) into PySide6 application
Uses geometry_bridge.py for correct coordinate calculation
"""

import logging
from pathlib import Path
from typing import Dict, Optional

from PySide6.QtCore import QUrl, Signal
from PySide6.QtQuickWidgets import QQuickWidget

# Import geometry bridge for correct coordinate calculation
from ..core.geometry import GeometryParams
from src.ui.geometry_bridge import GeometryTo3DConverter
from src.ui.scene_bridge import SceneBridge

_logger = logging.getLogger(__name__)


class SuspensionSceneHost(QQuickWidget):
    """Host widget for full suspension scene with 4 corners"""

    # Signals for user interaction
    view_reset_requested = Signal()

    def __init__(
        self, parent=None, geometry_overrides: Optional[Dict[str, float]] = None
    ):
        super().__init__(parent)

        self._geometry_params = self._build_geometry_params(geometry_overrides or {})
        self.geometry_converter = GeometryTo3DConverter(self._geometry_params)
        self._scene_bridge = SceneBridge(self)
        self.rootContext().setContextProperty("pythonSceneBridge", self._scene_bridge)

        # Get calculated coordinates for all corners
        self._corner_data = self.geometry_converter.get_all_corners_3d()
        frame_params = self.geometry_converter.get_frame_params()

        # Build parameters dictionary exposed via get_parameters for diagnostics
        self._params = {
            "beamSize": frame_params["beamSize"],
            "frameHeight": frame_params["frameHeight"],
            "frameLength": frame_params["frameLength"],
        }

        for corner_key, corner_values in self._corner_data.items():
            piston_position = corner_values.get("pistonPosition", 0.0)
            corner_payload = {
                f"{corner_key}_leverAngleRad": corner_values.get("leverAngleRad", 0.0),
                f"{corner_key}_pistonPosition": piston_position,
            }
            self._params.update(corner_payload)

        _logger.debug("Loaded coordinates from geometry_bridge: Frame=%s", frame_params)
        _logger.debug("FL lever angle (rad): %s", self._params["fl_leverAngleRad"])
        _logger.debug("FR lever angle (rad): %s", self._params["fr_leverAngleRad"])

        # Setup QML
        self.setResizeMode(QQuickWidget.SizeRootObjectToView)

        self._qml_path = self._resolve_qml_path()
        self.setSource(QUrl.fromLocalFile(str(self._qml_path)))

        # Check for QML errors
        if self.status() == QQuickWidget.Status.Error:
            errors = self.errors()
            error_msg = "\n".join(str(e) for e in errors)
            _logger.error("QML errors in %s:\n%s", self._qml_path.name, error_msg)
            raise RuntimeError(f"QML errors:\n{error_msg}")

        _logger.info("%s loaded, status: %s", self._qml_path.name, self.status())

        # Wait for QML to be fully ready, then apply parameters
        if self.status() == QQuickWidget.Status.Ready:
            self._apply_all_parameters()
        else:
            # Use a timer to apply parameters when ready
            from PySide6.QtCore import QTimer

            def delayed_apply():
                if self.status() == QQuickWidget.Status.Ready:
                    self._apply_all_parameters()
                else:
                    _logger.debug("QML still not ready, retrying...")
                    QTimer.singleShot(100, delayed_apply)

            QTimer.singleShot(50, delayed_apply)

    @staticmethod
    def _build_geometry_params(overrides: Dict[str, float]) -> GeometryParams:
        """Create :class:`GeometryParams` applying numeric overrides when possible."""

        params = GeometryParams()

        for key, value in overrides.items():
            if not hasattr(params, key):
                continue
            try:
                setattr(params, key, float(value))
            except (TypeError, ValueError):
                _logger.debug(
                    "Skipping geometry override %s=%r (unable to coerce to float)",
                    key,
                    value,
                )

        return params

    def _resolve_qml_path(self) -> Path:
        """Return the QML path, falling back to the 2D scene if legacy assets are absent."""

        base = Path(__file__).parent.parent.parent / "assets" / "qml"
        modular = base / "main.qml"
        if modular.exists():
            _logger.info("Loading modular main.qml: %s", modular)
            return modular

        legacy = base / "UFrameScene.qml"
        if legacy.exists():
            _logger.info("Loading legacy UFrameScene.qml: %s", legacy)
            return legacy

        fallback = base / "SimulationFallbackRoot.qml"
        if fallback.exists():
            _logger.warning(
                "Legacy UFrameScene.qml missing; using SimulationFallbackRoot.qml instead"
            )
            return fallback

        raise FileNotFoundError(
            "Neither UFrameScene.qml nor SimulationFallbackRoot.qml found"
        )

    def _apply_all_parameters(self):
        """Apply all parameters to QML root object"""
        updates = self._build_initial_updates()
        self._dispatch_updates(updates)

    def update_corner(self, corner: str, **kwargs):
        """Update parameters for specific corner (FL/FR/RL/RR)

        Args:
            corner: "FL", "FR", "RL", or "RR"
            **kwargs: Parameter updates (e.g., armAngleDeg=5.0, j_rod=QVector3D(...))
        """
        if self.rootObject() is None:
            return

        normalized_corner = corner.strip().lower()
        if normalized_corner not in {"fl", "fr", "rl", "rr"}:
            _logger.warning("Unknown corner key: %s", corner)
            return

        animation_patch = {}
        wheel_patch = {}

        for key, value in kwargs.items():
            if key.lower() in {"leverangle", "lever_angle", "leveranglerad"}:
                try:
                    rad = float(value)
                except (TypeError, ValueError):
                    _logger.debug(
                        "Skipping non-numeric lever angle for %s: %r", corner, value
                    )
                    continue
                animation_patch.setdefault("leverAngles", {})[normalized_corner] = rad
                wheel_patch.setdefault(normalized_corner, {})["leverAngle"] = rad
                self._params[f"{normalized_corner}_leverAngleRad"] = rad
            elif key.lower() in {"pistonposition", "piston_position"}:
                try:
                    position = float(value)
                except (TypeError, ValueError):
                    _logger.debug(
                        "Skipping non-numeric piston position for %s: %r", corner, value
                    )
                    continue
                animation_patch.setdefault("pistonPositions", {})[normalized_corner] = (
                    position
                )
                wheel_patch.setdefault(normalized_corner, {})["pistonPosition"] = (
                    position
                )
                self._params[f"{normalized_corner}_pistonPosition"] = position
            else:
                self._params[f"{normalized_corner}_{key}"] = value

        updates = {}
        if animation_patch:
            updates["animation"] = animation_patch
        if wheel_patch:
            updates["threeD"] = {"wheels": wheel_patch}

        if updates:
            self._dispatch_updates(updates)

    def update_frame(self, **kwargs):
        """Update frame parameters

        Args:
            **kwargs: beamSize, frameHeight, frameLength
        """
        payload = {}
        for key in ["beamSize", "frameHeight", "frameLength"]:
            if key in kwargs:
                try:
                    payload[key] = float(kwargs[key])
                except (TypeError, ValueError):
                    _logger.debug(
                        "Skipping non-numeric frame value %s=%r", key, kwargs[key]
                    )
                    continue
                self._params[key] = payload[key]

        if payload:
            self._dispatch_updates({"geometry": payload})

    def reset_view(self):
        """Reset camera to default view"""
        root = self.rootObject()
        if root:
            root.resetView()

    def auto_fit(self):
        """Auto-fit camera to entire scene"""
        root = self.rootObject()
        if root:
            root.autoFit()

    def get_parameters(self):
        """Get current parameters dictionary"""
        return self._params.copy()

    # ------------------------------------------------------------------
    # Helpers for modular QML bridge
    # ------------------------------------------------------------------

    def _build_initial_updates(self) -> Dict[str, Dict[str, object]]:
        """Prepare the initial payload dispatched to the modular QML scene."""

        geometry_payload = {
            "beamSize": float(self._params.get("beamSize", 0.0)),
            "frameHeight": float(self._params.get("frameHeight", 0.0)),
            "frameLength": float(self._params.get("frameLength", 0.0)),
            "leverLength": float(self.geometry_converter.leverLength),
            "cylinderLength": float(self.geometry_converter.cylinderBodyLength),
            "tailRodLength": float(self.geometry_converter.tailRodLength),
            "trackWidth": float(self._geometry_params.track_width),
            "frameToPivot": float(self._geometry_params.pivot_offset_from_frame),
            "rodPosition": float(self._geometry_params.rod_attach_fraction),
            "boreHead": float(self._geometry_params.cylinder_inner_diameter),
            "rodDiameter": float(self._geometry_params.rod_diameter),
            "pistonThickness": float(self._geometry_params.piston_thickness),
        }

        lever_angles = {}
        piston_positions = {}
        wheels: Dict[str, Dict[str, float]] = {}
        for corner, data in self._corner_data.items():
            rad = float(data.get("leverAngleRad", 0.0))
            piston = float(data.get("pistonPosition", 0.0))
            lever_angles[corner] = rad
            piston_positions[corner] = piston
            wheels[corner] = {"leverAngle": rad, "pistonPosition": piston}

        animation_payload = {
            "leverAngles": lever_angles,
            "pistonPositions": piston_positions,
        }

        three_d_payload = {
            "frame": {"heave": 0.0, "roll": 0.0, "pitch": 0.0},
            "wheels": wheels,
        }

        return {
            "geometry": geometry_payload,
            "animation": animation_payload,
            "threeD": three_d_payload,
        }

    def _dispatch_updates(self, updates: Dict[str, Dict[str, object]]) -> None:
        """Send updates to the active QML scene, falling back to legacy properties."""

        if not updates:
            return

        dispatched = False
        try:
            dispatched = self._scene_bridge.dispatch_updates(updates)
        except Exception as exc:  # pragma: no cover - Qt runtime failure
            _logger.error("SceneBridge dispatch failed: %s", exc, exc_info=True)

        if dispatched:
            categories = ", ".join(sorted(updates.keys()))
            _logger.debug("SceneBridge dispatched categories: %s", categories)
            return

        root = self.rootObject()
        if root is None:
            _logger.debug("Root object not ready; pending updates deferred")
            return

        try:
            root.setProperty("pendingPythonUpdates", updates)
            _logger.debug("Applied pendingPythonUpdates fallback: %s", updates.keys())
        except Exception as exc:  # pragma: no cover - QML specific failure
            _logger.warning("Failed to apply fallback updates: %s", exc)


# Backward compatibility alias
UFrameSceneHost = SuspensionSceneHost
