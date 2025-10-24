"""User interface package bootstrap with optional Qt dependencies."""

from __future__ import annotations

from importlib import import_module
from typing import TYPE_CHECKING, Any

__all__ = [
    "PressureScaleWidget",
    "TankOverlayHUD",
    "MainWindow",
    "ChartWidget",
]

_QT_IMPORT_ERROR: Exception | None = None


def _load_qt_component(name: str) -> Any:
    """Import Qt-backed widgets lazily and provide clear diagnostics on failure."""

    global _QT_IMPORT_ERROR
    if _QT_IMPORT_ERROR is not None:
        raise RuntimeError(
            "Qt widgets are unavailable because PySide6 could not be imported."
        ) from _QT_IMPORT_ERROR

    try:
        module = import_module("src.ui.hud")
    except Exception as exc:  # pragma: no cover - depends on system libraries
        _QT_IMPORT_ERROR = exc
        raise RuntimeError(
            "PySide6 (with libGL support) is required to use HUD widgets."
        ) from exc

    return getattr(module, name)


def __getattr__(name: str) -> Any:
    if name in {"PressureScaleWidget", "TankOverlayHUD"}:
        return _load_qt_component(name)

    if name == "MainWindow":
        from .main_window import MainWindow

        return MainWindow

    if name == "ChartWidget":
        from .charts import ChartWidget

        return ChartWidget

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


if TYPE_CHECKING:  # pragma: no cover - for static type checkers only
    from .charts import ChartWidget as ChartWidget
    from .hud import PressureScaleWidget as PressureScaleWidget
    from .hud import TankOverlayHUD as TankOverlayHUD
    from .main_window import MainWindow as MainWindow
