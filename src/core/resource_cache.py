"""Resource cache for geometry and material payloads.

The cache centralises geometry/material lookups so that the rest of the
application can share a consistent snapshot and refresh it when configuration
changes are published on the event bus.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from threading import RLock
from typing import Any, Protocol

from config.constants import (
    get_geometry_cylinder_constants,
    get_geometry_initial_state_constants,
    get_geometry_kinematics_constants,
)
from src.graphics.materials.cache import get_material_cache
from src.infrastructure.container import (
    ServiceContainer,
    ServiceToken,
    get_default_container,
)
from src.infrastructure.event_bus import EVENT_BUS_TOKEN, EventBus


class _Loader(Protocol):
    def __call__(self) -> Any:  # pragma: no cover - structural protocol
        ...


@dataclass(frozen=True)
class ResourceBundle:
    """Immutable snapshot of cached resources."""

    geometry: Any
    materials: Any
    checksum: str
    revision: int


def _digest_payload(payload: Any) -> str:
    serialized = json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    return hashlib.sha256(serialized).hexdigest()


def _default_geometry_loader() -> dict[str, Any]:
    return {
        "cylinder": get_geometry_cylinder_constants(),
        "initial": get_geometry_initial_state_constants(),
        "kinematics": get_geometry_kinematics_constants(),
    }


class ResourceCache:
    """Thread-safe cache for geometry and material resources."""

    change_topic = "resources.changed"

    def __init__(
        self,
        *,
        geometry_loader: _Loader | None = None,
        material_loader: _Loader | None = None,
        event_bus: EventBus | None = None,
    ) -> None:
        self._geometry_loader: _Loader = geometry_loader or _default_geometry_loader
        self._material_loader: _Loader = material_loader or (
            lambda: get_material_cache().baseline()
        )
        self._event_bus = event_bus
        self._lock = RLock()
        self._bundle: ResourceBundle | None = None
        self._revision = 0

        if self._event_bus is not None:
            self._event_bus.subscribe(
                self.change_topic, lambda _payload=None: self.invalidate()
            )

    def snapshot(self, *, reload: bool = False, verify: bool = True) -> ResourceBundle:
        with self._lock:
            if reload or self._bundle is None:
                self._bundle = self._build_bundle()
            elif verify and not self.is_consistent():
                self._bundle = self._build_bundle()
            return self._bundle

    def geometry(self) -> Any:
        return self.snapshot().geometry

    def materials(self) -> Any:
        return self.snapshot().materials

    def invalidate(self) -> None:
        with self._lock:
            self._bundle = None

    def is_consistent(self) -> bool:
        bundle = self._bundle
        if bundle is None:
            return False
        expected_checksum = _digest_payload(
            {"geometry": bundle.geometry, "materials": bundle.materials}
        )
        return expected_checksum == bundle.checksum

    def _build_bundle(self) -> ResourceBundle:
        geometry_payload = self._geometry_loader()
        material_payload = self._material_loader()
        checksum = _digest_payload(
            {"geometry": geometry_payload, "materials": material_payload}
        )
        self._revision += 1
        return ResourceBundle(
            geometry=geometry_payload,
            materials=material_payload,
            checksum=checksum,
            revision=self._revision,
        )


RESOURCE_CACHE_TOKEN = ServiceToken[ResourceCache](
    "core.resource_cache",
    "Shared geometry/material cache with consistency verification",
)


def _resource_cache_factory(container: ServiceContainer) -> ResourceCache:
    bus = container.resolve(EVENT_BUS_TOKEN)
    return ResourceCache(event_bus=bus)


def get_resource_cache(container: ServiceContainer | None = None) -> ResourceCache:
    target = container or get_default_container()
    return target.resolve(RESOURCE_CACHE_TOKEN)
