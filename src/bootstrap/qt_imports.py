# -*- coding: utf-8 -*-
"""
Модуль безопасного импорта Qt компонентов.

Проверяет наличие PySide6 и версию Qt, логирует предупреждения
при использовании версий < 6.10.
"""

from typing import Any, Callable

from src.bootstrap.dependency_config import match_dependency_error


def safe_import_qt(
    log_warning: Callable[[str], None], log_error: Callable[[str], None]
) -> tuple[Any, Any, Any, Any]:
    """
    Безопасный импорт Qt компонентов с проверкой версии.

    Args:
        log_warning: Функция для логирования предупреждений
        log_error: Функция для логирования ошибок

    Returns:
        Кортеж (QApplication, qInstallMessageHandler, Qt, QTimer)
    """
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import qInstallMessageHandler, Qt, QTimer, qVersion

        qt_version = qVersion()

        try:
            major, minor = qt_version.split(".")[:2]
            if int(major) == 6 and int(minor) < 10:
                log_warning(
                    f"Qt {qt_version} detected. Some 6.10+ features may be unavailable"
                )
        except (ValueError, IndexError):
            log_warning(f"Could not parse Qt version: {qt_version}")

        return QApplication, qInstallMessageHandler, Qt, QTimer
    except ImportError as e:
        error_message = f"PySide6 import failed: {e}"

        text = str(e)
        details: list[str] = []
        hints: list[str] = []

        variant = match_dependency_error("opengl_runtime", text)
        if variant is not None:
            missing = variant.missing_message
            if missing:
                details.append(missing)
            hint = variant.install_hint
            if hint:
                hints.append(hint)

        if "libEGL.so" in text:
            hints.append(
                "Missing libEGL runtime. Install an EGL package (e.g. 'apt-get install -y libegl1')."
            )

        if details:
            error_message = "\n".join([error_message, *details])
        if hints:
            unique_hints = dict.fromkeys(hints)
            hint_lines = [f"Hint: {value}" for value in unique_hints if value]
            if hint_lines:
                error_message = "\n".join([error_message, *hint_lines])

        log_error(error_message)

        from src.bootstrap.headless_qt import (
            HeadlessApplication,
            HeadlessQtNamespace,
            HeadlessTimer,
            headless_install_message_handler,
        )

        HeadlessApplication.headless_reason = error_message
        qt_namespace = HeadlessQtNamespace(headless_reason=error_message)

        log_warning(
            "PySide6 is unavailable; using headless diagnostics mode without a Qt GUI."
        )

        return (
            HeadlessApplication,
            headless_install_message_handler,
            qt_namespace,
            HeadlessTimer,
        )
