# PySide6 UI components
# Qt Quick 3D rendering (no OpenGL)

# REMOVED: GLView, GLScene (migrated to Qt Quick 3D)
# from .gl_view import GLView
# from .gl_scene import GLScene

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .charts import ChartWidget
    from .hud import PressureScaleWidget, TankOverlayHUD
    from .main_window import MainWindow

__all__ = [
    "PressureScaleWidget",
    "TankOverlayHUD",
    "MainWindow",
    "ChartWidget",
]


def __getattr__(name: str) -> Any:
    """Lazily import heavy UI components.

    Importing PySide6 widgets during test collection requires an OpenGL capable
    environment. The lazy loader keeps the module lightweight for non-GUI
    contexts (for example, unit tests that validate configuration helpers).
    """

    if name in {"PressureScaleWidget", "TankOverlayHUD"}:
        from .hud import PressureScaleWidget, TankOverlayHUD

        return {
            "PressureScaleWidget": PressureScaleWidget,
            "TankOverlayHUD": TankOverlayHUD,
        }[name]

    if name == "MainWindow":
        from .main_window import MainWindow

        return MainWindow

    if name == "ChartWidget":
        from .charts import ChartWidget

        return ChartWidget

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


def __dir__() -> list[str]:
    return sorted(__all__)
