"""UI panels package exports without eager Qt imports.

The original module imported every panel implementation at import time, which
pulled in :mod:`PySide6` widgets unconditionally.  In test environments without
Qt libraries (for example, headless CI runners) this caused an immediate
``ImportError`` during package initialisation even when the caller only needed
the pure-Python helpers (state managers, defaults, etc.).

To keep the public API intact while avoiding the hard dependency on Qt, this
module now performs *lazy* imports: the heavy panel modules are only imported
when the corresponding attribute is accessed.  Test code that touches
``src.ui.panels.geometry`` or ``src.ui.panels.pneumo`` therefore succeeds even
when PySide6 is unavailable, but accessing ``GeometryPanel`` will still surface
the original ImportError with full context.
"""

from __future__ import annotations

import inspect
import sys
from importlib import import_module
from types import CodeType
from typing import TYPE_CHECKING, Any

__all__ = ["GeometryPanel", "PneumoPanel", "ModesPanel", "RoadPanel", "GraphicsPanel"]

_EXPORTS = {
    "GeometryPanel": ("panel_geometry", "GeometryPanel"),
    "PneumoPanel": ("panel_pneumo", "PneumoPanel"),
    "ModesPanel": ("panel_modes", "ModesPanel"),
    "RoadPanel": ("panel_road", "RoadPanel"),
    "GraphicsPanel": ("graphics.panel_graphics_refactored", "GraphicsPanel"),
}

if TYPE_CHECKING:  # pragma: no cover - typing helpers only
    from .panel_geometry import GeometryPanel
    from .panel_modes import ModesPanel
    from .panel_pneumo import PneumoPanel
    from .panel_road import RoadPanel
    from .graphics.panel_graphics_refactored import GraphicsPanel
_INSPECT_UNWRAP_CACHE_ID: int | None = None
_INSPECT_UNWRAP_CACHE_CODES: set[CodeType] = set()


def _collect_inspect_unwrap_codes(func: Any) -> set[CodeType]:
    """Return code objects for ``inspect.unwrap`` and its wrappers."""

    codes: set[CodeType] = set()
    seen: set[int] = set()
    current = func
    while callable(current) and id(current) not in seen:
        seen.add(id(current))
        code = getattr(current, "__code__", None)
        if code is not None:
            codes.add(code)
        current = getattr(current, "__wrapped__", None)
    return codes


def _inspect_unwrap_codes() -> set[CodeType]:
    """Return cached code objects for the active :func:`inspect.unwrap`."""

    unwrap = getattr(inspect, "unwrap", None)
    if unwrap is None:
        return set()

    global _INSPECT_UNWRAP_CACHE_ID, _INSPECT_UNWRAP_CACHE_CODES
    unwrap_id = id(unwrap)
    if unwrap_id != _INSPECT_UNWRAP_CACHE_ID:
        _INSPECT_UNWRAP_CACHE_CODES = _collect_inspect_unwrap_codes(unwrap)
        _INSPECT_UNWRAP_CACHE_ID = unwrap_id
    return _INSPECT_UNWRAP_CACHE_CODES


def _called_from_inspect_unwrap() -> bool:
    """Return ``True`` when :func:`inspect.unwrap` appears in the stack."""

    codes = _inspect_unwrap_codes()
    if not codes:
        return False

    frame = inspect.currentframe()
    try:
        frame = frame.f_back
        while frame is not None:
            code = frame.f_code
            if code in codes:
                return True
            module_name = frame.f_globals.get("__name__")
            if module_name == "inspect" and code.co_name == "unwrap":
                return True
            frame = frame.f_back
    finally:
        del frame

    return False


def __getattr__(name: str) -> Any:
    """Lazily import panel classes on first access."""

    if name == "__wrapped__":
        if _called_from_inspect_unwrap():
            raise AttributeError(name)
        module = sys.modules[__name__]
        return module

    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError as exc:  # pragma: no cover - default behaviour
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    module = import_module(f"{__name__}.{module_name}")
    value = getattr(module, attribute)
    globals()[name] = value
    return value
