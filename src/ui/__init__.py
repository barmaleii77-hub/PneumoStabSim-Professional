# PySide6 UI components
# Qt Quick 3D rendering (no OpenGL)

# REMOVED: GLView, GLScene (migrated to Qt Quick 3D)
# from .gl_view import GLView
# from .gl_scene import GLScene

# ИСПРАВЛЕНО: Используем относительные импорты
from .hud import PressureScaleWidget, TankOverlayHUD
from .main_window import MainWindow
from .charts import ChartWidget

__all__ = [
    'PressureScaleWidget',
    'TankOverlayHUD', 
    'MainWindow',
    'ChartWidget'
]

# NOTE: 3D rendering now done via Qt Quick 3D QML scene
# See: assets/qml/main.qml
