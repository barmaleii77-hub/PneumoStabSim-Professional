"""Compatibility layer for legacy ``PneumoStabSim.*`` imports.

The modern codebase organises Python modules under domain-oriented packages such
as ``src.core`` and ``src.ui``.  Older scripts – especially archived tooling and
third-party integrations – may still reference CamelCase modules from the
pre-refactor layout (for example ``PneumoStabSim.Core.settings_service``).

This module keeps those imports working by forwarding lookups to the canonical
snake_case packages.  The compatibility layer is intentionally lightweight:

* ``import PneumoStabSim.core`` resolves to ``src.core``;
* ``import PneumoStabSim.Core`` resolves to the same module;
* submodule imports (``PneumoStabSim.core.settings_service``) are delegated to
  the aliased package, so existing code keeps functioning without changes.

Only the actively supported domains are exposed here.  Additional aliases can
be added in one place if future consumers require them.
"""

from __future__ import annotations

from importlib import import_module
import sys
from types import ModuleType
from typing import Final

__all__ = [
    "core",
    "Core",
    "ui",
    "UI",
    "graphics",
    "Graphics",
    "simulation",
    "Simulation",
    "infrastructure",
    "Infrastructure",
]


AliasKey = str

_ALIASES: Final[dict[AliasKey, str]] = {
    "core": "src.core",
    "ui": "src.ui",
    "graphics": "src.graphics",
    "simulation": "src.simulation",
    "infrastructure": "src.infrastructure",
}

_SYNONYMS: Final[dict[AliasKey, tuple[str, ...]]] = {
    "core": ("core", "Core"),
    "ui": ("ui", "UI"),
    "graphics": ("graphics", "Graphics"),
    "simulation": ("simulation", "Simulation"),
    "infrastructure": ("infrastructure", "Infrastructure"),
}


def _load_alias(name: str) -> ModuleType:
    key = name.lower()
    target = _ALIASES.get(key)
    if target is None:
        raise AttributeError(name)

    module = import_module(target)
    variants = set(_SYNONYMS.get(key, (name, name.lower())))
    variants.add(name)

    for variant in variants:
        qualified = f"{__name__}.{variant}"
        sys.modules.setdefault(qualified, module)
        setattr(sys.modules[__name__], variant, module)

    return module


def __getattr__(name: str) -> ModuleType:
    try:
        return _load_alias(name)
    except AttributeError as exc:  # pragma: no cover - mirrors stdlib behaviour
        raise AttributeError(
            f"module '{__name__}' has no attribute '{name}'"
        ) from exc


def __dir__() -> list[str]:  # pragma: no cover - convenience for debuggers
    entries = set(globals())
    for variants in _SYNONYMS.values():
        entries.update(variants)
    return sorted(entries)

