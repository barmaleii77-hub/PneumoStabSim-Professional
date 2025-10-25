from __future__ import annotations

import sys
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Mapping, Sequence

from src.core.settings_service import get_settings_service


class DependencyConfigError(RuntimeError):
    """Raised when the dependency configuration in settings is invalid."""


def _iter_string_sequence(value: Any) -> tuple[str, ...]:
    if isinstance(value, (list, tuple)):
        return tuple(item for item in value if isinstance(item, str))
    if isinstance(value, str):
        return (value,)
    return ()


@dataclass(frozen=True)
class DependencyVariant:
    """Represents a dependency variant resolved from settings."""

    name: str
    data: Mapping[str, Any]
    dependency: Mapping[str, Any]

    def matches_platform(self, platform_key: str) -> bool:
        prefixes = self.data.get("platform_prefixes")
        candidates = _iter_string_sequence(prefixes)
        if not candidates:
            return False
        return any(platform_key.startswith(prefix) for prefix in candidates)

    @property
    def library_name(self) -> str:
        value = self.data.get("library_name")
        if not isinstance(value, str):
            raise DependencyConfigError(
                f"Missing 'library_name' for dependency '{self.name}' variant {self.data!r}"
            )
        return value

    @property
    def human_name(self) -> str:
        value = self.data.get("human_name")
        if isinstance(value, str):
            return value
        return self.library_name

    @property
    def install_hint(self) -> str | None:
        value = self.data.get("install_hint")
        if isinstance(value, str):
            return value
        value = self.dependency.get("install_hint")
        if isinstance(value, str):
            return value
        return None

    @property
    def error_markers(self) -> tuple[str, ...]:
        markers = _iter_string_sequence(self.data.get("error_markers"))
        if markers:
            return markers
        return _iter_string_sequence(self.dependency.get("error_markers"))

    @property
    def missing_message(self) -> str | None:
        template = self.data.get("missing_message")
        if not isinstance(template, str):
            template = self.dependency.get("missing_message")
        if isinstance(template, str):
            try:
                context: dict[str, Any] = {}
                context.update(self.dependency)
                context.update(self.data)
                return template.format(**context)
            except KeyError:
                return template
        return None

    @property
    def is_default(self) -> bool:
        return bool(self.data.get("is_default", False))


@lru_cache(maxsize=None)
def _load_dependencies_section() -> Mapping[str, Any]:
    settings = get_settings_service()
    section = settings.get("current.system.dependencies")
    if not isinstance(section, Mapping):
        raise DependencyConfigError(
            "Missing 'current.system.dependencies' section in app settings."
        )
    return section


def _iter_variants(dependency: Mapping[str, Any]) -> Sequence[Mapping[str, Any]]:
    variants = dependency.get("variants")
    if not isinstance(variants, Sequence):
        raise DependencyConfigError(
            "Dependency configuration must define a list of variants."
        )
    return variants


def resolve_dependency_variant(
    name: str, *, platform_key: str | None = None
) -> DependencyVariant:
    """Resolve a dependency variant for the requested platform."""

    dependencies = _load_dependencies_section()
    raw_dependency = dependencies.get(name)
    if not isinstance(raw_dependency, Mapping):
        raise DependencyConfigError(f"Dependency '{name}' is not defined in settings.")

    target_platform = platform_key or sys.platform
    default_variant: DependencyVariant | None = None
    for raw_variant in _iter_variants(raw_dependency):
        if not isinstance(raw_variant, Mapping):
            continue
        variant = DependencyVariant(
            name=name, data=raw_variant, dependency=raw_dependency
        )
        if variant.matches_platform(target_platform):
            return variant
        if variant.is_default():
            default_variant = variant

    if default_variant is not None:
        return default_variant

    raise DependencyConfigError(
        f"No variant configured for dependency '{name}' matches platform '{target_platform}'."
    )


def match_dependency_error(
    name: str,
    message: str,
    *,
    platform_key: str | None = None,
) -> DependencyVariant | None:
    """Return the dependency variant if the error message matches its markers."""

    try:
        variant = resolve_dependency_variant(name, platform_key=platform_key)
    except DependencyConfigError:
        return None

    markers = variant.error_markers
    if not markers:
        return variant

    haystack = message.lower()
    for marker in markers:
        if marker.lower() in haystack:
            return variant
    return None


__all__ = [
    "DependencyConfigError",
    "DependencyVariant",
    "match_dependency_error",
    "resolve_dependency_variant",
]
