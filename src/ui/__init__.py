# PySide6 UI components
# Qt Quick 3D rendering (no OpenGL)

# REMOVED: GLView, GLScene (migrated to Qt Quick 3D)
# from .gl_view import GLView
# from .gl_scene import GLScene

# ИСПРАВЛЕНО: Используем относительные импорты
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:  # pragma: no cover - imported for typing only
    from .hud import PressureScaleWidget as PressureScaleWidget
    from .hud import TankOverlayHUD as TankOverlayHUD
else:  # pragma: no cover - executed only at runtime
    try:
        from .hud import PressureScaleWidget as PressureScaleWidget
        from .hud import TankOverlayHUD as TankOverlayHUD
    except Exception:

        class PressureScaleWidget:
            """Minimal stub used when Qt widgets are unavailable."""

            def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401
                """Ignore any construction arguments."""

        class TankOverlayHUD(PressureScaleWidget):
            pass


__all__ = ["PressureScaleWidget", "TankOverlayHUD"]

# NOTE: 3D rendering now done via Qt Quick 3D QML scene
# See: assets/qml/main.qml


def __getattr__(name: str) -> Any:
    # Ленивая загрузка компонентов интерфейса пользователя
    # Например, MainWindow, ChartWidget и т. д.
    from .main_window import MainWindow
    from .charts import ChartWidget

    if name == "MainWindow":
        return MainWindow
    if name == "ChartWidget":
        return ChartWidget

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
