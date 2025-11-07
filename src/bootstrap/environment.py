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
        scene_module = local_qml / "scene"

        local_candidates = []
        if local_qml.is_dir():
            local_candidates.append(str(local_qml))
        if local_components.is_dir():
            local_candidates.append(str(local_components))
        if scene_module.is_dir():
            local_candidates.append(str(scene_module))

        if local_candidates:
            _ensure_paths("QML2_IMPORT_PATH", local_candidates)
            _ensure_paths("QML_IMPORT_PATH", local_candidates)
            _ensure_paths("QT_QML_IMPORT_PATH", local_candidates)

        return True, None

    except Exception as e:
        reason = f"QtQuick3D setup failed: {e}"
        log_error(reason)
        return False, reason


def configure_qt_environment(
    *,
    safe_mode: bool = False,
    safe_execution: bool = False,
    log: Callable[[str], None] | None = None,
) -> None:
    """Настройка переменных окружения Qt для графики и логирования.

    Args:
        safe_mode: Если ``True``, не устанавливать ``QSG_RHI_BACKEND`` и
            позволить Qt самостоятельно выбрать графический backend.
        log: Необязательная функция логирования для сообщений о выбранном
            backend.
    """

    def _default_emitter(message: str) -> None:
        print(message)

    emitter = log if log is not None else _default_emitter

    platform = sys.platform.lower()
    if platform.startswith("win"):
        backend_default = "d3d11"
    elif platform.startswith("darwin"):
        backend_default = "metal"
    else:
        backend_default = "opengl"

    removed_backend: str | None = None
    removed_safe_mode_keys: list[str] = []
    headless_removed_keys: list[str] = []

    if safe_mode:
        removed_backend = os.environ.pop("QSG_RHI_BACKEND", None)
        if os.environ.pop("QT_OPENGL", None) is not None:
            removed_safe_mode_keys.append("QT_OPENGL")
        if os.environ.pop("QSG_OPENGL_VERSION", None) is not None:
            removed_safe_mode_keys.append("QSG_OPENGL_VERSION")
        backend = os.environ.get("QSG_RHI_BACKEND")
    else:
        backend = os.environ.get("QSG_RHI_BACKEND")
        if not backend:
            backend = backend_default
            os.environ["QSG_RHI_BACKEND"] = backend
    os.environ.setdefault("QT_QUICK_CONTROLS_STYLE", "Fusion")
    os.environ.setdefault("QSG_INFO", "0")
    os.environ.setdefault("QT_LOGGING_RULES", "*.debug=false;*.info=false")
    os.environ.setdefault("QT_ASSUME_STDERR_HAS_CONSOLE", "1")
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
    os.environ.setdefault("QT_SCALE_FACTOR_ROUNDING_POLICY", "PassThrough")
    os.environ.setdefault("QT_ENABLE_HIGHDPI_SCALING", "1")
    os.environ.setdefault("PSS_DIAG", "1")

    # OpenGL остаётся дефолтом на Windows, Linux и macOS — Qt подберёт нужный драйвер,
    # а в headless-режимах мы переключаемся на software backend. На Windows это
    # означает использование штатного desktop OpenGL (или ANGLE, если пользователь
    # явно включит его через QT_OPENGL). На Linux сохраняем 3.3 для Mesa и
    # проприетарных драйверов, чтобы сцена создавалась на одинаковом профиле.
    if (backend or "").lower() == "opengl":
        os.environ.setdefault("QSG_OPENGL_VERSION", "3.3")
        os.environ.setdefault("QT_OPENGL", "desktop")

    # В Linux контейнерах или на CI переменная DISPLAY часто отсутствует.
    # В этом случае переключаемся на offscreen/софтварный backend. Windows и
    # macOS при этом продолжают использовать нативные плагины (windows/cocoa),
    # поэтому платформу не переопределяем, чтобы Qt автоматически выбрал
    # подходящий back-end ввода и рендеринга.
    ci_detected = any(
        os.environ.get(var, "").strip().lower() in {"1", "true", "yes"}
        for var in ("CI", "GITHUB_ACTIONS", "BUILD_SERVER", "TEAMCITY_VERSION")
    )
    requested_platform = os.environ.get("QT_QPA_PLATFORM", "").strip().lower()
    headless_platform_requested = requested_platform in {"offscreen", "minimal"}
    display_missing = sys.platform.startswith("linux") and not os.environ.get("DISPLAY")

    headless_mode = (
        safe_execution or ci_detected or headless_platform_requested or display_missing
    )
    if headless_mode:
        os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
        os.environ.setdefault("QT_QUICK_BACKEND", "software")
        os.environ.setdefault("PSS_HEADLESS", "1")

    headless_backend_override = False
    if headless_mode and not safe_mode:
        current_backend = (backend or "").strip().lower()
        if current_backend not in {"software", "null"}:
            backend = "software"
            os.environ["QSG_RHI_BACKEND"] = backend
            headless_backend_override = True
        os.environ["QT_OPENGL"] = "software"
        if os.environ.pop("QSG_OPENGL_VERSION", None) is not None:
            headless_removed_keys.append("QSG_OPENGL_VERSION")

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

    backend_value = os.environ.get("QSG_RHI_BACKEND")
    backend_label = backend_value or "auto (Qt default)"
    if headless_mode:
        details: list[str] = []
        if headless_backend_override:
            details.append("software backend")
        if headless_removed_keys:
            details.append("cleared " + ", ".join(sorted(headless_removed_keys)))
        headless_note = (
            "; headless (" + "; ".join(details) + ")" if details else "; headless"
        )
    else:
        headless_note = ""
    if safe_mode:
        if removed_safe_mode_keys:
            removal_note = ", removed " + ", ".join(sorted(removed_safe_mode_keys))
        else:
            removal_note = ""
        if removed_backend:
            emitter(
                "Qt Quick Scene Graph backend: "
                f"{backend_label} [safe mode{headless_note}; removed '{removed_backend}'{removal_note}]"
            )
        else:
            emitter(
                "Qt Quick Scene Graph backend: "
                f"{backend_label} [safe mode{headless_note}{removal_note}]"
            )
    else:
        emitter(
            "Qt Quick Scene Graph backend: "
            f"{backend_label} [standard mode{headless_note}; default={backend_default}]"
        )
