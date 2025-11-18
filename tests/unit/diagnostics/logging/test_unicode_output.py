"""Regression tests for Unicode handling in structured logging."""

from __future__ import annotations

import json
import logging
from typing import Any

import structlog

from src.diagnostics.logger_factory import (
    _JSON_RENDERER_SERIALIZER,
    _flatten_event_payload,
    configure_logging,
)


def _extract_payload(raw: str) -> dict[str, object]:
    """Return the JSON payload embedded in the log message."""

    start = raw.find("{")
    if start == -1:
        raise AssertionError(f"No JSON payload found in log line: {raw!r}")
    return json.loads(raw[start:])


def _normalise_payload(raw: str, payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    flattened = _flatten_event_payload(payload)
    rendered = _JSON_RENDERER_SERIALIZER(flattened)
    return rendered, flattened


def _extract_structlog_output(caplog: Any, capsys: Any) -> tuple[str, dict[str, Any]]:
    messages: list[tuple[str, dict[str, Any]]] = []

    for record in caplog.records:
        message = getattr(record, "message", None) or record.getMessage()
        if isinstance(message, dict):
            messages.append(_normalise_payload(_JSON_RENDERER_SERIALIZER(message), message))
            continue
        if isinstance(message, str) and message.strip():
            try:
                messages.append(_normalise_payload(message, _extract_payload(message)))
            except AssertionError:
                continue

    if not messages:
        captured = capsys.readouterr()
        for stream in (captured.err, captured.out):
            if stream.strip():
                try:
                    messages.append(_normalise_payload(stream, _extract_payload(stream)))
                except AssertionError:
                    continue

    if not messages:
        raise AssertionError("No structured log output captured")
    if len(messages) > 1:
        raise AssertionError(f"expected a single structured log entry, got {len(messages)}")

    return messages[0]


def test_unicode_roundtrip_in_console_logs(
    structlog_logger_config, caplog, capsys
) -> None:
    """Ensure Unicode messages are emitted without ASCII escaping."""

    structlog.reset_defaults()
    caplog.set_level(logging.INFO)
    caplog.set_level(logging.INFO, logger="test.logger")
    configure_logging()

    logger = structlog_logger_config.build()
    logger.info("unicode-event", message="привет", emoji="✨", panel="графика")

    raw_message, payload = _extract_structlog_output(caplog, capsys)

    assert json.loads(raw_message[raw_message.find("{") :]) == payload
    assert "привет" in raw_message
    assert "✨" in raw_message
    assert "графика" in raw_message

    assert payload["event"] == "unicode-event"
    assert payload["message"] == "привет"
    assert payload["emoji"] == "✨"
    assert payload["panel"] == "графика"

    structlog.reset_defaults()
