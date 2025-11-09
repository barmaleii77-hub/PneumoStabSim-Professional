"""Utilities for managing optional pytest-qt integration."""

from __future__ import annotations

import importlib.util
import importlib
import os
import sys
from ctypes import util as ctypes_util
from pathlib import Path
from typing import Final

from pytest import PytestPluginManager


def _qt_display_available() -> bool:
    """Return True when a Qt-compatible display backend can be used."""

    qt_platform = os.environ.get("QT_QPA_PLATFORM", "").strip().lower()
    if qt_platform in {"offscreen", "minimal"}:
        return True

    if sys.platform.startswith("linux"):
        return bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))

    return True


def _libgl_available() -> bool:
    """Return ``True`` when the system OpenGL runtime is present."""

    if not sys.platform.startswith("linux"):
        return True

    if ctypes_util.find_library("GL"):
        return True

    fallback_paths = (
        Path("/usr/lib/x86_64-linux-gnu/libGL.so.1"),
        Path("/usr/lib64/libGL.so.1"),
    )
    return any(path.exists() for path in fallback_paths)


_PYTESTQT_SPEC = importlib.util.find_spec("pytestqt.plugin")
_PYSIDE_SPEC = importlib.util.find_spec("PySide6.QtWidgets")
_PYSIDE_IMPORT_ERROR: Exception | None = None
if _PYSIDE_SPEC is not None:
    try:  # noqa: SIM105 - capture platform-specific linker failures
        import PySide6.QtWidgets  # type: ignore[import-not-found]  # noqa: F401
        import PySide6.QtGui  # type: ignore[import-not-found]  # noqa: F401
    except Exception as exc:  # pragma: no cover - platform dependent
        _PYSIDE_IMPORT_ERROR = exc


def _build_skip_reason() -> str | None:
    if _PYTESTQT_SPEC is None:
        return "pytest-qt plugin is not installed"
    if _PYSIDE_SPEC is None:
        return "PySide6 is not available"
    if _PYSIDE_IMPORT_ERROR is not None:
        return f"PySide6 import failed: {_PYSIDE_IMPORT_ERROR}"
    if not _libgl_available():
        return "System OpenGL libraries (libGL) are missing"
    if not _qt_display_available():
        return "No display backend detected for Qt"
    return None


QT_SKIP_REASON: Final[str | None] = _build_skip_reason()


def disable_pytestqt(pluginmanager: PytestPluginManager) -> None:
    """Unregister the pytest-qt plugin to avoid hard failures."""

    for name in ("pytestqt", "pytestqt.plugin"):
        plugin = pluginmanager.get_plugin(name)
        if plugin is not None:
            pluginmanager.unregister(plugin, name=name)
        pluginmanager.set_blocked(name)


__all__ = ["QT_SKIP_REASON", "disable_pytestqt"]
