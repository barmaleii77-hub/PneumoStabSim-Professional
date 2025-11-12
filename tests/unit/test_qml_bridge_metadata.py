"""Unit tests covering failure handling in :mod:`src.ui.qml_bridge`."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

import pytest

MODULE_PATH = Path(__file__).resolve().parents[2] / "src" / "ui" / "qml_bridge.py"

spec = importlib.util.spec_from_file_location(
    "test_support.qml_bridge_meta", MODULE_PATH
)
if spec is None or spec.loader is None:  # pragma: no cover - defensive guard
    raise RuntimeError("Failed to load qml_bridge module for testing")
qml_bridge = importlib.util.module_from_spec(spec)
sys.modules.setdefault("test_support.qml_bridge_meta", qml_bridge)
spec.loader.exec_module(qml_bridge)


@pytest.fixture(autouse=True)
def clear_metadata_cache():
    """Ensure every test operates on a clean metadata cache."""

    qml_bridge.get_bridge_metadata.cache_clear()
    yield
    qml_bridge.get_bridge_metadata.cache_clear()


def test_get_bridge_metadata_raises_on_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "qml_bridge.yaml"

    with pytest.raises(qml_bridge.QMLBridgeMetadataError) as excinfo:
        qml_bridge.get_bridge_metadata(missing)

    message = str(excinfo.value)
    assert "metadata file not found" in message
    assert str(missing) in message


def test_get_bridge_metadata_raises_on_yaml_errors(tmp_path: Path) -> None:
    broken = tmp_path / "qml_bridge.yaml"
    broken.write_text("value: [unterminated", encoding="utf-8")

    with pytest.raises(qml_bridge.QMLBridgeMetadataError) as excinfo:
        qml_bridge.get_bridge_metadata(broken)

    message = str(excinfo.value)
    assert "Failed to parse" in message
    assert str(broken) in message
