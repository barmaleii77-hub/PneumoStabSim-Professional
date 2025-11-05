"""Integration tests validating the Training Panel QML bindings."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("pytestqt")
pytest.importorskip("PySide6.QtQml")

from PySide6.QtCore import QMetaObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

from tests.scenarios import SCENARIO_INDEX


@pytest.mark.gui
@pytest.mark.usefixtures("qapp")
def test_training_panel_loads_presets(qtbot, training_preset_bridge):
    """The Training panel should surface presets and scenario metadata."""

    preset_id = training_preset_bridge.defaultPresetId()
    if not preset_id:
        presets = training_preset_bridge.listPresets()
        assert presets, "Training preset bridge returned no presets"
        preset_id = str(presets[0].get("id", "")).strip()
        assert preset_id, "First preset is missing an identifier"
    assert training_preset_bridge.applyPreset(preset_id)

    engine = QQmlEngine()
    qml_root = Path("assets/qml").resolve()
    engine.addImportPath(str(qml_root))

    component = QQmlComponent(engine)
    panel_path = qml_root / "training" / "TrainingPanel.qml"
    component.loadUrl(QUrl.fromLocalFile(str(panel_path)))
    if component.isError():  # pragma: no cover - diagnostic aid
        messages = "; ".join(message.toString() for message in component.errors())
        pytest.fail(f"Failed to load TrainingPanel.qml: {messages}")

    panel = component.create()
    assert panel is not None, "Expected a concrete TrainingPanel instance"
    panel.setProperty("bridge", training_preset_bridge)

    QMetaObject.invokeMethod(panel, "loadFromBridge")
    qtbot.waitUntil(lambda: bool(panel.property("presetModel")), timeout=1000)

    active_id = panel.property("activePresetId") or ""
    assert active_id == preset_id

    selected_details = panel.property("selectedDetails")
    assert isinstance(selected_details, dict)
    assert selected_details.get("id") == preset_id

    metadata = selected_details.get("metadata", {})
    scenario_id = metadata.get("scenarioId", "")
    assert scenario_id in SCENARIO_INDEX

    descriptor = SCENARIO_INDEX[scenario_id]
    assert metadata.get("difficulty") in {descriptor.difficulty, "mixed"}
    assert set(metadata.get("evaluationMetrics", [])) <= set(descriptor.metrics)

    simulation_entries = panel.property("simulationEntries") or []
    assert simulation_entries, "Simulation entries should be populated"
    pneumatic_entries = panel.property("pneumaticEntries") or []
    assert pneumatic_entries, "Pneumatic entries should be populated"

    panel.deleteLater()
    component.deleteLater()
    engine.deleteLater()
