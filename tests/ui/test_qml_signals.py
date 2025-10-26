from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtTest import QSignalSpy


def test_batch_updates_signal_exposed(qapp):
    engine = QQmlApplicationEngine()
    engine.addImportPath(str(Path("assets/qml").resolve()))

    qml_path = Path("assets/qml/main.qml").resolve()
    engine.load(QUrl.fromLocalFile(str(qml_path)))

    assert engine.rootObjects(), "main.qml should produce a root object"
    root = engine.rootObjects()[0]
    assert hasattr(root, "batchUpdatesApplied"), "Root must expose batchUpdatesApplied"

    spy = QSignalSpy(root.batchUpdatesApplied)

    simulation_loader = root.findChild(QObject, "simulationLoader")
    fallback_loader = root.findChild(QObject, "fallbackLoader")
    assert simulation_loader is not None
    assert fallback_loader is not None

    target_item = None
    for _ in range(10):
        simulation_item = simulation_loader.property("item")
        fallback_item = fallback_loader.property("item")
        target_item = simulation_item or fallback_item
        if target_item is not None:
            break
        qapp.processEvents()

    assert target_item is not None

    target_item.batchUpdatesApplied.emit({"category": "geometry"})
    qapp.processEvents()

    assert spy.count() == 1

    engine.deleteLater()
