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


def _clear_pyside_modules() -> None:
    for module in list(sys.modules):
        if module.startswith("PySide6"):
            sys.modules.pop(module)


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


def test_lazy_loader_import_does_not_eagerly_load_qt() -> None:
    _clear_pyside_modules()

    lazy_loader = importlib.import_module("src.ui.lazy_loader")

    assert not any(key.startswith("PySide6") for key in sys.modules)
    assert hasattr(lazy_loader, "get_chart_widget")


def test_visualization_service_import_is_lightweight(block_pyside_import: None) -> None:
    module = importlib.import_module("src.ui.services.visualization_service")

    assert hasattr(module, "VisualizationService")


def test_ui_dunder_getattr_delegates_lazy_loader(monkeypatch) -> None:
    marker = object()

    stub_loader = ModuleType("src.ui.lazy_loader")
    stub_loader.get_main_window = lambda: marker  # type: ignore[attr-defined]
    sys.modules["src.ui.lazy_loader"] = stub_loader

    for module_name in [
        name for name in list(sys.modules) if name.startswith("src.ui")
    ]:
        if module_name != "src.ui.lazy_loader":
            sys.modules.pop(module_name)

    ui_module = importlib.import_module("src.ui")

    assert ui_module.MainWindow is marker


def test_hud_factories_are_cached(monkeypatch) -> None:
    # Ensure fresh import for cache isolation
    for module in [name for name in list(sys.modules) if name.startswith("src.ui.hud")]:
        sys.modules.pop(module)

    hud_module = importlib.import_module("src.ui.hud")
    monkeypatch.setattr(hud_module, "_CACHE", {})

    fake_widgets = ModuleType("src.ui.hud.widgets")
    fake_widgets.PressureScaleWidget = object()
    monkeypatch.setitem(sys.modules, "src.ui.hud.widgets", fake_widgets)

    call_count = {"factory": 0}
    original_cached = hud_module._cached

    def _tracking(name: str, factory):
        def _wrapped_factory():
            call_count["factory"] += 1
            return factory()

        return original_cached(name, _wrapped_factory)

    monkeypatch.setattr(hud_module, "_cached", _tracking)

    first = hud_module.get_pressure_scale_widget()
    second = hud_module.get_pressure_scale_widget()

    assert first is fake_widgets.PressureScaleWidget
    assert first is second
    assert call_count["factory"] == 1
