"""Dependency injection primitives for core services.

Alignment with the renovation plans:

* Master plan: `docs/RENOVATION_MASTER_PLAN.md`, Section 5 "Application
  Architecture Refinement", action item 2 "Service Composition" describing the
  typed service container with canonical registrations.
* Phase 2: `docs/RENOVATION_PHASE_2_ARCHITECTURE_AND_SETTINGS_PLAN.md`, work
  breakdown item "Dependency Injection & Services" and log entry
  "Service container foundation" (2025-07-02) that tracks the bootstrap
  lifecycle and override strategy.

The container implemented here is intentionally minimal yet opinionated:

* Services are addressed by their Python type which enables static type checkers
  and IDEs to infer the returned instance types.
* Providers are registered lazily.  A service is instantiated the first time it
  is requested which keeps test environments fast while still allowing
  dependencies between services.
* Circular dependencies are detected eagerly to aid debugging.
* The canonical :class:`~src.infrastructure.event_bus.EventBus` wiring is
  handled alongside other services so diagnostics can subscribe to lifecycle
  notifications.

In addition to the container itself, :func:`build_default_container` exposes the
canonical wiring for settings management, logging, event logging, and the
settings profile subsystem.  The helper keeps configuration centralised and
ensures that modules use consistent instances during tests and production runs.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any, TypeVar

from src.common.event_logger import EventLogger
from src.common.settings_manager import ProfileSettingsManager, SettingsManager
from src.diagnostics.logger_factory import (
    BoundLogger,
    configure_logging,
    get_logger,
)
from src.infrastructure.event_bus import EventBus
from src.telemetry import TelemetryTracker
from .settings_service import SettingsService

__all__ = [
    "EventBus",
    "ServiceContainer",
    "ServiceRegistrationError",
    "ServiceResolutionError",
    "build_default_container",
]


ServiceType = TypeVar("ServiceType")
FactoryType = Callable[["ServiceContainer"], ServiceType]


class ServiceRegistrationError(RuntimeError):
    """Raised when attempting to register a duplicate service."""


class ServiceResolutionError(RuntimeError):
    """Raised when resolving a service fails (missing or circular dependency)."""


class ServiceContainer:
    """Minimalistic dependency injection container keyed by service type."""

    def __init__(self) -> None:
        self._factories: dict[type[Any], FactoryType[Any]] = {}
        self._instances: dict[type[Any], Any] = {}
        self._resolution_stack: list[type[Any]] = []

    # ------------------------------------------------------------------ register
    def register_instance(self, key: type[ServiceType], instance: ServiceType) -> None:
        """Register a pre-built singleton instance for ``key``."""

        if key in self._instances or key in self._factories:
            raise ServiceRegistrationError(
                f"Service '{key.__qualname__}' already registered"
            )
        self._instances[key] = instance

    def register_factory(
        self,
        key: type[ServiceType],
        factory: FactoryType[ServiceType],
        *,
        eager: bool = False,
    ) -> None:
        """Register ``factory`` used to lazily construct ``key`` instances."""

        if key in self._instances or key in self._factories:
            raise ServiceRegistrationError(
                f"Service '{key.__qualname__}' already registered"
            )
        self._factories[key] = factory
        if eager:
            self._instances[key] = factory(self)

    # ------------------------------------------------------------------- resolve
    def resolve(self, key: type[ServiceType]) -> ServiceType:
        """Resolve ``key`` and return the singleton instance."""

        if key in self._instances:
            return self._instances[key]

        factory = self._factories.get(key)
        if factory is None:
            raise ServiceResolutionError(
                f"Service '{key.__qualname__}' is not registered"
            )

        if key in self._resolution_stack:
            cycle = " → ".join(
                cls.__qualname__ for cls in self._resolution_stack + [key]
            )
            raise ServiceResolutionError(f"Circular dependency detected: {cycle}")

        self._resolution_stack.append(key)
        try:
            instance = factory(self)
        except ServiceResolutionError:
            raise
        except Exception as exc:  # pragma: no cover - surface contextual error
            raise ServiceResolutionError(
                f"Failed to build service '{key.__qualname__}'"
            ) from exc
        finally:
            self._resolution_stack.pop()

        self._instances[key] = instance
        return instance

    def try_resolve(self, key: type[ServiceType]) -> ServiceType | None:
        """Return the registered service if available, otherwise ``None``."""

        try:
            return self.resolve(key)
        except ServiceResolutionError:
            return None

    def has(self, key: type[Any]) -> bool:
        """Check whether ``key`` is registered."""

        return key in self._instances or key in self._factories


def build_default_container(
    *,
    settings_path: str | Path | None = None,
    schema_path: str | Path | None = None,
    profile_dir: str | Path | None = None,
    validate_schema: bool = True,
    logger_name: str = "pneumostabsim",
) -> ServiceContainer:
    """Construct a :class:`ServiceContainer` with canonical registrations."""

    container = ServiceContainer()

    container.register_factory(
        SettingsService,
        lambda c: SettingsService(
            settings_path,
            schema_path=schema_path,
            validate_schema=validate_schema,
        ),
    )
    container.register_factory(
        SettingsManager,
        lambda c: SettingsManager(settings_path),
    )
    container.register_factory(
        ProfileSettingsManager,
        lambda c: ProfileSettingsManager(
            c.resolve(SettingsManager),
            Path(profile_dir) if profile_dir is not None else None,
        ),
    )
    configure_logging()
    container.register_factory(
        BoundLogger, lambda c: get_logger(logger_name).bind(component="core")
    )
    container.register_factory(EventLogger, lambda c: EventLogger())
    container.register_factory(TelemetryTracker, lambda c: TelemetryTracker())
    container.register_factory(EventBus, lambda c: EventBus())

    return container
