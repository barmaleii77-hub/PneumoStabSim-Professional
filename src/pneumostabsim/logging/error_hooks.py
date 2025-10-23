"""Global error handling hooks for PneumoStabSim (minimal implementation)."""
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
 """Простой менеджер хуков ошибок (заглушка для интеграции)."""

 logger: logging.Logger
 json_path: Path

 def install(self, *, loop: Optional[asyncio.AbstractEventLoop] = None, qt_install_message_handler: Optional[QtInstaller] = None) -> "ErrorHookManager": qt_install_message_handler(self._qt_message_handler) if qt_install_message_handler is not None else None; return self

 def restore(self) -> None: return None

 def _qt_message_handler(self, mode: Any, context: Any, message: str) -> None: self.logger.debug(f"Qt[{getattr(mode, 'name', str(mode))}]: {message}")


def install_error_hooks(logger: logging.Logger, json_log_path: Path | str, *, loop: Optional[asyncio.AbstractEventLoop] = None, qt_install_message_handler: Optional[QtInstaller] = None) -> ErrorHookManager:
 manager = ErrorHookManager(logger=logger, json_path=Path(json_log_path))
 return manager.install(loop=loop, qt_install_message_handler=qt_install_message_handler)
