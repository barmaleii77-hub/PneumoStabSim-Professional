"""Qt error hook integration utilities wired into the infrastructure layer."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Optional

QtMessageHandler = Callable[[Any, Any, str], None]
QtInstaller = Callable[[QtMessageHandler], Optional[QtMessageHandler]]


@dataclass
class ErrorHookManager:
    """Lightweight manager that proxies Qt log messages to Python logging."""

    logger: logging.Logger
    json_path: Path

    def install(
        self,
        *,
        loop: asyncio.AbstractEventLoop | None = None,
        qt_install_message_handler: QtInstaller | None = None,
    ) -> ErrorHookManager:
        if loop is not None:  # pragma: no cover - maintained for compatibility
            _ = loop
        if qt_install_message_handler is not None:
            qt_install_message_handler(self._qt_message_handler)
        return self

    def restore(self) -> None:
        return None

    def _qt_message_handler(self, mode: Any, context: Any, message: str) -> None:
        self.logger.debug("Qt[%s]: %s", getattr(mode, "name", str(mode)), message)


def install_error_hooks(
    logger: logging.Logger,
    json_log_path: Path | str,
    *,
    loop: asyncio.AbstractEventLoop | None = None,
    qt_install_message_handler: QtInstaller | None = None,
) -> ErrorHookManager:
    manager = ErrorHookManager(logger=logger, json_path=Path(json_log_path))
    return manager.install(
        loop=loop, qt_install_message_handler=qt_install_message_handler
    )


__all__ = ["ErrorHookManager", "install_error_hooks"]
