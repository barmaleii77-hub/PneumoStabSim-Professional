import importlib.util
import sys
from pathlib import Path

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


def _baseline_environment() -> dict:
    manager = get_settings_manager()
    env = manager.get("graphics.environment")
    assert env, "Expected environment settings in current profile"
    return validate_environment_settings(env)


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
    payload = {key: 0 for key in ENVIRONMENT_REQUIRED_KEYS}
    sanitized = validate_environment_settings(payload)
    assert sanitized == payload


def test_environment_validation_rejects_payload_missing_required_key():
    payload = {key: 0 for key in ENVIRONMENT_REQUIRED_KEYS - {"ao_radius"}}
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
        "ao_radius": 3.0,
        "fog_near": 10.0,
        "fog_far": 1000.0,
        "ibl_intensity": 1.0,
        "ao_sample_rate": 64,
        "background_color": [0, 0, 0],
    }
    sanitized = validate_environment_settings(payload)
    assert sanitized == payload
