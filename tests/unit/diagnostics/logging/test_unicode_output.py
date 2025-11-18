"""Regression tests for Unicode handling in structured logging."""

from __future__ import annotations

import json
import logging
from typing import Any

import structlog

from src.diagnostics.logger_factory import (
    configure_logging,
    _flatten_event_payload,
    _json_dumps,
)


def _extract_payload(raw: str) -> dict[str, object]:
    """Return the JSON payload embedded in the log message."""

    start = raw.find("{")
    if start == -1:
        raise AssertionError(f"No JSON payload found in log line: {raw!r}")
    return json.loads(raw[start:])


def _normalise_payload(raw: str, payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    flattened = _flatten_event_payload(payload)
    rendered = _json_dumps(flattened)
    return rendered, flattened


def _extract_structlog_output(caplog: Any, capsys: Any) -> tuple[str, dict[str, Any]]:
    for record in caplog.records:
        message = getattr(record, "message", None) or record.getMessage()
        if isinstance(message, dict):
            return _normalise_payload(json.dumps(message, ensure_ascii=False), message)
        if isinstance(message, str) and message.strip():
            try:
                return _normalise_payload(message, _extract_payload(message))
            except AssertionError:
                continue
    captured = capsys.readouterr()
    for stream in (captured.err, captured.out):
        if stream.strip():
            try:
                return _normalise_payload(stream, _extract_payload(stream))
            except AssertionError:
                continue
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

    assert raw_message.strip() == json.dumps(payload, ensure_ascii=False)
    assert json.loads(raw_message[raw_message.find("{") :]) == payload
    assert "привет" in raw_message
    assert "✨" in raw_message
    assert "графика" in raw_message

    assert payload["event"] == "unicode-event"
    assert payload["message"] == "привет"
    assert payload["emoji"] == "✨"
    assert payload["panel"] == "графика"

    structlog.reset_defaults()
