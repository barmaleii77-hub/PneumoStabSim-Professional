from __future__ import annotations

from collections.abc import Sequence
from typing import Any


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


__all__ = ["SignalListener"]
