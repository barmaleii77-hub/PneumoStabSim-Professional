"""Public UI entrypoints with deferred widget imports.

The module itself must remain import-light. Attribute resolution defers to
``src.ui.lazy_loader`` so that Qt-heavy modules are only imported when the
attribute is first accessed.
"""

from __future__ import annotations

from importlib import import_module
from typing import Any, Callable

__all__ = [
    "build_chart_widget",
    "build_main_window",
    "get_chart_widget",
    "get_main_window",
    "get_pressure_scale_widget",
    "get_tank_overlay_hud",
    "get_camera_hud_telemetry",
    "build_pressure_scale_widget",
    "build_tank_overlay_hud",
    "build_camera_hud_telemetry",
    "ChartWidget",
    "MainWindow",
    "PressureScaleWidget",
    "TankOverlayHUD",
    "CameraHudTelemetry",
]

_FACTORY_NAMES: dict[str, str] = {
    "build_chart_widget": "build_chart_widget",
    "build_main_window": "build_main_window",
    "get_chart_widget": "get_chart_widget",
    "get_main_window": "get_main_window",
    "get_pressure_scale_widget": "get_pressure_scale_widget",
    "get_tank_overlay_hud": "get_tank_overlay_hud",
    "get_camera_hud_telemetry": "get_camera_hud_telemetry",
}

_CLASS_FACTORIES: dict[str, str] = {
    "MainWindow": "get_main_window",
    "ChartWidget": "get_chart_widget",
    "PressureScaleWidget": "get_pressure_scale_widget",
    "TankOverlayHUD": "get_tank_overlay_hud",
    "CameraHudTelemetry": "get_camera_hud_telemetry",
}


def _load_factory(name: str) -> Callable[..., Any]:
    lazy_loader = import_module("src.ui.lazy_loader")
    factory_name = _FACTORY_NAMES.get(name) or _CLASS_FACTORIES.get(name)
    if not factory_name:
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")

    factory = getattr(lazy_loader, factory_name, None)
    if not callable(factory):
        raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
    return factory


def __getattr__(name: str) -> Any:
    if name in _FACTORY_NAMES:
        return _load_factory(name)
    if name in _CLASS_FACTORIES:
        return _load_factory(name)()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
