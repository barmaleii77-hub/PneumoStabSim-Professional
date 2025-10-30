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


def _called_from_inspect_unwrap() -> bool:
    """Return ``True`` when :func:`inspect.unwrap` triggered the lookup."""

    frame = inspect.currentframe()
    try:
        while frame is not None:
            code = frame.f_code
            # Проверяем, что это функция unwrap из любого файла, содержащего 'inspect' в имени
            if code.co_name == "unwrap" and "inspect" in code.co_filename:
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
        return sys.modules[__name__]

    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError as exc:  # pragma: no cover - default behaviour
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    module = import_module(f"{__name__}.{module_name}")
    value = getattr(module, attribute)
    globals()[name] = value
    return value
