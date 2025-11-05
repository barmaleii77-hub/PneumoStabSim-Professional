"""Centralised logging configuration using structlog.

The diagnostics stack historically mixed ``logging`` formatters, ad-hoc
``print`` statements, and bespoke JSON encoders.  This module establishes a
single entry-point for configuring :mod:`structlog` and exposing helpers that
return bound loggers ready for structured output.

Usage
-----

>>> from src.diagnostics.logger_factory import configure_logging, get_logger
>>> configure_logging()
>>> log = get_logger("diagnostics.example").bind(component="demo")
>>> log.info("started", details={"phase": 5})

All Python loggers (including modules that still rely on ``logging.getLogger``)
are routed through a :class:`structlog.stdlib.ProcessorFormatter` that renders
JSON objects.  This keeps legacy call sites working while allowing new code to
take advantage of structured logging semantics.
"""

from __future__ import annotations

import importlib
import importlib.util
import logging
from dataclasses import dataclass
from typing import Any, Iterable, Optional


_STRUCTLOG_SPEC = importlib.util.find_spec("structlog")
if _STRUCTLOG_SPEC is not None:
    structlog = importlib.import_module("structlog")
else:  # pragma: no cover - executed when structlog is absent
    structlog = None


DEFAULT_LOG_LEVEL = logging.INFO


def _shared_processors() -> list[Any]:
    """Return processors shared by stdlib + structlog pipelines."""

    if structlog is None:
        return []

    return [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]


def _ensure_stdlib_bridge(level: int) -> None:
    """Configure the logging bridge for structlog or provide a fallback."""

    if structlog is not None:
        formatter = structlog.stdlib.ProcessorFormatter(
            processor=structlog.processors.JSONRenderer(),
            foreign_pre_chain=_shared_processors(),
        )

        handler = logging.StreamHandler()
        handler.setFormatter(formatter)

        root_logger = logging.getLogger()
        root_logger.handlers[:] = [handler]
        root_logger.setLevel(level)
        return

    handler = logging.StreamHandler()
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(name)s [%(levelname)s] %(message)s")
    )

    root_logger = logging.getLogger()
    root_logger.handlers[:] = [handler]
    root_logger.setLevel(level)


_FALLBACK_CONFIGURED = False
_FALLBACK_LEVEL = DEFAULT_LOG_LEVEL


class _FallbackBoundLogger:
    """Minimal structlog-compatible logger based on :mod:`logging`."""

    __slots__ = ("_logger", "_context")

    def __init__(self, name: str, *, context: dict[str, object] | None = None) -> None:
        self._logger = logging.getLogger(name)
        self._context: dict[str, object] = dict(context or {})

    def bind(self, **kwargs: object) -> "_FallbackBoundLogger":
        if not kwargs:
            return self
        merged = {**self._context, **kwargs}
        return _FallbackBoundLogger(self._logger.name, context=merged)

    def setLevel(self, level: int) -> None:  # pragma: no cover - passthrough
        self._logger.setLevel(level)

    def _format(self, event: str, event_kwargs: dict[str, object]) -> str:
        parts = [event]
        if self._context:
            parts.append(f"context={self._context}")
        if event_kwargs:
            parts.append(f"event={event_kwargs}")
        return " | ".join(parts)

    def _log(self, level: int, event: str, **event_kwargs: object) -> None:
        message = self._format(event, event_kwargs)
        self._logger.log(level, message)

    def debug(self, event: str, **event_kwargs: object) -> None:
        self._log(logging.DEBUG, event, **event_kwargs)

    def info(self, event: str, **event_kwargs: object) -> None:
        self._log(logging.INFO, event, **event_kwargs)

    def warning(self, event: str, **event_kwargs: object) -> None:
        self._log(logging.WARNING, event, **event_kwargs)

    def error(self, event: str, **event_kwargs: object) -> None:
        self._log(logging.ERROR, event, **event_kwargs)

    def exception(self, event: str, **event_kwargs: object) -> None:
        message = self._format(event, event_kwargs)
        self._logger.exception(message)

    def critical(self, event: str, **event_kwargs: object) -> None:
        self._log(logging.CRITICAL, event, **event_kwargs)

    def __getattr__(self, item: str) -> Any:  # pragma: no cover - passthrough
        return getattr(self._logger, item)


def configure_logging(
    *,
    level: int = DEFAULT_LOG_LEVEL,
    wrapper_class: type[structlog.BoundLoggerBase] | None = None,
    cache_logger_on_first_use: bool = True,
    processors: Optional[Iterable[structlog.typing.Processor]] = None,
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

    if structlog is None:
        global _FALLBACK_CONFIGURED, _FALLBACK_LEVEL
        _FALLBACK_LEVEL = level
        _ensure_stdlib_bridge(level)
        _FALLBACK_CONFIGURED = True
        return

    chosen_wrapper = wrapper_class or structlog.stdlib.BoundLogger
    configured_processors = list(_shared_processors())
    if processors is not None:
        configured_processors.extend(processors)
    else:
        configured_processors.append(structlog.processors.JSONRenderer())

    structlog.configure(
        processors=configured_processors,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=chosen_wrapper,
        cache_logger_on_first_use=cache_logger_on_first_use,
    )

    _ensure_stdlib_bridge(level)


@dataclass(slots=True)
class LoggerConfig:
    """Declarative description of a structlog logger."""

    name: str
    level: int = DEFAULT_LOG_LEVEL
    context: tuple[tuple[str, object], ...] = ()

    def build(self) -> Any:
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


def get_logger(name: str) -> Any:
    """Return a structlog bound logger, configuring defaults if needed."""

    if structlog is None:
        global _FALLBACK_CONFIGURED
        if not _FALLBACK_CONFIGURED:
            configure_logging(level=_FALLBACK_LEVEL)
        return _FallbackBoundLogger(name)

    if not structlog.is_configured():  # pragma: no cover - defensive path
        configure_logging()
    return structlog.get_logger(name)  # type: ignore[return-value]


__all__ = [
    "DEFAULT_LOG_LEVEL",
    "LoggerConfig",
    "configure_logging",
    "get_logger",
]
