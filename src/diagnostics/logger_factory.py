"""Centralised logging configuration with graceful Structlog degradation.

The diagnostics stack historically mixed ``logging`` formatters, ad-hoc
``print`` statements, and bespoke JSON encoders.  This module establishes a
single entry-point for configuring :mod:`structlog` and exposing helpers that
return bound loggers ready for structured output.  When :mod:`structlog` is not
installed (as is the case in the lean execution environment used for the kata)
the helpers transparently fall back to a lightweight wrapper around the standard
:mod:`logging` module so that imports succeed and the rest of the application can
continue to record diagnostics.

Usage
-----

>>> from src.diagnostics.logger_factory import configure_logging, get_logger
>>> configure_logging()
>>> log = get_logger("diagnostics.example").bind(component="demo")
>>> log.info("started", details={"phase": 5})

All Python loggers (including modules that still rely on ``logging.getLogger``)
share the same structlog processor chain which renders UTF-8 JSON directly to
the configured handlers.  The standard library bridge keeps formatting minimal
to avoid double-encoding structured events while still emitting human-readable
output when :mod:`structlog` is unavailable.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import date, datetime
from types import ModuleType
from typing import Any, Protocol, runtime_checkable
from collections.abc import Iterable, Mapping
from functools import partial

try:  # pragma: no cover - exercised indirectly by tests
    import structlog
    from structlog.stdlib import BoundLogger as _StructlogBoundLogger
except ModuleNotFoundError:  # pragma: no cover - fallback exercised in kata env
    structlog = None  # type: ignore[assignment]
    _StructlogBoundLogger = None

    # Provide a very small compatibility shim so that modules importing
    # ``structlog.stdlib`` for typing continue to work in environments where the
    # dependency is unavailable.  Only the pieces exercised by the test-suite are
    # emulated which keeps the shim intentionally lightweight.
    stdlib_shim = ModuleType("structlog.stdlib")
    stdlib_shim.BoundLogger = None  # placeholder, assigned after class definition
    stdlib_shim.BoundLoggerBase = object

    class _ProcessorFormatter(logging.Formatter):  # pragma: no cover - shim
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__("%(message)s")

    class _LoggerFactory:  # pragma: no cover - shim
        def __call__(
            self, name: str = "root", *args: Any, **kwargs: Any
        ) -> logging.Logger:
            return logging.getLogger(name)

    stdlib_shim.ProcessorFormatter = _ProcessorFormatter
    stdlib_shim.LoggerFactory = _LoggerFactory

    structlog_shim = ModuleType("structlog")
    structlog_shim.stdlib = stdlib_shim
    structlog_shim.is_configured = lambda: False  # type: ignore[attr-defined]
    structlog_shim.configure = lambda *_, **__: None  # type: ignore[attr-defined]
    structlog_shim.get_logger = lambda name=None: logging.getLogger(name)  # type: ignore[attr-defined]
    structlog_shim.contextvars = ModuleType("structlog.contextvars")
    structlog_shim.contextvars.merge_contextvars = lambda *_, **__: {}  # type: ignore[attr-defined]
    structlog_shim.processors = ModuleType("structlog.processors")
    structlog_shim.processors.add_log_level = (
        lambda logger, name, event_dict: event_dict
    )  # type: ignore[attr-defined]
    structlog_shim.processors.TimeStamper = lambda *_, **__: (  # type: ignore[attr-defined]
        lambda logger, name, event_dict: event_dict
    )
    structlog_shim.processors.StackInfoRenderer = lambda *_, **__: (  # type: ignore[attr-defined]
        lambda logger, name, event_dict: event_dict
    )
    structlog_shim.processors.format_exc_info = (
        lambda logger, name, event_dict: event_dict
    )  # type: ignore[attr-defined]

    class _JSONRenderer:  # pragma: no cover - shim
        def __call__(self, logger: Any, name: str, event_dict: dict[str, Any]) -> str:
            payload = dict(_flatten_event_payload(event_dict))
            payload.setdefault("event", name)
            return _JSON_RENDERER_SERIALIZER(payload)

    structlog_shim.processors.JSONRenderer = _JSONRenderer  # type: ignore[attr-defined]

    import sys

    sys.modules.setdefault("structlog", structlog_shim)
    sys.modules.setdefault("structlog.stdlib", stdlib_shim)
    sys.modules.setdefault("structlog.contextvars", structlog_shim.contextvars)
    sys.modules.setdefault("structlog.processors", structlog_shim.processors)


@runtime_checkable
class LoggerProtocol(Protocol):
    """Common interface implemented by structlog and fallback loggers."""

    def bind(self, **kwargs: Any) -> LoggerProtocol: ...

    def debug(self, event: str, **kwargs: Any) -> None: ...

    def info(self, event: str, **kwargs: Any) -> None: ...

    def warning(self, event: str, **kwargs: Any) -> None: ...

    def error(self, event: str, **kwargs: Any) -> None: ...

    def exception(self, event: str, **kwargs: Any) -> None: ...

    def setLevel(self, level: int) -> None: ...


class _FallbackBoundLogger(LoggerProtocol):
    """Minimal ``structlog`` compatible logger backed by :mod:`logging`."""

    def __init__(
        self,
        base_logger: logging.Logger,
        context: dict[str, Any] | None = None,
    ) -> None:
        self._logger = base_logger
        self._context: dict[str, Any] = dict(context or {})

    # -------------------------------------------------------------- utils
    def _with_context(self, **extra: Any) -> dict[str, Any]:
        payload = dict(self._context)
        payload.update(extra)
        return payload

    @staticmethod
    def _normalise_for_json(value: Any) -> Any:
        if isinstance(value, (str, int, float, bool)) or value is None:
            return value
        if isinstance(value, (datetime, date)):
            return value.isoformat()
        if isinstance(value, Mapping):
            return {
                str(key): _FallbackBoundLogger._normalise_for_json(val)
                for key, val in value.items()
            }
        if isinstance(value, (list, tuple, set, frozenset)):
            return [_FallbackBoundLogger._normalise_for_json(item) for item in value]
        return repr(value)

    @classmethod
    def _render_json(
        cls, structured_payload: Mapping[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        normalised = {
            key: cls._normalise_for_json(value)
            for key, value in structured_payload.items()
        }
        try:
            rendered = json.dumps(normalised, ensure_ascii=False, sort_keys=True)
        except (TypeError, ValueError):  # pragma: no cover - defensive path
            fallback_payload = {
                key: cls._normalise_for_json(repr(value))
                for key, value in structured_payload.items()
            }
            rendered = json.dumps(fallback_payload, ensure_ascii=False, sort_keys=True)
            normalised = fallback_payload
        return rendered, normalised

    @staticmethod
    def _structured_payload(event: str, payload: dict[str, Any]) -> dict[str, Any]:
        structured = dict(payload)
        structured.setdefault("event", event)
        return structured

    def _log(self, level: int, event: str, **kwargs: Any) -> None:
        payload_kwargs = dict(kwargs)
        log_kwargs: dict[str, Any] = {}
        for key in ("exc_info", "stack_info", "extra"):
            if key in payload_kwargs:
                log_kwargs[key] = payload_kwargs.pop(key)

        payload = self._with_context(**payload_kwargs)
        structured_payload = self._structured_payload(event, payload)
        message, json_payload = self._render_json(structured_payload)

        existing_extra = log_kwargs.get("extra")
        if isinstance(existing_extra, Mapping):
            merged_extra = dict(existing_extra)
            merged_extra.update(json_payload)
        else:
            merged_extra = dict(json_payload)
        log_kwargs["extra"] = merged_extra

        self._logger.log(level, message, **log_kwargs)

    # -------------------------------------------------------------- api
    def bind(self, **kwargs: Any) -> _FallbackBoundLogger:
        if not kwargs:
            return self
        return _FallbackBoundLogger(self._logger, self._with_context(**kwargs))

    def debug(self, event: str, **kwargs: Any) -> None:
        self._log(logging.DEBUG, event, **kwargs)

    def info(self, event: str, **kwargs: Any) -> None:
        self._log(logging.INFO, event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        self._log(logging.WARNING, event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        self._log(logging.ERROR, event, **kwargs)

    def exception(self, event: str, **kwargs: Any) -> None:
        # logging.Logger.exception always records ``exc_info=True``
        payload_kwargs = dict(kwargs)
        log_kwargs: dict[str, Any] = {}
        for key in ("exc_info", "stack_info", "extra"):
            if key in payload_kwargs:
                log_kwargs[key] = payload_kwargs.pop(key)

        payload = self._with_context(**payload_kwargs)
        structured_payload = self._structured_payload(event, payload)
        message, json_payload = self._render_json(structured_payload)

        existing_extra = log_kwargs.get("extra")
        if isinstance(existing_extra, Mapping):
            merged_extra = dict(existing_extra)
            merged_extra.update(json_payload)
        else:
            merged_extra = dict(json_payload)
        log_kwargs["extra"] = merged_extra

        self._logger.exception(message, **log_kwargs)

    def setLevel(self, level: int) -> None:
        self._logger.setLevel(level)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._logger, name)

    def __repr__(self) -> str:  # pragma: no cover - diagnostic helper
        return f"_FallbackBoundLogger(name={self._logger.name!r}, context={self._context!r})"


HAS_STRUCTLOG = structlog is not None

if not HAS_STRUCTLOG:
    stdlib_shim.BoundLogger = _FallbackBoundLogger  # type: ignore[name-defined]

_FALLBACK_LOGGER_CACHE: dict[str, _FallbackBoundLogger] = {}
_fallback_configured = False


class _StructlogBridgeFilter(logging.Filter):
    """Populate LogRecord attributes with structlog event payload."""

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - shim
        message = getattr(record, "msg", None)
        if isinstance(message, dict):
            for key, value in message.items():
                if key.startswith("_"):
                    continue
                if key in record.__dict__:
                    continue
                try:
                    setattr(record, key, value)
                except Exception:
                    continue
        return True


if HAS_STRUCTLOG:  # pragma: no cover - covered by integration when structlog present
    BoundLogger = _StructlogBoundLogger  # type: ignore[assignment]
else:  # pragma: no cover - exercised in kata env
    BoundLogger = _FallbackBoundLogger


DEFAULT_LOG_LEVEL = logging.INFO


def _json_dumps(payload: Mapping[str, Any], **kwargs: Any) -> str:
    """Serialise mappings to JSON without ASCII escaping."""

    # structlog's ``JSONRenderer`` passes ``event_key`` to the serializer; the
    # standard library encoder does not understand this parameter, so strip it
    # out before delegating to :func:`json.dumps`.
    kwargs.pop("event_key", None)
    kwargs.setdefault("ensure_ascii", False)
    kwargs.setdefault("default", str)
    return json.dumps(payload, **kwargs)


_JSON_RENDERER_SERIALIZER = partial(_json_dumps, ensure_ascii=False)


def _flatten_event_payload(event_dict: Mapping[str, Any]) -> dict[str, Any]:
    """Merge nested JSON payloads into the root event dictionary."""

    flattened = dict(event_dict)
    event_value = flattened.get("event")
    if isinstance(event_value, str):
        candidate = event_value.strip()
        if candidate.startswith("{") and candidate.endswith("}"):
            try:
                nested = json.loads(candidate)
            except ValueError:
                return flattened

            nested_event = nested.get("event")
            for key, value in nested.items():
                if key == "event":
                    continue
                flattened.setdefault(key, value)
            if nested_event is not None:
                flattened["event"] = nested_event
    return flattened


def _flatten_event_processor(
    logger: Any, name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Normalise nested JSON payloads before rendering."""

    record = event_dict.get("_record")
    if record is not None:
        for key, value in event_dict.items():
            if key.startswith("_"):
                continue
            try:
                setattr(record, key, value)
            except Exception:  # pragma: no cover - defensive best effort
                continue
    return _flatten_event_payload(event_dict)


