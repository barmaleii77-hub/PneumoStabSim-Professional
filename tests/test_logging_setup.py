"""Tests for the structured logging helpers."""

from __future__ import annotations

import logging
from pathlib import Path

from src.common import logging_setup


def _read_latest_log(log_dir: Path, app_name: str) -> str:
    log_files = sorted(log_dir.glob(f"{app_name}_*.log"))
    assert log_files, "expected at least one rotated log file"
    return log_files[-1].read_text(encoding="utf-8")


def test_init_logging_injects_environment_context(tmp_path: Path) -> None:
    """init_logging should add env_context metadata to log entries."""

    app_name = "PneumoTest"
    logger = logging_setup.init_logging(app_name, tmp_path)
    logger.info("hello from test")

    # Ensure records are flushed to disk for inspection.
    logging_setup._cleanup_logging(app_name)
    logging.getLogger(app_name).handlers.clear()

    log_content = _read_latest_log(tmp_path, app_name)

    lines_with_context = [
        line for line in log_content.splitlines() if "app=PneumoTest" in line
    ]
    assert lines_with_context, "expected log lines annotated with application context"
    sample_line = lines_with_context[0]
    assert "python=" in sample_line
    assert "os=" in sample_line

