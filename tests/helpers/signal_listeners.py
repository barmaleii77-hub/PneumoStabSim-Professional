from __future__ import annotations

from collections.abc import Sequence
from importlib import import_module, util
from typing import Any

from PySide6.QtCore import QEventLoop, QTimer


def _load_qsignalspy() -> type | None:
    spec = util.find_spec("PySide6.QtTest")
    if spec is None:
        return None

    module = import_module("PySide6.QtTest")
    return getattr(module, "QSignalSpy", None)


_QT_SIGNAL_SPY: type | None = _load_qsignalspy()


class SignalListener:
    """Lightweight replacement for :class:`PySide6.QtTest.QSignalSpy`."""

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


class SignalSpy:
    """Minimal drop-in alternative to :class:`QSignalSpy`."""

    __slots__ = ("_delegate", "_listener", "__weakref__")

    def __init__(self, signal: Any) -> None:
        delegate = _QT_SIGNAL_SPY
        self._delegate = delegate(signal) if delegate is not None else None
        self._listener = None if self._delegate is not None else SignalListener(signal)

    def count(self) -> int:
        if self._delegate is not None:
            return int(self._delegate.count())
        assert self._listener is not None
        return self._listener.count()

    def __len__(self) -> int:
        return self.count()

    def _normalize(
        self, payload: Any
    ) -> tuple[Any, ...]:  # pragma: no cover - tiny helper
        if isinstance(payload, (list, tuple)):
            return tuple(payload)
        return (payload,)

    def __getitem__(self, index: int) -> tuple[Any, ...]:
        if self._delegate is not None:
            return self._normalize(self._delegate[index])
        assert self._listener is not None
        return self._listener[index]

    def at(self, index: int) -> tuple[Any, ...]:
        if self._delegate is not None:
            return self._normalize(self._delegate.at(index))
        assert self._listener is not None
        return self._listener.at(index)

    def arguments(self) -> Sequence[tuple[Any, ...]]:
        if self._delegate is not None:
            return tuple(self._normalize(entry) for entry in self._delegate)
        assert self._listener is not None
        return self._listener.arguments()

    def clear(self) -> None:
        if self._delegate is not None:
            self._delegate.clear()
        else:
            assert self._listener is not None
            self._listener.clear()

    def wait(self, timeout_ms: int = 500) -> bool:
        if self._delegate is not None:
            return bool(self._delegate.wait(timeout_ms))
        assert self._listener is not None
        return self._listener.wait(timeout_ms)


QSignalSpy = SignalSpy


__all__ = ["QSignalSpy", "SignalListener", "SignalSpy"]
