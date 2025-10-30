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
_USING_REFACTORED = False

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

    global _GRAPHICS_CLASS, _GRAPHICS_ERROR, _USING_REFACTORED

    if _GRAPHICS_CLASS is not None:
        return _GRAPHICS_CLASS
    if _GRAPHICS_ERROR is not None:
        raise _GRAPHICS_ERROR

    last_error: ImportError | None = None
    for module_name, refactored in (
        (".panel_graphics_refactored", True),
        ("..panel_graphics", False),
    ):
        try:
            module = import_module(module_name, __name__)
        except ImportError as exc:
            last_error = exc
            if refactored:
                _logger.warning(
                    "⚠️ GraphicsPanel: failed to load refactored version: %s", exc
                )
            else:
                _logger.error(
                    "❌ GraphicsPanel: failed to load legacy version: %s", exc
                )
            continue

        _GRAPHICS_CLASS = module.GraphicsPanel
        _USING_REFACTORED = refactored
        if refactored:
            _logger.info(
                "✅ GraphicsPanel: REFACTORED version v3.0 loaded (SettingsManager + GraphicsSettingsService)"
            )
        else:
            _logger.warning(
                "⚠️ GraphicsPanel: Using LEGACY version (~2600 lines) - migration incomplete"
            )
        return _GRAPHICS_CLASS

    _GRAPHICS_ERROR = ImportError(
        "GraphicsPanel: Neither refactored nor legacy version available!"
    )
    if last_error is not None:
        _GRAPHICS_ERROR.__cause__ = last_error
    raise _GRAPHICS_ERROR


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
