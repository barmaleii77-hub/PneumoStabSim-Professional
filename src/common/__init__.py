"""
Common utilities package - WITH LOGGING
Provides logging, CSV export, and UI event tracking
"""

# Logging utilities - ВСЕГДА активны
from .logging_setup import (
    init_logging,
    get_category_logger,
    log_ui_event,
    log_geometry_change,
    log_simulation_step,
    log_performance_metric,
)

# CSV export utilities - импортируем ВСЕ нужные функции
from .csv_export import (
    export_timeseries_csv,
    export_snapshot_csv,
    export_state_snapshot_csv,
    get_default_export_dir,
    ensure_csv_extension,
)

__all__ = [
    # Logging
    "init_logging",
    "get_category_logger",
    "log_ui_event",
    "log_geometry_change",
    "log_simulation_step",
    "log_performance_metric",
    # CSV Export
    "export_timeseries_csv",
    "export_snapshot_csv",
    "export_state_snapshot_csv",
    "get_default_export_dir",
    "ensure_csv_extension",
]
