"""Tests for the centralised QML bridge metadata registry."""

from __future__ import annotations

from pathlib import Path

from src.ui.main_window import qml_bridge as legacy_bridge
from src.ui.qml_bridge import (
    QMLBridgeRegistry,
    dump_bridge_routes,
    get_qml_update_methods,
    iter_bridge_categories,
)


def test_update_methods_match_legacy_bridge() -> None:
    methods = get_qml_update_methods()
    assert "geometry" in methods
    assert methods == legacy_bridge.QMLBridge.QML_UPDATE_METHODS


def test_dump_routes_contains_core_metadata() -> None:
    dump = dump_bridge_routes()
    assert "| geometry |" in dump
    assert legacy_bridge.QMLBridge.BRIDGE_PROPERTY in dump
    if legacy_bridge.QMLBridge.ACK_SIGNAL:
        assert legacy_bridge.QMLBridge.ACK_SIGNAL in dump


def test_registry_reload_with_custom_file(tmp_path: Path) -> None:
    metadata_file = tmp_path / "qml_bridge.yaml"
    metadata_file.write_text(
        """version: 1
qml_property: customPending
categories:
  demo:
    methods:
      - applyDemo
""",
        encoding="utf-8",
    )

    original_methods = get_qml_update_methods()

    try:
        QMLBridgeRegistry.configure(metadata_path=metadata_file)
        reloaded = get_qml_update_methods(force_reload=True)
        assert reloaded == {"demo": ("applyDemo",)}
    finally:
        QMLBridgeRegistry.configure(metadata_path=None)
        legacy_bridge.QMLBridge.reload_bridge_metadata(force=True)

    assert get_qml_update_methods(force_reload=True) == original_methods


def test_iter_bridge_categories_sorted() -> None:
    categories = list(iter_bridge_categories())
    names = [category.name for category in categories]
    assert names == sorted(names)
    assert {category.name for category in categories} == set(
        legacy_bridge.QMLBridge.QML_UPDATE_METHODS
    )
