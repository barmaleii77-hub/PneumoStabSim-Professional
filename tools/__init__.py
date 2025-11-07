"""Helper utilities for PneumoStabSim developer tools."""

from __future__ import annotations

import importlib
from types import ModuleType
from typing import Dict

_KNOWN_SUBMODULES = {
    "ci_tasks",
    "cipilot_environment",
    "project_sanitize",
    "quality.report_metrics",
    "validate_settings",
    "audit.redundant_files",
    "collect_qml_errors",
    "run_test_case",
    "check_shader_logs",
}

_cache: dict[str, ModuleType] = {}


def __getattr__(name: str) -> ModuleType:
    if name in _cache:
        return _cache[name]

    if name in _KNOWN_SUBMODULES:
        module = importlib.import_module(f"tools.{name}")
        _cache[name] = module
        return module

    # Support dotted module names declared in _KNOWN_SUBMODULES
    for dotted in _KNOWN_SUBMODULES:
        if "." in dotted and dotted.split(".")[0] == name:
            module = importlib.import_module(f"tools.{dotted}")
            _cache[dotted] = module
            return module

    raise AttributeError(f"module 'tools' has no attribute '{name}'")


__all__ = sorted({entry.split(".")[0] for entry in _KNOWN_SUBMODULES})
