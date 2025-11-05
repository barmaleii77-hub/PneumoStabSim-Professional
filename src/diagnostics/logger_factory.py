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

import logging
from dataclasses import dataclass
from typing import Iterable, Optional

import structlog


DEFAULT_LOG_LEVEL = logging.INFO


def _shared_processors() -> list[structlog.typing.Processor]:
    """Return the processors shared by stdlib + structlog pipelines."""

    return [
        structlog.contextvars.merge_contextvars,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]


def _ensure_stdlib_bridge(level: int) -> None:
    """Configure the standard logging module to forward records to structlog."""

    formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=_shared_processors(),
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers[:] = [handler]
    root_logger.setLevel(level)


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

    def build(self) -> structlog.stdlib.BoundLogger:
        logger = get_logger(self.name)
        if self.context:
            logger = logger.bind(**dict(self.context))
        if hasattr(logger, "setLevel"):
            # ``structlog`` bound loggers expose ``setLevel`` when using the
            # stdlib wrapper.
            logger.setLevel(self.level)  # type: ignore[attr-defined]
        return logger


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Return a structlog bound logger, configuring defaults if needed."""

    if not structlog.is_configured():  # pragma: no cover - defensive path
        configure_logging()
    return structlog.get_logger(name)  # type: ignore[return-value]


__all__ = [
    "DEFAULT_LOG_LEVEL",
    "LoggerConfig",
    "configure_logging",
    "get_logger",
]
