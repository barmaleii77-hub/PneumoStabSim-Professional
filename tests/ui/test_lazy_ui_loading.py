"""Smoke tests ensuring UI modules import without Qt bindings present."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType
from typing import Iterable

import pytest


@pytest.fixture
def block_pyside_import(monkeypatch) -> None:
    import builtins

    original_import = builtins.__import__

    def _guarded_import(  # type: ignore[override]
        name: str,
        globals: dict | None = None,
        locals: dict | None = None,
        fromlist: Iterable[str] = (),
        level: int = 0,
    ) -> ModuleType:
        if name.startswith("PySide6"):
            raise ImportError("PySide6 import blocked for smoke test")
        return original_import(name, globals, locals, fromlist, level)

    for module in list(sys.modules):
        if module.startswith("src.ui"):
            sys.modules.pop(module)

    monkeypatch.setattr(builtins, "__import__", _guarded_import)


def test_ui_imports_without_qt(block_pyside_import: None) -> None:
    ui_module = importlib.import_module("src.ui")
    hud_module = importlib.import_module("src.ui.hud")

    assert ui_module.__name__ == "src.ui"
    assert hud_module.__name__ == "src.ui.hud"


def test_lazy_factories_blocked_without_qt(block_pyside_import: None) -> None:
    lazy_loader = importlib.import_module("src.ui.lazy_loader")

    widget_cls = lazy_loader.get_pressure_scale_widget()
    assert widget_cls.__name__ == "PressureScaleWidget"

    ui_module = importlib.import_module("src.ui")
    assert ui_module.PressureScaleWidget is widget_cls
