"""Structured logging tests ensuring JSON payloads carry expected fields."""

import json
import logging

import structlog

from src.diagnostics.logger_factory import configure_logging


def test_structlog_json_contains_context(structlog_logger_config, caplog, capsys) -> None:
    """Emit a JSON log event and assert mandatory fields and bound context exist.

    The logger is pre-bound with ``subsystem="diagnostics"`` and ``component``
    context. After emitting an ``info`` event we expect the serialised JSON to
    include the message, severity level, ISO-8601 timestamp, and the bound
    context fields preserved by the processor chain.
    """

    structlog.reset_defaults()
    caplog.set_level(logging.INFO)
    capsys.readouterr()  # drain any prior stdout/stderr noise
    configure_logging()

    logger = structlog_logger_config.build()
    logger.info("diagnostic_event", action="bind-check")

    raw_message = None
    if caplog.records:
        raw_message = caplog.messages[0]
    else:
        captured = capsys.readouterr()
        raw_message = (captured.err or captured.out).strip()

    assert raw_message, "no log records captured"
    payload_start = raw_message.find("{")
    assert payload_start != -1, "expected JSON payload in log message"

    payload = json.loads(raw_message[payload_start:])
    assert payload["event"] == "diagnostic_event"
    assert payload["level"] == "info"
    assert "timestamp" in payload
    assert payload["subsystem"] == "diagnostics"
    assert payload["component"] == "logger"
    assert payload["action"] == "bind-check"

    structlog.reset_defaults()
