# -*- coding: utf-8 -*-
"""
Модуль bootstrap - инициализация окружения приложения.

Отвечает за:
- Настройку Qt и QtQuick3D окружения
- Конфигурацию терминала и кодировок
- Проверку версии Python
- Безопасный импорт Qt компонентов
"""

from .environment import setup_qtquick3d_environment, configure_qt_environment
from .terminal import configure_terminal_encoding
from .version_check import check_python_compatibility
from .qt_imports import safe_import_qt

__all__ = [
    "setup_qtquick3d_environment",
    "configure_qt_environment",
    "configure_terminal_encoding",
    "check_python_compatibility",
    "safe_import_qt",
]
