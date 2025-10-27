from pathlib import Path

import pytest

pytest.importorskip(
    "PySide6.QtTest",
    reason="PySide6 QtTest module is required for UI signal tests",
    exc_type=ImportError,
)

from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QSignalSpy


def _has_property(obj: QObject, name: str) -> bool:
    meta = obj.metaObject()
    return meta.indexOfProperty(name) >= 0


def _resolve_batch_target(root: QObject, qapp) -> QObject | None:
    if _has_property(root, "pendingPythonUpdates"):
        return root

    for loader_name in ("simulationLoader", "fallbackLoader"):
        loader = root.findChild(QObject, loader_name)
        if loader is None:
            continue

        item = loader.property("item")
        attempts = 0
        while item is None and attempts < 10:
            qapp.processEvents()
            item = loader.property("item")
            attempts += 1

        if item is not None and isinstance(item, QObject):
            if _has_property(item, "pendingPythonUpdates"):
                return item

    return None


@pytest.mark.parametrize(
    "qml_file",
    [
        "assets/qml/main.qml",
        "assets/qml/main_v2_realism.qml",
        "assets/qml/main_fallback.qml",
    ],
)
def test_batch_updates_signal_exposed(qapp, qml_file):
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(Path("assets/qml").resolve()))

    qml_path = Path(qml_file).resolve()
    engine.load(QUrl.fromLocalFile(str(qml_path)))

    assert engine.rootObjects(), f"{qml_file} should produce a root object"
    root = engine.rootObjects()[0]
    assert hasattr(root, "batchUpdatesApplied"), "Root must expose batchUpdatesApplied"

    target = _resolve_batch_target(root, qapp)
    assert target is not None, "No target exposing pendingPythonUpdates"

    spy = QSignalSpy(root.batchUpdatesApplied)

    initial_count = spy.count()
    target.setProperty("pendingPythonUpdates", {"geometry": {"frameLength": 2.0}})
    qapp.processEvents()

    assert spy.count() > initial_count
    summary = spy.at(spy.count() - 1)[0]
    if hasattr(summary, "toVariant"):
        summary = summary.toVariant()

    assert summary is not None
    if isinstance(summary, dict):
        categories = summary.get("categories")
        if categories is None and "category" in summary:
            categories = summary["category"]
        assert categories is not None

    engine.deleteLater()
