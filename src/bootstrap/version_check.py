# -*- coding: utf-8 -*-
"""
Модуль проверки совместимости версии Python.

Проект таргетирует Python 3.13+. Позволяет обходить проверку
через переменную окружения PSS_IGNORE_PYTHON_CHECK=1.
"""
import sys
import os
from typing import Callable


def check_python_compatibility(
    log_warning: Callable[[str], None], log_error: Callable[[str], None]
) -> None:
    """
    Проверка версии Python: проект требует Python 3.13+

    Args:
        log_warning: Функция для логирования предупреждений
        log_error: Функция для логирования ошибок

    Raises:
        SystemExit: Если версия Python < 3.13 и проверка не обойдена
    """
    # Позволяем обходить проверку при явном запросе
    if os.environ.get("PSS_IGNORE_PYTHON_CHECK") == "1":
        log_warning("Python version check bypassed via PSS_IGNORE_PYTHON_CHECK=1")
        return

    version = sys.version_info
    if version < (3, 13):
        log_error("Python 3.13+ required. Please upgrade Python.")
        sys.exit(1)
