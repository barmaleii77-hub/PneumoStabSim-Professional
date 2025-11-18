"""Public UI entrypoints with deferred widget imports."""

from __future__ import annotations

from typing import Any, Callable

from .lazy_loader import (
    build_chart_widget,
    build_main_window,
    get_camera_hud_telemetry,
    get_chart_widget,
    get_main_window,
    get_pressure_scale_widget,
    get_tank_overlay_hud,
)

__all__ = [
    "build_chart_widget",
    "build_main_window",
    "get_chart_widget",
    "get_main_window",
    "get_pressure_scale_widget",
    "get_tank_overlay_hud",
    "get_camera_hud_telemetry",
    "ChartWidget",
    "MainWindow",
    "PressureScaleWidget",
    "TankOverlayHUD",
    "CameraHudTelemetry",
]

_lazy_class_loaders: dict[str, Callable[[], Any]] = {
    "MainWindow": get_main_window,
    "ChartWidget": get_chart_widget,
    "PressureScaleWidget": get_pressure_scale_widget,
    "TankOverlayHUD": get_tank_overlay_hud,
    "CameraHudTelemetry": get_camera_hud_telemetry,
}


def __getattr__(name: str) -> Any:
    loader = _lazy_class_loaders.get(name)
    if loader:
        return loader()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


