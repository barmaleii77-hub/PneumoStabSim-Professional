"""Central metadata-driven helpers for the Python↔QML bridge.

This module is responsible for turning the declarative metadata stored in
``config/qml_bridge.yaml`` into runtime helpers that the rest of the
application can consume.  It exposes three primary capabilities:

* ``get_bridge_metadata`` – cached access to the parsed metadata.
* ``register_qml_signals`` – convenience helper that hooks QML signals
  defined in the metadata to Python handlers on the main window.
* ``describe_routes`` – lightweight introspection structure for diagnostics
  overlays and CLI tools.

The implementation is intentionally free of Qt specific imports at module load
so that unit tests can exercise the metadata layer without PySide6 installed.
Qt types are only imported when ``register_qml_signals`` is executed at
runtime.
"""

from __future__ import annotations

from dataclasses import dataclass
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, MutableMapping, Optional, Tuple

import yaml

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
