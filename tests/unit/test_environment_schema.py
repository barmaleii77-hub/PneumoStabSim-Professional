import importlib.util
import sys
from pathlib import Path
from typing import Any, Dict

import pytest

from src.common.settings_manager import get_settings_manager


def _load_environment_schema():
    module_name = "_environment_schema_for_tests"
    if module_name in sys.modules:
        return sys.modules[module_name]
    module_path = (
        Path(__file__).resolve().parents[2] / "src" / "ui" / "environment_schema.py"
    )
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader, "Failed to resolve environment_schema module"
    sys.modules[module_name] = module
    spec.loader.exec_module(module)  # type: ignore[attr-defined]
    return module


_env_schema = _load_environment_schema()
ENVIRONMENT_CONTEXT_PROPERTIES = _env_schema.ENVIRONMENT_CONTEXT_PROPERTIES
ENVIRONMENT_PARAMETERS = _env_schema.ENVIRONMENT_PARAMETERS
ENVIRONMENT_REQUIRED_KEYS = _env_schema.ENVIRONMENT_REQUIRED_KEYS
EnvironmentValidationError = _env_schema.EnvironmentValidationError
validate_environment_settings = _env_schema.validate_environment_settings
validate_scene_settings = _env_schema.validate_scene_settings
validate_animation_settings = _env_schema.validate_animation_settings


def _baseline_environment() -> dict:
    manager = get_settings_manager()
    env = manager.get("graphics.environment")
    assert env, "Expected environment settings in current profile"
    return validate_environment_settings(env)


def _build_minimal_environment_payload() -> Dict[str, Any]:
    payload: Dict[str, Any] = {}
    for definition in ENVIRONMENT_PARAMETERS:
        if definition.value_type == "bool":
            payload[definition.key] = False
        elif definition.value_type == "float":
            assert definition.min_value is not None, (
                f"Missing min value for {definition.key}"
            )
            payload[definition.key] = float(definition.min_value)
        elif definition.value_type == "int":
            if definition.allowed_values:
                payload[definition.key] = int(sorted(definition.allowed_values)[0])
            else:
                assert definition.min_value is not None, (
                    f"Missing min value for {definition.key}"
                )
                payload[definition.key] = int(definition.min_value)
        elif definition.value_type == "string":
            if definition.allowed_values:
                payload[definition.key] = next(iter(definition.allowed_values))
            elif definition.allow_empty_string:
                payload[definition.key] = ""
            elif "color" in definition.key:
                payload[definition.key] = "#000"
            else:
                payload[definition.key] = "value"
        else:  # pragma: no cover - safety guard for future types
            raise AssertionError(f"Unsupported value type: {definition.value_type}")

    if payload.get("fog_far", 0) < payload.get("fog_near", 0):
        payload["fog_far"] = payload["fog_near"]

    return payload


def test_environment_current_matches_schema():
    sanitized = _baseline_environment()
    assert set(sanitized.keys()) == set(ENVIRONMENT_REQUIRED_KEYS)


def test_environment_defaults_match_schema():
    manager = get_settings_manager()
    defaults = manager.get_all_defaults()
    env_defaults = defaults.get("graphics", {}).get("environment")
    assert env_defaults, "Defaults snapshot must contain environment section"
    sanitized = validate_environment_settings(env_defaults)
    assert set(sanitized.keys()) == set(ENVIRONMENT_REQUIRED_KEYS)


def test_environment_context_mapping_complete():
    assert set(ENVIRONMENT_CONTEXT_PROPERTIES.keys()) == set(ENVIRONMENT_REQUIRED_KEYS)


def test_environment_validation_rejects_missing_key():
    baseline = _baseline_environment()
    broken = baseline.copy()
    broken.pop("ao_radius")
    with pytest.raises(EnvironmentValidationError):
        validate_environment_settings(broken)


def test_environment_validation_rejects_invalid_range():
    baseline = _baseline_environment()
    broken = baseline.copy()
    broken["fog_far"] = broken["fog_near"] - 10
    with pytest.raises(EnvironmentValidationError):
        validate_environment_settings(broken)


def test_environment_validation_coerces_numeric_strings():
    baseline = _baseline_environment()
    mutated = baseline.copy()
    mutated["ibl_intensity"] = "2.5"
    mutated["ao_sample_rate"] = "3"
    sanitized = validate_environment_settings(mutated)
    assert isinstance(sanitized["ibl_intensity"], float)
    assert isinstance(sanitized["ao_sample_rate"], int)
    assert sanitized["ibl_intensity"] == pytest.approx(2.5)
    assert sanitized["ao_sample_rate"] == 3


