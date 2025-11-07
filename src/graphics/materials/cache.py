"""Material baseline cache registered in the service container."""

from __future__ import annotations

from pathlib import Path
from threading import RLock
from collections.abc import Callable

from src.infrastructure.container import (
    ServiceContainer,
    ServiceToken,
    get_default_container,
)

from .baseline import MaterialsBaseline, load_materials_baseline

__all__ = ["MaterialCache", "MATERIAL_CACHE_TOKEN", "get_material_cache"]


BaselineLoader = Callable[[Path | None], MaterialsBaseline]


class MaterialCache:
    """Thread-safe cache for the lighting/material baseline payload."""

    def __init__(
        self,
        *,
        baseline_path: Path | None = None,
        loader: BaselineLoader | None = None,
    ) -> None:
        self._baseline_path = baseline_path
        self._loader = loader or _default_loader
        self._baseline: MaterialsBaseline | None = None
        self._lock = RLock()

    def baseline(self, *, reload: bool = False) -> MaterialsBaseline:
        """Return the cached :class:`MaterialsBaseline` instance."""

        with self._lock:
            if reload:
                self._baseline = None
            if self._baseline is None:
                self._baseline = self._loader(self._baseline_path)
            return self._baseline

    def refresh(self) -> MaterialsBaseline:
        """Force a baseline reload and return the new instance."""

        return self.baseline(reload=True)


def _default_loader(path: Path | None) -> MaterialsBaseline:
    if path is None:
        return load_materials_baseline()
    return load_materials_baseline(path)


MATERIAL_CACHE_TOKEN = ServiceToken[MaterialCache](
    "graphics.material_cache",
    "Cached access to materials and lighting baselines",
)


def get_material_cache(container: ServiceContainer | None = None) -> MaterialCache:
    """Resolve the shared :class:`MaterialCache` from the service container."""

    target = container or get_default_container()
    return target.resolve(MATERIAL_CACHE_TOKEN)
