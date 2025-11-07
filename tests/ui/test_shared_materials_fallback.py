"""Tests for fallback behaviour in SharedMaterials texture loading."""

from __future__ import annotations

from pathlib import Path
from typing import List, Tuple

import pytest

pytest.importorskip("pytestqt")
pytest.importorskip("PySide6.QtQml")
pytest.importorskip("PySide6.QtQuick")
pytest.importorskip("PySide6.QtQuick3D")

from PySide6.QtCore import QUrl, QtMsgType, qInstallMessageHandler
from PySide6.QtQml import QQmlComponent, QQmlEngine

REPO_ROOT = Path(__file__).resolve().parents[2]
SHARED_MATERIALS_QML = REPO_ROOT / "assets" / "qml" / "scene" / "SharedMaterials.qml"


@pytest.fixture
def qml_engine(qapp):  # type: ignore[no-untyped-def]
    engine = QQmlEngine()
    engine.addImportPath(str((REPO_ROOT / "assets" / "qml").resolve()))
    try:
        yield engine
    finally:
        engine.deleteLater()


@pytest.mark.gui
def test_assets_loader_switches_to_fallback_when_source_missing(qml_engine, qapp):  # type: ignore[no-untyped-def]
    component = QQmlComponent(
        qml_engine, QUrl.fromLocalFile(str(SHARED_MATERIALS_QML.resolve()))
    )
    if component.isError():
        messages = ", ".join(message.toString() for message in component.errors())
        pytest.fail(f"Failed to load SharedMaterials component: {messages}")

    shared_materials = component.create()
    assert shared_materials is not None, "Expected SharedMaterials instance"

    captured_messages: List[Tuple[QtMsgType, str]] = []

    def _message_handler(mode: QtMsgType, _context, message: str) -> None:
        captured_messages.append((mode, message))

    previous_handler = qInstallMessageHandler(_message_handler)

    try:
        shared_materials.setProperty(
            "materialsDefaults",
            {"frame": {"texture_path": "/definitely/missing/texture.png"}},
        )

        for _ in range(5):
            qapp.processEvents()

        texture = shared_materials.property("frameBaseColorTexture")
        assert texture is not None, "Expected frame texture instance"
        assert bool(texture.property("fallbackActive")) is True
        assert bool(texture.property("usingFallbackItem")) is True
        reason = texture.property("fallbackReason")
        assert isinstance(reason, str) and reason, (
            "Expected fallback reason to be recorded"
        )
    finally:
        qInstallMessageHandler(previous_handler)
        shared_materials.deleteLater()
        component.deleteLater()
        qml_engine.collectGarbage()

    assert any(
        "AssetsLoader" in message and "fallback" in message.lower()
        for _mode, message in captured_messages
    ), "Expected warning about switching to fallback resource"
