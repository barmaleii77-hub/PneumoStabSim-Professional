"""Pneumatic panel package with refactored implementation and legacy fallback."""

from __future__ import annotations

import logging
from importlib import import_module
from typing import Any

logger = logging.getLogger(__name__)

__all__ = ["PneumoPanel", "get_version_info"]

_PNEUMO_CLASS: type[Any] | None = None
_PNEUMO_ERROR: ImportError | None = None
_USING_REFACTORED = False


def _load_pneumo_panel() -> type[Any]:
    """Load the pneumatic panel implementation on demand."""

    global _PNEUMO_CLASS, _PNEUMO_ERROR, _USING_REFACTORED

    if _PNEUMO_CLASS is not None:
        return _PNEUMO_CLASS
    if _PNEUMO_ERROR is not None:
        raise _PNEUMO_ERROR

    last_error: ImportError | None = None
    for module_name, refactored in (
        (".panel_pneumo_refactored", True),
        ("..panel_pneumo_legacy", False),
    ):
        try:
            module = import_module(module_name, __name__)
        except ImportError as exc:
            last_error = exc
            if refactored:
                logger.warning(
                    "⚠️ PneumoPanel: refactored import failed, falling back to legacy",
                    exc_info=exc,
                )
            else:
                logger.error("❌ PneumoPanel: legacy import failed", exc_info=exc)
            continue

        _PNEUMO_CLASS = module.PneumoPanel
        _USING_REFACTORED = refactored
        if refactored:
            logger.info("✅ PneumoPanel: using refactored modular implementation")
        else:
            logger.info("📦 PneumoPanel: legacy monolithic version active")
        return _PNEUMO_CLASS

    _PNEUMO_ERROR = ImportError(
        "PneumoPanel: Neither refactored nor legacy version available!"
    )
    if last_error is not None:
        _PNEUMO_ERROR.__cause__ = last_error
    raise _PNEUMO_ERROR


def get_version_info() -> dict[str, object]:
    """Return diagnostics about the active implementation."""

    try:
        _load_pneumo_panel()
    except ImportError:
        return {
            "module": "PneumoPanel",
            "refactored": False,
            "version": None,
            "available": False,
        }

    return {
        "module": "PneumoPanel",
        "refactored": _USING_REFACTORED,
        "version": "2.0.2" if _USING_REFACTORED else "legacy",
        "available": True,
    }


def __getattr__(name: str) -> Any:
    """Lazily expose the pneumatic panel class."""

    if name == "PneumoPanel":
        return _load_pneumo_panel()
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


if __name__ == "__main__":  # pragma: no cover - manual diagnostics
    info = get_version_info()
    print("=" * 60)
    print("PNEUMOPANEL MODULE INFO")
    print("=" * 60)
    for key, value in info.items():
        print(f"{key}: {value}")
    print("=" * 60)
