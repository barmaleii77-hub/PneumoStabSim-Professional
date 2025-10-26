"""Headless Qt compatibility layer.

This module provides extremely small stand-ins for the Qt classes used by the
application runner.  They are intentionally lightweight so the simulator can be
started in environments where PySide6 cannot be imported (for example, CI
containers without an OpenGL runtime).  The goal is not to emulate Qt but to
allow the bootstrap sequence and diagnostics to execute without crashing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


class _TimerSignal:
    """Minimal signal object exposing :meth:`connect` and :meth:`emit`."""

    def __init__(self) -> None:
        self._subscribers: list[Callable[..., Any]] = []

    def connect(self, callback: Callable[..., Any]) -> None:
        self._subscribers.append(callback)

    def emit(self) -> None:
        for subscriber in list(self._subscribers):
            subscriber()


class HeadlessTimer:
    """Replacement for :class:`PySide6.QtCore.QTimer`."""

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        self.timeout = _TimerSignal()

    def setSingleShot(self, _single_shot: bool) -> None:  # pragma: no cover - no-op
        """No-op placeholder matching the Qt API."""

    def start(self, _msec: int) -> None:
        """Immediately emit the timeout signal."""

        self.timeout.emit()


def headless_install_message_handler(handler: Callable[..., Any]) -> Callable[..., Any]:
    """Return the handler unchanged to mirror :func:`qInstallMessageHandler`."""

    return handler


@dataclass(slots=True)
class HeadlessQtNamespace:
    """Namespace object exposing Qt attributes used by :class:`ApplicationRunner`."""

    headless_reason: str | None = None
    is_headless: bool = True

    class HighDpiScaleFactorRoundingPolicy:  # pragma: no cover - attribute container
        PassThrough = 0


class HeadlessApplication:
    """Stand-in for :class:`PySide6.QtWidgets.QApplication`."""

    is_headless: bool = True
    headless_reason: str | None = None

    def __init__(self, *_args: Any, **_kwargs: Any) -> None:
        self._name: str | None = None
        self._version: str | None = None
        self._org: str | None = None

    # ----------------------------------------------------------------- setters
    def setApplicationName(self, name: str) -> None:  # pragma: no cover - simple setter
        self._name = name

    def setApplicationVersion(self, version: str) -> None:  # pragma: no cover - setter
        self._version = version

    def setOrganizationName(self, organization: str) -> None:  # pragma: no cover
        self._org = organization

    # ---------------------------------------------------------------- lifecycle
    def exec(self) -> int:
        """Pretend to run the Qt event loop."""

        print("⚠️ Qt GUI is unavailable; running in headless diagnostics mode.")
        return 0

    def quit(self) -> None:  # pragma: no cover - compatibility method
        """Compatibility placeholder for the real Qt API."""


__all__ = [
    "HeadlessApplication",
    "HeadlessQtNamespace",
    "HeadlessTimer",
    "headless_install_message_handler",
]
