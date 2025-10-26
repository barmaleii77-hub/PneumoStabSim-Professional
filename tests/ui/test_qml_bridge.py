"""Unit tests for :mod:`src.ui.qml_bridge`."""

from __future__ import annotations

from src.ui.qml_bridge import QMLBridge


def test_prepare_for_qml_adds_camel_case_aliases() -> None:
    payload = {
        "auto_rotate_speed": 1.0,
        "min_distance": 5,
        "nested": {"max_distance": 10},
    }

    result = QMLBridge._prepare_for_qml(payload)

    assert result["auto_rotate_speed"] == 1.0
    assert result["autoRotateSpeed"] == 1.0
    assert result["min_distance"] == 5
    assert result["minDistance"] == 5
    assert result["nested"]["max_distance"] == 10
    assert result["nested"]["maxDistance"] == 10


def test_prepare_for_qml_does_not_override_existing_camel_case() -> None:
    payload = {"autoRotate": True, "auto_rotate": False}

    result = QMLBridge._prepare_for_qml(payload)

    assert result["autoRotate"] is True
    assert result["auto_rotate"] is False
