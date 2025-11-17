from __future__ import annotations

from src.ui.main_window_pkg.validation import (
    clamp_parameter_value,
    normalise_mode_value,
    sanitize_physics_payload,
)


def test_clamp_parameter_value_respects_range() -> None:
    # amplitude max is 0.2 according to PARAMETER_RANGES
    assert clamp_parameter_value("amplitude", 0.25) == 0.2
    # values within range stay untouched
    assert clamp_parameter_value("frequency", 1.5) == 1.5


def test_clamp_parameter_value_handles_aliases() -> None:
    # phase_global should clamp to 0..360
    assert clamp_parameter_value("phase_global", -10.0) == 0.0
    assert clamp_parameter_value("phase_global", 720.0) == 360.0
    # invalid inputs return None
    assert clamp_parameter_value("amplitude", "invalid") is None


def test_normalise_mode_value_validates_known_modes() -> None:
    assert normalise_mode_value("sim_type", "dynamics") == "DYNAMICS"
    assert normalise_mode_value("thermo_mode", "adiabatic") == "ADIABATIC"
    assert normalise_mode_value("thermo_mode", "unsupported") is None


def test_sanitize_physics_payload_filters_and_clamps() -> None:
    payload = {
        "include_springs": 0,
        "include_dampers": 1,
        "include_springs_kinematics": 0,
        "include_dampers_kinematics": 1,
        "spring_constant": -5.0,
        "damper_coefficient": "not-a-number",
        "lever_inertia_multiplier": -0.5,
        "extra": 123,
    }
    sanitized = sanitize_physics_payload(payload)
    assert sanitized["include_springs"] is False
    assert sanitized["include_dampers"] is True
    assert sanitized["include_springs_kinematics"] is False
    assert sanitized["include_dampers_kinematics"] is True
    assert sanitized["spring_constant"] >= 0.0
    # fallback to defaults for invalid numeric input
    assert sanitized["damper_coefficient"] > 0.0
    assert sanitized["lever_inertia_multiplier"] >= 0.0
    assert "extra" not in sanitized
