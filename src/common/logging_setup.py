"""
Logging setup with QueueHandler for non-blocking logging
Overwrites log file on each run, ensures proper cleanup
"""

import logging
import logging.handlers
import atexit
import queue
import sys
import os
import platform
from pathlib import Path
from typing import Optional
from datetime import datetime


# Global queue listener for cleanup
_queue_listener: Optional[logging.handlers.QueueListener] = None


def init_logging(app_name: str, log_dir: Path) -> logging.Logger:
    """Initialize application logging with non-blocking queue handler
    
    Features:
    - Overwrites log file on each run (mode='w')
    - Non-blocking logging via QueueHandler/QueueListener
    - UTC timestamps in ISO8601 format
    - PID/TID tracking
    - Automatic flush/close on exit
    
    Args:
        app_name: Application name for logger
        log_dir: Directory for log files
        
    Returns:
        Root logger instance
        
    References:
        https://docs.python.org/3/library/logging.handlers.html#queuehandler
    """
    global _queue_listener
    
    # Create log directory
    log_dir.mkdir(parents=True, exist_ok=True)
    
    # Log file path (overwrite on each run)
    log_file = log_dir / "run.log"
    
    # Create log queue for non-blocking writes
    log_queue = queue.Queue(-1)  # Unlimited size
    
    # Get root logger (or app-specific root)
    root_logger = logging.getLogger(app_name)
    root_logger.setLevel(logging.DEBUG)  # Capture all levels
    root_logger.propagate = False  # Don't propagate to Python root logger
    
    # Remove existing handlers
    root_logger.handlers.clear()
    
    # Create formatter with UTC time, PID/TID
    # Note: %f (microseconds) not supported by strftime, using custom format
    formatter = logging.Formatter(
        fmt='%(asctime)s | PID:%(process)d TID:%(thread)d | %(levelname)-8s | %(name)s | %(message)s',
        datefmt='%Y-%m-%dT%H:%M:%S'  # ISO8601 without microseconds
    )
    
    # File handler (overwrite mode)
    file_handler = logging.FileHandler(
        log_file,
        mode='w',  # Overwrite on each run
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    
    # Console handler (INFO and above)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    
    # Create QueueListener with both handlers
    # QueueListener runs in background thread
    _queue_listener = logging.handlers.QueueListener(
        log_queue,
        file_handler,
        console_handler,
        respect_handler_level=True
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


def _cleanup_logging(app_name: str):
    """Cleanup logging on application exit
    
    Stops QueueListener and flushes all handlers
    """
    global _queue_listener
    
    if _queue_listener:
        # Log shutdown
        logger = logging.getLogger(app_name)
        logger.info("=" * 70)
        logger.info("=== END RUN ===")
        logger.info("=" * 70)
        
        # Stop listener (waits for queue to empty)
        _queue_listener.stop()
        _queue_listener = None
        
        # Flush and close all handlers
        for handler in logger.handlers:
            handler.flush()
            handler.close()


def get_category_logger(category: str) -> logging.Logger:
    """Get logger for specific category
    
    Categories:
    - GEOM_UPDATE: Geometry updates
    - VALVE_EVENT: Valve state changes
    - FLOW: Flow rate events
    - PRESSURE_UPDATE: Pressure changes
    - THERMO_MODE: Thermodynamic mode changes
    - ODE_STEP: Integration steps
    - EXPORT: Data export operations
    - UI: UI events
    
    Args:
        category: Category name
        
    Returns:
        Logger instance for category
    """
    # Use PneumoStabSim as root, category as child
    logger = logging.getLogger(f"PneumoStabSim.{category}")
    # Don't set level here - it inherits from parent
    return logger


def log_valve_event(time: float, line: str, kind: str, state: bool, 
                   dp: float, mdot: float):
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


def log_pressure_update(time: float, location: str, pressure: float, 
                        temperature: float, mass: float):
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


def log_ode_step(time: float, step_num: int, dt: float, error: Optional[float] = None):
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


def log_export(operation: str, path: Path, rows: int):
    """Log export operation
    
    Args:
        operation: Operation type (TIMESERIES, SNAPSHOTS)
        path: Export file path
        rows: Number of rows exported
    """
    logger = get_category_logger("EXPORT")
    logger.info(
        f"operation={operation} | file={path.name} | rows={rows}"
    )


def log_ui_event(event: str, details: str = ""):
    """Log UI event
    
    Args:
        event: Event type
        details: Additional details
    """
    logger = get_category_logger("UI")
    msg = f"event={event}"
    if details:
        msg += f" | {details}"
    logger.info(msg)
