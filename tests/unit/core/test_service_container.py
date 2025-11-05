from __future__ import annotations

import json
from pathlib import Path

import pytest
from structlog.stdlib import BoundLogger

from src.core.container import (
    EventBus,
    ServiceContainer,
    ServiceRegistrationError,
    ServiceResolutionError,
    build_default_container,
)
from src.core.settings_service import SettingsService
from src.common.settings_manager import ProfileSettingsManager, SettingsManager
from src.telemetry import TelemetryTracker


def test_register_and_resolve_singleton() -> None:
    container = ServiceContainer()

    calls: list[int] = []

    class Foo:
        pass

    container.register_factory(Foo, lambda c: calls.append(1) or Foo())

    first = container.resolve(Foo)
    second = container.resolve(Foo)

    assert isinstance(first, Foo)
    assert first is second
    assert calls == [1]


def test_register_duplicate_service_raises() -> None:
    container = ServiceContainer()

    class Foo:
        pass

    container.register_factory(Foo, lambda c: Foo())

    with pytest.raises(ServiceRegistrationError):
        container.register_instance(Foo, Foo())


def test_circular_dependency_detection() -> None:
    container = ServiceContainer()

    class Foo:
        pass

    class Bar:
        pass

    container.register_factory(Foo, lambda c: c.resolve(Bar))
    container.register_factory(Bar, lambda c: c.resolve(Foo))

    with pytest.raises(ServiceResolutionError) as exc:
        container.resolve(Foo)

    assert "Circular dependency" in str(exc.value)


def _write_settings_payload(path: Path) -> None:
    payload = {
        "current": {
            "graphics": {
                "environment": {"sky_intensity": 1.0},
                "scene": {"exposure": 0.5},
                "animation": {"speed": 1.0},
            }
        },
        "defaults_snapshot": {
            "graphics": {
                "environment": {"sky_intensity": 1.0},
                "scene": {"exposure": 0.5},
                "animation": {"speed": 1.0},
            }
        },
        "metadata": {"units_version": "si_v2"},
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def test_build_default_container_wires_core_services(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    profile_dir = tmp_path / "profiles"
    _write_settings_payload(settings_path)

    container = build_default_container(
        settings_path=settings_path,
        profile_dir=profile_dir,
        validate_schema=False,
        logger_name="test-logger",
    )

    settings_service = container.resolve(SettingsService)
    settings_manager = container.resolve(SettingsManager)
    profile_manager = container.resolve(ProfileSettingsManager)
    logger = container.resolve(BoundLogger)
    event_bus = container.resolve(EventBus)
    telemetry_tracker = container.resolve(TelemetryTracker)

    assert settings_service.resolve_path() == settings_path
    assert settings_manager.settings_file == settings_path

    result = profile_manager.save_profile("Test")
    assert result.success
    saved_file = Path(result.message)
    assert saved_file.exists()
    assert saved_file.parent == profile_dir

    events: list[dict[str, str]] = []
    unsubscribe = event_bus.subscribe(
        "settings.updated", lambda payload: events.append(payload)
    )
    payload = {"path": "graphics.scene"}
    event_bus.publish("settings.updated", payload)
    unsubscribe()
    event_bus.publish("settings.updated", payload)

    assert events == [payload]
    assert isinstance(logger, BoundLogger)
    assert isinstance(telemetry_tracker, TelemetryTracker)
    bound_logger = logger.bind(test_case="container")
    assert bound_logger._context.get("component") == "core"