def _json_renderer(logger: Any, name: str, event_dict: dict[str, Any]) -> str:
    """Render structured events as JSON with UTF-8 friendly output."""

    # ``ProcessorFormatter`` shares the event dictionary instance across
    # processors. ``json.dumps`` mutates neither the mapping nor the values but
    # copying keeps the renderer side-effect free and avoids surprises for
    # downstream formatters in custom pipelines.
    serialisable = _flatten_event_payload(dict(event_dict))
    if "event" not in serialisable and name:
        serialisable["event"] = name
    return _JSON_RENDERER_SERIALIZER(serialisable)


def _shared_processors() -> list[Any]:
    """Return the processors shared by stdlib + structlog pipelines."""

    if not HAS_STRUCTLOG:
        return []

    return [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]


def _configure_fallback_logging(level: int) -> None:
    """Initialise logging when structlog is unavailable."""

    global _fallback_configured
    root_logger = logging.getLogger()
    if not _fallback_configured:
        logging.basicConfig(
            level=level,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )
        _fallback_configured = True
    else:
        root_logger.setLevel(level)


def _ensure_stdlib_bridge(
    level: int,
    formatter: logging.Formatter | None = None,
    *,
    json_renderer: Any | None = None,
) -> None:
    """Configure the logging bridge for structlog or provide a fallback."""

    if not HAS_STRUCTLOG:
        _configure_fallback_logging(level)
        return

    handler = logging.StreamHandler()
    handler.addFilter(_StructlogBridgeFilter())
    if formatter is None:
        if json_renderer is None:
            json_renderer = _json_renderer
        formatter = structlog.stdlib.ProcessorFormatter(
            processors=[
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                _flatten_event_processor,
                json_renderer,
            ],
            foreign_pre_chain=_shared_processors(),
        )
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers[:] = [handler]
    root_logger.setLevel(level)


