# Service Container

The service container centralises cross-cutting dependencies so modules can
request the capabilities they need without importing module-level singletons.
It fulfils the objectives set in the renovation master plan (Phase 2 –
"Dependency Injection & Services") and provides the baseline for wiring
settings, logging, simulation, and diagnostic facilities.

## Core concepts

- **ServiceToken** – a typed identifier that names the dependency. Tokens live
  close to the modules that own a service. For example,
  `src/core/settings_service.py` exposes `SETTINGS_SERVICE_TOKEN`.
- **ServiceContainer** – a thread-safe registry that resolves services either
  via a lazy factory or a pre-constructed instance.
- **Default container** – `src.infrastructure.container.get_default_container()`
  returns the process-wide instance. Tests may replace it temporarily with
  `set_default_container`, but the common pattern is to work with the default
  container directly.

## Registering services

```python
from src.core.settings_service import SETTINGS_SERVICE_TOKEN, SettingsService
from src.infrastructure.container import get_default_container

container = get_default_container()
if not container.is_registered(SETTINGS_SERVICE_TOKEN):
    container.register_factory(SETTINGS_SERVICE_TOKEN, lambda _: SettingsService())
```

Factories receive the container so they can resolve other dependencies on
request. The helper `is_registered` prevents duplicate registrations when
modules are imported multiple times across Qt/Python boundaries.

## Resolving services

```python
from src.core.settings_service import get_settings_service

service = get_settings_service()  # pulls from the shared container
```

`get_settings_service` delegates to the container to honour overrides and other
lifecycle management hooks.

## Overrides in tests

```python
from src.infrastructure.container import get_default_container
from src.core.settings_service import SETTINGS_SERVICE_TOKEN, SettingsService

container = get_default_container()
override = SettingsService(settings_path="/tmp/test.json")

with container.override(SETTINGS_SERVICE_TOKEN, override):
    assert get_settings_service() is override
```

Overrides are stacked, making it safe to nest fixtures. Exiting the context
restores the previous value automatically. Use `container.reset(token)` to drop
cached singletons when tests need a clean slate.

## Lifecycle management

- `register_instance` stores a pre-built object for a token.
- `reset(token)` removes cached singletons and clears overrides for the token.
- `reset()` with no arguments clears the entire container state.
- `set_default_container` swaps the global container, intended only for highly
  isolated tests or experimental harnesses.

## Next steps

- Register logging, event bus, and simulation runner factories once their
  refactors stabilise.
- Document production wiring diagrams in `docs/ARCHITECTURE_MAP.md` so new
  contributors can map tokens to runtime components quickly.
