"""Graphics panel package with lazy imports to support headless environments."""

from __future__ import annotations

import logging
from importlib import import_module
from typing import Any

__all__ = [
    "GraphicsPanel",
    "LightingTab",
    "EnvironmentTab",
    "QualityTab",
    "CameraTab",
    "MaterialsTab",
    "EffectsTab",
    "SceneTab",
    "ColorButton",
    "LabeledSlider",
    "FileCyclerWidget",
    "GraphicsStateManager",
    "GraphicsSettingsService",
    "GraphicsSettingsError",
    "get_settings_manager",
]

_logger = logging.getLogger(__name__)

_GRAPHICS_CLASS: type[Any] | None = None
_GRAPHICS_ERROR: ImportError | None = None

_MODULE_EXPORTS = {
    "LightingTab": ("lighting_tab", "LightingTab"),
    "EnvironmentTab": ("environment_tab", "EnvironmentTab"),
    "QualityTab": ("quality_tab", "QualityTab"),
    "CameraTab": ("camera_tab", "CameraTab"),
    "MaterialsTab": ("materials_tab", "MaterialsTab"),
    "EffectsTab": ("effects_tab", "EffectsTab"),
    "SceneTab": ("scene_tab", "SceneTab"),
    "ColorButton": ("widgets", "ColorButton"),
    "LabeledSlider": ("widgets", "LabeledSlider"),
    "FileCyclerWidget": ("widgets", "FileCyclerWidget"),
    "GraphicsStateManager": ("state_manager", "GraphicsStateManager"),
    "GraphicsSettingsService": (
        "panel_graphics_settings_manager",
        "GraphicsSettingsService",
    ),
    "GraphicsSettingsError": (
        "panel_graphics_settings_manager",
        "GraphicsSettingsError",
    ),
}


def _load_graphics_panel() -> type[Any]:
    """Load the graphics panel implementation on demand."""

    global _GRAPHICS_CLASS, _GRAPHICS_ERROR

    if _GRAPHICS_CLASS is not None:
        return _GRAPHICS_CLASS
    if _GRAPHICS_ERROR is not None:
        raise _GRAPHICS_ERROR

    try:
        module = import_module(".panel_graphics", __name__)
    except ImportError as exc:
        _GRAPHICS_ERROR = ImportError("GraphicsPanel implementation is unavailable")
        _GRAPHICS_ERROR.__cause__ = exc
        raise _GRAPHICS_ERROR

    _GRAPHICS_CLASS = module.GraphicsPanel
    _logger.info(
        "✅ GraphicsPanel: modular coordinator v3.1 loaded (SettingsService, tab architecture)"
    )
    return _GRAPHICS_CLASS


def __getattr__(name: str) -> Any:
    """Provide lazy access to graphics panel exports."""

    if name == "GraphicsPanel":
        return _load_graphics_panel()
    if name == "get_settings_manager":
        module = import_module("src.common.settings_manager")
        value = getattr(module, name)
        globals()[name] = value
        return value

    try:
        module_name, attribute = _MODULE_EXPORTS[name]
    except KeyError as exc:  # pragma: no cover - default behaviour
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from exc

    module = import_module(f"{__name__}.{module_name}")
    value = getattr(module, attribute)
    globals()[name] = value
    return value