def configure_logging(
    *,
    level: int = DEFAULT_LOG_LEVEL,
    wrapper_class: type[object] | None = None,
    cache_logger_on_first_use: bool = True,
    processors: Iterable[Any] | None = None,
) -> None:
    """Initialise structlog and bridge stdlib loggers.

    Parameters
    ----------
    level:
        Log level applied to the root stdlib logger.  Defaults to
        :data:`logging.INFO`.
    wrapper_class:
        Custom wrapper used by structlog.  If omitted the stdlib compatible
        :class:`structlog.stdlib.BoundLogger` is used.
    cache_logger_on_first_use:
        Whether structlog should memoise the bound logger when it is first
        created.  Enabled by default as it reduces overhead in the hot path.
    processors:
        Optional iterable overriding the default processor chain.  The shared
        processors defined in :func:`_shared_processors` are always prepended so
        that contextual information is consistent across the application.
    """

    if not HAS_STRUCTLOG:
        _configure_fallback_logging(level)
        return

    # NB: _json_dumps sets ensure_ascii=False by default, so UTF-8 characters are serialized correctly.
    json_renderer = structlog.processors.JSONRenderer(
        serializer=_JSON_RENDERER_SERIALIZER,
        event_key="event",
    )
    chosen_wrapper = wrapper_class or structlog.stdlib.BoundLogger
    configured_processors = list(_shared_processors())
    if processors is not None:
        configured_processors.extend(processors)
    configured_processors.append(structlog.stdlib.ProcessorFormatter.wrap_for_formatter)

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            _flatten_event_processor,
            json_renderer,
        ],
        foreign_pre_chain=_shared_processors(),
    )

    structlog.configure(
        processors=configured_processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=chosen_wrapper,
        cache_logger_on_first_use=cache_logger_on_first_use,
    )

    _ensure_stdlib_bridge(level, formatter, json_renderer=json_renderer)


