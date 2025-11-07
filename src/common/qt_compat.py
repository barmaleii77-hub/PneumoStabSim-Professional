"""Qt compatibility helpers.

This module provides minimal fallbacks for Qt classes that are used in
headless or test environments where :mod:`PySide6` might not be available.

The real application always runs with PySide6 installed, but a lightweight
fallback keeps unit tests functional when Qt is missing (for example in CI
containers).  The fallback implements just enough behaviour for signal
dispatching used by the settings event bus and the signal trace service.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Callable, Optional, Protocol, TypeVar

if TYPE_CHECKING:  # pragma: no cover - typing support only
    from PySide6.QtCore import Property, QObject, Signal, Slot
else:
    try:  # pragma: no cover - exercised in runtime, skipped in headless tests
        from PySide6.QtCore import Property, QObject, Signal, Slot
    except ImportError:  # pragma: no cover - fallback when PySide6 is not present

        class _SupportsConnect(Protocol):
            def connect(self, callback: Callable[..., Any]) -> None: ...

        class _SupportsEmit(Protocol):
            def emit(self, *args: Any, **kwargs: Any) -> None: ...

        class QObject:
            """Lightweight stand-in for :class:`PySide6.QtCore.QObject`."""

            def __init__(self, *_args: Any, **_kwargs: Any) -> None:
                super().__init__()

        _CallbackT = TypeVar("_CallbackT", bound=Callable[..., Any])

        class _FallbackSignal(_SupportsConnect, _SupportsEmit):
            """Very small signal implementation for non-Qt environments."""

            def __init__(self) -> None:
                self._subscribers: list[Callable[..., Any]] = []

            def connect(self, callback: Callable[..., Any]) -> None:
                self._subscribers.append(callback)

            def emit(self, *args: Any, **kwargs: Any) -> None:
                for subscriber in list(self._subscribers):
                    subscriber(*args, **kwargs)

        def Signal(*_signature: Any, **_kwargs: Any) -> _FallbackSignal:
            return _FallbackSignal()

        def Slot(
            *_types: Any, **_kwargs: Any
        ) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
            def decorator(func: _CallbackT) -> _CallbackT:
                return func

            return decorator

        class _FallbackProperty:
            def __init__(
                self,
                fget: Callable[[Any], Any],
                fset: Callable[[Any, Any], None] | None = None,
                freset: Callable[[Any], None] | None = None,
                notify: Any | None = None,
                **extra: Any,
            ) -> None:
                self.fget = fget
                self.fset = fset
                self.freset = freset
                self.notify = notify
                self.extra = extra

            def __get__(self, instance: Any, owner: type[Any] | None) -> Any:
                if instance is None:
                    return self
                return self.fget(instance)

            def __set__(self, instance: Any, value: Any) -> None:
                if self.fset is None:
                    raise AttributeError("can't set attribute")
                self.fset(instance, value)

            def setter(self, func: Callable[[Any, Any], None]) -> _FallbackProperty:
                self.fset = func
                return self

            def reset(self, func: Callable[[Any], None]) -> _FallbackProperty:
                self.freset = func
                return self

        def Property(
            _type: Any,
            fget: Callable[[Any], Any] | None = None,
            fset: Callable[[Any, Any], None] | None = None,
            freset: Callable[[Any], None] | None = None,
            notify: Any | None = None,
            **extra: Any,
        ) -> Any:
            def _wrap(getter: Callable[[Any], Any]) -> _FallbackProperty:
                return _FallbackProperty(
                    getter,
                    fset=fset,
                    freset=freset,
                    notify=notify,
                    **extra,
                )

            if fget is None:
                return _wrap
            return _wrap(fget)


__all__ = ["Property", "QObject", "Signal", "Slot"]
