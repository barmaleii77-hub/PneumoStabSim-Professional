# PySide6 UI components
# Qt Quick 3D rendering (no OpenGL)

# REMOVED: GLView, GLScene (migrated to Qt Quick 3D)
# from .gl_view import GLView
# from .gl_scene import GLScene

# ИСПРАВЛЕНО: Используем относительные импорты
from .hud import PressureScaleWidget, TankOverlayHUD

__all__ = [
    "PressureScaleWidget",
    "TankOverlayHUD",
]

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
