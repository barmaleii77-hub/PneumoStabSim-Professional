from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from PySide6.QtCore import QEventLoop, QTimer


class SignalListener:
    """Lightweight replacement for :class:`PySide6.QtTest.QSignalSpy`.

    The helper stores every emission payload and exposes a small subset of the
    ``QSignalSpy`` interface used throughout the test-suite: ``count()``,
    ``__len__``, ``__getitem__`` and ``at()``.  Signals can emit zero or more
    arguments; they are captured as tuples to provide index-based access that
    mirrors the behaviour of ``QSignalSpy``.
    """

    # Qt 6.7+ stores signal connections as weak references; exposing a weakref
    # slot ensures ``SignalListener`` instances can be used directly without
    # PySide raising ``TypeError: cannot create weak reference``.
    __slots__ = ("_signal", "_records", "__weakref__")

    def __init__(self, signal: Any) -> None:
        self._signal = signal
        self._records: list[tuple[Any, ...]] = []
        signal.connect(self._capture)  # type: ignore[attr-defined]

    def _capture(self, *args: Any) -> None:
        self._records.append(tuple(args))

    def count(self) -> int:
        """Return the number of captured emissions."""

        return len(self._records)

    def __len__(self) -> int:  # pragma: no cover - trivial wrapper
        return len(self._records)

    def __getitem__(self, index: int) -> tuple[Any, ...]:
        return self._records[index]

    def at(self, index: int) -> tuple[Any, ...]:
        return self._records[index]

    def arguments(self) -> Sequence[tuple[Any, ...]]:
        """Expose captured payloads for advanced assertions."""

        return tuple(self._records)

    def clear(self) -> None:
        """Reset the captured history while keeping the connection active."""

        self._records.clear()

    def wait(self, timeout_ms: int = 500) -> bool:
        """Block until the next emission or until ``timeout_ms`` expires."""

        initial_count = len(self._records)
        loop = QEventLoop()
        timer = QTimer()
        timer.setSingleShot(True)
        timer.timeout.connect(loop.quit)

        def _quit_on_emit(*_: Any) -> None:
            loop.quit()

        self._signal.connect(_quit_on_emit)
        try:
            timer.start(int(timeout_ms))
            loop.exec()
        finally:
            try:
                self._signal.disconnect(_quit_on_emit)
            except Exception:
                pass
        return len(self._records) > initial_count


__all__ = ["SignalListener"]
