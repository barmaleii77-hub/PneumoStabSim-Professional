from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest

pytest.importorskip(
    "PySide6.QtQuick",
    reason="PySide6 QtQuick module is required for UISetup scene suspension tests",
    exc_type=ImportError,
)
pytest.importorskip(
    "PySide6.QtQuickWidgets",
    reason="PySide6 QtQuickWidgets module is required for UISetup scene suspension tests",
    exc_type=ImportError,
)

from src.common.settings_manager import SettingsManager
from src.ui.main_window_pkg.ui_setup import UISetup


def _load_settings_payload() -> dict:
    template_path = Path("config/app_settings.json")
    return json.loads(template_path.read_text(encoding="utf-8"))


def _make_settings_manager(tmp_path: Path, payload: dict) -> SettingsManager:
    settings_path = tmp_path / "app_settings.json"
    settings_path.write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return SettingsManager(settings_file=settings_path)


def test_scene_suspension_defaults_propagated(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    payload = _load_settings_payload()
    manager = _make_settings_manager(tmp_path, payload)

    caplog.set_level(logging.WARNING)
    context = UISetup.build_qml_context_payload(manager)

    suspension_defaults = context["scene"].get("suspension", {})
    assert suspension_defaults
    assert suspension_defaults["rod_warning_threshold_m"] == pytest.approx(0.001)
    assert "suspension" in context["scene"]
    assert "Scene settings missing 'suspension' section" not in caplog.text


def test_scene_suspension_missing_section_logs_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    payload = _load_settings_payload()
    payload["current"]["graphics"]["scene"].pop("suspension", None)
    manager = _make_settings_manager(tmp_path, payload)

    caplog.set_level(logging.WARNING)
    context = UISetup.build_qml_context_payload(manager)

    suspension_defaults = context["scene"]["suspension"]
    assert suspension_defaults["rod_warning_threshold_m"] == pytest.approx(0.001)
    assert "Scene settings missing 'suspension' section" in caplog.text


def test_scene_suspension_missing_key_falls_back_to_default(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    payload = _load_settings_payload()
    payload["current"]["graphics"]["scene"]["suspension"] = {}
    payload["defaults_snapshot"]["graphics"]["scene"]["suspension"] = {}
    manager = _make_settings_manager(tmp_path, payload)

    caplog.set_level(logging.WARNING)
    context = UISetup.build_qml_context_payload(manager)

    suspension_defaults = context["scene"]["suspension"]
    assert suspension_defaults["rod_warning_threshold_m"] == pytest.approx(0.001)
    assert (
        "Scene suspension settings missing keys: rod_warning_threshold_m" in caplog.text
    )


def test_scene_suspension_uses_metadata_defaults(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    payload = _load_settings_payload()
    payload["current"]["graphics"]["scene"].pop("suspension", None)
    payload["defaults_snapshot"]["graphics"]["scene"].pop("suspension", None)
    metadata = payload.setdefault("metadata", {})
    scene_defaults = metadata.setdefault("scene_defaults", {})
    scene_defaults["suspension"] = {"rod_warning_threshold_m": 0.0035}

    manager = _make_settings_manager(tmp_path, payload)

    caplog.set_level(logging.WARNING)
    context = UISetup.build_qml_context_payload(manager)

    suspension_defaults = context["scene"]["suspension"]
    assert suspension_defaults["rod_warning_threshold_m"] == pytest.approx(0.0035)
    assert "Scene settings missing 'suspension' section" in caplog.text
    assert "Scene suspension settings missing keys" not in caplog.text


def test_scene_basics_use_metadata_defaults(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    payload = _load_settings_payload()
    scene = payload["current"]["graphics"]["scene"]
    snapshot_scene = payload["defaults_snapshot"]["graphics"]["scene"]
    scene.pop("exposure", None)
    scene.pop("default_clear_color", None)
    snapshot_scene.pop("exposure", None)
    snapshot_scene.pop("default_clear_color", None)

    metadata = payload.setdefault("metadata", {})
    scene_defaults = metadata.setdefault("scene_defaults", {})
    scene_defaults.update({"exposure": 2.5, "default_clear_color": "#ABCDEF"})

    manager = _make_settings_manager(tmp_path, payload)

    caplog.set_level(logging.WARNING)
    context = UISetup.build_qml_context_payload(manager)

    assert context["scene"]["exposure"] == pytest.approx(2.5)
    assert context["scene"]["default_clear_color"] == "#abcdef"
    assert "Scene settings missing keys: default_clear_color, exposure" in caplog.text


def test_reflection_probe_missing_keys_use_defaults(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    payload = _load_settings_payload()
    payload["current"]["graphics"].pop("reflection_probe", None)
    payload["defaults_snapshot"]["graphics"].pop("reflection_probe", None)

    manager = _make_settings_manager(tmp_path, payload)

    caplog.set_level(logging.WARNING)
    context = UISetup.build_qml_context_payload(manager)

    probe_defaults = context["reflection_probe"]
    assert probe_defaults["enabled"] is True
    assert probe_defaults["padding_m"] == pytest.approx(0.15)
    assert probe_defaults["quality"] == "veryhigh"
    assert probe_defaults["refresh_mode"] == "everyframe"
    assert probe_defaults["time_slicing"] == "individualfaces"
    assert set(probe_defaults.get("missing_keys", [])) == {
        "enabled",
        "padding_m",
        "quality",
        "refresh_mode",
        "time_slicing",
    }
    assert (
        "Reflection probe settings missing keys: enabled, padding_m, quality, refresh_mode, time_slicing"
        in caplog.text
    )
