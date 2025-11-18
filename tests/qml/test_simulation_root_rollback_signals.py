from pathlib import Path

import pytest

from tests.helpers import SignalListener, require_qt_modules

require_qt_modules("PySide6.QtQml")

from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_simulation_root_emits_rollback_hooks(qapp) -> None:  # type: ignore[missing-type-doc]
    engine = QQmlEngine()
    component = QQmlComponent(engine)
    component.loadUrl(QUrl.fromLocalFile(str(Path("qml/SimulationRoot.qml").resolve())))

    if component.status() != QQmlComponent.Ready:
        messages = component.errorString()
        raise RuntimeError(f"Failed to load SimulationRoot.qml: {messages}")

    root = component.create()

    try:
        undo_spy = SignalListener(root.undoPostEffects)
        reset_spy = SignalListener(root.resetSharedMaterials)

        root.triggerUndoPostEffects()
        root.triggerResetSharedMaterials()
        qapp.processEvents()

        assert len(undo_spy) == 1
        assert len(reset_spy) == 1
    finally:
        root.deleteLater()
        component.deleteLater()
        engine.deleteLater()
