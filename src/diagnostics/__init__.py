# -*- coding: utf-8 -*-
"""
Модуль диагностики - накопление warnings/errors и анализ логов.
"""

from .warnings import log_warning, log_error, print_warnings_errors
from .logs import run_log_diagnostics
from .signal_tracing import (
    HAS_QT,
    MissingSignalError,
    SignalTraceRecord,
    SignalTracer,
    SignalTracerBridge,
    SignalTracingError,
)

__all__ = [
    "log_warning",
    "log_error",
    "print_warnings_errors",
    "run_log_diagnostics",
    "SignalTracer",
    "SignalTraceRecord",
    "SignalTracingError",
    "MissingSignalError",
    "SignalTracerBridge",
    "HAS_QT",
]
