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

_logger = logging.getLogger(__name__)


class SuspensionSceneHost(QQuickWidget):
    """Host widget for full suspension scene with 4 corners"""

    # Signals for user interaction
    view_reset_requested = Signal()

    def __init__(self, parent=None, geometry_overrides: Optional[Dict[str, float]] = None):
        super().__init__(parent)

        geometry_params = self._build_geometry_params(geometry_overrides or {})
        self.geometry_converter = GeometryTo3DConverter(geometry_params)

        # Get calculated coordinates for all corners
        all_corners = self.geometry_converter.get_all_corners_3d()
        frame_params = self.geometry_converter.get_frame_params()

        # Build parameters dictionary from geometry_bridge calculations
        self._params = {
            # Frame (from geometry_bridge)
            "beamSize": frame_params["beamSize"],
            "frameHeight": frame_params["frameHeight"],
            "frameLength": frame_params["frameLength"],
        }

        # Add all corner parameters from geometry_bridge
        for corner_key in ["fl", "fr", "rl", "rr"]:
            corner_data = all_corners[corner_key]

            # Convert to QML property names (use correct keys from geometry_bridge)
            self._params.update(
                {
                    f"{corner_key}_j_arm": corner_data["j_arm"],
                    f"{corner_key}_leverLength": corner_data[
                        "leverLength"
                    ],  # ? Correct key
                    f"{corner_key}_leverAngle": corner_data["leverAngle"],  # ? New key
                    f"{corner_key}_totalAngle": corner_data["totalAngle"],  # ? New key
                    f"{corner_key}_baseAngle": corner_data["baseAngle"],  # ? New key
                    f"{corner_key}_j_tail": corner_data["j_tail"],
                    f"{corner_key}_j_rod": corner_data["j_rod"],
                    f"{corner_key}_cylinderBodyLength": corner_data[
                        "cylinderBodyLength"
                    ],  # ? Correct key
                    f"{corner_key}_tailRodLength": corner_data[
                        "tailRodLength"
                    ],  # ? Correct key
                    # Additional properties for compatibility
                    f"{corner_key}_corner": corner_data["corner"],
                    f"{corner_key}_side": corner_data["side"],
                    f"{corner_key}_position": corner_data["position"],
                }
            )

        _logger.debug("Loaded coordinates from geometry_bridge: Frame=%s", frame_params)
        _logger.debug("FL j_arm: %s", all_corners["fl"]["j_arm"])
        _logger.debug("FR j_arm: %s", all_corners["fr"]["j_arm"])

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

        raise FileNotFoundError("Neither UFrameScene.qml nor SimulationFallbackRoot.qml found")

    def _apply_all_parameters(self):
        """Apply all parameters to QML root object"""
        root = self.rootObject()
        if not root:
            _logger.warning("QML root object is None!")
            return

        applied_count = 0
        failed_count = 0

        _logger.debug("Applying %d parameters to QML", len(self._params))

        for key, value in self._params.items():
            try:
                root.setProperty(key, value)
                applied_count += 1

                # Debug key coordinates and lever lengths
                if key in ["fl_j_arm", "fr_j_arm", "fl_leverLength", "fr_leverLength"]:
                    _logger.debug("Set %s = %s", key, value)
                elif "cylinderBodyLength" in key or "tailRodLength" in key:
                    _logger.debug("Set %s = %s", key, value)

            except Exception as e:
                _logger.warning("Failed to set %s = %s: %s", key, value, e)
                failed_count += 1

        _logger.info(
            "Applied %d/%d parameters to QML (failed=%d)",
            applied_count,
            len(self._params),
            failed_count,
        )

        # Debug: Try to read some values back
        try:
            beamSize = root.property("beamSize")
            frameLength = root.property("frameLength")
            fl_leverLength = root.property("fl_leverLength")
            _logger.debug(
                "Read-back beamSize=%s frameLength=%s fl_leverLength=%s",
                beamSize,
                frameLength,
                fl_leverLength,
            )
        except Exception as e:
            _logger.debug("Failed to read back values: %s", e)

    def update_corner(self, corner: str, **kwargs):
        """Update parameters for specific corner (FL/FR/RL/RR)

        Args:
            corner: "FL", "FR", "RL", or "RR"
            **kwargs: Parameter updates (e.g., armAngleDeg=5.0, j_rod=QVector3D(...))
        """
        root = self.rootObject()
        if not root:
            return

        for key, value in kwargs.items():
            prop_name = f"{corner}_{key}"
            if prop_name in self._params:
                self._params[prop_name] = value
                root.setProperty(prop_name, value)

    def update_frame(self, **kwargs):
        """Update frame parameters

        Args:
            **kwargs: beamSize, frameHeight, frameLength
        """
        root = self.rootObject()
        if not root:
            return

        for key in ["beamSize", "frameHeight", "frameLength"]:
            if key in kwargs:
                self._params[key] = kwargs[key]
                root.setProperty(key, kwargs[key])

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


# Backward compatibility alias
UFrameSceneHost = SuspensionSceneHost
