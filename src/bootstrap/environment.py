# -*- coding: utf-8 -*-
"""
Модуль настройки окружения Qt и QtQuick3D.

Отвечает за конфигурацию переменных среды для корректной работы
Qt Quick 3D, включая пути к QML-модулям и плагинам.
"""

import os
import sys
from typing import Callable


def setup_qtquick3d_environment(
    log_error: Callable[[str], None],
) -> tuple[bool, str | None]:
    """
    Настройка переменных окружения QtQuick3D перед импортом Qt.

    Args:
        log_error: Функция для логирования ошибок

    Returns:
        Кортеж (успех, причина ошибки). При успехе причина равна None.
    """
    # Если пользователь явно настроил переменные через .env — не трогаем
    required_vars = [
        "QML2_IMPORT_PATH",
        "QML_IMPORT_PATH",
        "QT_PLUGIN_PATH",
        "QT_QML_IMPORT_PATH",
    ]
    if all(var in os.environ and os.environ.get(var) for var in required_vars):
        return True, None

    try:
        import importlib.util

        spec = importlib.util.find_spec("PySide6.QtCore")
        if spec is None:
            reason = "PySide6 not found in the current environment"
            log_error(reason)
            return False, reason

        from PySide6.QtCore import QLibraryInfo

        qml_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.Qml2ImportsPath)
        plugins_path = QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)

        qtquick3d_env = {
            "QML2_IMPORT_PATH": str(qml_path),
            "QML_IMPORT_PATH": str(qml_path),
            "QT_PLUGIN_PATH": str(plugins_path),
            "QT_QML_IMPORT_PATH": str(qml_path),
        }

        # Разрешаем переопределить через .env стартовые пути, если заданы
        for var, value in qtquick3d_env.items():
            os.environ.setdefault(var, value)

        # Дополнительные import path для локальных QML (assets/qml)
        local_qml = os.path.abspath(os.path.join(os.getcwd(), "assets", "qml"))
        if os.path.isdir(local_qml):
            existing = os.environ.get("QML2_IMPORT_PATH", "")
            if local_qml not in existing:
                os.environ["QML2_IMPORT_PATH"] = (
                    (existing + os.pathsep + local_qml) if existing else local_qml
                )
            existing2 = os.environ.get("QML_IMPORT_PATH", "")
            if local_qml not in existing2:
                os.environ["QML_IMPORT_PATH"] = (
                    (existing2 + os.pathsep + local_qml) if existing2 else local_qml
                )

        return True, None

    except Exception as e:
        reason = f"QtQuick3D setup failed: {e}"
        log_error(reason)
        return False, reason


def configure_qt_environment() -> None:
    """Настройка переменных окружения Qt для графики и логирования."""
    # Уважаем .env, но задаём дефолты при отсутствии значений
    os.environ.setdefault(
        "QSG_RHI_BACKEND", "d3d11" if sys.platform == "win32" else "opengl"
    )
    os.environ.setdefault("QSG_INFO", "0")
    os.environ.setdefault("QT_LOGGING_RULES", "*.debug=false;*.info=false")
    os.environ.setdefault("QT_ASSUME_STDERR_HAS_CONSOLE", "1")
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
    os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "PassThrough")
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    os.environ.setdefault("PSS_DIAG", "1")

    # Если заданы стартовые параметры окружения для IBL/skybox через .env — передадим в QML через context props
    # Сохранение в окружении, а чтение/установка произойдёт в MainWindow при создании QML Engine
    for env_var in (
        "START_IBL_SOURCE",
        "START_IBL_FALLBACK",
        "START_IBL_INTENSITY",
        "START_SKYBOX_ENABLED",
        "START_IBL_ENABLED",
    ):
        if env_var in os.environ:
            # просто убедимся, что значение строковое (оставляем как есть)
            os.environ[env_var] = str(os.environ.get(env_var))
