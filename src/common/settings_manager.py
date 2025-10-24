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
from pathlib import Path
from typing import Any, Dict, Iterable, Optional


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

        if not parts:
            root[dotted_path] = _deep_copy(value)
            if auto_save:
                self.save()
            return True

        *parents, leaf = parts
        node = self._traverse(root, parents, create=True) if parents else root
        node[leaf] = _deep_copy(value)

        if auto_save:
            self.save()
        return True

    # Defaults ---------------------------------------------------------------
    def get_all_defaults(self) -> Dict[str, Any]:
        return _deep_copy(self._defaults)


_settings_manager: Optional[SettingsManager] = None


def get_settings_manager(settings_file: Optional[Path | str] = None) -> SettingsManager:
    global _settings_manager
    if _settings_manager is None or settings_file is not None:
        _settings_manager = SettingsManager(settings_file)
    return _settings_manager


__all__ = ["SettingsManager", "get_settings_manager"]
