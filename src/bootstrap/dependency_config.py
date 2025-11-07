from __future__ import annotations

import sys
from dataclasses import dataclass
from functools import lru_cache
from typing import Any
from collections.abc import Mapping, Sequence

try:  # pragma: no cover - import guarded for minimal environments
    from src.core.settings_service import (
        SETTINGS_SERVICE_TOKEN,
        SettingsValidationError,
    )
except Exception:  # pragma: no cover - fallback path when dependencies are missing
    SETTINGS_SERVICE_TOKEN = object()

    class SettingsValidationError(RuntimeError):
        """Fallback used when the typed settings service is unavailable."""

    _SETTINGS_IMPORT_FAILED = True
else:  # pragma: no cover - exercised in integration tests
    _SETTINGS_IMPORT_FAILED = False

try:  # pragma: no cover - import guarded for minimal environments
    from src.infrastructure.container import (
        ServiceResolutionError,
        get_default_container,
    )
except Exception:  # pragma: no cover - fallback when DI container is unavailable

    class ServiceResolutionError(LookupError):
        """Fallback error raised when the dependency container is missing."""

    def get_default_container() -> Any:
        raise ServiceResolutionError("Default service container is not available")

    _CONTAINER_IMPORT_FAILED = True
else:  # pragma: no cover - exercised in integration tests
    _CONTAINER_IMPORT_FAILED = False


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
def _fallback_dependencies() -> Mapping[str, Any]:
    """Return a minimal dependency configuration when settings cannot be read."""

    return {
        "opengl_runtime": {
            "description": "OpenGL runtime required for Qt Quick rendering.",
            "missing_message": "Required OpenGL runtime ({human_name}) is missing.",
            "variants": (
                {
                    "id": "linux_default",
                    "platform_prefixes": ("linux", "linux2"),
                    "library_name": "GL",
                    "human_name": "libGL.so.1",
                    "install_hint": "Install a Mesa/OpenGL package (e.g. 'apt-get install -y libgl1').",
                    "error_markers": ("libGL.so.1",),
                },
                {
                    "id": "windows_default",
                    "platform_prefixes": ("win32", "cygwin"),
                    "library_name": "opengl32",
                    "human_name": "opengl32.dll",
                    "install_hint": "Install the latest GPU drivers or enable OpenGL compatibility components.",
                    "error_markers": ("opengl32.dll", "opengl32"),
                },
                {
                    "id": "macos_default",
                    "platform_prefixes": ("darwin",),
                    "library_name": "OpenGL",
                    "human_name": "OpenGL.framework",
                    "install_hint": "Ensure the Xcode command line tools are installed for OpenGL support.",
                    "error_markers": ("OpenGL.framework", "OpenGL"),
                },
            ),
        }
    }


@lru_cache(maxsize=None)
def _load_dependencies_section() -> Mapping[str, Any]:
    if _SETTINGS_IMPORT_FAILED or _CONTAINER_IMPORT_FAILED:
        return _fallback_dependencies()

    try:
        container = get_default_container()
    except ServiceResolutionError:
        return _fallback_dependencies()

    try:
        settings = container.resolve(SETTINGS_SERVICE_TOKEN)
    except ServiceResolutionError:
        return _fallback_dependencies()

    try:
        section = settings.get("current.system.dependencies")
    except SettingsValidationError:
        return _fallback_dependencies()

    if not isinstance(section, Mapping):
        return _fallback_dependencies()
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
        if variant.is_default:
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
