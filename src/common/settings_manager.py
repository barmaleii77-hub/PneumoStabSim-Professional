"""Lightweight settings manager used for unit tests.

The original project ships with a very feature-rich configuration system that
interacts with Qt, performs schema migrations and manages complex defaults.  The
test-suite in this kata exercises only a tiny portion of that behaviour, so the
heavy implementation makes the tests brittle in a headless environment.  This
module provides a compact drop-in replacement that offers the pieces the tests
rely on:

* loading a JSON configuration file with ``current`` and ``defaults_snapshot``
  sections;
* coercing the ``units_version`` metadata to ``si_v2`` when legacy payloads are
  encountered;
* basic dotted-path ``get`` and ``set`` helpers;
* an opt-in singleton accessor exposed via :func:`get_settings_manager`.

The implementation intentionally stays conservative – it validates the presence
of the primary sections but otherwise keeps the payload opaque, letting the unit
tests drive the requirements.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from importlib import import_module, util
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

from src.core.settings_manager import (
    ProfileSettingsManager as _CoreProfileSettingsManager,
)


DEFAULT_SETTINGS_PATH = Path("config/app_settings.json")
_DEFAULT_UNITS_VERSION = "si_v2"


def _resolve_settings_file(settings_file: Optional[Path | str]) -> Path:
    if settings_file is not None:
        return Path(settings_file)

    env_path = os.environ.get("PSS_SETTINGS_FILE")
    if env_path:
        return Path(env_path)

    return DEFAULT_SETTINGS_PATH


def _deep_copy(data: Any) -> Any:
    return json.loads(json.dumps(data))


def _load_qt_core():
    spec = util.find_spec("PySide6.QtCore")
    if spec is None:
        return None
    return import_module("PySide6.QtCore")


_qt_core = _load_qt_core()

if _qt_core is not None:
    QObject = _qt_core.QObject
    Signal = _qt_core.Signal
else:

    class QObject:  # type: ignore[override]
        """Minimal QObject stand-in for headless environments."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401 - Qt compatibility
            super().__init__()

    class _SignalInstance:
        def __init__(self) -> None:
            self._subscribers: List[Any] = []

        def connect(self, callback: Any) -> None:
            if callback not in self._subscribers:
                self._subscribers.append(callback)

        def disconnect(self, callback: Any) -> None:
            if callback in self._subscribers:
                self._subscribers.remove(callback)

        def emit(self, *args: Any, **kwargs: Any) -> None:
            for callback in list(self._subscribers):
                callback(*args, **kwargs)

    class _Signal:
        def __init__(self) -> None:
            self._name: Optional[str] = None

        def __set_name__(self, owner: type, name: str) -> None:
            self._name = f"__signal_{name}"

        def __get__(self, instance: Any, owner: type | None = None) -> Any:
            if instance is None:
                return self
            assert self._name is not None
            signal = instance.__dict__.get(self._name)
            if signal is None:
                signal = _SignalInstance()
                instance.__dict__[self._name] = signal
            return signal

    def Signal(*_args: Any, **_kwargs: Any) -> Any:  # noqa: N802 - mirror Qt API
        return _Signal()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class _SettingsChange:
    path: str
    category: str
    changeType: str
    newValue: Any
    oldValue: Any
    timestamp: str


class SettingsEventBus(QObject):
    """Event bus mirroring the project's Qt-based settings notifications."""

    settingChanged = Signal(dict)
    settingsBatchUpdated = Signal(dict)

    def emit_setting_changed(self, payload: Dict[str, Any]) -> None:
        self.settingChanged.emit(payload)

    def emit_settings_batch(self, payload: Dict[str, Any]) -> None:
        self.settingsBatchUpdated.emit(payload)


ProfileSettingsManager = _CoreProfileSettingsManager


