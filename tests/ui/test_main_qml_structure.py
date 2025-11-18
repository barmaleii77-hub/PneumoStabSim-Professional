"""Structural checks for the main QML entry point."""

from __future__ import annotations

from pathlib import Path

import pytest

QML_ROOT = Path("assets/qml/main.qml")
HIGH_CONTRAST_THEME = Path("assets/qml/themes/HighContrastTheme.qml")


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
        "fog depth toggle": "property bool fogDepthEnabled",
    }

    for label, token in expected_tokens.items():
        assert token in contents, f"Missing {label} token '{token}' in main.qml"

    fog_structure_tokens = {
        "fog block present": "fog: Fog {",
        "fog depth curve": "depthCurve: root.fogDepthCurve",
    }

    for label, token in fog_structure_tokens.items():
        assert token in contents, f"Missing {label} token '{token}' in main.qml"

    assert contents.count("Loader {") >= 2, (
        "Expected both simulation and fallback loaders"
    )


def test_accessibility_attributes():
    """High-contrast theme must advertise accessibility metadata."""

    assert HIGH_CONTRAST_THEME.exists(), "HighContrastTheme.qml is missing"
    contents = HIGH_CONTRAST_THEME.read_text(encoding="utf-8")

    expected_tokens = {
        "accessibility dictionary": "readonly property var accessibility",
        "shortcut description": '"sequence": "Ctrl+Alt+H"',
        "contrast ratio": '"contrastRatio": 12.8',
        "translated description": 'qsTr("Dark background with vivid accents for accessibility reviews.")',
    }

    for label, token in expected_tokens.items():
        assert token in contents, (
            f"Missing {label} token '{token}' in HighContrastTheme.qml"
        )
