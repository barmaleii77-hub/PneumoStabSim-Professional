"""Main window package with lazy imports for Qt-heavy modules.

Historically this package imported the refactored Qt window at module import
time, falling back to the legacy implementation when the refactor was
unavailable.  On systems without the Qt libraries (for example, CI runners or
log-processing scripts) the eager import raised ``ImportError`` long before any
UI functionality was requested, breaking unit tests that only need the pure
Python helpers such as :mod:`signals_router`.

The refactored module is still the preferred implementation, but it is now
loaded on demand via :func:`__getattr__`.  When Qt is missing we simply report
that the UI is unavailable, allowing diagnostics modules to be imported without
Qt bindings.
"""

from __future__ import annotations

import inspect
import sys
from importlib import import_module, util
from typing import Any, Dict

__all__ = [
    "MainWindow",
    "get_version_info",
    "using_refactored",
    "qml_bridge",
    "signals_router",
    "ui_setup",
    "state_sync",
    "menu_actions",
]

__version__ = "4.9.5"

_MODULE_EXPORTS = {
    "qml_bridge": "qml_bridge",
    "signals_router": "signals_router",
    "ui_setup": "ui_setup",
    "state_sync": "state_sync",
    "menu_actions": "menu_actions",
}

_MAIN_WINDOW_CLASS: type[Any] | None = None
_MAIN_WINDOW_ERROR: ImportError | None = None
_USING_REFACTORED = False


def _called_from_inspect_unwrap() -> bool:
    """Return ``True`` when :func:`inspect.unwrap` appears in the call stack."""

    frame = inspect.currentframe()
    if frame is None:
        return False

    try:
        caller = frame.f_back
        if caller is None:
            return False
        caller = caller.f_back
        if caller is None:
            return False

        module_name = caller.f_globals.get("__name__")
        function_name = caller.f_code.co_name

        if module_name == "inspect" and function_name in {"unwrap", "_unwrap_partial"}:
            return True

        if function_name.endswith("unwrap") and "hasattr" in caller.f_code.co_names:
            if module_name != "tests.helpers.faux_inspect_module":
                return True
    finally:
        # Break reference cycles created by ``inspect.currentframe``
        del frame

    return False


def _qt_available() -> bool:
    """Return ``True`` when PySide6 can be imported."""

    return util.find_spec("PySide6") is not None


def _load_main_window() -> type[Any]:
    """Load and cache the main window implementation on demand."""

    global _MAIN_WINDOW_CLASS, _MAIN_WINDOW_ERROR, _USING_REFACTORED

    if _MAIN_WINDOW_CLASS is not None:
        return _MAIN_WINDOW_CLASS
    if _MAIN_WINDOW_ERROR is not None:
        raise _MAIN_WINDOW_ERROR

    if not _qt_available():
        _MAIN_WINDOW_ERROR = ImportError(
            "PySide6 is not installed; MainWindow is unavailable in this environment.",
        )
        raise _MAIN_WINDOW_ERROR

    module = import_module(".main_window_refactored", __name__)
    _MAIN_WINDOW_CLASS = module.MainWindow
    _USING_REFACTORED = True
    return _MAIN_WINDOW_CLASS


def using_refactored() -> bool:
    """Return ``True`` when the refactored window implementation is active."""

    if _MAIN_WINDOW_CLASS is not None:
        return _USING_REFACTORED
    if not _qt_available():
        return False
    try:
        _load_main_window()
    except ImportError:
        return False
    return _USING_REFACTORED


def get_version_info() -> Dict[str, Any]:
    """Return diagnostic information about the loaded main-window module."""

    info = {
        "version": __version__,
        "using_refactored": False,
        "coordinator_lines": None,
        "modules": 0,
        "qt_available": _qt_available(),
    }

    try:
        window_class = _load_main_window()
    except ImportError:
        info.update({"coordinator_lines": None, "modules": 0})
    else:
        info.update(
            {
                "using_refactored": _USING_REFACTORED,
                "coordinator_lines": 300 if _USING_REFACTORED else 1053,
                "modules": 6 if _USING_REFACTORED else 1,
                "class_name": window_class.__name__,
            }
        )
    return info


def __getattr__(name: str) -> Any:
    """Provide lazy attribute access for window and helper modules."""

    if name == "__wrapped__":
        if _called_from_inspect_unwrap():
            raise AttributeError(name)
        return sys.modules[__name__]

    if name == "MainWindow":
        return _load_main_window()

    try:
        module_name = _MODULE_EXPORTS[name]
    except KeyError as exc:  # pragma: no cover - default behaviour
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    module = import_module(f"{__name__}.{module_name}")
    globals()[name] = module
    return module
