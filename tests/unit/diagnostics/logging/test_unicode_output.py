"""Regression tests for Unicode handling in structured logging."""

from __future__ import annotations

import json
import logging

import structlog

from src.diagnostics.logger_factory import configure_logging


def _extract_payload(raw: str) -> dict[str, object]:
    """Return the JSON payload embedded in the log message."""

    start = raw.find("{")
    if start == -1:
        raise AssertionError(f"No JSON payload found in log line: {raw!r}")
    return json.loads(raw[start:])


def test_unicode_roundtrip_in_console_logs(
    structlog_logger_config, capsys, caplog
) -> None:
    """Ensure Unicode messages are emitted without ASCII escaping."""

    structlog.reset_defaults()
    caplog.set_level(logging.INFO)
    configure_logging()

    logger = structlog_logger_config.build()
    logger.info("unicode-event", message="привет", emoji="✨", panel="графика")

    if caplog.records:
        raw_message = caplog.messages[0]
    else:
        captured = capsys.readouterr()
        raw_message = (captured.err or captured.out).strip()

    assert raw_message, "expected log output"
    assert "привет" in raw_message
    assert "✨" in raw_message
    assert "графика" in raw_message

    payload = _extract_payload(raw_message)
    assert payload["message"] == "привет"
    assert payload["emoji"] == "✨"
    assert payload["panel"] == "графика"

    structlog.reset_defaults()
