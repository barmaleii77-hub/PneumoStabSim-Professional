"""Logging helpers and container integration."""

from __future__ import annotations

import logging
from logging import Logger

from ..container import ServiceContainer, ServiceToken, get_default_container
from .error_hooks import ErrorHookManager, install_error_hooks

__all__ = [
    "LOGGER_TOKEN",
    "configure_logging",
    "get_logger",
    "ErrorHookManager",
    "install_error_hooks",
]


LOGGER_TOKEN = ServiceToken[Logger](
    "logging.logger",
    "Application-wide structured logger",
)


def configure_logging(*, level: int = logging.INFO) -> Logger:
    """Configure and return the root application logger.

    The helper ensures that handlers are attached only once, preventing duplicate
    log lines when tests import modules repeatedly.
    """

    logger = logging.getLogger("pneumostabsim")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s %(levelname)s [%(name)s] %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
        logger.addHandler(handler)
    logger.setLevel(level)
    return logger


def get_logger(
    name: str | None = None,
    *,
    container: ServiceContainer | None = None,
) -> Logger:
    """Return the shared application logger or one of its children."""

    target = container or get_default_container()
    base = target.resolve(LOGGER_TOKEN)
    if name:
        return base.getChild(name)
    return base
