"""Qt compatibility helpers.

This module provides minimal fallbacks for Qt classes that are used in
headless or test environments where :mod:`PySide6` might not be available.

The real application always runs with PySide6 installed, but a lightweight
fallback keeps unit tests functional when Qt is missing (for example in CI
containers).  The fallback implements just enough behaviour for signal
dispatching used by the settings event bus and the signal trace service.
"""

from __future__ import annotations

from typing import Any, Callable, Optional

try:  # pragma: no cover - exercised in runtime, skipped in headless tests
    from PySide6.QtCore import Property, QObject, Signal, Slot
except Exception:  # pragma: no cover - fallback when PySide6 is not present

    class QObject:  # type: ignore[override]
        """Lightweight stand-in for :class:`PySide6.QtCore.QObject`."""

        def __init__(self, *_args: Any, **_kwargs: Any) -> None:
            pass

    class _FallbackSignal:
        """Very small signal implementation for non-Qt environments."""

        def __init__(self) -> None:
            self._subscribers: list[Callable[..., Any]] = []

        def connect(self, callback: Callable[..., Any]) -> None:
            self._subscribers.append(callback)

        def emit(self, *args: Any, **kwargs: Any) -> None:
            for subscriber in list(self._subscribers):
                subscriber(*args, **kwargs)

    def Signal(*_signature: Any, **_kwargs: Any) -> _FallbackSignal:  # type: ignore[misc]
        return _FallbackSignal()

    def Slot(*_types: Any, **_kwargs: Any) -> Callable[[Callable[..., Any]], Callable[..., Any]]:  # type: ignore[misc]
        def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
            return func

        return decorator

    class _FallbackProperty:
        def __init__(self, fget: Callable[[Any], Any]) -> None:
            self.fget = fget

        def __get__(self, instance: Any, owner: Optional[type[Any]]) -> Any:
            if instance is None:
                return self
            return self.fget(instance)

    def Property(  # type: ignore[misc,override]
        _type: Any,
        fget: Optional[Callable[[Any], Any]] = None,
        fset: Optional[Callable[[Any, Any], None]] = None,
        freset: Optional[Callable[[Any], None]] = None,
        notify: Optional[Any] = None,
    ) -> Any:
        if fget is None:
            raise TypeError("Fallback Property requires a getter")
        return _FallbackProperty(fget)


__all__ = ["Property", "QObject", "Signal", "Slot"]
