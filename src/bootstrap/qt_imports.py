# -*- coding: utf-8 -*-
"""
Модуль безопасного импорта Qt компонентов.

Проверяет наличие PySide6 и версию Qt, логирует предупреждения
при использовании версий < 6.10.
"""
import sys
from typing import Any, Callable


def safe_import_qt(
    log_warning: Callable[[str], None],
    log_error: Callable[[str], None]
) -> tuple[Any, Any, Any, Any]:
    """
    Безопасный импорт Qt компонентов с проверкой версии.
    
    Args:
        log_warning: Функция для логирования предупреждений
        log_error: Функция для логирования ошибок
        
    Returns:
        Кортеж (QApplication, qInstallMessageHandler, Qt, QTimer)
        
    Raises:
        SystemExit: Если PySide6 не установлен
    """
    try:
        from PySide6.QtWidgets import QApplication
        from PySide6.QtCore import qInstallMessageHandler, Qt, QTimer, qVersion
        
        qt_version = qVersion()
        
        try:
            major, minor = qt_version.split('.')[:2]
            if int(major) == 6 and int(minor) < 10:
                log_warning(f"Qt {qt_version} detected. Some 6.10+ features may be unavailable")
        except (ValueError, IndexError):
            log_warning(f"Could not parse Qt version: {qt_version}")
        
        return QApplication, qInstallMessageHandler, Qt, QTimer
    except ImportError as e:
        log_error(f"PySide6 import failed: {e}")
        sys.exit(1)
