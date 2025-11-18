"""Utilities for wiring Python code to QML update contracts.

Alignment with the renovation plan:

* Master plan: `docs/RENOVATION_MASTER_PLAN.md`, Section 5 "Application
  Architecture Refinement", action item 3 "Signal/Slot Registry".
* Phase playbooks: Phase 3 entries dated 2025-11-05 (Training preset bridge
  regression coverage) and 2025-11-30 (Panel bridge payload coverage) in
  `docs/RENOVATION_PHASE_3_UI_AND_GRAPHICS_PLAN.md`.

These references keep the metadata-driven bridge consistent with the
documented payload and wiring checklists.

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
import copy
import logging
from functools import lru_cache
from pathlib import Path
import time
from typing import TYPE_CHECKING, Any
from collections.abc import Iterable, Mapping, MutableMapping

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

_BATCH_RETRY_LIMIT = 2

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


class QMLBridgeMetadataError(RuntimeError):
    """Raised when the QML bridge metadata cannot be loaded."""


@dataclass(frozen=True)
class QMLSignalSpec:
    """Declarative description of a QML signal ↔ Python handler link."""

    name: str
    handler: str
    connection: str = "auto"
    description: str | None = None

    def resolve_connection_type(self) -> int | None:
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

    update_methods: Mapping[str, tuple[str, ...]]
    qml_signals: tuple[QMLSignalSpec, ...]

    def describe_routes(self) -> dict[str, tuple[str, ...]]:
        """Return a JSON-serialisable view of update categories → methods."""

        return {
            category: tuple(methods)
            for category, methods in self.update_methods.items()
        }


def _load_metadata_from_disk(path: Path) -> QMLBridgeMetadata:
    if not path.exists():
        message = (
            "QML bridge metadata file not found: "
            f"{path}. Ensure the renovation master plan assets are in place."
        )
        _LOGGER.error(message)
        raise QMLBridgeMetadataError(message)

    try:
        with path.open("r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
    except yaml.YAMLError as exc:
        _LOGGER.error("Failed to parse QML bridge metadata %s", path, exc_info=exc)
        raise QMLBridgeMetadataError(
            f"Failed to parse QML bridge metadata: {path}\n{exc}"
        ) from exc
    except OSError as exc:  # pragma: no cover - defensive branch
        _LOGGER.error("Failed to read QML bridge metadata %s", path, exc_info=exc)
        raise QMLBridgeMetadataError(
            f"Failed to read QML bridge metadata: {path}\n{exc}"
        ) from exc

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
def get_bridge_metadata(path: Path | None = None) -> QMLBridgeMetadata:
    """Return cached bridge metadata loaded from disk."""

    target_path = path or _METADATA_PATH
    return _load_metadata_from_disk(target_path)


def describe_routes() -> dict[str, tuple[str, ...]]:
    """Expose update routes for diagnostics overlays and CLI tooling."""

    return get_bridge_metadata().describe_routes()


def register_qml_signals(window: Any, root_object: Any) -> list[QMLSignalSpec]:
    """Connect QML signals described in metadata to Python handlers.

    Args:
        window: Python object (usually ``MainWindow``) containing the handlers.
        root_object: Root QML object exposing the Qt signals.

    Returns:
        List of successfully connected :class:`QMLSignalSpec` instances.
    """

    if root_object is None:
        return []

    connected: list[QMLSignalSpec] = []
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
    error: str | None = None
    exception: Exception | None = None


class QMLBridge:
    """High level helpers coordinating Python↔QML update flows."""

    logger = logging.getLogger(__name__ + ".bridge")

    QML_UPDATE_METHODS: dict[str, tuple[str, ...]] = {
        key: tuple(methods)
        for key, methods in get_bridge_metadata().update_methods.items()
    }

    @staticmethod
    def describe_routes() -> dict[str, tuple[str, ...]]:
        """Return the update categories declared in the metadata."""

        return describe_routes()

    # ------------------------------------------------------------------
    # Queue management
    # ------------------------------------------------------------------
    @staticmethod
    def queue_update(window: MainWindow, key: str, params: dict[str, Any]) -> None:
        """Queue changes for batched delivery to QML."""

        if not params:
            return

        queue: dict[str, dict[str, Any]] = getattr(window, "_qml_update_queue", {})
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
    def flush_updates(window: MainWindow) -> None:
        """Flush queued updates to QML, falling back to per-category calls."""

        queue: dict[str, dict[str, Any]] = getattr(window, "_qml_update_queue", {})
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
        window: MainWindow,
        updates: dict[str, Any],
        *,
        detailed: bool = False,
        raise_on_error: bool = False,
    ) -> bool | QMLUpdateResult:
        """Push a batched payload through ``pendingPythonUpdates``."""

        if not updates:
            return QMLBridge._make_update_result(True, detailed)

        if not getattr(window, "_qml_root_object", None):
            return QMLBridge._make_update_result(False, detailed, "QML root missing")

        try:
            batch_id = QMLBridge._next_batch_id(window)
            try:
                payload = copy.deepcopy(updates)
            except Exception:
                payload = dict(updates)
            sanitized = QMLBridge._prepare_for_qml(payload)
            window._suppress_qml_feedback = True
            try:
                window._qml_root_object.setProperty("pendingPythonUpdates", sanitized)
            finally:
                window._suppress_qml_feedback = False
            QMLBridge._track_pending_batch(window, batch_id, payload)
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
    def set_simulation_state(window: MainWindow, snapshot: StateSnapshot) -> bool:
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
    def _snapshot_to_payload(snapshot: StateSnapshot) -> dict[str, Any]:
        """Convert a :class:`StateSnapshot` into a QML friendly dict."""

        wheel_key_map = {
            Wheel.LP: "fl",
            Wheel.PP: "fr",
            Wheel.LZ: "rl",
            Wheel.PZ: "rr",
        }

        wheels_payload: dict[str, dict[str, Any]] = {}
        lever_angles: dict[str, float] = {}
        piston_positions: dict[str, float] = {}

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

        line_payload: dict[str, dict[str, Any]] = {}
        line_flow_network: dict[str, dict[str, Any]] = {}
        line_magnitudes: dict[str, float] = {}
        for line_enum in Line:
            line_state = getattr(snapshot, "lines", {}).get(line_enum)
            if not line_state:
                continue

            key = line_enum.value.lower()
            pressure = float(getattr(line_state, "pressure", 0.0))
            temperature = float(getattr(line_state, "temperature", 0.0))
            mass = float(getattr(line_state, "mass", 0.0))
            flow_atmo = float(getattr(line_state, "flow_atmo", 0.0))
            flow_tank = float(getattr(line_state, "flow_tank", 0.0))
            net_flow = flow_atmo - flow_tank
            direction = "intake" if net_flow >= 0.0 else "exhaust"
            magnitude = abs(net_flow)
            valves_state = {
                "atmosphereOpen": bool(getattr(line_state, "cv_atmo_open", False)),
                "tankOpen": bool(getattr(line_state, "cv_tank_open", False)),
            }
            flows_state = {
                "fromAtmosphere": flow_atmo,
                "toTank": flow_tank,
                "net": net_flow,
            }
            line_entry = {
                "pressure": pressure,
                "temperature": temperature,
                "mass": mass,
                "flows": flows_state,
                "valves": valves_state,
                "direction": direction,
                "netFlow": net_flow,
                "intensity": magnitude,
                "flowDirection": direction,
                "flowIntensity": magnitude,
            }
            line_payload[key] = line_entry
            line_flow_network[key] = {
                "flows": flows_state,
                "valves": valves_state,
                "direction": direction,
                "netFlow": net_flow,
                "pressure": pressure,
                "temperature": temperature,
                "intensity": magnitude,
            }
            line_magnitudes[key] = magnitude

        max_line_magnitude = max(line_magnitudes.values(), default=0.0)
        line_pressures: dict[str, float] = {}
        if max_line_magnitude > 0.0:
            for line_key, magnitude in line_magnitudes.items():
                speed_ratio = min(max(magnitude / max_line_magnitude, 0.0), 1.0)
                line_payload[line_key]["animationSpeed"] = speed_ratio
                line_flow_network[line_key]["animationSpeed"] = speed_ratio
                line_pressures[line_key] = float(
                    line_payload[line_key].get("pressure", 0.0)
                )
        else:
            for line_key, entry in line_payload.items():
                line_pressures[line_key] = float(entry.get("pressure", 0.0))

        tank_state = getattr(snapshot, "tank", {})
        tank_pressure = float(getattr(tank_state, "pressure", 0.0))
        tank_temperature = float(getattr(tank_state, "temperature", 0.0))
        relief_min_flow = float(getattr(tank_state, "flow_min", 0.0))
        relief_stiff_flow = float(getattr(tank_state, "flow_stiff", 0.0))
        relief_safety_flow = float(getattr(tank_state, "flow_safety", 0.0))
        relief_magnitudes = {
            "min": abs(relief_min_flow),
            "stiff": abs(relief_stiff_flow),
            "safety": abs(relief_safety_flow),
        }
        max_relief_magnitude = max(relief_magnitudes.values(), default=0.0)
        relief_payload = {
            "min": {
                "open": bool(getattr(tank_state, "relief_min_open", False)),
                "flow": relief_min_flow,
                "intensity": relief_magnitudes["min"],
                "direction": "exhaust" if relief_min_flow >= 0 else "intake",
            },
            "stiff": {
                "open": bool(getattr(tank_state, "relief_stiff_open", False)),
                "flow": relief_stiff_flow,
                "intensity": relief_magnitudes["stiff"],
                "direction": "exhaust" if relief_stiff_flow >= 0 else "intake",
            },
            "safety": {
                "open": bool(getattr(tank_state, "relief_safety_open", False)),
                "flow": relief_safety_flow,
                "intensity": relief_magnitudes["safety"],
                "direction": "exhaust" if relief_safety_flow >= 0 else "intake",
            },
        }
        if max_relief_magnitude > 0.0:
            for relief_key, magnitude in relief_magnitudes.items():
                relief_payload[relief_key]["animationSpeed"] = min(
                    max(magnitude / max_relief_magnitude, 0.0), 1.0
                )
        tank_flow_summary = {
            "min": relief_min_flow,
            "stiff": relief_stiff_flow,
            "safety": relief_safety_flow,
            "total": relief_min_flow + relief_stiff_flow + relief_safety_flow,
        }
        tank_valves_state = {
            "min": relief_payload["min"]["open"],
            "stiff": relief_payload["stiff"]["open"],
            "safety": relief_payload["safety"]["open"],
        }
        master_isolation_open = bool(getattr(snapshot, "master_isolation_open", False))

        min_line_pressure = (
            min(line_pressures.values()) if line_pressures else tank_pressure
        )
        max_line_pressure = (
            max(line_pressures.values()) if line_pressures else tank_pressure
        )

        receiver_payload = {
            "pressures": line_pressures,
            "tankPressure": tank_pressure,
            "minPressure": min_line_pressure,
            "maxPressure": max_line_pressure,
        }

        check_valves_payload: dict[str, dict[str, Any]] = {}
        for key, entry in line_flow_network.items():
            valves = entry.get("valves", {}) if isinstance(entry, dict) else {}
            check_valves_payload[key] = {
                "atmosphereOpen": bool(valves.get("atmosphereOpen")),
                "tankOpen": bool(valves.get("tankOpen")),
                "netFlow": float(entry.get("netFlow", 0.0))
                if isinstance(entry, dict)
                else 0.0,
                "direction": entry.get("direction", "intake")
                if isinstance(entry, dict)
                else "intake",
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
            "tankPressure": tank_pressure,
        }

        three_d_payload = {
            "wheels": wheels_payload,
            "lines": line_payload,
            "tank": {
                "pressure": tank_pressure,
                "temperature": tank_temperature,
                "flows": tank_flow_summary,
                "valves": tank_valves_state,
            },
            "frame": {
                "heave": float(getattr(getattr(snapshot, "frame", {}), "heave", 0.0)),
                "roll": float(getattr(getattr(snapshot, "frame", {}), "roll", 0.0)),
                "pitch": float(getattr(getattr(snapshot, "frame", {}), "pitch", 0.0)),
            },
            "valves": {
                "relief": relief_payload,
                "check": check_valves_payload,
                "masterIsolationOpen": master_isolation_open,
            },
            "flowNetwork": {
                "lines": line_flow_network,
                "relief": relief_payload,
                "tank": {
                    "pressure": tank_pressure,
                    "temperature": tank_temperature,
                    "flows": tank_flow_summary,
                    "valves": tank_valves_state,
                },
                "receiver": receiver_payload,
                "masterIsolationOpen": master_isolation_open,
                "maxLineIntensity": max_line_magnitude,
                "maxReliefIntensity": max_relief_magnitude,
                "timestamp": float(getattr(snapshot, "simulation_time", 0.0)),
            },
            "receiver": receiver_payload,
        }

        return {"animation": animation_payload, "threeD": three_d_payload}

    # ------------------------------------------------------------------
    # Function invocation
    # ------------------------------------------------------------------
    @staticmethod
    def invoke_qml_function(
        window: MainWindow, method_name: str, payload: dict[str, Any] | None = None
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

    @staticmethod
    def trigger_undo_post_effects(
        window: MainWindow, payload: dict[str, Any] | None = None
    ) -> bool:
        """Request QML to roll back post-processing settings."""

        return QMLBridge.invoke_qml_function(window, "undoPostEffects", payload)

    @staticmethod
    def trigger_reset_shared_materials(window: MainWindow) -> bool:
        """Request QML to refresh shared materials from snapshots."""

        return QMLBridge.invoke_qml_function(window, "resetSharedMaterials")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _make_update_result(
        success: bool,
        detailed: bool,
        error: str | None = None,
        exception: Exception | None = None,
    ) -> bool | QMLUpdateResult:
        if detailed:
            return QMLUpdateResult(success=success, error=error, exception=exception)
        return success

    @staticmethod
    def _log_qml_update_failure(
        window: MainWindow, *, context: str, payload: dict[str, Any], error: Exception
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
        window: MainWindow, message: str, details: str | None
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
    def _next_batch_id(window: MainWindow) -> int:
        current = int(getattr(window, "_qml_batch_sequence", 0)) + 1
        window._qml_batch_sequence = current
        return current

    @staticmethod
    def _track_pending_batch(
        window: MainWindow, batch_id: int, payload: dict[str, Any]
    ) -> None:
        try:
            stored_payload = copy.deepcopy(payload)
        except Exception:
            stored_payload = dict(payload)

        window._pending_batch_ack = {
            "batch_id": batch_id,
            "payload": stored_payload,
            "retries_left": _BATCH_RETRY_LIMIT,
            "issued_at": time.time(),
        }

    @staticmethod
    def _extract_ack_components(
        summary: dict[str, Any],
    ) -> tuple[int | None, dict[str, str], set[str], bool | None]:
        batch_id: int | None = None
        failed: dict[str, str] = {}
        unknown: set[str] = set()
        success_flag: bool | None = None

        if isinstance(summary, Mapping):
            raw_failed = summary.get("failed")
            if isinstance(raw_failed, Mapping):
                failed = {
                    str(key): (str(value) if value is not None else "")
                    for key, value in raw_failed.items()
                }

            raw_unknown = summary.get("unknownKeys")
            if isinstance(raw_unknown, (list, tuple, set)):
                unknown = {
                    str(item)
                    for item in raw_unknown
                    if item is not None and str(item) != ""
                }

            meta_candidates: list[Any | None] = []
            raw_meta = summary.get("meta") or summary.get("_meta")
            if isinstance(raw_meta, Mapping):
                meta_candidates.extend(
                    [raw_meta.get("batchId"), raw_meta.get("batch_id")]
                )
            meta_candidates.extend([summary.get("batchId"), summary.get("batch_id")])

            for candidate in meta_candidates:
                if candidate is None:
                    continue
                try:
                    batch_id = int(candidate)
                    break
                except (TypeError, ValueError):
                    continue

            success_value = summary.get("success")
            if isinstance(success_value, bool):
                success_flag = success_value

        return batch_id, failed, unknown, success_flag

    @staticmethod
    def _process_ack_retry(
        window: MainWindow, summary: dict[str, Any]
    ) -> tuple[bool, bool, dict[str, str], set[str], bool]:
        pending = getattr(window, "_pending_batch_ack", None)
        batch_id, failed, unknown, success_flag = QMLBridge._extract_ack_components(
            summary
        )

        ack_success = not failed and not unknown and success_flag is not False

        if not pending:
            return ack_success, False, failed, unknown, True

        expected_id = pending.get("batch_id")
        if batch_id is not None and expected_id is not None and batch_id != expected_id:
            QMLBridge.logger.debug(
                "Ignoring ACK for batch %s while waiting for %s",
                batch_id,
                expected_id,
            )
            return ack_success, False, failed, unknown, False

        has_failures = bool(failed) or bool(unknown) or success_flag is False
        if not has_failures:
            window._pending_batch_ack = None
            return True, False, failed, unknown, True

        retries_left = int(pending.get("retries_left", 0))
        if retries_left > 0:
            pending["retries_left"] = retries_left - 1
            categories = set(failed.keys()) | set(unknown)
            payload: Mapping[str, Any] = pending.get("payload", {})
            for category in categories:
                category_payload = payload.get(category)
                if not category_payload:
                    continue
                try:
                    retry_payload = copy.deepcopy(category_payload)
                except Exception:
                    retry_payload = dict(category_payload)
                QMLBridge.queue_update(window, category, retry_payload)

            window._pending_batch_ack = pending
            QMLBridge.logger.warning(
                "Retrying batch %s (%d retries left) after ACK failure: failed=%s unknown=%s",
                expected_id,
                pending.get("retries_left", 0),
                sorted(failed.keys()),
                sorted(unknown),
            )
            return False, True, failed, unknown, True

        window._pending_batch_ack = None
        QMLBridge.logger.error(
            "Batched update %s failed after retries: %s", expected_id, failed
        )
        if unknown:
            QMLBridge.logger.error(
                "Unhandled batch categories for %s: %s", expected_id, sorted(unknown)
            )
        return False, False, failed, unknown, True

    @staticmethod
    def _prepare_for_qml(value: Any) -> Any:
        """Normalise Python objects so they can be passed into QML."""

        if isinstance(value, dict):
            result: dict[str, Any] = {}
            for key, raw in value.items():
                prepared = QMLBridge._prepare_for_qml(raw)
                str_key = str(key)
                result[str_key] = prepared

                camel_key = QMLBridge._snake_to_camel(str_key)
                if camel_key != str_key and camel_key not in result:
                    result[camel_key] = prepared

            return result

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
    def _snake_to_camel(key: str) -> str:
        if "_" not in key:
            return key

        parts = [segment for segment in key.split("_") if segment]
        if not parts:
            return key

        head, *tail = parts
        return head + "".join(part[:1].upper() + part[1:] for part in tail)

    @staticmethod
    def _deep_merge_dicts(target: dict[str, Any], source: dict[str, Any]) -> None:
        for key, value in source.items():
            if isinstance(value, dict) and isinstance(target.get(key), dict):
                QMLBridge._deep_merge_dicts(target[key], value)
            else:
                target[key] = value

    @staticmethod
    def handle_qml_ack(window: MainWindow, summary: dict[str, Any]) -> None:
        """Handle acknowledgement payloads emitted from QML."""

        try:
            QMLBridge.logger.info("QML batch ACK: %s", summary)

            ack_success, retried, failed, unknown, matched = (
                QMLBridge._process_ack_retry(window, summary)
            )

            status_bar = getattr(window, "status_bar", None)
            if status_bar is not None:
                if ack_success:
                    status_bar.showMessage("Обновления применены в сцене", 1500)
                elif retried:
                    status_bar.showMessage(
                        "Повторная отправка обновлений в сцену…", 2000
                    )
                else:
                    status_bar.showMessage(
                        "Не удалось применить обновления в сцене", 4000
                    )

            if ack_success and matched and window._last_batched_updates:
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
            elif retried:
                QMLBridge.logger.debug(
                    "Batched update retry scheduled due to failures: %s", failed
                )
            elif (failed or unknown) and matched:
                QMLBridge.logger.error(
                    "QML reported batch failure without retry: failed=%s unknown=%s",
                    failed,
                    sorted(unknown),
                )
        except Exception:  # pragma: no cover - diagnostics best effort
            QMLBridge.logger.debug("handle_qml_ack failed", exc_info=True)

    @staticmethod
    def _log_graphics_change(
        window: MainWindow, category: str, payload: dict[str, Any], applied: bool
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
