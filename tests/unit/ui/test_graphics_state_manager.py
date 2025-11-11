"""Tests for the legacy GraphicsStateManager shim."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.common.settings_manager import SettingsManager
from src.ui.panels.graphics.state_manager import GraphicsStateManager


def _copy_settings_payload(target: Path) -> None:
    source = Path("config/app_settings.json")
    payload = json.loads(source.read_text(encoding="utf-8"))
    target.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def test_scene_state_roundtrip(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    _copy_settings_payload(settings_path)

    manager = SettingsManager(settings_file=settings_path)
    state_manager = GraphicsStateManager(settings_manager=manager)

    scene_state = state_manager.load_state("scene")
    assert isinstance(scene_state, dict)

    baseline_exposure = float(scene_state.get("exposure", 0.0) or 0.0)
    updated_exposure = baseline_exposure + 0.5 if baseline_exposure else 1.75
    scene_state["exposure"] = updated_exposure

    state_manager.save_state("scene", scene_state)

    reloaded = state_manager.load_state("scene")
    assert reloaded is not None
    assert reloaded["exposure"] == pytest.approx(updated_exposure)
    assert manager.get("graphics.scene.exposure") == pytest.approx(updated_exposure)


def test_load_all_includes_scene(tmp_path: Path) -> None:
    settings_path = tmp_path / "settings.json"
    _copy_settings_payload(settings_path)

    manager = SettingsManager(settings_file=settings_path)
    state_manager = GraphicsStateManager(settings_manager=manager)

    payload = state_manager.load_all()
    assert "scene" in payload
    assert isinstance(payload["scene"], dict)
