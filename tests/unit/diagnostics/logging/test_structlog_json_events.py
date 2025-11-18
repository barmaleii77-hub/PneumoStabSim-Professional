import json
import logging
from typing import Any

import structlog

from src.diagnostics.logger_factory import (
    _JSON_RENDERER_SERIALIZER,
    _flatten_event_payload,
    configure_logging,
)


def _normalise_payload(raw: str, payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
    """Flatten nested events and render with UTF-8 output for assertions."""

    flattened = _flatten_event_payload(payload)
    rendered = _JSON_RENDERER_SERIALIZER(flattened)
    return rendered, flattened


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
        return _normalise_payload(text, payload)

    messages: list[tuple[str, dict[str, Any]]] = []

    for record in caplog.records:
        message = getattr(record, "message", None) or record.getMessage()
        if isinstance(message, dict):
            messages.append(_normalise_payload(_JSON_RENDERER_SERIALIZER(message), message))
        if isinstance(message, str):
            parsed = _from_text(message)
            if parsed is not None:
                messages.append(parsed)

    if not messages:
        captured = capsys.readouterr()
        for stream in (captured.err, captured.out):
            parsed = _from_text(stream)
            if parsed is not None:
                messages.append(parsed)

    if not messages:
        raise AssertionError("structured log entry was not captured")
    if len(messages) > 1:
        raise AssertionError(f"expected a single structured log entry, got {len(messages)}")

    return messages[0]


def test_structlog_json_contains_context(
    structlog_logger_config, caplog, capsys
) -> None:
    """Emit a JSON log event and assert mandatory fields and bound context exist."""

    structlog.reset_defaults()
    caplog.set_level(logging.INFO)
    caplog.set_level(logging.INFO, logger="test.logger")
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
