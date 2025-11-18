"""Lazy factories for UI widgets and QML-driven windows.

The goal is to keep PySide6 imports out of module import time so that
configuration and smoke tests can import :mod:`src.ui` without pulling in Qt.
"""

from __future__ import annotations

from typing import Any


def get_pressure_scale_widget() -> type:
    """Return the :class:`PressureScaleWidget` class lazily."""
    from .hud.widgets import PressureScaleWidget

    return PressureScaleWidget


def get_tank_overlay_hud() -> type:
    """Return the :class:`TankOverlayHUD` class lazily."""
    from .hud.widgets import TankOverlayHUD

    return TankOverlayHUD


def get_camera_hud_telemetry() -> type:
    """Return the :class:`CameraHudTelemetry` helper lazily."""
    from .hud.widgets import CameraHudTelemetry

    return CameraHudTelemetry


def get_chart_widget() -> type:
    """Return the :class:`ChartWidget` widget lazily."""
    from .charts import ChartWidget

    return ChartWidget


def build_chart_widget(*args: Any, **kwargs: Any) -> Any:
    """Instantiate :class:`ChartWidget` lazily."""
    return get_chart_widget()(*args, **kwargs)


def get_main_window() -> type:
    """Return the primary :class:`MainWindow` lazily."""
    from .main_window import MainWindow

    return MainWindow


def build_main_window(*args: Any, **kwargs: Any) -> Any:
    """Instantiate :class:`MainWindow` lazily."""
    return get_main_window()(*args, **kwargs)


__all__ = [
    "get_pressure_scale_widget",
    "get_tank_overlay_hud",
    "get_camera_hud_telemetry",
    "get_chart_widget",
    "get_main_window",
    "build_chart_widget",
    "build_main_window",
]
