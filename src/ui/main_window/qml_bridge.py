"""QML Bridge Module - Python↔QML communication

Упрощённая и корректно отформатированная версия моста для тестирования.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, Optional, Union

# Try to import Qt pieces, but provide lightweight fallbacks for test environment
try:
    from PySide6.QtCore import Q_ARG, QMetaObject, Qt
except Exception:  # pragma: no cover - fallback for test env without PySide6

    class _DummyQt:
        class ConnectionType:
            DirectConnection = 0

    class _DummyQMetaObject:
        @staticmethod
        def invokeMethod(*_args: Any, **_kwargs: Any) -> bool:
            return False

    def Q_ARG(*_args: Any, **_kwargs: Any) -> None:
        return None

    QMetaObject = _DummyQMetaObject  # type: ignore[assignment]
    Qt = _DummyQt()  # type: ignore[assignment]


@dataclass(slots=True)
class QMLUpdateResult:
    """Структура результата попытки обновления QML."""

    success: bool
    error: Optional[str] = None
    exception: Optional[Exception] = None


class QMLBridge:
    """Мост между Python и QML (упрощённый).

    Реализует минимальный набор функций для батч-обновлений и ошибок.
    """

    logger = logging.getLogger(__name__)

    QML_UPDATE_METHODS: Dict[str, tuple[str, ...]] = {
        "geometry": ("applyGeometryUpdates", "updateGeometry"),
        "animation": ("applyAnimationUpdates", "updateAnimation"),
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
    def queue_update(window: "MainWindow", key: str, params: Dict[str, Any]) -> None:
        """Поставить изменения в очередь для батч-отправки в QML."""
        if not params:
            return

        queue: Dict[str, Dict[str, Any]] = getattr(window, "_qml_update_queue", {})
        if not queue:
            window._qml_update_queue = queue

        target = queue.setdefault(key, {})
        QMLBridge._deep_merge_dicts(target, params)

        timer = getattr(window, "_qml_flush_timer", None)
        if timer is not None:
            try:
                if not timer.isActive():
                    timer.start(0)
            except Exception:
                pass

    @staticmethod
    def flush_updates(window: "MainWindow") -> None:
        queue: Dict[str, Dict[str, Any]] = getattr(window, "_qml_update_queue", {})
        if not queue:
            return

        if not getattr(window, "_qml_root_object", None):
            timer = getattr(window, "_qml_flush_timer", None)
            if timer is not None:
                try:
                    timer.start(100)
                except Exception:
                    pass
            return

        window._qml_update_queue = {}
        result = QMLBridge._push_batched_updates(window, queue, detailed=True)

        if isinstance(result, QMLUpdateResult):
            push_success = result.success
            failure_reason = result.error
        else:
            push_success = bool(result)
            failure_reason = None

        if push_success:
            window._last_batched_updates = queue
            return

        QMLBridge._notify_qml_failure(
            window,
            "QML не принял пакет обновлений",
            failure_reason,
        )

        for category, payload in queue.items():
            methods = QMLBridge.QML_UPDATE_METHODS.get(category, ())
            for method_name in methods:
                if QMLBridge.invoke_qml_function(window, method_name, payload):
                    break

    @staticmethod
    def _push_batched_updates(
        window: "MainWindow",
        updates: Dict[str, Any],
        *,
        detailed: bool = False,
        raise_on_error: bool = False,
    ) -> Union[bool, QMLUpdateResult]:
        """Try to set `pendingPythonUpdates` property on QML root.

        Returns either bool or QMLUpdateResult when detailed=True.
        """
        if not updates:
            return QMLBridge._make_update_result(True, detailed)

        if not getattr(window, "_qml_root_object", None):
            return QMLBridge._make_update_result(False, detailed, "QML root missing")

        try:
            sanitized = QMLBridge._prepare_for_qml(updates)
            window._suppress_qml_feedback = True
            try:
                window._qml_root_object.setProperty("pendingPythonUpdates", sanitized)
            finally:
                window._suppress_qml_feedback = False
            return QMLBridge._make_update_result(True, detailed)
        except Exception as exc:
            QMLBridge.logger.error(
                "Failed to push batched updates to QML: %s", exc, exc_info=True
            )

            # Record into EventLogger if available
            try:
                QMLBridge._log_qml_update_failure(
                    window, context="flush_updates", payload=updates, error=exc
                )
            except Exception:
                QMLBridge.logger.debug(
                    "Failed to record qml update failure into event logger",
                    exc_info=True,
                )

            if raise_on_error:
                raise QMLUpdateError("QML rejected batched updates") from exc

            return QMLBridge._make_update_result(False, detailed, str(exc), exc)

    # ------------------------------------------------------------------
    # Simulation State Synchronization
    # ------------------------------------------------------------------
    @staticmethod
    def set_simulation_state(window: "MainWindow", snapshot: StateSnapshot) -> bool:
        """Push complete simulation state into QML as SI-based payload."""
        if snapshot is None or not window._qml_root_object:
            return False

        payload: Dict[str, Any] | None = None
        try:
            payload = QMLBridge._snapshot_to_payload(snapshot)
            payload.setdefault("animation", {})["isRunning"] = bool(
                getattr(window, "is_simulation_running", False)
            )

            sanitized = QMLBridge._prepare_for_qml(payload)
            window._suppress_qml_feedback = True
            try:
                window._qml_root_object.setProperty(
                    "pendingPythonUpdates",
                    sanitized,
                )
            finally:
                window._suppress_qml_feedback = False
            return True
        except Exception as exc:
            QMLBridge.logger.error(
                "Failed to push simulation state to QML: %s", exc, exc_info=True
            )

            try:
                QMLBridge._log_qml_update_failure(
                    window,
                    context="set_simulation_state",
                    payload=payload or {"snapshot": repr(snapshot)},
                    error=exc,
                )
            except Exception:
                QMLBridge.logger.debug(
                    "Failed to record simulation state failure in event logger",
                    exc_info=True,
                )

            QMLBridge._notify_qml_failure(
                window, "QML не принял состояние симуляции", str(exc)
            )

            return False

    @staticmethod
    def _snapshot_to_payload(snapshot: StateSnapshot) -> Dict[str, Any]:
        """Convert StateSnapshot dataclass into QML-friendly dict.

        Defensive implementation tolerant to missing fields for tests.
        """
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
            wheel_state = (
                getattr(snapshot, "wheels", {}).get(wheel_enum) if snapshot else None
            )
            if not wheel_state:
                continue

            lever_angle = float(getattr(wheel_state, "lever_angle", 0.0))
            piston_position = float(getattr(wheel_state, "piston_position", 0.0))

            wheels_payload[corner_key] = {
                "leverAngle": lever_angle,
                "pistonPosition": piston_position,
                "pistonVelocity": float(getattr(wheel_state, "piston_velocity", 0.0)),
                "joint": {
                    "x": float(getattr(wheel_state, "joint_x", 0.0)),
                    "y": float(getattr(wheel_state, "joint_y", 0.0)),
                    "z": float(getattr(wheel_state, "joint_z", 0.0)),
                },
                "forces": {
                    "pneumatic": float(getattr(wheel_state, "force_pneumatic", 0.0)),
                    "spring": float(getattr(wheel_state, "force_spring", 0.0)),
                    "damper": float(getattr(wheel_state, "force_damper", 0.0)),
                },
            }

            lever_angles[corner_key] = lever_angle
            piston_positions[corner_key] = piston_position

        line_payload: Dict[str, Dict[str, Any]] = {}
        for line_enum in Line:
            line_state = (
                getattr(snapshot, "lines", {}).get(line_enum) if snapshot else None
            )
            if not line_state:
                continue

            key = line_enum.value.lower()
            line_payload[key] = {
                "pressure": float(getattr(line_state, "pressure", 0.0)),
                "temperature": float(getattr(line_state, "temperature", 0.0)),
                "mass": float(getattr(line_state, "mass", 0.0)),
            }

        animation_payload = {
            "timestamp": float(getattr(snapshot, "timestamp", 0.0)),
            "simulationTime": float(getattr(snapshot, "simulation_time", 0.0)),
            "frame": {
                "heave": float(getattr(getattr(snapshot, "frame", {}), "heave", 0.0)),
                "roll": float(getattr(getattr(snapshot, "frame", {}), "roll", 0.0)),
                "pitch": float(getattr(getattr(snapshot, "frame", {}), "pitch", 0.0)),
                "heaveRate": float(
                    getattr(getattr(snapshot, "frame", {}), "heave_rate", 0.0)
                ),
                "rollRate": float(
                    getattr(getattr(snapshot, "frame", {}), "roll_rate", 0.0)
                ),
                "pitchRate": float(
                    getattr(getattr(snapshot, "frame", {}), "pitch_rate", 0.0)
                ),
            },
            "leverAngles": lever_angles,
            "pistonPositions": piston_positions,
            "linePressures": {k: v.get("pressure") for k, v in line_payload.items()},
            "tankPressure": float(
                getattr(getattr(snapshot, "tank", {}), "pressure", 0.0)
            ),
        }

        three_d_payload = {
            "wheels": wheels_payload,
            "lines": line_payload,
            "tank": {
                "pressure": float(
                    getattr(getattr(snapshot, "tank", {}), "pressure", 0.0)
                ),
                "temperature": float(
                    getattr(getattr(snapshot, "tank", {}), "temperature", 0.0)
                ),
            },
            "frame": {
                "heave": float(getattr(getattr(snapshot, "frame", {}), "heave", 0.0)),
                "roll": float(getattr(getattr(snapshot, "frame", {}), "roll", 0.0)),
                "pitch": float(getattr(getattr(snapshot, "frame", {}), "pitch", 0.0)),
            },
        }

        return {"animation": animation_payload, "threeD": three_d_payload}

    # ------------------------------------------------------------------
    # Function Invocation
    # ------------------------------------------------------------------
    @staticmethod
    def invoke_qml_function(
        window: "MainWindow", method_name: str, payload: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Безопасный вызов QML-функции."""
        if not getattr(window, "_qml_root_object", None):
            return False

        try:
            try:
                event_logger = getattr(window, "event_logger", None)
                if event_logger is not None:
                    event_logger.log_qml_invoke(method_name, payload or {})
            except Exception:
                pass

            window._suppress_qml_feedback = True
            try:
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
            finally:
                window._suppress_qml_feedback = False

            return bool(success)
        except Exception as exc:
            QMLBridge.logger.debug("QML call failed: %s - %s", method_name, exc)
            return False

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _make_update_result(
        success: bool,
        detailed: bool,
        error: Optional[str] = None,
        exception: Optional[Exception] = None,
    ) -> Union[bool, QMLUpdateResult]:
        if detailed:
            return QMLUpdateResult(success=success, error=error, exception=exception)
        return success

    @staticmethod
    def _log_qml_update_failure(
        window: "MainWindow", *, context: str, payload: Dict[str, Any], error: Exception
    ) -> None:
        """Записать событие отказа QML в EventLogger."""
        try:
            event_logger = getattr(window, "event_logger", None)
            if event_logger is None:
                return

            event_logger.log_qml_update_failure(
                component="qml_bridge", action=context, payload=payload, error=error
            )
        except Exception:
            QMLBridge.logger.debug(
                "Failed to write QML update failure event", exc_info=True
            )

    @staticmethod
    def _notify_qml_failure(
        window: "MainWindow", message: str, details: Optional[str]
    ) -> None:
        """Отобразить уведомление пользователю об ошибке обновления QML."""
        status_message = message if not details else f"{message}: {details}"

        try:
            status_bar = getattr(window, "status_bar", None)
            if status_bar is not None:
                status_bar.showMessage(status_message, 5000)
        except Exception:
            QMLBridge.logger.debug("Failed to update status bar", exc_info=True)

        if getattr(window, "_suppress_qml_failure_dialog", False):
            return

        if hasattr(window, "show_qml_error_dialog"):
            try:
                window.show_qml_error_dialog(message, details)
                return
            except Exception:
                QMLBridge.logger.debug(
                    "Custom QML error dialog handler failed", exc_info=True
                )

        try:
            from PySide6.QtWidgets import QMessageBox  # type: ignore

            text = message if not details else f"{message}\n\n{details}"
            QMessageBox.critical(window, "QML Update Failure", text)
        except Exception:
            QMLBridge.logger.debug(
                "Failed to show QMessageBox for QML error", exc_info=True
            )

    @staticmethod
    def _prepare_for_qml(value: Any) -> Any:
        """Подготовить данные для передачи в QML."""
        if isinstance(value, dict):
            return {str(k): QMLBridge._prepare_for_qml(v) for k, v in value.items()}

        if isinstance(value, (list, tuple)):
            return [QMLBridge._prepare_for_qml(i) for i in value]

        # NumPy conversion
        try:
            import numpy as np

            if isinstance(value, np.generic):
                return value.item()
            if hasattr(value, "tolist") and callable(value.tolist):
                return QMLBridge._prepare_for_qml(value.tolist())
        except Exception:
            pass

        if isinstance(value, Path):
            return str(value)

        return value

    @staticmethod
    def _deep_merge_dicts(target: Dict[str, Any], source: Dict[str, Any]) -> None:
        for key, value in source.items():
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                QMLBridge._deep_merge_dicts(target[key], value)
            else:
                target[key] = value

    @staticmethod
    def handle_qml_ack(window: "MainWindow", summary: Dict[str, Any]) -> None:
        try:
            QMLBridge.logger.info("QML batch ACK: %s", summary)

            if hasattr(window, "status_bar"):
                window.status_bar.showMessage("Обновления применены в сцене", 1500)

            if window._last_batched_updates:
                try:
                    from ..panels.graphics_logger import get_graphics_logger

                    glog = get_graphics_logger()

                    since_ts = (
                        summary.get("timestamp") if isinstance(summary, dict) else None
                    )

                    for cat, payload in window._last_batched_updates.items():
                        if isinstance(payload, dict) and payload:
                            QMLBridge._log_graphics_change(
                                window, str(cat), payload, applied=True
                            )

                            try:
                                glog.mark_category_changes_applied(
                                    str(cat), since_timestamp=since_ts
                                )
                            except Exception:
                                pass

                    window._last_batched_updates = None
                except Exception:
                    pass
        except Exception:
            # Best effort - don't fail the app on ACK handling
            QMLBridge.logger.debug("handle_qml_ack failed", exc_info=True)

    @staticmethod
    def _log_graphics_change(
        window: "MainWindow", category: str, payload: Dict[str, Any], applied: bool
    ) -> None:
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
