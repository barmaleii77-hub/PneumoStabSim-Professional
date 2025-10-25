import pytest

from src.infrastructure.container import (
    ServiceContainer,
    ServiceRegistrationError,
    ServiceResolutionError,
    ServiceToken,
)


def test_resolve_returns_singleton_instance() -> None:
    container = ServiceContainer()
    token = ServiceToken[object]("demo")
    container.register_factory(token, lambda _: object())

    first = container.resolve(token)
    second = container.resolve(token)

    assert first is second


def test_override_temporarily_replaces_instance() -> None:
    container = ServiceContainer()
    token = ServiceToken[int]("value")
    container.register_factory(token, lambda _: 1)

    assert container.resolve(token) == 1

    with container.override(token, 42):
        assert container.resolve(token) == 42

    assert container.resolve(token) == 1


def test_reset_discards_cached_singleton() -> None:
    container = ServiceContainer()
    token = ServiceToken[object]("demo")
    container.register_factory(token, lambda _: object())

    original = container.resolve(token)
    container.reset(token)
    replacement = container.resolve(token)

    assert original is not replacement


def test_register_instance_rejects_duplicates() -> None:
    container = ServiceContainer()
    token = ServiceToken[int]("value")

    container.register_instance(token, 7)

    with pytest.raises(ServiceRegistrationError):
        container.register_factory(token, lambda _: 8)


def test_resolve_missing_service_raises() -> None:
    container = ServiceContainer()
    token = ServiceToken[int]("missing")

    with pytest.raises(ServiceResolutionError):
        container.resolve(token)
