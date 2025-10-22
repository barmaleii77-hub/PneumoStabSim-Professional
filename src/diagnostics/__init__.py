# -*- coding: utf-8 -*-
"""
Модуль диагностики - накопление warnings/errors и анализ логов.
"""

from .warnings import log_warning, log_error, print_warnings_errors
from .logs import run_log_diagnostics

__all__ = [
    "log_warning",
    "log_error",
    "print_warnings_errors",
    "run_log_diagnostics",
]
