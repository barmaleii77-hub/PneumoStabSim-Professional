from __future__ import annotations

import copy
from dataclasses import dataclass
from threading import RLock
from typing import Any, Mapping

import structlog

from config.constants import get_settings_service
from src.core.settings_models import dump_settings
from src.infrastructure.container import (
    ServiceContainer,
    ServiceToken,
    get_default_container,
)
from src.infrastructure.event_bus import EventBus, get_event_bus


logger = structlog.get_logger(__name__)


@dataclass(frozen=True)
class GeometrySnapshot:
    current: Mapping[str, Any]
    defaults: Mapping[str, Any]


@dataclass(frozen=True)
class MaterialsSnapshot:
    current: Mapping[str, Any]
    defaults: Mapping[str, Any]


@dataclass(frozen=True)
class ResourceSnapshot:
    revision: int
    geometry: GeometrySnapshot
    materials: MaterialsSnapshot


class ResourceCache:
    """Thread-safe cache for geometry and material resources with consistency checks."""

    def __init__(
        self,
        *,
        settings_service: Any | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._settings_service = settings_service or get_settings_service()
        self._event_bus = event_bus or get_event_bus()
        self._lock = RLock()
        self._geometry: GeometrySnapshot | None = None
        self._materials: MaterialsSnapshot | None = None
        self._revision = 0
        self._unsubscribe = self._event_bus.subscribe(
            "settings.updated", self._handle_settings_updated
        )

    def snapshot(self) -> ResourceSnapshot:
        """Return a defensive copy of cached resources, loading if necessary."""

        with self._lock:
            if self._geometry is None or self._materials is None:
                self._load_from_settings()
            assert self._geometry is not None and self._materials is not None
            return ResourceSnapshot(
                revision=self._revision,
                geometry=copy.deepcopy(self._geometry),
                materials=copy.deepcopy(self._materials),
            )

    def invalidate(self) -> None:
        """Drop cached sections and advance the revision."""

        with self._lock:
            logger.info("resource_cache.invalidate", revision=self._revision)
            self._geometry = None
            self._materials = None
            self._revision += 1

    def _handle_settings_updated(self, payload: Any | None) -> None:
        logger.info("resource_cache.settings_updated", payload=bool(payload))
        self.invalidate()

    def _load_from_settings(self) -> None:
        payload = dump_settings(self._settings_service.load())

        geometry_current = self._extract_mapping(
            payload, ("current", "constants", "geometry")
        )
        geometry_defaults = self._extract_mapping(
            payload, ("defaults_snapshot", "constants", "geometry")
        )
        self._validate_geometry(geometry_current, geometry_defaults)

        materials_current = self._extract_mapping(
            payload, ("current", "graphics", "materials")
        )
        materials_defaults = self._extract_mapping(
            payload, ("defaults_snapshot", "graphics", "materials")
        )
        self._validate_materials(materials_current, materials_defaults)

        self._geometry = GeometrySnapshot(
            current=geometry_current, defaults=geometry_defaults
        )
        self._materials = MaterialsSnapshot(
            current=materials_current, defaults=materials_defaults
        )
        self._revision += 1
        logger.info(
            "resource_cache.loaded",
            revision=self._revision,
            geometry_keys=list(geometry_current.keys()),
            material_count=len(materials_current),
        )

    def _extract_mapping(
        self, payload: Mapping[str, Any], path: tuple[str, ...]
    ) -> Mapping[str, Any]:
        cursor: Any = payload
        for key in path:
            if not isinstance(cursor, Mapping) or key not in cursor:
                raise KeyError(f"Missing '{'.'.join(path)}' in settings")
            cursor = cursor[key]
        if not isinstance(cursor, Mapping):
            raise TypeError(
                f"Expected '{'.'.join(path)}' to be an object, got {type(cursor).__name__}"
            )
        return cursor

    def _validate_geometry(
        self,
        current: Mapping[str, Any],
        defaults: Mapping[str, Any],
    ) -> None:
        if set(current.keys()) != set(defaults.keys()):
            raise ValueError(
                "Geometry constants between current and defaults_snapshot are out of sync"
            )

    def _validate_materials(
        self,
        current: Mapping[str, Any],
        defaults: Mapping[str, Any],
    ) -> None:
        current_keys = set(current.keys())
        default_keys = set(defaults.keys())
        if current_keys != default_keys:
            raise ValueError(
                "Graphics materials between current and defaults_snapshot are out of sync"
            )

        for scope, section in (("current", current), ("defaults_snapshot", defaults)):
            for name, material in section.items():
                if not isinstance(material, Mapping):
                    raise TypeError(
                        f"graphics.materials.{name} in {scope} must be an object"
                    )
                material_id = material.get("id")
                if material_id != name:
                    raise ValueError(
                        f"graphics.materials.{name} in {scope} has mismatched id '{material_id}'"
                    )

    def close(self) -> None:
        """Detach event subscriptions when the cache is no longer needed."""

        with self._lock:
            unsubscribe = self._unsubscribe
            self._unsubscribe = None
        if unsubscribe:
            unsubscribe()


RESOURCE_CACHE_TOKEN = ServiceToken[ResourceCache](
    "core.resource_cache",
    "Cached geometry/material resources with consistency checks",
)


def get_resource_cache(container: ServiceContainer | None = None) -> ResourceCache:
    target = container or get_default_container()
    return target.resolve(RESOURCE_CACHE_TOKEN)
