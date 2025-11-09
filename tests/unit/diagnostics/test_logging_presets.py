from __future__ import annotations

from src.diagnostics.logging_presets import apply_logging_preset, describe_presets


def test_apply_logging_preset_defaults() -> None:
    env: dict[str, str] = {}

    preset = apply_logging_preset(env)

    assert preset.name == "normal"
    assert env["PSS_LOG_PRESET"] == "normal"
    assert env["QT_LOGGING_RULES"] == "*.debug=false;*.info=false"
    assert env["QSG_INFO"] == "0"
    assert "PSS_DIAG_DETAILS" not in env


def test_apply_logging_preset_debug() -> None:
    env: dict[str, str] = {}

    preset = apply_logging_preset(env, requested="debug")

    assert preset.name == "debug"
    assert env["PSS_LOG_PRESET"] == "debug"
    assert env["QT_LOGGING_RULES"].startswith("qt.qml.connections=true")
    assert env["QSG_INFO"] == "1"
    assert "PSS_DIAG_DETAILS" not in env


def test_apply_logging_preset_trace_enables_diagnostics() -> None:
    env: dict[str, str] = {}

    preset = apply_logging_preset(env, requested="trace")

    assert preset.name == "trace"
    assert env["PSS_LOG_PRESET"] == "trace"
    assert env["PSS_DIAG_DETAILS"] == "1"


def test_describe_presets_includes_expected_entries() -> None:
    presets = describe_presets()

    assert set(presets) == {"normal", "debug", "trace"}
