"""Инструменты трассировки Qt-сигналов."""

from __future__ import annotations

import logging
from collections import deque
from dataclasses import dataclass
from datetime import UTC, datetime
from threading import RLock
from typing import Any
from collections.abc import Callable
from collections.abc import Iterable, Iterator

from .logger_factory import LoggerProtocol, get_logger

logger: LoggerProtocol = get_logger("diagnostics.signals")


class SignalTracingError(RuntimeError):
    """Базовое исключение для ошибок трассировки сигналов."""


class MissingSignalError(SignalTracingError):
    """Сигнал не был зафиксирован за отведённое время/число событий."""


@dataclass(slots=True)
class SignalTraceRecord:
    """Представление зафиксированного Qt-сигнала."""

    timestamp: datetime
    sender: str
    signal: str
    args: tuple[Any, ...]

    def as_payload(self) -> dict[str, Any]:
        """Возвращает словарь, подходящий для передачи в QML/GUI."""

        return {
            "timestamp": self.timestamp.isoformat(timespec="milliseconds"),
            "sender": self.sender,
            "signal": self.signal,
            "args": list(self.args),
        }


def _resolve_object_name(obj: Any) -> str:
    name = getattr(obj, "objectName", None)
    if callable(name):
        try:
            name = name()
        except Exception:  # pragma: no cover - крайне редкие ошибки Qt
            name = None
    if isinstance(name, str) and name.strip():
        return name
    return getattr(obj, "__class__", type(obj)).__name__


class SignalTracer:
    """Централизованный менеджер подписки на Qt-сигналы."""

    def __init__(
        self,
        *,
        max_records: int = 500,
        log: LoggerProtocol | None = None,
    ) -> None:
        self._records: deque[SignalTraceRecord] = deque(maxlen=max_records)
        self._log = log or logger
        self._lock = RLock()
        self._sinks: list[Callable[[SignalTraceRecord], None]] = []
        self._reset_hooks: list[Callable[[], None]] = []
        self._connections: list[tuple[Any, Callable[..., None]]] = []

    @property
    def records(self) -> tuple[SignalTraceRecord, ...]:
        with self._lock:
            return tuple(self._records)

    def register_sink(
        self, sink: Callable[[SignalTraceRecord], None]
    ) -> Callable[[], None]:
        """Добавляет sink, возвращает функцию для его удаления."""

        with self._lock:
            self._sinks.append(sink)

        def _remove() -> None:
            with self._lock:
                try:
                    self._sinks.remove(sink)
                except ValueError:
                    pass

        return _remove

    def register_reset_hook(self, hook: Callable[[], None]) -> Callable[[], None]:
        """Регистрирует обработчик сброса буфера."""

        with self._lock:
            self._reset_hooks.append(hook)

        def _remove() -> None:
            with self._lock:
                try:
                    self._reset_hooks.remove(hook)
                except ValueError:
                    pass

        return _remove

    def attach(
        self,
        obj: Any,
        signal_name: str,
        *,
        alias: str | None = None,
        formatter: Callable[[tuple[Any, ...]], tuple[Any, ...]] | None = None,
    ) -> Callable[[], None]:
        """Подписывается на сигнал Qt и возвращает функцию для отписки."""

        signal = getattr(obj, signal_name, None)
        if signal is None:
            raise SignalTracingError(
                f"Object {obj!r} does not expose signal '{signal_name}'"
            )
        connect = getattr(signal, "connect", None)
        if connect is None or not callable(connect):
            raise SignalTracingError(
                f"Attribute '{signal_name}' of {obj!r} is not a Qt signal"
            )

        sender_name = _resolve_object_name(obj)
        alias_name = alias or signal_name

        def _handler(*args: Any) -> None:
            processed_args: tuple[Any, ...]
            if formatter is not None:
                processed_args = tuple(formatter(tuple(args)))
            else:
                processed_args = tuple(args)

            record = SignalTraceRecord(
                timestamp=datetime.now(UTC),
                sender=sender_name,
                signal=alias_name,
                args=processed_args,
            )

            with self._lock:
                self._records.append(record)
                sinks_snapshot = tuple(self._sinks)

            self._log.info(
                "signal_trace_event",
                timestamp=record.timestamp.isoformat(timespec="milliseconds"),
                sender=record.sender,
                signal=record.signal,
                args=list(record.args),
            )
            logging.getLogger("diagnostics.signals").info("signal_trace_event")

            for sink in sinks_snapshot:
                try:
                    sink(record)
                except Exception:  # pragma: no cover - не ломаем трассировку
                    self._log.exception("Signal sink failed")

        try:
            connect(_handler)
        except Exception as exc:  # pragma: no cover - Qt ошибки
            raise SignalTracingError(
                f"Failed to connect to signal '{signal_name}'"
            ) from exc

        with self._lock:
            self._connections.append((signal, _handler))

        def _detach() -> None:
            disconnect = getattr(signal, "disconnect", None)
            if disconnect is None:
                return
            try:
                disconnect(_handler)
            except Exception:
                self._log.debug("signal_trace_disconnect_failed", signal=alias_name)
            with self._lock:
                try:
                    self._connections.remove((signal, _handler))
                except ValueError:
                    pass

        return _detach

    def attach_many(
        self,
        obj: Any,
        signals: Iterable[str],
        *,
        alias_prefix: str | None = None,
    ) -> list[Callable[[], None]]:
        """Подписывается на несколько сигналов объекта."""

        disposers: list[Callable[[], None]] = []
        for name in signals:
            alias = f"{alias_prefix}{name}" if alias_prefix else None
            disposers.append(self.attach(obj, name, alias=alias))
        return disposers

    def assert_emitted(
        self,
        signal_name: str,
        *,
        min_count: int = 1,
    ) -> None:
        """Проверяет, что сигнал был зафиксирован минимум указанное количество раз."""

        if min_count < 0:
            raise ValueError("min_count must be non-negative")

        with self._lock:
            count = sum(1 for record in self._records if record.signal == signal_name)

        if count < min_count:
            raise MissingSignalError(
                f"Signal '{signal_name}' emitted {count} time(s), expected at least {min_count}"
            )

    def clear(self) -> None:
        """Очищает историю сигналов и уведомляет подписчиков."""

        with self._lock:
            self._records.clear()
            hooks_snapshot = tuple(self._reset_hooks)

        for hook in hooks_snapshot:
            try:
                hook()
            except Exception:  # pragma: no cover - диагностика не должна падать
                self._log.exception("Signal tracer reset hook failed")

    def iter_records(self) -> Iterator[SignalTraceRecord]:
        with self._lock:
            return iter(tuple(self._records))

    def dispose(self) -> None:
        """Отписывается от всех сигналов и очищает буфер."""

        with self._lock:
            connections = tuple(self._connections)
            self._connections.clear()

        for signal, handler in connections:
            disconnect = getattr(signal, "disconnect", None)
            if disconnect is None:
                continue
            try:
                disconnect(handler)
            except Exception:
                self._log.debug("Failed to disconnect handler %s", handler)

        self.clear()


