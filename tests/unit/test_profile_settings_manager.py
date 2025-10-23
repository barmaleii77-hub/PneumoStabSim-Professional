"""Tests for the profile-aware settings manager."""

from __future__ import annotations

import json
import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

from src.core.settings_manager import ProfileSettingsManager


def _load_environment_schema():
    module_name = "pss_environment_schema_profile_tests"
    if module_name in sys.modules:
        return sys.modules[module_name]

    module_path = (
        Path(__file__).resolve().parents[2] / "src" / "ui" / "environment_schema.py"
    )
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    assert spec and spec.loader, "Failed to load environment schema module"
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


_env_schema = _load_environment_schema()

ENVIRONMENT_PARAMETERS = _env_schema.ENVIRONMENT_PARAMETERS
SCENE_PARAMETERS = _env_schema.SCENE_PARAMETERS
ANIMATION_PARAMETERS = _env_schema.ANIMATION_PARAMETERS


def _example_value(defn: Any) -> Any:
    if defn.value_type == "bool":
        return True
    if defn.value_type == "float":
        min_value = defn.min_value if defn.min_value is not None else 0.0
        max_value = defn.max_value if defn.max_value is not None else min_value + 1.0
        return (min_value + max_value) / 2.0
    if defn.value_type == "int":
        min_value = defn.min_value if defn.min_value is not None else 0
        max_value = defn.max_value if defn.max_value is not None else min_value + 10
        return int((min_value + max_value) // 2)
    if defn.value_type == "string":
        if defn.allowed_values:
            return defn.allowed_values[0]
        if defn.allow_empty_string:
            return ""
        if defn.pattern is not None:
            return "#1a2b3c"
        return "value"
    raise AssertionError(f"Unsupported value type: {defn.value_type}")


def _build_payload(definitions) -> Dict[str, Any]:
    return {defn.key: _example_value(defn) for defn in definitions}


def _alternate_payload(definitions) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    for defn in definitions:
        if defn.value_type == "bool":
            result[defn.key] = False
        elif defn.value_type == "float":
            result[defn.key] = defn.min_value if defn.min_value is not None else 0.0
        elif defn.value_type == "int":
            result[defn.key] = defn.min_value if defn.min_value is not None else 0
        elif defn.value_type == "string":
            if defn.allowed_values:
                result[defn.key] = defn.allowed_values[-1]
            elif defn.allow_empty_string:
                result[defn.key] = ""
            elif defn.pattern is not None:
                result[defn.key] = "#ffffff"
            else:
                result[defn.key] = "alternate"
        else:
            raise AssertionError(f"Unsupported value type: {defn.value_type}")
    return result


class DummySettingsManager:
    def __init__(self) -> None:
        self.data: Dict[str, Any] = {
            "graphics": {
                "environment": _build_payload(ENVIRONMENT_PARAMETERS),
                "scene": _build_payload(SCENE_PARAMETERS),
                "animation": _build_payload(ANIMATION_PARAMETERS),
            }
        }
        self.saved = 0

    def get(self, path: str, default: Any = None) -> Any:
        keys = path.split(".")
        current: Any = self.data
        for key in keys:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return default
        return current

    def set(self, path: str, value: Any, auto_save: bool = True) -> bool:
        keys = path.split(".")
        current = self.data
        for key in keys[:-1]:
            current = current.setdefault(key, {})
        current[keys[-1]] = value
        if auto_save:
            self.saved += 1
        return True

    def save(self) -> bool:
        self.saved += 1
        return True


@pytest.fixture()
def dummy_manager() -> DummySettingsManager:
    return DummySettingsManager()


def test_save_profile_writes_file(
    tmp_path: Path, dummy_manager: DummySettingsManager
):
    manager = ProfileSettingsManager(dummy_manager, profile_dir=tmp_path)
    result = manager.save_profile("Demo Profile")
    assert result.success

    profile_path = tmp_path / "demo_profile.json"
    assert profile_path.exists()

    payload = json.loads(profile_path.read_text(encoding="utf-8"))
    assert payload["graphics"]["environment"] == dummy_manager.get(
        "graphics.environment"
    )
    assert payload["graphics"]["scene"] == dummy_manager.get("graphics.scene")
    assert payload["graphics"]["animation"] == dummy_manager.get("graphics.animation")


def test_load_profile_updates_settings(
    tmp_path: Path, dummy_manager: DummySettingsManager
):
    manager = ProfileSettingsManager(dummy_manager, profile_dir=tmp_path)
    manager.save_profile("Demo")

    # Mutate settings to ensure load overwrites them
    dummy_manager.set("graphics.environment", _alternate_payload(ENVIRONMENT_PARAMETERS))
    dummy_manager.set("graphics.scene", _alternate_payload(SCENE_PARAMETERS))
    dummy_manager.set("graphics.animation", _alternate_payload(ANIMATION_PARAMETERS))

    result = manager.load_profile("Demo")
    assert result.success
    assert dummy_manager.saved > 0

    profile_path = tmp_path / "demo.json"
    stored = json.loads(profile_path.read_text(encoding="utf-8"))
    assert dummy_manager.get("graphics.environment") == stored["graphics"]["environment"]
    assert dummy_manager.get("graphics.scene") == stored["graphics"]["scene"]
    assert dummy_manager.get("graphics.animation") == stored["graphics"]["animation"]


def test_list_profiles_returns_sorted_names(
    tmp_path: Path, dummy_manager: DummySettingsManager
):
    manager = ProfileSettingsManager(dummy_manager, profile_dir=tmp_path)
    manager.save_profile("Bravo")
    manager.save_profile("Alpha")

    names = manager.list_profiles()
    assert names == ["Alpha", "Bravo"]


def test_delete_profile_removes_file(
    tmp_path: Path, dummy_manager: DummySettingsManager
):
    manager = ProfileSettingsManager(dummy_manager, profile_dir=tmp_path)
    manager.save_profile("ToRemove")
    path = tmp_path / "toremove.json"
    assert path.exists()

    result = manager.delete_profile("ToRemove")
    assert result.success
    assert not path.exists()
