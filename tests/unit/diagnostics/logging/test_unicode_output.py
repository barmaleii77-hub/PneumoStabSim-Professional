"""Regression tests for Unicode handling in structured logging."""

from __future__ import annotations

import json
import logging
from typing import Any

import structlog

from src.diagnostics.logger_factory import configure_logging, normalise_event_payload


def _extract_payload(raw: str) -> dict[str, object]:
    """Return the JSON payload embedded in the log message."""

    start = raw.find("{")
    if start == -1:
        raise AssertionError(f"No JSON payload found in log line: {raw!r}")
    return json.loads(raw[start:])


def _extract_structlog_output(caplog: Any, capsys: Any) -> tuple[str, dict[str, Any]]:
    captured = capsys.readouterr()
    for stream in (captured.err, captured.out):
        if stream.strip():
            try:
                payload = _extract_payload(stream)
            except AssertionError:
                continue
            return stream, normalise_event_payload(payload)

    for record in caplog.records:
        message = getattr(record, "message", None) or record.getMessage()
        if isinstance(message, dict):
            payload = normalise_event_payload(message)
            serialised = json.dumps(payload, ensure_ascii=False)
            return serialised, payload
        if isinstance(message, str) and message.strip():
            try:
                payload = _extract_payload(message)
            except AssertionError:
                continue
            return message, normalise_event_payload(payload)

    raise AssertionError("No structured log output captured")


def test_unicode_roundtrip_in_console_logs(
    structlog_logger_config, capsys, caplog
) -> None:
    """Ensure Unicode messages are emitted without ASCII escaping."""

    structlog.reset_defaults()
    caplog.set_level(logging.INFO)
    configure_logging()

    logger = structlog_logger_config.build()
    logger.info("unicode-event", message="привет", emoji="✨", panel="графика")

    raw_message, payload = _extract_structlog_output(caplog, capsys)

    assert raw_message.rstrip("\n") == json.dumps(payload, ensure_ascii=False)
    assert "привет" in raw_message
    assert "✨" in raw_message
    assert "графика" in raw_message

    assert payload["event"] == "unicode-event"
    assert payload["message"] == "привет"
    assert payload["emoji"] == "✨"
    assert payload["panel"] == "графика"

    structlog.reset_defaults()
