# -*- coding: utf-8 -*-
"""Utilities for wiring Python code to QML update contracts.

The module provides several layers of functionality:

* :func:`get_bridge_metadata` – cached access to the parsed metadata file.
* :func:`register_qml_signals` – convenience helper that hooks QML signals
  defined in the metadata to Python handlers on the main window.
* :func:`describe_routes` – lightweight introspection structure for
  diagnostics overlays and CLI tools.
* :class:`QMLBridge` – batching helpers used by
  :class:`~src.ui.main_window.MainWindow`.

The implementation avoids importing Qt types at module load time so that unit
tests can exercise the metadata layer without PySide6 installed. Qt classes
are imported lazily when ``register_qml_signals`` or bridge helpers are
executed at runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from functools import lru_cache
from pathlib import Path
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Iterable,
    List,
    Mapping,
    MutableMapping,
    Optional,
    Tuple,
    Union,
)

import yaml

try:
    from PySide6.QtCore import Q_ARG, QMetaObject, Qt
except Exception:  # pragma: no cover - fallback for headless environments

    class _DummyQt:
        class ConnectionType:
            DirectConnection = 0

    class _DummyQMetaObject:
        @staticmethod
        def invokeMethod(*_args: Any, **_kwargs: Any) -> bool:
            return False

    def Q_ARG(*_args: Any, **_kwargs: Any) -> None:  # type: ignore[override]
        return None

    QMetaObject = _DummyQMetaObject  # type: ignore[assignment]
    Qt = _DummyQt()  # type: ignore[assignment]

from src.pneumo.enums import Line, Wheel
from src.runtime.state import StateSnapshot

if TYPE_CHECKING:  # pragma: no cover - imported only for typing
    from .main_window import MainWindow

_LOGGER = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
_METADATA_CANDIDATES = (
    _PROJECT_ROOT / "config" / "qml_bridge.yaml",
    Path(__file__).resolve().parents[1] / "config" / "qml_bridge.yaml",
)
for _candidate in _METADATA_CANDIDATES:
    if _candidate.exists():
        _METADATA_PATH = _candidate
        break
else:  # pragma: no cover - exercised only when metadata is missing
    _METADATA_PATH = _METADATA_CANDIDATES[0]


@dataclass(frozen=True)
class QMLSignalSpec:
    """Declarative description of a QML signal ↔ Python handler link."""

    name: str
    handler: str
    connection: str = "auto"
    description: Optional[str] = None

    def resolve_connection_type(self) -> Optional[int]:
        """Translate the textual connection hint into a Qt constant.

        The helper imports :mod:`PySide6.QtCore` lazily to avoid binding Qt when
        the metadata is merely inspected (e.g. by tests).  Unknown connection
        names default to ``None`` which lets Qt choose the strategy.
        """

        normalized = (self.connection or "auto").strip().lower()
        if normalized in {"auto", "default", ""}:
            return None

        try:  # Import lazily to keep module importable without PySide6.
            from PySide6.QtCore import Qt  # type: ignore
        except Exception:  # pragma: no cover - executed only in headless tests
            _LOGGER.debug(
                "Qt connection type %s requested but PySide6 is unavailable", normalized
            )
            return None

        mapping = {
            "direct": getattr(Qt, "DirectConnection", None),
            "queued": getattr(Qt, "QueuedConnection", None),
            "blocking": getattr(Qt, "BlockingQueuedConnection", None),
            "auto": None,
            "default": None,
        }
        resolved = mapping.get(normalized)
        if resolved is None and normalized not in {"auto", "default"}:
            _LOGGER.warning("Unknown Qt connection type hint: %s", normalized)
        return resolved


@dataclass(frozen=True)
class QMLBridgeMetadata:
    """Structured representation of the bridge metadata."""

    update_methods: Mapping[str, Tuple[str, ...]]
    qml_signals: Tuple[QMLSignalSpec, ...]

    def describe_routes(self) -> Dict[str, Tuple[str, ...]]:
        """Return a JSON-serialisable view of update categories → methods."""

        return {
            category: tuple(methods)
            for category, methods in self.update_methods.items()
        }


def _load_metadata_from_disk(path: Path) -> QMLBridgeMetadata:
    if not path.exists():
        raise FileNotFoundError(
            f"QML bridge metadata file not found: {path}. "
            "Ensure the renovation master plan assets are in place."
        )

    with path.open("r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}

    update_methods_raw: MutableMapping[str, Iterable[str]] = {
        str(key): tuple(str(item) for item in value or ())
        for key, value in (raw.get("update_methods") or {}).items()
    }

    qml_signals_raw = []
    for entry in raw.get("qml_signals", []) or []:
        if not isinstance(entry, Mapping):
            _LOGGER.warning("Skipping malformed qml_signals entry: %r", entry)
            continue
        qml_signals_raw.append(
            QMLSignalSpec(
                name=str(entry.get("signal", "")).strip(),
                handler=str(entry.get("handler", "")).strip(),
                connection=str(entry.get("connection", "auto")),
                description=entry.get("description"),
            )
        )

    cleaned_signals = tuple(
        signal for signal in qml_signals_raw if signal.name and signal.handler
    )
    return QMLBridgeMetadata(
        update_methods=dict(update_methods_raw), qml_signals=cleaned_signals
    )


@lru_cache(maxsize=1)
def get_bridge_metadata(path: Optional[Path] = None) -> QMLBridgeMetadata:
    """Return cached bridge metadata loaded from disk."""

    target_path = path or _METADATA_PATH
    return _load_metadata_from_disk(target_path)


def describe_routes() -> Dict[str, Tuple[str, ...]]:
    """Expose update routes for diagnostics overlays and CLI tooling."""

    return get_bridge_metadata().describe_routes()


def register_qml_signals(window: Any, root_object: Any) -> List[QMLSignalSpec]:
    """Connect QML signals described in metadata to Python handlers.

    Args:
        window: Python object (usually ``MainWindow``) containing the handlers.
        root_object: Root QML object exposing the Qt signals.

    Returns:
        List of successfully connected :class:`QMLSignalSpec` instances.
    """

    if root_object is None:
        return []

    connected: List[QMLSignalSpec] = []
    for spec in get_bridge_metadata().qml_signals:
        signal_obj = getattr(root_object, spec.name, None)
        handler = getattr(window, spec.handler, None)
        if signal_obj is None:
            _LOGGER.warning("QML root does not expose signal '%s'", spec.name)
            continue
        if handler is None:
            _LOGGER.warning(
                "Window missing handler '%s' for signal '%s'", spec.handler, spec.name
            )
            continue

        try:
            connection_type = spec.resolve_connection_type()
            if connection_type is None:
                signal_obj.connect(handler)
            else:
                signal_obj.connect(handler, connection_type)
        except Exception as exc:  # pragma: no cover - depends on runtime Qt
            _LOGGER.error(
                "Failed to connect QML signal '%s' to handler '%s': %s",
                spec.name,
                spec.handler,
                exc,
            )
            continue

        connected.append(spec)
        _LOGGER.debug(
            "Connected QML signal '%s' to '%s' with connection=%s",
            spec.name,
            spec.handler,
            spec.connection,
        )

    return connected


class QMLUpdateError(RuntimeError):
    """Raised when a batched QML update fails fatally."""


@dataclass(slots=True)
class QMLUpdateResult:
    """Structured result describing the outcome of a QML update push."""

    success: bool
    error: Optional[str] = None
    exception: Optional[Exception] = None


class QMLBridge:
    """High level helpers coordinating Python↔QML update flows."""

    logger = logging.getLogger(__name__ + ".bridge")

    QML_UPDATE_METHODS: Dict[str, tuple[str, ...]] = {
        key: tuple(methods)
        for key, methods in get_bridge_metadata().update_methods.items()
    }

    @staticmethod
    def describe_routes() -> Dict[str, tuple[str, ...]]:
        """Return the update categories declared in the metadata."""

        return describe_routes()

    # ------------------------------------------------------------------
    # Queue management
    # ------------------------------------------------------------------
    @staticmethod
    def queue_update(window: "MainWindow", key: str, params: Dict[str, Any]) -> None:
        """Queue changes for batched delivery to QML."""

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
            except Exception:  # pragma: no cover - Qt specific failure
                pass

    @staticmethod
    def flush_updates(window: "MainWindow") -> None:
        """Flush queued updates to QML, falling back to per-category calls."""

        queue: Dict[str, Dict[str, Any]] = getattr(window, "_qml_update_queue", {})
        if not queue:
            return

        if not getattr(window, "_qml_root_object", None):
            timer = getattr(window, "_qml_flush_timer", None)
            if timer is not None:
                try:
                    timer.start(100)
                except Exception:  # pragma: no cover - Qt specific failure
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
        """Push a batched payload through ``pendingPythonUpdates``."""

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
        except Exception as exc:  # pragma: no cover - Qt specific failure
            QMLBridge.logger.error(
                "Failed to push batched updates to QML: %s", exc, exc_info=True
            )

            try:
                QMLBridge._log_qml_update_failure(
                    window, context="flush_updates", payload=updates, error=exc
                )
            except Exception:  # pragma: no cover - diagnostics best effort
                QMLBridge.logger.debug(
                    "Failed to record qml update failure into event logger",
                    exc_info=True,
                )

            if raise_on_error:
                raise QMLUpdateError("QML rejected batched updates") from exc

            return QMLBridge._make_update_result(False, detailed, str(exc), exc)

    # ------------------------------------------------------------------
    # Simulation state synchronisation
    # ------------------------------------------------------------------
    @staticmethod
    def set_simulation_state(window: "MainWindow", snapshot: StateSnapshot) -> bool:
        """Push an entire :class:`StateSnapshot` into QML."""

        if snapshot is None or not getattr(window, "_qml_root_object", None):
            return False

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
        except Exception as exc:  # pragma: no cover - Qt specific failure
            QMLBridge.logger.error(
                "Failed to push simulation state to QML", exc_info=True
            )
            try:
                QMLBridge._log_qml_update_failure(
                    window,
                    context="set_simulation_state",
                    payload={"error": str(exc)},
                    error=exc,
                )
            except Exception:
                QMLBridge.logger.debug(
                    "Failed to record simulation state failure", exc_info=True
                )
            QMLBridge._notify_qml_failure(
                window,
                "QML не принял состояние симуляции",
                str(exc),
            )
            return False

    @staticmethod
    def _snapshot_to_payload(snapshot: StateSnapshot) -> Dict[str, Any]:
        """Convert a :class:`StateSnapshot` into a QML friendly dict."""

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
            wheel_state = getattr(snapshot, "wheels", {}).get(wheel_enum)
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
            line_state = getattr(snapshot, "lines", {}).get(line_enum)
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
    # Function invocation
    # ------------------------------------------------------------------
    @staticmethod
    def invoke_qml_function(
        window: "MainWindow", method_name: str, payload: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Safely invoke a QML method, logging failures at debug level."""

        if not getattr(window, "_qml_root_object", None):
            return False

        try:
            try:
                event_logger = getattr(window, "event_logger", None)
                if event_logger is not None:
                    event_logger.log_qml_invoke(method_name, payload or {})
            except Exception:  # pragma: no cover - diagnostics best effort
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
        except Exception as exc:  # pragma: no cover - Qt specific failure
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
        """Record failures in the diagnostic event logger."""

        try:
            event_logger = getattr(window, "event_logger", None)
            if event_logger is None:
                return

            event_logger.log_qml_update_failure(
                component="qml_bridge", action=context, payload=payload, error=error
            )
        except Exception:  # pragma: no cover - diagnostics best effort
            QMLBridge.logger.debug(
                "Failed to write QML update failure event", exc_info=True
            )

    @staticmethod
    def _notify_qml_failure(
        window: "MainWindow", message: str, details: Optional[str]
    ) -> None:
        """Surface a user-visible notification about a QML error."""

        status_message = message if not details else f"{message}: {details}"

        try:
            status_bar = getattr(window, "status_bar", None)
            if status_bar is not None:
                status_bar.showMessage(status_message, 5000)
        except Exception:  # pragma: no cover - Qt specific failure
            QMLBridge.logger.debug("Failed to update status bar", exc_info=True)

        if getattr(window, "_suppress_qml_failure_dialog", False):
            return

        if hasattr(window, "show_qml_error_dialog"):
            try:
                window.show_qml_error_dialog(message, details)
                return
            except Exception:  # pragma: no cover - diagnostics best effort
                QMLBridge.logger.debug(
                    "Custom QML error dialog handler failed", exc_info=True
                )

        try:
            from PySide6.QtWidgets import QMessageBox  # type: ignore

            text = message if not details else f"{message}\n\n{details}"
            QMessageBox.critical(window, "QML Update Failure", text)
        except Exception:  # pragma: no cover - Qt specific failure
            QMLBridge.logger.debug(
                "Failed to show QMessageBox for QML error", exc_info=True
            )

    @staticmethod
    def _prepare_for_qml(value: Any) -> Any:
        """Normalise Python objects so they can be passed into QML."""

        if isinstance(value, dict):
            return {str(k): QMLBridge._prepare_for_qml(v) for k, v in value.items()}

        if isinstance(value, (list, tuple)):
            return [QMLBridge._prepare_for_qml(i) for i in value]

        try:  # NumPy conversion support
            import numpy as np

            if isinstance(value, np.generic):
                return value.item()
            if hasattr(value, "tolist") and callable(value.tolist):
                return QMLBridge._prepare_for_qml(value.tolist())
        except Exception:  # pragma: no cover - optional dependency
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
        """Handle acknowledgement payloads emitted from QML."""

        try:
            QMLBridge.logger.info("QML batch ACK: %s", summary)

            if hasattr(window, "status_bar"):
                window.status_bar.showMessage("Обновления применены в сцене", 1500)

            if window._last_batched_updates:
                try:
                    from .panels.graphics_logger import get_graphics_logger

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
                            except (
                                Exception
                            ):  # pragma: no cover - diagnostics best effort
                                pass

                    window._last_batched_updates = None
                except Exception:  # pragma: no cover - diagnostics best effort
                    pass
        except Exception:  # pragma: no cover - diagnostics best effort
            QMLBridge.logger.debug("handle_qml_ack failed", exc_info=True)

    @staticmethod
    def _log_graphics_change(
        window: "MainWindow", category: str, payload: Dict[str, Any], applied: bool
    ) -> None:
        try:
            from .panels.graphics_logger import get_graphics_logger

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
        except Exception:  # pragma: no cover - diagnostics best effort
            pass


__all__ = [
    "QMLBridge",
    "QMLBridgeMetadata",
    "QMLSignalSpec",
    "QMLUpdateError",
    "QMLUpdateResult",
    "describe_routes",
    "get_bridge_metadata",
    "register_qml_signals",
]
