"""Simple dependency injection container for application services."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass
from threading import RLock
from typing import Any, Generic, TypeVar


__all__ = [
    "ServiceContainer",
    "ServiceRegistrationError",
    "ServiceResolutionError",
    "ServiceToken",
    "get_default_container",
    "set_default_container",
]


T_co = TypeVar("T_co", covariant=True)
T = TypeVar("T")
Factory = Callable[["ServiceContainer"], T]


class ServiceRegistrationError(RuntimeError):
    """Raised when attempting to register a conflicting service."""


class ServiceResolutionError(LookupError):
    """Raised when the requested service cannot be resolved."""


@dataclass(frozen=True)
class ServiceToken(Generic[T_co]):
    """Identifier for a service inside :class:`ServiceContainer`."""

    name: str
    description: str | None = None


class ServiceContainer:
    """Thread-safe container that manages shared application services."""

    def __init__(self) -> None:
        self._factories: dict[str, Factory[Any]] = {}
        self._instances: dict[str, Any] = {}
        self._override_stack: dict[str, list[Any]] = {}
        self._lock = RLock()

    # ------------------------------------------------------------------
    # Registration helpers
    # ------------------------------------------------------------------
    def register_factory(
        self,
        token: ServiceToken[T],
        factory: Factory[T],
        *,
        replace: bool = False,
    ) -> None:
        """Register a lazy factory for the given service token."""

        with self._lock:
            if not replace and (
                token.name in self._factories or token.name in self._instances
            ):
                raise ServiceRegistrationError(
                    f"Service '{token.name}' is already registered",
                )
            self._factories[token.name] = factory
            # Purge cached instance so the new factory is honoured.
            self._instances.pop(token.name, None)

    def register_instance(
        self,
        token: ServiceToken[T],
        instance: T,
        *,
        replace: bool = False,
    ) -> None:
        """Register an already constructed instance for the token."""

        with self._lock:
            if not replace and (
                token.name in self._instances or token.name in self._factories
            ):
                raise ServiceRegistrationError(
                    f"Service '{token.name}' is already registered",
                )
            self._factories.pop(token.name, None)
            self._instances[token.name] = instance

    def is_registered(self, token: ServiceToken[Any]) -> bool:
        """Return ``True`` if the container knows how to resolve ``token``."""

        with self._lock:
            return token.name in self._factories or token.name in self._instances

    # ------------------------------------------------------------------
    # Resolution helpers
    # ------------------------------------------------------------------
    def resolve(self, token: ServiceToken[T]) -> T:
        """Resolve the service identified by ``token``."""

        override = self._peek_override(token)
        if override is not None:
            return override

        with self._lock:
            if token.name in self._instances:
                return self._instances[token.name]
            factory = self._factories.get(token.name)

        if factory is None:
            raise ServiceResolutionError(
                f"Service '{token.name}' is not registered",
            )

        instance = factory(self)
        with self._lock:
            self._instances[token.name] = instance
        return instance

    # ------------------------------------------------------------------
    # Overrides & lifecycle management
    # ------------------------------------------------------------------
    @contextmanager
    def override(self, token: ServiceToken[T], instance: T) -> Iterator[T]:
        """Temporarily override a service instance for the active context."""

        with self._lock:
            stack = self._override_stack.setdefault(token.name, [])
            stack.append(instance)
        try:
            yield instance
        finally:
            with self._lock:
                stack = self._override_stack.get(token.name)
                if stack:
                    stack.pop()
                    if not stack:
                        self._override_stack.pop(token.name, None)

    def reset(self, token: ServiceToken[Any] | None = None) -> None:
        """Clear cached instances for ``token`` or for the entire container."""

        with self._lock:
            if token is None:
                self._instances.clear()
                self._override_stack.clear()
            else:
                self._instances.pop(token.name, None)
                self._override_stack.pop(token.name, None)

    def _peek_override(self, token: ServiceToken[T]) -> T | None:
        with self._lock:
            stack = self._override_stack.get(token.name)
            if not stack:
                return None
            return stack[-1]


_default_container = ServiceContainer()


def get_default_container() -> ServiceContainer:
    """Return the process-wide service container."""

    return _default_container


def set_default_container(container: ServiceContainer) -> None:
    """Replace the process-wide service container (useful for tests)."""

    global _default_container
    _default_container = container
