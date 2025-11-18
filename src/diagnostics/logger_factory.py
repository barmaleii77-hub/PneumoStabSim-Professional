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
import logging.handlers
import os
import queue
import threading
import time
from dataclasses import dataclass
from datetime import date, datetime
from types import ModuleType
from typing import Any, Protocol, runtime_checkable
from collections.abc import Iterable, Mapping

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
            return _json_dumps(payload)

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


@dataclass(slots=True)
class _QueueBundle:
    queue: "queue.Queue[logging.LogRecord]"
    listener: logging.handlers.QueueListener
    drop_counter: dict[str, int]
    poll_interval: float
    drain_delay: float


_QUEUE_BUNDLE: _QueueBundle | None = None


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

    event_value = event_dict.get("event")
    if event_value is None and name:
        event_dict["event"] = name
    elif event_value is not None and not isinstance(event_value, str):
        event_dict["event"] = str(event_value)

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


class _DroppingQueueHandler(logging.handlers.QueueHandler):
    """Queue handler that never blocks and records overflow statistics."""

    def __init__(
        self,
        log_queue: "queue.Queue[logging.LogRecord]",
        *,
        drop_counter: dict[str, int],
    ) -> None:
        super().__init__(log_queue)
        self._drop_counter = drop_counter

    def enqueue(self, record: logging.LogRecord) -> None:  # pragma: no cover - shim
        try:
            self.queue.put_nowait(record)
            return
        except queue.Full:
            self._drop_counter["dropped"] += 1

        try:
            self.queue.get_nowait()
        except queue.Empty:
            return

        try:
            self.queue.put_nowait(record)
        except queue.Full:
            self._drop_counter["dropped"] += 1


class _NonBlockingQueueListener(logging.handlers.QueueListener):
    """Queue listener that polls with a timeout to avoid blocking forever."""

    def __init__(
        self,
        log_queue: "queue.Queue[logging.LogRecord]",
        *handlers: logging.Handler,
        poll_interval: float = 0.1,
        drain_delay: float = 0.0,
        respect_handler_level: bool = False,
    ) -> None:
        super().__init__(
            log_queue, *handlers, respect_handler_level=respect_handler_level
        )
        self._poll_interval = poll_interval
        self._drain_delay = max(0.0, drain_delay)
        self._stop_event = threading.Event()

    def stop(self) -> None:  # pragma: no cover - thin wrapper
        self._stop_event.set()
        super().stop()

    def _monitor(self) -> None:  # pragma: no cover - shim
        has_task_done = hasattr(self.queue, "task_done")
        while not self._stop_event.is_set():
            try:
                record = self.queue.get(block=False)
            except queue.Empty:
                try:
                    record = self.queue.get(timeout=self._poll_interval)
                except queue.Empty:
                    continue

            if record is self._sentinel:
                break

            if self._drain_delay:
                time.sleep(self._drain_delay)

            self.handle(record)
            if has_task_done:
                self.queue.task_done()

        while True:
            try:
                record = self.queue.get(block=False)
            except queue.Empty:
                break

            if record is self._sentinel:
                break

            if self._drain_delay:
                time.sleep(self._drain_delay)

            self.handle(record)
            if has_task_done:
                self.queue.task_done()


def _stop_queue_listener() -> None:
    global _QUEUE_BUNDLE
    if _QUEUE_BUNDLE is None:
        return
    try:
        _QUEUE_BUNDLE.listener.stop()
    finally:
        _QUEUE_BUNDLE = None


def _install_queue_handler(
    root_logger: logging.Logger,
    handler: logging.Handler,
    *,
    queue_size: int,
    poll_interval: float,
    drain_delay: float,
) -> logging.Handler:
    global _QUEUE_BUNDLE

    _stop_queue_listener()

    bounded_size = max(1, int(queue_size))
    log_queue: "queue.Queue[logging.LogRecord]" = queue.Queue(bounded_size)
    drop_counter = {"dropped": 0, "max_size": bounded_size}

    queue_handler = _DroppingQueueHandler(log_queue, drop_counter=drop_counter)
    listener = _NonBlockingQueueListener(
        log_queue,
        handler,
        poll_interval=poll_interval,
        drain_delay=drain_delay,
        respect_handler_level=True,
    )
    listener.start()

    root_logger.handlers[:] = [queue_handler]
    _QUEUE_BUNDLE = _QueueBundle(
        queue=log_queue,
        listener=listener,
        drop_counter=drop_counter,
        poll_interval=poll_interval,
        drain_delay=drain_delay,
    )
    return queue_handler


def _queue_enabled(requested: bool) -> bool:
    if not requested:
        return False
    if os.environ.get("PSS_FORCE_LOG_QUEUE", "").strip().lower() in {
        "1",
        "true",
        "yes",
    }:
        return True
    if os.environ.get("PYTEST_CURRENT_TEST"):
        return False
    return True


