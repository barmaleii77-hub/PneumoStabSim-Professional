from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.ui.main_window import qml_bridge


class _DummySettingsManager:
    def __init__(self, payload: dict[str, object]):
        self._payload = payload

    def get(self, key: str, default=None):  # noqa: ANN001 - test stub
        if key == "current.threeD":
            return self._payload
        return default


class _DummyWindow:
    def __init__(self):
        self._qml_update_queue: dict[str, dict[str, object]] = {}
        self._qml_root_object = object()
        self._qml_flush_timer = None


@pytest.fixture()
def baseline_payload():
    return qml_bridge.initial_three_d_payload()


def test_initial_payload_exposes_phase3_defaults(baseline_payload):
    primitives = baseline_payload["primitives"]
    lighting = baseline_payload["lighting"]
    interaction = baseline_payload["interaction"]
    environment = baseline_payload["environment"]
    helpers = baseline_payload["helpers"]

    assert primitives["box"]["roughness"] == pytest.approx(0.35)
    assert primitives["sphere"]["metalness"] == pytest.approx(0.35)
    assert primitives["cylinder"]["position"] == [0.0, 0.9, -1.25]

    assert lighting["keyIntensity"] == pytest.approx(600.0)
    assert lighting["keyColor"].lower() == "#fff5e6"
    assert lighting["rimPosition"] == {"x": 3, "y": 2.5, "z": -4}

    assert interaction["enabled"] is True
    assert interaction["panSpeed"] == pytest.approx(0.015)

    assert environment["antialiasingMode"] == "msaa"
    assert environment["antialiasingQuality"] == "high"

    assert helpers["visible"] is True
    assert helpers["gridSpacing"] == pytest.approx(0.25)


def test_payload_merge_with_settings_and_overrides():
    settings_payload = {
        "primitives": {"box": {"scale": 2.0}},
        "interaction": {"enabled": False},
    }
    overrides = {"lighting": {"keyIntensity": 900.0}, "helpers": {"visible": False}}

    payload = qml_bridge.initial_three_d_payload(
        _DummySettingsManager(settings_payload), overrides=overrides
    )

    assert payload["primitives"]["box"]["scale"] == pytest.approx(2.0)
    assert payload["interaction"]["enabled"] is False
    assert payload["lighting"]["keyIntensity"] == pytest.approx(900.0)
    assert payload["helpers"]["visible"] is False


def test_sync_three_d_state_pushes_queue(monkeypatch):
    window = _DummyWindow()
    recorded: dict[str, object] = {}

    def _fake_queue(win, key, params):
        recorded["key"] = key
        recorded["params"] = params

    def _fake_flush(win):
        recorded["flushed"] = True

    monkeypatch.setattr(qml_bridge.QMLBridge, "queue_update", staticmethod(_fake_queue))
    monkeypatch.setattr(
        qml_bridge.QMLBridge, "flush_updates", staticmethod(_fake_flush)
    )

    payload = qml_bridge.sync_three_d_state(
        window, overrides={"interaction": {"enabled": False}}, flush=True
    )

    assert recorded["key"] == "threeD"
    assert recorded["params"]["interaction"]["enabled"] is False
    assert recorded.get("flushed") is True
    assert payload == recorded["params"]


def test_render_scenario_aligns_with_defaults(baseline_payload):
    scenario_path = Path("tests/scenarios/render/three_d_scene_baseline.json")
    scenario = json.loads(scenario_path.read_text(encoding="utf-8"))

    for primitive, fields in scenario["primitives"].items():
        for key, value in fields.items():
            assert baseline_payload["primitives"][primitive][key] == value

    for key, value in scenario["lighting"].items():
        assert baseline_payload["lighting"][key] == value
