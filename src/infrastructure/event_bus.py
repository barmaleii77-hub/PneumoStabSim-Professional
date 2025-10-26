"""In-process publish/subscribe helper used across the application."""

from __future__ import annotations

from threading import RLock
from typing import Any, Callable

from .container import (
    ServiceContainer,
    ServiceToken,
    get_default_container,
)

__all__ = [
    "EventBus",
    "EVENT_BUS_TOKEN",
    "get_event_bus",
    "subscribe",
]


Listener = Callable[[Any], None]


class EventBus:
    """Thread-safe in-process publish/subscribe helper."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Listener]] = {}
        self._lock = RLock()

    def subscribe(self, topic: str, callback: Listener) -> Callable[[], None]:
        """Subscribe ``callback`` to ``topic`` and return an unsubscribe handle."""

        with self._lock:
            callbacks = self._subscribers.setdefault(topic, [])
            callbacks.append(callback)

        def _unsubscribe() -> None:
            self.unsubscribe(topic, callback)

        return _unsubscribe

    def unsubscribe(self, topic: str, callback: Listener) -> None:
        """Remove ``callback`` from ``topic`` subscriptions."""

        with self._lock:
            callbacks = self._subscribers.get(topic)
            if not callbacks:
                return
            try:
                callbacks.remove(callback)
            except ValueError:
                return
            if not callbacks:
                self._subscribers.pop(topic, None)

    def publish(self, topic: str, payload: Any | None = None) -> None:
        """Broadcast ``payload`` to all subscribers of ``topic``."""

        with self._lock:
            callbacks = list(self._subscribers.get(topic, ()))

        for callback in callbacks:
            callback(payload)

    def clear(self) -> None:
        """Remove all subscriptions (useful for tests)."""

        with self._lock:
            self._subscribers.clear()


EVENT_BUS_TOKEN = ServiceToken[EventBus](
    "infrastructure.event_bus",
    "In-process publish/subscribe helper for diagnostics and settings",
)


def _ensure_default_registration() -> None:
    container = get_default_container()
    if not container.is_registered(EVENT_BUS_TOKEN):
        container.register_factory(EVENT_BUS_TOKEN, lambda _: EventBus())


_ensure_default_registration()


def get_event_bus(container: ServiceContainer | None = None) -> EventBus:
    """Resolve the shared :class:`EventBus` instance from the container."""

    target = container or get_default_container()
    return target.resolve(EVENT_BUS_TOKEN)


def subscribe(topic: str, callback: Listener) -> Callable[[], None]:
    """Convenience wrapper subscribing to ``topic`` on the default event bus."""

    bus = get_event_bus()
    return bus.subscribe(topic, callback)
