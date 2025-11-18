from __future__ import annotations

from pathlib import Path
import re

QML_PATH = Path("qml/ThreeDScene.qml")


def test_three_d_scene_lists_primitives_and_lights() -> None:
    content = QML_PATH.read_text(encoding="utf-8")

    assert 'source: "#Cube"' in content
    assert 'source: "#Sphere"' in content
    assert 'source: "#Cylinder"' in content
    assert "DirectionalLight" in content
    assert content.count("PointLight") >= 2
    assert "shadowBias" in content


def test_three_d_scene_supports_batching_and_interaction_telemetry() -> None:
    content = QML_PATH.read_text(encoding="utf-8")

    assert re.search(r"function\s+applyThreeDUpdates", content)
    assert "pendingPythonUpdates" in content
    assert "lastAppliedBatch" in content
    assert "interactionTelemetry" in content
    assert "fieldOfViewDeg" in content


def test_three_d_scene_input_handlers_cover_orbit_pan_zoom() -> None:
    content = QML_PATH.read_text(encoding="utf-8")

    assert "DragHandler" in content
    assert "WheelHandler" in content
    assert "PinchHandler" in content
    assert "rotate / pan / zoom" in content
