import importlib.util
import json
from copy import deepcopy
from pathlib import Path

import pytest

from src.common.settings_manager import SettingsManager

PROJECT_ROOT = Path(__file__).resolve().parents[3]
MODULE_PATH = (
    PROJECT_ROOT
    / "src"
    / "ui"
    / "panels"
    / "graphics"
    / "panel_graphics_settings_manager.py"
)

_SPEC = importlib.util.spec_from_file_location(
    "graphics_settings_manager_test", MODULE_PATH
)
if _SPEC is None or _SPEC.loader is None:  # pragma: no cover - import guard
    raise RuntimeError("Unable to load graphics settings manager module for tests")

_MODULE = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_MODULE)

GraphicsSettingsService = _MODULE.GraphicsSettingsService
GraphicsSettingsError = _MODULE.GraphicsSettingsError


def _make_materials() -> dict[str, dict[str, str]]:
    base_color = "#ffffff"
    return {
        "frame": {"base_color": base_color},
        "lever": {"base_color": base_color},
        "tail_rod": {"base_color": base_color},
        "cylinder": {"base_color": base_color},
        "piston_body": {"base_color": base_color},
        "piston_rod": {"base_color": base_color},
        "joint_tail": {"base_color": base_color},
        "joint_arm": {"base_color": base_color},
        "joint_rod": {"base_color": base_color},
    }


def _make_baseline_payload() -> dict[str, object]:
    graphics = {
        "lighting": {"key": {"brightness": 1.0}},
        "environment": {"ibl_intensity": 1.0},
        "quality": {"preset": "ultra"},
        "camera": {"fov": 60.0},
        "materials": _make_materials(),
        "effects": {"bloom_enabled": True},
        "scene": {"exposure": 1.2},
    }
    animation = {"is_running": False, "frequency": 1.0}
    return {
        "metadata": {"units_version": "si_v2"},
        "current": {"graphics": deepcopy(graphics), "animation": deepcopy(animation)},
        "defaults_snapshot": {
            "graphics": deepcopy(graphics),
            "animation": deepcopy(animation),
        },
    }


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


@pytest.fixture()
def baseline_file(tmp_path: Path) -> Path:
    path = tmp_path / "baseline.json"
    _write_json(path, _make_baseline_payload())
    return path


def _make_legacy_payload(
    material_override: dict[str, dict[str, str]],
) -> dict[str, object]:
    baseline = _make_baseline_payload()
    return {
        "metadata": {"units_version": "si_v1"},
        "current": {
            "graphics": {
                "environment": {"ibl_intensity": 0.5},
                "scene": {"exposure": 1.5},
                "animation": {"is_running": False},
                "materials": material_override,
            }
        },
        "defaults_snapshot": {
            "graphics": deepcopy(baseline["current"]["graphics"]),
            "animation": deepcopy(baseline["current"]["animation"]),
        },
    }


def test_load_current_hydrates_legacy_shape(
    tmp_path: Path, baseline_file: Path
) -> None:
    legacy_materials = _make_materials()
    # Simulate missing material to exercise baseline hydration.
    legacy_materials.pop("joint_rod")

    settings_path = tmp_path / "settings.json"
    _write_json(settings_path, _make_legacy_payload(legacy_materials))

    manager = SettingsManager(settings_file=settings_path)
    service = GraphicsSettingsService(manager, baseline_path=baseline_file)

    state = service.load_current()

    assert set(state) == set(GraphicsSettingsService.REQUIRED_CATEGORIES)
    assert state["environment"]["ibl_intensity"] == 0.5
    # Hydrated from baseline
    assert state["lighting"]["key"]["brightness"] == 1.0
    # Missing joint restored from baseline
    assert "tail_rod" in state["materials"]
    assert "joint_rod" in state["materials"]
    assert state["animation"]["is_running"] is False
    assert state["animation"]["frequency"] == 1.0


def test_load_current_rejects_legacy_tail_alias(
    tmp_path: Path, baseline_file: Path
) -> None:
    legacy_materials = _make_materials()
    legacy_materials["tail"] = legacy_materials.pop("tail_rod")

    settings_path = tmp_path / "settings.json"
    _write_json(settings_path, _make_legacy_payload(legacy_materials))

    manager = SettingsManager(settings_file=settings_path)
    service = GraphicsSettingsService(manager, baseline_path=baseline_file)

    with pytest.raises(GraphicsSettingsError):
        service.load_current()


def test_ensure_valid_state_requires_all_materials(
    tmp_path: Path, baseline_file: Path
) -> None:
    settings_path = tmp_path / "settings.json"
    payload = _make_legacy_payload(_make_materials())
    _write_json(settings_path, payload)

    manager = SettingsManager(settings_file=settings_path)
    service = GraphicsSettingsService(manager, baseline_path=baseline_file)

    valid_state = service.load_current()
    valid_state["materials"].pop("frame")

    with pytest.raises(GraphicsSettingsError):
        service.ensure_valid_state(valid_state)


def test_save_current_persists_normalised_copy(
    tmp_path: Path, baseline_file: Path
) -> None:
    settings_path = tmp_path / "settings.json"
    payload = _make_legacy_payload(_make_materials())
    _write_json(settings_path, payload)

    manager = SettingsManager(settings_file=settings_path)
    service = GraphicsSettingsService(manager, baseline_path=baseline_file)

    state = service.load_current()
    state["environment"]["ibl_intensity"] = 2.2
    state["materials"]["tail_rod"]["base_color"] = "#ff0000"
    state["animation"]["is_running"] = True
    state["animation"]["frequency"] = 2.5

    service.save_current(state)

    saved = manager.get_category("graphics")
    animation = manager.get_category("animation")
    assert saved["environment"]["ibl_intensity"] == 2.2
    assert saved["materials"]["tail_rod"]["base_color"] == "#ff0000"
    assert "tail" not in saved["materials"]
    assert "lighting" in saved
    assert "animation" not in saved
    assert animation["is_running"] is True
    assert animation["frequency"] == 2.5


def test_save_current_as_defaults_does_not_add_aliases(
    tmp_path: Path, baseline_file: Path
) -> None:
    settings_path = tmp_path / "settings.json"
    payload = _make_legacy_payload(_make_materials())
    _write_json(settings_path, payload)

    manager = SettingsManager(settings_file=settings_path)
    service = GraphicsSettingsService(manager, baseline_path=baseline_file)

    state = service.load_current()
    state["materials"]["tail_rod"]["base_color"] = "#00ff00"
    state["animation"]["frequency"] = 3.3

    service.save_current_as_defaults(state)

    current = manager.get_category("graphics")
    defaults = manager.get("defaults_snapshot.graphics")
    animation_current = manager.get_category("animation")
    animation_defaults = manager.get("defaults_snapshot.animation")

    assert "tail" not in current["materials"]
    assert "tail" not in defaults["materials"]
    assert "animation" not in current
    assert animation_current["frequency"] == 3.3
    assert animation_defaults["frequency"] == 3.3
