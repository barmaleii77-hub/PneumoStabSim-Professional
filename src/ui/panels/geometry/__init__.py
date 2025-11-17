"""Geometry panels package with optional Qt dependency."""

from __future__ import annotations

import logging
from importlib import import_module
from typing import Any

logger = logging.getLogger(__name__)

__all__ = ["GeometryPanel", "get_version_info"]

_GEOMETRY_CLASS: type[Any] | None = None
_GEOMETRY_ERROR: ImportError | None = None
_USING_REFACTORED = False


def _load_geometry_panel() -> type[Any]:
    """Load the geometry panel implementation on demand."""

    global _GEOMETRY_CLASS, _GEOMETRY_ERROR, _USING_REFACTORED

    if _GEOMETRY_CLASS is not None:
        return _GEOMETRY_CLASS
    if _GEOMETRY_ERROR is not None:
        raise _GEOMETRY_ERROR

    last_error: ImportError | None = None
    for module_name, refactored in (
        (".panel_geometry_refactored", True),
        ("..panel_geometry", False),
    ):
        try:
            module = import_module(module_name, __name__)
        except ImportError as exc:
            last_error = exc
            if refactored:
                logger.warning(
                    "⚠️ GeometryPanel: Cannot import refactored version: %s", exc
                )
                logger.info("📦 GeometryPanel: Falling back to legacy version...")
            else:
                logger.error("❌ GeometryPanel: Cannot import legacy version: %s", exc)
            continue

        _GEOMETRY_CLASS = module.GeometryPanel
        _USING_REFACTORED = refactored
        if refactored:
            logger.info("✅ GeometryPanel: Using REFACTORED modular version")
        else:
            logger.info("✅ GeometryPanel: Using LEGACY monolithic version")
        return _GEOMETRY_CLASS

    _GEOMETRY_ERROR = ImportError(
        "GeometryPanel: Neither refactored nor legacy version available!"
    )
    if last_error is not None:
        _GEOMETRY_ERROR.__cause__ = last_error
    raise _GEOMETRY_ERROR


def get_version_info() -> dict[str, Any]:
    """Return diagnostic information about the geometry panel module."""

    try:
        _load_geometry_panel()
    except ImportError:
        return {
            "module": "GeometryPanel",
            "refactored": False,
            "version": None,
            "coordinator_lines": None,
            "total_modules": 0,
            "available": False,
        }

    return {
        "module": "GeometryPanel",
        "refactored": _USING_REFACTORED,
        "version": "5.0.1" if _USING_REFACTORED else "legacy",
        "coordinator_lines": 250 if _USING_REFACTORED else 850,
        "total_modules": 8 if _USING_REFACTORED else 1,
        "available": True,
    }


def __getattr__(name: str) -> Any:
    """Lazily expose the geometry panel class."""

    if name == "GeometryPanel":
        return _load_geometry_panel()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if __name__ == "__main__":  # pragma: no cover - manual diagnostics
    info = get_version_info()
    print("=" * 60)
    print("GEOMETRYPANEL MODULE INFO")
    print("=" * 60)
    for key, value in info.items():
        print(f"{key}: {value}")