@dataclass(slots=True)
class LoggerConfig:
    """Declarative description of a structlog logger."""

    name: str
    level: int = DEFAULT_LOG_LEVEL
    context: tuple[tuple[str, object], ...] = ()

    def build(self) -> LoggerProtocol:
        logger = get_logger(self.name)
        if self.context:
            bind = getattr(logger, "bind", None)
            if callable(bind):
                logger = bind(**dict(self.context))
        if hasattr(logger, "setLevel"):
            # ``structlog`` bound loggers expose ``setLevel`` when using the
            # stdlib wrapper.
            logger.setLevel(self.level)  # type: ignore[attr-defined]
        return logger


def get_logger(name: str) -> LoggerProtocol:
    """Return a structlog bound logger, configuring defaults if needed."""

    if HAS_STRUCTLOG:
        if not structlog.is_configured():  # pragma: no cover - defensive path
            configure_logging()
        return structlog.get_logger(name)  # type: ignore[return-value]

    _configure_fallback_logging(DEFAULT_LOG_LEVEL)
    cached = _FALLBACK_LOGGER_CACHE.get(name)
    if cached is not None:
        return cached

    base_logger = logging.getLogger(name)
    fallback = _FallbackBoundLogger(base_logger)
    _FALLBACK_LOGGER_CACHE[name] = fallback
    return fallback


__all__ = [
    "DEFAULT_LOG_LEVEL",
    "HAS_STRUCTLOG",
    "BoundLogger",
    "LoggerConfig",
    "LoggerProtocol",
    "configure_logging",
    "get_logger",
]
