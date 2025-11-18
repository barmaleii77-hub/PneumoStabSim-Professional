"""HUD factories with caching and deferred PySide6 imports."""

from __future__ import annotations

from typing import Any, Callable

__all__ = [
    "get_pressure_scale_widget",
    "get_tank_overlay_hud",
    "get_camera_hud_telemetry",
    "build_pressure_scale_widget",
    "build_tank_overlay_hud",
    "build_camera_hud_telemetry",
    "PressureScaleWidget",
    "TankOverlayHUD",
    "CameraHudTelemetry",
]

_CACHE: dict[str, Any] = {}


def _cached(name: str, factory: Callable[[], Any]) -> Any:
    if name in _CACHE:
        return _CACHE[name]
    value = factory()
    _CACHE[name] = value
    return value


def get_pressure_scale_widget() -> type:
    """Return the :class:`PressureScaleWidget` class without importing it upfront."""
    from .widgets import PressureScaleWidget

    return _cached("PressureScaleWidget", lambda: PressureScaleWidget)


def build_pressure_scale_widget(*args: Any, **kwargs: Any) -> Any:
    """Instantiate :class:`PressureScaleWidget` lazily."""
    return get_pressure_scale_widget()(*args, **kwargs)


def get_tank_overlay_hud() -> type:
    """Return the :class:`TankOverlayHUD` class lazily."""
    from .widgets import TankOverlayHUD

    return _cached("TankOverlayHUD", lambda: TankOverlayHUD)


def build_tank_overlay_hud(*args: Any, **kwargs: Any) -> Any:
    """Instantiate :class:`TankOverlayHUD` lazily."""
    return get_tank_overlay_hud()(*args, **kwargs)


def get_camera_hud_telemetry() -> type:
    """Return the :class:`CameraHudTelemetry` helper lazily."""
    from .widgets import CameraHudTelemetry

    return _cached("CameraHudTelemetry", lambda: CameraHudTelemetry)


def build_camera_hud_telemetry(*args: Any, **kwargs: Any) -> Any:
    """Instantiate :class:`CameraHudTelemetry` lazily."""
    return get_camera_hud_telemetry()(*args, **kwargs)


_lazy_exports: dict[str, Callable[[], Any]] = {
    "PressureScaleWidget": get_pressure_scale_widget,
    "TankOverlayHUD": get_tank_overlay_hud,
    "CameraHudTelemetry": get_camera_hud_telemetry,
}


def __getattr__(name: str) -> Any:
    loader = _lazy_exports.get(name)
    if loader:
        return loader()
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
