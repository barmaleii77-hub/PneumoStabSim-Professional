from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.common.settings_manager import SettingsManager
from src.ui.panels.geometry.state_manager import GeometryStateManager


class DummySettingsManager:
    def __init__(self, payload):
        self._payload = payload
        self.saved = None

    def get(self, path, default=None):
        if path == "current.geometry":
            return dict(self._payload)
        return default

    def set(self, path, value, auto_save=True):
        self.saved = (path, value, auto_save)


def test_set_parameter_rejects_unknown_key():
    manager = GeometryStateManager()
    with pytest.raises(KeyError):
        manager.set_parameter("nonexistent", 0)


def test_update_parameters_rejects_unknown_keys():
    manager = GeometryStateManager()
    with pytest.raises(KeyError):
        manager.update_parameters({"wheelbase": 3.2, "extra": 1})


def test_load_state_filters_unknown_keys():
    dummy = DummySettingsManager({"wheelbase": 3.2, "unknown": 1.0})
    manager = GeometryStateManager(settings_manager=dummy)
    assert "unknown" not in manager.state


def test_save_state_persists_only_allowed_keys():
    dummy = DummySettingsManager({"wheelbase": 3.2, "unknown": 1.0})
    manager = GeometryStateManager(settings_manager=dummy)
    manager.state["wheelbase"] = 3.4
    manager.state["unknown"] = 99
    manager.save_state()
    assert dummy.saved is not None
    _, persisted, _ = dummy.saved
    assert "unknown" not in persisted
    assert "wheelbase" in persisted


def test_load_state_uses_persisted_geometry(tmp_path: Path) -> None:
    source = Path("config/app_settings.json")
    data = json.loads(source.read_text(encoding="utf-8"))
    data.setdefault("current", {}).setdefault("geometry", {})["wheelbase"] = 3.45

    target_dir = tmp_path / "config"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / "app_settings.json"
    target_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    settings = SettingsManager(settings_file=target_file)
    manager = GeometryStateManager(settings)

    assert pytest.approx(3.45) == manager.get_parameter("wheelbase")


def test_load_state_falls_back_to_defaults_snapshot(tmp_path: Path) -> None:
    source = Path("config/app_settings.json")
    data = json.loads(source.read_text(encoding="utf-8"))
    data.setdefault("defaults_snapshot", {}).setdefault("geometry", {})["wheelbase"] = 2.9
    data.setdefault("current", {}).pop("geometry", None)

    target_dir = tmp_path / "config"
    target_dir.mkdir(parents=True, exist_ok=True)
    target_file = target_dir / "app_settings.json"
    target_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    settings = SettingsManager(settings_file=target_file)
    manager = GeometryStateManager(settings)

    assert pytest.approx(2.9) == manager.get_parameter("wheelbase")


def test_rod_diameter_linking_roundtrip():
    manager = GeometryStateManager()

    manager.set_parameter("rod_diameter_m", 0.04)
    manager.set_parameter("rod_diameter_rear_m", 0.05)

    manager.set_parameter("link_rod_diameters", True)
    assert manager.get_parameter("rod_diameter_rear_m") == pytest.approx(0.04)

    manager.set_parameter("rod_diameter_m", 0.045)
    assert manager.get_parameter("rod_diameter_rear_m") == pytest.approx(0.045)

    manager.set_parameter("rod_diameter_rear_m", 0.046)
    assert manager.get_parameter("rod_diameter_m") == pytest.approx(0.046)

    manager.set_parameter("link_rod_diameters", False)
    assert manager.get_parameter("rod_diameter_m") == pytest.approx(0.04)
    assert manager.get_parameter("rod_diameter_rear_m") == pytest.approx(0.05)