def _configure_fallback_logging(
    level: int,
    *,
    use_queue_listener: bool,
    queue_size: int,
    queue_poll_interval: float,
    queue_drain_delay: float,
) -> None:
    """Initialise logging when structlog is unavailable."""

    global _fallback_configured
    root_logger = logging.getLogger()
    if use_queue_listener:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        )
        _install_queue_handler(
            root_logger,
            handler,
            queue_size=queue_size,
            poll_interval=queue_poll_interval,
            drain_delay=queue_drain_delay,
        )
        root_logger.setLevel(level)
        _fallback_configured = True
        return

    _stop_queue_listener()
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
    use_queue_listener: bool,
    queue_size: int,
    queue_poll_interval: float,
    queue_drain_delay: float,
) -> None:
    """Configure the logging bridge for structlog or provide a fallback."""

    if not HAS_STRUCTLOG:
        _configure_fallback_logging(
            level,
            use_queue_listener=use_queue_listener,
            queue_size=queue_size,
            queue_poll_interval=queue_poll_interval,
            queue_drain_delay=queue_drain_delay,
        )
        return

    handler = logging.StreamHandler()
    handler.addFilter(_StructlogBridgeFilter())
    if formatter is None:
        if json_renderer is None:
            json_renderer = structlog.processors.JSONRenderer(
                serializer=_json_dumps,
                ensure_ascii=False,
                default=str,
            )
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
    if use_queue_listener:
        _install_queue_handler(
            root_logger,
            handler,
            queue_size=queue_size,
            poll_interval=queue_poll_interval,
            drain_delay=queue_drain_delay,
        )
    else:
        _stop_queue_listener()
        root_logger.handlers[:] = [handler]
    root_logger.setLevel(level)


def configure_logging(
    *,
    level: int = DEFAULT_LOG_LEVEL,
    wrapper_class: type[object] | None = None,
    cache_logger_on_first_use: bool = True,
    processors: Iterable[Any] | None = None,
    use_queue_listener: bool = True,
    queue_size: int = 10000,
    queue_poll_interval: float = 0.1,
    queue_drain_delay: float = 0.0,
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
    use_queue_listener:
        Whether to offload emission to a non-blocking queue listener. Enabled by
        default to avoid blocking UI/simulation threads on IO-bound handlers.
    queue_size:
        Maximum number of records buffered by the queue listener before
        applying back-pressure via dropping the oldest entries.
    queue_poll_interval:
        Maximum time the background consumer waits before polling for new
        records using ``queue.get(block=False, timeout=...)`` semantics.
    queue_drain_delay:
        Optional sleep applied by the consumer between handling records to
        smooth bursts for slow downstream sinks.
    """

    queue_enabled = _queue_enabled(use_queue_listener)

    if not HAS_STRUCTLOG:
        _configure_fallback_logging(
            level,
            use_queue_listener=queue_enabled,
            queue_size=queue_size,
            queue_poll_interval=queue_poll_interval,
            queue_drain_delay=queue_drain_delay,
        )
        return

    json_renderer = structlog.processors.JSONRenderer(
        serializer=_json_dumps,
        ensure_ascii=False,
        default=str,
    )
    chosen_wrapper = wrapper_class or structlog.stdlib.BoundLogger
    configured_processors = list(_shared_processors())
    if processors is not None:
        configured_processors.extend(processors)
    configured_processors.extend((_flatten_event_processor, json_renderer))

    structlog.configure(
        processors=configured_processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=chosen_wrapper,
        cache_logger_on_first_use=cache_logger_on_first_use,
    )

    _ensure_stdlib_bridge(
        level,
        logging.Formatter("%(message)s"),
        json_renderer=json_renderer,
        use_queue_listener=queue_enabled,
        queue_size=queue_size,
        queue_poll_interval=queue_poll_interval,
        queue_drain_delay=queue_drain_delay,
    )


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

    _configure_fallback_logging(
        DEFAULT_LOG_LEVEL,
        use_queue_listener=_queue_enabled(True),
        queue_size=10000,
        queue_poll_interval=0.1,
        queue_drain_delay=0.0,
    )
    cached = _FALLBACK_LOGGER_CACHE.get(name)
    if cached is not None:
        return cached

    base_logger = logging.getLogger(name)
    fallback = _FallbackBoundLogger(base_logger)
    _FALLBACK_LOGGER_CACHE[name] = fallback
    return fallback


def get_logging_queue_stats() -> dict[str, int]:
    """Expose queue usage statistics for diagnostics and tests."""

    if _QUEUE_BUNDLE is None:
        return {"dropped": 0, "max_size": 0}
    return dict(_QUEUE_BUNDLE.drop_counter)


def shutdown_logging() -> None:
    """Stop background listeners to avoid leaking threads between tests."""

    _stop_queue_listener()
    logging.shutdown()


__all__ = [
    "DEFAULT_LOG_LEVEL",
    "HAS_STRUCTLOG",
    "BoundLogger",
    "LoggerConfig",
    "LoggerProtocol",
    "configure_logging",
    "get_logger",
    "get_logging_queue_stats",
    "shutdown_logging",
]
