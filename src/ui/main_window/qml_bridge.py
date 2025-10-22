"""QML Bridge Module - Python↔QML communication

Модуль управления взаимодействием между Python и QML.
Отвечает за вызов QML функций, батч-обновления и синхронизацию состояния.

Russian comments / English code.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional

from PySide6.QtCore import Q_ARG, QMetaObject, Qt

from src.pneumo.enums import Line, Wheel
from src.runtime.state import StateSnapshot

if TYPE_CHECKING:
    from .main_window import MainWindow


class QMLBridge:
    """Мост между Python и QML

    Управляет:
    - Вызовами QML функций
    - Батч-обновлениями
    - Очередью изменений
    - ACK сигналами

    Static methods для делегирования из MainWindow.
    """

    logger = logging.getLogger(__name__)

    # QML update method mapping
    QML_UPDATE_METHODS: Dict[str, tuple[str, ...]] = {
        "geometry": ("applyGeometryUpdates", "updateGeometry"),
        "animation": (
            "applyAnimationUpdates",
            "updateAnimation",
            "applyAnimParamsUpdates",
            "updateAnimParams",
        ),
        "lighting": ("applyLightingUpdates", "updateLighting"),
        "materials": ("applyMaterialUpdates", "updateMaterials"),
        "environment": ("applyEnvironmentUpdates", "updateEnvironment"),
        "quality": ("applyQualityUpdates", "updateQuality"),
        "camera": ("applyCameraUpdates", "updateCamera"),
        "effects": ("applyEffectsUpdates", "updateEffects"),
        "simulation": ("applySimulationUpdates",),
    }

    # ------------------------------------------------------------------
    # Queue Management
    # ------------------------------------------------------------------
    @staticmethod
    def queue_update(window: MainWindow, key: str, params: Dict[str, Any]) -> None:
        """Поставить изменения в очередь для батч-отправки в QML

        Args:
            window: MainWindow instance
            key: Update category (geometry, lighting, etc.)
            params: Update parameters
        """
        if not params:
            return

        if key not in window._qml_update_queue:
            window._qml_update_queue[key] = {}

        QMLBridge._deep_merge_dicts(window._qml_update_queue[key], params)

        if not window._qml_flush_timer.isActive():
            window._qml_flush_timer.start(0)

    @staticmethod
    def flush_updates(window: MainWindow) -> None:
        """Сбросить накопленные batched-обновления в QML

        Strategy:
        1. Try pendingPythonUpdates property (fast)
        2. Fallback to individual function calls

        Args:
            window: MainWindow instance
        """
        if not window._qml_update_queue:
            return

        if not window._qml_root_object:
            # Retry later
            window._qml_flush_timer.start(100)
            return

        pending = window._qml_update_queue
        window._qml_update_queue = {}

        # Try batched push
        if QMLBridge._push_batched_updates(window, pending):
            window._last_batched_updates = pending
            return

        # Fallback: individual calls
        for key, payload in pending.items():
            methods = QMLBridge.QML_UPDATE_METHODS.get(key, ())
            for method_name in methods:
                if QMLBridge.invoke_qml_function(window, method_name, payload):
                    break

    @staticmethod
    def _push_batched_updates(
        window: MainWindow, updates: Dict[str, Any]
    ) -> bool:
        """Push updates via pendingPythonUpdates property

        Args:
            window: MainWindow instance
            updates: Batched updates dict

        Returns:
            True if successful
        """
        if not updates:
            return True
        if not window._qml_root_object:
            return False

        try:
            sanitized = QMLBridge._prepare_for_qml(updates)
            window._qml_root_object.setProperty(
                "pendingPythonUpdates",
                sanitized,
            )
            return True
        except Exception:
            return False

    # ------------------------------------------------------------------
    # Simulation State Synchronization
    # ------------------------------------------------------------------
    @staticmethod
    def set_simulation_state(
        window: "MainWindow", snapshot: StateSnapshot
    ) -> bool:
        """Push complete simulation state into QML as SI-based payload."""

        if snapshot is None or not window._qml_root_object:
            return False

        try:
            payload = QMLBridge._snapshot_to_payload(snapshot)
            payload.setdefault("animation", {})["isRunning"] = bool(
                getattr(window, "is_simulation_running", False)
            )

            sanitized = QMLBridge._prepare_for_qml(payload)
            window._qml_root_object.setProperty(
                "pendingPythonUpdates",
                sanitized,
            )
            return True
        except Exception as exc:
            QMLBridge.logger.debug(
                f"Failed to push simulation state: {exc}"
            )
            return False

    @staticmethod
    def _snapshot_to_payload(snapshot: StateSnapshot) -> Dict[str, Any]:
        """Convert StateSnapshot dataclass into QML-friendly SI dictionary."""

        wheel_key_map = {
            Wheel.LP: "fl",
            Wheel.PP: "fr",
            Wheel.LZ: "rl",
            Wheel.PZ: "rr",
        }

        wheels_payload: Dict[str, Dict[str, Any]] = {}
        lever_angles: Dict[str, float] = {}
        piston_positions: Dict[str, float] = {}

        for wheel_enum, corner_key in wheel_key_map.items():
            wheel_state = snapshot.wheels.get(wheel_enum)
            if not wheel_state:
                continue

            lever_angle = float(wheel_state.lever_angle)
            piston_position = float(wheel_state.piston_position)

            wheels_payload[corner_key] = {
                "leverAngle": lever_angle,
                "pistonPosition": piston_position,
                "pistonVelocity": float(wheel_state.piston_velocity),
                "joint": {
                    "x": float(wheel_state.joint_x),
                    "y": float(wheel_state.joint_y),
                    "z": float(wheel_state.joint_z),
                },
                "forces": {
                    "pneumatic": float(wheel_state.force_pneumatic),
                    "spring": float(wheel_state.force_spring),
                    "damper": float(wheel_state.force_damper),
                },
            }

            lever_angles[corner_key] = lever_angle
            piston_positions[corner_key] = piston_position

        line_payload: Dict[str, Dict[str, Any]] = {}
        for line_enum in Line:
            line_state = snapshot.lines.get(line_enum)
            if not line_state:
                continue

            key = line_enum.value.lower()
            line_payload[key] = {
                "pressure": float(line_state.pressure),
                "temperature": float(line_state.temperature),
                "mass": float(line_state.mass),
            }

        animation_payload = {
            "timestamp": float(snapshot.timestamp),
            "simulationTime": float(snapshot.simulation_time),
            "frame": {
                "heave": float(snapshot.frame.heave),
                "roll": float(snapshot.frame.roll),
                "pitch": float(snapshot.frame.pitch),
                "heaveRate": float(snapshot.frame.heave_rate),
                "rollRate": float(snapshot.frame.roll_rate),
                "pitchRate": float(snapshot.frame.pitch_rate),
            },
            "leverAngles": lever_angles,
            "pistonPositions": piston_positions,
            "linePressures": {
                key: state["pressure"]
                for key, state in line_payload.items()
            },
            "tankPressure": float(snapshot.tank.pressure),
        }

        three_d_payload = {
            "wheels": wheels_payload,
            "lines": line_payload,
            "tank": {
                "pressure": float(snapshot.tank.pressure),
                "temperature": float(snapshot.tank.temperature),
            },
            "frame": {
                "heave": float(snapshot.frame.heave),
                "roll": float(snapshot.frame.roll),
                "pitch": float(snapshot.frame.pitch),
            },
        }

        return {
            "animation": animation_payload,
            "threeD": three_d_payload,
        }

    # ------------------------------------------------------------------
    # Function Invocation
    # ------------------------------------------------------------------
    @staticmethod
    def invoke_qml_function(
        window: MainWindow,
        method_name: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Безопасный вызов QML-функции

        Args:
            window: MainWindow instance
            method_name: QML function name
            payload: Optional function arguments

        Returns:
            True if call succeeded
        """
        if not window._qml_root_object:
            return False

        try:
            # Log QML invoke
            try:
                window.event_logger.log_qml_invoke(
                    method_name,
                    payload or {},
                )
            except Exception:
                pass

            if payload is None:
                success = QMetaObject.invokeMethod(
                    window._qml_root_object,
                    method_name,
                    Qt.ConnectionType.DirectConnection,
                )
            else:
                success = QMetaObject.invokeMethod(
                    window._qml_root_object,
                    method_name,
                    Qt.ConnectionType.DirectConnection,
                    Q_ARG("QVariant", payload),
                )

            return bool(success)
        except Exception as exc:
            QMLBridge.logger.debug(
                f"QML call failed: {method_name} - {exc}"
            )
            return False

    # ------------------------------------------------------------------
    # Data Preparation
    # ------------------------------------------------------------------
    @staticmethod
    def _prepare_for_qml(value: Any) -> Any:
        """Подготовить данные для передачи в QML

        Handles:
        - Nested dicts/lists
        - NumPy types
        - Path objects

        Args:
            value: Python value

        Returns:
            QML-safe value
        """
        if isinstance(value, dict):
            return {
                str(k): QMLBridge._prepare_for_qml(v)
                for k, v in value.items()
            }

        if isinstance(value, (list, tuple)):
            return [QMLBridge._prepare_for_qml(i) for i in value]

        # NumPy conversion
        try:
            import numpy as np

            if isinstance(value, np.generic):
                return value.item()
            if hasattr(value, "tolist") and callable(value.tolist):
                return QMLBridge._prepare_for_qml(value.tolist())
        except ImportError:
            pass

        # Path to string
        if isinstance(value, Path):
            return str(value)

        return value

    @staticmethod
    def _deep_merge_dicts(
        target: Dict[str, Any], source: Dict[str, Any]
    ) -> None:
        """Deep merge source dict into target

        Args:
            target: Target dict (modified in-place)
            source: Source dict
        """
        for k, v in source.items():
            if isinstance(v, dict) and isinstance(target.get(k), dict):
                QMLBridge._deep_merge_dicts(
                    target[k],
                    v,
                )
            else:
                target[k] = v

    # ------------------------------------------------------------------
    # ACK Handling
    # ------------------------------------------------------------------
    @staticmethod
    def handle_qml_ack(window: MainWindow, summary: Dict[str, Any]) -> None:
        """Обработать ACK от QML после применения батч-обновлений

        Args:
            window: MainWindow instance
            summary: ACK summary from QML
        """
        try:
            QMLBridge.logger.info(f"QML batch ACK: {summary}")

            if hasattr(window, "status_bar"):
                window.status_bar.showMessage(
                    "Обновления применены в сцене",
                    1500,
                )

            # Mark changes as applied in GraphicsLogger
            if window._last_batched_updates:
                try:
                    from ..panels.graphics_logger import get_graphics_logger

                    glog = get_graphics_logger()

                    since_ts = (
                        summary.get("timestamp")
                        if isinstance(summary, dict)
                        else None
                    )

                    for cat, payload in window._last_batched_updates.items():
                        if isinstance(payload, dict) and payload:
                            # Log as applied
                            QMLBridge._log_graphics_change(
                                window, str(cat), payload, applied=True
                            )

                            # Mark category as synced
                            try:
                                glog.mark_category_changes_applied(
                                    str(cat),
                                    since_timestamp=since_ts,
                                )
                            except Exception:
                                pass

                    window._last_batched_updates = None
                except Exception:
                    pass
        except Exception:
            pass

    # ------------------------------------------------------------------
    # Graphics Logger Integration
    # ------------------------------------------------------------------
    @staticmethod
    def _log_graphics_change(
        window: MainWindow,
        category: str,
        payload: Dict[str, Any],
        applied: bool,
    ) -> None:
        """Log graphics change for sync metrics

        Args:
            window: MainWindow instance
            category: Change category
            payload: Change data
            applied: Whether applied to QML
        """
        try:
            from ..panels.graphics_logger import get_graphics_logger

            logger = get_graphics_logger()
            logger.log_change(
                parameter_name=f"{category}_batch",
                old_value=None,
                new_value=payload,
                category=category,
                panel_state=payload,
                qml_state={"applied": applied},
                applied_to_qml=applied,
            )
        except Exception:
            pass

    @staticmethod
    def set_simulation_state(window: "MainWindow", snapshot: StateSnapshot) -> bool:
        """Push complete simulation state into QML as SI-based payload."""

        if snapshot is None or not window._qml_root_object:
            return False

        try:
            payload = QMLBridge._snapshot_to_payload(snapshot)
            payload.setdefault("animation", {})["isRunning"] = bool(
                getattr(window, "is_simulation_running", False)
            )

            sanitized = QMLBridge._prepare_for_qml(payload)
            window._qml_root_object.setProperty(
                "pendingPythonUpdates",
                sanitized,
            )
            return True
        except Exception as exc:
            QMLBridge.logger.debug(
                f"Failed to push simulation state: {exc}"
            )
            return False

    @staticmethod
    def _snapshot_to_payload(snapshot: StateSnapshot) -> Dict[str, Any]:
        """Convert StateSnapshot dataclass into QML-friendly SI dictionary."""

        wheel_key_map = {
            Wheel.LP: "fl",
            Wheel.PP: "fr",
            Wheel.LZ: "rl",
            Wheel.PZ: "rr",
        }

        wheels_payload: Dict[str, Dict[str, Any]] = {}
        lever_angles: Dict[str, float] = {}
        piston_positions: Dict[str, float] = {}

        for wheel_enum, corner_key in wheel_key_map.items():
            wheel_state = snapshot.wheels.get(wheel_enum)
            if not wheel_state:
                continue

            lever_angle = float(wheel_state.lever_angle)
            piston_position = float(wheel_state.piston_position)

            wheels_payload[corner_key] = {
                "leverAngle": lever_angle,
                "pistonPosition": piston_position,
                "pistonVelocity": float(wheel_state.piston_velocity),
                "joint": {
                    "x": float(wheel_state.joint_x),
                    "y": float(wheel_state.joint_y),
                    "z": float(wheel_state.joint_z),
                },
                "forces": {
                    "pneumatic": float(wheel_state.force_pneumatic),
                    "spring": float(wheel_state.force_spring),
                    "damper": float(wheel_state.force_damper),
                },
            }

            lever_angles[corner_key] = lever_angle
            piston_positions[corner_key] = piston_position

        line_payload: Dict[str, Dict[str, Any]] = {}
        for line_enum in Line:
            line_state = snapshot.lines.get(line_enum)
            if not line_state:
                continue

            key = line_enum.value.lower()
            line_payload[key] = {
                "pressure": float(line_state.pressure),
                "temperature": float(line_state.temperature),
                "mass": float(line_state.mass),
            }

        animation_payload = {
            "timestamp": float(snapshot.timestamp),
            "simulationTime": float(snapshot.simulation_time),
            "frame": {
                "heave": float(snapshot.frame.heave),
                "roll": float(snapshot.frame.roll),
                "pitch": float(snapshot.frame.pitch),
                "heaveRate": float(snapshot.frame.heave_rate),
                "rollRate": float(snapshot.frame.roll_rate),
                "pitchRate": float(snapshot.frame.pitch_rate),
            },
            "leverAngles": lever_angles,
            "pistonPositions": piston_positions,
            "linePressures": {
                key: state["pressure"]
                for key, state in line_payload.items()
            },
            "tankPressure": float(snapshot.tank.pressure),
        }

        three_d_payload = {
            "wheels": wheels_payload,
            "lines": line_payload,
            "tank": {
                "pressure": float(snapshot.tank.pressure),
                "temperature": float(snapshot.tank.temperature),
            },
            "frame": {
                "heave": float(snapshot.frame.heave),
                "roll": float(snapshot.frame.roll),
                "pitch": float(snapshot.frame.pitch),
            },
        }

        return {
            "animation": animation_payload,
            "threeD": three_d_payload,
        }
