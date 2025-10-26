# -*- coding: utf-8 -*-
"""
Модуль настройки окружения Qt и QtQuick3D.

Отвечает за конфигурацию переменных среды для корректной работы
Qt Quick 3D, включая пути к QML-модулям и плагинам.
"""

import os
import sys
from pathlib import Path
from typing import Callable, Iterable


def _split_paths(value: str) -> list[str]:
    """Split environment-style paths into a list while dropping empties."""

    if not value:
        return []
    return [segment for segment in value.split(os.pathsep) if segment]


def _ensure_paths(env_var: str, candidates: Iterable[str]) -> None:
    """Append missing paths to an environment variable preserving order."""

    existing_segments = _split_paths(os.environ.get(env_var, ""))
    updated = list(existing_segments)

    for candidate in candidates:
        if not candidate:
            continue
        if candidate not in updated:
            updated.append(candidate)

    if updated:
        os.environ[env_var] = os.pathsep.join(updated)


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

        qml_path_str = str(qml_path)
        plugins_path_str = str(plugins_path)

        # Всегда включаем системные пути Qt вне зависимости от пользовательских настроек
        _ensure_paths("QML2_IMPORT_PATH", [qml_path_str])
        _ensure_paths("QML_IMPORT_PATH", [qml_path_str])
        _ensure_paths("QT_QML_IMPORT_PATH", [qml_path_str])
        _ensure_paths("QT_PLUGIN_PATH", [plugins_path_str])

        # Дополнительные import path для локальных QML (assets/qml и components)
        project_root = Path(__file__).resolve().parents[2]
        local_qml = project_root / "assets" / "qml"
        local_components = local_qml / "components"

        local_candidates = []
        if local_qml.is_dir():
            local_candidates.append(str(local_qml))
        if local_components.is_dir():
            local_candidates.append(str(local_components))

        if local_candidates:
            _ensure_paths("QML2_IMPORT_PATH", local_candidates)
            _ensure_paths("QML_IMPORT_PATH", local_candidates)
            _ensure_paths("QT_QML_IMPORT_PATH", local_candidates)

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
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Fusion")
    os.environ.setdefault("QSG_INFO", "0")
    os.environ.setdefault("QT_LOGGING_RULES", "*.debug=false;*.info=false")
    os.environ.setdefault("QT_ASSUME_STDERR_HAS_CONSOLE", "1")
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
    os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "PassThrough")
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    os.environ.setdefault("PSS_DIAG", "1")

    if sys.platform.startswith("linux") and not os.environ.get("DISPLAY"):
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        os.environ.setdefault("QT_QUICK_BACKEND", "software")

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
