# -*- coding: utf-8 -*-
"""
Модуль настройки окружения Qt и QtQuick3D.

Отвечает за конфигурацию переменных среды для корректной работы
Qt Quick 3D, включая пути к QML-модулям и плагинам.
"""
import os
import sys
from typing import Callable


def setup_qtquick3d_environment(log_error: Callable[[str], None]) -> bool:
    """
    Настройка переменных окружения QtQuick3D перед импортом Qt.
    
    Args:
        log_error: Функция для логирования ошибок
        
    Returns:
        True если настройка успешна, False при ошибках
    """
    required_vars = ["QML2_IMPORT_PATH", "QML_IMPORT_PATH", "QT_PLUGIN_PATH", "QT_QML_IMPORT_PATH"]
    if all(var in os.environ for var in required_vars):
        return True
    
    try:
        import importlib.util
        spec = importlib.util.find_spec("PySide6.QtCore")
        if spec is None:
            log_error("PySide6 not found!")
            return False
            
        from PySide6.QtCore import QLibraryInfo
        
        qml_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.Qml2ImportsPath)
        plugins_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
        
        qtquick3d_env = {
            "QML2_IMPORT_PATH": str(qml_path),
            "QML_IMPORT_PATH": str(qml_path),
            "QT_PLUGIN_PATH": str(plugins_path),
            "QT_QML_IMPORT_PATH": str(qml_path),
        }
        
        for var, value in qtquick3d_env.items():
            os.environ[var] = value
        
        return True
        
    except Exception as e:
        log_error(f"QtQuick3D setup failed: {e}")
        return False


def configure_qt_environment() -> None:
    """Настройка переменных окружения Qt для графики и логирования."""
    os.environ.setdefault("QSG_RHI_BACKEND", "d3d11" if sys.platform == 'win32' else "opengl")
    os.environ.setdefault("QSG_INFO", "0")
    os.environ.setdefault("QT_LOGGING_RULES", "*.debug=false;*.info=false")
    os.environ.setdefault("QT_ASSUME_STDERR_HAS_CONSOLE", "1")
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
    os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "PassThrough")
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    os.environ.setdefault("PSS_DIAG", "1")
