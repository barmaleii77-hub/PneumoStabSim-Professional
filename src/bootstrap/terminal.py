"""
Модуль настройки кодировки терминала.

Обеспечивает корректную работу Unicode (UTF-8) в терминале
на разных платформах (Windows, Linux, macOS).
"""

import sys
import os
import locale
import subprocess
from collections.abc import Callable


def configure_terminal_encoding(log_warning: Callable[[str], None]) -> None:
    """
    Настройка кодировки терминала для кроссплатформенной поддержки Unicode.

    Args:
        log_warning: Функция для логирования предупреждений
    """
    if sys.platform == "win32":
        chcp_command = [os.environ.get("COMSPEC", "cmd"), "/c", "chcp", "65001"]
        try:
            result = subprocess.run(
                chcp_command,
                capture_output=True,
                check=False,
                text=True,
            )
            if result.returncode != 0:
                log_warning(
                    "Failed to switch Windows code page to UTF-8 via chcp 65001"
                )
        except Exception as exc:
            log_warning(f"Unable to adjust Windows code page: {exc}")

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
        for candidate_locale in ("en_US.UTF-8", "C.UTF-8"):
            try:
                locale.setlocale(locale.LC_ALL, candidate_locale)
            except locale.Error:
                continue
            else:
                os.environ.setdefault("LC_ALL", candidate_locale)
                os.environ.setdefault("LANG", candidate_locale)
                break
