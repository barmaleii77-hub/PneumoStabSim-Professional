# PySide6 UI components
# Qt Quick 3D rendering (no OpenGL)

# REMOVED: GLView, GLScene (migrated to Qt Quick 3D)
# from .gl_view import GLView
# from .gl_scene import GLScene

# ИСПРАВЛЕНО: Используем относительные импорты
try:  # pragma: no cover - UI widgets unavailable in headless tests
    from .hud import PressureScaleWidget, TankOverlayHUD
except Exception:  # pragma: no cover - PySide6 or OpenGL not installed
    class _HeadlessWidget:  # type: ignore[too-many-ancestors]
        """Minimal stub used when Qt widgets are unavailable."""

        def __init__(self, *args, **kwargs):  # noqa: D401 - simple stub
            """Ignore any construction arguments."""

    class PressureScaleWidget(_HeadlessWidget):
        pass

    class TankOverlayHUD(_HeadlessWidget):
        pass

__all__ = ["PressureScaleWidget", "TankOverlayHUD"]

# NOTE: 3D rendering now done via Qt Quick 3D QML scene
# See: assets/qml/main.qml


def __getattr__(name):
    # Ленивая загрузка компонентов интерфейса пользователя
    # Например, MainWindow, ChartWidget и т. д.
    from .main_window import MainWindow
    from .charts import ChartWidget

    if name == "MainWindow":
        return MainWindow
    if name == "ChartWidget":
        return ChartWidget

    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
