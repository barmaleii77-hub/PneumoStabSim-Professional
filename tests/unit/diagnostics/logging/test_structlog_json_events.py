"""Structured logging tests ensuring JSON payloads carry expected fields."""

import json
import logging
from typing import Any

import structlog

from src.diagnostics.logger_factory import configure_logging


def _extract_structlog_payload(caplog: Any, capsys: Any) -> tuple[str, dict[str, Any]]:
    """Return the rendered log line and its decoded payload."""

    def _from_text(value: str | None) -> tuple[str, dict[str, Any]] | None:
        if not value:
            return None
        text = value.strip()
        if not text:
            return None
        start = text.find("{")
        if start == -1:
            return None
        try:
            payload = json.loads(text[start:])
        except json.JSONDecodeError:
            return None
        return text, payload

    for record in caplog.records:
        message = getattr(record, "message", None) or record.getMessage()
        if isinstance(message, dict):
            serialised = json.dumps(message, ensure_ascii=False)
            return serialised, message
        if isinstance(message, str):
            parsed = _from_text(message)
            if parsed is not None:
                return parsed

    captured = capsys.readouterr()
    for stream in (captured.err, captured.out):
        parsed = _from_text(stream)
        if parsed is not None:
            return parsed

    raise AssertionError("structured log entry was not captured")


def test_structlog_json_contains_context(
    structlog_logger_config, caplog, capsys
) -> None:
    """Emit a JSON log event and assert mandatory fields and bound context exist."""

    structlog.reset_defaults()
    caplog.set_level(logging.INFO)
    capsys.readouterr()  # drain any prior stdout/stderr noise
    configure_logging()

    logger = structlog_logger_config.build()
    logger.info("diagnostic_event", action="bind-check")

    raw_message, payload = _extract_structlog_payload(caplog, capsys)

    assert json.loads(raw_message[raw_message.find("{") :]) == payload
    assert payload["event"] == "diagnostic_event"
    assert payload["level"] == "info"
    assert "timestamp" in payload
    assert payload["subsystem"] == "diagnostics"
    assert payload["component"] == "logger"
    assert payload["action"] == "bind-check"
    assert "diagnostic_event" in raw_message

    structlog.reset_defaults()
