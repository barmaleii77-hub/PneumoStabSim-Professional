# -*- coding: utf-8 -*-
"""
Модуль настройки кодировки терминала.

Обеспечивает корректную работу Unicode (UTF-8) в терминале
на разных платформах (Windows, Linux, macOS).
"""

import sys
import os
import locale
import subprocess
from typing import Callable


def configure_terminal_encoding(log_warning: Callable[[str], None]) -> None:
    """
    Настройка кодировки терминала для кроссплатформенной поддержки Unicode.

    Args:
        log_warning: Функция для логирования предупреждений
    """
    if sys.platform == "win32":
        try:
            subprocess.run(["chcp", "65001"], capture_output=True, check=False)
        except Exception:
            pass

        # На Windows используем UTF-8 writers
        try:
            import codecs

            if hasattr(sys.stdout, "buffer"):
                sys.stdout = codecs.getwriter("utf-8")(
                    sys.stdout.buffer, errors="replace"
                )
            if hasattr(sys.stderr, "buffer"):
                sys.stderr = codecs.getwriter("utf-8")(
                    sys.stderr.buffer, errors="replace"
                )
        except Exception as e:
            log_warning(f"UTF-8 setup: {e}")

    os.environ.setdefault("PYTHONIOENCODING", "utf-8")

    # На Unix-системах пытаемся установить UTF-8 локаль
    if sys.platform != "win32":
        try:
            locale.setlocale(locale.LC_ALL, "en_US.UTF-8")
        except locale.Error:
            try:
                locale.setlocale(locale.LC_ALL, "C.UTF-8")
            except locale.Error:
                pass  # Остаёмся на системной локали
