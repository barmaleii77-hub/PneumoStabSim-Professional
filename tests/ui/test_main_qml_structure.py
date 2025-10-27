"""Structural checks for the main QML entry point."""

from __future__ import annotations

from pathlib import Path

import pytest

QML_ROOT = Path("assets/qml/main.qml")


@pytest.mark.gui
def test_main_qml_contains_required_elements():
    """Ensure the top-level scene exposes loaders and acknowledgement hooks."""
    assert QML_ROOT.exists(), "assets/qml/main.qml must exist for the UI to load"

    contents = QML_ROOT.read_text(encoding="utf-8")

    expected_tokens = {
        "batch ack signal": "signal batchUpdatesApplied",
        "scene bridge guard": "readonly property bool hasSceneBridge",
        "simulation loader name": 'objectName: "simulationLoader"',
        "simulation loader component": "sourceComponent: SimulationRoot {",
        "fallback loader name": 'objectName: "fallbackLoader"',
        "fallback loader component": "sourceComponent: SimulationFallbackRoot {}",
        "ack hookup": "item.batchUpdatesApplied.connect(root.batchUpdatesApplied)",
    }

    for label, token in expected_tokens.items():
        assert token in contents, f"Missing {label} token '{token}' in main.qml"

    assert contents.count("Loader {") >= 2, "Expected both simulation and fallback loaders"