def test_environment_validation_rejects_bad_color():
    baseline = _baseline_environment()
    mutated = baseline.copy()
    mutated["background_color"] = "not-a-color"
    with pytest.raises(EnvironmentValidationError):
        validate_environment_settings(mutated)


def test_environment_parameters_metadata_ranges_match():
    # Ensure numeric parameters declare explicit ranges as per schema
    for definition in ENVIRONMENT_PARAMETERS:
        if definition.value_type in {"float", "int"}:
            assert definition.min_value is not None, f"Missing min for {definition.key}"
            assert definition.max_value is not None, f"Missing max for {definition.key}"


# Additional test cases
def test_environment_validation_accepts_minimal_valid_payload():
    payload = _build_minimal_environment_payload()
    sanitized = validate_environment_settings(payload)
    assert sanitized == payload


def test_environment_validation_rejects_payload_missing_required_key():
    payload = _build_minimal_environment_payload()
    payload.pop("ao_radius")
    with pytest.raises(EnvironmentValidationError):
        validate_environment_settings(payload)


def test_environment_validation_rejects_payload_with_additional_unexpected_key():
    baseline = _baseline_environment()
    mutated = baseline.copy()
    mutated["unexpected_key"] = "surprise"
    with pytest.raises(EnvironmentValidationError):
        validate_environment_settings(mutated)


def test_environment_validation_handles_edge_case_values():
    baseline = _baseline_environment()
    mutated = baseline.copy()
    mutated["fog_near"] = 0
    mutated["fog_far"] = 1e6
    sanitized = validate_environment_settings(mutated)
    assert sanitized["fog_near"] == 0
    assert sanitized["fog_far"] == 1e6


def test_environment_validation_rejects_empty_payload():
    with pytest.raises(EnvironmentValidationError):
        validate_environment_settings({})


def test_environment_validation_accepts_validations_payload():
    payload = {
        "background_mode": "skybox",
        "background_color": "#123456",
        "skybox_enabled": True,
        "ibl_enabled": False,
        "ibl_intensity": 2.5,
        "probe_brightness": 1.0,
        "probe_horizon": 0.0,
        "ibl_rotation": 45.0,
        "ibl_source": "hdr/example.exr",
        "ibl_fallback": "",
        "skybox_blur": 0.5,
        "ibl_offset_x": 5.0,
        "ibl_offset_y": -5.0,
        "ibl_bind_to_camera": True,
        "fog_enabled": True,
        "fog_color": "#abcdef",
        "fog_density": 0.1,
        "fog_near": 10.0,
        "fog_far": 200.0,
        "fog_height_enabled": False,
        "fog_least_intense_y": -10.0,
        "fog_most_intense_y": 20.0,
        "fog_height_curve": 1.0,
        "fog_transmit_enabled": True,
        "fog_transmit_curve": 1.5,
        "ao_enabled": True,
        "ao_strength": 50.0,
        "ao_radius": 3.0,
        "ao_softness": 10.0,
        "ao_dither": True,
        "ao_sample_rate": 8,
    }
    sanitized = validate_environment_settings(payload)
    assert sanitized == payload


def test_environment_validation_rejects_sample_rate_above_max():
    baseline = _baseline_environment()
    mutated = baseline.copy()
    mutated["ao_sample_rate"] = 12
    with pytest.raises(EnvironmentValidationError):
        validate_environment_settings(mutated)


def test_scene_validation_accepts_valid_payload():
    payload = _build_payload(SCENE_PARAMETERS)
    sanitized = validate_scene_settings(payload)
    assert sanitized == payload


def test_animation_validation_accepts_valid_payload():
    payload = _build_payload(ANIMATION_PARAMETERS)
    payload["is_running"] = "true"
    sanitized = validate_animation_settings(payload)
    assert sanitized["is_running"] is True
    assert sanitized["amplitude"] == pytest.approx(payload["amplitude"])


def test_animation_validation_rejects_out_of_range_value():
    payload = _build_payload(ANIMATION_PARAMETERS)
    payload["amplitude"] = 360.0
    with pytest.raises(EnvironmentValidationError):
        validate_animation_settings(payload)
