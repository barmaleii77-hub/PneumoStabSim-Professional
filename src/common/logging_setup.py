"""
Logging setup with QueueHandler for non-blocking logging
Overwrites log file on each run, ensures proper cleanup
УЛУЧШЕННАЯ ВЕРСИЯ с ротацией и контекстными логгерами
"""

import logging
import logging.handlers
import atexit
import queue
import sys
import os
import platform
from pathlib import Path
from typing import Any, Mapping, Optional
from datetime import datetime
import traceback


# Global queue listener for cleanup
_queue_listener: Optional[logging.handlers.QueueListener] = None
_logger_registry: dict[str, logging.Logger] = {}


class ContextualFilter(logging.Filter):
    """Добавляет контекстную информацию к логам"""

    def __init__(self, context: Optional[Mapping[str, Any]] = None) -> None:
        super().__init__()
        self.context: dict[str, Any] = dict(context or {})

    def filter(self, record: logging.LogRecord) -> bool:
        # Добавляем контекст к каждому record
        for key, value in self.context.items():
            setattr(record, key, value)
        return True


class ColoredFormatter(logging.Formatter):
    """Форматтер с цветами для консоли (опционально)"""

    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[32m",  # Green
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[35m",  # Magenta
        "RESET": "\033[0m",
    }

    def format(self, record: logging.LogRecord) -> str:
        if hasattr(sys.stdout, "isatty") and sys.stdout.isatty():
            levelname = record.levelname
            if levelname in self.COLORS:
                record.levelname = (
                    f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
                )
        return super().format(record)


def init_logging(
    app_name: str,
    log_dir: Path,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5,
    console_output: bool = False,
) -> logging.Logger:
    """Initialize application logging with non-blocking queue handler

    УЛУЧШЕНИЯ v4.9.5:
    - Ротация логов (max_bytes, backup_count)
    - Опциональный вывод в консоль
    - Цветной вывод для консоли
    - Контекстные фильтры

    Features:
    - Log rotation with configurable size/count
    - Non-blocking logging via QueueHandler/QueueListener
    - UTC timestamps in ISO8601 format
    - PID/TID tracking
    - Automatic flush/close on exit
    - Optional console output with colors

    Args:
        app_name: Application name for logger
        log_dir: Directory for log files
        max_bytes: Maximum log file size before rotation (default 10MB)
        backup_count: Number of backup files to keep (default 5)
        console_output: Enable console output (default False)

    Returns:
        Root logger instance

    References:
        https://docs.python.org/3/library/logging.handlers.html#queuehandler
    """
    global _queue_listener

    # Create log directory
    log_dir.mkdir(parents=True, exist_ok=True)

    # Log file path with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"{app_name}_{timestamp}.log"

    # Также сохраняем копию в run.log для совместимости
    run_log = log_dir / "run.log"

    # Create log queue for non-blocking writes
    log_queue: "queue.Queue[logging.LogRecord]" = queue.Queue(-1)  # Unlimited size

    # Get root logger (or app-specific root)
    root_logger = logging.getLogger(app_name)
    root_logger.setLevel(logging.DEBUG)  # Capture all levels
    root_logger.propagate = False  # Don't propagate to Python root logger

    # Remove existing handlers
    root_logger.handlers.clear()

    # ✅ УЛУЧШЕННЫЙ ФОРМАТТЕР с микросекундами
    class MicrosecondFormatter(logging.Formatter):
        """Форматтер с микросекундами"""

        converter = datetime.fromtimestamp

        def formatTime(
            self, record: logging.LogRecord, datefmt: Optional[str] = None
        ) -> str:
            ct = self.converter(record.created)
            if datefmt:
                s = ct.strftime(datefmt)
            else:
                s = ct.strftime("%Y-%m-%dT%H:%M:%S")
                s = f"{s}.{int(record.msecs):03d}"
            return s

    formatter = MicrosecondFormatter(
        fmt="%(asctime)s | PID:%(process)d TID:%(thread)d | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
    )

    # ✅ РОТИРУЮЩИЙСЯ FILE HANDLER
    rotating_handler = logging.handlers.RotatingFileHandler(
        log_file,
        mode="a",
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    rotating_handler.setLevel(logging.DEBUG)
    rotating_handler.setFormatter(formatter)

    # ✅ ДОПОЛНИТЕЛЬНЫЙ HANDLER для run.log (всегда перезаписываем)
    run_handler = logging.FileHandler(run_log, mode="w", encoding="utf-8")
    run_handler.setLevel(logging.DEBUG)
    run_handler.setFormatter(formatter)

    handlers = [rotating_handler, run_handler]

    # ✅ ОПЦИОНАЛЬНЫЙ CONSOLE HANDLER
    if console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)  # Только INFO+ в консоль
        console_handler.setFormatter(
            ColoredFormatter(fmt="%(levelname)-8s | %(name)s | %(message)s")
        )
        handlers.append(console_handler)

    # Create QueueListener with ALL handlers
    _queue_listener = logging.handlers.QueueListener(
        log_queue, *handlers, respect_handler_level=True
    )
    _queue_listener.start()

    # Add QueueHandler to root logger (non-blocking)
    queue_handler = logging.handlers.QueueHandler(log_queue)
    root_logger.addHandler(queue_handler)

    # Register cleanup on exit
    atexit.register(_cleanup_logging, app_name)

    # Log startup information
    root_logger.info("=" * 70)
    root_logger.info(f"=== START RUN: {app_name} ===")
    root_logger.info("=" * 70)
    root_logger.info(f"Python version: {sys.version}")
    root_logger.info(f"Platform: {platform.platform()}")
    root_logger.info(f"Process ID: {os.getpid()}")
    root_logger.info(f"Log file: {log_file.absolute()}")
    root_logger.info(f"Run log: {run_log.absolute()}")
    root_logger.info(f"Max log size: {max_bytes / 1024 / 1024:.1f} MB")
    root_logger.info(f"Backup count: {backup_count}")
    root_logger.info(f"Timestamp: {datetime.utcnow().isoformat()}Z")

    # Log package versions
    try:
        import PySide6

        root_logger.info(f"PySide6 version: {PySide6.__version__}")
    except (ImportError, AttributeError):
        pass

    try:
        import numpy

        root_logger.info(f"NumPy version: {numpy.__version__}")
    except (ImportError, AttributeError):
        pass

    try:
        import scipy

        root_logger.info(f"SciPy version: {scipy.__version__}")
    except (ImportError, AttributeError):
        pass

    root_logger.info("=" * 70)

    return root_logger


def _cleanup_logging(app_name: str) -> None:
    """Cleanup logging on application exit

    Stops QueueListener and flushes all handlers
    """
    global _queue_listener

    if _queue_listener:
        # Log shutdown
        logger = logging.getLogger(app_name)
        logger.info("=" * 70)
        logger.info("=== END RUN ===")
        logger.info(f"Shutdown at: {datetime.utcnow().isoformat()}Z")
        logger.info("=" * 70)

        # Stop listener (waits for queue to empty)
        _queue_listener.stop()
        _queue_listener = None

        # Flush and close all handlers
        for handler in logger.handlers:
            try:
                handler.flush()
            except Exception:
                pass
            try:
                handler.close()
            except Exception:
                pass


def get_category_logger(
    category: str, context: Optional[Mapping[str, Any]] = None
) -> logging.Logger:
    """Get logger for specific category with optional context

    УЛУЧШЕНИЯ v4.9.5:
    - Кэширование логгеров
    - Контекстные фильтры
    - Автоматическое именование

    Categories:
    - GEOM_UPDATE: Geometry updates
    - VALVE_EVENT: Valve state changes
    - FLOW: Flow rate events
    - PRESSURE_UPDATE: Pressure changes
    - THERMO_MODE: Thermodynamic mode changes
    - ODE_STEP: Integration steps
    - EXPORT: Data export operations
    - UI: UI events
    - GRAPHICS: Graphics changes
    - IBL: IBL events
    - QML: QML events
    - PYTHON: Python events

    Args:
        category: Category name
        context: Optional context dict to add to all log records

    Returns:
        Logger instance for category
    """
    global _logger_registry

    # Кэшируем логгеры
    cache_key = f"{category}_{id(context)}"
    if cache_key in _logger_registry:
        return _logger_registry[cache_key]

    # Use PneumoStabSim as root, category as child
    logger = logging.getLogger(f"PneumoStabSim.{category}")

    # Добавляем контекстный фильтр если нужен
    if context:
        logger.addFilter(ContextualFilter(context))

    # Сохраняем в кэш
    _logger_registry[cache_key] = logger

    return logger


# ============================================================================
# СПЕЦИАЛИЗИРОВАННЫЕ ЛОГГЕРЫ
# ============================================================================


def log_valve_event(
    time: float, line: str, kind: str, state: bool, dp: float, mdot: float
) -> None:
    """Log valve event with structured fields

    Args:
        time: Simulation time (s)
        line: Line identifier (A1, B1, A2, B2, or TANK)
        kind: Valve kind (CV_ATMO, CV_TANK, RELIEF_MIN, etc.)
        state: Valve state (True=open, False=closed)
        dp: Pressure difference (Pa)
        mdot: Mass flow rate (kg/s)
    """
    logger = get_category_logger("VALVE_EVENT")
    logger.info(
        f"t={time:.6f}s | line={line} | valve={kind} | "
        f"state={'OPEN' if state else 'CLOSED'} | "
        f"dp={dp:.2f}Pa | mdot={mdot:.6e}kg/s"
    )


def log_pressure_update(
    time: float, location: str, pressure: float, temperature: float, mass: float
) -> None:
    """Log pressure update with structured fields

    Args:
        time: Simulation time (s)
        location: Location (LINE_A1, LINE_B1, TANK, etc.)
        pressure: Pressure (Pa)
        temperature: Temperature (K)
        mass: Gas mass (kg)
    """
    logger = get_category_logger("PRESSURE_UPDATE")
    logger.debug(
        f"t={time:.6f}s | loc={location} | "
        f"p={pressure:.2f}Pa | T={temperature:.2f}K | m={mass:.6e}kg"
    )


def log_ode_step(
    time: float, step_num: int, dt: float, error: Optional[float] = None
) -> None:
    """Log ODE integration step

    Args:
        time: Simulation time (s)
        step_num: Step number
        dt: Time step used (s)
        error: Integration error (optional)
    """
    logger = get_category_logger("ODE_STEP")
    msg = f"t={time:.6f}s | step={step_num} | dt={dt:.6e}s"
    if error is not None:
        msg += f" | error={error:.6e}"
    logger.debug(msg)


def log_export(operation: str, path: Path, rows: int) -> None:
    """Log export operation

    Args:
        operation: Operation type (TIMESERIES, SNAPSHOTS)
        path: Export file path
        rows: Number of rows exported
    """
    logger = get_category_logger("EXPORT")
    logger.info(f"operation={operation} | file={path.name} | rows={rows}")


def log_ui_event(event: str, details: str = "", **kwargs: Any) -> None:
    """Log UI event with optional context

    Args:
        event: Event type
        details: Additional details
        **kwargs: Additional context to log
    """
    logger = get_category_logger("UI")
    msg = f"event={event}"
    if details:
        msg += f" | {details}"

    # Добавляем дополнительный контекст
    if kwargs:
        context_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        msg += f" | {context_str}"

    logger.info(msg)


def log_geometry_change(
    param_name: str, old_value: float, new_value: float, **kwargs: Any
) -> None:
    """Log geometry parameter change

    Args:
        param_name: Parameter name
        old_value: Previous value
        new_value: New value
        **kwargs: Additional context
    """
    logger = get_category_logger("GEOMETRY")
    msg = f"param={param_name} | {old_value} → {new_value}"

    if kwargs:
        context_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        msg += f" | {context_str}"

    logger.info(msg)


def log_simulation_step(step_num: int, sim_time: float, dt: float) -> None:
    """Log simulation step

    Args:
        step_num: Step number
        sim_time: Simulation time (s)
        dt: Time step (s)
    """
    logger = get_category_logger("SIMULATION")
    logger.debug(f"step={step_num} | t={sim_time:.6f}s | dt={dt:.6e}s")


def log_performance_metric(metric_name: str, value: float, unit: str = "") -> None:
    """Log performance metric

    Args:
        metric_name: Metric name
        value: Metric value
        unit: Unit of measurement (optional)
    """
    logger = get_category_logger("PERFORMANCE")
    msg = f"metric={metric_name} | value={value:.6f}"
    if unit:
        msg += f" | unit={unit}"
    logger.info(msg)


# ============================================================================
# EXCEPTION LOGGING
# ============================================================================


def log_exception(exc: Exception, context: str = "", **kwargs: Any) -> None:
    """Log exception with full traceback and context

    Args:
        exc: Exception to log
        context: Context description
        **kwargs: Additional context
    """
    logger = get_category_logger("EXCEPTION")

    msg = f"Exception: {type(exc).__name__}: {exc}"
    if context:
        msg = f"{context} | {msg}"

    if kwargs:
        context_str = " | ".join(f"{k}={v}" for k, v in kwargs.items())
        msg += f" | {context_str}"

    logger.error(msg)
    logger.error(f"Traceback:\n{traceback.format_exc()}")


# ============================================================================
# UTILITY FUNCTIONS
# ============================================================================


def rotate_old_logs(log_dir: Path, keep_count: int = 10) -> None:
    """Удаляет старые лог-файлы, оставляя только последние N

    Args:
        log_dir: Директория с логами
        keep_count: Сколько последних файлов оставить (0 = удалить все)
    """
    if not log_dir.exists():
        return

    # Находим все лог-файлы с timestamp
    log_files = sorted(
        list(log_dir.glob("PneumoStabSim_*.log")),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )

    # Если keep_count == 0 — удаляем все timestamp-логи
    if keep_count <= 0:
        for lf in log_files:
            try:
                lf.unlink()
                print(f"🗑️  Удален лог: {lf.name}")
            except Exception as e:
                print(f"⚠️  Не удалось удалить {lf.name}: {e}")
        # Также очищаем run.log, если существует
        run_log = log_dir / "run.log"
        try:
            if run_log.exists():
                run_log.unlink()
                print("🗑️  Удален старый run.log")
        except Exception as e:
            print(f"⚠️  Не удалось удалить run.log: {e}")
        return

    # Обычный режим: оставляем N последних
    for old_log in log_files[keep_count:]:
        try:
            old_log.unlink()
            print(f"🗑️  Удален старый лог: {old_log.name}")
        except Exception as e:
            print(f"⚠️  Не удалось удалить {old_log.name}: {e}")
