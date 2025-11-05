"""Infrastructure utilities shared across application layers."""

from .container import (
    ServiceContainer,
    ServiceRegistrationError,
    ServiceResolutionError,
    ServiceToken,
    get_default_container,
    set_default_container,
)
from .event_bus import EVENT_BUS_TOKEN, EventBus, get_event_bus
from .logging import (
    LOGGER_TOKEN,
    ErrorHookManager,
    configure_logging,
    get_logger,
    install_error_hooks,
)

__all__ = [
    "ServiceContainer",
    "ServiceRegistrationError",
    "ServiceResolutionError",
    "ServiceToken",
    "get_default_container",
    "set_default_container",
    "EventBus",
    "EVENT_BUS_TOKEN",
    "get_event_bus",
    "LOGGER_TOKEN",
    "ErrorHookManager",
    "configure_logging",
    "get_logger",
    "install_error_hooks",
]
