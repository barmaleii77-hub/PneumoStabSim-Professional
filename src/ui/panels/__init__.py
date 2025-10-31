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
from types import ModuleType
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
_SELF_ALIAS: ModuleType | None = None


class _ModuleAlias(ModuleType):
    """Proxy module object used to satisfy ``__wrapped__`` lookups."""

    def __init__(self, module: ModuleType) -> None:
        super().__init__(module.__name__, module.__doc__)
        object.__setattr__(self, "_module", module)
        object.__setattr__(self, "_wrapped", module)

    def __getattribute__(self, name: str) -> Any:
        if name == "__wrapped__":
            return object.__getattribute__(self, "_wrapped")
        if name in {
            "_module",
            "_wrapped",
            "__class__",
            "__dict__",
            "__doc__",
            "__name__",
            "__getattribute__",
            "__setattr__",
            "__dir__",
        }:
            return object.__getattribute__(self, name)
        module = object.__getattribute__(self, "_module")
        return getattr(module, name)

    def __setattr__(self, key: str, value: Any) -> None:
        module = object.__getattribute__(self, "_module")
        setattr(module, key, value)

    @property
    def __dict__(self) -> Dict[str, Any]:  # type: ignore[override]
        module = object.__getattribute__(self, "_module")
        return module.__dict__

    def __dir__(self) -> list[str]:
        module = object.__getattribute__(self, "_module")
        module_dir = dir(module)
        if "__wrapped__" not in module_dir:
            module_dir.append("__wrapped__")
        return module_dir

    def __repr__(self) -> str:
        module = object.__getattribute__(self, "_module")
        return repr(module)


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
    finally:
        # Break reference cycles created by ``inspect.currentframe``
        del frame

    return False


def __getattr__(name: str) -> Any:
    """Lazily import panel classes on first access."""

    if name == "__wrapped__":
        raise AttributeError(name)

    try:
        module_name, attribute = _EXPORTS[name]
    except KeyError as exc:  # pragma: no cover - default behaviour
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    module = import_module(f"{__name__}.{module_name}")
    value = getattr(module, attribute)
    globals()[name] = value
    return value
