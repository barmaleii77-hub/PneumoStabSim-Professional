"""
Модуль диагностики - накопление warnings/errors и анализ логов.
"""

from .warnings import log_warning, log_error, print_warnings_errors
from .logs import run_log_diagnostics
from .logger_factory import configure_logging, get_logger, LoggerConfig
from .signal_tracing import (
    HAS_QT,
    MissingSignalError,
    SignalTraceRecord,
    SignalTracer,
    SignalTracerBridge,
    SignalTracingError,
)
from .profiler import (
    ProfilerOverlayState,
    export_profiler_report,
    get_profiler_overlay_defaults,
    load_profiler_overlay_state,
    record_profiler_overlay,
)

__all__ = [
    "log_warning",
    "log_error",
    "print_warnings_errors",
    "run_log_diagnostics",
    "configure_logging",
    "get_logger",
    "LoggerConfig",
    "SignalTracer",
    "SignalTraceRecord",
    "SignalTracingError",
    "MissingSignalError",
    "SignalTracerBridge",
    "HAS_QT",
    "ProfilerOverlayState",
    "get_profiler_overlay_defaults",
    "load_profiler_overlay_state",
    "record_profiler_overlay",
    "export_profiler_report",
]