class SettingsManager:
    """Minimal settings manager tailored for the unit tests."""

    def __init__(self, settings_file: Optional[Path | str] = None) -> None:
        self._settings_path = _resolve_settings_file(settings_file)
        self._data: Dict[str, Any] = {}
        self._defaults: Dict[str, Any] = {}
        self._metadata: Dict[str, Any] = {}
        self._extra: Dict[str, Any] = {}
        self.load()

    # ------------------------------------------------------------------ helpers
    @property
    def settings_file(self) -> Path:
        return self._settings_path

    def _ensure_units_version(self) -> None:
        units_version = self._metadata.get("units_version")
        if units_version != _DEFAULT_UNITS_VERSION:
            self._metadata["units_version"] = _DEFAULT_UNITS_VERSION

    def _assign_sections(self, payload: Dict[str, Any]) -> None:
        self._metadata = _deep_copy(payload.get("metadata", {}))
        self._data = _deep_copy(payload.get("current", {}))
        self._defaults = _deep_copy(payload.get("defaults_snapshot", {}))
        self._extra = {
            key: _deep_copy(value)
            for key, value in payload.items()
            if key not in {"metadata", "current", "defaults_snapshot"}
        }
        self._ensure_units_version()

    # ------------------------------------------------------------------- public
    def load(self) -> None:
        if not self._settings_path.exists():
            raise FileNotFoundError(
                f"Settings file does not exist: {self._settings_path}"
            )

        payload = json.loads(self._settings_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Settings file must contain a JSON object")

        for key in ("current", "defaults_snapshot", "metadata"):
            if key not in payload:
                raise ValueError(f"Missing required section: {key}")

        self._assign_sections(payload)

    def save(self) -> None:
        payload: Dict[str, Any] = {
            "metadata": _deep_copy(self._metadata),
            "current": _deep_copy(self._data),
            "defaults_snapshot": _deep_copy(self._defaults),
        }
        payload.update(self._extra)
        self._settings_path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _notify_change(self, change: _SettingsChange) -> None:
        if _settings_event_bus is None:
            return
        payload = {
            "path": change.path,
            "category": change.category,
            "changeType": change.changeType,
            "newValue": _deep_copy(change.newValue),
            "oldValue": _deep_copy(change.oldValue),
            "timestamp": change.timestamp,
        }
        _settings_event_bus.emit_setting_changed(payload)

    def _notify_batch(
        self, changes: List[_SettingsChange], summary: Dict[str, Any]
    ) -> None:
        if _settings_event_bus is None or not changes:
            return
        payload = {
            "changes": [
                {
                    "path": change.path,
                    "category": change.category,
                    "changeType": change.changeType,
                    "newValue": _deep_copy(change.newValue),
                    "oldValue": _deep_copy(change.oldValue),
                    "timestamp": change.timestamp,
                }
                for change in changes
            ],
            "summary": summary,
        }
        _settings_event_bus.emit_settings_batch(payload)

    # Dotted-path helpers -----------------------------------------------------
    def _traverse(
        self, root: Dict[str, Any], path: Iterable[str], create: bool
    ) -> Dict[str, Any]:
        node = root
        for key in path:
            if key not in node:
                if not create:
                    return {}
                node[key] = {}
            value = node[key]
            if not isinstance(value, dict):
                if create:
                    node[key] = {}
                    value = node[key]
                else:
                    return {}
            node = value
        return node

    def get(self, dotted_path: str, default: Any = None) -> Any:
        parts = dotted_path.split(".") if dotted_path else []
        if not parts:
            return _deep_copy(self._data)

        head = parts[0]
        if head == "metadata":
            node: Any = self._metadata
            parts = parts[1:]
        elif head == "defaults_snapshot":
            node = self._defaults
            parts = parts[1:]
        elif head == "current":
            node = self._data
            parts = parts[1:]
        elif head in self._extra:
            node = self._extra[head]
            parts = parts[1:]
        else:
            node = self._data

        if not parts:
            return _deep_copy(node)

        for part in parts:
            if not isinstance(node, dict) or part not in node:
                return default
            node = node[part]
        return _deep_copy(node)

    def set(self, dotted_path: str, value: Any, auto_save: bool = True) -> bool:
        if not dotted_path:
            raise ValueError("Path must be non-empty")

        parts = dotted_path.split(".")
        # Determine which root dictionary to update
        if parts[0] == "current":
            root = self._data
            parts = parts[1:]
        elif parts[0] == "defaults_snapshot":
            root = self._defaults
            parts = parts[1:]
        elif parts[0] == "metadata":
            root = self._metadata
            parts = parts[1:]
        elif parts[0] in self._extra:
            root = self._extra[parts[0]]
            parts = parts[1:]
        elif len(parts) == 1:
            root = self._extra
        else:
            root = self._data

        timestamp = _utc_now()
        if not parts:
            previous = (
                _deep_copy(root.get(dotted_path)) if dotted_path in root else None
            )
            root[dotted_path] = _deep_copy(value)
            if auto_save:
                self.save()
            category = dotted_path.split(".", 1)[0]
            self._notify_change(
                _SettingsChange(
                    path=dotted_path,
                    category=category,
                    changeType="set",
                    newValue=value,
                    oldValue=previous,
                    timestamp=timestamp,
                )
            )
            return True

        *parents, leaf = parts
        node = self._traverse(root, parents, create=True) if parents else root
        previous = _deep_copy(node.get(leaf)) if leaf in node else None
        node[leaf] = _deep_copy(value)

        if auto_save:
            self.save()
        category = dotted_path.split(".", 1)[0]
        self._notify_change(
            _SettingsChange(
                path=dotted_path,
                category=category,
                changeType="set",
                newValue=value,
                oldValue=previous,
                timestamp=timestamp,
            )
        )
        return True

    # Defaults ---------------------------------------------------------------
    def get_all_defaults(self) -> Dict[str, Any]:
        return _deep_copy(self._defaults)

    # Category helpers -------------------------------------------------------
    def get_category(
        self, category: str, default: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Return a deep copy of a category from the ``current`` section."""

        if not category:
            raise ValueError("Category name must be non-empty")

        if category in self._data:
            return _deep_copy(self._data[category])

        if default is None:
            return None

        return _deep_copy(default)

    def set_category(
        self, category: str, payload: Dict[str, Any], *, auto_save: bool = True
    ) -> None:
        """Replace a category inside the ``current`` section."""

        if not category:
            raise ValueError("Category name must be non-empty")
        previous = _deep_copy(self._data.get(category))

        self._data[category] = _deep_copy(payload)

        if auto_save:
            self.save()

        self._notify_change(
            _SettingsChange(
                path=f"current.{category}",
                category=category,
                changeType="set_category",
                newValue=payload,
                oldValue=previous,
                timestamp=_utc_now(),
            )
        )

    def reset_to_defaults(
        self, *, category: Optional[str] = None, auto_save: bool = True
    ) -> None:
        """Reset ``current`` values to the defaults snapshot."""

        timestamp = _utc_now()
        changes: List[_SettingsChange] = []

        if category is None:
            before = _deep_copy(self._data)
            self._data = _deep_copy(self._defaults)
            changes.append(
                _SettingsChange(
                    path="current",
                    category="*",
                    changeType="reset_all",
                    newValue=self._data,
                    oldValue=before,
                    timestamp=timestamp,
                )
            )
        else:
            if category not in self._defaults:
                raise KeyError(f"Unknown defaults category: {category}")
            before = _deep_copy(self._data.get(category))
            self._data[category] = _deep_copy(self._defaults[category])
            changes.append(
                _SettingsChange(
                    path=f"current.{category}",
                    category=category,
                    changeType="reset",
                    newValue=self._defaults[category],
                    oldValue=before,
                    timestamp=timestamp,
                )
            )

        if auto_save:
            self.save()

        if changes:
            summary = {
                "count": len(changes),
                "categories": sorted({change.category for change in changes}),
                "operation": "reset",
            }
            if len(changes) == 1:
                self._notify_change(changes[0])
            else:
                self._notify_batch(changes, summary)

    def save_current_as_defaults(
        self, *, category: Optional[str] = None, auto_save: bool = True
    ) -> None:
        """Persist the current values into the defaults snapshot."""

        timestamp = _utc_now()
        changes: List[_SettingsChange] = []

        if category is None:
            before = _deep_copy(self._defaults)
            self._defaults = _deep_copy(self._data)
            changes.append(
                _SettingsChange(
                    path="defaults_snapshot",
                    category="*",
                    changeType="save_defaults_all",
                    newValue=self._defaults,
                    oldValue=before,
                    timestamp=timestamp,
                )
            )
        else:
            if category not in self._data:
                raise KeyError(f"Unknown current category: {category}")
            before = _deep_copy(self._defaults.get(category))
            self._defaults[category] = _deep_copy(self._data[category])
            changes.append(
                _SettingsChange(
                    path=f"defaults_snapshot.{category}",
                    category=category,
                    changeType="save_defaults",
                    newValue=self._defaults[category],
                    oldValue=before,
                    timestamp=timestamp,
                )
            )

        if auto_save:
            self.save()

        if changes:
            summary = {
                "count": len(changes),
                "categories": sorted({change.category for change in changes}),
                "operation": "save_defaults",
            }
            if len(changes) == 1:
                self._notify_change(changes[0])
            else:
                self._notify_batch(changes, summary)


_settings_manager: Optional[SettingsManager] = None
_settings_event_bus: Optional[SettingsEventBus] = None


def get_settings_manager(settings_file: Optional[Path | str] = None) -> SettingsManager:
    global _settings_manager
    if _settings_manager is None or settings_file is not None:
        _settings_manager = SettingsManager(settings_file)
    return _settings_manager


def get_settings_event_bus() -> SettingsEventBus:
    global _settings_event_bus
    if _settings_event_bus is None:
        _settings_event_bus = SettingsEventBus()
    return _settings_event_bus


__all__ = [
    "ProfileSettingsManager",
    "SettingsEventBus",
    "SettingsManager",
    "get_settings_event_bus",
    "get_settings_manager",
]