try:  # pragma: no cover - PySide может отсутствовать в среде тестов
    from PySide6.QtCore import QObject, Signal
except Exception:  # pragma: no cover - мы не хотим падать от ImportError
    QObject = None  # type: ignore[assignment]
    Signal = None  # type: ignore[assignment]


HAS_QT = QObject is not None and Signal is not None


if HAS_QT:  # pragma: no cover - зависит от наличия PySide6

    class SignalTracerBridge(QObject):
        """Qt-обёртка, транслирующая события трассировки в QML."""

        traceAdded = Signal(dict)
        traceReset = Signal()

        def __init__(self, tracer: SignalTracer, parent: QObject | None = None):
            super().__init__(parent)
            self._tracer = tracer
            self._remove_sink = tracer.register_sink(self._emit_trace)
            self._remove_reset = tracer.register_reset_hook(self.traceReset.emit)

        def _emit_trace(self, record: SignalTraceRecord) -> None:
            self.traceAdded.emit(record.as_payload())

        def dispose(self) -> None:
            if self._remove_sink:
                self._remove_sink()
                self._remove_sink = None  # type: ignore[assignment]
            if self._remove_reset:
                self._remove_reset()
                self._remove_reset = None  # type: ignore[assignment]

        def __del__(self) -> None:
            try:
                self.dispose()
            except Exception:
                logger.debug("Failed to dispose SignalTracerBridge", exc_info=True)

else:

    class SignalTracerBridge:  # pragma: no cover - простой заглушечный класс
        """Заглушка, выбрасывающая исключение при попытке использовать мост без Qt."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:  # noqa: D401 - коротко
            raise SignalTracingError(
                "PySide6 is required to use SignalTracerBridge (Qt bridge)"
            )

        def dispose(self) -> None:
            """Совместимость с интерфейсом Qt-версии."""


__all__ = [
    "SignalTraceRecord",
    "SignalTracer",
    "SignalTracerBridge",
    "SignalTracingError",
    "MissingSignalError",
    "HAS_QT",
]
